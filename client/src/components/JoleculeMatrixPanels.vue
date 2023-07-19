<template lang="pug">
  .d-flex.flex-row.h-100

      #fail-modal.modal.fade
        .modal-dialog
          .modal-content
            .modal-header
              h5.modal-title ERROR: Loading trajectory {{ foamId }}
              button.btn-close(data-bs-dismiss="modal")
            .modal-body
              pre {{ errorMsg }}

      #matrix-widget.h-100(:style="matrixStyle" :key="forceMatrixKey")
      #strip-widget.h-100(:style="stripStyle" :key="forceStripKey")
      #table.p-2.me-2.overflow-scroll(:style="tableStyle")
        ligand-table(ref="table")

      ///////////////////////
      #jolecule-container.h-100(:style="joleculeStyle")
      ///////////////////////

</template>

<script>
import "bootstrap/dist/css/bootstrap.min.css";
import * as bootstrap from "bootstrap";
import _ from "lodash";
import { initEmbedJolecule } from "jolecule";
import { MatrixWidget } from "../modules/matrixwidget";
import {
  getFirstValue,
  inFrames,
  isSameVec,
  saveBlobFile,
  saveTextFile,
  getPdbText,
} from "../modules/util";
import { aysnc_rpc } from "../modules/rpc";
import LigandTable from "./LigandTable.vue";

