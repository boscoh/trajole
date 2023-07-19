import Vue from "vue";
import "@fortawesome/fontawesome-free/css/all.css";
import "@fortawesome/fontawesome-free/js/all.js";
import VueRouter from "vue-router";

import Vuex from "vuex";
import mystore from "./store.js";

import App from "./App.vue";
import Page from "./views/PageView.vue";
import Home from "./views/HomeView.vue";

Vue.use(VueRouter);
const routes = [
  { path: "/", component: Home },
  { path: "/foamtraj/:foamId", component: Page },
];
const router = new VueRouter({
  routes,
});

Vue.use(Vuex);
const store = new Vuex.Store(mystore);

// Vue.config.productionTip = false
new Vue({
  router,
  store,
  render: (h) => h(App),
}).$mount("#app");
