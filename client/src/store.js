import * as rpc from "./modules/rpc";
import _ from "lodash";

export default {
  state() {
    return {
      foamId: "",
      nLoaders: 0,
      keyboardLock: false,
      datasets: [],
      iFrameTrajList: [],
      selectFrame: null,
      tags: {},
      editTags: [],
      editFrames: [],
    };
  },
  getters: {
    isLoading(state) {
      return state.nLoaders > 0;
    },

    frameStr(state) {
      let values = _.map(state.iFrameTrajList, (x) => x[0]);
      return `Foam: ${state.foamId} - Frame: ${values.join(" ")}`;
    },
  },
  mutations: {
    setFoamId(state, foamId) {
      state.foamId = foamId;
    },

    setDatasets(state, datasets) {
      state.datasets = datasets;
    },

    addIFrameTraj(state, iFrameTraj) {
      state.iFrameTrajList.push(iFrameTraj);
    },

    deleteIFrameTraj(state, i) {
      state.iFrameTrajList.splice(i, 1);
    },

    cleariFrameTrajList(state) {
      state.iFrameTrajList = [];
    },

    setItem(state, payload) {
      for (let key of _.keys(payload)) {
        let value = payload[key];
        console.log(
          `setItem this.$store.state.${payload.key}=${payload.value}`
        );
        state[key] = value;
      }
    },

    toggleFrame(state, iFrameTraj) {
      state.selectFrame = iFrameTraj;
    },

    pushLoading(state) {
      state.nLoaders += 1;
    },

    popLoading(state) {
      state.nLoaders -= 1;
      if (state.nLoaders <= 0) {
        state.nLoaders = 0;
      }
    },

    addEditTag(state) {
      state.editTags.push({ key: "", value: "" });
    },

    addFrame(state, frame) {
      state.editFrames.push({ frame });
    },

    setEditFrames(state) {
      let editFrames = [];
      for (let iFrameTraj of state.iFrameTrajList) {
        editFrames.push({ frame: iFrameTraj[0] });
      }
      console.log(`setEditFrames`, editFrames);
      state.editFrames = editFrames;
    },
  },
};
