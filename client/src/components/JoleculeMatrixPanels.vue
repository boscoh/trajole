<template lang="pug">
.d-flex.flex-row.h-100

    #fail-modal.modal.fade
        .modal-dialog
            .modal-content
                .modal-header
                    h5.modal-title ERROR: Loading trajectory {{ foamId }}
                    button.btn-close(data-bs-dismiss="modal")
                .modal-body
                    pre {{ errorMsg }}

    #matrix-widget.h-100(:style="matrixStyle" :key="forceMatrixKey")

    .ms-2.mt-n2(v-if="optKeys.length" style="position: absolute;")
        .dropdown
            button.btn.btn-sm.btn-secondary.dropdown-toggle(data-bs-toggle="dropdown" type="button")
                | {{ key }}
            ul.dropdown-menu
                li.dropdown-item(v-for="k of optKeys" @click="selectOptKey(k)") {{ k }}

    #strip-widget.h-100(:style="stripStyle" :key="forceStripKey")

    #table.p-2.me-2.overflow-scroll(:style="tableStyle")
        ligand-table(ref="table")

    ///////////////////////
    #jolecule-container.h-100(:style="joleculeStyle")
    ///////////////////////

</template>

<script>
import 'bootstrap/dist/css/bootstrap.min.css'
import * as bootstrap from 'bootstrap'
import _ from 'lodash'
import { initEmbedJolecule, v3 } from 'jolecule'
import { MatrixWidget } from '../modules/matrixwidget'
import {
    delay,
    getFirstValue,
    getPdbText,
    inFrames,
    isSameVec,
    saveTextFile,
} from '../modules/util'
import { aysnc_rpc } from '../modules/rpc'
import LigandTable from './LigandTable.vue'

