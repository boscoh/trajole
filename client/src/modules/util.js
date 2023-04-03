import _ from "lodash";

export function isSameVec(v1, v2) {
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

export function inFrames(iFrameTrajs, iFrameTraj) {
    return _.some(iFrameTrajs, i => isSameVec(i, iFrameTraj))
}

export function getIndexOfFrames(iFrameTrajs, iFrameTraj) {
    return _.findIndex(iFrameTrajs, i => isSameVec(i, iFrameTraj))
}

export function delFromFrames(iFrameTrajs, iFrameTraj) {
    let i = _.findIndex(iFrameTrajs, i => isSameVec(i, iFrameTraj))
    iFrameTrajs.splice(i, 1)
}

export function getFirstValue(matrix) {
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

export function saveFile(blob, filename) {
    if (window.navigator.msSaveOrOpenBlob) {
        window.navigator.msSaveOrOpenBlob(blob, filename);
    } else {
        const a = document.createElement('a');
        document.body.appendChild(a);
        const url = window.URL.createObjectURL(blob);
        a.href = url;
        a.download = filename;
        a.click();
        setTimeout(() => {
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        }, 0)
    }
}