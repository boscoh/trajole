<template lang="pug">
  .overflow-hidden.d-flex.flex-row.user-select-none(
    style="width: calc(100vw); height: calc(100vh); background-color: #CCC"
  )

    // Main column
    .flex-grow-1.d-flex.flex-column.user-select-none
      .d-flex.flex-row.justify-content-between.m-2

        .h2.m-0 Slide show

      .flex-grow-1(style="height: calc(100vh - 65px)")
        jolecule-matrix-panels(ref="joleculeMatrix" style="width: calc(100vw - 200px)")

    // Auxillary right action panel
    .me-2.ps-2.d-flex.flex-column(
      style="width: 200px; height: calc(100vh);"
    )

      div(:class="[isLoading ? 'overlay' : '']")

      .ps-2.my-2.w-100(style="z-index: 2002")
        loading-button

      .ms-2.flex-grow-1.overflow-scroll.mt-1
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
              .py-2
                template(v-if="view.text")
                  | {{ view.text }}
                template(v-else)
                  | (No description)
            button.btn.w-100.text-start.btn-sm.btn-outline-secondary(
              @click="selectView(view)"
              v-else
            )
              .py-2
                template(v-if="view.text")
                  | {{ view.text }}
                span.text-secondary(v-else)
                  | (No description)


</template>

<style>
.overlay {
  top: 0;
  opacity: 0.6;
  background: #aaa;
  position: absolute;
  height: 100%;
  width: 100%;
  pointer-events: visible;
  display: block;
  z-index: 1001;
}
</style>

<script>
import _ from 'lodash'
import * as rpc from '../modules/rpc'
import JoleculeMatrixPanels from '../components/JoleculeMatrixPanels.vue'
import LoadingButton from '../components/LoadingButton.vue'

export default {
  data () {
    return {
      isAsPockets: false,
      isAsCommunities: false,
      actionWidth: `200px`,
      key: '',
      opt_keys: [],
      distances: []
    }
  },
  components: {
    JoleculeMatrixPanels,
    LoadingButton
  },
  watch: {
    $route (to, from) {
      this.handleUrl()
    },
    views (to, from) {
      if (!_.isNull(to)) {
        this.selectView(to[0])
      }
    }
  },
  mounted () {
    this.handleUrl()
  },
  computed: {
    foamId () {
      return this.$store.state.foamId
    },
    viewId () {
      return this.$store.state.viewId
    },
    views () {
      return this.$store.state.views
    },
    isLoading () {
      return this.$store.getters.isLoading
    }
  },
  methods: {
    handleUrl () {
      let ensembleId = this.$route.params.ensembleId
      let viewId = this.$route.query.view
      this.$refs.joleculeMatrix.loadEnsemble(ensembleId, viewId, 'slide')
    },
    async selectView (view) {
      this.$store.commit('setItem', { viewId: view.id })
      this.$store.commit('setItem', { selectView: view })
    }
  }
}
</script>
