// vue component in pug
<template lang="pug">
  div
    button.mb-1.btn.btn-sm.w-100.btn-secondary(
      @click="downloadParmed()" v-if="hasParmed"
    )
      | Download Parmed

    button.mb-1.btn.btn-sm.w-100.btn-secondary(
      v-if="hasMin" @click="selectFesMinFrame()") FES Min

</template>

<script>
import * as rpc from "../modules/rpc";
import _ from "lodash";
import { saveBlobFile } from "../modules/util";

export default {
  data() {
    return {};
  },
  computed: {
    hasParmed() {
      return this.$store.state.datasets.includes("parmed");
    },
    hasMin() {
      return this.$store.state.datasets.includes("json_min");
    },
  },
  methods: {
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
  },
};
</script>
