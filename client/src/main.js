import Vue from 'vue'
import '@fortawesome/fontawesome-free/css/all.css'
import '@fortawesome/fontawesome-free/js/all.js'
import VueRouter from 'vue-router'

import Vuex from 'vuex'
import mystore from './store.js'

import App from './App.vue'
import FoamTraj from './views/FoamTraj.vue'
import HomeView from './views/HomeView.vue'
import EnsembleListView from './views/EnsembleListView.vue'
import EnsembleView from './views/EnsembleView.vue'
import EditEnsembleView from './views/EditEnsembleView.vue'

Vue.use(VueRouter)
const routes = [
  { path: '/', component: HomeView },
  { path: '/ensembles', component: EnsembleListView },
  { path: '/ensemble/:ensembleId', component: EnsembleView },
  { path: '/editensemble/:ensembleId', component: EditEnsembleView },
  { path: '/foamtraj/:foamId', component: FoamTraj }
]
const router = new VueRouter({
  routes
})

Vue.use(Vuex)
const store = new Vuex.Store(mystore)

// Vue.config.productionTip = false
new Vue({
  router,
  store,
  render: h => h(App)
}).$mount('#app')
