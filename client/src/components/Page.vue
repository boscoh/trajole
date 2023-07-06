<template lang="pug">
  .overflow-hidden.d-flex.flex-row.user-select-none(
    style="width: calc(100vw); height: calc(100vh); background-color: #CCC"
  )

    // Main column with nav-bar
    .flex-grow-1.d-flex.flex-column.user-select-none
      nav-bar

      .flex-grow-1(style="height: calc(var(--vh) - 65px)")
        jolecule(ref="jolecule" :style="joleculeStyle")

    // Auxillary right action panel
    .me-2.d-flex.flex-column(:style="actionsStripStyle")

      div(:class="[isLoading ? 'overlay' : '']")

      .ps-2

        .my-2(style="z-index: 2002; height: 50px; position: relative")
          loading-button

        frames-button

        // Dropdown for energy components
        select.ms-2.form-select.form-select-sm(
          v-if="opt_keys.length" v-model="key" @change="selectKey(key)"
        )
          option(v-for="k in opt_keys" :value="k") {{k}}

        toggle-text(:flag="isAsCommunities" @click="toggleAsCommunities()")
          | ASCommunities

        toggle-text(:flag="isAsPockets" @click="toggleAsPockets()")
          | ASPockets

        button.mb-1.btn.btn-sm.w-100.btn-secondary(@click="downloadPdb")
          | Download PDB

        json-button

        button.mb-1.btn.btn-sm.w-100.btn-secondary(
          v-if="hasParmed" @click="downloadParmed()"
        ) Download Parmed

        button.mb-1.btn.btn-sm.w-100.btn-secondary(
          v-if="hasMin" @click="selectFesMinFrame()"
        ) FES Min

        button.mt-3.btn.btn-sm.w-100.btn-secondary(
          @click="saveView"
        ) Save View

        view-manager

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
import Jolecule from "./Jolecule.vue";
import FramesButton from "./FramesButton.vue";
import JsonButton from "./JsonButton.vue";
import ViewManager from "./ViewManager.vue";
import LoadingButton from "./LoadingButton.vue";
import ToggleText from "./ToggleText.vue";
import NavBar from "./NavBar.vue";

export default {
  data() {
    return {
      isAsCommunities: false,
      isAsPockets: false,
      actionWidth: `200px`,
      key: "",
      opt_keys: [],
    };
  },
  components: {
    Jolecule,
    FramesButton,
    JsonButton,
    ViewManager,
    LoadingButton,
    ToggleText,
    NavBar,
  },
  watch: {
    $route(to, from) {
      this.handleUrl();
    },
  },
  mounted() {
    window.addEventListener("resize", this.resize);

    this.handleUrl();
  },
  computed: {
    isLoading() {
      return this.$store.getters.isLoading;
    },
    joleculeStyle() {
      return `width: calc(100vw - ${this.actionWidth});`;
    },
    actionsStripStyle() {
      return `width: ${this.actionWidth}`;
    },
    hasParmed() {
      return this.$store.state.datasets.includes("parmed");
    },
    hasMin() {
      return this.$store.state.datasets.includes("json_min");
    },
  },
  methods: {
    resize() {
      let vh = window.innerHeight;
      document.documentElement.style.setProperty("--vh", `${vh}px`);
    },
    handleUrl() {
      let frames = this.$route.query.frame;
      if (frames) {
        frames = _.map(frames.split(","), _.parseInt);
      }
      let viewId = this.$route.query.view;
      let foamId = this.$route.params.foamId;
      this.$refs.jolecule.loadFoamId(foamId, frames, viewId);
    },
    downloadPdb() {
      this.$refs.jolecule.downloadPdb();
    },
    saveView() {
      this.$refs.jolecule.saveView();
    },
    async selectFesMinFrame() {
      let foamId = this.$store.state.foamId;
      let response = await rpc.remote.get_min_frame(foamId);
      if (response.result) {
        console.log(
          `selectFesMinFrame foamId=${foamId} frame=${response.result}`
        );
        this.$store.commit("toggleFrame", response.result);
      }
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
      this.$refs.jolecule.selectOptKey(key);
    },
    toggleAsCommunities() {
      this.$refs.jolecule.toggleAsCommunities();
      this.isAsPockets = this.$refs.jolecule.isAsPockets;
      this.isAsCommunities = this.$refs.jolecule.isAsCommunities;
    },
    toggleAsPockets() {
      this.$refs.jolecule.toggleAsPockets();
      this.isAsPockets = this.$refs.jolecule.isAsPockets;
      this.isAsCommunities = this.$refs.jolecule.isAsCommunities;
    },
  },
};
</script>