export default {
    components: {
        LigandTable,
    },
    data () {
        return {
            forceMatrixKey: 1,
            forceStripKey: -1,
            isAsCommunities: false,
            isAsPockets: false,
            displayMode: '', // "strip", "slide", "table", "matrix-strip", "matrix", "sparse-matrix"
            errorMsg: '',
            joleculeStyle: 'height: 100%',
            tableStyle: 'display: none',
            stripStyle: 'display: none',
            matrixStyle: 'display: none',
            optKeys: [],
            key: '',
        }
    },
    async mounted () {
        document.oncontextmenu = _.noop

        window.addEventListener('keydown', e => {
            this.onkeydown(e)
        })

        this.table = this.$refs.table

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
            isToolbarOnTop: true,
        })
        this.controller = this.jolecule.soupWidget.controller
        this.soupView = this.jolecule.soupView

        this.initView = null

        this.stripWidth = '70px'
        this.actionsStripWidth = '200px'

        this.errorModal = new bootstrap.Modal(
            document.getElementById('fail-modal')
        )

        window.addEventListener('beforeunload', e => this.close())
        window.addEventListener('resize', this.resize)

        this.resize()

        this.initRemoteRpc()
    },
    computed: {
        foamId () {
            return this.$store.state.foamId
        },
        ensembleId () {
            return this.$store.state.ensembleId
        },
        selectView () {
            return this.$store.state.selectView
        },
        iFrameTrajList () {
            return this.$store.state.iFrameTrajList
        },
        loadIFrameTrajList () {
            return this.$store.state.loadIFrameTrajList
        },
        dumpIFrameTrajList () {
            return this.$store.state.dumpIFrameTrajList
        },
    },
    watch: {
        selectView (to, from) {
            if (!_.isNull(to)) {
                this.loadView(to)
            }
        },
        loadIFrameTrajList (to, from) {
            if (to.length) {
                let entry = to.shift()
                console.log(`watch loadIFrameTrajList`, _.cloneDeep(entry))
                this.loadFrameIntoJolecule(
                    entry.iFrameTraj,
                    entry.thisFrameOnly,
                    false
                )
            }
        },
        dumpIFrameTrajList (to, from) {
            if (to.length) {
                let entry = to.shift()
                console.log(
                    `watch dumpIFrameTrajList`,
                    _.cloneDeep(entry),
                    _.cloneDeep(this.dumpIFrameTrajList)
                )
                this.deleteFrame(entry)
            }
        },
    },
    methods: {
        initRemoteRpc () {
            let _this = this

            class RemoteResultRpcProxy {
                constructor () {
                    return new Proxy(this, {
                        get (target, prop) {
                            return async function () {
                                _this.pushLoading()

                                let response = await aysnc_rpc(
                                    prop,
                                    ...arguments
                                )

                                let result = null
                                if (!response.result) {
                                    _this.handleError(response)
                                } else {
                                    result = response.result
                                }

                                _this.popLoading()

                                return result
                            }
                        },
                    })
                }
            }

            this.remote = new RemoteResultRpcProxy()
        },

        resize () {
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

        pushLoading (loadingMsg = null) {
            this.$store.commit('pushLoading')
            if (!_.isNull(loadingMsg)) {
                this.$store.commit('setItem', { loadingMsg })
            }
            this.$forceUpdate()
        },

        popLoading (loadingMsg = null) {
            this.$store.commit('popLoading')
            if (!_.isNull(loadingMsg)) {
                this.$store.commit('setItem', { loadingMsg })
            }
            this.$forceUpdate()
        },

        handleError (response) {
            if (!response.error) {
                return
            }
            this.errorModal.show()
            if (_.last(response.error.message).includes('FileNotFoundError')) {
                this.errorMsg = `Trajectory #${this.foamId} is empty`
            } else {
                this.errorMsg = JSON.stringify(response.error, null, 2)
            }
            this.$store.commit('setItem', {
                tags: { Error: `loading FoamId=${this.foamId}` },
            })
        },

        async getConfig (key) {
            return await this.remote.get_config(this.foamId, key)
        },

        resetWidgets () {
            console.log('resetWidgets')
            this.forceMatrixKey = Math.random()
            this.forceStripKey = Math.random()
            this.$forceUpdate()
        },

        async loadFoamId (foamId, frames, viewId) {
            this.pushLoading()

            this.clearPage()

            console.log(
                `loadFoamId(foamId=${foamId}, frames=${frames}, viewId=${viewId})`
            )
            document.title = '#' + foamId
            this.$store.commit('setItem', { foamId })

            let result

            result = await this.remote.reset_foam_id(this.foamId)
            if (result) {
                this.$store.commit('setItem', { tags: result.title })
            }

            this.displayMode = await this.getConfig('mode')

            this.resetStyles()

            this.loadMetadata()

            let initView = null

            result = await this.remote.get_views(this.foamId)
            if (result) {
                this.views = result
                this.$store.commit('setItem', { views: this.views })
                if (viewId && this.views) {
                    let view = _.find(this.views, v => v.id === viewId)
                    if (view) {
                        initView = view
                    }
                }
            }

            let iFrameTraj
            if (this.displayMode === 'strip') {
                iFrameTraj = await this.loadStrip()
            } else if (
                this.displayMode === 'sparse-matrix' ||
                this.displayMode === 'matrix'
            ) {
                iFrameTraj = await this.loadMatrix()
            } else if (this.displayMode.includes('matrix-strip')) {
                await this.loadStrip()
                iFrameTraj = await this.loadMatrix()
            } else if (
                this.displayMode === 'table' ||
                this.displayMode === 'slide'
            ) {
                iFrameTraj = await this.table.loadTable()
            } else if (this.displayMode === 'frame') {
                iFrameTraj = [0, 0]
            }

            await this.loadFrameIntoJolecule(iFrameTraj, true)

            if (!initView) {
                if (this.matrixWidget || this.stripWidget) {
                    if (frames) {
                        let n = 0
                        for (let frame of frames) {
                            await this.loadFrameIntoJolecule(
                                [frame, 0],
                                n === 0
                            )
                            n += 1
                        }
                    }
                }
                await this.selectLigand()
            }

            if (initView) {
                await this.loadView(initView)
            }

            this.resize()
            this.popLoading()
        },

        async loadEnsemble (
            ensembleId,
            viewId = null,
            ensembleMode = 'display'
        ) {
            console.log(`loadEnsemble(ensembleId=${ensembleId})`)
            this.pushLoading()
            this.clearPage()

            if (ensembleMode === 'slide') {
                this.displayMode = 'slide'
            } else {
                this.displayMode = 'table'
            }
            this.resetStyles()

            document.title = '#' + ensembleId
            this.$store.commit('setItem', { ensembleId })
            this.$store.commit('setItem', { foamId: ensembleId })

            await this.table.loadTable(ensembleMode)

            let result = await this.remote.get_views(ensembleId)
            if (result) {
                this.views = result
                this.$store.commit('setItem', { views: this.views })
                if (viewId && this.views) {
                    let view = _.find(this.views, v => v.id === viewId)
                    if (view) {
                        await this.loadView(view)
                    }
                }
            }

            await delay(500)
            this.resize()
            this.popLoading()
        },

        clearPage () {
            this.$store.commit('setItem', { foamId: '' })
            this.$store.commit('setItem', { ensembleId: '' })
            this.$store.commit('setItem', { viewId: '' })
            this.$store.commit('setItem', { minFrame: null })
            this.$store.commit('setItem', { setDatasets: [] })
            this.$store.commit('setItem', { tags: {} })
            this.$store.commit('setItem', { iFrameTrajList: [] })
            this.$store.commit('setItem', { loadIFrameTrajList: [] })
            this.$store.commit('setItem', { dumpIFrameTrajList: [] })
            this.$store.commit('setItem', { datasets: [] })

            this.jolecule.clear()
            this.cacheByiFrameTraj = {}
            this.cacheAsCommunitiesByiFrameTraj = {}
            this.cacheAsPocketsByiFrameTraj = {}
            this.nStructureInFrameList = []

            this.resetWidgets()
            if (this.matrixWidget) {
                this.matrixWidget.values = []
                this.matrixWidget.draw()
            }
            if (this.stripWidget) {
                this.stripWidget.values = []
                this.stripWidget.draw()
            }
        },

        resetStyles () {
            let result
            if (
                !this.displayMode ||
                this.displayMode === 'frame' ||
                this.displayMode === 'slide'
            ) {
                result = `width: calc(100%);`
            } else if (this.displayMode === 'strip') {
                result = `width: calc(100% - ${this.stripWidth});`
            } else {
                result = `width: calc(50%)`
            }
            this.joleculeStyle = result

            if (this.displayMode === 'table') {
                result = `width: calc(50%)`
            } else {
                result = 'display: none'
            }
            this.tableStyle = result

            if (
                this.displayMode === 'matrix-strip' ||
                this.displayMode === 'strip'
            ) {
                result = `width: ${this.stripWidth}`
            } else {
                result = 'display: none'
            }
            this.stripStyle = result

            if (this.displayMode === 'matrix-strip') {
                result = `width: calc(50% - ${this.stripWidth})`
            } else if (
                this.displayMode === 'matrix' ||
                this.displayMode === 'sparse-matrix'
            ) {
                result = `width: calc(50%)`
            } else {
                result = 'display: none'
            }
            this.matrixStyle = result

            this.$forceUpdate()
        },

        selectLigand () {
            let soup = this.jolecule.soup
            let residue = soup.getResidueProxy()
            console.log(`selectLigand nRes`, soup.getResidueCount())
            for (let i = 0; i < soup.getResidueCount(); i += 1) {
                residue.iRes = i
                if (_.includes(['LIG', 'UNK', 'UNL'], residue.resType)) {
                    let atomIndices = residue.getAtomIndices()
                    let ligandCenter = soup.getCenter(atomIndices)

                    let maxDist = 0
                    let maxPos = v3.create(0, 0, 0)
                    let atom = soup.getAtomProxy()
                    for (let iAtom of atomIndices) {
                        let pos = atom.load(iAtom).pos
                        let dist = v3.distance(ligandCenter, pos)
                        if (dist > maxDist) {
                            maxPos = pos
                            maxDist = dist
                        }
                    }

                    let systemCenter = soup.getCenter(
                        _.range(soup.getAtomCount())
                    )

                    let zoom = 50
                    let inVec = v3
                        .diff(systemCenter, ligandCenter)
                        .normalize()
                        .multiplyScalar(zoom)
                    let maxVec = v3.diff(maxPos, ligandCenter)
                    let upVec = v3.perpendicular(maxVec, inVec).normalize()

                    let soupView = this.jolecule.soupView
                    let view = soupView.getCurrentView()
                    view.cameraParams.focus = ligandCenter
                    view.cameraParams.position = ligandCenter.clone().sub(inVec)
                    view.cameraParams.up = upVec
                    view.cameraParams.zFront = -soup.maxLength / 2
                    view.cameraParams.zBack = soup.maxLength / 2
                    view.cameraParams.zoom = zoom

                    console.log(`selectLigand view`, _.cloneDeep(view))
                    this.jolecule.controller.setTargetView(view)
                    return
                }
            }
            console.log(`selectLigand no ligand found`)
        },

        async loadMetadata () {
            this.pushLoading()
            this.key = await this.getConfig('key')
            let result = await this.getConfig('opt_keys')
            if (result) {
                this.optKeys = result
            }
            let datasets = await this.remote.get_json_datasets(this.foamId)
            if (datasets) {
                this.$store.commit('setItem', { datasets })
            }
            let tags = await this.remote.get_tags(this.foamId)
            if (tags) {
                this.$store.commit('setItem', { tags })
            }
            let minFrame = await this.remote.get_min_frame(this.foamId)
            if (!_.isNull(minFrame)) {
                this.$store.commit('setItem', { minFrame })
                console.log('minFrame', minFrame)
            }
            this.popLoading()
        },

        async loadMatrix (iFrameTraj) {
            this.pushLoading('Matrix...')
            let matrix = await this.getConfig('matrix')
            this.popLoading('Connecting...')
            if (_.isEmpty(matrix)) {
                return
            }
            let value = _.isNil(iFrameTraj)
                ? getFirstValue(matrix)
                : { iFrameTraj }
            let isSparse = this.displayMode === 'sparse-matrix'
            this.matrixWidget = new MatrixWidget(
                '#matrix-widget',
                matrix,
                isSparse
            )
            this.resize()
            this.matrixWidget.selectGridValue = this.selectMatrixGridValue
            this.matrixWidget.deselectGridValue = this.deselectMatrixGridValue
            return value.iFrameTraj
        },

        async selectMatrixGridValue (value, thisFrameOnly = false) {
            if (this.stripWidget && _.has(value, 'iFrameTrajs')) {
                let label = value.label
                let iFrameTrajs = value.iFrameTrajs
                let n = iFrameTrajs.length
                let strip = _.map(iFrameTrajs, (iFrameTraj, i) => ({
                    p: i / n,
                    label,
                    iFrameTraj,
                }))
                this.stripWidget.loadGrid([strip])
                let firstValue = getFirstValue([[strip]])
                await this.stripWidget.clickGridValue(firstValue, thisFrameOnly)
            } else {
                let iFrameTraj = value.iFrameTraj
                if (!this.isIFrameTrajSelected(iFrameTraj)) {
                    await this.loadFrameIntoJolecule(iFrameTraj, thisFrameOnly)
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
            if (this.isIFrameTrajSelected(iFrameTraj)) {
                this.$store.commit('addDumpIFrameTraj', iFrameTraj)
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
            console.log('firstValue', value)
            if (_.isNil(value)) {
                return null
            } else {
                return value.iFrameTraj
            }
        },

        async selectStripGridValue (value, thisFrameOnly) {
            let iFrameTraj = value.iFrameTraj
            if (_.isNil(iFrameTraj)) {
                return
            }
            if (
                this.hasFramesInJolecule() ||
                !this.isIFrameTrajSelected(iFrameTraj)
            ) {
                await this.loadFrameIntoJolecule(iFrameTraj, thisFrameOnly)
            }
        },

        async deselectStripGridValue (value) {
            let iFrameTraj = value.iFrameTraj
            if (this.isIFrameTrajSelected(iFrameTraj)) {
                await this.deleteFrame(iFrameTraj)
            }
        },

        isIFrameTrajSelected (iFrameTraj) {
            return inFrames(this.iFrameTrajList, iFrameTraj)
        },

        async getPdbLines (iFrameTraj, useCache = true) {
            this.pushLoading('Frames...')
            let key = iFrameTraj.toString()
            let result = []
            if (this.isAsCommunities) {
                if (useCache && key in this.cacheAsCommunitiesByiFrameTraj) {
                    console.log(
                        `getPdbLines from cacheAsCommunitiesByiFrameTraj[${key}]`
                    )
                    result = this.cacheAsCommunitiesByiFrameTraj[key]
                } else {
                    let response = await this.remote.get_pdb_lines_with_as_communities(
                        this.foamId,
                        iFrameTraj
                    )
                    if (response) {
                        this.cacheAsCommunitiesByiFrameTraj[key] = response
                        result = response
                    }
                }
            } else if (this.isAsPockets) {
                if (useCache && key in this.cacheAsPocketsByiFrameTraj) {
                    console.log(
                        `getPdbLines from cacheAsPocketsByiFrameTraj[${key}]`
                    )
                    result = this.cacheAsPocketsByiFrameTraj[key]
                } else {
                    let response = await this.remote.get_pdb_lines_with_as_pockets(
                        this.foamId,
                        iFrameTraj
                    )
                    if (response) {
                        this.cacheAsPocketsByiFrameTraj[key] = response
                        result = response
                    }
                }
            } else {
                if (useCache && key in this.cacheByiFrameTraj) {
                    console.log(`getPdbLines from cacheByiFrameTraj[${key}]`)
                    result = this.cacheByiFrameTraj[key]
                } else {
                    let response = await this.remote.get_pdb_lines(
                        this.foamId,
                        iFrameTraj
                    )
                    if (response) {
                        this.cacheByiFrameTraj[key] = response
                        result = response
                    }
                }
            }
            this.popLoading('Connecting...')
            return result
        },

        hasFramesInJolecule () {
            return this.nStructureInFrameList.length
        },

        updateWidgetValues () {
            if (!this.ensembleId) {
                let frames = _.map(this.iFrameTrajList, x => x[0])
                history.pushState(
                    {},
                    null,
                    '#' + this.$route.path + '?frame=' + frames.join(',')
                )
                if (this.stripWidget) {
                    this.stripWidget.resetValuesFromFrames(this.iFrameTrajList)
                    this.stripWidget.draw()
                }
                if (this.matrixWidget) {
                    this.matrixWidget.resetValuesFromFrames(this.iFrameTrajList)
                    this.matrixWidget.draw()
                }
            }
        },

        async loadFrameIntoJolecule (
            iFrameTraj,
            thisFrameOnly = false,
            useCache = true
        ) {
            if (this.isFetching) {
                return
            }
            this.isFetching = true
            let pdbLines = await this.getPdbLines(iFrameTraj, useCache)
            if (pdbLines) {
                let saveCurrentView = null
                let frameStr = iFrameTraj.slice(0, 2)
                let pdbId = `frame-${frameStr}`.replace(',', '-')
                let soup = this.jolecule.soupWidget.soup
                let nStructurePrev = soup.structureIds.length
                if (nStructurePrev > 0) {
                    saveCurrentView = this.jolecule.soupView.getCurrentView()
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
                        async asyncDeleteViews () {},
                    },
                    false
                )

                let nStructureInThisFrame =
                    soup.structureIds.length - nStructurePrev
                if (thisFrameOnly && this.hasFramesInJolecule()) {
                    let iLastStructureToDelete =
                        soup.structureIds.length - 1 - nStructureInThisFrame
                    for (let i = iLastStructureToDelete; i >= 0; i -= 1) {
                        console.log(
                            `loadFrameIntoJolecule delete`,
                            soup.structureIds[i]
                        )
                        this.jolecule.controller.deleteStructure(i)
                    }
                    this.nStructureInFrameList = []
                    this.$store.commit('setItem', { iFrameTrajList: [] })
                }
                this.nStructureInFrameList.push(nStructureInThisFrame)
                this.$store.commit('addIFrameTraj', iFrameTraj)

                console.log(
                    'added iFrameTrajList',
                    _.cloneDeep(this.iFrameTrajList)
                )

                if (saveCurrentView) {
                    this.jolecule.soupView.setHardCurrentView(saveCurrentView)
                }
                this.jolecule.soupWidget.distanceMeasuresWidget.drawFrame()
                if (!this.isAsCommunities && !this.isAsPockets) {
                    this.clearGridDisplay()
                }
                this.jolecule.soupWidget.buildScene()
            }
            this.isFetching = false
            this.updateWidgetValues()
        },

        async reloadLastFrameOfJolecule () {
            if (this.isFetching) {
                return
            }
            this.isFetching = true
            let iFrameTraj = _.last(this.iFrameTrajList)

            console.log(
                'reloadLastFrameOfJolecule iFrameTraj',
                _.cloneDeep(this.iFrameTrajList)
            )

            let pdbLines = await this.getPdbLines(iFrameTraj)
            if (pdbLines) {
                let saveCurrentView = this.jolecule.soupView.getCurrentView()

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
                        async asyncDeleteViews () {},
                    },
                    false
                )
                soup.structureIds[soup.structureIds.length - 1] = structureId

                // delete the entire frame to clear potential grid atoms
                let nStructure = _.last(this.nStructureInFrameList)
                let i = this.iFrameTrajList.length - 1
                await this.deleteItemFromIFrameTrajList(i)
                this.nStructureInFrameList.splice(i, 1)

                // recount the grids after removing the grids from
                // the deleted frame
                soup.findGridLimits()

                // add back iFrameTraj without rebuilding whole thing
                this.nStructureInFrameList.push(nStructure)
                this.$store.commit('addIFrameTraj', iFrameTraj)

                this.jolecule.soupView.setHardCurrentView(saveCurrentView)
                this.jolecule.soupWidget.distanceMeasuresWidget.drawFrame()
                if (!this.isAsCommunities && !this.isAsPockets) {
                    this.clearGridDisplay()
                }
                this.jolecule.soupWidget.buildScene()
            }

            this.isFetching = false
        },

        async deleteFrame (delIFrameTraj) {
            let i = _.findIndex(this.iFrameTrajList, iFrameTraj =>
                isSameVec(iFrameTraj, delIFrameTraj)
            )
            if (!_.isNil(i)) {
                await this.deleteItemFromIFrameTrajList(i)
            }
            this.updateWidgetValues()
        },

        async deleteItemFromIFrameTrajList (i) {
            let nStructureBefore = _.sum(this.nStructureInFrameList.slice(0, i))
            let nStructureToDelete = this.nStructureInFrameList[i]
            let soup = this.jolecule.soupWidget.soup
            while (nStructureToDelete) {
                let iStructureToDelete =
                    nStructureBefore + nStructureToDelete - 1
                let structureId = soup.structureIds[iStructureToDelete]
                this.jolecule.controller.deleteStructure(iStructureToDelete)
                console.log(
                    `deleteIFromIFrameTrajList ${iStructureToDelete}:${structureId}`
                )
                nStructureToDelete -= 1
            }
            this.jolecule.soupWidget.buildScene()
            this.$store.commit('deleteItemFromIFrameTrajList', i)
            this.nStructureInFrameList.splice(i, 1)
        },

        downloadPdb () {
            let text = getPdbText(this.jolecule, `Foamid:${this.foamId}`)

            let filename = `foamid-${this.foamId}`
            let iFrameTraj = _.last(this.iFrameTrajList)
            if (iFrameTraj) {
                let iFrame = iFrameTraj[0]
                filename += `-frame-${iFrame}`
            }
            filename += '.pdb'

            saveTextFile(text, filename)
        },

        async loadView (view) {
            console.log(`loadView`, _.cloneDeep(view))
            this.pushLoading('Views...')
            // First load all the frames

            if (_.has(view, 'matrixWidgetValues')) {
                await this.matrixWidget.loadValues(view.matrixWidgetValues)
            }

            if (_.has(view, 'stripWidgetValues')) {
                await this.stripWidget.loadValues(view.stripWidgetValues)
            }

            if (this.ensembleId) {
                if (_.has(view, 'ensembleTableValues')) {
                    await this.remote.clear_ensemble_cache(this.ensembleId)
                    for (let iFrameTraj of _.cloneDeep(this.iFrameTrajList)) {
                        await this.deleteFrame(iFrameTraj)
                    }
                    let values = view.ensembleTableValues
                    for (let i = 0; i < values.length; i += 1) {
                        let iFrameTraj = values[i]
                        await this.loadFrameIntoJolecule(iFrameTraj, i === 0)
                    }
                    this.table.iFrameTrajList = _.cloneDeep(this.iFrameTrajList)
                }
            }

            // Then set the view
            let newView = this.jolecule.soupView.getCurrentView()
            newView.setFromDict(view.viewDict)
            this.controller.setTargetView(newView)

            // update store and URL
            this.$store.commit('setItem', { viewId: view.id })
            history.pushState(
                {},
                null,
                '#' + this.$route.path + '?view=' + view.id
            )

            this.popLoading()
        },

        async saveView () {
            let viewDict = this.jolecule.soupView.getCurrentView().getDict()
            let view = {
                id: viewDict.view_id.replace('view:', ''),
                timestamp: Math.floor(Date.now() / 1000),
                viewDict: viewDict,
                text: '',
                imgs: '',
            }
            if (this.ensembleId) {
                view.ensembleId = this.ensembleId
            } else if (this.foamId) {
                view.foamId = this.foamId
            }
            if (this.matrixWidget) {
                view.matrixWidgetValues = _.cloneDeep(this.matrixWidget.values)
            }
            if (this.stripWidget) {
                view.stripWidgetValues = _.cloneDeep(this.stripWidget.values)
            }
            if (this.ensembleId && this.table) {
                view.ensembleTableValues = _.cloneDeep(
                    this.table.iFrameTrajList
                )
            }
            this.$store.commit('setItem', { newView: view })
        },

        clearGridDisplay () {
            this.jolecule.soupView.currentView.grid.isElem = {}
            let grid = this.jolecule.soupView.soup.grid
            grid.isElem = {}
            grid.isChanged = true
            this.jolecule.soupView.isUpdateColors = true
            this.jolecule.soupWidget.buildScene()
        },

        async toggleAsCommunities () {
            this.isAsCommunities = !this.isAsCommunities
            this.clearGridDisplay()
            if (this.isAsCommunities) {
                this.isAsPockets = false
            }
            this.reloadLastFrameOfJolecule()
            this.$forceUpdate()
        },

        async toggleAsPockets () {
            this.isAsPockets = !this.isAsPockets
            this.clearGridDisplay()
            if (this.isAsPockets) {
                this.isAsCommunities = false
            }
            this.reloadLastFrameOfJolecule()
            this.$forceUpdate()
        },

        async selectOptKey (key) {
            let iFrameTraj = _.last(this.iFrameTrajList)
            console.log('selectOptKey', key, iFrameTraj)
            this.key = key
            await this.remote.select_new_key(this.foamId, key)
            this.resetWidgets()
            iFrameTraj = await this.loadMatrix(iFrameTraj)
            this.clickFrame(iFrameTraj)
        },

        async close () {
            await this.remote.kill()
        },

        onkeydown (event) {
            if (
                this.$store.state.keyboardLock ||
                window.keyboardLock ||
                event.metaKey ||
                event.ctrlKey
            ) {
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
            } else if (c === 'H') {
                this.controller.toggleShowOption('hydrogen')
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
            } else if (event.keyCode === 27) {
                this.controller.clear()
            } else if (c === 'Z' || event.keyCode === 13) {
                this.controller.zoomToSelection()
            } else if (event.key === 'Escape') {
                this.controller.clear()
            }
        },

        getGridWidget () {
            if (this.matrixWidget) {
                return this.matrixWidget
            } else if (this.stripWidget) {
                return this.stripWidget
            }
            return null
        },

        async clickFrame (iFrameTraj, thisFrameOnly = true) {
            console.log(`clickFrame ${iFrameTraj}`)
            let gridWidget = this.getGridWidget()
            if (!gridWidget) {
                await this.loadFrameIntoJolecule(iFrameTraj)
            } else {
                let value = gridWidget.getGridValue(iFrameTraj)
                if (value) {
                    await gridWidget.clickGridValue(value, thisFrameOnly)
                }
            }
        },
    },
}
</script>
