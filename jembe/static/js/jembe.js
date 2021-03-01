// modules are defined as an array
// [ module function, map of requires ]
//
// map of requires is short require name -> numeric require
//
// anything defined in a previous bundle is accessed via the
// orig method which is the require for previous bundles
parcelRequire = (function (modules, cache, entry, globalName) {
  // Save the require from previous bundle to this closure if any
  var previousRequire = typeof parcelRequire === 'function' && parcelRequire;
  var nodeRequire = typeof require === 'function' && require;

  function newRequire(name, jumped) {
    if (!cache[name]) {
      if (!modules[name]) {
        // if we cannot find the module within our internal map or
        // cache jump to the current global require ie. the last bundle
        // that was added to the page.
        var currentRequire = typeof parcelRequire === 'function' && parcelRequire;
        if (!jumped && currentRequire) {
          return currentRequire(name, true);
        }

        // If there are other bundles on this page the require from the
        // previous one is saved to 'previousRequire'. Repeat this as
        // many times as there are bundles until the module is found or
        // we exhaust the require chain.
        if (previousRequire) {
          return previousRequire(name, true);
        }

        // Try the node require function if it exists.
        if (nodeRequire && typeof name === 'string') {
          return nodeRequire(name);
        }

        var err = new Error('Cannot find module \'' + name + '\'');
        err.code = 'MODULE_NOT_FOUND';
        throw err;
      }

      localRequire.resolve = resolve;
      localRequire.cache = {};

      var module = cache[name] = new newRequire.Module(name);

      modules[name][0].call(module.exports, localRequire, module, module.exports, this);
    }

    return cache[name].exports;

    function localRequire(x){
      return newRequire(localRequire.resolve(x));
    }

    function resolve(x){
      return modules[name][1][x] || x;
    }
  }

  function Module(moduleName) {
    this.id = moduleName;
    this.bundle = newRequire;
    this.exports = {};
  }

  newRequire.isParcelRequire = true;
  newRequire.Module = Module;
  newRequire.modules = modules;
  newRequire.cache = cache;
  newRequire.parent = previousRequire;
  newRequire.register = function (id, exports) {
    modules[id] = [function (require, module) {
      module.exports = exports;
    }, {}];
  };

  var error;
  for (var i = 0; i < entry.length; i++) {
    try {
      newRequire(entry[i]);
    } catch (e) {
      // Save first error but execute all entries
      if (!error) {
        error = e;
      }
    }
  }

  if (entry.length) {
    // Expose entry point to Node, AMD or browser globals
    // Based on https://github.com/ForbesLindesay/umd/blob/master/template.js
    var mainExports = newRequire(entry[entry.length - 1]);

    // CommonJS
    if (typeof exports === "object" && typeof module !== "undefined") {
      module.exports = mainExports;

    // RequireJS
    } else if (typeof define === "function" && define.amd) {
     define(function () {
       return mainExports;
     });

    // <script>
    } else if (globalName) {
      this[globalName] = mainExports;
    }
  }

  // Override the current require with this new one
  parcelRequire = newRequire;

  if (error) {
    // throw error from earlier, _after updating parcelRequire_
    throw error;
  }

  return newRequire;
})({"utils.js":[function(require,module,exports) {
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.walkComponentDom = walkComponentDom;
exports.deepCopy = deepCopy;
exports.AsyncFunction = void 0;

/**
 * Return null or the execName of the component 
 * @param {Element} el 
 */
function elIsNewComponent(el) {
  if (el.hasAttribute('jmb:name')) {
    return el.getAttribute('jmb:name');
  } else if (el.hasAttribute('jmb-placeholder')) {
    return el.getAttribute('jmb-placeholder');
  } else {
    return null;
  }
}

function walkComponentDom(el, callback, callbackOnNewComponent, myExecName) {
  if (myExecName === undefined) {
    myExecName = el.getAttribute('jmb:name');
  }

  let componentExecName = elIsNewComponent(el);

  if (componentExecName !== null && componentExecName !== myExecName) {
    callbackOnNewComponent(el, componentExecName);
  } else {
    callback(el);
    el = el.firstElementChild;

    while (el) {
      walkComponentDom(el, callback, callbackOnNewComponent, myExecName);
      el = el.nextElementSibling;
    }
  }
}

let AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
exports.AsyncFunction = AsyncFunction;

function deepCopy(inObject) {
  let outObject, value, key;

  if (typeof inObject !== "object" || inObject === null) {
    return inObject; // Return the value if inObject is not an object
  } // Create an array or object to hold the values


  outObject = Array.isArray(inObject) ? [] : {};

  for (key in inObject) {
    value = inObject[key]; // Recursively (deep) copy for nested objects, including arrays

    outObject[key] = deepCopy(value);
  }

  return outObject;
}
},{}],"../../../node_modules/process/browser.js":[function(require,module,exports) {

// shim for using process in browser
var process = module.exports = {}; // cached from whatever global is present so that test runners that stub it
// don't break things.  But we need to wrap it in a try catch in case it is
// wrapped in strict mode code which doesn't define any globals.  It's inside a
// function because try/catches deoptimize in certain engines.

var cachedSetTimeout;
var cachedClearTimeout;

function defaultSetTimout() {
  throw new Error('setTimeout has not been defined');
}

function defaultClearTimeout() {
  throw new Error('clearTimeout has not been defined');
}

(function () {
  try {
    if (typeof setTimeout === 'function') {
      cachedSetTimeout = setTimeout;
    } else {
      cachedSetTimeout = defaultSetTimout;
    }
  } catch (e) {
    cachedSetTimeout = defaultSetTimout;
  }

  try {
    if (typeof clearTimeout === 'function') {
      cachedClearTimeout = clearTimeout;
    } else {
      cachedClearTimeout = defaultClearTimeout;
    }
  } catch (e) {
    cachedClearTimeout = defaultClearTimeout;
  }
})();

function runTimeout(fun) {
  if (cachedSetTimeout === setTimeout) {
    //normal enviroments in sane situations
    return setTimeout(fun, 0);
  } // if setTimeout wasn't available but was latter defined


  if ((cachedSetTimeout === defaultSetTimout || !cachedSetTimeout) && setTimeout) {
    cachedSetTimeout = setTimeout;
    return setTimeout(fun, 0);
  }

  try {
    // when when somebody has screwed with setTimeout but no I.E. maddness
    return cachedSetTimeout(fun, 0);
  } catch (e) {
    try {
      // When we are in I.E. but the script has been evaled so I.E. doesn't trust the global object when called normally
      return cachedSetTimeout.call(null, fun, 0);
    } catch (e) {
      // same as above but when it's a version of I.E. that must have the global object for 'this', hopfully our context correct otherwise it will throw a global error
      return cachedSetTimeout.call(this, fun, 0);
    }
  }
}

function runClearTimeout(marker) {
  if (cachedClearTimeout === clearTimeout) {
    //normal enviroments in sane situations
    return clearTimeout(marker);
  } // if clearTimeout wasn't available but was latter defined


  if ((cachedClearTimeout === defaultClearTimeout || !cachedClearTimeout) && clearTimeout) {
    cachedClearTimeout = clearTimeout;
    return clearTimeout(marker);
  }

  try {
    // when when somebody has screwed with setTimeout but no I.E. maddness
    return cachedClearTimeout(marker);
  } catch (e) {
    try {
      // When we are in I.E. but the script has been evaled so I.E. doesn't  trust the global object when called normally
      return cachedClearTimeout.call(null, marker);
    } catch (e) {
      // same as above but when it's a version of I.E. that must have the global object for 'this', hopfully our context correct otherwise it will throw a global error.
      // Some versions of I.E. have different rules for clearTimeout vs setTimeout
      return cachedClearTimeout.call(this, marker);
    }
  }
}

var queue = [];
var draining = false;
var currentQueue;
var queueIndex = -1;

function cleanUpNextTick() {
  if (!draining || !currentQueue) {
    return;
  }

  draining = false;

  if (currentQueue.length) {
    queue = currentQueue.concat(queue);
  } else {
    queueIndex = -1;
  }

  if (queue.length) {
    drainQueue();
  }
}

function drainQueue() {
  if (draining) {
    return;
  }

  var timeout = runTimeout(cleanUpNextTick);
  draining = true;
  var len = queue.length;

  while (len) {
    currentQueue = queue;
    queue = [];

    while (++queueIndex < len) {
      if (currentQueue) {
        currentQueue[queueIndex].run();
      }
    }

    queueIndex = -1;
    len = queue.length;
  }

  currentQueue = null;
  draining = false;
  runClearTimeout(timeout);
}

process.nextTick = function (fun) {
  var args = new Array(arguments.length - 1);

  if (arguments.length > 1) {
    for (var i = 1; i < arguments.length; i++) {
      args[i - 1] = arguments[i];
    }
  }

  queue.push(new Item(fun, args));

  if (queue.length === 1 && !draining) {
    runTimeout(drainQueue);
  }
}; // v8 likes predictible objects


function Item(fun, array) {
  this.fun = fun;
  this.array = array;
}

Item.prototype.run = function () {
  this.fun.apply(null, this.array);
};

process.title = 'browser';
process.env = {};
process.argv = [];
process.version = ''; // empty string to avoid regexp issues

process.versions = {};

function noop() {}

process.on = noop;
process.addListener = noop;
process.once = noop;
process.off = noop;
process.removeListener = noop;
process.removeAllListeners = noop;
process.emit = noop;
process.prependListener = noop;
process.prependOnceListener = noop;

process.listeners = function (name) {
  return [];
};

process.binding = function (name) {
  throw new Error('process.binding is not supported');
};

process.cwd = function () {
  return '/';
};

process.chdir = function (dir) {
  throw new Error('process.chdir is not supported');
};

process.umask = function () {
  return 0;
};
},{}],"../../../node_modules/node-libs-browser/node_modules/path-browserify/index.js":[function(require,module,exports) {
var process = require("process");
// .dirname, .basename, and .extname methods are extracted from Node.js v8.11.1,
// backported and transplited with Babel, with backwards-compat fixes

// Copyright Joyent, Inc. and other Node contributors.
//
// Permission is hereby granted, free of charge, to any person obtaining a
// copy of this software and associated documentation files (the
// "Software"), to deal in the Software without restriction, including
// without limitation the rights to use, copy, modify, merge, publish,
// distribute, sublicense, and/or sell copies of the Software, and to permit
// persons to whom the Software is furnished to do so, subject to the
// following conditions:
//
// The above copyright notice and this permission notice shall be included
// in all copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
// OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
// MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN
// NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
// DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
// OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
// USE OR OTHER DEALINGS IN THE SOFTWARE.

// resolves . and .. elements in a path array with directory names there
// must be no slashes, empty elements, or device names (c:\) in the array
// (so also no leading and trailing slashes - it does not distinguish
// relative and absolute paths)
function normalizeArray(parts, allowAboveRoot) {
  // if the path tries to go above the root, `up` ends up > 0
  var up = 0;
  for (var i = parts.length - 1; i >= 0; i--) {
    var last = parts[i];
    if (last === '.') {
      parts.splice(i, 1);
    } else if (last === '..') {
      parts.splice(i, 1);
      up++;
    } else if (up) {
      parts.splice(i, 1);
      up--;
    }
  }

  // if the path is allowed to go above the root, restore leading ..s
  if (allowAboveRoot) {
    for (; up--; up) {
      parts.unshift('..');
    }
  }

  return parts;
}

// path.resolve([from ...], to)
// posix version
exports.resolve = function() {
  var resolvedPath = '',
      resolvedAbsolute = false;

  for (var i = arguments.length - 1; i >= -1 && !resolvedAbsolute; i--) {
    var path = (i >= 0) ? arguments[i] : process.cwd();

    // Skip empty and invalid entries
    if (typeof path !== 'string') {
      throw new TypeError('Arguments to path.resolve must be strings');
    } else if (!path) {
      continue;
    }

    resolvedPath = path + '/' + resolvedPath;
    resolvedAbsolute = path.charAt(0) === '/';
  }

  // At this point the path should be resolved to a full absolute path, but
  // handle relative paths to be safe (might happen when process.cwd() fails)

  // Normalize the path
  resolvedPath = normalizeArray(filter(resolvedPath.split('/'), function(p) {
    return !!p;
  }), !resolvedAbsolute).join('/');

  return ((resolvedAbsolute ? '/' : '') + resolvedPath) || '.';
};

// path.normalize(path)
// posix version
exports.normalize = function(path) {
  var isAbsolute = exports.isAbsolute(path),
      trailingSlash = substr(path, -1) === '/';

  // Normalize the path
  path = normalizeArray(filter(path.split('/'), function(p) {
    return !!p;
  }), !isAbsolute).join('/');

  if (!path && !isAbsolute) {
    path = '.';
  }
  if (path && trailingSlash) {
    path += '/';
  }

  return (isAbsolute ? '/' : '') + path;
};

// posix version
exports.isAbsolute = function(path) {
  return path.charAt(0) === '/';
};

// posix version
exports.join = function() {
  var paths = Array.prototype.slice.call(arguments, 0);
  return exports.normalize(filter(paths, function(p, index) {
    if (typeof p !== 'string') {
      throw new TypeError('Arguments to path.join must be strings');
    }
    return p;
  }).join('/'));
};


// path.relative(from, to)
// posix version
exports.relative = function(from, to) {
  from = exports.resolve(from).substr(1);
  to = exports.resolve(to).substr(1);

  function trim(arr) {
    var start = 0;
    for (; start < arr.length; start++) {
      if (arr[start] !== '') break;
    }

    var end = arr.length - 1;
    for (; end >= 0; end--) {
      if (arr[end] !== '') break;
    }

    if (start > end) return [];
    return arr.slice(start, end - start + 1);
  }

  var fromParts = trim(from.split('/'));
  var toParts = trim(to.split('/'));

  var length = Math.min(fromParts.length, toParts.length);
  var samePartsLength = length;
  for (var i = 0; i < length; i++) {
    if (fromParts[i] !== toParts[i]) {
      samePartsLength = i;
      break;
    }
  }

  var outputParts = [];
  for (var i = samePartsLength; i < fromParts.length; i++) {
    outputParts.push('..');
  }

  outputParts = outputParts.concat(toParts.slice(samePartsLength));

  return outputParts.join('/');
};

exports.sep = '/';
exports.delimiter = ':';

exports.dirname = function (path) {
  if (typeof path !== 'string') path = path + '';
  if (path.length === 0) return '.';
  var code = path.charCodeAt(0);
  var hasRoot = code === 47 /*/*/;
  var end = -1;
  var matchedSlash = true;
  for (var i = path.length - 1; i >= 1; --i) {
    code = path.charCodeAt(i);
    if (code === 47 /*/*/) {
        if (!matchedSlash) {
          end = i;
          break;
        }
      } else {
      // We saw the first non-path separator
      matchedSlash = false;
    }
  }

  if (end === -1) return hasRoot ? '/' : '.';
  if (hasRoot && end === 1) {
    // return '//';
    // Backwards-compat fix:
    return '/';
  }
  return path.slice(0, end);
};

function basename(path) {
  if (typeof path !== 'string') path = path + '';

  var start = 0;
  var end = -1;
  var matchedSlash = true;
  var i;

  for (i = path.length - 1; i >= 0; --i) {
    if (path.charCodeAt(i) === 47 /*/*/) {
        // If we reached a path separator that was not part of a set of path
        // separators at the end of the string, stop now
        if (!matchedSlash) {
          start = i + 1;
          break;
        }
      } else if (end === -1) {
      // We saw the first non-path separator, mark this as the end of our
      // path component
      matchedSlash = false;
      end = i + 1;
    }
  }

  if (end === -1) return '';
  return path.slice(start, end);
}

// Uses a mixed approach for backwards-compatibility, as ext behavior changed
// in new Node.js versions, so only basename() above is backported here
exports.basename = function (path, ext) {
  var f = basename(path);
  if (ext && f.substr(-1 * ext.length) === ext) {
    f = f.substr(0, f.length - ext.length);
  }
  return f;
};

exports.extname = function (path) {
  if (typeof path !== 'string') path = path + '';
  var startDot = -1;
  var startPart = 0;
  var end = -1;
  var matchedSlash = true;
  // Track the state of characters (if any) we see before our first dot and
  // after any path separator we find
  var preDotState = 0;
  for (var i = path.length - 1; i >= 0; --i) {
    var code = path.charCodeAt(i);
    if (code === 47 /*/*/) {
        // If we reached a path separator that was not part of a set of path
        // separators at the end of the string, stop now
        if (!matchedSlash) {
          startPart = i + 1;
          break;
        }
        continue;
      }
    if (end === -1) {
      // We saw the first non-path separator, mark this as the end of our
      // extension
      matchedSlash = false;
      end = i + 1;
    }
    if (code === 46 /*.*/) {
        // If this is our first dot, mark it as the start of our extension
        if (startDot === -1)
          startDot = i;
        else if (preDotState !== 1)
          preDotState = 1;
    } else if (startDot !== -1) {
      // We saw a non-dot and non-path separator before our dot, so we should
      // have a good chance at having a non-empty extension
      preDotState = -1;
    }
  }

  if (startDot === -1 || end === -1 ||
      // We saw a non-dot character immediately before the dot
      preDotState === 0 ||
      // The (right-most) trimmed path component is exactly '..'
      preDotState === 1 && startDot === end - 1 && startDot === startPart + 1) {
    return '';
  }
  return path.slice(startDot, end);
};

function filter (xs, f) {
    if (xs.filter) return xs.filter(f);
    var res = [];
    for (var i = 0; i < xs.length; i++) {
        if (f(xs[i], i, xs)) res.push(xs[i]);
    }
    return res;
}

// String.prototype.substr - negative index don't work in IE8
var substr = 'ab'.substr(-1) === 'b'
    ? function (str, start, len) { return str.substr(start, len) }
    : function (str, start, len) {
        if (start < 0) start = str.length + start;
        return str.substr(start, len);
    }
;

},{"process":"../../../node_modules/process/browser.js"}],"../../../node_modules/setimmediate/setImmediate.js":[function(require,module,exports) {
var global = arguments[3];
var process = require("process");
(function (global, undefined) {
    "use strict";

    if (global.setImmediate) {
        return;
    }

    var nextHandle = 1; // Spec says greater than zero
    var tasksByHandle = {};
    var currentlyRunningATask = false;
    var doc = global.document;
    var registerImmediate;

    function setImmediate(callback) {
      // Callback can either be a function or a string
      if (typeof callback !== "function") {
        callback = new Function("" + callback);
      }
      // Copy function arguments
      var args = new Array(arguments.length - 1);
      for (var i = 0; i < args.length; i++) {
          args[i] = arguments[i + 1];
      }
      // Store and register the task
      var task = { callback: callback, args: args };
      tasksByHandle[nextHandle] = task;
      registerImmediate(nextHandle);
      return nextHandle++;
    }

    function clearImmediate(handle) {
        delete tasksByHandle[handle];
    }

    function run(task) {
        var callback = task.callback;
        var args = task.args;
        switch (args.length) {
        case 0:
            callback();
            break;
        case 1:
            callback(args[0]);
            break;
        case 2:
            callback(args[0], args[1]);
            break;
        case 3:
            callback(args[0], args[1], args[2]);
            break;
        default:
            callback.apply(undefined, args);
            break;
        }
    }

    function runIfPresent(handle) {
        // From the spec: "Wait until any invocations of this algorithm started before this one have completed."
        // So if we're currently running a task, we'll need to delay this invocation.
        if (currentlyRunningATask) {
            // Delay by doing a setTimeout. setImmediate was tried instead, but in Firefox 7 it generated a
            // "too much recursion" error.
            setTimeout(runIfPresent, 0, handle);
        } else {
            var task = tasksByHandle[handle];
            if (task) {
                currentlyRunningATask = true;
                try {
                    run(task);
                } finally {
                    clearImmediate(handle);
                    currentlyRunningATask = false;
                }
            }
        }
    }

    function installNextTickImplementation() {
        registerImmediate = function(handle) {
            process.nextTick(function () { runIfPresent(handle); });
        };
    }

    function canUsePostMessage() {
        // The test against `importScripts` prevents this implementation from being installed inside a web worker,
        // where `global.postMessage` means something completely different and can't be used for this purpose.
        if (global.postMessage && !global.importScripts) {
            var postMessageIsAsynchronous = true;
            var oldOnMessage = global.onmessage;
            global.onmessage = function() {
                postMessageIsAsynchronous = false;
            };
            global.postMessage("", "*");
            global.onmessage = oldOnMessage;
            return postMessageIsAsynchronous;
        }
    }

    function installPostMessageImplementation() {
        // Installs an event handler on `global` for the `message` event: see
        // * https://developer.mozilla.org/en/DOM/window.postMessage
        // * http://www.whatwg.org/specs/web-apps/current-work/multipage/comms.html#crossDocumentMessages

        var messagePrefix = "setImmediate$" + Math.random() + "$";
        var onGlobalMessage = function(event) {
            if (event.source === global &&
                typeof event.data === "string" &&
                event.data.indexOf(messagePrefix) === 0) {
                runIfPresent(+event.data.slice(messagePrefix.length));
            }
        };

        if (global.addEventListener) {
            global.addEventListener("message", onGlobalMessage, false);
        } else {
            global.attachEvent("onmessage", onGlobalMessage);
        }

        registerImmediate = function(handle) {
            global.postMessage(messagePrefix + handle, "*");
        };
    }

    function installMessageChannelImplementation() {
        var channel = new MessageChannel();
        channel.port1.onmessage = function(event) {
            var handle = event.data;
            runIfPresent(handle);
        };

        registerImmediate = function(handle) {
            channel.port2.postMessage(handle);
        };
    }

    function installReadyStateChangeImplementation() {
        var html = doc.documentElement;
        registerImmediate = function(handle) {
            // Create a <script> element; its readystatechange event will be fired asynchronously once it is inserted
            // into the document. Do so, thus queuing up the task. Remember to clean up once it's been called.
            var script = doc.createElement("script");
            script.onreadystatechange = function () {
                runIfPresent(handle);
                script.onreadystatechange = null;
                html.removeChild(script);
                script = null;
            };
            html.appendChild(script);
        };
    }

    function installSetTimeoutImplementation() {
        registerImmediate = function(handle) {
            setTimeout(runIfPresent, 0, handle);
        };
    }

    // If supported, we should attach to the prototype of global, since that is where setTimeout et al. live.
    var attachTo = Object.getPrototypeOf && Object.getPrototypeOf(global);
    attachTo = attachTo && attachTo.setTimeout ? attachTo : global;

    // Don't get fooled by e.g. browserify environments.
    if ({}.toString.call(global.process) === "[object process]") {
        // For Node.js before 0.9
        installNextTickImplementation();

    } else if (canUsePostMessage()) {
        // For non-IE10 modern browsers
        installPostMessageImplementation();

    } else if (global.MessageChannel) {
        // For web workers, where supported
        installMessageChannelImplementation();

    } else if (doc && "onreadystatechange" in doc.createElement("script")) {
        // For IE 6–8
        installReadyStateChangeImplementation();

    } else {
        // For older browsers
        installSetTimeoutImplementation();
    }

    attachTo.setImmediate = setImmediate;
    attachTo.clearImmediate = clearImmediate;
}(typeof self === "undefined" ? typeof global === "undefined" ? this : global : self));

},{"process":"../../../node_modules/process/browser.js"}],"../../../node_modules/timers-browserify/main.js":[function(require,module,exports) {
var global = arguments[3];
var scope = typeof global !== "undefined" && global || typeof self !== "undefined" && self || window;
var apply = Function.prototype.apply; // DOM APIs, for completeness

exports.setTimeout = function () {
  return new Timeout(apply.call(setTimeout, scope, arguments), clearTimeout);
};

exports.setInterval = function () {
  return new Timeout(apply.call(setInterval, scope, arguments), clearInterval);
};

exports.clearTimeout = exports.clearInterval = function (timeout) {
  if (timeout) {
    timeout.close();
  }
};

function Timeout(id, clearFn) {
  this._id = id;
  this._clearFn = clearFn;
}

Timeout.prototype.unref = Timeout.prototype.ref = function () {};

Timeout.prototype.close = function () {
  this._clearFn.call(scope, this._id);
}; // Does not start the time, just sets up the members needed.


exports.enroll = function (item, msecs) {
  clearTimeout(item._idleTimeoutId);
  item._idleTimeout = msecs;
};

exports.unenroll = function (item) {
  clearTimeout(item._idleTimeoutId);
  item._idleTimeout = -1;
};

exports._unrefActive = exports.active = function (item) {
  clearTimeout(item._idleTimeoutId);
  var msecs = item._idleTimeout;

  if (msecs >= 0) {
    item._idleTimeoutId = setTimeout(function onTimeout() {
      if (item._onTimeout) item._onTimeout();
    }, msecs);
  }
}; // setimmediate attaches itself to the global object


require("setimmediate"); // On some exotic environments, it's not clear which object `setimmediate` was
// able to install onto.  Search each possibility in the same order as the
// `setimmediate` library.


exports.setImmediate = typeof self !== "undefined" && self.setImmediate || typeof global !== "undefined" && global.setImmediate || this && this.setImmediate;
exports.clearImmediate = typeof self !== "undefined" && self.clearImmediate || typeof global !== "undefined" && global.clearImmediate || this && this.clearImmediate;
},{"setimmediate":"../../../node_modules/setimmediate/setImmediate.js"}],"componentApi.js":[function(require,module,exports) {
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.JembeComponentAPI = void 0;

var _client = require("./client");

var _utils = require("./utils");

var _path = require("path");

var _timers = require("timers");

/**
 * jembeClient.component(this).set('paramName', paramValue)
 * jembeClient.component(this).call('actionName', {kwargs})
 * jembeClient.component(this).display()
 * jembeClient.component(this).emit('eventName', {kwargs})
 * jembeClient.component(this).init('componentRelativeOrFullName', {kwargs})
 * jembeClient.executeCommands()
 * 
 * Short form that needs to be support for jmb:on.<eventName>[.defer]:
 * $jmb.set('paramName', paramValue)
 * $jmb.call('actionName', {kwargs}) or actionName({kwargs})
 * $jmb.display() // call('display',{})
 * $jmb.emit('eventName',{kwargs})
 * $jmb.[init|component]('componentRelativeOrFullName', {kwargs})[.call|.display|.emit]
 * 
 * $jmb.ref('referencedDomName') // jmb:ref="referencedDomName"
 * 
 * RETHINKIG
 * From alpine: $el, $refs, $event, $dispatch, $nextTick, $watch
 * From jmb: $jmb with $jmb.emit, $jmb.init|component, $jmb.call
 *           $self - referenc on curent node
 *           $local - reference local javascript variables tied to component.localData
 * all actions and state params are localy avaiable so
 * paramName = paramValue or paramName = $self.value or file = $self.files[0] are valid
 * also actionName({kwargs}) or display() are valid
 * param names overrides actionNames and prints warning in console if thay colides
 * All changes to state valiables should call display if defer modifier is not present
 * If no chages are made to state variables (only to $local etc) display will not be called
 * 
 * what to use j-on.click j-data and j-ignore 
 */
class JembeComponentAPI {
  constructor(componentRef, jembeClient = undefined, execName = undefined) {
    if (componentRef !== undefined && componentRef !== null) {
      /** @type {JembeClient} */
      this.jembeClient = componentRef.jembeClient;
      /** @type {ComponentRef} */

      this.componentRef = componentRef;
      this.execName = componentRef.execName;
      this.localData = componentRef.localData;
    } else {
      /** @type {JembeClient} */
      this.jembeClient = jembeClient;
      /** @type {ComponentRef} */

      this.componentRef = undefined;
      this.execName = execName;
      this.localData = {};
    }

    this.refs = {}; // internal

    this.onReadyEvents = [];
    this.unnamedTimers = [];
    this.previouseNamedTimers = {};

    if (this.localData.namedTimers !== undefined) {
      this.previouseNamedTimers = this.localData.namedTimers;
    }

    this.localData.namedTimers = {}; // initialistion

    this.initialiseJmbOnListeners();
  }

  call(actionName, ...params) {
    let kwargs = {};
    let args = [];

    if (params.length === 1 && params[0].constructor == Object) {
      kwargs = params[0];
    } else {
      args = params;
    }

    this.jembeClient.addCallCommand(this.execName, actionName, args, kwargs);
  }

  display() {
    this.call("display");
  }
  /**
   *  Change state param of current component,
   *  by addig initialise command with only state param 
   *  defined by stateName changed to newlly provided value
   * stateName can use dots (.) to set attribure of object
   * Examples: "someObject.paramName" 
   * @param {string} stateName 
   * @param {*} value 
   */


  set(stateName, value) {
    if (value instanceof FileList || value instanceof File) {
      this.jembeClient.addFilesForUpload(this.execName, stateName, value);
    } else {
      let params = {};
      params[stateName] = value;
      this.jembeClient.addInitialiseCommand(this.execName, params);
    }
  }

  emit(eventName, kwargs = {}, to = null) {
    this.jembeClient.addEmitCommand(this.execName, eventName, kwargs, to);
  }

  component(relativeExecName, kwargs = {}) {
    let execName = relativeExecName;

    if (!(0, _path.isAbsolute)(relativeExecName)) {
      execName = (0, _path.join)(this.execName, relativeExecName);
    }

    let componentNames = [];
    let startWith = [];
    let index = 0;
    let equalSoFar = true;
    let execNameSplit = execName.split("/");
    let thisExecNameSplit = this.execName.split("/");

    while (index < execNameSplit.length) {
      if (equalSoFar === true && ( // if execName is different (including key) we need to genereate init command
      execNameSplit[index] !== thisExecNameSplit[index] || // alsy if kwargs are specified for last component we need do generate init command
      index === execNameSplit.length - 1 && kwargs !== {})) {
        equalSoFar = false;
      }

      if (!equalSoFar) {
        componentNames.push(execNameSplit[index]);
      } else {
        startWith.push(execNameSplit[index]);
      }

      index++;
    }

    index = 0;

    while (index < componentNames.length) {
      this.jembeClient.addInitialiseCommand([startWith.join("/"), componentNames.slice(0, index + 1).join("/")].join("/"), index == componentNames.length - 1 ? kwargs : {});
      index++;
    }

    return new JembeComponentAPI(undefined, this.jembeClient, execName);
  }

  init(relativeExecName, kwargs = {}) {
    return this.component(relativeExecName, kwargs);
  }

  ref(referenceName) {
    return this.refs[referenceName];
  }

  initialiseJmbOnListeners() {
    if (this.componentRef !== undefined) {
      // TODO walk dom and select elements
      this.onReadyEvents = [];

      for (const jmbddattr of this.componentRef.jmbDoubleDotAttributes) {
        this._processDomAttribute(jmbddattr.el, jmbddattr.name, jmbddattr.value);
      }

      for (const eventFunction of this.onReadyEvents) {
        eventFunction();
      }
    }
  }

  _processDomAttribute(el, attrName, attrValue) {
    attrName = attrName.toLowerCase();

    if (attrName.startsWith('jmb:on.')) {
      this._processJmbOnAttribute(el, attrName, attrValue);
    } else if (attrName === "jmb:ref") {
      this._processJmbRefAttribute(el, attrName, attrValue);
    }
  }

  _processJmbOnAttribute(el, attrName, attrValue) {
    let [jmbTag, onEventAndDecorators, actionName] = attrName.split(":");
    let [onTag, eventName, ...decorators] = onEventAndDecorators.split(".");
    let expression = `${attrValue}`; // support defer decorator

    if (decorators.indexOf("defer") < 0) {
      if (expression.includes("$jmb.set(")) {
        // if action is not deferred and has $jmb.set then call display
        expression += ";$jmb.display();";
      }

      expression += ';window.jembeClient.executeCommands();';
    } //support delay decorator
    // must be last decorator


    const delayIndexOf = decorators.indexOf("delay");

    if (delayIndexOf >= 0) {
      let timer = 1000;

      if (delayIndexOf + 1 < decorators.length && decorators[delayIndexOf + 1].endsWith('ms')) {
        timer = parseInt(decorators[delayIndexOf + 1].substr(0, decorators[delayIndexOf + 1].length - 2)) * 10;
      }

      if (actionName === undefined) {
        expression = `
        var timerId = window.setTimeout(function() {${expression}}, ${timer});
        $jmb.unnamedTimers.push(timerId);
        `;
      } else {
        let start = new Date().getTime();

        if (this.previouseNamedTimers[actionName] !== undefined) {
          start = this.previouseNamedTimers[actionName].start;
          timer = timer - (new Date().getTime() - start);
        }

        if (timer > 0) {
          expression = `
          var timerId = window.setTimeout(function() {
            ${expression};
            delete $jmb.localData.namedTimers['${actionName}'];
          }, ${timer});
          $jmb.localData.namedTimers['${actionName}'] = {id: timerId, start: ${start}};
          `;
        } else {
          //run emidiatly like on.ready
          this.onReadyEvents.push(() => this._executeJmbOnLogic(el, null, expression));
        }
      }
    }

    if (eventName === 'ready') {
      // support on.ready event, that is executed when component is rendered
      // that means execute it right now
      this.onReadyEvents.push(() => this._executeJmbOnLogic(el, null, expression));
    } else {
      // support for browser events
      el.addEventListener(eventName, event => {
        this._executeJmbOnLogic(el, event, expression);
      });
    }
  }

  _processJmbRefAttribute(el, attrName, attrValue) {
    this.refs[attrValue] = el;
  }

  _executeJmbOnLogic(el, event, expression) {
    /** @type {Array<string>} */
    const actions = this.componentRef.actions;
    let helpers = {
      "$jmb": this,
      "$event": event,
      "$el": el
    }; // allow action functions to be called directly 

    for (const action of actions) {
      helpers[action] = (...params) => {
        this.call(action, ...params);
      };
    }

    let scope = {};
    return Promise.resolve(new _utils.AsyncFunction(['scope', ...Object.keys(helpers)], `with(scope) { ${expression} }`)(scope, ...Object.values(helpers)));
  }

  mount() {}

  unmount() {
    for (const timerId of this.unnamedTimers) {
      window.clearTimeout(timerId);
    }

    for (const [timerName, timerInfo] of Object.entries(this.localData.namedTimers)) {
      window.clearTimeout(timerInfo.id);
    }
  }

}

exports.JembeComponentAPI = JembeComponentAPI;
},{"./client":"client.js","./utils":"utils.js","path":"../../../node_modules/node-libs-browser/node_modules/path-browserify/index.js","timers":"../../../node_modules/timers-browserify/main.js"}],"morphdom/morphAttrs.js":[function(require,module,exports) {
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = morphAttrs;
var DOCUMENT_FRAGMENT_NODE = 11;

function morphAttrs(fromNode, toNode) {
  var toNodeAttrs = toNode.attributes;
  var attr;
  var attrName;
  var attrNamespaceURI;
  var attrValue;
  var fromValue; // document-fragments dont have attributes so lets not do anything

  if (toNode.nodeType === DOCUMENT_FRAGMENT_NODE || fromNode.nodeType === DOCUMENT_FRAGMENT_NODE) {
    return;
  } // update attributes on original DOM element


  for (var i = toNodeAttrs.length - 1; i >= 0; i--) {
    attr = toNodeAttrs[i];
    attrName = attr.name;
    attrNamespaceURI = attr.namespaceURI;
    attrValue = attr.value;

    if (attrNamespaceURI) {
      attrName = attr.localName || attrName;
      fromValue = fromNode.getAttributeNS(attrNamespaceURI, attrName);

      if (fromValue !== attrValue) {
        if (attr.prefix === 'xmlns') {
          attrName = attr.name; // It's not allowed to set an attribute with the XMLNS namespace without specifying the `xmlns` prefix
        }

        fromNode.setAttributeNS(attrNamespaceURI, attrName, attrValue);
      }
    } else {
      fromValue = fromNode.getAttribute(attrName);

      if (fromValue !== attrValue) {
        fromNode.setAttribute(attrName, attrValue);
      }
    }
  } // Remove any extra attributes found on the original DOM element that
  // weren't found on the target element.


  var fromNodeAttrs = fromNode.attributes;

  for (var d = fromNodeAttrs.length - 1; d >= 0; d--) {
    attr = fromNodeAttrs[d];
    attrName = attr.name;
    attrNamespaceURI = attr.namespaceURI;

    if (attrNamespaceURI) {
      attrName = attr.localName || attrName;

      if (!toNode.hasAttributeNS(attrNamespaceURI, attrName)) {
        fromNode.removeAttributeNS(attrNamespaceURI, attrName);
      }
    } else {
      if (!toNode.hasAttribute(attrName)) {
        fromNode.removeAttribute(attrName);
      }
    }
  }
}
},{}],"morphdom/util.js":[function(require,module,exports) {
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.toElement = toElement;
exports.compareNodeNames = compareNodeNames;
exports.createElementNS = createElementNS;
exports.moveChildren = moveChildren;
exports.doc = void 0;
var range; // Create a range object for efficently rendering strings to elements.

var NS_XHTML = 'http://www.w3.org/1999/xhtml';
var doc = typeof document === 'undefined' ? undefined : document;
exports.doc = doc;
var HAS_TEMPLATE_SUPPORT = !!doc && 'content' in doc.createElement('template');
var HAS_RANGE_SUPPORT = !!doc && doc.createRange && 'createContextualFragment' in doc.createRange();

function createFragmentFromTemplate(str) {
  var template = doc.createElement('template');
  template.innerHTML = str;
  return template.content.childNodes[0];
}

function createFragmentFromRange(str) {
  if (!range) {
    range = doc.createRange();
    range.selectNode(doc.body);
  }

  var fragment = range.createContextualFragment(str);
  return fragment.childNodes[0];
}

function createFragmentFromWrap(str) {
  var fragment = doc.createElement('body');
  fragment.innerHTML = str;
  return fragment.childNodes[0];
}
/**
 * This is about the same
 * var html = new DOMParser().parseFromString(str, 'text/html');
 * return html.body.firstChild;
 *
 * @method toElement
 * @param {String} str
 */


function toElement(str) {
  str = str.trim();

  if (HAS_TEMPLATE_SUPPORT) {
    // avoid restrictions on content for things like `<tr><th>Hi</th></tr>` which
    // createContextualFragment doesn't support
    // <template> support not available in IE
    return createFragmentFromTemplate(str);
  } else if (HAS_RANGE_SUPPORT) {
    return createFragmentFromRange(str);
  }

  return createFragmentFromWrap(str);
}
/**
 * Returns true if two node's names are the same.
 *
 * NOTE: We don't bother checking `namespaceURI` because you will never find two HTML elements with the same
 *       nodeName and different namespace URIs.
 *
 * @param {Element} a
 * @param {Element} b The target element
 * @return {boolean}
 */


function compareNodeNames(fromEl, toEl) {
  var fromNodeName = fromEl.nodeName;
  var toNodeName = toEl.nodeName;
  var fromCodeStart, toCodeStart;

  if (fromNodeName === toNodeName) {
    return true;
  }

  fromCodeStart = fromNodeName.charCodeAt(0);
  toCodeStart = toNodeName.charCodeAt(0); // If the target element is a virtual DOM node or SVG node then we may
  // need to normalize the tag name before comparing. Normal HTML elements that are
  // in the "http://www.w3.org/1999/xhtml"
  // are converted to upper case

  if (fromCodeStart <= 90 && toCodeStart >= 97) {
    // from is upper and to is lower
    return fromNodeName === toNodeName.toUpperCase();
  } else if (toCodeStart <= 90 && fromCodeStart >= 97) {
    // to is upper and from is lower
    return toNodeName === fromNodeName.toUpperCase();
  } else {
    return false;
  }
}
/**
 * Create an element, optionally with a known namespace URI.
 *
 * @param {string} name the element name, e.g. 'div' or 'svg'
 * @param {string} [namespaceURI] the element's namespace URI, i.e. the value of
 * its `xmlns` attribute or its inferred namespace.
 *
 * @return {Element}
 */


function createElementNS(name, namespaceURI) {
  return !namespaceURI || namespaceURI === NS_XHTML ? doc.createElement(name) : doc.createElementNS(namespaceURI, name);
}
/**
 * Copies the children of one DOM element to another DOM element
 */


function moveChildren(fromEl, toEl) {
  var curChild = fromEl.firstChild;

  while (curChild) {
    var nextChild = curChild.nextSibling;
    toEl.appendChild(curChild);
    curChild = nextChild;
  }

  return toEl;
}
},{}],"morphdom/specialElHandlers.js":[function(require,module,exports) {
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;

function syncBooleanAttrProp(fromEl, toEl, name) {
  if (fromEl[name] !== toEl[name]) {
    fromEl[name] = toEl[name];

    if (fromEl[name]) {
      fromEl.setAttribute(name, '');
    } else {
      fromEl.removeAttribute(name);
    }
  }
}

var _default = {
  OPTION: function (fromEl, toEl) {
    var parentNode = fromEl.parentNode;

    if (parentNode) {
      var parentName = parentNode.nodeName.toUpperCase();

      if (parentName === 'OPTGROUP') {
        parentNode = parentNode.parentNode;
        parentName = parentNode && parentNode.nodeName.toUpperCase();
      }

      if (parentName === 'SELECT' && !parentNode.hasAttribute('multiple')) {
        if (fromEl.hasAttribute('selected') && !toEl.selected) {
          // Workaround for MS Edge bug where the 'selected' attribute can only be
          // removed if set to a non-empty value:
          // https://developer.microsoft.com/en-us/microsoft-edge/platform/issues/12087679/
          fromEl.setAttribute('selected', 'selected');
          fromEl.removeAttribute('selected');
        } // We have to reset select element's selectedIndex to -1, otherwise setting
        // fromEl.selected using the syncBooleanAttrProp below has no effect.
        // The correct selectedIndex will be set in the SELECT special handler below.


        parentNode.selectedIndex = -1;
      }
    }

    syncBooleanAttrProp(fromEl, toEl, 'selected');
  },

  /**
   * The "value" attribute is special for the <input> element since it sets
   * the initial value. Changing the "value" attribute without changing the
   * "value" property will have no effect since it is only used to the set the
   * initial value.  Similar for the "checked" attribute, and "disabled".
   */
  INPUT: function (fromEl, toEl) {
    syncBooleanAttrProp(fromEl, toEl, 'checked');
    syncBooleanAttrProp(fromEl, toEl, 'disabled');

    if (fromEl.value !== toEl.value) {
      fromEl.value = toEl.value;
    }

    if (!toEl.hasAttribute('value')) {
      fromEl.removeAttribute('value');
    }
  },
  TEXTAREA: function (fromEl, toEl) {
    var newValue = toEl.value;

    if (fromEl.value !== newValue) {
      fromEl.value = newValue;
    }

    var firstChild = fromEl.firstChild;

    if (firstChild) {
      // Needed for IE. Apparently IE sets the placeholder as the
      // node value and vise versa. This ignores an empty update.
      var oldValue = firstChild.nodeValue;

      if (oldValue == newValue || !newValue && oldValue == fromEl.placeholder) {
        return;
      }

      firstChild.nodeValue = newValue;
    }
  },
  SELECT: function (fromEl, toEl) {
    if (!toEl.hasAttribute('multiple')) {
      var selectedIndex = -1;
      var i = 0; // We have to loop through children of fromEl, not toEl since nodes can be moved
      // from toEl to fromEl directly when morphing.
      // At the time this special handler is invoked, all children have already been morphed
      // and appended to / removed from fromEl, so using fromEl here is safe and correct.

      var curChild = fromEl.firstChild;
      var optgroup;
      var nodeName;

      while (curChild) {
        nodeName = curChild.nodeName && curChild.nodeName.toUpperCase();

        if (nodeName === 'OPTGROUP') {
          optgroup = curChild;
          curChild = optgroup.firstChild;
        } else {
          if (nodeName === 'OPTION') {
            if (curChild.hasAttribute('selected')) {
              selectedIndex = i;
              break;
            }

            i++;
          }

          curChild = curChild.nextSibling;

          if (!curChild && optgroup) {
            curChild = optgroup.nextSibling;
            optgroup = null;
          }
        }
      }

      fromEl.selectedIndex = selectedIndex;
    }
  }
};
exports.default = _default;
},{}],"morphdom/morphdom.js":[function(require,module,exports) {
'use strict';
/**
 * Changes taged with @jembeModification
 * 
 */

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = morphdomFactory;

var _util = require("./util");

var _specialElHandlers = _interopRequireDefault(require("./specialElHandlers"));

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

var ELEMENT_NODE = 1;
var DOCUMENT_FRAGMENT_NODE = 11;
var TEXT_NODE = 3;
var COMMENT_NODE = 8;

function noop() {}

function defaultGetNodeKey(node) {
  if (node) {
    return node.getAttribute && node.getAttribute('id') || node.id;
  }
}

function morphdomFactory(morphAttrs) {
  return function morphdom(fromNode, toNode, options) {
    if (!options) {
      options = {};
    }

    if (typeof toNode === 'string') {
      if (fromNode.nodeName === '#document' || fromNode.nodeName === 'HTML' || fromNode.nodeName === 'BODY') {
        var toNodeHtml = toNode;
        toNode = _util.doc.createElement('html');
        toNode.innerHTML = toNodeHtml;
      } else {
        toNode = (0, _util.toElement)(toNode);
      }
    } else if (toNode.nodeType === DOCUMENT_FRAGMENT_NODE) {
      toNode = toNode.firstElementChild;
    }

    var getNodeKey = options.getNodeKey || defaultGetNodeKey;
    var onBeforeNodeAdded = options.onBeforeNodeAdded || noop;
    var onNodeAdded = options.onNodeAdded || noop;
    var onBeforeElUpdated = options.onBeforeElUpdated || noop;
    var onElUpdated = options.onElUpdated || noop;
    var onBeforeNodeDiscarded = options.onBeforeNodeDiscarded || noop;
    var onNodeDiscarded = options.onNodeDiscarded || noop;
    var onBeforeElChildrenUpdated = options.onBeforeElChildrenUpdated || noop;
    var childrenOnly = options.childrenOnly === true; // This object is used as a lookup to quickly find all keyed elements in the original DOM tree.

    var fromNodesLookup = Object.create(null);
    var keyedRemovalList = [];

    function addKeyedRemoval(key) {
      keyedRemovalList.push(key);
    }

    function walkDiscardedChildNodes(node, skipKeyedNodes) {
      if (node.nodeType === ELEMENT_NODE) {
        var curChild = node.firstChild;

        while (curChild) {
          var key = undefined;

          if (skipKeyedNodes && (key = getNodeKey(curChild))) {
            // If we are skipping keyed nodes then we add the key
            // to a list so that it can be handled at the very end.
            addKeyedRemoval(key);
          } else {
            // Only report the node as discarded if it is not keyed. We do this because
            // at the end we loop through all keyed elements that were unmatched
            // and then discard them in one final pass.
            onNodeDiscarded(curChild);

            if (curChild.firstChild) {
              walkDiscardedChildNodes(curChild, skipKeyedNodes);
            }
          }

          curChild = curChild.nextSibling;
        }
      }
    }
    /**
     * Removes a DOM node out of the original DOM
     *
     * @param  {Node} node The node to remove
     * @param  {Node} parentNode The nodes parent
     * @param  {Boolean} skipKeyedNodes If true then elements with keys will be skipped and not discarded.
     * @return {undefined}
     */


    function removeNode(node, parentNode, skipKeyedNodes) {
      if (onBeforeNodeDiscarded(node) === false) {
        return;
      }

      if (parentNode) {
        parentNode.removeChild(node);
      }

      onNodeDiscarded(node);
      walkDiscardedChildNodes(node, skipKeyedNodes);
    } // // TreeWalker implementation is no faster, but keeping this around in case this changes in the future
    // function indexTree(root) {
    //     var treeWalker = document.createTreeWalker(
    //         root,
    //         NodeFilter.SHOW_ELEMENT);
    //
    //     var el;
    //     while((el = treeWalker.nextNode())) {
    //         var key = getNodeKey(el);
    //         if (key) {
    //             fromNodesLookup[key] = el;
    //         }
    //     }
    // }
    // // NodeIterator implementation is no faster, but keeping this around in case this changes in the future
    //
    // function indexTree(node) {
    //     var nodeIterator = document.createNodeIterator(node, NodeFilter.SHOW_ELEMENT);
    //     var el;
    //     while((el = nodeIterator.nextNode())) {
    //         var key = getNodeKey(el);
    //         if (key) {
    //             fromNodesLookup[key] = el;
    //         }
    //     }
    // }


    function indexTree(node) {
      if (node.nodeType === ELEMENT_NODE || node.nodeType === DOCUMENT_FRAGMENT_NODE) {
        var curChild = node.firstChild;

        while (curChild) {
          var key = getNodeKey(curChild);

          if (key) {
            fromNodesLookup[key] = curChild;
          } // Walk recursively


          indexTree(curChild);
          curChild = curChild.nextSibling;
        }
      }
    }

    indexTree(fromNode);

    function handleNodeAdded(el) {
      onNodeAdded(el);
      var curChild = el.firstChild;

      while (curChild) {
        var nextSibling = curChild.nextSibling;
        var key = getNodeKey(curChild);

        if (key) {
          var unmatchedFromEl = fromNodesLookup[key]; // if we find a duplicate #id node in cache, replace `el` with cache value
          // and morph it to the child node.

          if (unmatchedFromEl && (0, _util.compareNodeNames)(curChild, unmatchedFromEl)) {
            curChild.parentNode.replaceChild(unmatchedFromEl, curChild);
            morphEl(unmatchedFromEl, curChild);
          } else {
            handleNodeAdded(curChild);
          }
        } else {
          // recursively call for curChild and it's children to see if we find something in
          // fromNodesLookup
          handleNodeAdded(curChild);
        }

        curChild = nextSibling;
      }
    }

    function cleanupFromEl(fromEl, curFromNodeChild, curFromNodeKey) {
      // We have processed all of the "to nodes". If curFromNodeChild is
      // non-null then we still have some from nodes left over that need
      // to be removed
      while (curFromNodeChild) {
        var fromNextSibling = curFromNodeChild.nextSibling;

        if (curFromNodeKey = getNodeKey(curFromNodeChild)) {
          // Since the node is keyed it might be matched up later so we defer
          // the actual removal to later
          addKeyedRemoval(curFromNodeKey);
        } else {
          // NOTE: we skip nested keyed nodes from being removed since there is
          //       still a chance they will be matched up later
          removeNode(curFromNodeChild, fromEl, true
          /* skip keyed nodes */
          );
        }

        curFromNodeChild = fromNextSibling;
      }
    }

    function morphEl(fromEl, toEl, childrenOnly) {
      var toElKey = getNodeKey(toEl);

      if (toElKey) {
        // If an element with an ID is being morphed then it will be in the final
        // DOM so clear it out of the saved elements collection
        delete fromNodesLookup[toElKey];
      }

      if (!childrenOnly) {
        // optional
        if (onBeforeElUpdated(fromEl, toEl) === false) {
          return;
        } // update attributes on original DOM element first


        morphAttrs(fromEl, toEl); // optional

        onElUpdated(fromEl);

        if (onBeforeElChildrenUpdated(fromEl, toEl) === false) {
          return;
        }
      }

      if (fromEl.nodeName !== 'TEXTAREA') {
        morphChildren(fromEl, toEl);
      } else {
        _specialElHandlers.default.TEXTAREA(fromEl, toEl);
      }
    }

    function morphChildren(fromEl, toEl) {
      var curToNodeChild = toEl.firstChild;
      var curFromNodeChild = fromEl.firstChild;
      var curToNodeKey;
      var curFromNodeKey;
      var fromNextSibling;
      var toNextSibling;
      var matchingFromEl; // walk the children

      outer: while (curToNodeChild) {
        toNextSibling = curToNodeChild.nextSibling;
        curToNodeKey = getNodeKey(curToNodeChild); // walk the fromNode children all the way through

        while (curFromNodeChild) {
          fromNextSibling = curFromNodeChild.nextSibling;

          if (curToNodeChild.isSameNode && curToNodeChild.isSameNode(curFromNodeChild)) {
            curToNodeChild = toNextSibling;
            curFromNodeChild = fromNextSibling;
            continue outer;
          }

          curFromNodeKey = getNodeKey(curFromNodeChild);
          var curFromNodeType = curFromNodeChild.nodeType; // this means if the curFromNodeChild doesnt have a match with the curToNodeChild

          var isCompatible = undefined;

          if (curFromNodeType === curToNodeChild.nodeType) {
            if (curFromNodeType === ELEMENT_NODE) {
              // Both nodes being compared are Element nodes
              if (curToNodeKey) {
                // The target node has a key so we want to match it up with the correct element
                // in the original DOM tree
                if (curToNodeKey !== curFromNodeKey) {
                  // The current element in the original DOM tree does not have a matching key so
                  // let's check our lookup to see if there is a matching element in the original
                  // DOM tree
                  if (matchingFromEl = fromNodesLookup[curToNodeKey]) {
                    if (fromNextSibling === matchingFromEl) {
                      // Special case for single element removals. To avoid removing the original
                      // DOM node out of the tree (since that can break CSS transitions, etc.),
                      // we will instead discard the current node and wait until the next
                      // iteration to properly match up the keyed target element with its matching
                      // element in the original tree
                      isCompatible = false;
                    } else {
                      // We found a matching keyed element somewhere in the original DOM tree.
                      // Let's move the original DOM node into the current position and morph
                      // it.
                      // NOTE: We use insertBefore instead of replaceChild because we want to go through
                      // the `removeNode()` function for the node that is being discarded so that
                      // all lifecycle hooks are correctly invoked
                      fromEl.insertBefore(matchingFromEl, curFromNodeChild); // fromNextSibling = curFromNodeChild.nextSibling;

                      if (curFromNodeKey) {
                        // Since the node is keyed it might be matched up later so we defer
                        // the actual removal to later
                        addKeyedRemoval(curFromNodeKey);
                      } else {
                        // NOTE: we skip nested keyed nodes from being removed since there is
                        //       still a chance they will be matched up later
                        removeNode(curFromNodeChild, fromEl, true
                        /* skip keyed nodes */
                        );
                      }

                      curFromNodeChild = matchingFromEl;
                    }
                  } else {
                    // The nodes are not compatible since the "to" node has a key and there
                    // is no matching keyed node in the source tree
                    isCompatible = false;
                  }
                }
              } else if (curFromNodeKey) {
                // The original has a key
                isCompatible = false;
              }

              isCompatible = isCompatible !== false && (0, _util.compareNodeNames)(curFromNodeChild, curToNodeChild);

              if (isCompatible) {
                // @jembeModification
                // If the two nodes are different, but the next element is an exact match,
                // we can assume that the new node is meant to be inserted, instead of
                // used as a morph target.
                // original at: https://github.com/livewire/livewire/blob/master/js/dom/morphdom/morphdom.js
                if (!curToNodeChild.isEqualNode(curFromNodeChild) && curToNodeChild.nextElementSibling && curToNodeChild.nextElementSibling.isEqualNode(curFromNodeChild)) {
                  isCompatible = false;
                } else {
                  // We found compatible DOM elements so transform
                  // the current "from" node to match the current
                  // target DOM node.
                  // MORPH
                  morphEl(curFromNodeChild, curToNodeChild);
                }
              }
            } else if (curFromNodeType === TEXT_NODE || curFromNodeType == COMMENT_NODE) {
              // Both nodes being compared are Text or Comment nodes
              isCompatible = true; // Simply update nodeValue on the original node to
              // change the text value

              if (curFromNodeChild.nodeValue !== curToNodeChild.nodeValue) {
                curFromNodeChild.nodeValue = curToNodeChild.nodeValue;
              }
            }
          }

          if (isCompatible) {
            // Advance both the "to" child and the "from" child since we found a match
            // Nothing else to do as we already recursively called morphChildren above
            curToNodeChild = toNextSibling;
            curFromNodeChild = fromNextSibling;
            continue outer;
          } // @jembeModification
          // Before we just remove the original element, let's see if it's the very next
          // element in the "to" list. If it is, we can assume we can insert the new
          // element before the original one instead of removing it. This is kind of
          // a "look-ahead".
          // original at: https://github.com/livewire/livewire/blob/master/js/dom/morphdom/morphdom.js


          if (curToNodeChild.nextElementSibling && curToNodeChild.nextElementSibling.isEqualNode(curFromNodeChild)) {
            const nodeToBeAdded = curToNodeChild.cloneNode(true);
            fromEl.insertBefore(nodeToBeAdded, curFromNodeChild);
            handleNodeAdded(nodeToBeAdded);
            curToNodeChild = curToNodeChild.nextElementSibling.nextSibling;
            curFromNodeChild = fromNextSibling;
            continue outer;
          } else {
            // No compatible match so remove the old node from the DOM and continue trying to find a
            // match in the original DOM. However, we only do this if the from node is not keyed
            // since it is possible that a keyed node might match up with a node somewhere else in the
            // target tree and we don't want to discard it just yet since it still might find a
            // home in the final DOM tree. After everything is done we will remove any keyed nodes
            // that didn't find a home
            if (curFromNodeKey) {
              // Since the node is keyed it might be matched up later so we defer
              // the actual removal to later
              addKeyedRemoval(curFromNodeKey);
            } else {
              // NOTE: we skip nested keyed nodes from being removed since there is
              //       still a chance they will be matched up later
              removeNode(curFromNodeChild, fromEl, true
              /* skip keyed nodes */
              );
            }
          }

          curFromNodeChild = fromNextSibling;
        } // END: while(curFromNodeChild) {}
        // If we got this far then we did not find a candidate match for
        // our "to node" and we exhausted all of the children "from"
        // nodes. Therefore, we will just append the current "to" node
        // to the end


        if (curToNodeKey && (matchingFromEl = fromNodesLookup[curToNodeKey]) && (0, _util.compareNodeNames)(matchingFromEl, curToNodeChild)) {
          fromEl.appendChild(matchingFromEl); // MORPH

          morphEl(matchingFromEl, curToNodeChild);
        } else {
          var onBeforeNodeAddedResult = onBeforeNodeAdded(curToNodeChild);

          if (onBeforeNodeAddedResult !== false) {
            if (onBeforeNodeAddedResult) {
              curToNodeChild = onBeforeNodeAddedResult;
            }

            if (curToNodeChild.actualize) {
              curToNodeChild = curToNodeChild.actualize(fromEl.ownerDocument || _util.doc);
            }

            fromEl.appendChild(curToNodeChild);
            handleNodeAdded(curToNodeChild);
          }
        }

        curToNodeChild = toNextSibling;
        curFromNodeChild = fromNextSibling;
      }

      cleanupFromEl(fromEl, curFromNodeChild, curFromNodeKey);
      var specialElHandler = _specialElHandlers.default[fromEl.nodeName];

      if (specialElHandler) {
        specialElHandler(fromEl, toEl);
      }
    } // END: morphChildren(...)


    var morphedNode = fromNode;
    var morphedNodeType = morphedNode.nodeType;
    var toNodeType = toNode.nodeType;

    if (!childrenOnly) {
      // Handle the case where we are given two DOM nodes that are not
      // compatible (e.g. <div> --> <span> or <div> --> TEXT)
      if (morphedNodeType === ELEMENT_NODE) {
        if (toNodeType === ELEMENT_NODE) {
          if (!(0, _util.compareNodeNames)(fromNode, toNode)) {
            onNodeDiscarded(fromNode);
            morphedNode = (0, _util.moveChildren)(fromNode, (0, _util.createElementNS)(toNode.nodeName, toNode.namespaceURI));
          }
        } else {
          // Going from an element node to a text node
          morphedNode = toNode;
        }
      } else if (morphedNodeType === TEXT_NODE || morphedNodeType === COMMENT_NODE) {
        // Text or comment node
        if (toNodeType === morphedNodeType) {
          if (morphedNode.nodeValue !== toNode.nodeValue) {
            morphedNode.nodeValue = toNode.nodeValue;
          }

          return morphedNode;
        } else {
          // Text node to something else
          morphedNode = toNode;
        }
      }
    }

    if (morphedNode === toNode) {
      // The "to node" was not compatible with the "from node" so we had to
      // toss out the "from node" and use the "to node"
      onNodeDiscarded(fromNode);
    } else {
      if (toNode.isSameNode && toNode.isSameNode(morphedNode)) {
        return;
      }

      morphEl(morphedNode, toNode, childrenOnly); // We now need to loop over any keyed nodes that might need to be
      // removed. We only do the removal if we know that the keyed node
      // never found a match. When a keyed node is matched up we remove
      // it out of fromNodesLookup and we use fromNodesLookup to determine
      // if a keyed node has been matched up or not

      if (keyedRemovalList) {
        for (var i = 0, len = keyedRemovalList.length; i < len; i++) {
          var elToRemove = fromNodesLookup[keyedRemovalList[i]];

          if (elToRemove) {
            removeNode(elToRemove, elToRemove.parentNode, false);
          }
        }
      }
    }

    if (!childrenOnly && morphedNode !== fromNode && fromNode.parentNode) {
      if (morphedNode.actualize) {
        morphedNode = morphedNode.actualize(fromNode.ownerDocument || _util.doc);
      } // If we had to swap out the from node with a new node because the old
      // node was not compatible with the target node then we need to
      // replace the old DOM node in the original DOM tree. This is only
      // possible if the original DOM node was part of a DOM tree which
      // we know is the case if it has a parent node.


      fromNode.parentNode.replaceChild(morphedNode, fromNode);
    }

    return morphedNode;
  };
}
},{"./util":"morphdom/util.js","./specialElHandlers":"morphdom/specialElHandlers.js"}],"morphdom/index.js":[function(require,module,exports) {
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;

var _morphAttrs = _interopRequireDefault(require("./morphAttrs"));

var _morphdom = _interopRequireDefault(require("./morphdom"));

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

var morphdom = (0, _morphdom.default)(_morphAttrs.default);
var _default = morphdom;
exports.default = _default;
},{"./morphAttrs":"morphdom/morphAttrs.js","./morphdom":"morphdom/morphdom.js"}],"client.js":[function(require,module,exports) {
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.JembeClient = void 0;

var _componentApi = require("./componentApi.js");

var _utils = require("./utils.js");

var _index = _interopRequireDefault(require("./morphdom/index.js"));

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

/*
  Supported tags:
    # jmb:on.<eventname>.<modifier>.<modifier>
    # jmb:model=
    <button jmb:on.click="$jmb.call('increase',10)"
*/

/**
 * Reference to component html with associated data
 */
class ComponentRef {
  constructor(jembeClient, execName, data, dom, onDocument) {
    this.jembeClient = jembeClient;
    this.execName = execName;
    this.hierarchyLevel = execName.split("/").length;
    this.isPageComponent = this.hierarchyLevel === 2;
    this.state = data.state;
    this.url = data.url;
    this.changesUrl = data.changesUrl;
    this.actions = data.actions !== undefined ? data.actions : [];
    this.dom = this._cleanDom(dom);
    this.onDocument = onDocument; // data of local js component
    // needs to be preserved when merging with new dom

    this.localData = {};
    this.mounted = false;
    this.placeHolders = {};
    this.jmbDoubleDotAttributes = [];
    this.api = null;
  }

  mount(localData = undefined) {
    if (!this.mounted) {
      if (localData !== undefined) {
        this.localData = localData;
      }

      this._getPlaceHoldersAndJmbAttributes();

      this.api = new _componentApi.JembeComponentAPI(this);
      this.api.mount();
    }

    this.mounted = true;
  }

  unmount() {
    if (this.mounted) {
      this.api.unmount();
      this.api = null;
    }

    this.mounted = false;
  }

  toJsonRequest() {
    return {
      "execName": this.execName,
      "state": this.state
    };
  }

  merge(parentComponent, originalComponent) {
    if (this.isPageComponent && this.onDocument) {
      // if page component is already on document do nothing
      // because it is already mounted and it's not changed
      return;
    }

    if (this.onDocument && originalComponent !== undefined && originalComponent.dom.isSameNode(this.dom)) {
      // no need to unmount-merge-mount component that is already on document
      if (!parentComponent.placeHolders[this.execName].isSameNode(this.dom)) {
        // but if paramet is changed we need to update parent place holders
        parentComponent.placeHolders[this.execName].replaceWith(this.dom);
        parentComponent.placeHolders[this.execName] = this.dom;
      }

      return;
    }

    if (originalComponent !== undefined) {
      originalComponent.unmount();
    }

    if (this.isPageComponent) {
      let documentElement = this.jembeClient.document.documentElement; // TODO morph dom

      this.dom = documentElement = this._morphdom(documentElement, this.dom); // documentElement.innerHTML = this.dom.innerHTML

      this.dom.setAttribute("jmb:name", this.execName);
    } else {
      // TODO morph dom
      this.dom = this._morphdom(parentComponent.placeHolders[this.execName], this.dom); // parentComponent.placeHolders[this.execName].replaceWith(this.dom)

      parentComponent.placeHolders[this.execName] = this.dom;
    }

    this.mount(originalComponent !== undefined && originalComponent.execName === this.execName ? originalComponent.localData : undefined);
    this.onDocument = true;
  }

  _morphdom(from, to) {
    return (0, _index.default)(from, to, {
      getNodeKey: node => {
        return node.nodeType === Node.ELEMENT_NODE && node.hasAttribute('jmb:name') ? node.getAttribute('jmb:name') : node.id;
      },
      onBeforeElUpdated: (fromEl, toEl) => {
        // spec - https://dom.spec.whatwg.org/#concept-node-equals
        if (fromEl.isEqualNode(toEl)) {
          return false;
        } // don't pass to next component or template


        if (!this.isPageComponent && fromEl.hasAttribute('jmb:name') && fromEl.getAttribute('jmb:name') !== this.execName) return false;
        if (fromEl.hasAttribute('jmb-placeholder') && fromEl.getAttribute('jmb-placeholder') !== this.execName) return false;

        if (fromEl.hasAttribute('jmb-ignore')) {
          return false;
        } // TODO rename jmb-placeholder to jmb:placeholder


        return true;
      },
      childrenOnly: this.isPageComponent
    });
  }

  _getPlaceHoldersAndJmbAttributes() {
    this.placeHolders = {};
    this.jmbDoubleDotAttributes = [];
    (0, _utils.walkComponentDom)(this.dom, el => {
      // populate jmbDoubleDotAttributes
      if (el.hasAttributes()) {
        for (const attribute of el.attributes) {
          if (attribute.name.startsWith("jmb:")) {
            this.jmbDoubleDotAttributes.push({
              el: el,
              name: attribute.name,
              value: attribute.value
            });
          }
        }
      }
    }, (el, execName) => {
      // populate placeHolders
      this.placeHolders[execName] = el;
    });
  }

  _cleanDom(dom) {
    // if html dom has only one child use that child to put jmb:name tag
    // if not enclose html with div and put jmb:name into it
    if (typeof dom === "string") {
      let domString = dom.trim();

      if (!this.isPageComponent) {
        let template = this.jembeClient.document.createElement("template");
        template.innerHTML = domString; // check is it needed to add souranding DIV tag

        if (template.content.childNodes.length > 1 || template.content.childNodes.length === 0 || template.content.firstChild.nodeType === Node.TEXT_NODE || template.content.childNodes.length === 1 && (template.content.firstChild.hasAttribute("jmb:name") || template.content.firstChild.hasAttribute("jmb-placeholder"))) {
          let div = this.jembeClient.document.createElement("div");
          let curChild = template.content.firstChild;

          while (curChild) {
            let nextChild = curChild.nextSibling;
            div.appendChild(curChild);
            curChild = nextChild;
          }

          template.content.appendChild(div);
        } // add jmb:name tag


        template.content.firstChild.setAttribute("jmb:name", this.execName);
        dom = template.content.firstChild;
      } else {
        const doc = this.jembeClient.domParser.parseFromString(domString, "text/html");
        doc.documentElement.setAttribute("jmb:name", this.execName);
        dom = doc.documentElement;
      }
    }

    dom.removeAttribute('jmb:data');
    return dom;
  }

}

class UploadedFile {
  constructor(execName, paramName, fileUploadId, files) {
    this.execName = execName;
    this.paramName = paramName;
    this.fileUploadId = fileUploadId;
    this.files = files;
    this.multipleFiles = files instanceof FileList || files instanceof Array;
  }

  addToFormData(formData) {
    if (this.multipleFiles) {
      for (const file of this.files) {
        formData.append(this.fileUploadId, file);
      }
    } else {
      formData.append(this.fileUploadId, this.files);
    }
  }

}
/**
 * Handle all jembe logic on client side, primarly building, sending, processing 
 * and refreshing page for/on x-jembe requests
 */


class JembeClient {
  constructor(doc = document) {
    this.document = doc;
    this.components = {};
    this.getComponentsFromDocument();
    this.updateLocation(true);
    this.commands = [];
    this.filesForUpload = {};
    this.domParser = new DOMParser();
    this.xRequestUrl = null;
    window.onpopstate = this.onHistoryPopState;
  }
  /**
   * Finds all jmb:name and associate jmb:data tags in document 
   * and create ComponentRefs
   */


  getComponentsFromDocument() {
    this.components = {};
    let componentsNodes = this.document.querySelectorAll("[jmb\\:name][jmb\\:data]");

    for (const componentNode of componentsNodes) {
      const componentRef = new ComponentRef(this, componentNode.getAttribute('jmb:name'), eval(`(${componentNode.getAttribute('jmb:data')})`), componentNode, true);
      this.components[componentRef.execName] = componentRef;
      componentRef.mount();
    }
  }
  /**
   * Create dict of {execName:component} for all components find in
   * x-jembe response
   * @param {*} xJembeResponse 
   */


  getComponentsFromXResponse(xJembeResponse) {
    let components = {};

    for (const xComp of xJembeResponse) {
      const dom = xComp.dom;
      components[xComp.execName] = new ComponentRef(this, xComp.execName, {
        "url": xComp.url,
        "changesUrl": xComp.changesUrl,
        "state": xComp.state,
        "actions": xComp.actions
      }, xComp.dom, false);
    }

    return components;
  }
  /**
   * Update document with new components:dict
   * @param {} components 
   */


  updateDocument(components) {
    // make list of all existing components that can be display on updated document
    // list contains all from this.components merged with components where
    // if there is components with same execname one from components is used
    let currentComponents = {}; // add from this.components if not exist in components otherwise add from components

    for (const [execName, compRef] of Object.entries(this.components)) {
      if (components[execName] === undefined) {
        currentComponents[execName] = compRef;
      } else {
        currentComponents[execName] = components[execName];
      }
    } // add from components if not already added


    for (const [execName, compRef] of Object.entries(components)) {
      if (currentComponents[execName] === undefined) {
        currentComponents[execName] = compRef;
      }
    } //process current components one by one starting with root page
    // all components gatthered from document but whitout its placeholder
    // will be ignored.
    // chose root/page component from compoents if it exist otherwise use
    // one on the document


    let pageExecNames = Object.values(currentComponents).filter(c => c.isPageComponent).map(c => c.execName); // execName of new pageComponent 

    let pageExecName = pageExecNames[0];

    if (pageExecNames.length > 1) {
      for (const pen of pageExecNames) {
        if (!currentComponents[pen].onDocument) {
          pageExecName = pen;
        }
      }
    }

    let processingExecNames = [pageExecName];
    let newComponents = {};

    while (processingExecNames.length > 0) {
      const currentComponent = currentComponents[processingExecNames.shift()];
      let orignalComponent = this.components[currentComponent.execName];
      let parentComponent = Object.values(newComponents).find(c => Object.keys(c.placeHolders).includes(currentComponent.execName));
      currentComponent.merge(parentComponent, orignalComponent); // if (parentComponent !== undefined) {
      //   parentComponent.placeHolders[currentComponent.execName] = currentComponent.dom
      // }

      newComponents[currentComponent.execName] = currentComponent; // currentComponent.mount()

      for (const placeHolderName of Object.keys(currentComponent.placeHolders)) {
        processingExecNames.push(placeHolderName);
      }
    }

    this.components = newComponents;
  }

  addInitialiseCommand(execName, initParams) {
    const exisitingInitCommands = this.commands.filter(x => x.type === "init" && x.componentExecName === execName);

    if (exisitingInitCommands.length > 0) {
      for (const [paramName, paramValue] of Object.entries(initParams)) {
        exisitingInitCommands[0].initParams = this._updateParam(exisitingInitCommands[0].initParams, paramName, paramValue); // exisitingInitCommands[0].initParams[paramName] = initParams[paramName]
      }
    } else {
      let params = this.components[execName] !== undefined ? (0, _utils.deepCopy)(this.components[execName].state) : {};

      for (const [paramName, paramValue] of Object.entries(initParams)) {
        params = this._updateParam(params, paramName, paramValue);
      }

      this.commands.push({
        "type": "init",
        "componentExecName": execName,
        "initParams": params
      });
    }
  }
  /**
   * Update params with [paramName] =  paramValue
   * paramName can contain dots (.) to separate object attributes
   * @param {dict} params 
   * @param {string} paramName 
   * @param {*} paramValue 
   */


  _updateParam(params, paramName, paramValue) {
    if (paramName.startsWith('.') || paramName.endsWith(".")) {
      throw "paramName cant start or end in dot (.)";
    }

    return this._updateParamR(params, paramName.split("."), paramValue);
  }

  _updateParamR(params, paramNames, paramValue) {
    let pName = paramNames[0];

    if (paramNames.length === 1) {
      // last element
      params[pName] = paramValue;
    } else if (params[pName] === undefined) {
      params[pName] = this._updateParamR({}, paramNames.slice(1), paramValue);
    } else {
      params[pName] = this._updateParamR(params[pName], paramNames.slice(1), paramValue);
    }

    return params;
  }

  addCallCommand(execName, actionName, args, kwargs) {
    this.commands.push({
      "type": "call",
      "componentExecName": execName,
      "actionName": actionName,
      "args": args,
      "kwargs": kwargs
    });
  }

  addEmitCommand(execName, eventName, kwargs = {}, to = null) {
    this.commands.push({
      "type": "emit",
      "componentExecName": execName,
      "eventName": eventName,
      "params": kwargs,
      "to": to
    });
  }

  addFilesForUpload(execName, paramName, files) {
    // remove existing files for same param name
    let existingFileId = null;

    for (const uf of Object.values(this.filesForUpload)) {
      if (uf.execName === execName && uf.paramName === paramName) {
        existingFileId = uf.fileUploadId;
      }
    }

    if (existingFileId !== null) {
      delete this.filesForUpload[existingFileId];
    }

    if ((files instanceof FileList || files instanceof Array) && files.length > 0 || files instanceof File) {
      // add files to paramName
      let fileId = null;

      while (fileId == null || Object.keys(this.filesForUpload).includes(fileId)) {
        fileId = Math.random().toString(36).substring(7);
      }

      this.filesForUpload[fileId] = new UploadedFile(execName, paramName, fileId, files); // add init command if not exist

      this.addInitialiseCommand(execName, {
        [paramName]: fileId
      });
    } else {
      // remove init command if only containt file init param
      let initCommandIndex = this.commands.findIndex(cmd => cmd.componentExecName === execName && cmd.type === "init" && Object.keys(cmd.initParams).includes(paramName) && Object.keys(cmd.initParams).length === 1);

      if (initCommandIndex >= 0) {
        this.commands.splice(initCommandIndex, 1);
      }
    }
  }

  getXUploadRequestFormData() {
    if (Object.keys(this.filesForUpload).length === 0) {
      // no files for uplaod
      return null;
    }

    let fd = new FormData();

    for (const uf of Object.values(this.filesForUpload)) {
      uf.addToFormData(fd);
    }

    return fd;
  }

  getXRequestJson() {
    return JSON.stringify({
      "components": Object.values(this.components).map(x => x.toJsonRequest()),
      "commands": this.commands
    });
  }

  setXRequestUrl(url) {
    this.xRequestUrl = url;
  }

  executeUpload() {
    const url = "/jembe/upload_files";
    const uploadFormData = this.getXUploadRequestFormData();

    if (uploadFormData === null) {
      return new Promise((resolve, reject) => {
        resolve(null);
      });
    }

    return window.fetch(url, {
      method: "POST",
      cache: "no-cache",
      credentials: "same-origin",
      redirect: "follow",
      referrer: "no-referrer",
      headers: {
        'X-JEMBE': 'upload'
      },
      body: uploadFormData
    }).then(response => {
      if (!response.ok) {
        throw Error(response.statusText);
      }

      return response.json();
    }).then(json => {
      // fileupload returns files = dict(fileUploadId, [{storage=storage_name, path=file_path}]) and unique fileUplaodResponseId
      for (const fileUploadId of Object.keys(json.files)) {
        // replace all uploaded files init params with 
        //(storage=storage_name, path=file_path) returned from x-jembe=fileupload request
        const ufiles = json.files[fileUploadId];
        const fu = this.filesForUpload[fileUploadId];
        this.addInitialiseCommand(fu.execName, {
          [fu.paramName]: fu.multipleFiles ? ufiles : ufiles[0]
        });
      }

      this.filesForUpload = {};
      return json.fileUploadResponseId;
    });
  }

  executeCommands(updateLocation = true) {
    const url = this.xRequestUrl !== null ? this.xRequestUrl : window.location.href;
    this.executeUpload().then(fileUploadResponseId => {
      const requestBody = this.getXRequestJson(); // reset commads since we create request body from it

      this.commands = []; // fetch request and process response

      window.fetch(url, {
        method: "POST",
        cache: "no-cache",
        credentials: "same-origin",
        redirect: "follow",
        referrer: "no-referrer",
        headers: fileUploadResponseId !== null ? {
          'X-JEMBE': 'commands',
          'X-JEMBE-RELATED-UPLOAD': fileUploadResponseId
        } : {
          'X-JEMBE': 'commands'
        },
        body: requestBody
      }).then(response => {
        if (!response.ok) {
          throw Error(response.statusText);
        }

        return response.json();
      }).then(json => this.getComponentsFromXResponse(json)).then(components => {
        this.updateDocument(components);

        if (updateLocation) {
          this.updateLocation();
        }
      }).catch(error => {
        throw error; // console.error("Error in request", error)
      });
    }).catch(error => {
      console.error("Error in request", error);
    });
  }

  updateLocation(replace = false) {
    let topComponent = null;
    let level = -1;
    let historyState = [];

    for (const component of Object.values(this.components)) {
      if (component.hierarchyLevel > level && component.changesUrl === true) {
        topComponent = component;
        level = component.hierarchyLevel;
      }

      historyState.push({
        execName: component.execName,
        state: component.state
      });
    }

    if (topComponent !== null) {
      if (replace) {
        window.history.replaceState(historyState, '', topComponent.url);
      } else {
        window.history.pushState(historyState, '', topComponent.url);
      }
    }
  }

  onHistoryPopState(event) {
    if (event.state === null) {
      window.location = document.location;
    } else {
      for (const comp of event.state) {
        this.jembeClient.addInitialiseCommand(comp.execName, comp.state);
        this.jembeClient.addCallCommand(comp.execName, "display");
      }

      this.jembeClient.executeCommands(false);
    }
  }
  /**
   * Used for geting jembeCompoentApi usually attached to document or window.jembeComponent 
   * @param {*} domNode 
   */


  component(domNode) {
    const componentExecName = domNode.closest('[jmb\\:name]').getAttribute('jmb:name');
    return this.components[componentExecName].api;
  }

}

exports.JembeClient = JembeClient;
},{"./componentApi.js":"componentApi.js","./utils.js":"utils.js","./morphdom/index.js":"morphdom/index.js"}],"jembe.js":[function(require,module,exports) {
"use strict";

var _client = require("./client.js");

window.jembeClient = new _client.JembeClient(document);
},{"./client.js":"client.js"}],"../../../node_modules/parcel/src/builtins/hmr-runtime.js":[function(require,module,exports) {
var global = arguments[3];
var OVERLAY_ID = '__parcel__error__overlay__';
var OldModule = module.bundle.Module;

function Module(moduleName) {
  OldModule.call(this, moduleName);
  this.hot = {
    data: module.bundle.hotData,
    _acceptCallbacks: [],
    _disposeCallbacks: [],
    accept: function (fn) {
      this._acceptCallbacks.push(fn || function () {});
    },
    dispose: function (fn) {
      this._disposeCallbacks.push(fn);
    }
  };
  module.bundle.hotData = null;
}

module.bundle.Module = Module;
var checkedAssets, assetsToAccept;
var parent = module.bundle.parent;

if ((!parent || !parent.isParcelRequire) && typeof WebSocket !== 'undefined') {
  var hostname = "" || location.hostname;
  var protocol = location.protocol === 'https:' ? 'wss' : 'ws';
  var ws = new WebSocket(protocol + '://' + hostname + ':' + "37327" + '/');

  ws.onmessage = function (event) {
    checkedAssets = {};
    assetsToAccept = [];
    var data = JSON.parse(event.data);

    if (data.type === 'update') {
      var handled = false;
      data.assets.forEach(function (asset) {
        if (!asset.isNew) {
          var didAccept = hmrAcceptCheck(global.parcelRequire, asset.id);

          if (didAccept) {
            handled = true;
          }
        }
      }); // Enable HMR for CSS by default.

      handled = handled || data.assets.every(function (asset) {
        return asset.type === 'css' && asset.generated.js;
      });

      if (handled) {
        console.clear();
        data.assets.forEach(function (asset) {
          hmrApply(global.parcelRequire, asset);
        });
        assetsToAccept.forEach(function (v) {
          hmrAcceptRun(v[0], v[1]);
        });
      } else if (location.reload) {
        // `location` global exists in a web worker context but lacks `.reload()` function.
        location.reload();
      }
    }

    if (data.type === 'reload') {
      ws.close();

      ws.onclose = function () {
        location.reload();
      };
    }

    if (data.type === 'error-resolved') {
      console.log('[parcel] ✨ Error resolved');
      removeErrorOverlay();
    }

    if (data.type === 'error') {
      console.error('[parcel] 🚨  ' + data.error.message + '\n' + data.error.stack);
      removeErrorOverlay();
      var overlay = createErrorOverlay(data);
      document.body.appendChild(overlay);
    }
  };
}

function removeErrorOverlay() {
  var overlay = document.getElementById(OVERLAY_ID);

  if (overlay) {
    overlay.remove();
  }
}

function createErrorOverlay(data) {
  var overlay = document.createElement('div');
  overlay.id = OVERLAY_ID; // html encode message and stack trace

  var message = document.createElement('div');
  var stackTrace = document.createElement('pre');
  message.innerText = data.error.message;
  stackTrace.innerText = data.error.stack;
  overlay.innerHTML = '<div style="background: black; font-size: 16px; color: white; position: fixed; height: 100%; width: 100%; top: 0px; left: 0px; padding: 30px; opacity: 0.85; font-family: Menlo, Consolas, monospace; z-index: 9999;">' + '<span style="background: red; padding: 2px 4px; border-radius: 2px;">ERROR</span>' + '<span style="top: 2px; margin-left: 5px; position: relative;">🚨</span>' + '<div style="font-size: 18px; font-weight: bold; margin-top: 20px;">' + message.innerHTML + '</div>' + '<pre>' + stackTrace.innerHTML + '</pre>' + '</div>';
  return overlay;
}

function getParents(bundle, id) {
  var modules = bundle.modules;

  if (!modules) {
    return [];
  }

  var parents = [];
  var k, d, dep;

  for (k in modules) {
    for (d in modules[k][1]) {
      dep = modules[k][1][d];

      if (dep === id || Array.isArray(dep) && dep[dep.length - 1] === id) {
        parents.push(k);
      }
    }
  }

  if (bundle.parent) {
    parents = parents.concat(getParents(bundle.parent, id));
  }

  return parents;
}

function hmrApply(bundle, asset) {
  var modules = bundle.modules;

  if (!modules) {
    return;
  }

  if (modules[asset.id] || !bundle.parent) {
    var fn = new Function('require', 'module', 'exports', asset.generated.js);
    asset.isNew = !modules[asset.id];
    modules[asset.id] = [fn, asset.deps];
  } else if (bundle.parent) {
    hmrApply(bundle.parent, asset);
  }
}

function hmrAcceptCheck(bundle, id) {
  var modules = bundle.modules;

  if (!modules) {
    return;
  }

  if (!modules[id] && bundle.parent) {
    return hmrAcceptCheck(bundle.parent, id);
  }

  if (checkedAssets[id]) {
    return;
  }

  checkedAssets[id] = true;
  var cached = bundle.cache[id];
  assetsToAccept.push([bundle, id]);

  if (cached && cached.hot && cached.hot._acceptCallbacks.length) {
    return true;
  }

  return getParents(global.parcelRequire, id).some(function (id) {
    return hmrAcceptCheck(global.parcelRequire, id);
  });
}

function hmrAcceptRun(bundle, id) {
  var cached = bundle.cache[id];
  bundle.hotData = {};

  if (cached) {
    cached.hot.data = bundle.hotData;
  }

  if (cached && cached.hot && cached.hot._disposeCallbacks.length) {
    cached.hot._disposeCallbacks.forEach(function (cb) {
      cb(bundle.hotData);
    });
  }

  delete bundle.cache[id];
  bundle(id);
  cached = bundle.cache[id];

  if (cached && cached.hot && cached.hot._acceptCallbacks.length) {
    cached.hot._acceptCallbacks.forEach(function (cb) {
      cb();
    });

    return true;
  }
}
},{}]},{},["../../../node_modules/parcel/src/builtins/hmr-runtime.js","jembe.js"], null)
//# sourceMappingURL=jembe.js.map