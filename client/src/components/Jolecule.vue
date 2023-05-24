<template lang="pug">
.overflow-hidden(
  :key="$route.params.id"
  style="width: calc(100vw); height: calc(var(--vh));"
)

  #fail-modal.modal.fade
    .modal-dialog
      .modal-content
        .modal-header
          h5.modal-title ERROR: Loading trajectory {{ foamId }}
          button.btn-close(data-bs-dismiss="modal")
        .modal-body
          pre {{ errorMsg }}

  #view-edit-modal.modal.fade
    .modal-dialog
      .modal-content
        .modal-header
          h5.modal-title Edit Text Description
        .modal-body
          .mb-3(style="font-size: 0.75em") URL: {{currentUrl}}?query={{ editViewId }}
          textarea.form-control(v-model="editViewText" rows=4)
        .modal-footer
          button.btn.btn-secondary(data-bs-dismiss="modal" @click="clearKeyboardLock") Cancel
          button.btn.btn-primary(data-bs-dismiss="modal" @click="saveViewText") Save

  #tags-edit-modal.modal.fade
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
          button.btn.btn-secondary(data-bs-dismiss="modal" @click="clearKeyboardLock") Cancel
          button.btn.btn-primary(data-bs-dismiss="modal" @click="saveTags") Save

  #frames-edit-modal.modal.fade
    .modal-dialog
      .modal-content
        .modal-header
          h5.modal-title {{frames}}
        .modal-body
          .mb-1.d-flex.flex-row.align-items-center(
              v-for="frame in editFrames"
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
                @click="addFrame(frame.frame)"
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
          button.btn.btn-secondary(data-bs-dismiss="modal" @click="clearKeyboardLock") Cancel

  // Main Page
  .w-100.d-flex.flex-row.user-select-none(style="background-color: #CCC")

    // Left Two Panels
    .flex-grow-1.d-flex.flex-column.user-select-none(
      style="background-color: #CCC; width: calc(100vw - 200px)"
    )

      // Top bar
      .d-flex.flex-row.justify-content-between.m-2(style="height: 50px")

        .flex-grow-1.d-flex.flex-row

          // Home button
          router-link.btn.btn-sm.btn-secondary.me-3(
            to="/" tag="button" style="font-size: 1.5em; width: 50px; height: 50px;"
          )
            i.fas.fa-home

          // Title tags, fits in space in toolbar
          .flex-grow-1.overflow-hidden.w-100(style="height: 50px")
            .d-flex.flex-row.flex-wrap.text-wrap(
              style="font-family: monospace; line-height: 1.1em; font-size: 15px;"
            )
              template(v-for="(key) in Object.keys(tags)")
                span(style="color: #888") {{key}}:
                | {{ tags[key] }}&nbsp;
              span &nbsp;
              span.text-secondary(@click="openTagModal()")
                i.fas.fa-edit

          // Dropdown for energy components
          .ms-2(v-if="opt_keys.length")
            select.form-select.form-select-sm(v-model="key" @change="selectOptKey(key)")
              option(v-for="opt_key in opt_keys" :value="opt_key")
                | {{opt_key}}

      // FES, strip & ligand table
      .d-flex.flex-row(style="height: calc(var(--vh) - 60px)")

        // The Free-Energy Surface
        #matrix-widget.h-100(:style="matrixStyle" :key="forceMatrixKey")

        // Traj Strip
        #strip-widget.h-100(:style="stripStyle" :key="forceStripKey")

        // Table of Ligands
        #table.p-2.me-2.overflow-scroll(:style="tableStyle")
          table.table(v-if="table" style="cursor: pointer")
            thead(v-if="tableHeaders")
              tr
                th(v-for="h in tableHeaders")
                  .d-flex.flex-nowrap(@click="sortTable(h.iCol, h.status)")
                    span.me-1 {{ h.value }}
                    template(v-if="h.status === 'none'")
                      span.text-muted &uarr;
                      span.text-muted &darr;
                    template(v-if="h.status==='up'")
                      span &uarr;
                      span.text-muted &darr;
                    template(v-if="h.status==='down'")
                      span.text-muted &uarr;
                      span &darr;
            tbody
              tr(
                v-for="(row, i) in table"
                :key="i"
                :class="[isIFrameTrajSelected(row.iFrameTraj) ? 'bg-primary' : '']"
                @mousedown="e => downTableEntry(e, row)"
                @mouseup="e => upTableEntry(e, row)"
                @mousemove="e => moveTableEntry(e, row)"
              )
                td(v-for="val in row.vals") {{val}}

        // Jolecule
        #jolecule-container.h-100(:style="joleculeStyle")

    // Actions Strip
    #view-container.h-100.me-2.d-flex.flex-column(:style="viewStyle")

      // isLoading status button
      .ps-2.my-2.w-100(style="z-index: 2002; height: 50px; position: relative")
        button.border-0.flash-button.btn.h-100.w-100(
            disabled=false
            v-if="isLoading"
        )
          .d-flex.flex-row.justify-content-center.align-items-center
            span.spinner-border.spinner-border-sm
            .mx-2 Connecting...

      div(:class="[isLoading ? 'overlay' : '']")

      .ps-2
        //////////////////////////////////
        // Buttons on the side

        button.mb-1.btn.btn-sm.w-100.btn-secondary(@click="openFramesModal")
          | {{ frames }}

        button.mb-1.btn.btn-sm.w-100.btn-secondary(@click="toggleAsCommunities()")
          span(v-if="isAsCommunities")
            | AS Communities&nbsp;
            i.fas.fa-check
          template(v-else) AS Communities

        button.mb-1.btn.btn-sm.w-100.btn-secondary(@click="toggleAsPockets()")
          span(v-if="isAsPockets")
            | AS Pockets&nbsp;
            i.fas.fa-check
          template(v-else) AS Pockets

        button.mb-1.btn.btn-sm.w-100.btn-secondary(@click="downloadPdb")
          | Download PDB

        button.mb-1.btn.btn-sm.w-100.btn-secondary(
          @click="downloadParmed()"
          :disabled="!isParmed"
        )
          span(v-if="!isParmed") No Parmed
          span(v-else) Download Parmed

        button.mb-1.btn.btn-sm.w-100.btn-secondary(@click="goToJson()") JSON

        // Views handlers
        button.mt-3.btn.btn-sm.w-100.btn-secondary(@click="saveView")
          | Save View

        .flex-grow-1.overflow-scroll.mt-1(style="height: calc(var(--vh) - 210px")
          div
            .w-100.mb-1.p-2.rounded(
              style="background-color: #BBB"
              v-for="view in views"
            )
              .d-flex.flex-row.w-100.mb-1.pt-2.pb-0.text-start(style="font-size:0.9em")
                button.btn.w-100.text-start.btn-sm.btn-secondary(
                  v-if="view.id == viewId"
                  @click="selectView(view)"
                  :key="view.id"
                )
                  .py-2(v-if="view.text")
                      | {{ view.text }}
                  .py-2(v-if="!view.text")
                      | Click
                      i.mx-2.far.fa-comment
                      | to add text
                button.btn.w-100.text-start.btn-sm.btn-outline-secondary(
                  @click="selectView(view)"
                  v-else
                )
                  .py-2
                    template(v-if="view.text")
                      | {{ view.text }}
                    span.text-secondary(v-else)
                      | Click
                      i.mx-2.far.fa-comment
                      | to add text
              .d-flex.flex-row.justify-content-between
                .flex-start.flex-row
                  button.btn.btn-sm.btn-outline-secondary.border-0(
                    @click="startEditViewModal(view)"
                  )
                    i.far.fa-comment
                  button.btn.btn-sm.btn-outline-secondary.border-0(
                    @click="updateView(view)"
                  )
                    i.fas.fa-save
                .flex-end
                  button.btn.btn-sm.btn-outline-secondary.border-0(
                    @click="deleteView(view)"
                  )
                    i.fas.fa-trash
</template>

<style scoped>
body {
  overflow: hidden;
}
#jolecule-container {
  min-height: 0;
  min-width: 0;
  flex: 1;
  margin: 0;
  padding: 0;
}
.overlay {
  top: 0;
  opacity: .6;
  background: #AAA;
  position: absolute;
  height: 100%;
  width: 100%;
  pointer-events: visible;
  display: block;
  z-index: 1001;
}
@keyframes glowing {
  0% {
    background-color: #BBB;
    box-shadow: 0 0 0;
    border: 0;
  }
  50% {
    background-color: #55B;
    box-shadow: 0 0 0;
    border: 0;
  }
  100% {
    background-color: #BBB;
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
import {initEmbedJolecule} from 'jolecule'
import * as rpc from '../modules/rpc'
import {MatrixWidget} from "../modules/matrixwidget";
import {getFirstValue, inFrames, isSameVec} from "../modules/util";
import {saveFile} from "../modules/util";


export default {
  name: 'Jolecule',
  data () {
    return {
      nLoaders: 0,
      stripWidth: '70px',
      viewWidth: '200px',
      forceMatrixKey: 1,
      forceStripKey: -1,
      currentUrl: '',
      foamId: '',
      views: [],
      viewId: null,
      editTags: [],
      isAsCommunities: false,
      isAsPockets: false,
      iFrameTrajList: [],
      isParmed: false,
      mode: '',
      tags: {},
      key: '',
      opt_keys: [],
      table: [],
      tableHeaders: [],
      errorMsg: '',
      editViewText: '',
      editViewId: '',
      editFrames: [],
      newFrame: null,
    }
  },
  watch: {
    $route (to, from) {
      console.log(`watch new url`, to)
      this.forceMatrixKey = Math.random()
      this.forceStripKey = Math.random()
      this.handleNewUrl()
    }
  },
  async mounted () {
    console.log(`mounted`)
    this.pushLoading()

    document.oncontextmenu = _.noop
    document.onkeydown = e => {
      this.onkeydown(e)
    }

    this.jolecule = initEmbedJolecule({
      divTag: '#jolecule-container',
      backgroundColor: '#CCC',
      viewId: '',
      viewHeight: 170,
      isViewTextShown: false,
      isSequenceBar: true,
      isEditable: true,
      isGrid: true,
      bCutoff: -1.0,
      isPlayable: false,
      isLegend: true,
      isToolbarOnTop: true
    })
    this.controller = this.jolecule.soupWidget.controller
    this.soupView = this.jolecule.soupView

    // saves the PDB for every frame
    this.cacheByiFrameTraj = {}

    // saves the alphaspace-PDB for every frame
    this.cacheAsCommunitiesByiFrameTraj = {}
    this.cacheAsPocketsByiFrameTraj = {}

    window.addEventListener('beforeunload', e => this.close())
    window.addEventListener('resize', this.resize)

    this.resize()

    // saves which structures belongs to a loaded frame on display
    this.nStructureInFrameList = []
    this.handleNewUrl()

    this.resize()
    this.popLoading()
  },
  computed: {
    joleculeStyle () {
      if (this.mode === 'strip') {
        return `width: calc(100% - ${this.stripWidth})`
      }
      return 'width: calc(50vw)'
    },

    tableStyle () {
      if (this.mode === 'table') {
        return `width: calc(50vw - ${this.viewWidth})`
      }
      return 'display: none'
    },

    stripStyle () {
      if (this.mode === 'matrix-strip' || this.mode === 'strip') {
        return `width: ${this.stripWidth}`
      }
      return 'display: none'
    },

    viewStyle () {
      return `width: ${this.viewWidth}`
    },

    matrixStyle () {
      if (this.mode === 'matrix-strip') {
        return `width: calc(50% - ${this.stripWidth} - ${this.viewWidth})`
      } else if (this.mode === 'matrix' || this.mode === 'sparse-matrix') {
        return `width: calc(50% - ${this.viewWidth})`
      }
      return 'display: none'
    },

    isLoading() {
      return this.nLoaders > 0
    },

    frames() {
      let values = _.map(this.iFrameTrajList, x => x[0])
      return `Foam: ${this.foamId} - Frame: ${values.join(" ")}`
    }
  },

  methods: {
    resize () {
      let vh = window.innerHeight
      document.documentElement.style.setProperty('--vh', `${vh}px`)

      if (this.matrixWidget) {
        this.matrixWidget.resize()
      }

      if (this.stripWidget) {
        this.stripWidget.resize()
      }

      if (this.jolecule) {
        this.jolecule.resize()
      }
    },

    pushLoading() {
      this.nLoaders += 1
      this.$forceUpdate()
    },

    popLoading() {
      this.nLoaders -= 1
      if (this.nLoaders <= 0) {
        this.nLoaders = 0
      }
      this.$forceUpdate()
    },

    openModal(elemId) {
      let myModal = new bootstrap.Modal(document.getElementById(elemId))
      myModal.show()
    },

    async clearKeyboardLock() {
      window.keyboardLock = false
    },

    handleError(response) {
      if (response.error) {
        this.openModal('fail-modal')
        if (_.last(response.error.message).includes("FileNotFoundError")) {
          this.errorMsg = `Trajectory #${this.foamId} is empty`
        } else {
          this.errorMsg = JSON.stringify(response.error, null, 2)
        }
        this.tags = {"Error": `loading FoamId=${this.foamId}`}
      }
    },

    async getConfig (key) {
      this.pushLoading()
      let response = await rpc.remote.get_config(this.foamId, key)
      this.popLoading()
      if (response.result) {
        return response.result
      }
      return null
    },

    handleNewUrl() {
      let frameQuery = this.$route.query.frame
      if (!frameQuery) {
        frameQuery = ""
      }
      let frames = _.map(frameQuery.split(','), _.parseInt)
      let viewId = this.$route.query.view
      let foamId = this.$route.params.foamId
      this.loadFoamId(foamId, frames, viewId)
    },

    async loadFoamId (foamId, frames, viewId) {
      console.log('loadFoamId', foamId, frames, viewId)

      document.title = '#' + foamId
      this.foamId = foamId

      // Clear all widgets
      this.tags = {}
      this.jolecule.clear()
      this.cacheByiFrameTraj = {}
      this.cacheAsCommunitiesByiFrameTraj = {}
      this.cacheAsPocketsByiFrameTraj = {}
      this.nStructureInFrameList = []
      this.iFrameTrajList = []
      if (this.matrixWidget) {
        this.matrixWidget.iFrameTrajs = []
        this.matrixWidget.draw()
      }
      if (this.stripWidget) {
        this.stripWidget.iFrameTrajs = []
        this.stripWidget.draw()
      }

      this.pushLoading()

      let response

      response = await rpc.remote.reset_foam_id(this.foamId)

      this.handleError(response)
      if (response.result) {
        this.tags = response.result.title
      }

      this.mode = await this.getConfig('mode')
      this.key = await this.getConfig('key')
      this.opt_keys = await this.getConfig('opt_keys')

      if (this.mode === 'strip') {
        await this.loadStrip()
      } else if ((this.mode === 'sparse-matrix') || (this.mode === 'matrix')) {
        await this.loadMatrix()
      } else if (this.mode.includes('matrix-strip')) {
        await this.loadStrip()
        await this.loadMatrix()
      } else if (this.mode === 'table') {
        await this.loadTable()
      } else if (this.mode === 'frame') {
        await this.loadFrameIntoJolecule([0, 0], false)
      }

      if (frames) {
        let initIFrame = this.iFrameTrajList[0][0]
        console.log('loading frames', frames)
        for (let iFrame of frames) {
            await this.clickFrame(iFrame)
        }
        await this.clickFrame(initIFrame)
      }

      response = await rpc.remote.get_views(this.foamId)
      if (response.result) {
        this.views = response.result
        console.log('loading view', this.queryView)
        if (viewId && this.views) {
          let view = _.find(this.views, v => v.id === viewId)
          if (view) {
            await this.selectView(view)
          }
        }
      }

      this.popLoading()

      response = (await rpc.remote.get_json_datasets(this.foamId))
      if (response.result) {
        let keys = response?.result
        if (keys.includes("parmed")) {
          this.isParmed = true
          this.$forceUpdate()
        }
      }

    },

    async loadMatrix (iFrameTraj) {
      let matrix = await this.getConfig('matrix')
      if (_.isEmpty(matrix)) {
        return
      }
      let value = _.isNil(iFrameTraj) ? getFirstValue(matrix) : { iFrameTraj }
      let isSparse = this.mode === 'sparse-matrix'
      this.matrixWidget = new MatrixWidget('#matrix-widget', matrix, isSparse)
      this.resize()
      this.matrixWidget.selectGridValue = this.selectMatrixGridValue
      this.matrixWidget.deselectGridValue = this.deselectMatrixGridValue
      await this.matrixWidget.clickGridValue(value)
    },

    async selectMatrixGridValue (value, thisFrameOnly = false) {
      let iFrameTraj
      if (_.has(value, 'iFrameTrajs')) {
        let label = value.label
        let n = value.iFrameTrajs.length
        let grid = [
          _.map(value.iFrameTrajs, (iFrameTraj, i) => ({
            p: i / n,
            label,
            iFrameTraj
          }))
        ]
        this.stripWidget.loadGrid(grid)
        value = getFirstValue([grid])
        await this.stripWidget.clickGridValue(value)
      }
      if (_.has(value, 'iFrameTraj')) {
        iFrameTraj = value.iFrameTraj
        if (!_.isNil(iFrameTraj)) {
          if (
            this.hasFramesInJolecule() ||
            !inFrames(this.iFrameTrajList, iFrameTraj)
          ) {
            await this.loadFrameIntoJolecule(iFrameTraj, thisFrameOnly)
          }
        }
      }
    },

    async deselectMatrixGridValue (value) {
      let iFrameTraj
      if (_.has(value, 'iFrameTraj')) {
        iFrameTraj = value.iFrameTraj
      } else if (_.has(value, 'iFrameTrajs')) {
        iFrameTraj = value.iFrameTrajs[0]
      }
      if (inFrames(this.iFrameTrajList, iFrameTraj)) {
        await this.deleteIFrameTraj(iFrameTraj)
      }
    },

    async loadStrip () {
      let strip = await this.getConfig('strip')
      if (_.isEmpty(strip)) {
        strip = [[]]
      }
      this.stripWidget = new MatrixWidget('#strip-widget', strip, false)
      this.resize()
      this.stripWidget.selectGridValue = this.selectStripGridValue
      this.stripWidget.deselectGridValue = this.deselectStripGridValue
      let value = getFirstValue(strip)
      if (value) {
        await this.stripWidget.clickGridValue(value)
      }
    },

    async selectStripGridValue (value, thisFrameOnly) {
      let iFrameTraj = value.iFrameTraj
      if (_.isNil(iFrameTraj)) {
        return
      }
      if (
        this.hasFramesInJolecule() ||
        !inFrames(this.iFrameTrajList, iFrameTraj)
      ) {
        await this.loadFrameIntoJolecule(iFrameTraj, thisFrameOnly)
      }
    },

    async deselectStripGridValue (value) {
      let iFrameTraj = value.iFrameTraj
      if (inFrames(this.iFrameTrajList, iFrameTraj)) {
        await this.deleteIFrameTraj(iFrameTraj)
      }
    },

    async loadTable (iFrameTraj) {
      this.table = await this.getConfig('table')
      if (_.isEmpty(this.table)) {``
        return
      }
      let headers = await this.getConfig('table_headers')
      if (headers) {
        this.tableHeaders = _.map(headers, (h, i) => ({
          value: h,
          status: 'none',
          iCol: i
        }))
      }
      let values = _.filter(_.flattenDeep(this.table), v =>
        _.has(v, 'iFrameTraj')
      )
      this.iFrameTraj = _.first(values).iFrameTraj
      await this.selectTableiFrameTraj(this.iFrameTraj)
      this.resize()
    },

    async selectTableiFrameTraj (iFrameTraj, thisFrameOnly) {
      await this.loadFrameIntoJolecule(iFrameTraj, thisFrameOnly)
    },

    async downTableEntry (event, row) {
      this.mouseDownInTable = true
      if (event.shiftKey) {
        if (inFrames(this.iFrameTrajList, row.iFrameTraj)) {
          if (this.iFrameTrajList.length > 1) {
            await this.deleteIFrameTraj(row.iFrameTraj)
          }
          return
        }
      }
      this.selectTableiFrameTraj(row.iFrameTraj, !event.shiftKey)
    },

    async moveTableEntry (event, row) {
      if (this.mouseDownInTable) {
        this.selectTableiFrameTraj(row.iFrameTraj, !event.shiftKey)
      }
    },

    async upTableEntry (event, row) {
      this.mouseDownInTable = false
    },

    async sortTable (iCol, status) {
      let newStatus = 'up'
      if (status === 'up') {
        newStatus = 'down'
      }
      for (let iCol = 0; iCol < this.tableHeaders.length; iCol += 1) {
        this.tableHeaders[iCol].status = 'none'
      }
      this.tableHeaders[iCol].status = newStatus
      if (newStatus !== 'none') {
        if (iCol === 0) {
          this.table = _.sortBy(this.table, row => row.vals[iCol])
          if (newStatus === 'down') {
            this.table = _.reverse(this.table)
          }
        } else {
          let multiplier = newStatus === 'up' ? 1 : -1
          this.table = _.sortBy(this.table, row => multiplier * row.vals[iCol])
        }
      }
    },

    isIFrameTrajSelected (iFrameTraj) {
      return inFrames(this.iFrameTrajList, iFrameTraj)
    },

    async getPdbLines (iFrameTraj) {
      let key = `${iFrameTraj[0]}-${iFrameTraj[1]}`
      let result = []
      if (this.isAsCommunities) {
        if (key in this.cacheAsCommunitiesByiFrameTraj) {
          console.log(`getPdbLines from cacheAsCommunitiesByiFrameTraj[${key}]`)
          result = this.cacheAsCommunitiesByiFrameTraj[key]
        } else {
          this.pushLoading()
          let response = await rpc.remote.get_pdb_lines_with_as_communities(
              this.foamId,
              iFrameTraj
          )
          this.popLoading()
          if (response.result) {
            this.cacheAsCommunitiesByiFrameTraj[key] = response.result
            result = response.result
          }
        }
      } else if (this.isAsPockets) {
        if (key in this.cacheAsPocketsByiFrameTraj) {
          console.log(`getPdbLines from cacheAsPocketsByiFrameTraj[${key}]`)
          result = this.cacheAsPocketsByiFrameTraj[key]
        } else {
          this.pushLoading()
          let response = await rpc.remote.get_pdb_lines_with_as_pockets(
            this.foamId,
            iFrameTraj
          )
          this.popLoading()
          if (response.result) {
            this.cacheAsPocketsByiFrameTraj[key] = response.result
            result = response.result
          }
        }
      } else {
        if (key in this.cacheByiFrameTraj) {
          console.log(`getPdbLines from cacheByiFrameTraj[${key}]`)
          result = this.cacheByiFrameTraj[key]
        } else {
          this.pushLoading()
          let response = await rpc.remote.get_pdb_lines(this.foamId, iFrameTraj)
          this.popLoading()
          if (response.result) {
            this.cacheByiFrameTraj[key] = response.result
            result = response.result
          }
        }
      }
      return result
    },

    hasFramesInJolecule () {
      return this.nStructureInFrameList.length
    },

    rewriteUrlWithFrames() {
      let values = _.map(this.iFrameTrajList, x => x[0])
      history.pushState(
        {},
        null,
        '#' + this.$route.path + '?frame=' + values.join(",")
      )
    },

    async loadFrameIntoJolecule (iFrameTraj, thisFrameOnly = false) {
      if (this.isFetching) {
        return
      }
      this.isFetching = true
      let pdbLines = await this.getPdbLines(iFrameTraj)
      if (pdbLines) {
        let saveView = null
        let pdbId = `frame-${iFrameTraj}`.replace(',', '-')
        let soup = this.jolecule.soupWidget.soup
        let nStructurePrev = soup.structureIds.length
        if (nStructurePrev > 0) {
          saveView = this.jolecule.soupView.getCurrentView()
        }
        console.log(`loadFrameIntoJolecule load`, pdbId)
        await this.jolecule.asyncAddDataServer(
          {
            version: 2,
            pdbId: pdbId,
            format: 'pdb',
            asyncGetData: async () => pdbLines.join('\n'),
            asyncGetViews: async () => [],
            async asyncSaveViews () {},
            async asyncDeleteViews () {}
          },
          false
        )

        let nStructureInThisFrame = soup.structureIds.length - nStructurePrev
        if (thisFrameOnly && this.hasFramesInJolecule()) {
          let iLastStructureToDelete = soup.structureIds.length - 1 - nStructureInThisFrame
          for (let i=iLastStructureToDelete; i>=0; i-=1) {
            console.log(`loadFrameIntoJolecule delete`, soup.structureIds[i])
            this.jolecule.controller.deleteStructure(i)
          }
          this.nStructureInFrameList = []
          this.iFrameTrajList = []
        }
        this.nStructureInFrameList.push(nStructureInThisFrame)
        this.iFrameTrajList.push(iFrameTraj)

        if (saveView) {
          this.jolecule.soupView.setHardCurrentView(saveView)
        }
        this.jolecule.soupWidget.distanceMeasuresWidget.drawFrame()
        if (!this.isAsCommunities && !this.isAsPockets) {
          this.clearGridDisplay()
        }
        this.jolecule.soupWidget.buildScene()
      }
      this.isFetching = false
      this.rewriteUrlWithFrames()
    },

    async reloadLastFrameOfJolecule() {
      if (this.isFetching) {
        return
      }
      this.isFetching = true
      let iFrameTraj =_.last(this.iFrameTrajList)
      let pdbLines = await this.getPdbLines(iFrameTraj)
      if (pdbLines) {
        let saveView = this.jolecule.soupView.getCurrentView()

        let pdbId = `frame-${iFrameTraj}`.replace(',', '-')
        let soup = this.jolecule.soup
        let structureId = _.last(soup.structureIds)
        await this.jolecule.asyncAddDataServer(
          {
            version: 2,
            pdbId: pdbId,
            format: 'pdb',
            asyncGetData: async () => pdbLines.join('\n'),
            asyncGetViews: async () => [],
            async asyncSaveViews () {},
            async asyncDeleteViews () {}
          },
          false
        )
        soup.structureIds[soup.structureIds.length - 1] = structureId

        let nStructure = _.last(this.nStructureInFrameList)
        let i = this.iFrameTrajList.length - 1
        await this.deleteFromIFrameTrajList(i)
        this.nStructureInFrameList.splice(i, 1)
        this.iFrameTrajList.splice(i, 1)
        this.nStructureInFrameList.push(nStructure)
        this.iFrameTrajList.push(iFrameTraj)

        this.jolecule.soupView.setHardCurrentView(saveView)
        this.jolecule.soupWidget.distanceMeasuresWidget.drawFrame()
        if (!this.isAsCommunities && !this.isAsPockets) {
          this.clearGridDisplay()
        }
        this.jolecule.soupWidget.buildScene()
      }
      this.isFetching = false
    },

    async deleteIFrameTraj (delIFrameTraj) {
      let i = _.findIndex(
          this.iFrameTrajList, iFrameTraj => isSameVec(iFrameTraj, delIFrameTraj)
      )
      if (!_.isNil(i)) {
        await this.deleteFromIFrameTrajList(i)
      }
      this.rewriteUrlWithFrames()
    },

    async deleteFromIFrameTrajList (iFrame) {
      let nStructureBefore = _.sum(this.nStructureInFrameList.slice(0, iFrame))
      let nStructureToDelete = this.nStructureInFrameList[iFrame]
      let soup = this.jolecule.soupWidget.soup
      while (nStructureToDelete) {
        let iStructureToDelete = nStructureBefore + nStructureToDelete - 1
        let structureId = soup.structureIds[iStructureToDelete]
        this.jolecule.controller.deleteStructure(iStructureToDelete)
        console.log(`deleteIFromIFrameTrajList ${iStructureToDelete}:${structureId}`)
        nStructureToDelete -= 1
      }
      this.jolecule.soupWidget.buildScene()
      this.iFrameTrajList.splice(iFrame, 1)
      this.nStructureInFrameList.splice(iFrame, 1)
    },

    downloadPdb() {
      let lines = []
      let soup = this.jolecule.soup
      let nStructure = soup.structureIds.length
      let iStructure = null
      let atom = soup.getAtomProxy()
      let residue = soup.getResidueProxy()
      let isMultiple = nStructure > 1
      for (let iAtom of _.range(soup.getAtomCount())) {
        atom.iAtom = iAtom
        residue.iRes = atom.iRes

        if (iStructure !== residue.iStructure) {
          iStructure = residue.iStructure
          if (isMultiple) {
            if (iStructure > 0) {
              lines.push('ENDMDL')
            }
            lines.push('MODEL    ' + (iStructure+1).toString())
          }
          lines.push(`REMARK   6     Foamid:${this.foamId} ${residue.structureId}`)
        }

        let line = "ATOM  "
        line += (atom.iAtom + 1).toString().padStart(5)
        line += " "
        line += atom.atomType.padStart(4)
        line += " "
        line += residue.resType.padEnd(4)
        line += residue.chain
        line += residue.resNum.toString().padStart(4)
        line += "    "
        line += atom.pos.x.toFixed(3).padStart(8)
        line += atom.pos.y.toFixed(3).padStart(8)
        line += atom.pos.z.toFixed(3).padStart(8)
        line += atom.bfactor.toFixed(2).padStart(6)
        line += "1.00".padStart(6)
        line += "          "
        line += atom.elem.padStart(2)
        lines.push(line)
      }

      if (isMultiple) {
        lines.push('ENDMDL')
      }

      let text = lines.join("\n")
      let filename = `foamid-${this.foamId}`
      let iFrameTraj = _.last(this.iFrameTrajList)
      if (iFrameTraj) {
        let iFrame = iFrameTraj[0]
        filename += `-frame-${iFrame}`
      }
      filename += '.pdb'

      let element = document.createElement('a');
      element.setAttribute('href', 'data:text/csv;charset=utf-8,' + encodeURIComponent(text));
      element.setAttribute('download', filename);

      element.style.display = 'none';
      document.body.appendChild(element);

      element.click();
      document.body.removeChild(element);
    },

    async selectView(view) {
      this.viewId = view.id
      console.log(`selectView`, _.cloneDeep(view))
      if (_.has(view, "matrixWidgetValues")) {
        await this.matrixWidget.loadValues(view.matrixWidgetValues)
      }
      if (_.has(view, "stripWidgetValues")) {
        await this.stripWidget.loadValues(view.stripWidgetValues)
      }
      let newView = this.jolecule.soupView.getCurrentView()
      newView.setFromDict(view.viewDict)
      this.controller.setTargetView(newView)
      history.pushState(
        {},
        null,
        '#' + this.$route.path + '?view=' + view.id
      )
    },

    async startEditViewModal(view) {
      window.keyboardLock = true
      this.editViewText = view.text
      this.editViewId = view.id
      this.currentUrl = window.location.href.split('?')[0]
      this.openModal('view-edit-modal')
    },
    
    async saveView() {
      let viewDict = this.jolecule.soupView.getCurrentView().getDict()
      let view = {
        id: viewDict.view_id.replace("view:", ""),
        foamId: this.foamId,
        timestamp: Math.floor(Date.now() / 1000),
        viewDict: viewDict,
        text: '',
        imgs: '',
      }
      if (this.matrixWidget) {
        view.matrixWidgetValues = this.matrixWidget.values
      }
      if (this.stripWidget) {
        view.stripWidgetValues = this.stripWidget.values
      }
      console.log(`saveView`, _.cloneDeep(view))
      // NOTE: reverse chronological order insert at top
      this.views.unshift(view)
      this.pushLoading()
      await rpc.remote.add_view(this.foamId, view)
      this.popLoading()
      this.selectView(view)
    },

    async saveViewText() {
      let view = _.find(this.views, {id: this.editViewId})
      view.foamId = this.foamId,
      view.timestamp = Math.floor(Date.now() / 1000),
      view.text = this.editViewText
      this.pushLoading()
      await rpc.remote.add_view(this.foamId, view)
      this.popLoading()
      window.keyboardLock = false
    },

    async updateView(view) {
      view.viewDict = this.jolecule.soupView.getCurrentView().getDict()
      if (this.matrixWidget) {
        view.matrixWidgetValues = this.matrixWidget.values
      }
      if (this.stripWidget) {
        view.stripWidgetValues = this.stripWidget.values
      }
      view.foamId = this.foamId,
      view.timestamp = Math.floor(Date.now() / 1000),
      this.pushLoading()
      await rpc.remote.add_view(this.foamId, view)
      this.popLoading()
      this.$forceUpdate()
    },

    async deleteView(view) {
      let i = this.views.indexOf(view)
      this.views.splice(i, 1)
      this.pushLoading()
      await rpc.remote.delete_view(this.foamId, view)
      this.popLoading()
      this.viewId = null
      history.pushState({}, null, '#' + this.$route.path)
    },

    clearGridDisplay() {
      let grid = this.jolecule.soupView.soup.grid
      grid.isElem = {}
      grid.isChanged = true
      this.jolecule.soupView.isUpdateColors = true
      this.jolecule.soupWidget.buildScene()
    },

    async toggleAsCommunities () {
      this.isAsCommunities = !this.isAsCommunities
      this.$forceUpdate()
      if (!this.isAsCommunities) {
        this.clearGridDisplay()
      } else {
        this.isAsPockets = false
      }
      this.reloadLastFrameOfJolecule()
    },

    async toggleAsPockets () {
      this.isAsPockets = !this.isAsPockets
      this.$forceUpdate()
      if (!this.isAsPockets) {
        this.clearGridDisplay()
      } else {
        this.isAsCommunities = false
      }
      this.reloadLastFrameOfJolecule()
    },

    async selectOptKey (key) {
      let iFrameTraj = _.last(this.iFrameTrajList)
      console.log('selectOptKey', key, iFrameTraj)
      await rpc.remote.select_new_key(this.foamId, key)
      this.forceMatrixKey = Math.random()
      this.forceStripKey = Math.random()
      await this.loadMatrix(iFrameTraj)
    },

    async close () {
      await rpc.remote.kill()
    },

    onkeydown (event) {
      if ((window.keyboardLock) || (event.metaKey) || (event.ctrlKey)) {
          return
      }
      let c = String.fromCharCode(event.keyCode).toUpperCase()
      if (c === 'V') {
        this.createView()
      } else if (c === 'K' || event.keyCode === 37) {
        this.controller.setTargetToPrevResidue()
      } else if (c === 'J' || event.keyCode === 39) {
        this.controller.setTargetToNextResidue()
      } else if (c === 'S') {
        this.controller.toggleShowOption('sphere')
      } else if (c === 'B') {
        this.controller.toggleShowOption('backbone')
      } else if (c === 'R') {
        this.controller.toggleShowOption('ribbon')
      } else if (c === 'L') {
        this.controller.toggleShowOption('ligands')
      } else if (c === 'W') {
        this.controller.toggleShowOption('water')
      } else if (c === 'T') {
        this.controller.toggleShowOption('transparent')
      } else if (c === 'N') {
        this.controller.toggleResidueNeighbors()
      } else if (c === 'C') {
        this.controller.toggleSelectedSidechains()
      } else if (c === 'X') {
        let iAtom = this.soupView.getICenteredAtom()
        if (iAtom >= 0) {
          let atom = this.soupView.soup.getAtomProxy(iAtom)
          this.controller.selectResidue(atom.iRes)
        }
      } else if (c === 'A') {
        this.toggleAsCommunities()
        event.preventDefault()
      } else if (event.keyCode === 27) {
        this.controller.clear()
      } else if (c === 'Z' || event.keyCode === 13) {
        this.controller.zoomToSelection()
      } else if (event.key == "Escape") {
        this.controller.clear()
      }

    },

    async openTagModal(view) {
      this.editTags = []
      for (let key of Object.keys(this.tags)) {
        this.editTags.push({key: key, value: this.tags[key]})
      }
      window.keyboardLock = true
      this.openModal('tags-edit-modal')
    },

    async saveTags() {
      let tags = {}
      for (let editTag of this.editTags) {
        if (editTag.key && editTag.value) {
          tags[editTag.key] = editTag.value
        }
      }
      console.log('saveTags', _.cloneDeep(this.editTags), _.cloneDeep(tags))
      this.pushLoading()
      let response = await rpc.remote.set_tags(this.foamId, tags)
      this.popLoading()
      if (response.result) {
        this.tags = tags
      }
    },

    removeTag(iTag) {
      this.editTags.splice(iTag, 1)
      this.$forceUpdate()
    },

    addTag(tag) {
      this.editTags.push({key: '', value: ''})
    },

    goToJson() {
      this.$router.push(`/json/${this.foamId}`)
    },

    async downloadParmed() {
      this.pushLoading()
      let url = rpc.remoteUrl.replace('rpc-run', 'parmed') + `/${this.foamId}`
      let fname = `foamid-${this.foamId}`
      let iFrameTraj = _.last(this.iFrameTrajList)
      if (iFrameTraj) {
        let iFrame = iFrameTraj[0]
        url += `?i_frame=${iFrame}`
        fname += `-frame-${iFrame}`
      }
      fname += '.parmed'
      const fetchResponse = await fetch(url, {method: 'get'})
      let blob = await fetchResponse.blob()
      console.log(`downloadParmed ${url} ${fname}`, blob)
      saveFile(blob, fname)
      this.popLoading()
    },

    setEditFrames() {
      this.editFrames = []
      for (let iFrameTraj of this.iFrameTrajList) {
        this.editFrames.push({frame: iFrameTraj[0]})
      }
      let frames = _.map(this.editFrames, 'frame')
    },

    async openFramesModal(view) {
      this.setEditFrames()
      window.keyboardLock = true
      this.openModal('frames-edit-modal')
    },

    async clickFrame(iFrame) {

      let widget

      if (this.matrixWidget) {
        widget = this.matrixWidget
      } else if (this.stripWidget) {
        widget = this.stripWidget
      } else {
        return
      }
      let getMatrixValue = (iFrameTraj) => {
        let value = null
        let grid = widget.grid
        let nCol = widget.grid.length
        let nRow = widget.grid[0].length
        for (let i=0; i<nCol; i+=1) {
          for (let j=0; j<nRow; j+=1) {
            let isMatch = false
            let gridValue = grid[i][j]
            if (!grid[i][j].iFrameTraj) {
              continue
            }
            let iFrameTrajCell = grid[i][j].iFrameTraj
            let thisMatch = (iFrameTraj[0] == iFrameTrajCell[0]) && (iFrameTraj[1] == iFrameTrajCell[1])
            if (thisMatch) {
              return gridValue
            }
          }
        }
        return null
      }

      let iFrameTraj = [iFrame, 0]
      let value = getMatrixValue(iFrameTraj)
      if (!value) {
        return
      }
      await widget.clickGridValue(value, true)
    },

    async addFrame(iFrame) {
      await this.clickFrame(iFrame)
      this.setEditFrames()
      this.newFrame = null
    },

    copyFramesToClipboard(text) {
      navigator.clipboard.writeText(text);
    }
  }
}
</script>
