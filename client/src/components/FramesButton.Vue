// vue component in pug
<template lang="pug">
  div
    button.mb-1.btn.btn-sm.w-100.btn-secondary(
      @click="openFramesModal"
    )
      | {{ frameStr }}

    #edit-frames-modal.modal.fade
      .modal-dialog
        .modal-content
          .modal-header
            h5.modal-title {{frameStr}}
          .modal-body

            .mb-1.d-flex.flex-row.align-items-center(
              v-for="(frame, i) in editFrames"
            )
              | Frame
              input.ms-2.form-control(
                style="width: 8em"
                type="number"
                disabled
                v-model="frame.frame"
              )
              button.ms-2.btn.btn-small.btn-outline-secondary(
                @click="copyFramesToClipboard(frame.frame)"
              )
                i.far.fa-copy
              button.ms-2.btn.btn-small.btn-outline-secondary(
                v-if="editFrames.length > 1"
                @click="removeFrame(i)"
              )
                i.fas.fa-minus

            .mb-1.d-flex.flex-row.align-items-center
              | Frame
              input.ms-2.form-control(
                style="width: 8em"
                v-model="newFrame"
                type="number"
              )
              button.ms-2.btn.btn-small.btn-outline-secondary(
                @click="addFrame(newFrame)"
              )
                i.fas.fa-plus

          .modal-footer
            button.btn.btn-secondary(data-bs-dismiss="modal" @click="cancel") Cancel

</template>

<script>
import * as bootstrap from "bootstrap";

export default {
  data() {
    return {
      newFrame: null
    };
  },
  computed: {
    frameStr() {
      return this.$store.getters.frameStr
    },
    editFrames() {
      return this.$store.state.editFrames
    }
  },
  mounted() {
    this.editFramesModal = new bootstrap.Modal(document.getElementById("edit-frames-modal"));
  },
  methods: {
    async openFramesModal() {
      this.$store.commit("setEditFrames");
      this.$store.commit("setItem", { keyboardLock: true });
      this.editFramesModal.show()
    },
    addFrame(newFrame) {
      this.$store.commit("addFrame", newFrame)
      this.$store.commit("toggleFrame", newFrame)
      this.newFrame = null
    },
    removeFrame(i) {
      let editFrames = this.$store.state.editFrames;
      this.$store.commit("toggleFrame", editFrames[i].frame)
      editFrames.splice(i, 1);
      this.$store.commit("setItem", {editFrames})
    },
    cancel() {
      this.$store.commit("setItem", { keyboardLock: false });
    },
    copyFramesToClipboard(text) {
      navigator.clipboard.writeText(text);
    },
  },
};
</script>
