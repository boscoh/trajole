import _ from "lodash";

export default {
  state() {
    return {
      foamId: "",
      tags: {},
      nLoaders: 0,
      loadingMsg: "Connecting...",
      keyboardLock: false,
      datasets: [],
      views: [],
      viewId: "",
      newView: null,
      selectView: null,
      iFrameTrajList: [],
      toClickFrame: null,
      loadIFrameTraj: null,
      dumpIFrameTraj: null,
      forceRedrawKey: "",
      minFrame: null,
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
    setItem(state, payload) {
      for (let key of _.keys(payload)) {
        state[key] = payload[key];
      }
    },

    setFoamId(state, foamId) {
      state.foamId = foamId;
    },

    setDatasets(state, datasets) {
      state.datasets = datasets;
    },

    addIFrameTraj(state, iFrameTraj) {
      let iFrameTrajList = state.iFrameTrajList;
      iFrameTrajList.push(iFrameTraj);
      state.iFrameTrajList = iFrameTrajList;
    },

    deleteIFrameTraj(state, i) {
      state.iFrameTrajList.splice(i, 1);
    },

    cleariFrameTrajList(state) {
      state.iFrameTrajList = [];
    },

    selectFrame(state, iFrame) {
      state.toClickFrame = iFrame;
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
  },
};
