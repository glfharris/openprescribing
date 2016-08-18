import csv
import sys
from datetime import datetime
from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist
from frontend.models import Practice, PracticeStatistics, PCT, ImportLog

"""List size data comes in the form of a file that covers a particular
quarter. The quarter for which it is valid is not apparent from the
data or from the file name; only from the page on the NHSBSA website
from which it is downloaded.

Therefore, we encode this knowledge in the folder structure used in
the openprescribing-data repository layout, e.g.:

    data/patient_list_size/2016_03/Patient_List_Size_2016_05_12.csv

This indicates that the file covers the quarter to March 2016. The
dates in the filename are not relevant to the import process.

We maintain a log of when the prescribing and patient list size
datasets were last imported. Using this log, we can work out the
months for which patient list size data is required.

We insist on importing patient list data sequentially, to ensure there
are no gaps in the data.

"""

class Command(BaseCommand):
    args = ''
    help = 'Imports list size information. '
    help += 'Filename should be in the format '
    help += 'Patient_List_Size_YYYY_M1-M1.csv '
    help += 'where M1 is the first month in the quarter '
    help += 'and M2 is the last month in the quarter. '
    help += 'For example, Patient_List_Size_2014_06-09.csv'

    def add_arguments(self, parser):
        parser.add_argument('--filename')
        parser.add_argument('filenames', nargs='*')

    def handle(self, *args, **options):
        self.IS_VERBOSE = False
        filename_usage = (
            "You must either specify a filename or pass multiple filenames "
            "as positional arguments, e.g. `python manage.py "
            "import_list_sizes ../openprescribing-data/data/"
            "patient_list_size/*/*csv`, or `python manage.py import_list_sizes"
            " --filename ../openprescribing-data/data/2016_02/"
            "Patient_List_Size_2016-02-01.csv`, but not both"
        )
        if options['verbosity'] > 1:
            self.IS_VERBOSE = True
        if options['filename'] and options['filenames']:
            raise CommandError(filename_usage)
        if options['filename']:
            filenames = [options['filename']]
        elif options['filenames']:
            filenames = options['filenames']
        else:
            raise CommandError(filename_usage)
        filenames = sorted(filenames)
        months_without_list_data = \
            self.months_with_prescribing_data_but_no_list_data(self.IS_VERBOSE)
        for filename in filenames:
            if self.IS_VERBOSE:
                print "Processing %s" % filename
            entries = csv.DictReader(open('%s' % filename, 'rU'))
            if 'Month' in entries.fieldnames:
                # This is the BSA's multi-year data from an FOI request:
                # we don't need to derive the months from the filename.
                # What we do need to do is fill in the missing months.
                for row in entries:
                    m = row['Month'].split('/')
                    m.reverse()
                    month = '20' + '-'.join(m)
                    self.process_row(row, month)
                    n = [m[0], str(int(m[1]) + 1), m[2]]
                    self.process_row(row, '20' + '-'.join(n))
                    n = [m[0], str(int(m[1]) + 2), m[2]]
                    self.process_row(row, '20' + '-'.join(n))
            else:
                importfile_quarter_end = datetime.strptime(
                    filename.split("/")[-2] + "_01", "%Y_%m_%d")
                importfile_quarter_start = (importfile_quarter_end +
                                            relativedelta(months=-3))
                list_size_gap = [
                    required for required in months_without_list_data
                    if datetime.strptime(required, "%Y-%m-%d") <
                    importfile_quarter_start
                ]
                if list_size_gap:
                    msg = ("The supplied patient list size data file %s "
                           "covers the period %s to %s. To avoid gaps in the "
                           "data, you must import patient list size data in "
                           "date order; but the following months of "
                           "prescribing data are missing patient list sizes: "
                           "%s. Run the command again supplying list size "
                           "data current for these months.")
                    raise CommandError(msg % (filename,
                                              importfile_quarter_start,
                                              importfile_quarter_end,
                                              ', '.join(list_size_gap)))
                if self.IS_VERBOSE:
                    print ("Applying list size data for months %s to %s" %
                           (importfile_quarter_start, importfile_quarter_end))
                for i, row in enumerate(entries):
                    if self.IS_VERBOSE and i % 100 == 0:
                        sys.stdout.write(".")
                        sys.stdout.flush()
                    for m in months_without_list_data:
                        if m > importfile_quarter_end.strftime('%Y-%m-%d'):
                            break
                        else:
                            self.process_row(row, m)
                if self.IS_VERBOSE:
                    print
                    print ("Timestamping patient_list_log with date %s" %
                           importfile_quarter_end)
                ImportLog.objects.create(
                    current_at=importfile_quarter_end,
                    filename=filename,
                    category='patient_list_size'
                )
                months_without_list_data = \
                    self.months_with_prescribing_data_but_no_list_data(
                        self.IS_VERBOSE)
                if not months_without_list_data:
                    break

    def months_with_prescribing_data_but_no_list_data(self, verbose=False):
        prescribing_date = ImportLog.objects.latest_in_category(
            'prescribing').current_at
        list_size_date = ImportLog.objects.latest_in_category(
            'patient_list_size').current_at
        rd = relativedelta(prescribing_date, list_size_date)
        total_months = rd.years * 12 + rd.months
        months = []
        if total_months:
            for i in range(0, total_months):
                list_size_date = list_size_date + \
                    relativedelta(months=1)
                months.append(list_size_date.strftime("%Y-%m-01"))
        if verbose:
            if months:
                print ('Prescribing data lacking patient list data: '
                       '%s to %s' % (months[0],
                                     months[-1]))
            else:
                print 'All prescribing data and patient list data up to date'
        return months

    def process_row(self, row, month):
        prac_code = row['Practice Code']
        pct_code = row['PCO Code'][:3]
        try:
            practice = Practice.objects.get(code=prac_code)
        except Practice.DoesNotExist:
            return
        try:
            pct = PCT.objects.get(code=pct_code)
        except PCT.DoesNotExist:
            pct = None
        try:
            prac_list = PracticeStatistics.objects.get(
                practice=practice,
                pct=pct,
                date=month
            )
            prac_list.male_0_4 = int(row['Male 0-4'])
            prac_list.female_0_4 = int(row['Female 0-4'])
            prac_list.male_5_14 = int(row['Male 5-14'])
            prac_list.female_5_14 = int(row['Female 5-14'])
            prac_list.male_15_24 = int(row['Male 15-24'])
            prac_list.female_15_24 = int(row['Female 15-24'])
            prac_list.male_25_34 = int(row['Male 25-34'])
            prac_list.female_25_34 = int(row['Female 25-34'])
            prac_list.male_35_44 = int(row['Male 35-44'])
            prac_list.female_35_44 = int(row['Female 35-44'])
            prac_list.male_45_54 = int(row['Male 45-54'])
            prac_list.female_45_54 = int(row['Female 45-54'])
            prac_list.male_55_64 = int(row['Male 55-64'])
            prac_list.female_55_64 = int(row['Female 55-64'])
            prac_list.male_65_74 = int(row['Male 65-74'])
            prac_list.female_65_74 = int(row['Female 65-74'])
            prac_list.male_75_plus = int(row['Male 75+'])
            prac_list.female_75_plus = int(row['Female 75+'])
            prac_list.save()
        except ObjectDoesNotExist:
            prac_list = PracticeStatistics.objects.create(
                practice=practice,
                pct=pct,
                date=month,
                male_0_4=int(row['Male 0-4']),
                female_0_4=int(row['Female 0-4']),
                male_5_14=int(row['Male 5-14']),
                female_5_14=int(row['Female 5-14']),
                male_15_24=int(row['Male 15-24']),
                female_15_24=int(row['Female 15-24']),
                male_25_34=int(row['Male 25-34']),
                female_25_34=int(row['Female 25-34']),
                male_35_44=int(row['Male 35-44']),
                female_35_44=int(row['Female 35-44']),
                male_45_54=int(row['Male 45-54']),
                female_45_54=int(row['Female 45-54']),
                male_55_64=int(row['Male 55-64']),
                female_55_64=int(row['Female 55-64']),
                male_65_74=int(row['Male 65-74']),
                female_65_74=int(row['Female 65-74']),
                male_75_plus=int(row['Male 75+']),
                female_75_plus=int(row['Female 75+'])
            )
