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

    .ms-2.mb-1
      frames-button

    .ms-2.mb-1
      button.w-100.btn.btn-sm.btn-secondary( @click="openDistPlotModal")
        | Distance Plot
      #distance-plot-modal.modal.modal-xl.fade
        .modal-dialog.mx-auto(style="max-width: none; width: calc(100vw*.9)")
          .modal-content(style="width: calc(100vw*.9)")
            .modal-header
              h5.modal-title Distance Plots (click on points)
            .modal-body.w-90
              .mb-1.d-flex.flex-row.align-items-center
                template(v-if="distances.length")
                  #distance-plot(style="width: calc(100vw*.8); height: 400px")
                template(v-else)
                  | Please select some distances
            .modal-footer
              button.btn.btn-secondary(data-bs-dismiss="modal" @click="cancel") Close

    .ms-2.mb-1
      button.w-100.btn.btn-sm.btn-secondary( @click="openContactModal")
        | Contact Map
      #contact-modal.modal.modal-xl.fade
        .modal-dialog.mx-auto(style="max-width: none; width: calc(100vw*.5); height: calc(100vh*.5)")
          .modal-content(style="width: calc(100vw*.5)")
            .modal-header
              h5.modal-title {{contactMapTitle}}
            .modal-body.w-90
              .mb-1.d-flex.flex-row.align-items-center
                template(v-if="contactMap")
                  #contact-map(style="width: calc(100vw*.4); height: calc(100vh*.4)")
                template(v-else)
                  | Contact Map only works with 1 or 2 frames selected
            .modal-footer
              button.btn.btn-secondary(data-bs-dismiss="modal" @click="cancel") Close

    toggle-text.ms-2.mb-1(:flag="isAsCommunities" @click="toggleAsCommunities()")
      | ASCommunities

    toggle-text.ms-2.mb-1(:flag="isAsPockets" @click="toggleAsPockets()")
      | ASPockets

    .ms-2.mb-1(v-show="isAsPockets || isAsCommunities")
      pockets-panel(
        ref="pocketsPanel"
      )

    button.ms-2.mb-1.btn.btn-sm.btn-secondary(@click="downloadPdb")
      | Download PDB

    .ms-2.mb-1
      json-button

    button.ms-2.mb-1.btn.btn-sm.btn-secondary(
      v-if="hasParmed" @click="downloadParmed()"
    ) Download Parmed

    button.ms-2.mb-1.btn.btn-sm.btn-secondary(
      @click="selectLigand()"
    ) Ligand

    button.ms-2.mb-1.btn.btn-sm.btn-secondary(
      v-if="minFrame !== null" @click="selectFesMinFrame()"
    ) Min Frame: {{minFrame}}

    .ps-2
      button.mt-3.btn.btn-sm.w-100.btn-secondary(
        @click="saveView"
      ) Save View

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
import { MatrixWidget } from "../modules/matrixwidget";
import { v3 } from "jolecule";

