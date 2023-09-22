// vue component in pug
<template lang="pug">
.flex-grow-1.overflow-scroll.mt-1

    #edit-view-text-modal.modal.fade
      .modal-dialog
        .modal-content
          .modal-header
            h5.modal-title Edit Text Description
          .modal-body
            .mb-3(style="font-size: 0.75em") URL: {{currentUrl}}?query={{ editViewId }}
            textarea.form-control(v-model="editViewText" rows=4)
          .modal-footer
            //button.btn.btn-secondary(data-bs-dismiss="modal" @click="clearKeyboardLock") Cancel
            button.btn.btn-primary(data-bs-dismiss="modal" @click="saveViewText") Save

    .w-100.mb-1.p-2.rounded(
      style="background-color: #BBB"
      v-for="view in views"
      :key="view.id"
    )
      .d-flex.flex-row.w-100.mb-1.pt-2.pb-0.text-start(style="font-size:0.9em")
        button.btn.w-100.text-start.btn-sm.btn-secondary(
          v-if="view.id === viewId"
          @click="selectView(view)"
          :key="view.id"
        )
          .py-2(v-if="view.text")
            | {{ view.text }}
          .py-2(v-if="!view.text")
            | Click
            i.mx-2.far.fa-comment
            | to add text
        button.btn.w-100.text-start.btn-sm.btn-outline-secondary(
          @click="selectView(view)"
          v-else
        )
          .py-2
            template(v-if="view.text")
              | {{ view.text }}
            span.text-secondary(v-else)
              | Click
              i.mx-2.far.fa-comment
              | to add text
      .d-flex.flex-row.justify-content-between
        .flex-start.flex-row
          button.btn.btn-sm.btn-outline-secondary.border-0(
            @click="openEditViewModal(view)"
          )
            i.far.fa-comment
        .flex-end
          button.btn.btn-sm.btn-outline-secondary.border-0(
            @click="deleteView(view)"
          )
            i.fas.fa-trash

</template>

<script>
import { remote } from "../modules/rpc";
import _ from "lodash";
import * as bootstrap from "bootstrap";

export default {
  data() {
    return {
      currentUrl: "",
      editViewText: "",
      editViewId: "",
    };
  },
  computed: {
    foamId() {
      return this.$store.state.foamId;
    },
    viewId() {
      return this.$store.state.viewId;
    },
    views() {
      return this.$store.state.views;
    },
    newView() {
      return this.$store.state.newView;
    },
  },
  watch: {
    async newView(to, from) {
      if (!_.isNull(to)) {
        this.addView(_.cloneDeep(to));
      }
    },
  },
  mounted() {
    this.currentUrl = window.location.href.split("?")[0];
    this.modal = new bootstrap.Modal(
      document.getElementById("edit-view-text-modal")
    );
  },
  methods: {
    async selectView(view) {
      this.$store.commit("setItem", { viewId: view.id });
      this.$store.commit("setItem", { selectView: view });
    },

    pushLoading() {
      this.$store.commit("pushLoading");
    },

    popLoading() {
      this.$store.commit("popLoading");
    },

    async openEditViewModal(view) {
      this.$store.commit("setItem", { keyboardLock: true });
      this.editViewText = view.text;
      this.editViewId = view.id;
      this.currentUrl = window.location.href.split("?")[0];
      this.modal.show();
    },

    clearKeyboardLock() {
      this.$store.commit("setItem", { keyboardLock: false });
    },

    async addView(newView) {
      console.log("addView", _.cloneDeep(newView));
      await remote.update_view(this.foamId, newView);
      // NOTE: reverse chronological order insert at top
      let views = _.cloneDeep(this.views);
      views.unshift(newView);
      this.$store.commit("setItem", { views });
      this.$store.commit("setItem", { selectView: newView });
    },

    async saveViewText() {
      let view = _.find(this.views, { id: this.editViewId });
      view.foamId = this.foamId;
      view.timestamp = Math.floor(Date.now() / 1000);
      view.text = this.editViewText;
      this.pushLoading();
      await remote.update_view(this.foamId, view);
      this.popLoading();
      this.clearKeyboardLock();
    },

    async deleteView(view) {
      let views = this.views;
      let i = views.indexOf(view);
      this.pushLoading();
      await remote.delete_view(this.foamId, view);
      this.popLoading();
      views.splice(i, 1);
      this.$store.commit("setItem", { views: _.cloneDeep(views) });
      this.$store.commit("setItem", { viewId: null });
      history.pushState({}, null, "#" + this.$route.path);
    },
  },
};
</script>
