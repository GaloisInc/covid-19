import Vue from 'vue'
import VueRouter, { RouteConfig } from 'vue-router'

Vue.use(VueRouter)

const routes: Array<RouteConfig> = [
  {
    path: '/',
    name: 'home',
    redirect: '/county/36061',  // 36061 - FIPS for NY, NY
  },
  {
    path: '/county/:fips',
    name: 'county-over-time',
    // route level code-splitting
    // this generates a separate chunk (about.[hash].js) for this route
    // which is lazy-loaded when the route is visited.
    component: () => import(/* webpackChunkName: "CountyOverTime" */ '../components/CountyOverTime/index.vue'),
  },
];

const router = new VueRouter({
  routes
});

export default router;
