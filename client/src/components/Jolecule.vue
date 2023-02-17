<template lang="pug">
.w-100.overflow-hidden(:key="$route.params.id")

  #fail-modal.modal.fade
    .modal-dialog
      .modal-content
        .modal-header
          h5.modal-title ERROR: Loading trajectory {{ foamId }}
          button.btn-close(data-bs-dismiss="modal")
        .modal-body
          pre {{ errorMsg }}


  .w-100.d-flex.flex-column.user-select-none(style="background-color: #CCC")

    // Top bar
    .w-100.d-flex.flex-row.justify-content-between.mx-2(style="height: 60px")

        .d-flex.flex-grow-1.flex-row.flex-nowrap.align-items-center.text-nowrap.align-middle
          router-link.btn.btn-sm.btn-secondary.me-2(
             to="/" tag="button" style="font-size: 1.5em; width: 50px; height: 50px;"
          )
            i.fas.fa-home
          .text-center(
              style="width: 50px; height: 50px; background-color: #BBB"
          )
            .spinner-grow.spinner-grow.text-primary(style="width: 50px; height: 50px;" v-if="isLoading")
            div(style="width: 50px; height: 50px" v-if="!isLoading") &nbsp;
          // Title tags, fits in space in toolbar
          .flex-grow-1.m-0.ms-2.overflow-hidden(style="height: 50px")
            .d-flex.flex-wrap.d-inline(
              style="width: 100%; font-family: monospace; line-height: 1.1em; font-size: 15px;"
            )
              template(v-for="(key) in Object.keys(title)")
                span(style="color: #888") {{key}}:
                span.ms-1.me-3 {{ title[key] }}

          // Dropdown for energy components
          .ms-2(v-if="opt_keys.length")
            select.form-select.form-select-sm(v-model="key" @change="selectOptKey(key)")
               option(v-for="opt_key in opt_keys" :value="opt_key")
                 | {{opt_key}}

    .w-100.d-flex.flex-row(style="height: calc(100vh - 60px)")

      // The Free-Energy Surface
      #matrix-widget.h-100(:style="matrixStyle" :key="forceFesKey")

      // Traj Strip
      #strip-widget.h-100(:style="stripStyle" :key="forceStripKey")

      // Table of Ligands
      #table.p-2.overflow-scroll(:style="tableStyle")
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
              :class="[isCurrentTableiFrameTraj(row.iFrameTraj) ? 'bg-primary' : '']"
              @mousedown="e => downTableEntry(e, row)"
              @mouseup="e => upTableEntry(e, row)"
              @mousemove="e => moveTableEntry(e, row)"
            )
              td(v-for="val in row.vals") {{val}}

      // Jolecule
      #jolecule-container.h-100(:style="joleculeStyle")

      // Traj Strip
      #view-container.h-100.text-end.m-2(:style="viewStyle" :key="forceViewKey")
        // Alphaspace check box
        .mb-1
          .form-check.input-group-sm
            input.form-check-input(
              type="checkbox"
              v-model="isAlphaSpace"
              @change="toggleAlphaSpace()"
            )
            label.form-check-label alphaspace
        button.mb-1.btn.btn-sm.w-100.btn-secondary.me-2(@click="savePdb")
          | Save PDB
        button.mb-1.btn.btn-sm.w-100.btn-secondary.me-2(@click="saveView")
          | Save View
        template(v-for="view in views")
          .d-flex.flex-row.mb-1.w-100
            button.btn.btn-sm.btn-secondary(
                @click="selectView(view)"
            )
              | {{ view.id }}
            button.ms-1.btn.btn-sm.btn-info(
                @click="deleteView(view)"
            )
              | X


</template>

<style>
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
@media (max-width: 778px) {
}
@media (max-width: 992px) {
}
</style>

<script>
import { getColor } from '../modules/viridis'
import 'bootstrap/dist/css/bootstrap.min.css'
import * as bootstrap from 'bootstrap'
import _ from 'lodash'
import { initEmbedJolecule } from 'jolecule'
import { widgets } from 'jolecule'
import * as rpc from '../modules/rpc'

function isSameVec (v1, v2) {
  if (_.isNil(v1) || _.isNil(v2)) {
    return false
  }
  const n = v1.length
  if (n !== v2.length) {
    return false
  }
  for (let i = 0; i < n; i += 1) {
    if (v1[i] !== v2[i]) {
      return false
    }
  }
  return true
}

