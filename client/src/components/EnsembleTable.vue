// vue component in pug
<template lang="pug">
div
  table.table(v-if="table && mode==='display'" style="cursor: pointer")
    thead(v-if="headers")
      tr
        th(v-for="h in headers")
          .d-flex.flex-nowrap(@click="sortTable(h.iCol, h.status)")
            span.me-1 {{ h.value }}
            template(v-if="h.status === 'none'")
              span.text-muted &uarr;
              span.text-muted &darr;
            template(v-if="h.status==='up'")
              span &uarr;
              span.text-muted &darr;
            template(v-if="h.status==='down'")
              span.text-muted &uarr;
              span &darr;
    tbody
      tr(
        v-for="(row, i) in table.rows"
        :key="i"
        :class="[isIFrameTrajSelected(row.iFrameTraj) ? 'bg-primary' : '']"
        @mousedown="e => downTableEntry(e, row)"
        @mouseup="e => upTableEntry(e, row)"
        @mousemove="e => moveTableEntry(e, row)"
      )
        td.text-nowrap(v-for="val in row.vals") {{val}}

  div(v-if="table && mode==='edit'")

    .d-flex.flex-row.flex-nowrap
      input.ms-2.form-control(
        style="width: 6em"
        type="number"
        v-model="foamId"
      )
      input.ms-2.form-control(
        style="width: 4em"
        type="number"
        v-model="frame"
      )
      button.ms-2.btn.btn-small.btn-outline-secondary(
        @click="add"
      )
        | Add

    table.table(style="cursor: pointer")
      thead(v-if="headers")
        tr
          th(v-if="iFoamCol !== null")
              span.me-1 {{ headers[iFoamCol].value }}
          th(v-if="iFrameCol !== null")
              span.me-1 {{ headers[iFrameCol].value }}
          th
      tbody
        tr(
          v-for="(row, i) in table.rows"
          :key="i"
          :class="[isIFrameTrajSelected(row.iFrameTraj) ? 'bg-primary' : '']"
          @mousedown="e => downTableEntry(e, row)"
          @mouseup="e => upTableEntry(e, row)"
          @mousemove="e => moveTableEntry(e, row)"
        )
          td.text-nowrap(v-if="iFoamCol !== null")
            | {{row.vals[iFoamCol]}}
          td.text-nowrap(v-if="iFrameCol !== null")
            | {{row.vals[iFrameCol]}}
          td
            i.fas.fa-trash

</template>

<style scoped></style>
<script>
import * as rpc from "../modules/rpc";
import _ from "lodash";
import * as bootstrap from "bootstrap";
import { inFrames, getIndexOfFrames, isSameVec } from "../modules/util";


export default {
  data() {
    return {
      table: {},
      mode: 'display', // 'edit'
      headers: [],
      iFoamCol: null,
      iFrameCol: null,
      iFrameTraj: null,
      iFrameTrajList: [],
      foamId: null,
      frame: null
    };
  },
  methods: {
    async loadTable(mode="display") {
      this.mode = mode
      this.$store.commit("setItem", { foamId: this.$store.state.ensembleId })
      this.$store.commit("setItem", {tags: {ensemble: this.$store.state.ensembleId + '.csv'}});

      this.$store.commit("pushLoading");
      let response = await rpc.remote.load_ensemble_id(this.$store.state.ensembleId);
      this.$store.commit("popLoading");

      let result = response.result ? response.result : null;
      this.table = result
      console.log("loadtable", _.cloneDeep(this.table))

      this.headers = _.map(result.headers, (h, i) => ({
        value: h,
        status: "none",
        iCol: i,
      }));
      this.iFoamCol = this.table.iFoamCol
      this.iFrameCol = this.table.iFrameCol

      if (this.table.rows.length) {
        return this.table.rows[0].iFrameTraj
      } else {
        return null
      }

    },

    isIFrameTrajSelected(iFrameTraj) {
      return inFrames(this.iFrameTrajList, iFrameTraj);
    },

    async selectIFrameTraj(selectIFrameTraj, thisFrameOnly) {
      console.log("selectIFrameTraj", selectIFrameTraj, `thisFrameOnly=${thisFrameOnly}`, _.cloneDeep(this.iFrameTrajList) )
      this.$store.commit("addLoad", {iFrameTraj: _.cloneDeep(selectIFrameTraj), thisFrameOnly: !!thisFrameOnly});
    },

    deleteIFrameTraj(iFrameTraj) {
      this.$store.commit("addDumpIFrameTraj", iFrameTraj)
      console.log("deleteIFrameTraj", _.cloneDeep(iFrameTraj))
    },

    async downTableEntry(event, row) {
      this.mouseDownInTable = true;
      if (!row.iFrameTraj) {
        return;
      }
      if (event.shiftKey) {
        if (inFrames(this.iFrameTrajList, row.iFrameTraj)) {
          if (this.iFrameTrajList.length > 1) {
            this.deleteIFrameTraj(row.iFrameTraj);
          }
          return;
        }
      }
      this.selectIFrameTraj(row.iFrameTraj, !event.shiftKey);
    },

    async moveTableEntry(event, row) {
      if (this.mouseDownInTable && row.iFrameTraj) {
        this.selectIFrameTraj(row.iFrameTraj, !event.shiftKey);
      }
    },

    async upTableEntry(event, row) {
      this.mouseDownInTable = false;
    },

    async sortTable(iCol, status) {
      let newStatus = "up";
      if (status === "up") {
        newStatus = "down";
      }
      for (let iCol = 0; iCol < this.headers.length; iCol += 1) {
        this.headers[iCol].status = "none";
      }
      this.headers[iCol].status = newStatus;
      if (newStatus !== "none") {
        if (iCol === 0) {
          this.table.rows = _.sortBy(this.table.rows, (row) => row.vals[iCol]);
          if (newStatus === "down") {
            this.table.rows = _.reverse(this.table.rows);
          }
        } else {
          let multiplier = newStatus === "up" ? 1 : -1;
          this.table.rows = _.sortBy(
            this.table.rows,
            (row) => multiplier * row.vals[iCol]
          );
        }
      }
    },

    async add() {
      let response = await rpc.remote.add_to_ensemble(this.$store.state.ensembleId, _.parseInt(this.foamId), _.parseInt(this.frame));
      this.loadTable(this.mode)
    }
  },
};
</script>
