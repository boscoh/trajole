import Vue from 'vue'
import '@fortawesome/fontawesome-free/css/all.css'
import '@fortawesome/fontawesome-free/js/all.js'
import VueRouter from 'vue-router'
import App from './App.vue'

import Jolecule from './components/Jolecule.vue'
import Home from './components/Home.vue'

Vue.use(VueRouter)

const routes = [
  { path: '/', component: Home },
  { path: '/foamtraj/:foamId', component: Jolecule },
]

const router = new VueRouter({
  routes
})

// Vue.config.productionTip = false
new Vue({
  router,
  render: h => h(App)
}).$mount('#app')
