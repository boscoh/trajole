<template lang="pug">
.d-flex.justify-content-center.text-center
  .col-md-6.col-sm-10.col-lg-4

    // Title
    .mt-4(style="font-size: 7rem; font-family: Courier; line-height: 1em")
      b R_S
    .mt-2(style="font-size: 3.2rem; font-family: Courier; line-height: 1em")
      b Lounge
    .text-center
      img(
        style="width: 200px"
        src="../assets/watching-tv-icon-isometric-icon-with-man-watching-tv-in-living-room-holding-remote-control-vector-vector-clipart_csp92715008.webp.png"
      )
    div Online Viewer for FoamDB
    div
      // User Guide
      a.mt-1(
        href="https://www.notion.so/redesignscience/Trajectories-in-FoamDB-77c74685264a4d908e567669ff897fe9"
      ) User Guide to FoamDB


    .d-flex.flex-column.align-items-center

      // Search bar
      .mt-5.form-group.mb-1.text-center
        label
          | Enter FoamID Here
        .d-flex.flex-row.justify-content-center
          input.form-control(
            v-model="foamId" type="number"
            @keypress.enter="changeFoamId()"
            style="width: 200px"
          )
          button.btn.btn-light(@click="changeFoamId") Go

      // Example Trajectories
      .mt-5 Example Trajectories
      .d-flex.justify-content-center(v-for="example in examples")
        router-link.btn.btn-light.mb-1(
          :to="'/foamtraj/' + example.foamId"
          tag="button"
          style="width: 250px"
        )
          template(v-if="example.name")
            | {{ example.name }}
          template(v-else)
            | FoamId:{{example.foamId}}

      // Last Views
      template(v-if="lastFoamIdViews.length > 0")
        .mt-5 Last views updated
        .d-flex.justify-content-center(v-for="v in lastFoamIdViews")
          router-link.btn.btn-light.mt-1(
            :to="'/foamtraj/' + v.foamId + '?view=' + v.id"
            tag="button"
            style="width: 250px"
          )
            | FoamId:{{v.foamId}}:{{v.id}}
            span.text-muted(v-if="v.text" style="font-size: 0.8rem")
              br
              | {{v.text}}

    .pb-5
    .pb-5
</template>

<style>
body {
  overflow: auto;
}
</style>

<script>
import * as rpc from '../modules/rpc'
import * as _ from 'lodash'

export default {
  name: 'Home',
  data () {
    return {
      foamId: '',
      examples: [
        {foamId: 23, name: 'FES for HSP 90'},
        {foamId: 17, name: 'Alanine Dipeptide'},
      ],
      lastFoamIdViews: []
    }
  },
  watch: {
    async $route (to, from) {
      console.log('route changed', to, from)
      await this.restart()
    }
  },
  async mounted() {
    await this.restart()
  },
  methods: {
    async restart() {
      document.title = "R_S Lounge"
      let response = await rpc.remote.get_last_foamid_views(100)
      if (response.result) {
        this.lastFoamIdViews = response.result.reverse()
      }
      console.log('restart', _.cloneDeep(this.lastFoamIdViews))
    },
    changeFoamId (event) {
      console.log(this.foamId)
      this.$router.push(`/foamtraj/${this.foamId}`)
    }
  }
}
</script>
