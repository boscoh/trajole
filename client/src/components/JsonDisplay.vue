<template lang="pug">
.overflow-hidden(
  :key="$route.params.id"
)

  #fail-modal.modal.fade
    .modal-dialog
      .modal-content
        .modal-header
          h5.modal-title ERROR: Loading trajectory {{ foamId }}
          button.btn-close(data-bs-dismiss="modal")
        .modal-body
          pre {{ errorMsg }}

  // Main Page
  .w-100.d-flex.flex-row(style="background-color: #CCC")

    // Left Two Panels
    .flex-grow-1.d-flex.flex-column.user-select-none(
      style="background-color: #CCC; width: calc(100vw - 200px)"
    )

      // Top bar
      .m-2.d-flex.flex-row.justify-content-between(style="height: 50px")

        .flex-grow-1.d-flex.flex-row

          // Home button
          router-link.me-3.btn.btn-sm.btn-secondary(
            to="/" tag="button" style="font-size: 1.5em; width: 50px; height: 50px;"
          )
            i.fas.fa-home

          // Title tags, fits in space in toolbar
          .flex-grow-1.overflow-hidden.w-100(style="height: 50px")
              .d-flex.flex-row.flex-wrap.text-wrap(
                style="font-family: monospace; line-height: 1.1em; font-size: 15px;"
              )
                template(v-for="(key) in Object.keys(title)")
                  span(style="color: #888") {{key}}:
                  | {{ title[key] }}&nbsp;

          div(style="width: 200px; height: 50px;")
            template(v-if="isLoading")
              button.flash-button.btn.btn-info.h-100.w-100
                .d-flex.flex-row.justify-content-center.align-items-center
                  span.spinner-border.spinner-border-sm
                  .mx-2 Connecting...

      // FES, strip & ligand table
      .p-2.d-flex.flex-column(style="height: calc(var(--vh) - 60px)")

        h4 JSON Datasets
        .d-flex.flex-row(style="height: calc(var(--vh) - 120px)")
          .h-100.overflow-scroll
            ul.list-group.justify-content-between(v-for="key in keys")
                li.list-group-item(
                    style="cursor: pointer"
                    @click="loadContent(key)"
                    :class="{active: key === selectKey}"
                )
                    | {{ key }}
          .h-100.ms-2.p-2.overflow-scroll.bg-white.flex-grow-1
              pre(style="user-select: text;") {{ content }}


</template>

<style scoped>
@keyframes glowing {
  0% {
    background-color: #CCC;
    box-shadow: 0 0 0;
    border: 0;
  }
  50% {
    background-color: #55B;
    box-shadow: 0 0 0;
    border: 0;
  }
  100% {
    background-color: #CCC;
    box-shadow: 0 0 0;
    border: 0;
  }
}
.flash-button {
  color: white;
  animation: glowing 2000ms infinite;
}
</style>

<script>
import 'bootstrap/dist/css/bootstrap.min.css'
import * as bootstrap from 'bootstrap'
import _ from 'lodash'
import * as rpc from '../modules/rpc'

export default {
  name: 'JsonDisplay',
  data () {
    return {
      foamId: '',
      mode: '',
      forceFesKey: 1,
      forceStripKey: -1,
      forceViewKey: -2,
      title: {},
      isLoading: false,
      nLoaders: 0,
      keys: [],
      selectKey: '',
      content: '',
      table: [],
      tableHeaders: [],
      errorMsg: '',
      currentUrl: '',
    }
  },
  watch: {
    $route (to, from) {
      console.log(this.$route.params.foamId)
      this.forceFesKey = Math.random()
      this.forceStripKey = Math.random()
      this.loadFoamId(this.$route.params.foamId)
    }
  },
  async mounted () {
    this.pushLoading()
    this.$forceUpdate()

    window.addEventListener('resize', this.resize)

    this.resize()

    await this.loadFoamId(this.$route.params.foamId)

    this.resize()
    this.popLoading()
  },
  computed: {
    tableStyle () {
      if (this.mode === 'table') {
        return `width: calc(50vw - ${this.viewWidth})`
      }
      return 'display: none'
    },

  },

  methods: {
    resize () {
      let vh = window.innerHeight
      document.documentElement.style.setProperty('--vh', `${vh}px`)
    },

    pushLoading() {
      this.isLoading = true
      this.nLoaders += 1
      this.$forceUpdate()
    },

    popLoading() {
      this.nLoaders -= 1
      if (this.nLoaders <= 0) {
        this.nLoaders = 0
        this.isLoading = false
        this.$forceUpdate()
      }
    },

    handleError(response) {
      if (response.error) {
        let myModal = new bootstrap.Modal(document.getElementById('fail-modal'))
        myModal.show()
        if (_.last(response.error.message).includes("FileNotFoundError")) {
          this.errorMsg = `Trajectory #${this.foamId} is empty`
        } else {
          this.errorMsg = JSON.stringify(response.error, null, 2)
        }
      }
    },

    async loadFoamId (foamId) {
      console.log('loadFrameId', foamId)
      document.title = '#' + foamId
      this.foamId = foamId
      this.title = {}
      this.pushLoading()

      let response = await rpc.remote.get_tags(this.foamId)
      this.handleError(response)
      if (response.error) {
        this.title = {"Error": `loading FoamId=${this.foamId}`}
      } else {
        this.title = response.result
      }

      await this.reload()

      this.popLoading()
    },

    async reload () {
      this.pushLoading()
      let response = (await rpc.remote.get_json_datasets(this.foamId))
      this.handleError(response)
      if (response.result) {
        let keys = response?.result
        this.keys = _.filter(keys, k => k.includes("json"))
      }
      this.popLoading()
    },

    async loadContent (key) {
      this.pushLoading()
      let response = (await rpc.remote.get_json(this.foamId, key))
      this.handleError(response)
      if (response.result) {
        this.content = JSON.stringify(response.result, null, 2)
      }
      this.selectKey = key
      this.popLoading()
    },

  }
}
</script>
