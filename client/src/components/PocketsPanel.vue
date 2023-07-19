<template lang="pug">
.w-100
  button.w-100.btn.btn-sm.btn-secondary(
    @click="openPocketsModal"
  )
    | Pockets Panel
  #pockets-modal.modal.fade
    .modal-dialog
      .modal-content
        .modal-header
          h5.modal-title Pockets
          button.btn-close(data-bs-dismiss="modal")
        .modal-body
          .mb-1.d-flex.flex-row.flex-wrap
            button.mb-1.me-1.btn.btn-small.btn-secondary(
              @click="toggleAll()"
            )
              | Toggle All
          .mb-1.d-flex.flex-row.flex-wrap
            button.mb-1.me-1.btn.btn-small(
              v-for="(pocket, i) in pockets"
              :style="buttonStyle(pocket.elem)"
              @click="clickPocket(pocket.elem)"
            )
              | {{pocket.elem}}
</template>

<script>
import * as bootstrap from "bootstrap";
import * as _ from "lodash";

export default {
  data() {
    return {
      pockets: [],
    };
  },
  mounted() {
    this.pocketsModal = new bootstrap.Modal(
      document.getElementById("pockets-modal")
    );
    this.jolecule = null;
  },
  methods: {
    setJolecule(jolecule) {
      this.jolecule = jolecule;
    },
    buttonStyle(elem) {
      let soup = this.jolecule.soupView.soup;
      if (!soup.grid.isElem[elem]) {
        return "";
      } else {
        let colorHexStr = soup.getElemColorStr(elem);
        console.log("pocket elem color", elem, colorHexStr);
        return `background-color: ${colorHexStr}`;
      }
    },
    buildPockets() {
      let soup = this.jolecule.soupView.soup;
      let controller = this.jolecule.controller;
      let soupView = this.jolecule.soupView;
      let grid = this.jolecule.soupView.soup.grid;

      this.pockets = [];
      for (let elem of _.keys(grid.isElem)) {
        this.pockets.push({ elem: elem });
      }

      grid.isChanged = true;
      soupView.currentView.grid.isElem = _.cloneDeep(grid.isElem);
      soupView.isChanged = true;
      soupView.isUpdateObservers = true;
      soupView.isUpdateColors = true;
    },
    toggleAll() {
      let soup = this.jolecule.soupView.soup;
      let grid = soup.grid;
      let values = _.values(grid.isElem);
      let nAll = values.length;
      let nSelected = _.filter(values).length;
      if (nSelected === nAll) {
        for (let key of _.keys(grid.isElem)) {
          grid.isElem[key] = false;
        }
      } else {
        for (let key of _.keys(grid.isElem)) {
          grid.isElem[key] = true;
        }
      }
      this.buildPockets();
    },
    clickPocket(elem) {
      let grid = this.jolecule.soupView.soup.grid;
      grid.isElem[elem] = !grid.isElem[elem];
      this.buildPockets();
    },
    async openPocketsModal() {
      this.buildPockets();
      this.pocketsModal.show();
    },
  },
};
</script>
