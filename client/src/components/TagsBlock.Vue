// vue component in pug
<template lang="pug">
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
    };
  },
  computed: {
    editTags() {
      return this.$store.state.editTags
    }
  },
  mounted() {
    this.editTagsModal = new bootstrap.Modal(document.getElementById("edit-tags-modal"));
  },
  methods: {
    async openTagModal() {
      let editTags = [];
      let tags = this.$store.state.tags;
      for (let key of Object.keys(tags)) {
        editTags.push({ key: key, value: tags[key] });
      }
      this.$store.commit("setItem", { editTags });
      this.$store.commit("setItem", { keyboardLock: true });

      this.editTagsModal.show();
    },
    addTag() {
       this.$store.commit("addEditTag")
    },
    removeTag(iTag) {
      let editTags = this.editTags;
      editTags.splice(iTag, 1);
      this.$store.commit("setItem", {editTags})
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
      this.$store.commit("setItem", {tags})

      this.$store.commit("popLoading")

    },
    cancel() {
      this.$store.commit("setItem", { keyboardLock: false });
    }
  },
};
</script>
