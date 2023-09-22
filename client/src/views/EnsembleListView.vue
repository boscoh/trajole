<template lang="pug">
.overflow-scroll(style="height: 100vh")
    .col-md-6.col-sm-10.col-lg-4.mx-auto.text-center.p-2
        a.btn.btn-sm.btn-secondary-outline.me-3(
          href="/#/" style="font-size: 1.5em; width: 50px; height: 100%;"
        )
          i.fas.fa-home

        h1.mt-5 Ensembles over
          br
          | Multiple Trajectories

        h4.mt-5 Load a .csv file

        | Trajectories specified by <code>foam_id</code> column
        br
        | Frame specified by <code>i_frame</code> or <code>foam_frame_idx</code> column
        br
        br

        .flex-row.d-flex
            input.form-control(type="file" @change="uploadFile" ref="file")
            button.btn.btn-primary(@click="submitFile" :disabled="!file")
                | upload
            .ms-2.spinner-grow.text-success(v-if="isUploading")

        button.mt-4.btn.btn-primary(@click="create")
            | Create Ensemble

        h4.mt-5.bheading Ensembles

        ul.list-group(v-for="ensemble in ensembles")
            .d-flex.flex-row.justify-content-between.align-items-center(
              style="height:3em"
            )
                router-link.flex-grow-1.text-start.list-group-item(
                  :to="'/ensemble/' + ensemble.id" style="height:3em"
                )
                    | {{ ensemble.id }}
                a.list-group-item(
                    style="height:3em; border-top-width: 1px; cursor:pointer;"
                    @click="deleteEnsemble(ensemble.id)"
                )
                  i.fas.fa-trash

        .pb-5
</template>

<script>
import { remote, remoteResult, remoteUrl } from '../modules/rpc'
import _ from 'lodash'
import { makeId } from '../modules/util'

export default {
  data() {
    return {
      ensembles: [],
      isUploading: false,
      file: null,
    }
  },
  async mounted() {
    this.getEnsembles()
  },
  methods: {
    uploadFile() {
      this.file = this.$refs.file.files[0]
    },
    async getEnsembles() {
      this.ensembles = await remoteResult.get_ensembles()
    },
    async deleteEnsemble(ensembleId) {
      await remoteResult.delete_ensemble(ensembleId)
      await this.getEnsembles()
    },
    async submitFile() {
      this.file = this.$refs.file.files[0]
      const formData = new FormData()
      formData.append('file', this.file, this.file.name)
      let payload = { body: formData, method: 'post' }

      this.isUploading = true
      console.log(`rpc.start.upload`, payload)
      let startTime = new Date()
      let response = await fetch(remoteUrl.replace('rpc-run', 'upload/'), payload)
      let elapsed = new Date() - startTime
      console.log(`rpc.result.upload[${elapsed}ms]: ↓`)
      console.log(response.result)
      this.isUploading = false

      let result = await response.json()
      let filename = result.filename
      if (!filename) {
        return
      }
      let ensembleId = result.ensembleId
      this.getEnsembles()
      this.$router.push(`/ensemble/${ensembleId}`)
    },
    async create() {
      let ensembleId = makeId()
      let result = await remoteResult.create_ensemble(ensembleId)
      this.$router.push({ path: `/editensemble/${result.ensembleId}` });
    }
  }
}
</script>