function inFrames (iFrameTrajs, iFrameTraj) {
  return _.some(iFrameTrajs, i => isSameVec(i, iFrameTraj))
}

function getIndexOfFrames (iFrameTrajs, iFrameTraj) {
  return _.findIndex(iFrameTrajs, i => isSameVec(i, iFrameTraj))
}


function delFromFrames (iFrameTrajs, iFrameTraj) {
  let i = _.findIndex(iFrameTrajs, i => isSameVec(i, iFrameTraj))
  iFrameTrajs.splice(i, 1)
}

function getFirstValue (matrix) {
  let value
  value = _.first(_.filter(_.flattenDeep(matrix), v => _.has(v, 'iFrameTraj')))
  if (value) {
    return value
  }
  value = _.first(_.filter(_.flattenDeep(matrix), v => _.has(v, 'iFrameTrajs')))
  if (value) {
    return value
  }
  return null
}

class MatrixWidget extends widgets.CanvasWidget {
  constructor (selector, grid, isSparse) {
    super(selector)
    this.iFrameTrajs = []
    this.values = []
    this.isSparse = isSparse
    this.mousePressed = false
    this.borderColor = 'rgb(255, 0, 0, 0.2)'
    this.clickBox = 8
    this.clickBoxHalf = this.clickBox / 2
    this.div.attr('id', `${this.parentDivId}-inner`)
    this.div.css({
      'background-color': '#CCC',
      position: 'relative'
    })
    this.hover = new widgets.PopupText(`#${this.parentDivId}-inner`, 15)
    this.grid = grid
    this.canvasDom.addEventListener('mouseleave', e => this.mouseleave(e))
    this.loadGrid(grid)
    this.resize()
  }

  loadGrid (grid) {
    this.grid = grid
    this.nGridX = this.grid.length
    this.nGridY = this.grid[0].length
    console.log(`FesWidget.loadGrid ${this.nGridX} x ${this.nGridY}`)
    this.draw()
  }

  resize () {
    super.resize()
    this.div.height(this.height())
    this.parentDiv.height(this.height())
    this.draw()
  }

  getValue (i, j) {
    if (i < 0 || j < 0) {
      return {}
    }
    if (i >= this.grid.length || j >= this.grid[0].length) {
      return {}
    }
    return this.grid[i][this.nGridY - j - 1]
  }

  getIFrameTrajFromValue (value) {
    if (_.has(value, 'iFrameTrajs')) {
      if (value.iFrameTrajs.length) {
        return value.iFrameTrajs[0]
      }
    } else if (_.has(value, 'iFrameTraj')) {
      return value.iFrameTraj
    }
    return null
  }

  getIFrameTraj (i, j) {
    let value = this.getValue(i, j)
    return this.getIFrameTrajFromValue(value)
  }

  async loadValues(values) {
    await this.clickGridValue(values[0], false)
    for (let i=1; i<values.length; i+=1) {
      await this.clickGridValue(values[i], true)
    }
  }

  getXFromI (i) {
    return i * this.diffX
  }

  getIFromX (x) {
    return i * this.diffX
  }

  draw () {
    // draw background
    this.diffX = this.width() / this.nGridX
    this.diffY = this.height() / this.nGridY
    for (let i = 0; i < this.nGridX; i += 1) {
      for (let j = 0; j < this.nGridY; j += 1) {
        let color = getColor(this.getValue(i, j).p)
        this.fillRect(
          i * this.diffX,
          j * this.diffY,
          this.diffX + 1,
          this.diffY + 1,
          color
        )
      }
    }
    let boxX = this.diffX
    let boxY = this.diffY
    if (this.isSparse) {
      boxX = _.max([this.diffX, this.clickBox])
      boxY = _.max([this.diffY, this.clickBox])
    }
    let boxXHalf = boxX / 2
    let boxYHalf = boxY / 2
    for (let i = 0; i < this.nGridX; i += 1) {
      for (let j = 0; j < this.nGridY; j += 1) {
        let iFrameTraj = this.getIFrameTraj(i, j)
        if (!iFrameTraj) {
          continue
        }
        if (this.isSparse) {
          this.fillRect(
            i * this.diffX + this.diffX / 2 - boxXHalf,
            j * this.diffY + this.diffY / 2 - boxYHalf,
            boxX,
            boxY,
            this.borderColor
          )
        }
        for (let selectediFrameTraj of this.iFrameTrajs) {
          if (isSameVec(iFrameTraj, selectediFrameTraj)) {
            this.fillRect(
              i * this.diffX + this.diffX / 2 - boxXHalf,
              j * this.diffY + this.diffY / 2 - boxYHalf,
              boxX,
              boxY,
              'red'
            )
          }
        }
      }
    }
  }

