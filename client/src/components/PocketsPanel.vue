<template lang="pug">
.w-100
  button.w-100.btn.btn-sm.btn-secondary(
    @click="openPocketsModal"
  )
    | Pockets Panel
  #pockets-modal.modal.fade
    .modal-dialog.ms-5.me-0
      .modal-content
        .modal-header
          h5.modal-title Pockets
          button.btn-close(data-bs-dismiss="modal")
        .modal-body
          .mb-2.d-flex.flex-row.align-items-center
            | Radius &angst;
            input.ms-2.form-control(
              style="width: 8em"
              type="number"
              v-model="radius"
              @input="changeRadius"
            )
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
import { v3 } from "jolecule";

export default {
  data() {
    return {
      pockets: [],
      radius: null,
    };
  },
  mounted() {
    this.pocketsModal = new bootstrap.Modal(
      document.getElementById("pockets-modal"),
    );
    this.jolecule = null;
  },
  methods: {
    setJolecule(jolecule) {
      this.jolecule = jolecule;
      this.radius = _.get(this.jolecule, "soupView.soup.grid.radiusToCenter");
    },
    changeRadius() {
      let soupView = this.jolecule.soupView;
      let soup = soupView.soup;
      soup.grid.radiusToCenter = this.radius;

      soup.grid.isChanged = true;
      soupView.isChanged = true;
      soupView.isUpdateObservers = true;
      soupView.isUpdateColors = true;
      this.buildPocketLabels();
    },
    buttonStyle(elem) {
      let soup = this.jolecule.soupView.soup;
      if (!this.isElemInRadius(elem)) {
        return "";
      } else {
        let colorHexStr = soup.getElemColorStr(elem);
        return `background-color: ${colorHexStr}`;
      }
    },
    isElemInRadius(elem) {
      let soup = this.jolecule.soupView.soup;
      let controller = this.jolecule.controller;
      let soupView = this.jolecule.soupView;
      let grid = this.jolecule.soupView.soup.grid;

      let residue = soup.getResidueProxy();
      let atom = soup.getAtomProxy();
      for (let iRes of _.range(soup.getResidueCount())) {
        residue.iRes = iRes;
        if (residue.ss === "G") {
          for (let iAtom of residue.getAtomIndices()) {
            atom.iAtom = iAtom;
            let dist = v3.distance(atom.pos, grid.center);
            if (dist > grid.radiusToCenter) {
              continue;
            }
            if (atom.atomType == elem) {
              return true;
            }
          }
        }
      }
      return false;
    },
    buildPocketLabels() {
      let grid = this.jolecule.soupView.soup.grid;
      this.pockets = [];
      for (let elem of _.keys(grid.isElem)) {
        this.pockets.push({ elem: elem });
      }
    },
    clickPocket(elem) {
      let soupView = this.jolecule.soupView;
      let soup = soupView.soup;
      let residue = soup.getResidueProxy();
      let atom = soup.getAtomProxy();
      for (let iRes of _.range(soup.getResidueCount())) {
        residue.iRes = iRes;
        if (residue.ss === "G") {
          for (let iAtom of residue.getAtomIndices()) {
            atom.iAtom = iAtom;
            if (atom.atomType == elem) {
              soupView.soup.grid.center = atom.pos;
              this.jolecule.controller.setTargetViewByIAtom(iAtom);
              soup.grid.isChanged = true;

              soupView.isChanged = true;
              soupView.isUpdateObservers = true;
              soupView.isUpdateColors = true;
            }
          }
        }
      }
      this.buildPocketLabels();
    },
    async openPocketsModal() {
      this.buildPocketLabels();
      this.pocketsModal.show();
    },
  },
};
</script>
