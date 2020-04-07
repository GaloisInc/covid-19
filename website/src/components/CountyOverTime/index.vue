<template lang="pug">
  div(style="position: relative")
    .chartjs-fullscreen
      div(style="position: absolute; left: 0; top: 0; bottom: 0; width: 50%")
        canvas(ref="mychart")
      div(style="position: absolute; left: 50%; top: 0; bottom: 0; width: 50%")
        canvas(ref="mychart2")
    .banner
      .banner-content
        v-autocomplete(
            v-model="regionSelected"
            placeholder="Select a county"
            prepend-icon="mdi-map-search"
            :items="regionsAvailable"
            :item-text="[1]"
            :item-value="[0]"
        )
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
    }
  }

  .chartjs-fullscreen {
    position: absolute;
    left: 0;
    top: 0;
    right: 0;
    height: 100vh;
  }
</style>

<script lang="ts">
import axios, {AxiosResponse} from 'axios';
import chartjs from 'chart.js';
import Vue from 'vue';
// @ is an alias to /src

export default Vue.extend({
  name: 'county-over-time',

  components: {
    //HelloWorld: () => import('@/components/HelloWorld.vue'),
  },

  computed: {
    regionSelected: {
      get() { return this.$route.params.fips; },
      set(v: string) { this.$router.push({ name: this.$options.name, params: {fips: v}}); },
    },
  },

  data() {
    return {
      chart: null as chartjs | null,
      chart2: null as chartjs | null,
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
    async reloadData() {
      const fips = this.regionSelected;
      const fipsBucket = fips.substring(0, 4);
      const url = `d/county_date_${fipsBucket}.json`;
      const resp = await axios.get(url, {responseType: 'json'});
      const county = resp.data[fips];

      let n = county.state_test_positive.length;
      while (county.state_test_positive[n] == null) {
        n -= 1;
      }
      const testsStateMax = county.state_test_positive[n] + county.state_test_negative[n];
      const testsVolume = county.state_test_positive.map((v: number, i: number) => {
        return (v + county.state_test_negative[i]) * 100 / testsStateMax;
      });
      const testsPositive = county.state_test_positive.map((v: number, i: number) => {
        return 100 * v / (v + county.state_test_negative[i]);
      });

      const chart = this.chart!;
      chart.data.labels = county.date;
      chart.data.datasets = [
        {
          label: 'Cases', 
          data: county.cases,
          backgroundColor: 'red',
          borderColor: 'red',
          fill: false,
        },
        {
          label: 'Mobility, % of Normal', 
          data: county.mobility_m50_index.map((x: number) => Math.min(100, x)), 
          backgroundColor: 'lightgrey',
          borderColor: 'grey',
          yAxisID: 'second-y',
        },
        {
          label: 'State-Wide Testing, % of Most Recent', 
          data: testsVolume, 
          backgroundColor: 'blue',
          borderColor: 'blue',
          fill: false,
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