  getMouseValue (event) {
    this.getPointer(event)
    let i = Math.floor(this.pointerX / this.diffX)
    let j = Math.floor(this.pointerY / this.diffY)
    let centralValue = this.getValue(i, j)
    if (this.diffX > this.clickBox && this.diffY > this.clickBox) {
      return centralValue
    }
    if (_.get(centralValue, 'iFrameTraj')) {
      return centralValue
    }
    let boxX = _.max([this.diffX, this.clickBox])
    let boxY = _.max([this.diffY, this.clickBox])
    let delta = 1
    while (
      (delta - 1) * this.diffX <= boxX &&
      (delta - 1) * this.diffY <= boxY
    ) {
      for (let i2 = i - delta; i2 <= i + delta; i2 += 1) {
        for (let j2 = j - delta; j2 <= j + delta; j2 += 1) {
          let value = this.getValue(i2, j2)
          if (_.get(value, 'iFrameTraj')) {
            return value
          }
        }
      }
      delta += 1
    }
    return centralValue
  }

  // to be overriden
  async selectGridValue (value, selectOnly) {}

  // to be overriden
  async deselectGridValue (value) {}

  async clickGridValue (value, isShift) {
    if (!value.iFrameTraj) {
      return
    }
    if (isShift) {
      if (inFrames(this.iFrameTrajs, value.iFrameTraj)) {
        delFromFrames(this.iFrameTrajs, value.iFrameTraj)
        await this.deselectGridValue(value)
        let i = getIndexOfFrames(this.iFrameTrajs, value.iFrameTraj)
        this.values.splice(i, 1)
      } else {
        await this.selectGridValue(value, false)
        this.iFrameTrajs.push(value.iFrameTraj)
        this.values.push(value)
      }
    } else {
      await this.selectGridValue(value, true)
      this.iFrameTrajs = [value.iFrameTraj]
      this.values = [value]
    }
    this.draw()
  }

  async handleSelect (event) {
    let value = this.getMouseValue(event)
    let isShift = event.shiftKey
    this.clickGridValue(value, isShift)
  }

  mouseleave (event) {
    this.hover.hide()
  }

  mousemove (event) {
    let value = this.getMouseValue(event)
    let s = ''
    if (value.label) {
      s += `${value.label}`
    }
    if (_.has(value, 'iFrameTraj')) {
      if (s) {
        s += '<br>'
      }
      s += `frame ${value.iFrameTraj}`
    }
    if (s) {
      this.hover.html(s)
      this.hover.move(this.pointerX, this.pointerY)
      if (this.mousePressed) {
        this.handleSelect(event)
      }
    } else {
      this.hover.hide()
    }
  }

  mouseup (event) {
    this.mousePressed = false
  }

  mousedown (event) {
    this.mousePressed = true
    this.handleSelect(event)
  }
}

