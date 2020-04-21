<template lang="pug">
  header.header
    v-app-bar(dark, color='#2d78bd')
      v-app-bar-nav-icon(@click.stop='drawer = !drawer')
      v-toolbar-title Mobility, Cases, and Testing
      v-spacer
      v-autocomplete(
          v-if='isHome'
          v-model='selectedCountyModel'
          placeholder='Select a county'
          :items='regions'
          :item-text="[1]"
          :item-value="[0]"
          class='mx-4'
          flat
          hide-no-data
          hide-details
          solo-inverted
      )
    v-navigation-drawer(
          v-model='drawer'
          absolute
          bottom
          temporary
          width='60'
    )
      v-list(nav, dense, class='nav-menu')
        v-list-item-group(active-class='deep-purple--text text--accent-4')
          v-list-item
              v-tooltip(right)
                  template(v-slot:activator='{ on }')
                      router-link(to='/')
                          v-icon(v-on='on') mdi-home
                  span Home
          v-list-item
              v-tooltip(right)
                  template(v-slot:activator='{ on }')
                      v-btn(icon, max-width='24', @click.stop='showAboutDialog = !showAboutDialog; drawer = false')
                          v-icon(v-on='on') mdi-information
                  span About
          v-list-item
              v-tooltip(right)
                  template(v-slot:activator='{ on }')
                      a(href='d/data.xlsx', @click='drawer = false')
                          v-icon(v-on='on') mdi-download
                  span Download an .xslx file of all the data
    v-dialog(v-model='showAboutDialog', max-width='50vw')
      v-card(class='pa-5')
        v-card-text
          p(class='display-1 text--primary')  Mobility, Cases, and Testing
          p COVID-19 is still spreading to new cases, but is testing keeping up with the spread of the disease?  Shown here is mobility, known-positive-cases of COVID-19, and volume of testing administered, plotted for different US counties.
          p While mobility data from Descartes Labs corroborates that the public adhered to shelter-in-place orders, the number of positive cases was rising linearly with the amount of testing.  This could be further seen by looking at the percentage of tests coming back positive over time - when that percentage was increasing over time, the disease was spreading faster than testing was being rolled out.
          p What this means: we did not actually know the percentage of population affected by COVID-19 in some states, such as New York before April 6th, or Michigan before April 14th.  The disease’s spread was outpacing testing efforts.  On the other hand, states such as Oregon, California, and Florida appear to have administered adequate testing during those times. 
          p The information for this dashboard comes from several sources, including:
          div.my-2
            v-btn(text, color='primary accent-4', href='https://github.com/nytimes/covid-19-data') the New York Times' GitHub Repository
          div.my-2
            v-btn(text, color='primary accent-4', href='https://github.com/descarteslabs/DL-COVID-19') Descartes Labs' GitHub Repository
          div.my-2
            v-btn(text, color='primary accent-4', href='https://www.ers.usda.gov/data-products/county-level-data-sets/download-data/') the USDA's County-Level Datasets
          div.my-2
            v-btn(text, color='primary accent-4', href='https://covidtracking.com/api') CovidTracking.com's API
</template>

<style lang="scss">
    .nav-menu {
        overflow-y: visible;
        a {
            text-decoration: none;
        }
    }
</style>

<script lang="ts">
    import Vue from 'vue';

    export default Vue.component('app-header', {
        props: {
          regions: {
            default: (): Array<Array<string>> => ([])
          },
          regionSelected: {
            default: '',
          },
        },
        computed: {
          isHome(): boolean {
            return this.$route.name === 'county-over-time';
          },
          selectedCountyModel: {
            get(): string { return this.$props.regionSelected; },
            set(selection: string): string {
              this.$emit('search', selection);
              return selection;
            },
          },
        },
        data: () => ({
          showAboutDialog: false,
          drawer: false,
        }),
    });
</script>
