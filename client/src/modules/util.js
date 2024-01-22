import _ from 'lodash'

export function isSameVec (v1, v2) {
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

export function inFrames (iFrameTrajs, iFrameTraj) {
  return _.some(iFrameTrajs, i => isSameVec(i, iFrameTraj))
}

export function getIndexOfFrames (iFrameTrajs, iFrameTraj) {
  return _.findIndex(iFrameTrajs, i => isSameVec(i, iFrameTraj))
}

export function delFromFrames (iFrameTrajs, iFrameTraj) {
  let i = _.findIndex(iFrameTrajs, i => isSameVec(i, iFrameTraj))
  iFrameTrajs.splice(i, 1)
}

export function getFirstValue (matrix) {
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

export function saveBlobFile (blob, filename) {
  if (window.navigator.msSaveOrOpenBlob) {
    window.navigator.msSaveOrOpenBlob(blob, filename)
  } else {
    const a = document.createElement('a')
    document.body.appendChild(a)
    const url = window.URL.createObjectURL(blob)
    a.href = url
    a.download = filename
    a.click()
    setTimeout(() => {
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    }, 0)
  }
}

export function saveTextFile (text, filename) {
  let element = document.createElement('a')
  element.setAttribute(
    'href',
    'data:text/csv;charset=utf-8,' + encodeURIComponent(text)
  )
  element.setAttribute('download', filename)

  element.style.display = 'none'
  document.body.appendChild(element)

  element.click()
  document.body.removeChild(element)
}

export function getPdbText (jolecule, title) {
  let lines = []
  let soup = jolecule.soup
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
        lines.push('MODEL    ' + (iStructure + 1).toString())
      }
      lines.push(`REMARK   6    ${title} - ${residue.structureId}`)
    }

    let line = 'ATOM  '
    line += (atom.iAtom + 1).toString().padStart(5)
    line += ' '
    line += atom.atomType.padStart(4)
    line += ' '
    line += residue.resType.padEnd(4)
    line += residue.chain
    line += residue.resNum.toString().padStart(4)
    line += '    '
    line += atom.pos.x.toFixed(3).padStart(8)
    line += atom.pos.y.toFixed(3).padStart(8)
    line += atom.pos.z.toFixed(3).padStart(8)
    line += atom.bfactor.toFixed(2).padStart(6)
    line += '1.00'.padStart(6)
    line += '          '
    line += atom.elem.padStart(2)
    lines.push(line)
  }

  if (isMultiple) {
    lines.push('ENDMDL')
  }

  let text = lines.join('\n')
  return text
}

export function delay (ms) {
  return new Promise(resolve => setTimeout(resolve, ms))
}

export function makeId () {
  let result = ''
  const uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
  for (let i = 0; i < 3; i += 1) {
    result += _.sample(uppercase)
  }
  const numbers = '123456789'
  for (let i = 0; i < 2; i += 1) {
    result += _.sample(numbers)
  }
  return result
}

export function isSameValue (testV, value) {
  return isSameVec(value.iFrameTraj, testV.iFrameTraj)
}

export function inValues (testV, values) {
  return _.some(values, v => isSameVec(v.iFrameTraj, testV.iFrameTraj))
}
