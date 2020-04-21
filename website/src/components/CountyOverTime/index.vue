<template lang="pug">
  v-card(class='page')
    app-header(v-on:search='onSearch', :regionSelected='regionSelected' :regions='regionsAvailable')
    v-card(class='charts')
      .chartjs-fullscreen
        div(style="position: absolute; left: 0; top: 0; bottom: 0; width: 50%")
          canvas(ref="mychart")
        div(style="position: absolute; left: 50%; top: 0; bottom: 0; width: 50%")
          canvas(ref="mychart2")
</template>

<style lang="scss">  
  @import '~vuetify/src/styles/settings/_colors.scss';

  .banner {
    position: relative;
    height: 5rem;
    
    .banner-content {
      margin-left: 2rem;
      margin-right: auto; 
      margin-top: 3rem;
      width: 20rem;
      padding: 0.5rem;
      border-radius: 1rem;
      background-color: map-get($grey, lighten-4);
      border: solid 8px map-get($orange, base);
      border-top: 0;
      border-bottom: 0;

      // Show info beside search
      display: flex;
      align-items: center;
    }
  }

  .page {
    height: 100vh;
  }
  .charts {
    position: relative;

    .chartjs-fullscreen {
      position: absolute;
      left: 0;
      top: 0;
      right: 0;
      height: 90vh;
    }
  }
</style>

<script lang="ts">
import axios, {AxiosResponse} from 'axios';
import chartjs from 'chart.js';
import Vue from 'vue';
// @ is an alias to /src

import Header from '../Header/index.vue';

