import json
import glob
import numpy as np
import os
import pandas as pd
import sys
import api.view_utils as utils
from datetime import datetime
from dateutil.parser import *
from dateutil.relativedelta import *
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from frontend.models import Measure, MeasureGlobal,  MeasureValue, Practice
from scipy.stats import rankdata



class Command(BaseCommand):
    '''
    Supply either an --end_date argument to load data for
    all months up to that date.
    Or a --month argument to load data for just one month.
    '''
    def add_arguments(self, parser):
        parser.add_argument('--month')
        parser.add_argument('--end_date')
        parser.add_argument('--measure')

    def handle(self, *args, **options):
        self.IS_VERBOSE = False
        if options['verbosity'] > 1:
            self.IS_VERBOSE = True

        fpath = os.path.dirname(__file__)
        files = glob.glob(fpath + "/measure_definitions/*.json")
        measures = {}
        for fname in files:
            fname = os.path.join(fpath, fname)
            json_data=open(fname).read()
            d = json.loads(json_data)
            for k in d:
                if k in measures:
                    sys.exit()
                    print "duplicate entry found!", k
                else:
                    measures[k] = d[k]

        if 'measure' in options and options['measure']:
            measure_ids = [options['measure']]
        else:
            measure_ids = [k for k in measures]
        if not options['month'] and not options['end_date']:
            err = 'You must supply either --month or --end_date '
            err += 'in the format YYYY-MM-DD'
            print err
            sys.exit()
        months = []
        if 'month' in options and options['month']:
            months.append(options['month'])
        else:
            d = datetime(2014, 1, 1)
            end_date = parse(options['end_date'])
            while (d <= end_date):
                months.append(datetime.strftime(d, '%Y-%m-01'))
                d = d + relativedelta(months=1)

        for m in measure_ids:
            v = measures[m]
            v['description'] = ' '.join(v['description'])
            v['num'] = ' '.join(v['num'])
            v['denom'] = ' '.join(v['denom'])
            v['num_sql'] = ' '.join(v['num_sql'])
            v['denom_sql'] = ' '.join(v['denom_sql'])
            try:
                measure = Measure.objects.get(id=m)
            except ObjectDoesNotExist:
                measure = Measure.objects.create(
                    id=m,
                    name=v['name'],
                    title=v['title'],
                    description=v['description'],
                    numerator_description=v['num'],
                    denominator_description=v['denom'],
                    ranking_description=v['rank'],
                    numerator_short=v['numerator_short'],
                    denominator_short=v['denominator_short'],
                    url=v['url'],
                    is_cost_based=v['is_cost_based']
                )

            for month in months:
                # We're interested in all standard practices that were
                # operating that month.
                practices = Practice.objects.filter(setting=4) \
                                            .filter(Q(open_date__isnull=True) |
                                                    Q(open_date__lt=month)) \
                                            .filter(Q(close_date__isnull=True) |
                                                    Q(close_date__gt=month))
                if self.IS_VERBOSE:
                    print 'updating', measure.title, 'for', month

                for p in practices:
                    self.create_measurevalue(measure, p, month,
                                             v['num_sql'], v['denom_sql'])

                records = MeasureValue.objects.filter(month=month)\
                            .filter(measure=measure).values()
                df = self.create_ranked_dataframe(records)
                mg = self.create_measureglobal(df, measure, month)
                for i, row in df.iterrows():
                    self.update_practice_percentile(row, measure, month)
                    if measure.is_cost_based:
                        self.update_cost_savings(row, df)

    def create_measurevalue(self, measure, p, month, num_sql, denom_sql):
        '''
        Given a practice and the definition of a measure, calculate
        the measure's values for a particular month.
        '''
        try:
            mv = MeasureValue.objects.get(
                measure=measure,
                practice=p,
                month=month
            )
        except ObjectDoesNotExist:
            mv = MeasureValue.objects.create(
                measure=measure,
                practice=p,
                month=month
            )
        # Values should match *current* organisational hierarchy.
        mv.pct = p.ccg
        numerator = utils.execute_query(num_sql, [[p.code, month]])
        if numerator and numerator[0]['items']:
                mv.numerator = float(numerator[0]['items'])
        else:
            mv.numerator = None
        denominator = utils.execute_query(denom_sql, [[p.code, month]])
        if denominator and denominator[0]['items']:
            mv.denominator = float(denominator[0]['items'])
        else:
            mv.denominator = None
        if mv.denominator:
            if mv.numerator:
                mv.calc_value = mv.numerator / mv.denominator
            else:
                mv.calc_value = 0
        else:
            mv.calc_value = None
        mv.save()

    def update_practice_percentile(self, row, measure, month):
        practice = Practice.objects.get(code=row.practice_id)
        mv = MeasureValue.objects.get(practice=practice,
                                      month=month,
                                      measure=measure)
        if (row.percentile is None) or np.isnan(row.percentile):
            row.percentile = None
        mv.percentile = row.percentile
        mv.save()

    def update_cost_savings(self, row, df):
        '''
        Stub
        '''
        pass

    def create_ranked_dataframe(self, records):
        '''
        Use scipy's rankdata to rank by calc_value - we use rankdata rather than
        pandas qcut because pandas qcut does not cope well with repeated values
        (e.g. repeated values of zero, which we will have a lot of).
        Then normalise percentiles between 0 and 100.
        '''
        if self.IS_VERBOSE:
            print 'processing dataframe of length', len(records)
        df = pd.DataFrame.from_records(records)
        if 'calc_value' in df:
            df.loc[df['calc_value'].notnull(), 'rank_val'] = \
                rankdata(df[df.calc_value.notnull()].calc_value.values,
                         method='min') - 1
            df1 = df[df['rank_val'].notnull()]
            df.loc[df['rank_val'].notnull(), 'percentile'] = \
                (df1.rank_val / float(len(df1)-1)) * 100
            return df
        else:
            return None

    def create_measureglobal(self, df, measure, month):
        '''
        Given the ranked dataframe of all practices, create or
        update the MeasureGlobal percentiles for that month.
        '''
        mg, created = MeasureGlobal.objects.get_or_create(
            measure=measure,
            month=month
        )
        mg.numerator = df['numerator'].sum()
        if np.isnan(mg.numerator):
            mg.numerator = None
        mg.denominator = df['denominator'].sum()
        if np.isnan(mg.denominator):
            mg.denominator = None
        if mg.denominator:
            if mg.numerator:
                mg.calc_value = float(mg.numerator) / \
                    float(mg.denominator)
            else:
                mg.calc_value = mg.numerator
        else:
            mg.calc_value = None
        mg.practice_10th = df.quantile(.1)['calc_value']
        mg.practice_25th = df.quantile(.25)['calc_value']
        mg.practice_50th = df.quantile(.5)['calc_value']
        mg.practice_75th = df.quantile(.75)['calc_value']
        mg.practice_90th = df.quantile(.9)['calc_value']
        mg.save()
        return mg