export default {
  components: {
    LigandTable,
  },
  data() {
    return {
      forceMatrixKey: 1,
      forceStripKey: -1,
      isAsCommunities: false,
      isAsPockets: false,
      displayMode: "", // "strip", "table", "matrix-strip", "matrix", "sparse-matrix"
      errorMsg: "",
      joleculeStyle: "height: 100%",
      tableStyle: "display: none",
      stripStyle: "display: none",
      matrixStyle: "display: none",
    };
  },
  async mounted() {
    document.oncontextmenu = _.noop;

    document.onkeydown = (e) => {
      this.onkeydown(e);
    };

    this.jolecule = initEmbedJolecule({
      divTag: "#jolecule-container",
      backgroundColor: "#CCC",
      viewId: "",
      viewHeight: 170,
      isViewTextShown: false,
      isSequenceBar: true,
      isEditable: true,
      isGrid: true,
      bCutoff: -1.0,
      isPlayable: false,
      isLegend: true,
      isToolbarOnTop: true,
    });
    this.controller = this.jolecule.soupWidget.controller;
    this.soupView = this.jolecule.soupView;

    this.stripWidth = "70px";
    this.actionsStripWidth = "200px";

    this.errorModal = new bootstrap.Modal(
      document.getElementById("fail-modal")
    );

    window.addEventListener("beforeunload", (e) => this.close());
    window.addEventListener("resize", this.resize);

    this.resize();

    this.initRemoteRpc();
  },
  computed: {
    foamId() {
      return this.$store.state.foamId;
    },
    selectFrame() {
      return this.$store.state.selectFrame;
    },
    selectView() {
      return this.$store.state.selectView;
    },
    iFrameTrajList() {
      return this.$store.state.iFrameTrajList;
    },
    loadIFrameTraj() {
      return this.$store.state.loadIFrameTraj;
    },
    dumpIFrameTraj() {
      return this.$store.state.dumpIFrameTraj;
    },
  },
  watch: {
    selectFrame(to, from) {
      if (!_.isNull(to)) {
        this.clickFrame(to, true);
      }
    },
    selectView(to, from) {
      if (!_.isNull(to)) {
        this.loadView(to);
      }
    },
    loadIFrameTraj(to, from) {
      if (!_.isNull(to)) {
        this.loadFrameIntoJolecule(to.iFrameTraj, to.thisFrameOnly);
      }
    },
    dumpIFrameTraj(to, from) {
      if (!_.isNull(to)) {
        this.deleteIFrameTraj(to);
      }
    },
  },
  methods: {
    initRemoteRpc() {
      let _this = this;

      class RemoteResultRpcProxy {
        constructor() {
          return new Proxy(this, {
            get(target, prop) {
              return async function () {
                _this.pushLoading();

                let response = await aysnc_rpc(prop, ...arguments);

                let result = null;
                if (!response.result) {
                  _this.handleError(response);
                } else {
                  result = response.result;
                }

                _this.popLoading();

                return result;
              };
            },
          });
        }
      }

      this.remote = new RemoteResultRpcProxy();
    },

    resize() {
      if (this.matrixWidget) {
        this.matrixWidget.resize();
      }
      if (this.stripWidget) {
        this.stripWidget.resize();
      }
      if (this.jolecule) {
        this.jolecule.resize();
      }
    },

    pushLoading(loadingMsg = null) {
      this.$store.commit("pushLoading");
      if (!_.isNull(loadingMsg)) {
        this.$store.commit("setItem", { loadingMsg });
      }
      this.$forceUpdate();
    },

    popLoading(loadingMsg = null) {
      this.$store.commit("popLoading");
      if (!_.isNull(loadingMsg)) {
        this.$store.commit("setItem", { loadingMsg });
      }
      this.$forceUpdate();
    },

    handleError(response) {
      if (!response.error) {
        return;
      }
      this.errorModal.show();
      if (_.last(response.error.message).includes("FileNotFoundError")) {
        this.errorMsg = `Trajectory #${this.foamId} is empty`;
      } else {
        this.errorMsg = JSON.stringify(response.error, null, 2);
      }
      this.$store.commit("setItem", {
        tags: { Error: `loading FoamId=${this.foamId}` },
      });
    },

    async getConfig(key) {
      return await this.remote.get_config(this.foamId, key);
    },

    resetWidgets() {
      this.forceMatrixKey = Math.random();
      this.forceStripKey = Math.random();
      this.$forceUpdate();
    },

    async loadFoamId(foamId, frames, viewId) {
      this.pushLoading();

      console.log(
        `loadFoamId(foamId=${foamId}, frames=${frames}, viewId=${viewId})`
      );

      document.title = "#" + foamId;
      this.$store.commit("setFoamId", foamId);

      // Clear all widgets
      this.$store.commit("setItem", { tags: {} });
      this.jolecule.clear();
      this.cacheByiFrameTraj = {};
      this.cacheAsCommunitiesByiFrameTraj = {};
      this.cacheAsPocketsByiFrameTraj = {};
      this.nStructureInFrameList = [];

      this.$store.commit("cleariFrameTrajList");

      this.resetWidgets();

      if (this.matrixWidget) {
        this.matrixWidget.iFrameTrajs = [];
        this.matrixWidget.draw();
      }
      if (this.stripWidget) {
        this.stripWidget.iFrameTrajs = [];
        this.stripWidget.draw();
      }

      let result;

      result = await this.remote.reset_foam_id(this.foamId);
      if (result) {
        this.$store.commit("setItem", { tags: result.title });
      }

      this.displayMode = await this.getConfig("mode");

      if (!this.displayMode || this.displayMode === "frame") {
        result = `width: calc(100%);`;
      } else if (this.displayMode === "strip") {
        result = `width: calc(100% - ${this.stripWidth});`;
      } else {
        result = `width: calc(50%)`;
      }
      this.joleculeStyle = result;

      if (this.displayMode === "table") {
        result = `width: calc(50%)`;
      } else {
        result = "display: none";
      }
      this.tableStyle = result;

      if (this.displayMode === "matrix-strip" || this.displayMode === "strip") {
        result = `width: ${this.stripWidth}`;
      } else {
        result = "display: none";
      }
      this.stripStyle = result;

      if (this.displayMode === "matrix-strip") {
        result = `width: calc(50% - ${this.stripWidth})`;
      } else if (
        this.displayMode === "matrix" ||
        this.displayMode === "sparse-matrix"
      ) {
        result = `width: calc(50%)`;
      } else {
        result = "display: none";
      }
      this.matrixStyle = result;

      this.$forceUpdate();

      this.loadOther();

      result = await this.remote.get_views(this.foamId);
      let initView = null;
      if (result) {
        this.views = result;
        this.$store.commit("setItem", { views: this.views });
        if (viewId && this.views) {
          let view = _.find(this.views, (v) => v.id === viewId);
          if (view) {
            initView = view;
          }
        }
      }

      if (this.displayMode === "strip") {
        await this.loadStrip();
      } else if (
        this.displayMode === "sparse-matrix" ||
        this.displayMode === "matrix"
      ) {
        await this.loadMatrix();
      } else if (this.displayMode.includes("matrix-strip")) {
        await this.loadStrip();
        await this.loadMatrix();
      } else if (this.displayMode === "table") {
        let iFrameTraj = await this.$refs.table.loadTable();
        await this.loadFrameIntoJolecule(iFrameTraj);
      } else if (this.displayMode === "frame") {
        await this.loadFrameIntoJolecule([0, 0], false);
      }

      if (initView) {
        await this.loadView(initView);
      } else {
        if (this.matrixWidget || this.stripWidget) {
          if (frames) {
            // this will clear previous initIFrameTraj
            await this.clickFrame(frames[0], false);
            for (let i = 1; i < frames.length; i += 1) {
              await this.clickFrame(frames[i], true);
            }
          }
        }
      }

      this.resize();
      this.popLoading();
    },

    async loadOther() {
      this.pushLoading();
      this.key = await this.getConfig("key");
      this.opt_keys = await this.getConfig("opt_keys");
      let datasets = await this.remote.get_json_datasets(this.foamId);
      if (datasets) {
        this.$store.commit("setDatasets", datasets);
      }
      let tags = await this.remote.get_tags(this.foamId);
      if (tags) {
        this.$store.commit("setItem", { tags });
      }
      this.popLoading();
    },

    async loadMatrix(iFrameTraj) {
      this.pushLoading("Matrix...");
      let matrix = await this.getConfig("matrix");
      this.popLoading("Connecting...");
      if (_.isEmpty(matrix)) {
        return;
      }
      let value = _.isNil(iFrameTraj) ? getFirstValue(matrix) : { iFrameTraj };
      let isSparse = this.displayMode === "sparse-matrix";
      this.matrixWidget = new MatrixWidget("#matrix-widget", matrix, isSparse);
      this.resize();
      this.matrixWidget.selectGridValue = this.selectMatrixGridValue;
      this.matrixWidget.deselectGridValue = this.deselectMatrixGridValue;
      await this.matrixWidget.clickGridValue(value);
    },

    async selectMatrixGridValue(value, thisFrameOnly = false) {
      let iFrameTraj;
      if (_.has(value, "iFrameTrajs")) {
        let label = value.label;
        let n = value.iFrameTrajs.length;
        let grid = [
          _.map(value.iFrameTrajs, (iFrameTraj, i) => ({
            p: i / n,
            label,
            iFrameTraj,
          })),
        ];
        this.stripWidget.loadGrid(grid);
        value = getFirstValue([grid]);
        await this.stripWidget.clickGridValue(value);
      }
      if (_.has(value, "iFrameTraj")) {
        iFrameTraj = value.iFrameTraj;
        if (!_.isNil(iFrameTraj)) {
          if (
            this.hasFramesInJolecule() ||
            !this.isIFrameTrajSelected(iFrameTraj)
          ) {
            await this.loadFrameIntoJolecule(iFrameTraj, thisFrameOnly);
          }
        }
      }
    },

    async deselectMatrixGridValue(value) {
      let iFrameTraj;
      if (_.has(value, "iFrameTraj")) {
        iFrameTraj = value.iFrameTraj;
      } else if (_.has(value, "iFrameTrajs")) {
        iFrameTraj = value.iFrameTrajs[0];
      }
      if (this.isIFrameTrajSelected(iFrameTraj)) {
        await this.deleteIFrameTraj(iFrameTraj);
      }
    },

    async loadStrip() {
      let strip = await this.getConfig("strip");
      if (_.isEmpty(strip)) {
        strip = [[]];
      }
      this.stripWidget = new MatrixWidget("#strip-widget", strip, false);
      this.resize();
      this.stripWidget.selectGridValue = this.selectStripGridValue;
      this.stripWidget.deselectGridValue = this.deselectStripGridValue;
      let value = getFirstValue(strip);
      if (value) {
        await this.stripWidget.clickGridValue(value);
      }
    },

    async selectStripGridValue(value, thisFrameOnly) {
      let iFrameTraj = value.iFrameTraj;
      if (_.isNil(iFrameTraj)) {
        return;
      }
      if (
        this.hasFramesInJolecule() ||
        !this.isIFrameTrajSelected(iFrameTraj)
      ) {
        await this.loadFrameIntoJolecule(iFrameTraj, thisFrameOnly);
      }
    },

    async deselectStripGridValue(value) {
      let iFrameTraj = value.iFrameTraj;
      if (this.isIFrameTrajSelected(iFrameTraj)) {
        await this.deleteIFrameTraj(iFrameTraj);
      }
    },

    isIFrameTrajSelected(iFrameTraj) {
      return inFrames(this.iFrameTrajList, iFrameTraj);
    },

    async getPdbLines(iFrameTraj) {
      this.pushLoading("Frames...");
      let key = `${iFrameTraj[0]}-${iFrameTraj[1]}`;
      let result = [];
      if (this.isAsCommunities) {
        if (key in this.cacheAsCommunitiesByiFrameTraj) {
          console.log(
            `getPdbLines from cacheAsCommunitiesByiFrameTraj[${key}]`
          );
          result = this.cacheAsCommunitiesByiFrameTraj[key];
        } else {
          let response = await this.remote.get_pdb_lines_with_as_communities(
            this.foamId,
            iFrameTraj
          );
          if (response) {
            this.cacheAsCommunitiesByiFrameTraj[key] = response;
            result = response;
          }
        }
      } else if (this.isAsPockets) {
        if (key in this.cacheAsPocketsByiFrameTraj) {
          console.log(`getPdbLines from cacheAsPocketsByiFrameTraj[${key}]`);
          result = this.cacheAsPocketsByiFrameTraj[key];
        } else {
          let response = await this.remote.get_pdb_lines_with_as_pockets(
            this.foamId,
            iFrameTraj
          );
          if (response) {
            this.cacheAsPocketsByiFrameTraj[key] = response;
            result = response;
          }
        }
      } else {
        if (key in this.cacheByiFrameTraj) {
          console.log(`getPdbLines from cacheByiFrameTraj[${key}]`);
          result = this.cacheByiFrameTraj[key];
        } else {
          let response = await this.remote.get_pdb_lines(
            this.foamId,
            iFrameTraj
          );
          if (response) {
            this.cacheByiFrameTraj[key] = response;
            result = response;
          }
        }
      }
      this.popLoading("Connecting...");
      return result;
    },

    hasFramesInJolecule() {
      return this.nStructureInFrameList.length;
    },

    rewriteUrlWithFrames() {
      let values = _.map(this.iFrameTrajList, (x) => x[0]);
      history.pushState(
        {},
        null,
        "#" + this.$route.path + "?frame=" + values.join(",")
      );
    },

    async loadFrameIntoJolecule(iFrameTraj, thisFrameOnly = false) {
      if (this.isFetching) {
        return;
      }
      this.isFetching = true;
      let pdbLines = await this.getPdbLines(iFrameTraj);
      if (pdbLines) {
        let saveCurrentView = null;
        let pdbId = `frame-${iFrameTraj}`.replace(",", "-");
        let soup = this.jolecule.soupWidget.soup;
        let nStructurePrev = soup.structureIds.length;
        if (nStructurePrev > 0) {
          saveCurrentView = this.jolecule.soupView.getCurrentView();
        }
        console.log(`loadFrameIntoJolecule load`, pdbId);
        await this.jolecule.asyncAddDataServer(
          {
            version: 2,
            pdbId: pdbId,
            format: "pdb",
            asyncGetData: async () => pdbLines.join("\n"),
            asyncGetViews: async () => [],
            async asyncSaveViews() {},
            async asyncDeleteViews() {},
          },
          false
        );

        let nStructureInThisFrame = soup.structureIds.length - nStructurePrev;
        if (thisFrameOnly && this.hasFramesInJolecule()) {
          let iLastStructureToDelete =
            soup.structureIds.length - 1 - nStructureInThisFrame;
          for (let i = iLastStructureToDelete; i >= 0; i -= 1) {
            console.log(`loadFrameIntoJolecule delete`, soup.structureIds[i]);
            this.jolecule.controller.deleteStructure(i);
          }
          this.nStructureInFrameList = [];
          this.$store.commit("cleariFrameTrajList");
        }
        this.nStructureInFrameList.push(nStructureInThisFrame);
        this.$store.commit("addIFrameTraj", iFrameTraj);

        if (saveCurrentView) {
          this.jolecule.soupView.setHardCurrentView(saveCurrentView);
        }
        this.jolecule.soupWidget.distanceMeasuresWidget.drawFrame();
        if (!this.isAsCommunities && !this.isAsPockets) {
          this.clearGridDisplay();
        }
        this.jolecule.soupWidget.buildScene();
      }
      this.isFetching = false;
      this.rewriteUrlWithFrames();
    },

    async reloadLastFrameOfJolecule() {
      if (this.isFetching) {
        return;
      }
      this.isFetching = true;
      let iFrameTraj = _.last(this.iFrameTrajList);
      console.log(`reloadLastFrameOfJolecule`, this.iFrameTrajList, iFrameTraj);
      let pdbLines = await this.getPdbLines(iFrameTraj);
      if (pdbLines) {
        let saveCurrentView = this.jolecule.soupView.getCurrentView();

        let pdbId = `frame-${iFrameTraj}`.replace(",", "-");
        let soup = this.jolecule.soup;
        let structureId = _.last(soup.structureIds);
        await this.jolecule.asyncAddDataServer(
          {
            version: 2,
            pdbId: pdbId,
            format: "pdb",
            asyncGetData: async () => pdbLines.join("\n"),
            asyncGetViews: async () => [],
            async asyncSaveViews() {},
            async asyncDeleteViews() {},
          },
          false
        );
        soup.structureIds[soup.structureIds.length - 1] = structureId;

        let nStructure = _.last(this.nStructureInFrameList);
        let i = this.iFrameTrajList.length - 1;
        await this.deleteItemFromIFrameTrajList(i);
        this.nStructureInFrameList.splice(i, 1);
        this.$store.commit("deleteIFrameTraj", i);
        this.nStructureInFrameList.push(nStructure);
        this.$store.commit("addIFrameTraj", iFrameTraj);

        this.jolecule.soupView.setHardCurrentView(saveCurrentView);
        this.jolecule.soupWidget.distanceMeasuresWidget.drawFrame();
        if (!this.isAsCommunities && !this.isAsPockets) {
          this.clearGridDisplay();
        }
        this.jolecule.soupWidget.buildScene();
      }
      this.isFetching = false;
    },

    async deleteIFrameTraj(delIFrameTraj) {
      let i = _.findIndex(this.iFrameTrajList, (iFrameTraj) =>
        isSameVec(iFrameTraj, delIFrameTraj)
      );
      if (!_.isNil(i)) {
        await this.deleteItemFromIFrameTrajList(i);
      }
      this.rewriteUrlWithFrames();
    },

    async deleteItemFromIFrameTrajList(i) {
      let nStructureBefore = _.sum(this.nStructureInFrameList.slice(0, i));
      let nStructureToDelete = this.nStructureInFrameList[i];
      let soup = this.jolecule.soupWidget.soup;
      while (nStructureToDelete) {
        let iStructureToDelete = nStructureBefore + nStructureToDelete - 1;
        let structureId = soup.structureIds[iStructureToDelete];
        this.jolecule.controller.deleteStructure(iStructureToDelete);
        console.log(
          `deleteIFromIFrameTrajList ${iStructureToDelete}:${structureId}`
        );
        nStructureToDelete -= 1;
      }
      this.jolecule.soupWidget.buildScene();
      this.$store.commit("deleteIFrameTraj", i);
      this.nStructureInFrameList.splice(i, 1);
    },

    downloadPdb() {
      let text = getPdbText(this.jolecule, `Foamid:${this.foamId}`);

      let filename = `foamid-${this.foamId}`;
      let iFrameTraj = _.last(this.iFrameTrajList);
      if (iFrameTraj) {
        let iFrame = iFrameTraj[0];
        filename += `-frame-${iFrame}`;
      }
      filename += ".pdb";

      saveTextFile(text, filename);
    },

    async loadView(view) {
      if (_.has(view, "matrixWidgetValues")) {
        await this.matrixWidget.loadValues(view.matrixWidgetValues);
      }
      if (_.has(view, "stripWidgetValues")) {
        await this.stripWidget.loadValues(view.stripWidgetValues);
      }
      let newView = this.jolecule.soupView.getCurrentView();
      newView.setFromDict(view.viewDict);
      this.controller.setTargetView(newView);
      history.pushState({}, null, "#" + this.$route.path + "?view=" + view.id);
    },

    async saveView() {
      let viewDict = this.jolecule.soupView.getCurrentView().getDict();
      let view = {
        id: viewDict.view_id.replace("view:", ""),
        foamId: this.foamId,
        timestamp: Math.floor(Date.now() / 1000),
        viewDict: viewDict,
        text: "",
        imgs: "",
      };
      if (this.matrixWidget) {
        view.matrixWidgetValues = this.matrixWidget.values;
      }
      if (this.stripWidget) {
        view.stripWidgetValues = this.stripWidget.values;
      }
      this.$store.commit("setItem", { newView: view });
    },

    clearGridDisplay() {
      let grid = this.jolecule.soupView.soup.grid;
      grid.isElem = {};
      grid.isChanged = true;
      this.jolecule.soupView.isUpdateColors = true;
      this.jolecule.soupWidget.buildScene();
    },

    async toggleAsCommunities() {
      this.isAsCommunities = !this.isAsCommunities;
      this.$forceUpdate();
      if (!this.isAsCommunities) {
        this.clearGridDisplay();
      } else {
        this.isAsPockets = false;
      }
      this.reloadLastFrameOfJolecule();
    },

    async toggleAsPockets() {
      this.isAsPockets = !this.isAsPockets;
      this.$forceUpdate();
      if (!this.isAsPockets) {
        this.clearGridDisplay();
      } else {
        this.isAsCommunities = false;
      }
      this.reloadLastFrameOfJolecule();
    },

    async selectOptKey(key) {
      let iFrameTraj = _.last(this.iFrameTrajList);
      console.log("selectOptKey", key, iFrameTraj);
      await this.remote.select_new_key(this.foamId, key);
      this.resetWidgets();
      await this.loadMatrix(iFrameTraj);
    },

    async close() {
      await this.remote.kill();
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
      if (c === "V") {
        this.createView();
      } else if (c === "K" || event.keyCode === 37) {
        this.controller.setTargetToPrevResidue();
      } else if (c === "J" || event.keyCode === 39) {
        this.controller.setTargetToNextResidue();
      } else if (c === "S") {
        this.controller.toggleShowOption("sphere");
      } else if (c === "B") {
        this.controller.toggleShowOption("backbone");
      } else if (c === "R") {
        this.controller.toggleShowOption("ribbon");
      } else if (c === "L") {
        this.controller.toggleShowOption("ligands");
      } else if (c === "H") {
        this.controller.toggleShowOption("hydrogen");
      } else if (c === "W") {
        this.controller.toggleShowOption("water");
      } else if (c === "T") {
        this.controller.toggleShowOption("transparent");
      } else if (c === "N") {
        this.controller.toggleResidueNeighbors();
      } else if (c === "C") {
        this.controller.toggleSelectedSidechains();
      } else if (c === "X") {
        let iAtom = this.soupView.getICenteredAtom();
        if (iAtom >= 0) {
          let atom = this.soupView.soup.getAtomProxy(iAtom);
          this.controller.selectResidue(atom.iRes);
        }
      } else if (c === "A") {
        this.toggleAsCommunities();
        event.preventDefault();
      } else if (event.keyCode === 27) {
        this.controller.clear();
      } else if (c === "Z" || event.keyCode === 13) {
        this.controller.zoomToSelection();
      } else if (event.key == "Escape") {
        this.controller.clear();
      }
    },

    async clickFrame(iFrame, isShift = true) {
      console.log(`clickFrame ${iFrame}`);
      let widget;
      if (this.matrixWidget) {
        widget = this.matrixWidget;
      } else if (this.stripWidget) {
        widget = this.stripWidget;
      } else {
        this.loadFrameIntoJolecule([iFrame, 0]);
        return;
      }
      let getMatrixValue = (iFrameTraj) => {
        let value = null;
        let grid = widget.grid;
        let nCol = widget.grid.length;
        let nRow = widget.grid[0].length;
        for (let i = 0; i < nCol; i += 1) {
          for (let j = 0; j < nRow; j += 1) {
            let isMatch = false;
            let gridValue = grid[i][j];
            if (!grid[i][j].iFrameTraj) {
              continue;
            }
            let iFrameTrajCell = grid[i][j].iFrameTraj;
            let thisMatch =
              iFrameTraj[0] == iFrameTrajCell[0] &&
              iFrameTraj[1] == iFrameTrajCell[1];
            if (thisMatch) {
              return gridValue;
            }
          }
        }
        return null;
      };

      let iFrameTraj = [iFrame, 0];
      let value = getMatrixValue(iFrameTraj);
      if (!value) {
        return;
      }

      await widget.clickGridValue(value, isShift);
    },
  },
};
</script>