export default Vue.extend({
  name: 'county-over-time',

  components: {
    'app-header': Header,
  },

  computed: {
    regionSelected: {
      get(): string { return this.$route.params.fips; },
      set(v: string) {
        this.$router.push({ name: this.$options.name, params: {fips: v}});
      },
    },
  },

  data() {
    return {
      chart: null as chartjs | null,
      chart2: null as chartjs | null,
      helpShow: false,
      regionsAvailable: new Array<[string, string]>(),
    };
  },

  watch: {
    $route() {
      this.reloadData().catch(console.error);
    },
  },

  async mounted() {
    // Initialize chart first
    const roundTooltipLabels = (places: number) => {
      const mul = 10 ** places;
      return (tooltipItem: any, data: any) => {
        let label = data.datasets[tooltipItem.datasetIndex].label || '';

        if (label) {
            label += ': ';
        }
        label += Math.round(tooltipItem.yLabel * mul) / mul;
        return label;
      };
    };
    this.chart = new chartjs.Chart((this.$refs.mychart as any).getContext('2d'), {
      type: 'line',
      options: {
        maintainAspectRatio: false,
        scales: {
          xAxes: [
            {
              type: 'time',
              time: {
                unit: 'day',
              },
            },
          ],
          yAxes: [
            {ticks: {beginAtZero: true}},
            {id: 'second-y', 
              ticks: {
                beginAtZero: true, 
                callback: (value: any) => `${value}%`,
                suggestedMin: 0,
                suggestedMax: 100,
              }, 
              position: 'right'},
          ],
        },
        tooltips: {
          mode: 'index',
          intersect: false,
          callbacks: {
            label: roundTooltipLabels(2),
          },
        },
      },
    });
    this.chart2 = new chartjs.Chart((this.$refs.mychart2 as any).getContext('2d'), {
      type: 'line',
      options: {
        maintainAspectRatio: false,
        scales: {
          xAxes: [
            {
              type: 'time',
              time: {
                unit: 'day',
              },
            },
          ],
          yAxes: [
            {
              ticks: {
                beginAtZero: true,
                callback: (value: any) => `${value}%`,
                suggestedMin: 0,
                suggestedMax: 100,
              },
            },
          ],
        },
        tooltips: {
          mode: 'index',
          intersect: false,
          callbacks: {
            label: roundTooltipLabels(2),
          },
        },
      },
    });

    // Fetch data
    const promises: [Promise<AxiosResponse<any>>, Promise<void>] = [
      axios.get('d/counties.tsv'),
      this.reloadData(),
    ];
    const responses = await Promise.all(promises);
    const response = responses[0];
    this.regionsAvailable = (response.data as string).split('\n').map(x => x.split('\t') as [string, string]);
  },

  methods: {
    onSearch(term: string) {
      this.regionSelected = term;
    },
    async reloadData() {
      const fips = this.regionSelected;
      const fipsBucket = fips.substring(0, 4);
      const url = `d/county_date_${fipsBucket}.json`;
      const resp = await axios.get(url, {responseType: 'json'});
      const county = resp.data[fips];

      for (const c of Object.keys(county)) {
        const v = county[c];
        if (!(v instanceof Array)) continue;
        county[c] = v.map(x => x === null ? NaN : x);
      }

      // Convert a few, key values to derivatives
      // (First, assert dates are contiguous.
      let dateLast = '0000-00-00';
      for (const d of county['date']) {
        if (dateLast >= d) {
          console.log(`ERROR: ${dateLast} >= ${d}`);
          break;
        }
        dateLast = d;
      }
      for (const c of ['state_test_positive', 'state_test_negative', 'cases', 'deaths']) {
        county[c + '_orig'] = county[c];

        let vBase = 0;
        let vBuffer = 0;
        // If zero, no impulse.  Otherwise, take derivative after treating signal as
        // an impulse over time rather than an impulse.
        // Sum should be same at end.
        const u = Math.exp(-1 / 5);
        county[c] = county[c].map((x: number) => {
          if (!isNaN(x)) {
            vBuffer *= u;
            vBuffer += (x - vBase) * (1 - u);
            vBase = x;
            return vBuffer;
          }
          return NaN;
        });
      }
      (window as any).county = county;

      let n = county.state_test_positive.length;
      while (isNaN(county.state_test_positive[n])) {
        n -= 1;
      }
      const testsStateMax = county.state_test_positive[n] + county.state_test_negative[n];
      const testsVolumeCount = county.state_test_positive.map((v: number, i: number) => {
        return (v + county.state_test_negative[i]);
      });
      const testsVolumeMax = Math.max.apply(null, testsVolumeCount.map((x: number) => isNaN(x) ? 0 : x));
      const testsVolume = testsVolumeCount.map((x: number) => x * 100 / testsVolumeMax);
      const testsPositive = county.state_test_positive.map((v: number, i: number) => {
        return 100 * v / (v + county.state_test_negative[i]);
      });

      const chart = this.chart!;
      chart.data.labels = county.date;
      chart.data.datasets = [
        {
          label: 'New Cases / Day',
          data: county.cases,
          backgroundColor: 'red',
          borderColor: 'red',
          fill: false,
        },
        {
          label: 'State-Wide Tests / Day, % of Maximum', 
          data: testsVolume, 
          backgroundColor: 'blue',
          borderColor: 'blue',
          fill: false,
          yAxisID: 'second-y',
        },
        {
          label: 'Deaths / Day',
          data: county.deaths,
          backgroundColor: 'rgba(0.4, 0.4, 0.4, 0.6)',
          borderColor: 'black',
          fill: true,
        },
        { // Plot mobility below deaths
          label: 'Mobility, % of Normal', 
          data: county.mobility_m50_index.map((x: number) => Math.min(100, x)), 
          backgroundColor: 'lightgrey',
          borderColor: 'grey',
          yAxisID: 'second-y',
        },
      ];
      chart.update();

      const chart2 = this.chart2!;
      chart2.data.labels = county.date;
      chart2.data.datasets = [
        {
          label: '% Testing Positive',
          data: testsPositive,
          backgroundColor: 'pink',
          borderColor: 'red',
          fill: true,
        },
      ];
      chart2.update();
    },
  },
});
</script>
