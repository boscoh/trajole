<template lang="pug">
.d-flex.justify-content-center.text-center
  .col-md-6.col-sm-10.col-lg-4
    .pt-5
    .pt-5
    .mt-2(style="font-size: 3.2rem; font-family: Courier; line-height: 1.1em")
      | Janan's Lounge
    .badge.bg-secondary(style="font-size: 1.5rem;")
      | Online Viewer for FoamDB
    .d-flex.flex-column
      h3.mt-5 Enter FoamID Here
      .form-group.mb-1
        .d-flex.flex-row
            input.form-control(v-model="foamId" type="number" @keypress.enter="changeFoamId()")
            button.btn.btn-secondary(@click="changeFoamId") Go
      img(
        style="width: 100%"
        src="../assets/watching-tv-icon-isometric-icon-with-man-watching-tv-in-living-room-holding-remote-control-vector-vector-clipart_csp92715008.webp.png"
      )
      h3.mt-4 Example Trajectories
      router-link.btn.btn-secondary.mt-2(to='/foamtraj/23' tag="button")
        | #23: FES for HSP 90
      router-link.btn.btn-secondary.mt-2(to='/foamtraj/25' tag="button")
        | #25: FES for BAX
      router-link.btn.btn-secondary.mt-2(to='/foamtraj/16' tag="button")
        | #16: P53
      router-link.btn.btn-secondary.mt-2(to='/foamtraj/17' tag="button")
        | #17: Alanine Dipeptide
    .pb-5
    .pb-5
</template>

<style>
body {
  overflow: auto;
}
</style>

<script>

export default {
  name: "Home",
  data() {
    return {
      foamId: ''
    }

  },
  methods: {
    changeFoamId(event) {
      console.log(this.foamId)
      this.$router.push(`/foamtraj/${this.foamId}`)
    }
  }
}
</script>
