var expect = require('chai').expect;
var mu = require('../src/measure_utils');
var _ = require('underscore');

describe('Measures', function() {
  describe('#getDataUrls', function() {
    it('should get the URL for all CCGs', function() {
      var options = {
        orgId: null,
        orgType: 'CCG',
        measure: null
      };
      var urls = mu.getDataUrls(options);
      expect(urls.panelMeasuresUrl).to.equal('/api/1.0/measure_by_ccg/?format=json');
      expect(urls.globalMeasuresUrl).to.equal('/api/1.0/measure/?format=json');
    });

    it('should get the URL for an organisation', function() {
      var options = {
        orgId: 'A81001',
        orgType: 'practice',
        measure: null
      };
      var urls = mu.getDataUrls(options);
      expect(urls.panelMeasuresUrl).to.equal('/api/1.0/measure_by_practice/?format=json&org=A81001');
      expect(urls.globalMeasuresUrl).to.equal('/api/1.0/measure/?format=json');
    });

    it('should get the URL for an measure', function() {
      var options = {
        orgId: null,
        orgType: 'CCG',
        measure: 'ace'
      };
      var urls = mu.getDataUrls(options);
      expect(urls.panelMeasuresUrl).to.equal('/api/1.0/measure_by_ccg/?format=json&measure=ace');
      expect(urls.globalMeasuresUrl).to.equal('/api/1.0/measure/?format=json&measure=ace');
    });
  });

  describe('#getCentilesAndYAxisExtent', function() {
    it('should calculate global series and y-extent correctly', function() {
      var globalData = [{
        data: [
        {
          date: '2015-01-01',
          percentiles: {
            practice: {10: 46, 90: 97}
          }
        },
        {
          date: '2015-02-01',
          percentiles: {
            practice: {10: 25, 90: 82}
          }
        }
        ],
        id: 'ace'
      }
      ],
      options = {
        rollUpBy: 'org_id',
        measure: 'ace',
        orgType: 'practice'
      },
      centiles = ["10", "20", "30", "40", "50", "60", "70", "80", "90"];
      var result = mu.getCentilesAndYAxisExtent(globalData, options, centiles);
      expect(result.globalYMax.y).to.equal(97);
      expect(result.globalYMin.y).to.equal(25);
      expect(result.globalCentiles['10'][0].x).to.equal(1420070400000);
      expect(result.globalCentiles['10'][0].y).to.equal(46);
      expect(result.globalCentiles['90'][0].x).to.equal(1420070400000);
      expect(result.globalCentiles['90'][0].y).to.equal(97);
    });

    it('should do nothing when the charts are multiple measures', function() {
      var globalData = [],
      options = {
        rollUpBy: 'measure_id'
      },
      centiles = ["10", "20", "30", "40", "50", "60", "70", "80", "90"];
      var result = mu.getCentilesAndYAxisExtent(globalData, options, centiles);
      expect(result.globalYMax).to.equal(0);
      expect(result.globalYMin).to.equal(0);
    });
  });

  describe('annotateData', function () {
    it('rolls up by organisation and calculates means', function() {
      var org_data = [{
        data: [
          {
            pct_id: '04N',
            pct_name: 'NHS RUSHCLIFFE CCG',
            date: '2015-01-01',
            calc_value: 8,
            percentile: 20
          },
          {
            pct_id: '04N',
            pct_name: 'NHS RUSHCLIFFE CCG',
            date: '2015-02-01',
            calc_value: 9,
            percentile: 21
          },
          {
            pct_id: '03V',
            pct_name: 'NHS CORBY CCG',
            date: '2015-01-01',
            calc_value: 10,
            percentile: 40
          },
          {
            pct_id: '03V',
            pct_name: 'NHS CORBY CCG',
            date: '2015-02-01',
            calc_value: 12,
            percentile: 37
          },
          {
            pct_id: '99P',
            pct_name: 'NHS NORTH, EAST AND WEST DEVON CCG',
            date: '2015-01-01',
            calc_value: null,
            percentile: null
          },
          {
            pct_id: '99P',
            pct_name: 'NHS NORTH, EAST AND WEST DEVON CCG',
            date: '2015-02-01',
            calc_value: null,
            percentile: null
          }
        ],
        id:"ace",
        is_cost_based: true,
        is_percentage: true,
        name: "High-cost ACE inhibitors",
        numerator_short: "High-cost ACEs quantity",
        title: "TBA"
      }];
      var summarise_months = 6;
      var result = mu.annotateData(
        org_data,
        { rollUpBy: 'org_id', orgType: 'ccg'}, summarise_months);
      expect(result.length).to.equal(3);
      var corby = _.findWhere(result, {name: 'NHS CORBY CCG'});
      expect(corby.meanPercentile).to.equal(38.5);
      expect(corby.isPercentage).to.be.true;
      expect(corby.data.length).to.equal(2);
      var devon = _.findWhere(result, {name: 'NHS NORTH, EAST AND WEST DEVON CCG'});
      expect(devon.meanPercentile).to.equal(null);
      expect(devon.isPercentage).to.be.true;
      expect(devon.data.length).to.equal(2);
    });
  });

  describe('sortData', function () {
    it("sorts as expected", function () {
      var data = [
        {
          id: 1,
          meanPercentile: 40,
          lowIsGood: true
        },
        {
          id: 2,
          meanPercentile: 60,
          lowIsGood: true
        },
        {
          id: 3,
          meanPercentile: 50,
          lowIsGood: false
        },
        {
          id: 4,
          meanPercentile: 50,
          lowIsGood: true
        },
        {
          id: 5,
          meanPercentile: 40,
          lowIsGood: false,
        },
        {
          id: 6,
          meanPercentile: null,
          lowIsGood: false
        }
      ];
      var result = mu.sortData(data);
      var positions = _.map(result, function(d) {return d.id});
      expect(positions).to.eql([2,5,3,4,1,6]);
    });
  });

  describe('#_rollUpByOrg', function() {
    it('rolls up by CCG', function() {
      var data = {
        data: [
        {
          pct_id: '04N',
          pct_name: 'NHS RUSHCLIFFE CCG',
          date: '2015-01-01',
          calc_value: 8
        },
        {
          pct_id: '04N',
          pct_name: 'NHS RUSHCLIFFE CCG',
          date: '2015-02-01',
          calc_value: 9
        },
        {
          pct_id: '03V',
          pct_name: 'NHS CORBY CCG',
          date: '2015-01-01',
          calc_value: 10
        },
        {
          pct_id: '03V',
          pct_name: 'NHS CORBY CCG',
          date: '2015-02-01',
          calc_value: 12
        }
        ],
        id:"ace",
        is_cost_based: true,
        is_percentage: true,
        name: "High-cost ACE inhibitors",
        numerator_short: "High-cost ACEs quantity",
        title: "TBA"
      };
      var result = mu._rollUpByOrg(data, 'CCG');
      expect(result.length).to.equal(2);
      expect(result[0].data[0].date).to.equal('2015-01-01');
    });

    it('rolls up by practice', function() {
      var data = {
        data: [
        {
          practice_id: 'A81001',
          practice_name: 'foo',
          date: '2015-01-01',
          calc_value: 8
        },
        {
          practice_id: 'A81001',
          practice_name: 'foo',
          date: '2015-02-01',
          calc_value: 9
        },
        {
          practice_id: 'A81002',
          practice_name: 'bar',
          date: '2015-01-01',
          calc_value: 10
        },
        {
          practice_id: 'A81002',
          practice_name: 'bar',
          date: '2015-02-01',
          calc_value: 12
        }
        ],
        id:"ace",
        is_cost_based: true,
        is_percentage: true,
        name: "High-cost ACE inhibitors",
        numerator_short: "High-cost ACEs quantity",
        title: "TBA"
      };
      var result = mu._rollUpByOrg(data, 'practice');
      expect(result.length).to.equal(2);
      expect(result[0].data[0].date).to.equal('2015-01-01');
    });
  });

  describe('#_getSavingAndPercentilePerItem', function() {

    it('should get mean cost saving and percentile across last N months', function() {
      var data = [{
        data: [
        {date: '2015-01-01', percentile: 21, cost_savings: { 50: 7 }},
        {date: '2015-02-01', percentile: 22, cost_savings: { 50: 7 }},
        {date: '2015-03-01', percentile: 19, cost_savings: { 50: 7 }},
        {date: '2015-04-01', percentile: 16, cost_savings: { 50: 7 }},
        {date: '2015-05-01', percentile: 15, cost_savings: { 50: 7 }},
        {date: '2015-06-01', percentile: 19, cost_savings: { 50: 12 }},
        {date: '2015-07-01', percentile: 18, cost_savings: { 50: 81 }},
        {date: '2015-08-01', percentile: 16, cost_savings: { 50: 12.8 }},
        {date: '2015-09-01', percentile: 13, cost_savings: { 50: 12.4 }},
        {date: '2015-10-01', percentile: 12, cost_savings: { 50: 10 }},
        {date: '2015-11-01', percentile: 12, cost_savings: { 50: 8 }},
        {date: '2015-12-01', percentile: 7, cost_savings: { 50: 7 }},
        ]
      }];
      var result = mu._getSavingAndPercentilePerItem(data, 6);
      expect(result[0].meanPercentile).to.equal(13);
      expect(result[0].costSaving50th).to.equal(131.2);
    });

    it('should handle intermittent null elements correctly', function() {
      var data = [{
        data: [
        {date: '2015-07-01', percentile: 2, cost_savings: { 50: -20 }},
        {date: '2015-08-01', percentile: null, cost_savings: null},
        {date: '2015-09-01', percentile: 3, cost_savings: { 50: -10 }},
        {date: '2015-10-01', percentile: 2, cost_savings: { 50: -10 }},
        {date: '2015-11-01', percentile: 0, cost_savings: { 50: -10 }},
        {date: '2015-12-01', percentile: 4, cost_savings: { 50: -10 }},
        ]
      }];
      var result = mu._getSavingAndPercentilePerItem(data, 6);
      expect(result[0].meanPercentile).to.equal(11/5);
      expect(result[0].costSaving50th).to.equal(-60);
    });

    it('should handle entirely null data correctly', function() {
      var data = [{
        data: [
        {date: '2015-07-01', percentile: null, cost_savings: null},
        {date: '2015-08-01', percentile: null, cost_savings: null},
        {date: '2015-09-01', percentile: null, cost_savings: null},
        {date: '2015-10-01', percentile: null, cost_savings: null},
        {date: '2015-11-01', percentile: null, cost_savings: null},
        {date: '2015-12-01', percentile: null, cost_savings: null},
        ]
      }];
      var result = mu._getSavingAndPercentilePerItem(data, 6);
      expect(result[0].meanPercentile).to.equal(null);
      expect(result[0].costSaving50th).to.equal(0);
    });

    it('should handle a short data array', function() {
      var data = [{
        data: [
        {date: '2015-10-01', percentile: 12, cost_savings: { 50: 10 }},
        {date: '2015-11-01', percentile: 12, cost_savings: { 50: 8 }},
        {date: '2015-12-01', percentile: 6, cost_savings: { 50: 7 }},
        ]
      }];
      var result = mu._getSavingAndPercentilePerItem(data, 6);
      expect(result[0].meanPercentile).to.equal(10);
      expect(result[0].costSaving50th).to.equal(25);
    });

    it('should handle an empty data array', function() {
      var data = [{
        data: []
      }];
      var result = mu._getSavingAndPercentilePerItem(data, 6);
      expect(result[0].data.length).to.equal(0);
    });
  });

  describe('#getPerformanceSummary', function() {

    it('gets summaries for a single measure across organisations', function() {
      var data = [
      { meanPercentile: 100, costSaving50th: 100 },
      { meanPercentile: 77, costSaving50th: 100 },
      { meanPercentile: 60, costSaving50th: 100 },
      { meanPercentile: 50, costSaving50th: 0 },
      { meanPercentile: 30, costSaving50th: -100 },
      { meanPercentile: 21, costSaving50th: -100 },
      { meanPercentile: 11, costSaving50th: -100 }
      ];
      var options = {
        rollUpBy: 'org_id',
        isCostBasedMeasure: true,
        orgId: null,
        orgType: 'CCG',
        measure: 'statins'
      };
      var result = mu.getPerformanceSummary(data, options, 6);
      expect(result.total).to.equal(7);
      expect(result.worseThanMedian).to.equal(3);
      expect(result.potentialSavings50th).to.equal(300);
      var str = "Over the past 6 months, 3 of 7 CCGs have prescribed ";
      str += 'worse than the national median.';
      expect(result.performanceDescription).to.equal(str);
      str = 'Over the past 6 months, if all CCGs had prescribed at ';
      str += 'the median ratio or better, then NHS England would have ';
      str += 'spent £300.00 less. (We use the national median as a ';
      str += 'suggested target because by definition, 50% of CCGs ';
      str += 'were already prescribing at this level or better, so ';
      str += 'we think it ought to be achievable.)';
      expect(result.costSavings).to.equal(str);
    });

    it('gets summaries for all measures across one organisation', function() {
      var data = [
        { meanPercentile: 14, lowIsGood: true },
        { meanPercentile: 33, lowIsGood: true },
        { meanPercentile: 82, lowIsGood: true, costSaving50th: 12000 },
        { meanPercentile: 50, lowIsGood: true },
        { meanPercentile: 30, lowIsGood: false },
        { meanPercentile: 21, lowIsGood: true, costSaving50th: -200 }
      ];
      var options = {
        rollUpBy: 'measure_id',
        isCostBasedMeasure: true,
        orgId: 'A81001',
        orgType: 'practice',
        measure: null
      };
      var result = mu.getPerformanceSummary(data, options, 6);
      expect(result.total).to.equal(6);
      expect(result.worseThanMedian).to.equal(2);
      expect(result.potentialSavings50th).to.equal(12000);
      var str = "Over the past 6 months, this organisation has ";
      str += "prescribed worse than the median on 2 of 6 measures.";
      expect(result.performanceDescription).to.equal(str);
      str = "Over the past 6 months, if this practice  had prescribed ";
      str += "at the median ratio or better on all cost-saving measures ";
      str += "below, then it would have spent £12,000.00 less. (We use ";
      str += "the national median as a suggested target because by ";
      str += "definition, 50% of practices were already prescribing ";
      str += "at this level or better, so we think it ought to be ";
      str += "achievable.)";
      expect(result.costSavings).to.equal(str);
    });

    it('handles empty data', function() {
      var options = {
        rollUpBy: 'org_id',
        isCostBasedMeasure: true,
        orgId: null,
        orgType: 'CCG',
        measure: 'ace'
      };
      var result = mu.getPerformanceSummary([], options, null);
      var str = "This organisation hasn't prescribed on any of these measures.";
      expect(result.performanceDescription).to.equal(str);
    });

  });

  describe('#addChartAttributes', function() {
    it('should not error when a given measure is missing', function () {
      var data = [{
        'data': [],
        'isPercentage': false,
        'id': 'somethingMissing',
      }];
      expect(
        function () {
          mu.addChartAttributes(
            data, [], [], [], {'orgType': '', 'rollUpBy': 'measure_id'}, 0);
        }).to.not.throw(TypeError);
    });

    it('sets the expected title, URL, and descriptions for all-CCG charts', function() {
      var data = [
      {
        id: '10W',
        name: 'NHS SOUTH READING CCG',
        meanPercentile: 80,
        costSaving50th: 10,
        isCostBased: true,
        data: []
      }
      ],
      globalData = [],
      globalCentiles = [],
      centiles = ['10'],
      options = {
        rollUpBy: 'org_id',
        orgType: 'CCG',
        orgId: null,
        parentOrg: null
      };
      var result = mu.addChartAttributes(data, globalData, globalCentiles,
        centiles, options, 6);
      expect(result[0].chartTitle).to.equal('10W: NHS SOUTH READING CCG');
      expect(result[0].chartTitleUrl).to.equal('/ccg/10W');
      str = 'This CCG was at the 80th percentile on average across the past ';
      str += '6 months. If it had prescribed in line ';
      str += 'with the median, this CCG would have spent £10.00 less ';
      str += 'over the past 6 months.';
      expect(result[0].chartExplanation).to.equal(str);
    });

    it('sets the expected title, URL, and descriptions for non-cost-based all-CCG charts', function() {
      var data = [
      {
        id: '10W',
        name: 'NHS SOUTH READING CCG',
        meanPercentile: 80,
        isCostBased: false,
        data: []
      }
      ],
      globalData = [],
      globalCentiles = [],
      centiles = ['10'],
      options = {
        rollUpBy: 'org_id',
        orgType: 'CCG',
        orgId: null,
        parentOrg: null
      };
      var result = mu.addChartAttributes(data, globalData, globalCentiles,
        centiles, options, 6);
      expect(result[0].chartTitle).to.equal('10W: NHS SOUTH READING CCG');
      expect(result[0].chartTitleUrl).to.equal('/ccg/10W');
      var str = 'This CCG was at the 80th percentile ';
      str += 'on average across the past 6 months. ';
      expect(result[0].chartExplanation).to.equal(str);
    });

    it('sets the expected title, URL, and descriptions for one-CCG measure charts', function() {
      var data = [
      {
        id: 'ace',
        name: 'ACE',
        meanPercentile: 80,
        costSaving50th: 10,
        isCostBased: true,
        data: []
      }
      ],
      globalData = [{ id: 'ace', data: []}],
      globalCentiles = [],
      centiles = ['10'],
      options = {
        rollUpBy: 'measure_id',
        orgType: 'CCG',
        orgId: '03V',
        parentOrg: null
      };
      var result = mu.addChartAttributes(data, globalData, globalCentiles,
        centiles, options, 6);
      expect(result[0].chartTitle).to.equal('ACE');
      expect(result[0].chartTitleUrl).to.equal('/ccg/03V/ace');
      str = 'This CCG was at the 80th percentile on average across the ';
      str += 'past 6 months. If it had prescribed in line ';
      str += 'with the median, this CCG would have spent £10.00 less ';
      str += 'over the past 6 months.';
      expect(result[0].chartExplanation).to.equal(str);
    });

    it('sets the expected title, URL, and descriptions for measure practice charts', function() {
      var data = [
      {
        id: 'ace',
        name: 'ACE',
        meanPercentile: 80,
        costSaving50th: 10,
        isCostBased: true,
        data: []
      }
      ],
      globalData = [{ id: 'ace', data: []}],
      globalCentiles = [],
      centiles = ['10'],
      options = {
        rollUpBy: 'measure_id',
        orgType: 'practice',
        orgId: 'A81001',
        parentOrg: '03V'
      };
      var result = mu.addChartAttributes(data, globalData, globalCentiles,
        centiles, options, 6);
      expect(result[0].chartTitle).to.equal('ACE');
      expect(result[0].chartTitleUrl).to.equal('/ccg/03V/ace');
      str = 'This practice was at the 80th percentile on average across ';
      str += 'the past 6 months. If it had prescribed in line ';
      str += 'with the median, this practice would have spent £10.00 less ';
      str += 'over the past 6 months.';
      expect(result[0].chartExplanation).to.equal(str);
    });
  });

  describe('#_addHighchartsXAndY', function() {
    it('should convert global data correctly', function() {
      var data = [
      { date: '2015-01-01', percentiles: { 'ccg': { '10': 2.1} }},
      { date: '2015-02-01', percentiles: { 'ccg': { '10': 2.4} }},
      { date: '2015-03-01', percentiles: { 'ccg': { '10': 2.2} }}
      ];
      var options = {'orgType': 'ccg'};
      var result = mu._addHighchartsXAndY(data, true, false, options, '10');
      expect(result.length).to.equal(3);
      expect(result[0].x).to.equal(1420070400000);
      expect(result[0].y).to.equal(2.1);
    });

    it('should multiply percentages by 100 for display purposes', function() {
      var data = [
      { date: '2015-01-01', calc_value: '0.08'},
      { date: '2015-02-01', calc_value: '0.04'},
      { date: '2015-03-01', calc_value: '0.05'}
      ];
      var options = {};
      var result = mu._addHighchartsXAndY(data, false, true, options, null);
      expect(result.length).to.equal(3);
      expect(result[0].x).to.equal(1420070400000);
      expect(result[0].y).to.equal(8);
    });
  });

  describe('#_getChartTitleEtc', function() {
    it('should get explanation for cost-based measures', function() {
      var d = {
        id: 'ace',
        name: 'ACE',
        meanPercentile: 80,
        costSaving50th: 10,
        isCostBased: true,
        data: []
      },
      options = {
        rollUpBy: 'measure_id',
        orgType: 'practice',
        orgId: 'A81001',
        parentOrg: '03V'
      };
      var result = mu._getChartTitleEtc(d, options, 6);
      expect(result.chartTitle).to.equal('ACE');
      expect(result.chartTitleUrl).to.equal('/ccg/03V/ace');
      str = 'This practice was at the 80th percentile on average across ';
      str += 'the past 6 months. If it had prescribed in line ';
      str += 'with the median, this practice would have spent £10.00 less ';
      str += 'over the past 6 months.';
      expect(result.chartExplanation).to.equal(str);
    });

    it('should get explanation for non-cost-based measures', function() {
      var d = {
        id: 'ace',
        name: 'ACE',
        meanPercentile: 80,
        costSaving50th: null,
        isCostBased: false,
        data: []
      },
      options = {
        rollUpBy: 'measure_id',
        orgType: 'practice',
        orgId: 'A81001',
        parentOrg: '03V'
      };
      var result = mu._getChartTitleEtc(d, options, 6);
      expect(result.chartTitle).to.equal('ACE');
      expect(result.chartTitleUrl).to.equal('/ccg/03V/ace');
      str = 'This practice was at the 80th percentile ';
      str += 'on average across the past 6 months. ';
      expect(result.chartExplanation).to.equal(str);
    });
  });

  describe('#_getChartOptions', function() {

    it('sets correct Highcharts options for % measures', function() {
      var d = {
        data: [{x: 0, y: 60}, {x: 10, y: 0}]
      },
      options = {
        rollUpBy: 'org_id',
        globalYMax: {y: 100},
        globalYMin: {y: 10}
      },
      chartOptions = {dashOptions: { chart: {}, legend: {}}};
      var result = mu._getChartOptions(d, true,
        options, chartOptions);
      expect(result.yAxis.title.text).to.equal('%');
      expect(result.yAxis.min).to.equal(0);
      expect(result.yAxis.max).to.equal(100);
      var point = {
        x: '2015-01-01',
        point: {
          numerator: 10,
          denominator: 30,
          percentile: 60,
          y: 0.3333333
        },
        series: {
          name: 'Foo',
          options: {
            isNationalSeries: true
          }
        }
      };
      var tooltip = result.tooltip.formatter.call(point);
      var str = '<b>Foo in Jan 2015</b><br/>Measure: 0.333%';
      expect(tooltip).to.equal(str);
    });

    it('reverses the yAxis when low is bad', function() {
      var d = {
        lowIsGood: false,
        data: [{x: 0, y: 60}, {x: 10, y: 0}]
      },
      options = {
        rollUpBy: 'org_id',
        globalYMax: {y: 100},
        globalYMin: {y: 10}
      },
      chartOptions = {dashOptions: { chart: {}, legend: {}}};
      var result = mu._getChartOptions(d, true,
        options, chartOptions);
      expect(result.yAxis.reversed).to.equal(true);
      d.lowIsGood = true;
      result = mu._getChartOptions(d, true,
        options, chartOptions);
      expect(result.yAxis.reversed).not.to.equal(true);
    });

    it('sets correct Highcharts options for non-% measures', function() {
      var d = {
        data: [{x: 0, y: 90}, {x: 10, y: 10}],
        numeratorShort: 'foo',
        denominatorShort: 'bar'
      },
      options = {
        rollUpBy: 'org_id',
        globalYMax: { y: 50},
        globalYMin: { y: 0}
      },
      chartOptions = { dashOptions: { chart: {}, legend: {}}};
      var result = mu._getChartOptions(d, false,
        options, chartOptions);
      expect(result.yAxis.title.text).to.equal('Measure');
      expect(result.yAxis.min).to.equal(0);
      expect(result.yAxis.max).to.equal(90);
      var point = {
        x: '2015-01-01',
        point: {
          numerator: 10,
          denominator: 30,
          percentile: 60,
          y: 0.3333333
        },
        series: {
          name: 'Bar',
          options: {
            isNationalSeries: false
          }
        }
      };
      var tooltip = result.tooltip.formatter.call(point);
      var str = '<b>Bar in Jan 2015</b><br/>foo: 10<br/>';
      str += 'bar: 30<br/>Measure: 0.333 (60th percentile)';
      expect(tooltip).to.equal(str);
    });
  });

  describe('#getGraphOptions', function() {
    it('should amalgamate the series correctly', function() {
      var d = {
        data: [{x: 0, y: 12}, {x: 10, y: 10}],
        numeratorShort: 'foo',
        denominatorShort: 'bar',
        globalCentiles: {
          10: [{ x: 0, y: 2}, { x: 10, y: 3}],
          50: [{ x: 0, y: 45}, { x: 10, y: 46}],
          90: [{ x: 0, y: 88}, { x: 10, y: 92}],
        }
      },
      options = {
        orgType: 'CCG',
        rollUpBy: 'org_id',
        globalYMax: { y: 50},
        globalYMin: { y: 0}
      },
      chartOptions = { dashOptions: { chart: {}, legend: {}}};
      var result = mu.getGraphOptions(d, options, true, chartOptions);
      expect(result.series.length).to.equal(4);
      expect(result.series[0].name).to.equal('This CCG');
      expect(result.series[2].name).to.equal('50th percentile nationally');
      expect(result.series[2].isNationalSeries).to.equal(true);
      expect(result.series[2].dashStyle).to.equal('longdash');

    });
  });
});
