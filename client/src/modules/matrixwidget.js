import _ from "lodash";
import {widgets} from "jolecule";
import {getColor} from "./viridis";
import {delFromFrames, getIndexOfFrames, inFrames, isSameVec} from "./util";

export class MatrixWidget extends widgets.CanvasWidget {
    constructor(selector, grid, isSparse) {
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

    loadGrid(grid) {
        this.grid = grid
        this.nGridX = this.grid.length
        this.nGridY = this.grid[0].length
        console.log(`FesWidget.loadGrid ${this.nGridX} x ${this.nGridY}`)
        this.draw()
    }

    resize() {
        super.resize()
        this.div.height(this.height())
        this.parentDiv.height(this.height())
        this.draw()
    }

    getValue(i, j) {
        if (i < 0 || j < 0) {
            return {}
        }
        if (i >= this.grid.length || j >= this.grid[0].length) {
            return {}
        }
        return this.grid[i][this.nGridY - j - 1]
    }

    getIFrameTrajFromValue(value) {
        if (_.has(value, 'iFrameTrajs')) {
            if (value.iFrameTrajs.length) {
                return value.iFrameTrajs[0]
            }
        } else if (_.has(value, 'iFrameTraj')) {
            return value.iFrameTraj
        }
        return null
    }

    getIFrameTraj(i, j) {
        let value = this.getValue(i, j)
        return this.getIFrameTrajFromValue(value)
    }

    async loadValues(values) {
        await this.clickGridValue(values[0], false)
        for (let i = 1; i < values.length; i += 1) {
            await this.clickGridValue(values[i], true)
        }
    }

    getXFromI(i) {
        return i * this.diffX
    }

    getIFromX(x) {
        return i * this.diffX
    }

    draw() {
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

    getMouseValue(event) {
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
    async selectGridValue(value, thisFrameOnly) {
    }

    // to be overriden
    async deselectGridValue(value) {
    }

    async clickGridValue(value, isShift) {
        if (!value.iFrameTraj) {
            return
        }
        if (isShift) {
            if (inFrames(this.iFrameTrajs, value.iFrameTraj)) {
                if (this.values.length === 1) {
                    return
                }
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

    async handleSelect(event) {
        let value = this.getMouseValue(event)
        let isShift = event.shiftKey
        this.clickGridValue(value, isShift)
    }

    mouseleave(event) {
        this.hover.hide()
    }

    mousemove(event) {
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

    mouseup(event) {
        this.mousePressed = false
    }

    mousedown(event) {
        this.mousePressed = true
        this.handleSelect(event)
    }
}