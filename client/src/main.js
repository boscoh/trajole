import Vue from 'vue'
import '@fortawesome/fontawesome-free/css/all.css'
import '@fortawesome/fontawesome-free/js/all.js'
import VueRouter from 'vue-router'
import App from './App.vue'
import Vuex from 'vuex'

import Jolecule from './components/Jolecule.vue'
import Home from './components/Home.vue'
import JsonDisplay from './components/JsonDisplay.vue'

Vue.use(Vuex)

// Create a new store instance.
const store = new Vuex.Store({
  state () {
    return {
      count: 0
    }
  },
  mutations: {
    increment (state) {
      state.count++
    }
  }
})


Vue.use(VueRouter)

const routes = [
  { path: '/', component: Home },
  { path: '/foamtraj/:foamId', component: Jolecule },
  { path: '/json/:foamId', component: JsonDisplay }
]

const router = new VueRouter({
  routes
})

// Vue.config.productionTip = false
new Vue({
  router,
  store: store,
  render: h => h(App),
}).$mount('#app')
