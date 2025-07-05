import "@fortawesome/fontawesome-free/css/all.css";
import "@fortawesome/fontawesome-free/js/all.js";

import Vue from "vue";

import Vuex from "vuex";
import mystore from "./store.js";
Vue.use(Vuex);

import VueRouter from "vue-router";
import router from "./views/router.js";
Vue.use(VueRouter);

import App from "./App.vue";

const store = new Vuex.Store(mystore);
// Vue.config.productionTip = false
new Vue({
  router,
  store,
  render: (h) => h(App),
}).$mount("#app");
