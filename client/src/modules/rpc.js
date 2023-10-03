import _ from "lodash";
import config from "../../../config/config.json";

console.log(`config=${JSON.stringify(config)}`);

const remoteUrl = config.apiUrl;
console.log(`rpc.remoteUrl=${remoteUrl}`);

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
async function aysnc_rpc(method, ...params) {
  let startTime = new Date();

  const id = Math.random().toString(36).slice(-6);

  let s = `rpc.${method}.start(`;
  let n = params.length;
  for (let i = 0; i < n; i += 1) {
    s += JSON.stringify(_.cloneDeep(params[i]));
    if (i < n - 1) {
      s += ", ";
    }
  }
  s += ")";
  console.log(s);

  let response;
  try {
    const payload = { method, params, jsonrpc: "2.0", id };
    if ("electron" in window) {
      response = await window.electron.rpc(payload);
    } else {
      const fetchResponse = await fetch(remoteUrl, {
        method: "post",
        mode: "cors",
        cache: "no-cache",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      response = await fetchResponse.json();

      let elapsed = new Date() - startTime;
      if (_.has(response, "result")) {
        console.log(`rpc.${method}.result[${elapsed}ms]: ↓`);
        console.groupCollapsed();
        console.log(_.cloneDeep(response.result));
        console.groupEnd();
      } else {
        console.log(
          `rpc.${method}.error[${elapsed}ms]:`,
          _.cloneDeep(response.error)
        );
        for (let line of response.error.message) {
          console.log(`!! ${line}`);
        }
      }
    }
  } catch (e) {
    let elapsed = new Date() - startTime;
    console.log(`rpc.${method}.fail[${elapsed}ms]: ${e}`);
    response = { error: { message: `${e}`, code: -32000 }, jsonrpc: "2.0", id };
  }
  return response;
}

class RemoteRpcProxy {
  constructor() {
    return new Proxy(this, {
      get(target, prop) {
        return async function () {
          return await aysnc_rpc(prop, ...arguments);
        };
      },
    });
  }
}

class RemoteResultRpcProxy {
  constructor() {
    return new Proxy(this, {
      get(target, prop) {
        return async function () {
          let response = await aysnc_rpc(prop, ...arguments);
          if (_.has(response, "result")) {
            return response.result;
          } else {
            return null;
          }
        };
      },
    });
  }
}

const remote = new RemoteRpcProxy();
const remoteResult = new RemoteResultRpcProxy();

export { remote, remoteResult, remoteUrl, aysnc_rpc };
