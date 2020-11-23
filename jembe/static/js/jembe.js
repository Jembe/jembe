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
exports.AsyncFunction = void 0;

function elIsNewComponent(el) {
  return el.hasAttribute('jmb:name');
}

function walkComponentDom(el, callback) {
  if (!elIsNewComponent(el)) {
    callback(el);
  }

  el = el.firstElementChild;

  while (el) {
    if (!elIsNewComponent(el)) {
      walkComponentDom(el, callback);
    }

    el = el.nextElementSibling;
  }
}

let AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
exports.AsyncFunction = AsyncFunction;
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

},{"process":"../../../node_modules/process/browser.js"}],"componentApi.js":[function(require,module,exports) {
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.JembeComponentAPI = void 0;

var _client = require("./client");

var _utils = require("./utils");

var _path = require("path");

/**
 * jembeClient.component(this).set('paramName', paramValue)
 * jembeClient.component(this).call('actionName', {kwargs})
 * jembeClient.component(this).display()
 * jembeClient.component(this).emit('eventName', {kwargs})
 * jembeClient.component(this).init('componentRelativeOrFullName', {kwargs})
 * jembeClient.executeCommands()
 * 
 * Short form that needs to be support for jmb:on.<eventName>[.deferred]:
 * $jmb.set('paramName', paramValue)
 * $jmb.call('actionName', {kwargs}) or actionName({kwargs})
 * $jmb.display() // call('display',{})
 * $jmb.emit('eventName',{kwargs})
 * $jmb.[init|component]('componentRelativeOrFullName', {kwargs})[.call|.display|.emit]
 * 
 * $jmb.ref('referencedDomName') // jmb:ref="referencedDomName"
 */
class JembeComponentAPI {
  constructor(jembeClient, componentExecName, initListeners = true) {
    /** @type {JembeClient} */
    this.jembeClient = jembeClient;
    /** @type {ComponentRef} */

    this.execName = componentExecName;

    if (initListeners) {
      this.initialiseJmbOnListeners();
    }

    this.refs = {};
  }

  call(actionName, kwargs = {}, args = []) {
    this.jembeClient.addCallCommand(this.execName, actionName, args, kwargs);
  }

  display() {
    this.call("display");
  }

  set(stateName, value) {
    //TODO set deep parameters
    params = {};
    params[stateName] = value;
    this.jembeClient.addInitialiseCommand(this.execName, params);
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

    return new JembeComponentAPI(this.jembeClient, execName, false);
  }

  init(relativeExecName, kwargs = {}) {
    return this.component(relativeExecName, kwargs);
  }

  ref(referenceName) {
    return this.refs[referenceName];
  }

  initialiseJmbOnListeners() {
    /** @type {ComponentRef} */
    const componentRef = this.jembeClient.components[this.execName];

    if (componentRef !== undefined) {
      // TODO walk dom and select elements
      (0, _utils.walkComponentDom)(componentRef.dom, el => {
        // initialise event listeneres for jmb:on. attributes
        if (el.hasAttributes()) {
          for (const attribute of el.attributes) {
            this._processDomAttribute(el, attribute.name, attribute.value);
          }
        }
      });
    }
  }

  _processDomAttribute(el, attrName, attrValue) {
    attrName = attrName.toLowerCase();

    if (attrName.startsWith('jmb:on.')) {
      let [jmbOn, eventName, ...decorators] = attrName.split("."); // support deferred decorator

      const deferred = decorators.indexOf("deferred") >= 0 ? "" : 'window.jembeClient.executeCommands()';
      let expression = `${attrValue};${deferred}`;
      el.addEventListener(eventName, event => {
        let helpers = {
          "$jmb": this,
          "$event": event,
          "$el": el
        };
        let scope = {};
        return Promise.resolve(new _utils.AsyncFunction(['scope', ...Object.keys(helpers)], `with(scope) { ${expression} }`)(scope, ...Object.values(helpers)));
      });
    } else if (attrName === "jmb:ref") {
      this.refs[attrValue] = el;
    }
  }

}

exports.JembeComponentAPI = JembeComponentAPI;
},{"./client":"client.js","./utils":"utils.js","path":"../../../node_modules/node-libs-browser/node_modules/path-browserify/index.js"}],"client.js":[function(require,module,exports) {
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.JembeClient = void 0;

var _componentApi = require("./componentApi.js");

/*
  Supported tags:
    # jmb:on.<eventname>.<modifier>.<modifier>
    # jmb:model=
    <button jmb:on.click="$jmb.call('increase',10)"
  TODO
  On x-jembe response update page:  
    - update only changed html of received components html
    - update window location


    build commands, send it and process response
    initialise ClientApi for every component
    add handles for jmb:on...
    $jmb (clientApi) avaiable in jmb:on... scripts
*/

/**
 * Reference to component html with associated data
 */
class ComponentRef {
  constructor(execName, data, dom, onDocument) {
    this.execName = execName;
    this.state = data.state;
    this.url = data.url;
    this.changesUrl = data.changesUrl;
    this.dom = dom;
    this.placeHolders = {};
    this.onDocument = onDocument;
    this.getPlaceHolders();
    this.api = null;
    this.hierarchyLevel = execName.split("/").length;
  }

  getPlaceHolders() {
    this.placeHolders = {};

    for (const placeholder of this.dom.querySelectorAll("template[jmb-placeholder]")) {
      this.placeHolders[placeholder.getAttribute("jmb-placeholder")] = placeholder;
    }

    for (const placeholder of this.dom.querySelectorAll("[jmb\\:name]")) {
      this.placeHolders[placeholder.getAttribute("jmb:name")] = placeholder;
    }
  }

  toJsonRequest() {
    return {
      "execName": this.execName,
      "state": this.state
    };
  }

}
/**
 * Handle all jembe logic on client side, primarly building, sending, processing 
 * and refreshing page for/on x-jembe requests
 */


class JembeClient {
  constructor(doc = document) {
    this.document = doc;
    this.components = this.getComponentsFromDocument();
    this.initComponentsAPI();
    this.updateLocation(true);
    this.commands = [];
    this.domParser = new DOMParser();
    this.xRequestUrl = null;
    window.onpopstate = this.onHistoryPopState;
  }
  /**
   * Finds all jmb:name and associate jmb:data tags in document 
   * and create ComponentRefs
   */


  getComponentsFromDocument() {
    // 
    let components = {}; // TODO traverse dom dont use querySelectorAll

    let componentsNodes = this.document.querySelectorAll("[jmb\\:name][jmb\\:data]");

    for (const componentNode of componentsNodes) {
      const execName = componentNode.getAttribute('jmb:name');
      components[execName] = new ComponentRef(execName, eval(`(${componentNode.getAttribute('jmb:data')})`), componentNode, true);
      componentNode.removeAttribute('jmb:data');
    }

    return components;
  }

  transformXResponseDom(execName, domString) {
    // if html dom has only one child use that child to put jmb:name tag
    // if not enclose html with div and put jmb:name into it
    // TODO: How to run event handlers onclick jmb:on.click <script> etc found in
    // html after integration with document
    if (!this.isPageExecName(execName)) {
      let template = this.document.createElement("template");
      template.innerHTML = domString;

      if (template.content.childNodes.length > 1) {
        let div = this.document.createElement("div");
        let curChild = template.content.firstChild;

        while (curChild) {
          let nextChild = curChild.nextSibling;
          div.appendChild(curChild);
          curChild = nextChild;
        }

        template.content.appendChild(div);
      } // check is it needed to add souranding DIV tag
      // add jmb:name tag


      if (template.content.childNodes.length > 1 || template.content.childNodes.length === 0 || template.content.firstChild.nodeType === Node.TEXT_NODE) {
        let div = this.document.createElement("div");

        for (const child of template.content.childNodes) {
          div.appendChild(child);
        }

        div.setAttribute("jmb:name", execName);
        return div;
      } else {
        template.content.firstChild.setAttribute("jmb:name", execName);
        return template.content.firstChild;
      }
    } else {
      const doc = this.domParser.parseFromString(domString, "text/html");
      doc.documentElement.setAttribute("jmb:name", execName);
      return doc.documentElement;
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
      components[xComp.execName] = new ComponentRef(xComp.execName, {
        "url": xComp.url,
        "changesUrl": xComp.changesUrl,
        "state": xComp.state
      }, this.transformXResponseDom(xComp.execName, xComp.dom), false);
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


    let pageExecNames = Object.keys(currentComponents).filter(execName => this.isPageExecName(execName));
    let pageExecName = pageExecNames[0];

    if (pageExecNames.length > 1) {
      for (const pen of pageExecNames) {
        if (!currentComponents[pen].onDocument) {
          pageExecName = pen;
        }
      }
    }

    let processingExecNames = [pageExecName];
    this.components = {};

    while (processingExecNames.length > 0) {
      const currentExecName = processingExecNames.shift();
      const currentCompoRef = currentComponents[currentExecName];
      this.mergeComponent(currentCompoRef);
      this.components[currentCompoRef.execName] = currentCompoRef;

      for (const placeHolderName of Object.keys(currentCompoRef.placeHolders)) {
        processingExecNames.push(placeHolderName);
      }
    }

    this.initComponentsAPI();
  }
  /**
   * Replaces component dom in this.document
   * and update this.components
   */


  mergeComponent(componentRef) {
    if (this.isPageExecName(componentRef.execName)) {
      // if page component is already on document do nothing
      if (!componentRef.onDocument) {
        this.document.documentElement.innerHTML = componentRef.dom.innerHTML;
        componentRef.dom = this.document.documentElement;
        componentRef.dom.setAttribute("jmb:name", componentRef.execName);
        componentRef.getPlaceHolders(); // becouse we use innerHTML not appendChild

        componentRef.onDocument = true;
      }
    } else {
      // search this.components for component with placeholder for this component
      let parentComponent = Object.values(this.components).filter(comp => Object.keys(comp.placeHolders).includes(componentRef.execName))[0];
      parentComponent.placeHolders[componentRef.execName].replaceWith(componentRef.dom);
      componentRef.onDocument = true;
    }
  }

  isPageExecName(execName) {
    return execName.split("/").length === 2;
  }

  addInitialiseCommand(execName, initParams) {
    const exisitingInitCommands = this.commands.filter(x => x.type === "init" && x.componentExecName === execName);

    if (exisitingInitCommands.length > 0) {
      for (const key of Object.keys(initParams)) {
        exisitingInitCommands[0].initParams[key] = initParams[key];
      }
    } else if (this.components[execName] !== undefined) {
      this.commands.push({
        "type": "init",
        "componentExecName": execName,
        "initParams": { ...this.components[execName].state,
          ...initParams
        }
      });
    } else {
      this.commands.push({
        "type": "init",
        "componentExecName": execName,
        "initParams": initParams
      });
    }
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

  getXRequestJson() {
    return JSON.stringify({
      "components": Object.values(this.components).map(x => x.toJsonRequest()),
      "commands": this.commands
    });
  }

  setXRequestUrl(url) {
    this.xRequestUrl = url;
  }

  executeCommands(updateLocation = true) {
    const url = this.xRequestUrl !== null ? this.xRequestUrl : window.location.href;
    const requestBody = this.getXRequestJson(); // reset commads since we create request body from it

    this.commands = []; // fetch request and process response

    fetch(url, {
      method: "POST",
      cache: "no-cache",
      credentials: "same-origin",
      redirect: "follow",
      referrer: "no-referrer",
      headers: {
        'X-JEMBE': true
      },
      body: requestBody
    }).then(response => {
      if (response.ok) {
        return response.json();
      } else {
        console.error("Request not successfull");
      }
    }).catch(error => {
      console.error("Error in request", error);
    }).then(json => this.getComponentsFromXResponse(json)).then(components => {
      this.updateDocument(components);

      if (updateLocation) {
        this.updateLocation();
      }
    });
  }

  initComponentsAPI() {
    for (const component of Object.values(this.components)) {
      if (component.api === null) {
        component.api = new _componentApi.JembeComponentAPI(this, component.execName);
      }
    }
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
},{"./componentApi.js":"componentApi.js"}],"jembe.js":[function(require,module,exports) {
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
  var ws = new WebSocket(protocol + '://' + hostname + ':' + "32769" + '/');

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