export default {
  name: 'Jolecule',
  data () {
    return {
      stripWidth: '70px',
      viewWidth: '120px',
      foamId: '',
      mode: '',
      forceFesKey: 1,
      forceStripKey: -1,
      forceViewKey: -2,
      title: {},
      key: '',
      opt_keys: [],
      isAlphaSpace: false,
      isLoading: false,
      nLoaders: 0,
      iFrameTrajs: [],
      table: [],
      tableHeaders: [],
      errorMsg: '',
      views: [],
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

    document.oncontextmenu = _.noop
    document.onkeydown = e => {
      this.onkeydown(e)
    }

    // let backgroundColor = (await rpc.remote.get_config(this.foamId, "background"))?.result;
    let backgroundColor = '#CCC'

    this.jolecule = initEmbedJolecule({
      divTag: '#jolecule-container',
      backgroundColor: backgroundColor,
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
    this.cacheAlphaSpaceByiFrameTraj = {}

    // saves which structures belongs to a loaded frame on display
    this.nStructuresInFrame = []

    await this.loadFoamId(this.$route.params.foamId)

    window.addEventListener('beforeunload', e => this.close())
    window.addEventListener('resize', this.resize)

    this.resize()
    this.popLoading()
  },
  computed: {
    joleculeStyle () {
      if (this.mode === 'strip') {
        return `width: calc(100% - ${this.stripWidth})`
      }
      return 'width: 50%'
    },

    tableStyle () {
      if (this.mode === 'table') {
        return 'width: 50%'
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
        return `width: calc(50% - ${this.stripWidth})`
      } else if (this.mode === 'matrix' || this.mode === 'sparse-matrix') {
        return 'width: 50%'
      }
      return 'display: none'
    }
  },

  methods: {
    pushLoading() {
      this.isLoading = true
      this.nLoaders += 1
    },

    popLoading() {
      this.nLoaders -= 1
      if (this.nLoaders <= 0) {
        this.nLoaders = 0
        this.isLoading = false
      }
    },

    async reload () {
      this.pushLoading()
      await this.$forceUpdate()
      this.mode = (await rpc.remote.get_config(this.foamId, 'mode'))?.result
      this.key = (await rpc.remote.get_config(this.foamId, 'key'))?.result
      this.opt_keys = (
        await rpc.remote.get_config(this.foamId, 'opt_keys')
      )?.result
      await this.$forceUpdate()
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
      this.popLoading()
    },

    async loadFoamId (foamId) {
      console.log('loadFrameId', foamId)
      document.title = '#' + foamId
      this.foamId = foamId
      this.title = {"Connecting": ""}
      this.pushLoading()
      await this.$forceUpdate()

      this.jolecule.clear()
      this.cacheByiFrameTraj = {}
      this.cacheAlphaSpaceByiFrameTraj = {}
      this.nStructuresInFrame = []
      this.iFrameTrajs = []
      if (this.matrixWidget) {
        this.matrixWidget.iFrameTrajs = []
        this.matrixWidget.draw()
      }
      if (this.stripWidget) {
        this.stripWidget.iFrameTrajs = []
        this.stripWidget.draw()
      }

      let response = await rpc.remote.reset_foam_id(this.foamId)
      if (response.error) {
        let myModal = new bootstrap.Modal(document.getElementById('fail-modal'))
        myModal.show()
        this.errorMsg = JSON.stringify(response.error, null, 2)
        this.title = {"Error": `loading FoamId=${this.foamId}`}
      } else {
        this.title = response.result.title
      }
      this.popLoading()

      await this.reload()

      response = await rpc.remote.get_views(this.foamId)
      if (response.result) {
        this.views = response.result
        console.log(`mounted`, _.cloneDeep(this.$route.params), _.cloneDeep(this.$route.query))
        let view = this.getView(this.$route.query.view)
        if (view) {
          this.selectView(view)
        }
      }

    },

    getView(viewId) {
      return _.find(this.views, v => v.id === viewId)
    },

    async get_config (key) {
      this.pushLoading()

      await this.$forceUpdate()
      let response = await rpc.remote.get_config(this.foamId, 'matrix')

      this.popLoading()

      if (response.result) {
        return response.result
      }
      return null
    },

    async loadMatrix (iFrameTraj) {
      let response = await rpc.remote.get_config(this.foamId, 'matrix')
      let matrix = response.result
      if (_.isEmpty(matrix)) {
        return
      }
      let value
      if (_.isNil(iFrameTraj)) {
        value = getFirstValue(matrix)
      } else {
        value = { iFrameTraj }
      }
      let isSparse = this.mode === 'sparse-matrix'
      this.matrixWidget = new MatrixWidget('#matrix-widget', matrix, isSparse)
      this.resize()
      this.matrixWidget.selectGridValue = this.selectMatrixGridValue
      this.matrixWidget.deselectGridValue = this.deselectMatrixGridValue
      await this.matrixWidget.clickGridValue(value)
    },

    async selectMatrixGridValue (value, selectOnly = false) {
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
            !inFrames(this.iFrameTrajs, iFrameTraj)
          ) {
            await this.loadFrameIntoJolecule(iFrameTraj, selectOnly)
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
      if (inFrames(this.iFrameTrajs, iFrameTraj)) {
        await this.deleteFrameFromJolecule(iFrameTraj)
      }
    },

    async loadStrip () {
      let response = await rpc.remote.get_config(this.foamId, 'strip')
      let strip = response.result
      if (_.isEmpty(strip)) {
        strip = [[]]
      }
      let value = getFirstValue(strip)

      this.stripWidget = new MatrixWidget('#strip-widget', strip, false)
      this.resize()
      this.stripWidget.selectGridValue = this.selectStripGridValue
      this.stripWidget.deselectGridValue = this.deselectStripGridValue
      if (value) {
        await this.stripWidget.clickGridValue(value)
      }
    },

    async selectStripGridValue (value, selectOnly) {
      let iFrameTraj = value.iFrameTraj
      if (_.isNil(iFrameTraj)) {
        return
      }
      if (
        this.hasFramesInJolecule() ||
        !inFrames(this.iFrameTrajs, iFrameTraj)
      ) {
        await this.loadFrameIntoJolecule(iFrameTraj, selectOnly)
      }
    },

    async deselectStripGridValue (value) {
      let iFrameTraj = value.iFrameTraj
      if (inFrames(this.iFrameTrajs, iFrameTraj)) {
        await this.deleteFrameFromJolecule(iFrameTraj)
      }
    },

    async loadTable (iFrameTraj) {
      let response = await rpc.remote.get_config(this.foamId, 'table')
      this.table = response.result
      if (_.isEmpty(this.table)) {
        return
      }
      let headers = (await rpc.remote.get_config(this.foamId, 'table_headers'))
        ?.result
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

    async selectTableiFrameTraj (iFrameTraj, selectOnly) {
      await this.loadFrameIntoJolecule(iFrameTraj, selectOnly)
    },

    async downTableEntry (event, row) {
      this.mouseDownInTable = true
      if (event.shiftKey) {
        if (inFrames(this.iFrameTrajs, row.iFrameTraj)) {
          await this.deleteFrameFromJolecule(row.iFrameTraj)
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

    isCurrentTableiFrameTraj (iFrameTraj) {
      return inFrames(this.iFrameTrajs, iFrameTraj)
    },

    resize () {
      if (this.matrixWidget) {
        this.matrixWidget.resize()
      }
      if (this.stripWidget) {
        this.stripWidget.resize()
      }
      this.jolecule.resize()
    },

    async getPdbLines (iFrameTraj) {
      let key = `${iFrameTraj[0]}-${iFrameTraj[1]}`
      let result = []
      if (this.isAlphaSpace) {
        if (key in this.cacheAlphaSpaceByiFrameTraj) {
          console.log(`getPdbLines from cacheAlphaSpaceByiFrameTraj[${key}]`)
          result = this.cacheAlphaSpaceByiFrameTraj[key]
        } else {
          this.pushLoading()
          await this.$forceUpdate()
          let response = await rpc.remote.get_pdb_lines_with_alphaspace(
            this.foamId,
            iFrameTraj
          )
          this.popLoading()
          if (response.result) {
            this.cacheAlphaSpaceByiFrameTraj[key] = response.result
            result = response.result
          }
        }
      } else {
        if (key in this.cacheByiFrameTraj) {
          console.log(`getPdbLines from cacheByiFrameTraj[${key}]`)
          result = this.cacheByiFrameTraj[key]
        } else {
          this.pushLoading()
          await this.$forceUpdate()
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
      return this.nStructuresInFrame.length
    },

    async loadFrameIntoJolecule (iFrameTraj, selectOnly = false) {
      if (this.isFetching) {
        return
      }
      this.isFetching = true
      let pdbLines = await this.getPdbLines(iFrameTraj)
      if (pdbLines) {
        let saveView = this.jolecule.soupView.getCurrentView()
        let pdbId = `frame-${iFrameTraj}`.replace(',', '-')

        let soup = this.jolecule.soupWidget.soup

        let iStructureStart = soup.structureIds.length
          console.log(`loadFrameIntoJolecule add ${_.last(soup.structureIds)}`)
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
        let nStructureLoaded = soup.structureIds.length - iStructureStart

        if (selectOnly && this.hasFramesInJolecule()) {
          let nStructuresToDelete = _.sum(this.nStructuresInFrame)
          while (nStructuresToDelete) {
            let iStructureToDelete =
              soup.structureIds.length - 1 - nStructureLoaded
            let structureId = soup.structureIds[iStructureToDelete]
            this.jolecule.controller.deleteStructure(iStructureToDelete)
            console.log(`loadFrameIntoJolecule delete`, structureId)
            nStructuresToDelete -= 1
          }
          this.jolecule.soupView.setHardCurrentView(saveView)
          this.jolecule.soupWidget.distanceMeasuresWidget.drawFrame()

          this.nStructuresInFrame = []
          this.iFrameTrajs = []
        }

        if (!this.isAlphaSpace) {
          let grid = this.jolecule.soupView.soup.grid
          grid.isElem = {}
          grid.isChanged = true
          this.jolecule.soupView.isUpdateColors = true
        }

        this.nStructuresInFrame.push(nStructureLoaded)
        this.iFrameTrajs.push(iFrameTraj)
        this.jolecule.soupWidget.buildScene()
      }
      this.isFetching = false
    },

    async deleteFrameFromJolecule (iFrameTraj) {
      let i = _.findIndex(this.iFrameTrajs, i => isSameVec(i, iFrameTraj))
      if (_.isNil(i)) {
        return
      }
      if (this.iFrameTrajs.length === 1) {
        return
      }
      let nStructureBefore = _.sum(this.nStructuresInFrame.slice(0, i))
      let nStructureToDelete = this.nStructuresInFrame[i]
      let soup = this.jolecule.soupWidget.soup
      console.log(`deleteFrameFromJolecule before=${soup.structureIds}`)
      while (nStructureToDelete) {
        let iStructureToDelete = nStructureBefore + nStructureToDelete - 1
        this.jolecule.controller.deleteStructure(iStructureToDelete)
        console.log(
          `deleteFrameFromJolecule delete structure ${iStructureToDelete}`
        )
        nStructureToDelete -= 1
      }
      console.log(
        `deleteFrameFromJolecule after=${this.jolecule.soupWidget.soup.structureIds}`
      )
      this.jolecule.soupWidget.buildScene()
      delFromFrames(this.iFrameTrajs, iFrameTraj)
      this.nStructuresInFrame.splice(i, 1)
    },

    savePdb() {
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
      let filename = 'out.pdb';

      let element = document.createElement('a');
      element.setAttribute('href', 'data:text/csv;charset=utf-8,' + encodeURIComponent(text));
      element.setAttribute('download', filename);

      element.style.display = 'none';
      document.body.appendChild(element);

      element.click();
      document.body.removeChild(element);
    },

    async saveView() {
      let viewDict = this.jolecule.soupView.getCurrentView().getDict()
      let nFrameTraj = this.iFrameTrajs
      let view = {
        id: viewDict.view_id.replace("view:", ""),
        viewDict: viewDict,
      }
      if (this.matrixWidget) {
        view.matrixWidgetValues = this.matrixWidget.values
      }
      if (this.stripWidget) {
        view.stripWidgetValues = this.stripWidget.values
      }
      console.log(`saveView`, _.cloneDeep(view))
      this.views.push(view)
      await rpc.remote.add_view(this.foamId, view)
    },

    async selectView(view) {
      console.log(`selectView`, _.cloneDeep(view))
      if (_.has(view, "matrixWidgetValues")) {
        this.matrixWidget.loadValues(view.matrixWidgetValues)
      }
      if (_.has(view, "stripWidgetValues")) {
        this.stripWidget.loadValues(view.stripWidgetValues)
      }
      let newView = this.jolecule.soupView.getCurrentView()
      newView.setFromDict(view.viewDict)
      history.pushState(
        {},
        null,
        '#' + this.$route.path + '?view=' + view.id
      )
      this.controller.setTargetView(newView)
    },

    async deleteView(view) {
      let i = this.views.indexOf(view)
      this.views.splice(i, 1)
      await rpc.remote.delete_view(this.foamId, view)
    },

    async toggleAlphaSpace () {
      this.loadFrameIntoJolecule(_.last(this.iFrameTrajs))
    },

    async selectOptKey (key) {
      let iFrameTraj = _.last(this.iFrameTrajs)
      console.log('selectOptKey', key, iFrameTraj)
      await rpc.remote.select_new_key(this.foamId, key)
      this.forceFesKey = Math.random()
      this.forceStripKey = Math.random()
      await this.loadMatrix(iFrameTraj)
    },

    async close () {
      await rpc.remote.kill()
    },

    onkeydown (e) {
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
        if (event.metaKey) {
          this.controller.selectAllSidechains(true)
          event.preventDefault()
        } else {
          this.soupWidget.atomLabelDialog()
        }
      } else if (event.keyCode === 27) {
        this.controller.clear()
      } else if (c === 'Z' || event.keyCode === 13) {
        this.controller.zoomToSelection()
      }
    }
  }
}
</script>
