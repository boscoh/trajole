import _ from 'lodash'
import config from '../../../config/config.json'

const defaultRemoteUrl = `${location.protocol}//${location.host}/rpc-run`
const remoteUrl = config.apiUrl
console.log(`config.apiUrl = ${config.apiUrl}`)
console.log(`defaultRemoteUrl = ${defaultRemoteUrl}`)
console.log(`rpc-run remoteUrl = ${remoteUrl}`)

/**
 * RPC interface to talk to a function on a server.
 *
 * Say, to run myFunction on the server remotely, the calling code
 * is:
 *
 *   let response = await remote.myFunction(a, b)
 *
 * This will pass method=functionOnServer, params=[a, b] to the
 * rpc function, which will package the method & params and send them
 * to the server, then wait for the results
 *
 * The results from the server are then returned asyncronously to
 * the caller using the JSON-RPC format
 *
 * @returns {Promise} - which wraps:
 *   1. on success:
 *      {
 *        success: {
 *          result: {any} - result returned from myFunction on server
 *        }
 *      }
 *   2. on any error:
 *      {
 *        error: {
 *          code: {number},
 *          message: {string}
 *        }
 *      }
 */
async function rpc (method, ...params) {
  const id = Math.random()
    .toString(36)
    .slice(-6)
  let wrap_params = _.map(params, _.cloneDeep)
  console.log(`rpc-run ${method}(`, wrap_params, ')')
  console.groupCollapsed()
  let response
  try {
    const payload = { method, params, jsonrpc: '2.0', id }
    if ('electron' in window) {
      response = await window.electron.rpc(payload)
    } else {
      const fetchResponse = await fetch(remoteUrl, {
        method: 'post',
        mode: 'cors',
        cache: 'no-cache',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      response = await fetchResponse.json()
      if (_.has(response, 'result')) {
        console.log(`rpc-run ${method} result:`, _.cloneDeep(response.result))
      } else {
        console.log(
          `rpc-run ${method} server-error:`,
          _.cloneDeep(response.error)
        )
      }
    }
  } catch (e) {
    console.log(`rpc-run ${method} fail: ${e}`)
    response = { error: { message: `${e}`, code: -32000 }, jsonrpc: '2.0', id }
  }
  console.groupEnd()
  return response
}

class RemoteRpcProxy {
  constructor () {
    return new Proxy(this, {
      get (target, prop) {
        return async function () {
          return await rpc(prop, ...arguments)
        }
      }
    })
  }
}

class RemoteResultRpcProxy {
  constructor () {
    return new Proxy(this, {
      get (target, prop) {
        return async function () {
          let response = await rpc(prop, ...arguments)
          return response.result
        }
      }
    })
  }
}

const remote = new RemoteRpcProxy()
const remoteResult = new RemoteRpcProxy()

export { remote, remoteResult }
