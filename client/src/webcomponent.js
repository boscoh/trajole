import Vue from "vue";
import "@fortawesome/fontawesome-free/css/all.css";
import "@fortawesome/fontawesome-free/js/all.js";
import VueRouter from "vue-router";
import App from "./App.vue";
import Vuex from "vuex";

import Jolecule from "./components/Jolecule.vue";
import Home from "./components/Home.vue";
import mystore from "./store.js";
Vue.use(Vuex);

Vue.use(VueRouter);

const routes = [
  { path: "/", component: Home },
  { path: "/foamtraj/:foamId", component: Jolecule },
];

const router = new VueRouter({
  routes,
});

const store = new Vuex.Store(mystore);

// Vue.config.productionTip = false
new Vue({
  router,
  store: store,
  render: (h) => h(App),
}).$mount("#app");
