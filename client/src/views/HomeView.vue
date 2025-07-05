<template lang="pug">
.d-flex.justify-content-center.text-center.overflow-scroll
  .col-md-6.col-sm-10.col-lg-4
    .mt-5
    // Title
    .mt-2(style="font-size: 3.2rem; font-family: Courier; line-height: 1em")
      b Trajolecule
    .text-center
      img(
        style="width: 200px"
        src="../assets/watching-tv-icon-isometric-icon-with-man-watching-tv-in-living-room-holding-remote-control-vector-vector-clipart_csp92715008.webp.png"
      )
    div Trajectory Viewer based on Jolecule
    .d-flex.flex-column.align-items-center
      .mt-5 More
      .d-flex.justify-content-center
    .pb-5
    .pb-5
</template>

<script>
export default {
  name: "Home",
  data() {
    return {
      examples: [
        {foamId: 23, name: "FES for HSP 90"},
        {foamId: 17, name: "Alanine Dipeptide"},
      ],
    };
  },
};
</script>
