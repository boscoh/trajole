// vue component in pug
<template lang="pug">
  div

    .mb-2.d-flex.flex-row.flex-nowrap

      button.me-2.btn.btn-small.btn-outline-secondary(
        @click="edit" v-if="mode === 'display'"
      )
        | Edit
      button.me-2.btn.btn-small.btn-outline-secondary(
        @click="display" v-if="mode === 'edit'"
      )
        | View
      button.btn.btn-small.btn-outline-secondary(
        @click="slide" v-if="mode !== 'slide'"
      )
        | Slide Show

    table.table(v-if="table && mode==='display'" style="cursor: pointer")
      thead(v-if="headers")
        tr
          th(v-for="h in headers")
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
          v-for="(row, i) in table.rows"
          :key="i"
          :class="[isIFrameTrajSelected(row.iFrameTraj) ? 'bg-primary' : '']"
          @mousedown="e => downTableEntry(e, i)"
          @mouseup="e => upTableEntry(e, i)"
          @mousemove="e => moveTableEntry(e, i)"
        )
          td.text-nowrap(v-for="val in row.vals") {{val}}

    div(v-if="table && mode==='edit'")

      .mb-1.d-flex.flex-row.flex-nowrap.align-items-center
        button.btn.btn-small.btn-outline-secondary(
          @click="addAlignedRows"
        )
          .text-nowrap Seq Align
        label.form-label FoamId1
        input.form-control(
          style="width: 6em"
          type="number"
          v-model="foamId1"
        )
        label.form-label FoamId2
        input.form-control(
          style="width: 6em"
          type="number"
          v-model="foamId2"
        )
        label.form-label Residues
        input.form-control(
          style="width: 4em"
          type="number"
          v-model="rangeStart"
        )
        input.ms-1.form-control(
          style="width: 4em"
          type="number"
          v-model="rangeEnd"
        )

      .mb-1.d-flex.flex-row.flex-nowrap.align-items-center
        button.btn.btn-small.btn-outline-secondary(
          @click="add"
        )
          .text-nowrap Add Row
        label.form-label FoamId
        input.form-control(
          style="width: 6em"
          type="number"
          v-model="addFoamId"
        )
        label.form-label Frame
        input.form-control(
          style="width: 5em"
          type="number"
          v-model="addFrame"
        )
        label.form-label AtomMask
        input.form-control(
          style="width: 20em"
          type="str"
          v-model="addAtomMask"
        )

      .mb-1.d-flex.flex-row.flex-nowrap.align-items-center
        button.btn.btn-small.btn-outline-secondary(
          @click="updateRow"
        )
          .text-nowrap Update Row {{ iRowUpdate }}
        button.ms-2.btn.btn-small.btn-outline-secondary(
          @click="remove(iRowUpdate)"
        )
          i.fas.fa-trash
        label.form-label FoamId
        input.form-control(
          style="width: 6em"
          type="number"
          v-model="updateFoamId"
        )
        label.form-label Frame
        input.form-control(
          style="width: 5em"
          type="number"
          v-model="updateFrame"
        )
        label.form-label AtomMask
        input.form-control(
          style="width: 20em"
          type="str"
          v-model="updateAtomMask"
        )

      table.table(style="cursor: pointer")
        thead(v-if="headers")
          tr
            th #
            th(v-if="iFoamCol !== null")
              span.me-1 {{ headers[iFoamCol].value }}
            th(v-if="iFrameCol !== null")
              span.me-1 {{ headers[iFrameCol].value }}
            th(v-if="iAtomMask !== null")
              span.me-1 {{ headers[iAtomMask].value }}
            th
        tbody
          tr(
            v-for="(row, i) in table.rows"
            :key="i"
            :class="[isIFrameTrajSelected(row.iFrameTraj) ? 'bg-primary' : '']"
            @mousedown="e => downTableEntry(e, i)"
            @mouseup="e => upTableEntry(e, i)"
            @mousemove="e => moveTableEntry(e, i)"
          )
            td {{ i }}
            td.text-nowrap(
              v-if="iFoamCol !== null"
            )
              | {{row.vals[iFoamCol]}}
            td.text-nowrap(
              v-if="iFrameCol !== null"
            )
              | {{row.vals[iFrameCol]}}
            td.text-nowrap(
              v-if="iAtomMask !== null"
            )
              | {{row.vals[iAtomMask]}}