export default {
  data() {
    return {
      isAsPockets: false,
      isAsCommunities: false,
      actionWidth: `200px`,
      key: "",
      distances: [],
      contactMap: [],
      contactMapTitle: "Contact Map",
    };
  },
  components: {
    NavBar,
    JoleculeMatrixPanels,
    FramesButton,
    JsonButton,
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
    minFrame() {
      return this.$store.state.minFrame;
    },
  },
  methods: {
    async handleUrl() {
      let frames = this.$route.query.frame;
      if (frames) {
        frames = _.map(frames.split(","), _.parseInt);
      }
      let viewId = this.$route.query.view;
      let foamId = this.$route.params.foamId;
      await this.$refs.joleculeMatrix.loadFoamId(foamId, frames, viewId);
    },
    downloadPdb() {
      this.$store.commit("pushLoading");
      this.$refs.joleculeMatrix.downloadPdb();
      this.$store.commit("popLoading");
    },
    async saveView() {
      await this.$refs.joleculeMatrix.saveView();
    },
    async selectFesMinFrame() {
      let minFrame = this.$store.state.minFrame;
      if (!_.isNull(minFrame)) {
        this.$store.commit("toggleIFrameTraj", [minFrame, 0]);
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
    async openDistPlotModal() {
      let joleculeMatrix = this.$refs.joleculeMatrix;
      this.distances = joleculeMatrix.soupView.getCurrentView().distances;

      let foamId = this.$store.state.foamId;
      let remote = this.$refs.joleculeMatrix.remote;
      this.distances = await remote.get_distances(foamId, this.distances);

      let clickableFrames = [];
      if (_.has(joleculeMatrix, "matrixWidget")) {
        let grid = joleculeMatrix.matrixWidget.grid;
        let values = _.flattenDepth(grid, 2);
        for (let value of values) {
          if (_.has(value, "iFrameTraj")) {
            clickableFrames.push(value.iFrameTraj[0]);
          }
        }
      }
      if (this.distances.length) {
        let data = [];
        for (let distance of this.distances) {
          let nFrame = distance.values.length;
          let xValues = _.range(nFrame);
          let hoverTexts = [];
          for (let x of xValues) {
            let s = "";
            if (_.includes(clickableFrames, x)) {
              s += `matrix(fr=${x}) `;
            } else {
              s += `fr=${x} `;
            }
            hoverTexts.push(s);
          }
          data.push({
            x: xValues,
            y: distance.values,
            type: "lines+markers",
            mode: "lines",
            hovertemplate: "%{text}d=%{y:.1f}",
            text: hoverTexts,
            name: distance.label,
          });
        }
        let layout = {
          autosize: true,
          showlegend: true,
          title: `FoamID ${foamId}`,
          xaxis: { title: "frame" },
          yaxis: { title: "distance [Å]" },
        };
        let options = { responsive: true };
        Plotly.newPlot("distance-plot", data, layout, options);
        let myPlot = document.getElementById("distance-plot");
        myPlot.on("plotly_click", function (data) {
          for (let p of data.points) {
            joleculeMatrix.clickFrame([p.x, 0], false);
          }
        });
      }

      this.distancePlotModal = new bootstrap.Modal(
        document.getElementById("distance-plot-modal"),
      );

      this.$store.commit("setItem", { keyboardLock: true });
      this.distancePlotModal.show();
    },
    makeContactMap(iStructure) {
      let joleculeMatrix = this.$refs.joleculeMatrix;
      let soup = joleculeMatrix.jolecule.soup;
      let nRes = soup.getResidueCount();
      let residueI = soup.getResidueProxy(0);
      let residueJ = soup.getResidueProxy(0);

      const lower_cutoff = 5;
      const upper_cutoff = 10;
      const diff = upper_cutoff - lower_cutoff;

      let contactMap = [];
      for (let i = 0; i < nRes; i += 1) {
        residueI.load(i);
        if (residueI.iStructure !== iStructure) {
          continue;
        }
        if (!residueI.isPolymer) {
          continue;
        }
        const posI = soup.getAtomProxy(residueI.iAtom).pos;
        let row = [];
        for (let j = 0; j < nRes; j += 1) {
          residueJ.load(j);
          if (residueJ.iStructure !== iStructure) {
            continue;
          }
          if (!residueJ.isPolymer) {
            continue;
          }
          const posJ = soup.getAtomProxy(residueJ.iAtom).pos;
          let label =
            `${residueI.chain}${residueI.resNum}${residueI.resType}` +
            `--` +
            `${residueJ.chain}${residueJ.resNum}${residueJ.resType}`;
          const d = v3.distance(posI, posJ);
          let p = (d - lower_cutoff) / diff;
          if (p > 1) {
            p = 1;
          }
          if (p < 0) {
            p = 0;
          }
          p = 1 - p;
          row.push({
            label,
            p,
            value: d,
            iFrameTraj: [i, j],
          });
        }
        contactMap.push(row);
      }
      return contactMap;
    },
    selectContact(newValue, thisFrameOnly) {
      console.log(`selectContact`, _.cloneDeep(newValue), thisFrameOnly);
      let joleculeMatrix = this.$refs.joleculeMatrix;
      let soup = joleculeMatrix.jolecule.soup;
      let residueI = soup.getResidueProxy(newValue.iFrameTraj[0]);
      let residueJ = soup.getResidueProxy(newValue.iFrameTraj[1]);
      const posI = soup.getAtomProxy(residueI.iAtom).pos;
      const posJ = soup.getAtomProxy(residueJ.iAtom).pos;
      const pos = v3.midPoint(posI, posJ);
      let newView = joleculeMatrix.jolecule.soupView
        .getCurrentView()
        .getViewTranslatedTo(pos);
      joleculeMatrix.jolecule.controller.setTargetView(newView);
    },
    deselectContact(value) {
      console.log(`deselectContact`, _.cloneDeep(value));
    },
    async openContactModal() {
      let joleculeMatrix = this.$refs.joleculeMatrix;
      let soup = joleculeMatrix.jolecule.soup;
      const nStructure = soup.structureIds.length;
      console.log("nStructure", nStructure);
      if (nStructure === 1 || nStructure === 2) {
        this.contactMap = this.makeContactMap(0);
        this.contactMapTitle = "Contact Map";
        if (nStructure === 2) {
          this.contactMapTitle = "Contact Difference Map";
          const map1 = this.makeContactMap(1);
          const n = map1.length;
          for (let i = 0; i < n; i += 1) {
            for (let j = 0; j < n; j += 1) {
              const d0 = this.contactMap[i][j].value;
              const d1 = map1[i][j].value;
              let diff = Math.abs(d0 - d1);
              this.contactMap[i][j].value = diff;
              let p = diff / 5;
              if (p > 1) {
                p = 1;
              }
              this.contactMap[i][j].p = p;
            }
          }
        }
        if (!this.hasOwnProperty("contactWidget")) {
          this.contactWidget = new MatrixWidget(
            "#contact-map",
            this.contactMap,
            false,
          );
          this.contactWidget.selectGridValue = this.selectContact;
          this.contactWidget.deselectGridValue = this.deselectContact;
        } else {
          this.contactWidget.loadGrid(this.contactMap);
        }
      } else {
        this.contactMap = null;
      }
      this.$store.commit("setItem", { keyboardLock: true });
      this.contactModal = new bootstrap.Modal(
        document.getElementById("contact-modal"),
      );
      this.contactModal.show();
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
