// vue component in pug
<template lang="pug">
  .w-100
    button.w-100.btn.btn-sm.btn-secondary(
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
import * as bootstrap from 'bootstrap'
import * as _ from 'lodash'

export default {
  data () {
    return {
      newFrame: null,
      editFrames: []
    }
  },
  computed: {
    frameStr () {
      return this.$store.getters.frameStr
    },
    iFrameTrajList () {
      return this.$store.state.iFrameTrajList
    }
  },
  mounted () {
    this.editFramesModal = new bootstrap.Modal(
      document.getElementById('edit-frames-modal')
    )
  },
  methods: {
    buildEditFrames () {
      this.editFrames = []
      for (let iFrameTraj of this.iFrameTrajList) {
        this.editFrames.push({ frame: iFrameTraj[0] })
      }
    },
    async openFramesModal () {
      this.buildEditFrames()
      this.$store.commit('setItem', { keyboardLock: true })
      this.editFramesModal.show()
    },
    addFrame (newFrame) {
      this.editFrames.push({ frame: newFrame })
      this.$store.commit('addLoad', {
        iFrameTraj: [_.parseInt(newFrame), 0],
        thisFrameOnly: false
      })
      this.newFrame = null
    },
    removeFrame (i) {
      this.$store.commit('addDumpIFrameTraj', [
        _.parseInt(this.editFrames[i].frame),
        0
      ])
      this.editFrames.splice(i, 1)
    },
    cancel () {
      this.$store.commit('setItem', { keyboardLock: false })
    },
    copyFramesToClipboard (text) {
      navigator.clipboard.writeText(text)
    }
  }
}
</script>