</template>

<style scoped>
label {
  padding-left: 0.7em;
  padding-right: 0.2em;
  margin: 0;
  font-size: 0.75em;
}
</style>
<script>
import * as rpc from '../modules/rpc'
import _ from 'lodash'
import * as bootstrap from 'bootstrap'
import { inFrames, getIndexOfFrames, isSameVec } from '../modules/util'

export default {
  data () {
    return {
      mode: 'display', // 'edit'
      table: {},
      headers: [],
      iFoamCol: null,
      iFrameCol: null,
      iAtomMask: null,
      addFoamId: null,
      addFrame: null,
      addAtomMask: null,
      foamId1: null,
      foamId2: null,
      rangeStart: null,
      rangeEnd: null,
      updateFoamId: null,
      updateFrame: null,
      updateAtomMask: null,
      iRowUpdate: 0
    }
  },
  computed: {
    iFrameTrajList: {
      get () {
        return this.$store.state.iFrameTrajList
      },
      set () {}
    }
  },
  methods: {
    async loadTable (mode = 'display') {
      this.mode = mode
      this.$store.commit('setItem', { foamId: this.$store.state.ensembleId })
      this.$store.commit('setItem', {
        tags: { ensemble: this.$store.state.ensembleId + '.csv' }
      })

      this.$store.commit('pushLoading')
      let response = await rpc.remote.load_ensemble_id(
        this.$store.state.ensembleId
      )
      this.$store.commit('popLoading')

      let result = response.result ? response.result : null
      this.table = result
      console.log('loadtable', _.cloneDeep(this.table))

      this.headers = _.map(result.headers, (h, i) => ({
        value: h,
        status: 'none',
        iCol: i
      }))
      this.iFoamCol = this.table.iFoamCol
      this.iFrameCol = this.table.iFrameCol
      this.iAtomMask = this.table.iAtomMask

      this.setUpdate(this.iRowUpdate)
      if (this.table.rows.length) {
        return this.table.rows[0].iFrameTraj
      } else {
        return null
      }
    },

    isIFrameTrajSelected (iFrameTraj) {
      return inFrames(this.iFrameTrajList, iFrameTraj)
    },

    async selectIFrameTraj (selectIFrameTraj, thisFrameOnly) {
      console.log(
        'selectIFrameTraj',
        selectIFrameTraj,
        `thisFrameOnly=${thisFrameOnly}`,
        _.cloneDeep(this.iFrameTrajList)
      )
      if (thisFrameOnly) {
        await rpc.remote.clear_ensemble_cache(this.$store.state.ensembleId)
      }
      this.$store.commit('addLoad', {
        iFrameTraj: _.cloneDeep(selectIFrameTraj),
        thisFrameOnly: !!thisFrameOnly
      })
    },

    deleteIFrameTraj (iFrameTraj) {
      this.$store.commit('addDumpIFrameTraj', iFrameTraj)
      console.log('deleteIFrameTraj', _.cloneDeep(iFrameTraj))
    },

    setUpdate (iRow) {
      if (iRow < this.table.rows.length) {
        let row = this.table.rows[iRow]
        this.iRowUpdate = iRow
        this.updateFoamId = row.iFrameTraj[1]
        this.updateFrame = row.iFrameTraj[0]
        if (row.iFrameTraj.length > 2) {
          this.updateAtomMask = row.iFrameTraj[2]
        }
      }
    },

    async downTableEntry (event, iRow) {
      this.setUpdate(iRow)
      this.mouseDownInTable = true
      let iFrameTraj = this.table.rows[iRow].iFrameTraj
      if (!iFrameTraj) {
        return
      }
      if (event.shiftKey) {
        if (inFrames(this.iFrameTrajList, iFrameTraj)) {
          if (this.iFrameTrajList.length > 1) {
            this.deleteIFrameTraj(iFrameTraj)
          }
          return
        }
      }
      this.selectIFrameTraj(iFrameTraj, !event.shiftKey)
    },

    async moveTableEntry (event, iRow) {
      let iFrameTraj = this.table.rows[iRow].iFrameTraj
      if (this.mouseDownInTable && iFrameTraj) {
        this.selectIFrameTraj(iFrameTraj, !event.shiftKey)
      }
    },

    async upTableEntry (event, iRow) {
      this.mouseDownInTable = false
    },

    async sortTable (iCol, status) {
      let newStatus = 'up'
      if (status === 'up') {
        newStatus = 'down'
      }
      for (let iCol = 0; iCol < this.headers.length; iCol += 1) {
        this.headers[iCol].status = 'none'
      }
      this.headers[iCol].status = newStatus
      if (newStatus !== 'none') {
        if (iCol === 0) {
          this.table.rows = _.sortBy(this.table.rows, row => row.vals[iCol])
          if (newStatus === 'down') {
            this.table.rows = _.reverse(this.table.rows)
          }
        } else {
          let multiplier = newStatus === 'up' ? 1 : -1
          this.table.rows = _.sortBy(
            this.table.rows,
            row => multiplier * row.vals[iCol]
          )
        }
      }
    },

    edit () {
      this.$router.push(`/editensemble/${this.$store.state.ensembleId}`)
    },

    display () {
      this.$router.push(`/ensemble/${this.$store.state.ensembleId}`)
    },

    slide () {
      this.$router.push(`/slideensemble/${this.$store.state.ensembleId}`)
    },

    async addAlignedRows () {
      this.$store.commit('pushLoading')
      let response = await rpc.remote.add_aligned_rows(
        this.$store.state.ensembleId,
        _.parseInt(this.foamId1),
        _.parseInt(this.foamId2),
        _.parseInt(this.rangeStart),
        _.parseInt(this.rangeEnd)
      )
      await this.loadTable(this.mode)
      console.log(response.result)
      for (let iFrameTraj of response.result) {
        this.selectIFrameTraj(iFrameTraj)
      }
      this.$store.commit('popLoading')
    },

    async add () {
      this.$store.commit('pushLoading')
      let response = await rpc.remote.add_to_ensemble(
        this.$store.state.ensembleId,
        _.parseInt(this.addFoamId),
        _.parseInt(this.addFrame),
        this.addAtomMask
      )
      await this.loadTable(this.mode)
      this.selectIFrameTraj([this.addFrame, this.addFoamId, this.addAtomMask])
      this.$store.commit('popLoading')
    },

    async updateRow () {
      this.$store.commit('pushLoading')
      let response = await rpc.remote.update_ensemble_row(
        this.$store.state.ensembleId,
        _.parseInt(this.iRowUpdate),
        _.parseInt(this.updateFoamId),
        _.parseInt(this.updateFrame),
        this.updateAtomMask
      )
      await this.loadTable(this.mode)
      this.selectIFrameTraj([
        _.parseInt(this.updateFrame),
        _.parseInt(this.updateFoamId),
        this.updateAtomMask
      ])
      this.$store.commit('popLoading')
    },

    async remove (i) {
      this.$store.commit('pushLoading')
      this.table.rows.splice(i, 1)
      let response = await rpc.remote.remove_from_ensemble(
        this.$store.state.ensembleId,
        i
      )
      await this.loadTable(this.mode)
      this.$store.commit('popLoading')
    }
  }
}
</script>
