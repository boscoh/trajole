import VueRouter from "vue-router";

import FoamTraj from "./FoamTraj.vue";
import HomeView from "./HomeView.vue";

const router = new VueRouter({
  routes: [
    { path: "/", component: HomeView },
    { path: "/foamtraj/:foamId", component: FoamTraj },
  ],
});

export default router;
