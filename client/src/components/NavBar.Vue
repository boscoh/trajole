// vue component in pug
<template lang="pug">
  .d-flex.flex-row.justify-content-between.m-2(style="height: 50px")

    // Home button
    router-link.btn.btn-sm.btn-secondary.me-3(
      to="/" tag="button" style="font-size: 1.5em; width: 50px; height: 100%;"
    )
      i.fas.fa-home

    // Tags display
    .flex-grow-1.overflow-hidden.w-100(style="height: 50px")

      //Tags
      .d-flex.flex-row.flex-wrap.text-wrap(
        style="font-family: monospace; line-height: 1.1em; font-size: 15px;"
      )
        template(v-for="(key) in Object.keys($store.state.tags)")
          span(style="color: #888") {{key}}:
          | {{ $store.state.tags[key] }}&nbsp;

        span &nbsp;

        span.text-secondary(@click="openTagModal")
          i.fas.fa-edit

    #edit-tags-modal.modal.fade
      .modal-dialog
        .modal-content
          .modal-header
            h5.modal-title Edit Text Description
          .modal-body
            .mb-1.d-flex.flex-row.align-items-center(
              v-for="(editTag, iTag) in editTags"
            )
              input.form-control.w-25(v-model="editTag.key")
              input.form-control.w-75(v-model="editTag.value")
              .ms-2.a(@click="removeTag(iTag)")
                i.fas.fa-trash
            button.btn.btn-secondary(@click="addTag") +Tag
          .modal-footer
            button.btn.btn-secondary(data-bs-dismiss="modal" @click="cancel") Cancel
            button.btn.btn-primary(data-bs-dismiss="modal" @click="saveTags") Save

</template>

<script>
import * as rpc from "../modules/rpc";
import _ from "lodash";
import * as bootstrap from "bootstrap";

export default {
  data() {
    return {
      editTags: []
    };
  },
  mounted() {
  },
  methods: {
    async openTagModal() {
      this.editTags = [];
      let tags = this.$store.state.tags;
      for (let key of Object.keys(tags)) {
        this.editTags.push({ key: key, value: tags[key] });
      }
      this.$store.commit("setItem", { keyboardLock: true });

      this.editTagsModal = new bootstrap.Modal(document.getElementById("edit-tags-modal"));
      this.editTagsModal.show();
    },
    addTag() {
      this.editTags.push({key: "", value: ""})
    },
    removeTag(iTag) {
      this.editTags.splice(iTag, 1);
    },
    async saveTags() {
      let tags = {};
      for (let editTag of this.editTags) {
        if (editTag.key && editTag.value) {
          tags[editTag.key] = editTag.value;
        }
      }
      console.log("saveTags", _.cloneDeep(this.editTags), _.cloneDeep(tags));

      this.$store.commit("pushLoading")
      let response = await rpc.remote.set_tags(this.$store.state.foamId, tags);
      this.$store.commit("popLoading")

      this.$store.commit("setItem", {tags})
    },
    cancel() {
      console.log("Cancel")
      this.$store.commit("setItem", { keyboardLock: false });
    }
  },
};
</script>
