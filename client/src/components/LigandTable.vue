// vue component in pug
<template lang="pug">
// Table of Ligands
table.table(v-if="table" style="cursor: pointer")
  thead(v-if="tableHeaders")
    tr
      th.bg-transparent(v-for="h in tableHeaders")
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
      v-for="(row, i) in table"
      :key="i"
      :class="[isIFrameTrajSelected(row.iFrameTraj) ? 'bg-primary' : '']"
      @mousedown="e => downTableEntry(e, row)"
      @mouseup="e => upTableEntry(e, row)"
      @mousemove="e => moveTableEntry(e, row)"
    )
      td.bg-transparent(:class="[isIFrameTrajSelected(row.iFrameTraj) ? 'bg-primary' : '']" v-for="val in row.vals" style="background-color: auto") {{val}}
</template>

<style scoped>
.bg-transparent {
  background-color: transparent;
}
</style>
<script>
import * as rpc from "../modules/rpc";
import _ from "lodash";
import * as bootstrap from "bootstrap";
import { inFrames } from "../modules/util";

export default {
  data() {
    return {
      table: [],
      tableHeaders: [],
      iFrameTraj: null,
    };
  },
  computed: {
    editTags() {
      return this.$store.state.editTags;
    },
    iFrameTrajList() {
      return this.$store.state.iFrameTrajList;
    },
  },
  mounted() {
    this.editTagsModal = new bootstrap.Modal(
      document.getElementById("edit-tags-modal"),
    );
  },
  methods: {
    async getConfig(key) {
      this.$store.commit("pushLoading");
      let response = await rpc.remote.get_config(this.$store.state.foamId, key);
      this.$store.commit("popLoading");
      return response.result ? response.result : null;
    },

    async loadTable() {
      this.table = await this.getConfig("table");
      if (_.isEmpty(this.table)) {
        return;
      }
      let headers = await this.getConfig("table_headers");
      if (headers) {
        this.tableHeaders = _.map(headers, (h, i) => ({
          value: h,
          status: "none",
          iCol: i,
        }));
      }
      let values = _.filter(_.flattenDeep(this.table), (v) =>
        _.has(v, "iFrameTraj"),
      );
      return _.first(values).iFrameTraj;
    },

    isIFrameTrajSelected(iFrameTraj) {
      return inFrames(this.iFrameTrajList, iFrameTraj);
    },

    async selectTableiFrameTraj(iFrameTraj, thisFrameOnly) {
      console.log("selectTableiFrameTraj", iFrameTraj);
      this.$store.commit("addLoad", { iFrameTraj, thisFrameOnly });
    },

    async deleteIFrameTraj(iFrameTraj) {
      console.log("commit");
      this.$store.commit("setItem", { dumpIFrameTrajList: [iFrameTraj] });
    },

    async downTableEntry(event, row) {
      console.log("downTableEntry");
      this.mouseDownInTable = true;
      if (event.shiftKey) {
        if (inFrames(this.iFrameTrajList, row.iFrameTraj)) {
          if (this.iFrameTrajList.length > 1) {
            await this.deleteIFrameTraj(row.iFrameTraj);
          }
          return;
        }
      }
      this.selectTableiFrameTraj(row.iFrameTraj, !event.shiftKey);
    },

    async moveTableEntry(event, row) {
      if (this.mouseDownInTable) {
        this.selectTableiFrameTraj(row.iFrameTraj, !event.shiftKey);
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
      for (let iCol = 0; iCol < this.tableHeaders.length; iCol += 1) {
        this.tableHeaders[iCol].status = "none";
      }
      this.tableHeaders[iCol].status = newStatus;
      if (newStatus !== "none") {
        if (iCol === 0) {
          this.table = _.sortBy(this.table, (row) => row.vals[iCol]);
          if (newStatus === "down") {
            this.table = _.reverse(this.table);
          }
        } else {
          let multiplier = newStatus === "up" ? 1 : -1;
          this.table = _.sortBy(
            this.table,
            (row) => multiplier * row.vals[iCol],
          );
        }
      }
    },
  },
};
</script>
