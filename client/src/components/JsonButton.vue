<template lang="pug">
  div
    button.mb-1.btn.btn-sm.w-100.btn-secondary(
      @click="openJsonModal"
    ) JSON

    #json-modal.modal.fade
      .modal-dialog.modal-xl
        .modal-content
          .modal-header
            h5.modal-title JSON Datasets
            button.btn-close(data-bs-dismiss="modal")
          .modal-body
            .d-flex.flex-row(style="height: calc(var(--vh) - 220px)")
              .h-100.overflow-scroll
                ul.list-group.justify-content-between(v-for="key in keys")
                  li.list-group-item(
                      style="cursor: pointer"
                      @click="loadContent(key)"
                      :class="{active: key === selectKey}"
                  )
                    | {{ key }}
              .h-100.ms-2.p-2.overflow-scroll.bg-white.flex-grow-1
                  pre(style="user-select: text;") {{ content }}
</template>

<script>
import * as bootstrap from "bootstrap";
import _ from "lodash";
import * as rpc from "../modules/rpc";

export default {
  data() {
    return {
      selectKey: "",
      content: "",
    };
  },
  async mounted() {
    this.jsonModal = new bootstrap.Modal(document.getElementById("json-modal"));
  },
  computed: {
    keys() {
      return _.filter(this.$store.state.datasets, (k) => k.includes("json"));
    },
  },
  methods: {
    async openJsonModal() {
      if (this.keys.length > 0) {
        this.loadContent(this.keys[0]);
      }
      this.jsonModal.show();
    },

    async loadContent(key) {
      this.content = "";
      this.selectKey = key;
      this.$store.commit("pushLoading");
      let response = await rpc.remote.get_json(this.$store.state.foamId, key);
      if (response.result) {
        this.content = JSON.stringify(response.result, null, 2);
      }
      this.$store.commit("popLoading");
    },
  },
};
</script>
