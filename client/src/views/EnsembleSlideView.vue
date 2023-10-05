<template lang="pug">
  .overflow-hidden.d-flex.flex-row.user-select-none(
    style="width: calc(100vw); height: calc(100vh); background-color: #CCC"
  )

    // Main column with nav-bar
    .flex-grow-1.d-flex.flex-column.user-select-none
      nav-bar

      .flex-grow-1(style="height: calc(100vh - 65px)")
        jolecule-matrix-panels(ref="joleculeMatrix" style="width: calc(100vw - 200px)")

    // Auxillary right action panel
    .me-2.ps-2.d-flex.flex-column(
      style="width: 200px; height: calc(100vh);"
    )

      div(:class="[isLoading ? 'overlay' : '']")

      .ps-2.my-2.w-100(style="z-index: 2002")
        loading-button

      view-manager.ms-2

</template>

<style>
.overlay {
  top: 0;
  opacity: 0.6;
  background: #aaa;
  position: absolute;
  height: 100%;
  width: 100%;
  pointer-events: visible;
  display: block;
  z-index: 1001;
}
</style>

<script>
import _ from "lodash";
import { saveBlobFile } from "../modules/util";
import * as rpc from "../modules/rpc";
import JoleculeMatrixPanels from "../components/JoleculeMatrixPanels.vue";
import FramesButton from "../components/FramesButton.vue";
import JsonButton from "../components/JsonButton.vue";
import PocketsPanel from "../components/PocketsPanel.vue";
import ViewManager from "../components/ViewManager.vue";
import LoadingButton from "../components/LoadingButton.vue";
import ToggleText from "../components/ToggleText.vue";
import NavBar from "../components/NavBar.vue";
import * as bootstrap from "bootstrap";
export default {
  data() {
    return {
      isAsPockets: false,
      isAsCommunities: false,
      actionWidth: `200px`,
      key: "",
      opt_keys: [],
      distances: [],
    };
  },
  components: {
    NavBar,
    JoleculeMatrixPanels,
    FramesButton,
    PocketsPanel,
    ViewManager,
    LoadingButton,
    ToggleText,
  },
  watch: {
    $route(to, from) {
      this.handleUrl();
    },
  },
  mounted() {
    this.handleUrl();
    this.$refs.pocketsPanel.setJolecule(this.$refs.joleculeMatrix.jolecule);
    window.addEventListener("keypress", (e) => {
      this.onkeydown(e);
    });
  },
  computed: {
    isLoading() {
      return this.$store.getters.isLoading;
    },
    hasParmed() {
      return this.$store.state.datasets.includes("parmed");
    },
  },
  methods: {
    handleUrl() {
      let ensembleId = this.$route.params.ensembleId;
      let viewId = this.$route.query.view;
      let trajs = this.$route.query.traj;
      if (trajs) {
        trajs = _.map(trajs.split(","), _.parseInt);
      }
      this.$refs.joleculeMatrix.loadEnsemble(ensembleId, viewId, trajs, "slide")
    },
    downloadPdb() {
      this.$refs.joleculeMatrix.downloadPdb();
    },
    saveView() {
      this.$refs.joleculeMatrix.saveView();
    },
    async downloadParmed() {
      this.$store.commit("pushLoading");

      let foamId = this.$store.state.foamId;
      let url = rpc.remoteUrl.replace("rpc-run", "parmed") + `/${foamId}`;
      let fname = `foamid-${foamId}`;
      let iFrameTraj = _.last(this.$store.state.iFrameTrajList);
      if (iFrameTraj) {
        let iFrame = iFrameTraj[0];
        url += `?i_frame=${iFrame}`;
        fname += `-frame-${iFrame}`;
      }
      fname += ".parmed";
      console.log(`parmed download`);
      const fetchResponse = await fetch(url, { method: "get" });
      let blob = await fetchResponse.blob();
      console.log(`downloadParmed ${url} ${fname}`, blob);
      saveBlobFile(blob, fname);

      this.$store.commit("popLoading");
    },
    selectKey(key) {
      this.$refs.joleculeMatrix.selectOptKey(key);
    },
    toggleAsCommunities() {
      this.$refs.joleculeMatrix.toggleAsCommunities();
      this.isAsPockets = this.$refs.joleculeMatrix.isAsPockets;
      this.isAsCommunities = this.$refs.joleculeMatrix.isAsCommunities;
    },
    toggleAsPockets() {
      this.$refs.joleculeMatrix.toggleAsPockets();
      this.isAsPockets = this.$refs.joleculeMatrix.isAsPockets;
      this.isAsCommunities = this.$refs.joleculeMatrix.isAsCommunities;
    },
    selectLigand() {
      this.$refs.joleculeMatrix.selectLigand();
    },
    cancel() {
      this.$store.commit("setItem", { keyboardLock: false });
    },
    onkeydown(event) {
      if (
        this.$store.state.keyboardLock ||
        window.keyboardLock ||
        event.metaKey ||
        event.ctrlKey
      ) {
        return;
      }
      let c = String.fromCharCode(event.keyCode).toUpperCase();
      if (c === "P") {
        this.toggleAsPockets();
      } else if (c === "A") {
        this.toggleAsCommunities();
      }
    },
  },
};
</script>
