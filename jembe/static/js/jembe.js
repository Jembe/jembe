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
})({"componentApi/utils.js":[function(require,module,exports) {
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.domReady = domReady;
exports.arrayUnique = arrayUnique;
exports.isTesting = isTesting;
exports.checkedAttrLooseCompare = checkedAttrLooseCompare;
exports.warnIfMalformedTemplate = warnIfMalformedTemplate;
exports.kebabCase = kebabCase;
exports.camelCase = camelCase;
exports.walk = walk;
exports.debounce = debounce;
exports.saferEval = saferEval;
exports.saferEvalNoReturn = saferEvalNoReturn;
exports.isXAttr = isXAttr;
exports.getXAttrs = getXAttrs;
exports.parseHtmlAttribute = parseHtmlAttribute;
exports.isBooleanAttr = isBooleanAttr;
exports.replaceAtAndColonWithStandardSyntax = replaceAtAndColonWithStandardSyntax;
exports.convertClassStringToArray = convertClassStringToArray;
exports.transitionIn = transitionIn;
exports.transitionOut = transitionOut;
exports.transitionHelperIn = transitionHelperIn;
exports.transitionHelperOut = transitionHelperOut;
exports.transitionHelper = transitionHelper;
exports.transitionClassesIn = transitionClassesIn;
exports.transitionClassesOut = transitionClassesOut;
exports.transitionClasses = transitionClasses;
exports.transition = transition;
exports.isNumeric = isNumeric;
exports.once = once;
exports.TRANSITION_CANCELLED = exports.TRANSITION_TYPE_OUT = exports.TRANSITION_TYPE_IN = void 0;

// Thanks @stimulus:
// https://github.com/stimulusjs/stimulus/blob/master/packages/%40stimulus/core/src/application.ts
function domReady() {
  return new Promise(resolve => {
    if (document.readyState == "loading") {
      document.addEventListener("DOMContentLoaded", resolve);
    } else {
      resolve();
    }
  });
}

function arrayUnique(array) {
  return Array.from(new Set(array));
}

function isTesting() {
  return navigator.userAgent, navigator.userAgent.includes("Node.js") || navigator.userAgent.includes("jsdom");
}

function checkedAttrLooseCompare(valueA, valueB) {
  return valueA == valueB;
}

function warnIfMalformedTemplate(el, directive) {
  if (el.tagName.toLowerCase() !== 'template') {
    console.warn(`Alpine: [${directive}] directive should only be added to <template> tags. See https://github.com/alpinejs/alpine#${directive}`);
  } else if (el.content.childElementCount !== 1) {
    console.warn(`Alpine: <template> tag with [${directive}] encountered with an unexpected number of root elements. Make sure <template> has a single root element. `);
  }
}

function kebabCase(subject) {
  return subject.replace(/([a-z])([A-Z])/g, '$1-$2').replace(/[_\s]/, '-').toLowerCase();
}

function camelCase(subject) {
  return subject.toLowerCase().replace(/-(\w)/g, (match, char) => char.toUpperCase());
}

function walk(el, callback) {
  if (callback(el) === false) return;
  let node = el.firstElementChild;

  while (node) {
    walk(node, callback);
    node = node.nextElementSibling;
  }
}

function debounce(func, wait) {
  var timeout;
  return function () {
    var context = this,
        args = arguments;

    var later = function () {
      timeout = null;
      func.apply(context, args);
    };

    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

const handleError = (el, expression, error) => {
  console.warn(`Alpine Error: "${error}"\n\nExpression: "${expression}"\nElement:`, el);

  if (!isTesting()) {
    Object.assign(error, {
      el,
      expression
    });
    throw error;
  }
};

function tryCatch(cb, {
  el,
  expression
}) {
  try {
    const value = cb();
    return value instanceof Promise ? value.catch(e => handleError(el, expression, e)) : value;
  } catch (e) {
    handleError(el, expression, e);
  }
}

function saferEval(el, expression, dataContext, additionalHelperVariables = {}) {
  return tryCatch(() => {
    if (typeof expression === 'function') {
      return expression.call(dataContext);
    }

    return new Function(['$data', ...Object.keys(additionalHelperVariables)], `var __alpine_result; with($data) { __alpine_result = ${expression} }; return __alpine_result`)(dataContext, ...Object.values(additionalHelperVariables));
  }, {
    el,
    expression
  });
}

function saferEvalNoReturn(el, expression, dataContext, additionalHelperVariables = {}) {
  return tryCatch(() => {
    if (typeof expression === 'function') {
      return Promise.resolve(expression.call(dataContext, additionalHelperVariables['$event']));
    }

    let AsyncFunction = Function;
    /* MODERN-ONLY:START */

    AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
    /* MODERN-ONLY:END */
    // For the cases when users pass only a function reference to the caller: `jmb-on:click="foo"`
    // Where "foo" is a function. Also, we'll pass the function the event instance when we call it.

    if (Object.keys(dataContext).includes(expression)) {
      let methodReference = new Function(['dataContext', ...Object.keys(additionalHelperVariables)], `with(dataContext) { return ${expression} }`)(dataContext, ...Object.values(additionalHelperVariables));

      if (typeof methodReference === 'function') {
        return Promise.resolve(methodReference.call(dataContext, additionalHelperVariables['$event']));
      } else {
        return Promise.resolve();
      }
    }

    return Promise.resolve(new AsyncFunction(['dataContext', ...Object.keys(additionalHelperVariables)], `with(dataContext) { ${expression} }`)(dataContext, ...Object.values(additionalHelperVariables)));
  }, {
    el,
    expression
  });
}

const xAttrRE = /^jmb-(on|bind|data|text|html|model|if|for|show|cloak|transition|ref|spread)\b/;

function isXAttr(attr) {
  const name = replaceAtAndColonWithStandardSyntax(attr.name);
  return xAttrRE.test(name);
}

function getXAttrs(el, component, type) {
  let directives = Array.from(el.attributes).filter(isXAttr).map(parseHtmlAttribute); // Get an object of directives from jmb-spread.

  let spreadDirective = directives.filter(directive => directive.type === 'spread')[0];

  if (spreadDirective) {
    let spreadObject = saferEval(el, spreadDirective.expression, component.$data); // Add jmb-spread directives to the pile of existing directives.

    directives = directives.concat(Object.entries(spreadObject).map(([name, value]) => parseHtmlAttribute({
      name,
      value
    })));
  }

  if (type) return directives.filter(i => i.type === type);
  return sortDirectives(directives);
}

function sortDirectives(directives) {
  let directiveOrder = ['bind', 'model', 'show', 'catch-all'];
  return directives.sort((a, b) => {
    let typeA = directiveOrder.indexOf(a.type) === -1 ? 'catch-all' : a.type;
    let typeB = directiveOrder.indexOf(b.type) === -1 ? 'catch-all' : b.type;
    return directiveOrder.indexOf(typeA) - directiveOrder.indexOf(typeB);
  });
}

function parseHtmlAttribute({
  name,
  value
}) {
  const normalizedName = replaceAtAndColonWithStandardSyntax(name);
  const typeMatch = normalizedName.match(xAttrRE);
  const valueMatch = normalizedName.match(/:([a-zA-Z0-9\-:]+)/);
  const modifiers = normalizedName.match(/\.[^.\]]+(?=[^\]]*$)/g) || [];
  return {
    type: typeMatch ? typeMatch[1] : null,
    value: valueMatch ? valueMatch[1] : null,
    modifiers: modifiers.map(i => i.replace('.', '')),
    expression: value
  };
}

function isBooleanAttr(attrName) {
  // As per HTML spec table https://html.spec.whatwg.org/multipage/indices.html#attributes-3:boolean-attribute
  // Array roughly ordered by estimated usage
  const booleanAttributes = ['disabled', 'checked', 'required', 'readonly', 'hidden', 'open', 'selected', 'autofocus', 'itemscope', 'multiple', 'novalidate', 'allowfullscreen', 'allowpaymentrequest', 'formnovalidate', 'autoplay', 'controls', 'loop', 'muted', 'playsinline', 'default', 'ismap', 'reversed', 'async', 'defer', 'nomodule'];
  return booleanAttributes.includes(attrName);
}

function replaceAtAndColonWithStandardSyntax(name) {
  if (name.startsWith('@')) {
    return name.replace('@', 'jmb-on:');
  } else if (name.startsWith(':')) {
    return name.replace(':', 'jmb-bind:');
  }

  return name;
}

function convertClassStringToArray(classList, filterFn = Boolean) {
  return classList.split(' ').filter(filterFn);
}

const TRANSITION_TYPE_IN = 'in';
exports.TRANSITION_TYPE_IN = TRANSITION_TYPE_IN;
const TRANSITION_TYPE_OUT = 'out';
exports.TRANSITION_TYPE_OUT = TRANSITION_TYPE_OUT;
const TRANSITION_CANCELLED = 'cancelled';
exports.TRANSITION_CANCELLED = TRANSITION_CANCELLED;

function transitionIn(el, show, reject, component, forceSkip = false) {
  // We don't want to transition on the initial page load.
  if (forceSkip) return show();

  if (el.__jmb_transition && el.__jmb_transition.type === TRANSITION_TYPE_IN) {
    // there is already a similar transition going on, this was probably triggered by
    // a change in a different property, let's just leave the previous one doing its job
    return;
  }

  const attrs = getXAttrs(el, component, 'transition');
  const showAttr = getXAttrs(el, component, 'show')[0]; // If this is triggered by a jmb-show.transition.

  if (showAttr && showAttr.modifiers.includes('transition')) {
    let modifiers = showAttr.modifiers; // If jmb-show.transition.out, we'll skip the "in" transition.

    if (modifiers.includes('out') && !modifiers.includes('in')) return show();
    const settingBothSidesOfTransition = modifiers.includes('in') && modifiers.includes('out'); // If jmb-show.transition.in...out... only use "in" related modifiers for this transition.

    modifiers = settingBothSidesOfTransition ? modifiers.filter((i, index) => index < modifiers.indexOf('out')) : modifiers;
    transitionHelperIn(el, modifiers, show, reject); // Otherwise, we can assume jmb-transition:enter.
  } else if (attrs.some(attr => ['enter', 'enter-start', 'enter-end'].includes(attr.value))) {
    transitionClassesIn(el, component, attrs, show, reject);
  } else {
    // If neither, just show that damn thing.
    show();
  }
}

function transitionOut(el, hide, reject, component, forceSkip = false) {
  // We don't want to transition on the initial page load.
  if (forceSkip) return hide();

  if (el.__jmb_transition && el.__jmb_transition.type === TRANSITION_TYPE_OUT) {
    // there is already a similar transition going on, this was probably triggered by
    // a change in a different property, let's just leave the previous one doing its job
    return;
  }

  const attrs = getXAttrs(el, component, 'transition');
  const showAttr = getXAttrs(el, component, 'show')[0];

  if (showAttr && showAttr.modifiers.includes('transition')) {
    let modifiers = showAttr.modifiers;
    if (modifiers.includes('in') && !modifiers.includes('out')) return hide();
    const settingBothSidesOfTransition = modifiers.includes('in') && modifiers.includes('out');
    modifiers = settingBothSidesOfTransition ? modifiers.filter((i, index) => index > modifiers.indexOf('out')) : modifiers;
    transitionHelperOut(el, modifiers, settingBothSidesOfTransition, hide, reject);
  } else if (attrs.some(attr => ['leave', 'leave-start', 'leave-end'].includes(attr.value))) {
    transitionClassesOut(el, component, attrs, hide, reject);
  } else {
    hide();
  }
}

function transitionHelperIn(el, modifiers, showCallback, reject) {
  // Default values inspired by: https://material.io/design/motion/speed.html#duration
  const styleValues = {
    duration: modifierValue(modifiers, 'duration', 150),
    origin: modifierValue(modifiers, 'origin', 'center'),
    first: {
      opacity: 0,
      scale: modifierValue(modifiers, 'scale', 95)
    },
    second: {
      opacity: 1,
      scale: 100
    }
  };
  transitionHelper(el, modifiers, showCallback, () => {}, reject, styleValues, TRANSITION_TYPE_IN);
}

function transitionHelperOut(el, modifiers, settingBothSidesOfTransition, hideCallback, reject) {
  // Make the "out" transition .5x slower than the "in". (Visually better)
  // HOWEVER, if they explicitly set a duration for the "out" transition,
  // use that.
  const duration = settingBothSidesOfTransition ? modifierValue(modifiers, 'duration', 150) : modifierValue(modifiers, 'duration', 150) / 2;
  const styleValues = {
    duration: duration,
    origin: modifierValue(modifiers, 'origin', 'center'),
    first: {
      opacity: 1,
      scale: 100
    },
    second: {
      opacity: 0,
      scale: modifierValue(modifiers, 'scale', 95)
    }
  };
  transitionHelper(el, modifiers, () => {}, hideCallback, reject, styleValues, TRANSITION_TYPE_OUT);
}

function modifierValue(modifiers, key, fallback) {
  // If the modifier isn't present, use the default.
  if (modifiers.indexOf(key) === -1) return fallback; // If it IS present, grab the value after it: jmb-show.transition.duration.500ms

  const rawValue = modifiers[modifiers.indexOf(key) + 1];
  if (!rawValue) return fallback;

  if (key === 'scale') {
    // Check if the very next value is NOT a number and return the fallback.
    // If jmb-show.transition.scale, we'll use the default scale value.
    // That is how a user opts out of the opacity transition.
    if (!isNumeric(rawValue)) return fallback;
  }

  if (key === 'duration') {
    // Support jmb-show.transition.duration.500ms && duration.500
    let match = rawValue.match(/([0-9]+)ms/);
    if (match) return match[1];
  }

  if (key === 'origin') {
    // Support chaining origin directions: jmb-show.transition.top.right
    if (['top', 'right', 'left', 'center', 'bottom'].includes(modifiers[modifiers.indexOf(key) + 2])) {
      return [rawValue, modifiers[modifiers.indexOf(key) + 2]].join(' ');
    }
  }

  return rawValue;
}

function transitionHelper(el, modifiers, hook1, hook2, reject, styleValues, type) {
  // clear the previous transition if exists to avoid caching the wrong styles
  if (el.__jmb_transition) {
    el.__jmb_transition.cancel && el.__jmb_transition.cancel();
  } // If the user set these style values, we'll put them back when we're done with them.


  const opacityCache = el.style.opacity;
  const transformCache = el.style.transform;
  const transformOriginCache = el.style.transformOrigin; // If no modifiers are present: jmb-show.transition, we'll default to both opacity and scale.

  const noModifiers = !modifiers.includes('opacity') && !modifiers.includes('scale');
  const transitionOpacity = noModifiers || modifiers.includes('opacity');
  const transitionScale = noModifiers || modifiers.includes('scale'); // These are the explicit stages of a transition (same stages for in and for out).
  // This way you can get a birds eye view of the hooks, and the differences
  // between them.

  const stages = {
    start() {
      if (transitionOpacity) el.style.opacity = styleValues.first.opacity;
      if (transitionScale) el.style.transform = `scale(${styleValues.first.scale / 100})`;
    },

    during() {
      if (transitionScale) el.style.transformOrigin = styleValues.origin;
      el.style.transitionProperty = [transitionOpacity ? `opacity` : ``, transitionScale ? `transform` : ``].join(' ').trim();
      el.style.transitionDuration = `${styleValues.duration / 1000}s`;
      el.style.transitionTimingFunction = `cubic-bezier(0.4, 0.0, 0.2, 1)`;
    },

    show() {
      hook1();
    },

    end() {
      if (transitionOpacity) el.style.opacity = styleValues.second.opacity;
      if (transitionScale) el.style.transform = `scale(${styleValues.second.scale / 100})`;
    },

    hide() {
      hook2();
    },

    cleanup() {
      if (transitionOpacity) el.style.opacity = opacityCache;
      if (transitionScale) el.style.transform = transformCache;
      if (transitionScale) el.style.transformOrigin = transformOriginCache;
      el.style.transitionProperty = null;
      el.style.transitionDuration = null;
      el.style.transitionTimingFunction = null;
    }

  };
  transition(el, stages, type, reject);
}

const ensureStringExpression = (expression, el, component) => {
  return typeof expression === 'function' ? component.evaluateReturnExpression(el, expression) : expression;
};

function transitionClassesIn(el, component, directives, showCallback, reject) {
  const enter = convertClassStringToArray(ensureStringExpression((directives.find(i => i.value === 'enter') || {
    expression: ''
  }).expression, el, component));
  const enterStart = convertClassStringToArray(ensureStringExpression((directives.find(i => i.value === 'enter-start') || {
    expression: ''
  }).expression, el, component));
  const enterEnd = convertClassStringToArray(ensureStringExpression((directives.find(i => i.value === 'enter-end') || {
    expression: ''
  }).expression, el, component));
  transitionClasses(el, enter, enterStart, enterEnd, showCallback, () => {}, TRANSITION_TYPE_IN, reject);
}

function transitionClassesOut(el, component, directives, hideCallback, reject) {
  const leave = convertClassStringToArray(ensureStringExpression((directives.find(i => i.value === 'leave') || {
    expression: ''
  }).expression, el, component));
  const leaveStart = convertClassStringToArray(ensureStringExpression((directives.find(i => i.value === 'leave-start') || {
    expression: ''
  }).expression, el, component));
  const leaveEnd = convertClassStringToArray(ensureStringExpression((directives.find(i => i.value === 'leave-end') || {
    expression: ''
  }).expression, el, component));
  transitionClasses(el, leave, leaveStart, leaveEnd, () => {}, hideCallback, TRANSITION_TYPE_OUT, reject);
}

function transitionClasses(el, classesDuring, classesStart, classesEnd, hook1, hook2, type, reject) {
  // clear the previous transition if exists to avoid caching the wrong classes
  if (el.__jmb_transition) {
    el.__jmb_transition.cancel && el.__jmb_transition.cancel();
  }

  const originalClasses = el.__jmb_original_classes || [];
  const stages = {
    start() {
      el.classList.add(...classesStart);
    },

    during() {
      el.classList.add(...classesDuring);
    },

    show() {
      hook1();
    },

    end() {
      // Don't remove classes that were in the original class attribute.
      el.classList.remove(...classesStart.filter(i => !originalClasses.includes(i)));
      el.classList.add(...classesEnd);
    },

    hide() {
      hook2();
    },

    cleanup() {
      el.classList.remove(...classesDuring.filter(i => !originalClasses.includes(i)));
      el.classList.remove(...classesEnd.filter(i => !originalClasses.includes(i)));
    }

  };
  transition(el, stages, type, reject);
}

function transition(el, stages, type, reject) {
  const finish = once(() => {
    stages.hide(); // Adding an "isConnected" check, in case the callback
    // removed the element from the DOM.

    if (el.isConnected) {
      stages.cleanup();
    }

    delete el.__jmb_transition;
  });
  el.__jmb_transition = {
    // Set transition type so we can avoid clearing transition if the direction is the same
    type: type,
    // create a callback for the last stages of the transition so we can call it
    // from different point and early terminate it. Once will ensure that function
    // is only called one time.
    cancel: once(() => {
      reject(TRANSITION_CANCELLED);
      finish();
    }),
    finish,
    // This store the next animation frame so we can cancel it
    nextFrame: null
  };
  stages.start();
  stages.during();
  el.__jmb_transition.nextFrame = requestAnimationFrame(() => {
    // Note: Safari's transitionDuration property will list out comma separated transition durations
    // for every single transition property. Let's grab the first one and call it a day.
    let duration = Number(getComputedStyle(el).transitionDuration.replace(/,.*/, '').replace('s', '')) * 1000;

    if (duration === 0) {
      duration = Number(getComputedStyle(el).animationDuration.replace('s', '')) * 1000;
    }

    stages.show();
    el.__jmb_transition.nextFrame = requestAnimationFrame(() => {
      stages.end();
      setTimeout(el.__jmb_transition.finish, duration);
    });
  });
}

function isNumeric(subject) {
  return !Array.isArray(subject) && !isNaN(subject);
} // Thanks @vuejs
// https://github.com/vuejs/vue/blob/4de4649d9637262a9b007720b59f80ac72a5620c/src/shared/util.js


function once(callback) {
  let called = false;
  return function () {
    if (!called) {
      called = true;
      callback.apply(this, arguments);
    }
  };
}
},{}],"componentApi/directives/for.js":[function(require,module,exports) {
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.handleForDirective = handleForDirective;

var _utils = require("../utils");

function handleForDirective(component, templateEl, expression, initialUpdate, extraVars) {
  (0, _utils.warnIfMalformedTemplate)(templateEl, 'jmb-for');
  let iteratorNames = typeof expression === 'function' ? parseForExpression(component.evaluateReturnExpression(templateEl, expression)) : parseForExpression(expression);
  let items = evaluateItemsAndReturnEmptyIfXIfIsPresentAndFalseOnElement(component, templateEl, iteratorNames, extraVars); // As we walk the array, we'll also walk the DOM (updating/creating as we go).

  let currentEl = templateEl;
  items.forEach((item, index) => {
    let iterationScopeVariables = getIterationScopeVariables(iteratorNames, item, index, items, extraVars());
    let currentKey = generateKeyForIteration(component, templateEl, index, iterationScopeVariables);
    let nextEl = lookAheadForMatchingKeyedElementAndMoveItIfFound(currentEl.nextElementSibling, currentKey); // If we haven't found a matching key, insert the element at the current position.

    if (!nextEl) {
      nextEl = addElementInLoopAfterCurrentEl(templateEl, currentEl); // And transition it in if it's not the first page load.

      (0, _utils.transitionIn)(nextEl, () => {}, () => {}, component, initialUpdate);
      nextEl.__jmb_for = iterationScopeVariables;
      component.initializeElements(nextEl, () => nextEl.__jmb_for); // Otherwise update the element we found.
    } else {
      // Temporarily remove the key indicator to allow the normal "updateElements" to work.
      delete nextEl.__jmb_for_key;
      nextEl.__jmb_for = iterationScopeVariables;
      component.updateElements(nextEl, () => nextEl.__jmb_for);
    }

    currentEl = nextEl;
    currentEl.__jmb_for_key = currentKey;
  });
  removeAnyLeftOverElementsFromPreviousUpdate(currentEl, component);
} // This was taken from VueJS 2.* core. Thanks Vue!


function parseForExpression(expression) {
  let forIteratorRE = /,([^,\}\]]*)(?:,([^,\}\]]*))?$/;
  let stripParensRE = /^\(|\)$/g;
  let forAliasRE = /([\s\S]*?)\s+(?:in|of)\s+([\s\S]*)/;
  let inMatch = String(expression).match(forAliasRE);
  if (!inMatch) return;
  let res = {};
  res.items = inMatch[2].trim();
  let item = inMatch[1].trim().replace(stripParensRE, '');
  let iteratorMatch = item.match(forIteratorRE);

  if (iteratorMatch) {
    res.item = item.replace(forIteratorRE, '').trim();
    res.index = iteratorMatch[1].trim();

    if (iteratorMatch[2]) {
      res.collection = iteratorMatch[2].trim();
    }
  } else {
    res.item = item;
  }

  return res;
}

function getIterationScopeVariables(iteratorNames, item, index, items, extraVars) {
  // We must create a new object, so each iteration has a new scope
  let scopeVariables = extraVars ? { ...extraVars
  } : {};
  scopeVariables[iteratorNames.item] = item;
  if (iteratorNames.index) scopeVariables[iteratorNames.index] = index;
  if (iteratorNames.collection) scopeVariables[iteratorNames.collection] = items;
  return scopeVariables;
}

function generateKeyForIteration(component, el, index, iterationScopeVariables) {
  let bindKeyAttribute = (0, _utils.getXAttrs)(el, component, 'bind').filter(attr => attr.value === 'key')[0]; // If the dev hasn't specified a key, just return the index of the iteration.

  if (!bindKeyAttribute) return index;
  return component.evaluateReturnExpression(el, bindKeyAttribute.expression, () => iterationScopeVariables);
}

function evaluateItemsAndReturnEmptyIfXIfIsPresentAndFalseOnElement(component, el, iteratorNames, extraVars) {
  let ifAttribute = (0, _utils.getXAttrs)(el, component, 'if')[0];

  if (ifAttribute && !component.evaluateReturnExpression(el, ifAttribute.expression)) {
    return [];
  }

  let items = component.evaluateReturnExpression(el, iteratorNames.items, extraVars); // This adds support for the `i in n` syntax.

  if ((0, _utils.isNumeric)(items) && items >= 0) {
    items = Array.from(Array(items).keys(), i => i + 1);
  }

  return items;
}

function addElementInLoopAfterCurrentEl(templateEl, currentEl) {
  let clone = document.importNode(templateEl.content, true);
  currentEl.parentElement.insertBefore(clone, currentEl.nextElementSibling);
  return currentEl.nextElementSibling;
}

function lookAheadForMatchingKeyedElementAndMoveItIfFound(nextEl, currentKey) {
  if (!nextEl) return; // If we are already past the jmb-for generated elements, we don't need to look ahead.

  if (nextEl.__jmb_for_key === undefined) return; // If the the key's DO match, no need to look ahead.

  if (nextEl.__jmb_for_key === currentKey) return nextEl; // If they don't, we'll look ahead for a match.
  // If we find it, we'll move it to the current position in the loop.

  let tmpNextEl = nextEl;

  while (tmpNextEl) {
    if (tmpNextEl.__jmb_for_key === currentKey) {
      return tmpNextEl.parentElement.insertBefore(tmpNextEl, nextEl);
    }

    tmpNextEl = tmpNextEl.nextElementSibling && tmpNextEl.nextElementSibling.__jmb_for_key !== undefined ? tmpNextEl.nextElementSibling : false;
  }
}

function removeAnyLeftOverElementsFromPreviousUpdate(currentEl, component) {
  var nextElementFromOldLoop = currentEl.nextElementSibling && currentEl.nextElementSibling.__jmb_for_key !== undefined ? currentEl.nextElementSibling : false;

  while (nextElementFromOldLoop) {
    let nextElementFromOldLoopImmutable = nextElementFromOldLoop;
    let nextSibling = nextElementFromOldLoop.nextElementSibling;
    (0, _utils.transitionOut)(nextElementFromOldLoop, () => {
      nextElementFromOldLoopImmutable.remove();
    }, () => {}, component);
    nextElementFromOldLoop = nextSibling && nextSibling.__jmb_for_key !== undefined ? nextSibling : false;
  }
}
},{"../utils":"componentApi/utils.js"}],"componentApi/directives/bind.js":[function(require,module,exports) {
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.handleAttributeBindingDirective = handleAttributeBindingDirective;

var _utils = require("../utils");

var _index = _interopRequireDefault(require("../index"));

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

function handleAttributeBindingDirective(component, el, attrName, expression, extraVars, attrType, modifiers) {
  var value = component.evaluateReturnExpression(el, expression, extraVars);

  if (attrName === 'value') {
    if (_index.default.ignoreFocusedForValueBinding && document.activeElement.isSameNode(el)) return; // If nested model key is undefined, set the default value to empty string.

    if (value === undefined && String(expression).match(/\./)) {
      value = '';
    }

    if (el.type === 'radio') {
      // Set radio value from jmb-bind:value, if no "value" attribute exists.
      // If there are any initial state values, radio will have a correct
      // "checked" value since jmb-bind:value is processed before jmb-model.
      if (el.attributes.value === undefined && attrType === 'bind') {
        el.value = value;
      } else if (attrType !== 'bind') {
        el.checked = (0, _utils.checkedAttrLooseCompare)(el.value, value);
      }
    } else if (el.type === 'checkbox') {
      // If we are explicitly binding a string to the :value, set the string,
      // If the value is a boolean, leave it alone, it will be set to "on"
      // automatically.
      if (typeof value !== 'boolean' && ![null, undefined].includes(value) && attrType === 'bind') {
        el.value = String(value);
      } else if (attrType !== 'bind') {
        if (Array.isArray(value)) {
          // I'm purposely not using Array.includes here because it's
          // strict, and because of Numeric/String mis-casting, I
          // want the "includes" to be "fuzzy".
          el.checked = value.some(val => (0, _utils.checkedAttrLooseCompare)(val, el.value));
        } else {
          el.checked = !!value;
        }
      }
    } else if (el.tagName === 'SELECT') {
      updateSelect(el, value);
    } else {
      if (el.value === value) return;
      el.value = value;
    }
  } else if (attrName === 'class') {
    if (Array.isArray(value)) {
      const originalClasses = el.__jmb_original_classes || [];
      el.setAttribute('class', (0, _utils.arrayUnique)(originalClasses.concat(value)).join(' '));
    } else if (typeof value === 'object') {
      // Sorting the keys / class names by their boolean value will ensure that
      // anything that evaluates to `false` and needs to remove classes is run first.
      const keysSortedByBooleanValue = Object.keys(value).sort((a, b) => value[a] - value[b]);
      keysSortedByBooleanValue.forEach(classNames => {
        if (value[classNames]) {
          (0, _utils.convertClassStringToArray)(classNames).forEach(className => el.classList.add(className));
        } else {
          (0, _utils.convertClassStringToArray)(classNames).forEach(className => el.classList.remove(className));
        }
      });
    } else {
      const originalClasses = el.__jmb_original_classes || [];
      const newClasses = value ? (0, _utils.convertClassStringToArray)(value) : [];
      el.setAttribute('class', (0, _utils.arrayUnique)(originalClasses.concat(newClasses)).join(' '));
    }
  } else {
    attrName = modifiers.includes('camel') ? (0, _utils.camelCase)(attrName) : attrName; // If an attribute's bound value is null, undefined or false, remove the attribute

    if ([null, undefined, false].includes(value)) {
      el.removeAttribute(attrName);
    } else {
      (0, _utils.isBooleanAttr)(attrName) ? setIfChanged(el, attrName, attrName) : setIfChanged(el, attrName, value);
    }
  }
}

function setIfChanged(el, attrName, value) {
  if (el.getAttribute(attrName) != value) {
    el.setAttribute(attrName, value);
  }
}

function updateSelect(el, value) {
  const arrayWrappedValue = [].concat(value).map(value => {
    return value + '';
  });
  Array.from(el.options).forEach(option => {
    option.selected = arrayWrappedValue.includes(option.value || option.text);
  });
}
},{"../utils":"componentApi/utils.js","../index":"componentApi/index.js"}],"componentApi/directives/text.js":[function(require,module,exports) {
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.handleTextDirective = handleTextDirective;

function handleTextDirective(el, output, expression) {
  // If nested model key is undefined, set the default value to empty string.
  if (output === undefined && String(expression).match(/\./)) {
    output = '';
  }

  el.textContent = output;
}
},{}],"componentApi/directives/html.js":[function(require,module,exports) {
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.handleHtmlDirective = handleHtmlDirective;

function handleHtmlDirective(component, el, expression, extraVars) {
  el.innerHTML = component.evaluateReturnExpression(el, expression, extraVars);
}
},{}],"componentApi/directives/show.js":[function(require,module,exports) {
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.handleShowDirective = handleShowDirective;

var _utils = require("../utils");

function handleShowDirective(component, el, value, modifiers, initialUpdate = false) {
  const hide = () => {
    el.style.display = 'none';
    el.__jmb_is_shown = false;
  };

  const show = () => {
    if (el.style.length === 1 && el.style.display === 'none') {
      el.removeAttribute('style');
    } else {
      el.style.removeProperty('display');
    }

    el.__jmb_is_shown = true;
  };

  if (initialUpdate === true) {
    if (value) {
      show();
    } else {
      hide();
    }

    return;
  }

  const handle = (resolve, reject) => {
    if (value) {
      if (el.style.display === 'none' || el.__jmb_transition) {
        (0, _utils.transitionIn)(el, () => {
          show();
        }, reject, component);
      }

      resolve(() => {});
    } else {
      if (el.style.display !== 'none') {
        (0, _utils.transitionOut)(el, () => {
          resolve(() => {
            hide();
          });
        }, reject, component);
      } else {
        resolve(() => {});
      }
    }
  }; // The working of jmb-show is a bit complex because we need to
  // wait for any child transitions to finish before hiding
  // some element. Also, this has to be done recursively.
  // If jmb-show.immediate, foregoe the waiting.


  if (modifiers.includes('immediate')) {
    handle(finish => finish(), () => {});
    return;
  } // jmb-show is encountered during a DOM tree walk. If an element
  // we encounter is NOT a child of another jmb-show element we
  // can execute the previous jmb-show stack (if one exists).


  if (component.showDirectiveLastElement && !component.showDirectiveLastElement.contains(el)) {
    component.executeAndClearRemainingShowDirectiveStack();
  }

  component.showDirectiveStack.push(handle);
  component.showDirectiveLastElement = el;
}
},{"../utils":"componentApi/utils.js"}],"componentApi/directives/if.js":[function(require,module,exports) {
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.handleIfDirective = handleIfDirective;

var _utils = require("../utils");

function handleIfDirective(component, el, expressionResult, initialUpdate, extraVars) {
  (0, _utils.warnIfMalformedTemplate)(el, 'jmb-if');
  const elementHasAlreadyBeenAdded = el.nextElementSibling && el.nextElementSibling.__jmb_inserted_me === true;

  if (expressionResult && (!elementHasAlreadyBeenAdded || el.__jmb_transition)) {
    const clone = document.importNode(el.content, true);
    el.parentElement.insertBefore(clone, el.nextElementSibling);
    (0, _utils.transitionIn)(el.nextElementSibling, () => {}, () => {}, component, initialUpdate);
    component.initializeElements(el.nextElementSibling, extraVars);
    el.nextElementSibling.__jmb_inserted_me = true;
  } else if (!expressionResult && elementHasAlreadyBeenAdded) {
    (0, _utils.transitionOut)(el.nextElementSibling, () => {
      el.nextElementSibling.remove();
    }, () => {}, component, initialUpdate);
  }
}
},{"../utils":"componentApi/utils.js"}],"componentApi/directives/on.js":[function(require,module,exports) {
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.registerListener = registerListener;

var _utils = require("../utils");

function registerListener(component, el, event, modifiers, expression, extraVars = {}) {
  const options = {
    passive: modifiers.includes('passive')
  };

  if (modifiers.includes('camel')) {
    event = (0, _utils.camelCase)(event);
  }

  let handler, listenerTarget;

  if (modifiers.includes('away')) {
    listenerTarget = document;

    handler = e => {
      // Don't do anything if the click came from the element or within it.
      if (el.contains(e.target)) return; // Don't do anything if this element isn't currently visible.

      if (el.offsetWidth < 1 && el.offsetHeight < 1) return; // Now that we are sure the element is visible, AND the click
      // is from outside it, let's run the expression.

      runListenerHandler(component, expression, e, extraVars);

      if (modifiers.includes('once')) {
        document.removeEventListener(event, handler, options);
      }
    };
  } else {
    listenerTarget = modifiers.includes('window') ? window : modifiers.includes('document') ? document : el;

    handler = e => {
      // Remove this global event handler if the element that declared it
      // has been removed. It's now stale.
      if (listenerTarget === window || listenerTarget === document) {
        if (!document.body.contains(el)) {
          listenerTarget.removeEventListener(event, handler, options);
          return;
        }
      }

      if (isKeyEvent(event)) {
        if (isListeningForASpecificKeyThatHasntBeenPressed(e, modifiers)) {
          return;
        }
      }

      if (modifiers.includes('prevent')) e.preventDefault();
      if (modifiers.includes('stop')) e.stopPropagation(); // If the .self modifier isn't present, or if it is present and
      // the target element matches the element we are registering the
      // event on, run the handler

      if (!modifiers.includes('self') || e.target === el) {
        const returnValue = runListenerHandler(component, expression, e, extraVars);
        returnValue.then(value => {
          if (value === false) {
            e.preventDefault();
          } else {
            if (modifiers.includes('once')) {
              listenerTarget.removeEventListener(event, handler, options);
            }
          }
        });
      }
    };
  } // if expression adds commands to jembeClient
  // then execute jembeClient comands and refresh page


  handler = ((component, func) => {
    return e => {
      component.$jmb.callsCommands = false;
      func(e);

      if (component.$jmb.callsCommands === true) {
        component.$jmb.executeCommands();
      }
    };
  })(component, handler);

  if (modifiers.includes('debounce')) {
    let nextModifier = modifiers[modifiers.indexOf('debounce') + 1] || 'invalid-wait';
    let wait = (0, _utils.isNumeric)(nextModifier.split('ms')[0]) ? Number(nextModifier.split('ms')[0]) : 250;
    handler = (0, _utils.debounce)(handler, wait, this);
  } // register listener so it can be removed when morphing dom


  if (el.__jmb_listeners === undefined) {
    el.__jmb_listeners = [];
  }

  el.__jmb_listeners.push([event, handler, options]);

  listenerTarget.addEventListener(event, handler, options);
}

function runListenerHandler(component, expression, e, extraVars) {
  return component.evaluateCommandExpression(e.target, expression, () => {
    return { ...extraVars(),
      '$event': e
    };
  });
}

function isKeyEvent(event) {
  return ['keydown', 'keyup'].includes(event);
}

function isListeningForASpecificKeyThatHasntBeenPressed(e, modifiers) {
  let keyModifiers = modifiers.filter(i => {
    return !['window', 'document', 'prevent', 'stop'].includes(i);
  });

  if (keyModifiers.includes('debounce')) {
    let debounceIndex = keyModifiers.indexOf('debounce');
    keyModifiers.splice(debounceIndex, (0, _utils.isNumeric)((keyModifiers[debounceIndex + 1] || 'invalid-wait').split('ms')[0]) ? 2 : 1);
  } // If no modifier is specified, we'll call it a press.


  if (keyModifiers.length === 0) return false; // If one is passed, AND it matches the key pressed, we'll call it a press.

  if (keyModifiers.length === 1 && keyModifiers[0] === keyToModifier(e.key)) return false; // The user is listening for key combinations.

  const systemKeyModifiers = ['ctrl', 'shift', 'alt', 'meta', 'cmd', 'super'];
  const selectedSystemKeyModifiers = systemKeyModifiers.filter(modifier => keyModifiers.includes(modifier));
  keyModifiers = keyModifiers.filter(i => !selectedSystemKeyModifiers.includes(i));

  if (selectedSystemKeyModifiers.length > 0) {
    const activelyPressedKeyModifiers = selectedSystemKeyModifiers.filter(modifier => {
      // Alias "cmd" and "super" to "meta"
      if (modifier === 'cmd' || modifier === 'super') modifier = 'meta';
      return e[`${modifier}Key`];
    }); // If all the modifiers selected are pressed, ...

    if (activelyPressedKeyModifiers.length === selectedSystemKeyModifiers.length) {
      // AND the remaining key is pressed as well. It's a press.
      if (keyModifiers[0] === keyToModifier(e.key)) return false;
    }
  } // We'll call it NOT a valid keypress.


  return true;
}

function keyToModifier(key) {
  switch (key) {
    case '/':
      return 'slash';

    case ' ':
    case 'Spacebar':
      return 'space';

    default:
      return key && (0, _utils.kebabCase)(key);
  }
}
},{"../utils":"componentApi/utils.js"}],"componentApi/directives/model.js":[function(require,module,exports) {
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.registerModelListener = registerModelListener;

var _on = require("./on");

var _utils = require("../utils");

function registerModelListener(component, el, modifiers, expression, extraVars) {
  // If the element we are binding to is a select, a radio, or checkbox
  // we'll listen for the change event instead of the "input" event.
  var event = el.tagName.toLowerCase() === 'select' || ['checkbox', 'radio'].includes(el.type) || modifiers.includes('lazy') ? 'change' : 'input';
  const listenerExpression = `${expression} = rightSideOfExpression($event, ${expression})`;
  (0, _on.registerListener)(component, el, event, modifiers, listenerExpression, () => {
    return { ...extraVars(),
      rightSideOfExpression: generateModelAssignmentFunction(el, modifiers, expression)
    };
  });
}

function generateModelAssignmentFunction(el, modifiers, expression) {
  if (el.type === 'radio') {
    // Radio buttons only work properly when they share a name attribute.
    // People might assume we take care of that for them, because
    // they already set a shared "jmb-model" attribute.
    if (!el.hasAttribute('name')) el.setAttribute('name', expression);
  }

  return (event, currentValue) => {
    // Check for event.detail due to an issue where IE11 handles other events as a CustomEvent.
    if (event instanceof CustomEvent && event.detail) {
      return event.detail;
    } else if (el.type === 'checkbox') {
      // If the data we are binding to is an array, toggle its value inside the array.
      if (Array.isArray(currentValue)) {
        const newValue = modifiers.includes('number') ? safeParseNumber(event.target.value) : event.target.value;
        return event.target.checked ? currentValue.concat([newValue]) : currentValue.filter(el => !(0, _utils.checkedAttrLooseCompare)(el, newValue));
      } else {
        return event.target.checked;
      }
    } else if (el.tagName.toLowerCase() === 'select' && el.multiple) {
      return modifiers.includes('number') ? Array.from(event.target.selectedOptions).map(option => {
        const rawValue = option.value || option.text;
        return safeParseNumber(rawValue);
      }) : Array.from(event.target.selectedOptions).map(option => {
        return option.value || option.text;
      });
    } else {
      const rawValue = event.target.value;
      return modifiers.includes('number') ? safeParseNumber(rawValue) : modifiers.includes('trim') ? rawValue.trim() : rawValue;
    }
  };
}

function safeParseNumber(rawValue) {
  const number = rawValue ? parseFloat(rawValue) : null;
  return (0, _utils.isNumeric)(number) ? number : rawValue;
}
},{"./on":"componentApi/directives/on.js","../utils":"componentApi/utils.js"}],"../../../node_modules/observable-membrane/dist/modules/observable-membrane.js":[function(require,module,exports) {
var global = arguments[3];
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;

/**
 * Copyright (C) 2017 salesforce.com, inc.
 */
const {
  isArray
} = Array;
const {
  getPrototypeOf,
  create: ObjectCreate,
  defineProperty: ObjectDefineProperty,
  defineProperties: ObjectDefineProperties,
  isExtensible,
  getOwnPropertyDescriptor,
  getOwnPropertyNames,
  getOwnPropertySymbols,
  preventExtensions,
  hasOwnProperty
} = Object;
const {
  push: ArrayPush,
  concat: ArrayConcat,
  map: ArrayMap
} = Array.prototype;
const OtS = {}.toString;

function toString(obj) {
  if (obj && obj.toString) {
    return obj.toString();
  } else if (typeof obj === 'object') {
    return OtS.call(obj);
  } else {
    return obj + '';
  }
}

function isUndefined(obj) {
  return obj === undefined;
}

function isFunction(obj) {
  return typeof obj === 'function';
}

const proxyToValueMap = new WeakMap();

function registerProxy(proxy, value) {
  proxyToValueMap.set(proxy, value);
}

const unwrap = replicaOrAny => proxyToValueMap.get(replicaOrAny) || replicaOrAny;

class BaseProxyHandler {
  constructor(membrane, value) {
    this.originalTarget = value;
    this.membrane = membrane;
  } // Shared utility methods


  wrapDescriptor(descriptor) {
    if (hasOwnProperty.call(descriptor, 'value')) {
      descriptor.value = this.wrapValue(descriptor.value);
    } else {
      const {
        set: originalSet,
        get: originalGet
      } = descriptor;

      if (!isUndefined(originalGet)) {
        descriptor.get = this.wrapGetter(originalGet);
      }

      if (!isUndefined(originalSet)) {
        descriptor.set = this.wrapSetter(originalSet);
      }
    }

    return descriptor;
  }

  copyDescriptorIntoShadowTarget(shadowTarget, key) {
    const {
      originalTarget
    } = this; // Note: a property might get defined multiple times in the shadowTarget
    //       but it will always be compatible with the previous descriptor
    //       to preserve the object invariants, which makes these lines safe.

    const originalDescriptor = getOwnPropertyDescriptor(originalTarget, key);

    if (!isUndefined(originalDescriptor)) {
      const wrappedDesc = this.wrapDescriptor(originalDescriptor);
      ObjectDefineProperty(shadowTarget, key, wrappedDesc);
    }
  }

  lockShadowTarget(shadowTarget) {
    const {
      originalTarget
    } = this;
    const targetKeys = ArrayConcat.call(getOwnPropertyNames(originalTarget), getOwnPropertySymbols(originalTarget));
    targetKeys.forEach(key => {
      this.copyDescriptorIntoShadowTarget(shadowTarget, key);
    });
    const {
      membrane: {
        tagPropertyKey
      }
    } = this;

    if (!isUndefined(tagPropertyKey) && !hasOwnProperty.call(shadowTarget, tagPropertyKey)) {
      ObjectDefineProperty(shadowTarget, tagPropertyKey, ObjectCreate(null));
    }

    preventExtensions(shadowTarget);
  } // Shared Traps


  apply(shadowTarget, thisArg, argArray) {
    /* No op */
  }

  construct(shadowTarget, argArray, newTarget) {
    /* No op */
  }

  get(shadowTarget, key) {
    const {
      originalTarget,
      membrane: {
        valueObserved
      }
    } = this;
    const value = originalTarget[key];
    valueObserved(originalTarget, key);
    return this.wrapValue(value);
  }

  has(shadowTarget, key) {
    const {
      originalTarget,
      membrane: {
        tagPropertyKey,
        valueObserved
      }
    } = this;
    valueObserved(originalTarget, key); // since key is never going to be undefined, and tagPropertyKey might be undefined
    // we can simply compare them as the second part of the condition.

    return key in originalTarget || key === tagPropertyKey;
  }

  ownKeys(shadowTarget) {
    const {
      originalTarget,
      membrane: {
        tagPropertyKey
      }
    } = this; // if the membrane tag key exists and it is not in the original target, we add it to the keys.

    const keys = isUndefined(tagPropertyKey) || hasOwnProperty.call(originalTarget, tagPropertyKey) ? [] : [tagPropertyKey]; // small perf optimization using push instead of concat to avoid creating an extra array

    ArrayPush.apply(keys, getOwnPropertyNames(originalTarget));
    ArrayPush.apply(keys, getOwnPropertySymbols(originalTarget));
    return keys;
  }

  isExtensible(shadowTarget) {
    const {
      originalTarget
    } = this; // optimization to avoid attempting to lock down the shadowTarget multiple times

    if (!isExtensible(shadowTarget)) {
      return false; // was already locked down
    }

    if (!isExtensible(originalTarget)) {
      this.lockShadowTarget(shadowTarget);
      return false;
    }

    return true;
  }

  getPrototypeOf(shadowTarget) {
    const {
      originalTarget
    } = this;
    return getPrototypeOf(originalTarget);
  }

  getOwnPropertyDescriptor(shadowTarget, key) {
    const {
      originalTarget,
      membrane: {
        valueObserved,
        tagPropertyKey
      }
    } = this; // keys looked up via getOwnPropertyDescriptor need to be reactive

    valueObserved(originalTarget, key);
    let desc = getOwnPropertyDescriptor(originalTarget, key);

    if (isUndefined(desc)) {
      if (key !== tagPropertyKey) {
        return undefined;
      } // if the key is the membrane tag key, and is not in the original target,
      // we produce a synthetic descriptor and install it on the shadow target


      desc = {
        value: undefined,
        writable: false,
        configurable: false,
        enumerable: false
      };
      ObjectDefineProperty(shadowTarget, tagPropertyKey, desc);
      return desc;
    }

    if (desc.configurable === false) {
      // updating the descriptor to non-configurable on the shadow
      this.copyDescriptorIntoShadowTarget(shadowTarget, key);
    } // Note: by accessing the descriptor, the key is marked as observed
    // but access to the value, setter or getter (if available) cannot observe
    // mutations, just like regular methods, in which case we just do nothing.


    return this.wrapDescriptor(desc);
  }

}

const getterMap = new WeakMap();
const setterMap = new WeakMap();
const reverseGetterMap = new WeakMap();
const reverseSetterMap = new WeakMap();

class ReactiveProxyHandler extends BaseProxyHandler {
  wrapValue(value) {
    return this.membrane.getProxy(value);
  }

  wrapGetter(originalGet) {
    const wrappedGetter = getterMap.get(originalGet);

    if (!isUndefined(wrappedGetter)) {
      return wrappedGetter;
    }

    const handler = this;

    const get = function () {
      // invoking the original getter with the original target
      return handler.wrapValue(originalGet.call(unwrap(this)));
    };

    getterMap.set(originalGet, get);
    reverseGetterMap.set(get, originalGet);
    return get;
  }

  wrapSetter(originalSet) {
    const wrappedSetter = setterMap.get(originalSet);

    if (!isUndefined(wrappedSetter)) {
      return wrappedSetter;
    }

    const set = function (v) {
      // invoking the original setter with the original target
      originalSet.call(unwrap(this), unwrap(v));
    };

    setterMap.set(originalSet, set);
    reverseSetterMap.set(set, originalSet);
    return set;
  }

  unwrapDescriptor(descriptor) {
    if (hasOwnProperty.call(descriptor, 'value')) {
      // dealing with a data descriptor
      descriptor.value = unwrap(descriptor.value);
    } else {
      const {
        set,
        get
      } = descriptor;

      if (!isUndefined(get)) {
        descriptor.get = this.unwrapGetter(get);
      }

      if (!isUndefined(set)) {
        descriptor.set = this.unwrapSetter(set);
      }
    }

    return descriptor;
  }

  unwrapGetter(redGet) {
    const reverseGetter = reverseGetterMap.get(redGet);

    if (!isUndefined(reverseGetter)) {
      return reverseGetter;
    }

    const handler = this;

    const get = function () {
      // invoking the red getter with the proxy of this
      return unwrap(redGet.call(handler.wrapValue(this)));
    };

    getterMap.set(get, redGet);
    reverseGetterMap.set(redGet, get);
    return get;
  }

  unwrapSetter(redSet) {
    const reverseSetter = reverseSetterMap.get(redSet);

    if (!isUndefined(reverseSetter)) {
      return reverseSetter;
    }

    const handler = this;

    const set = function (v) {
      // invoking the red setter with the proxy of this
      redSet.call(handler.wrapValue(this), handler.wrapValue(v));
    };

    setterMap.set(set, redSet);
    reverseSetterMap.set(redSet, set);
    return set;
  }

  set(shadowTarget, key, value) {
    const {
      originalTarget,
      membrane: {
        valueMutated
      }
    } = this;
    const oldValue = originalTarget[key];

    if (oldValue !== value) {
      originalTarget[key] = value;
      valueMutated(originalTarget, key);
    } else if (key === 'length' && isArray(originalTarget)) {
      // fix for issue #236: push will add the new index, and by the time length
      // is updated, the internal length is already equal to the new length value
      // therefore, the oldValue is equal to the value. This is the forking logic
      // to support this use case.
      valueMutated(originalTarget, key);
    }

    return true;
  }

  deleteProperty(shadowTarget, key) {
    const {
      originalTarget,
      membrane: {
        valueMutated
      }
    } = this;
    delete originalTarget[key];
    valueMutated(originalTarget, key);
    return true;
  }

  setPrototypeOf(shadowTarget, prototype) {
    if ("development" !== 'production') {
      throw new Error(`Invalid setPrototypeOf invocation for reactive proxy ${toString(this.originalTarget)}. Prototype of reactive objects cannot be changed.`);
    }
  }

  preventExtensions(shadowTarget) {
    if (isExtensible(shadowTarget)) {
      const {
        originalTarget
      } = this;
      preventExtensions(originalTarget); // if the originalTarget is a proxy itself, it might reject
      // the preventExtension call, in which case we should not attempt to lock down
      // the shadow target.

      if (isExtensible(originalTarget)) {
        return false;
      }

      this.lockShadowTarget(shadowTarget);
    }

    return true;
  }

  defineProperty(shadowTarget, key, descriptor) {
    const {
      originalTarget,
      membrane: {
        valueMutated,
        tagPropertyKey
      }
    } = this;

    if (key === tagPropertyKey && !hasOwnProperty.call(originalTarget, key)) {
      // To avoid leaking the membrane tag property into the original target, we must
      // be sure that the original target doesn't have yet.
      // NOTE: we do not return false here because Object.freeze and equivalent operations
      // will attempt to set the descriptor to the same value, and expect no to throw. This
      // is an small compromise for the sake of not having to diff the descriptors.
      return true;
    }

    ObjectDefineProperty(originalTarget, key, this.unwrapDescriptor(descriptor)); // intentionally testing if false since it could be undefined as well

    if (descriptor.configurable === false) {
      this.copyDescriptorIntoShadowTarget(shadowTarget, key);
    }

    valueMutated(originalTarget, key);
    return true;
  }

}

const getterMap$1 = new WeakMap();
const setterMap$1 = new WeakMap();

class ReadOnlyHandler extends BaseProxyHandler {
  wrapValue(value) {
    return this.membrane.getReadOnlyProxy(value);
  }

  wrapGetter(originalGet) {
    const wrappedGetter = getterMap$1.get(originalGet);

    if (!isUndefined(wrappedGetter)) {
      return wrappedGetter;
    }

    const handler = this;

    const get = function () {
      // invoking the original getter with the original target
      return handler.wrapValue(originalGet.call(unwrap(this)));
    };

    getterMap$1.set(originalGet, get);
    return get;
  }

  wrapSetter(originalSet) {
    const wrappedSetter = setterMap$1.get(originalSet);

    if (!isUndefined(wrappedSetter)) {
      return wrappedSetter;
    }

    const handler = this;

    const set = function (v) {
      if ("development" !== 'production') {
        const {
          originalTarget
        } = handler;
        throw new Error(`Invalid mutation: Cannot invoke a setter on "${originalTarget}". "${originalTarget}" is read-only.`);
      }
    };

    setterMap$1.set(originalSet, set);
    return set;
  }

  set(shadowTarget, key, value) {
    if ("development" !== 'production') {
      const {
        originalTarget
      } = this;
      throw new Error(`Invalid mutation: Cannot set "${key.toString()}" on "${originalTarget}". "${originalTarget}" is read-only.`);
    }

    return false;
  }

  deleteProperty(shadowTarget, key) {
    if ("development" !== 'production') {
      const {
        originalTarget
      } = this;
      throw new Error(`Invalid mutation: Cannot delete "${key.toString()}" on "${originalTarget}". "${originalTarget}" is read-only.`);
    }

    return false;
  }

  setPrototypeOf(shadowTarget, prototype) {
    if ("development" !== 'production') {
      const {
        originalTarget
      } = this;
      throw new Error(`Invalid prototype mutation: Cannot set prototype on "${originalTarget}". "${originalTarget}" prototype is read-only.`);
    }
  }

  preventExtensions(shadowTarget) {
    if ("development" !== 'production') {
      const {
        originalTarget
      } = this;
      throw new Error(`Invalid mutation: Cannot preventExtensions on ${originalTarget}". "${originalTarget} is read-only.`);
    }

    return false;
  }

  defineProperty(shadowTarget, key, descriptor) {
    if ("development" !== 'production') {
      const {
        originalTarget
      } = this;
      throw new Error(`Invalid mutation: Cannot defineProperty "${key.toString()}" on "${originalTarget}". "${originalTarget}" is read-only.`);
    }

    return false;
  }

}

function extract(objectOrArray) {
  if (isArray(objectOrArray)) {
    return objectOrArray.map(item => {
      const original = unwrap(item);

      if (original !== item) {
        return extract(original);
      }

      return item;
    });
  }

  const obj = ObjectCreate(getPrototypeOf(objectOrArray));
  const names = getOwnPropertyNames(objectOrArray);
  return ArrayConcat.call(names, getOwnPropertySymbols(objectOrArray)).reduce((seed, key) => {
    const item = objectOrArray[key];
    const original = unwrap(item);

    if (original !== item) {
      seed[key] = extract(original);
    } else {
      seed[key] = item;
    }

    return seed;
  }, obj);
}

const formatter = {
  header: plainOrProxy => {
    const originalTarget = unwrap(plainOrProxy); // if originalTarget is falsy or not unwrappable, exit

    if (!originalTarget || originalTarget === plainOrProxy) {
      return null;
    }

    const obj = extract(plainOrProxy);
    return ['object', {
      object: obj
    }];
  },
  hasBody: () => {
    return false;
  },
  body: () => {
    return null;
  }
}; // Inspired from paulmillr/es6-shim
// https://github.com/paulmillr/es6-shim/blob/master/es6-shim.js#L176-L185

function getGlobal() {
  // the only reliable means to get the global object is `Function('return this')()`
  // However, this causes CSP violations in Chrome apps.
  if (typeof globalThis !== 'undefined') {
    return globalThis;
  }

  if (typeof self !== 'undefined') {
    return self;
  }

  if (typeof window !== 'undefined') {
    return window;
  }

  if (typeof global !== 'undefined') {
    return global;
  } // Gracefully degrade if not able to locate the global object


  return {};
}

function init() {
  if ("development" === 'production') {
    // this method should never leak to prod
    throw new ReferenceError();
  }

  const global = getGlobal(); // Custom Formatter for Dev Tools. To enable this, open Chrome Dev Tools
  //  - Go to Settings,
  //  - Under console, select "Enable custom formatters"
  // For more information, https://docs.google.com/document/d/1FTascZXT9cxfetuPRT2eXPQKXui4nWFivUnS_335T3U/preview

  const devtoolsFormatters = global.devtoolsFormatters || [];
  ArrayPush.call(devtoolsFormatters, formatter);
  global.devtoolsFormatters = devtoolsFormatters;
}

if ("development" !== 'production') {
  init();
}

const ObjectDotPrototype = Object.prototype;

function defaultValueIsObservable(value) {
  // intentionally checking for null
  if (value === null) {
    return false;
  } // treat all non-object types, including undefined, as non-observable values


  if (typeof value !== 'object') {
    return false;
  }

  if (isArray(value)) {
    return true;
  }

  const proto = getPrototypeOf(value);
  return proto === ObjectDotPrototype || proto === null || getPrototypeOf(proto) === null;
}

const defaultValueObserved = (obj, key) => {
  /* do nothing */
};

const defaultValueMutated = (obj, key) => {
  /* do nothing */
};

const defaultValueDistortion = value => value;

function createShadowTarget(value) {
  return isArray(value) ? [] : {};
}

class ReactiveMembrane {
  constructor(options) {
    this.valueDistortion = defaultValueDistortion;
    this.valueMutated = defaultValueMutated;
    this.valueObserved = defaultValueObserved;
    this.valueIsObservable = defaultValueIsObservable;
    this.objectGraph = new WeakMap();

    if (!isUndefined(options)) {
      const {
        valueDistortion,
        valueMutated,
        valueObserved,
        valueIsObservable,
        tagPropertyKey
      } = options;
      this.valueDistortion = isFunction(valueDistortion) ? valueDistortion : defaultValueDistortion;
      this.valueMutated = isFunction(valueMutated) ? valueMutated : defaultValueMutated;
      this.valueObserved = isFunction(valueObserved) ? valueObserved : defaultValueObserved;
      this.valueIsObservable = isFunction(valueIsObservable) ? valueIsObservable : defaultValueIsObservable;
      this.tagPropertyKey = tagPropertyKey;
    }
  }

  getProxy(value) {
    const unwrappedValue = unwrap(value);
    const distorted = this.valueDistortion(unwrappedValue);

    if (this.valueIsObservable(distorted)) {
      const o = this.getReactiveState(unwrappedValue, distorted); // when trying to extract the writable version of a readonly
      // we return the readonly.

      return o.readOnly === value ? value : o.reactive;
    }

    return distorted;
  }

  getReadOnlyProxy(value) {
    value = unwrap(value);
    const distorted = this.valueDistortion(value);

    if (this.valueIsObservable(distorted)) {
      return this.getReactiveState(value, distorted).readOnly;
    }

    return distorted;
  }

  unwrapProxy(p) {
    return unwrap(p);
  }

  getReactiveState(value, distortedValue) {
    const {
      objectGraph
    } = this;
    let reactiveState = objectGraph.get(distortedValue);

    if (reactiveState) {
      return reactiveState;
    }

    const membrane = this;
    reactiveState = {
      get reactive() {
        const reactiveHandler = new ReactiveProxyHandler(membrane, distortedValue); // caching the reactive proxy after the first time it is accessed

        const proxy = new Proxy(createShadowTarget(distortedValue), reactiveHandler);
        registerProxy(proxy, value);
        ObjectDefineProperty(this, 'reactive', {
          value: proxy
        });
        return proxy;
      },

      get readOnly() {
        const readOnlyHandler = new ReadOnlyHandler(membrane, distortedValue); // caching the readOnly proxy after the first time it is accessed

        const proxy = new Proxy(createShadowTarget(distortedValue), readOnlyHandler);
        registerProxy(proxy, value);
        ObjectDefineProperty(this, 'readOnly', {
          value: proxy
        });
        return proxy;
      }

    };
    objectGraph.set(distortedValue, reactiveState);
    return reactiveState;
  }

}

var _default = ReactiveMembrane;
/** version: 1.0.0 */

exports.default = _default;
},{}],"componentApi/observable.js":[function(require,module,exports) {
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.wrap = wrap;
exports.unwrap = unwrap;

var _observableMembrane = _interopRequireDefault(require("observable-membrane"));

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

function wrap(data, mutationCallback) {
  /* IE11-ONLY:START */
  return wrapForIe11(data, mutationCallback);
  /* IE11-ONLY:END */

  let membrane = new _observableMembrane.default({
    valueMutated(target, key) {
      mutationCallback(target, key);
    }

  });
  return {
    data: membrane.getProxy(data),
    membrane: membrane
  };
}

function unwrap(membrane, observable) {
  let unwrappedData = membrane.unwrapProxy(observable);
  let copy = {};
  Object.keys(unwrappedData).forEach(key => {
    if (['$el', '$refs', '$nextTick', '$watch', '$jmb'].includes(key)) return;
    copy[key] = unwrappedData[key];
  });
  return copy;
}

function wrapForIe11(data, mutationCallback) {
  const proxyHandler = {
    set(target, key, value) {
      // Set the value converting it to a "Deep Proxy" when required
      // Note that if a project is not a valid object, it won't be converted to a proxy
      const setWasSuccessful = Reflect.set(target, key, deepProxy(value, proxyHandler));
      mutationCallback(target, key);
      return setWasSuccessful;
    },

    get(target, key) {
      // Provide a way to determine if this object is an Alpine proxy or not.
      if (key === "$isAlpineProxy") return true; // Just return the flippin' value. Gawsh.

      return target[key];
    }

  };
  return {
    data: deepProxy(data, proxyHandler),
    membrane: {
      unwrapProxy(proxy) {
        return proxy;
      }

    }
  };
}

function deepProxy(target, proxyHandler) {
  // If target is null, return it.
  if (target === null) return target; // If target is not an object, return it.

  if (typeof target !== 'object') return target; // If target is a DOM node (like in the case of this.$el), return it.

  if (target instanceof Node) return target; // If target is already an Alpine proxy, return it.

  if (target['$isAlpineProxy']) return target; // Otherwise proxy the properties recursively.
  // This enables reactivity on setting nested data.
  // Note that if a project is not a valid object, it won't be converted to a proxy

  for (let property in target) {
    target[property] = deepProxy(target[property], proxyHandler);
  }

  return new Proxy(target, proxyHandler);
}
},{"observable-membrane":"../../../node_modules/observable-membrane/dist/modules/observable-membrane.js"}],"../../../node_modules/process/browser.js":[function(require,module,exports) {

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

},{"process":"../../../node_modules/process/browser.js"}],"componentApi/magic/jmb.js":[function(require,module,exports) {
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;

var _path = require("path");

class JMB {
  constructor(jembeClient, execName) {
    this.jembeClient = jembeClient;
    this.execName = execName;
    this.callsCommands = false;
  }

  call(actionName, ...params) {
    this.callsCommands = true;
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
    this.callsCommands = true;

    if (value instanceof FileList || value instanceof File) {
      this.jembeClient.addFilesForUpload(this.execName, stateName, value);
    } else {
      let params = {};
      params[stateName] = value;
      this.jembeClient.addInitialiseCommand(this.execName, params);
    }
  }

  emit(eventName, kwargs = {}, to = null) {
    this.callsCommands = true;
    this.jembeClient.addEmitCommand(this.execName, eventName, kwargs, to);
  }

  component(relativeExecName, kwargs = {}) {
    this.callsCommands = true;
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

    return new JMB(this.jembeClient, execName);
  }

  init(relativeExecName, kwargs = {}) {
    return this.component(relativeExecName, kwargs);
  }

  executeCommands() {
    this.jembeClient.consolidateCommands();
    this.jembeClient.executeCommands();
  }

}

exports.default = JMB;
},{"path":"../../../node_modules/node-libs-browser/node_modules/path-browserify/index.js"}],"componentApi/component.js":[function(require,module,exports) {
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;

var _utils = require("./utils");

var _for = require("./directives/for");

var _bind = require("./directives/bind");

var _text = require("./directives/text");

var _html = require("./directives/html");

var _show = require("./directives/show");

var _if = require("./directives/if");

var _model = require("./directives/model");

var _on = require("./directives/on");

var _observable = require("./observable");

var _jmb = _interopRequireDefault(require("./magic/jmb"));

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

/**
 * Havily modified alpine.js 2.8.1 to:
 *  - user 'jmb-' instead 'x-' as prefix
 *  - jembe component becomes alpine component
 *  - jembe compoenent state params and actions becomes alpine x-data params and actions
 *  - when jembe state params are changed or action is called in x-data,
 *     call appropriate function on jembeclient
 *  - support local variables accessible only in alpine componetn with jmb-local,
 *    jmb-init, jmb-update directives
 *  - alpine/copmonentapi local variables are accessible with $local prefix
 *  - $node references current node on witch action is executed (jmb-on etc.)
 *  - add $jmb magic variable to reference jembeClient.component(this) to access set, cal display emit and init commands
 *  - when componentApi action changes any state variable are call any jembe action jembeClient.executeCommands() will be called
 *    if there is not defer modifier
 *  
 * modification are enclosed with @jembeModification
 */
// import Alpine from './index'
class Component {
  // @jembeModification
  // constructor is separated in constructor + mount and havily modified to support
  // jembeComponents
  // mount do actual initialisation of component cunstructor don't do anything
  constructor(el) {
    this.$el = el;
    this.mounted = false;
    this.jembeClient = undefined;
    this.execName = undefined;
    this.state = undefined;
    this.actions = undefined;
  }
  /**
   * @param {Component} originalComponent 
   */


  mount(jembeClient, execName, state, actions, originalComponent = undefined) {
    if (this.mounted && (this.jembeClient !== jembeClient || this.execName !== execName)) {
      throw `Mounting ComponetApi for new component: ${this.execName} -> ${execName}`;
    } else {
      this.mounted = true;
      this.jembeClient = jembeClient;
      this.execName = execName;
      this.$jmb = new _jmb.default(this.jembeClient, this.execName);
    }

    this.state = state;
    this.actions = actions;

    for (const stateName of Object.keys(this.state)) {
      if (this.actions.includes(stateName)) {
        console.warn(`state param '${stateName}' overrides action with same name in component ${this.execName}!`);
      }
    }

    const localAttr = this.$el.getAttribute('jmb-local');
    const localExpression = localAttr === '' ? '{}' : localAttr;
    const initExpression = this.$el.getAttribute('jmb-init');
    const updateExpression = this.$el.getAttribute('jmb-update');
    let dataExtras = {
      $el: this.$el,
      $jmb: this.$jmb
    };
    let canonicalComponentElementReference = this.$el; // Object.entries(Alpine.magicProperties).forEach(([name, callback]) => {
    //     Object.defineProperty(dataExtras, `$${name}`, { get: function () { return callback(canonicalComponentElementReference) } });
    // })

    this.unobservedData = {
      $local: originalComponent === undefined ? (0, _utils.saferEval)(this.$el, localExpression, dataExtras) : originalComponent.getUnobservedData()['$local']
    }; // add actions

    Object.keys(this.actions).forEach(([actionName]) => {
      Object.defineProperty(this.unobservedData, `$${actionName}`, {
        get: function () {
          return (...params) => {
            this.$jmb.call(actionName, ...params);
          };
        }
      });
    }); // add states

    Object.entries(this.state).forEach(([name, value]) => {
      this.unobservedData[name] = value;
    }); // TODO add watcher to state data and fire init commands accoringly

    /* IE11-ONLY:START */
    // For IE11, add our magic properties to the original data for access.
    // The Proxy polyfill does not allow properties to be added after creation.

    this.unobservedData.$el = null;
    this.unobservedData.$refs = null;
    this.unobservedData.$nextTick = null;
    this.unobservedData.$watch = null;
    this.unobservedData.$jmb = null; // The IE build uses a proxy polyfill which doesn't allow properties
    // to be defined after the proxy object is created so,
    // for IE only, we need to define our helpers earlier.
    // Object.entries(Alpine.magicProperties).forEach(([name, callback]) => {
    //     Object.defineProperty(this.unobservedData, `$${name}`, { get: function () { return callback(canonicalComponentElementReference, this.$el) } });
    // })

    /* IE11-ONLY:END */
    // Construct a Proxy-based observable. This will be used to handle reactivity.

    let {
      membrane,
      data
    } = this.wrapDataInObservable(this.unobservedData);
    this.$data = data;
    this.membrane = membrane; // After making user-supplied data methods reactive, we can now add
    // our magic properties to the original data for access.

    this.unobservedData.$el = this.$el;
    this.unobservedData.$refs = this.getRefsProxy();
    this.unobservedData.$jmb = this.$jmb;
    this.nextTickStack = [];

    this.unobservedData.$nextTick = callback => {
      this.nextTickStack.push(callback);
    };

    this.watchers = {};

    this.unobservedData.$watch = (property, callback) => {
      if (!this.watchers[property]) this.watchers[property] = [];
      this.watchers[property].push(callback);
    };
    /* MODERN-ONLY:START */
    // We remove this piece of code from the legacy build.
    // In IE11, we have already defined our helpers at this point.
    // Register custom magic properties.
    // Object.entries(Alpine.magicProperties).forEach(([name, callback]) => {
    //     Object.defineProperty(this.unobservedData, `$${name}`, { get: function () { return callback(canonicalComponentElementReference, this.$el) } });
    // })

    /* MODERN-ONLY:END */


    this.showDirectiveStack = [];
    this.showDirectiveLastElement; // Alpine.onBeforeComponentInitializeds.forEach(callback => callback(this))

    var initReturnedCallback; // If jmb-init is present AND we aren't cloning (skip jmb-init on clone)

    if (originalComponent === undefined && initExpression) {
      // We want to allow data manipulation, but not trigger DOM updates just yet.
      // We haven't even initialized the elements with their Alpine bindings. I mean c'mon.
      this.pauseReactivity = true;
      initReturnedCallback = this.evaluateReturnExpression(this.$el, initExpression);
      this.pauseReactivity = false;
    } else if (originalComponent !== undefined && updateExpression) {
      this.pauseReactivity = true;
      initReturnedCallback = this.evaluateReturnExpression(this.$el, updateExpression);
      this.pauseReactivity = false;
    } // Register all our listeners and set all our attribute bindings.
    // If we're cloning a component, the third parameter ensures no duplicate
    // event listeners are registered (the mutation observer will take care of them)
    //this.initializeElements(this.$el, () => { }, originalComponent === undefined)


    this.initializeElements(this.$el, () => {}, true); // Use mutation observer to detect new elements being added within this component at run-time.
    // Alpine's just so darn flexible amirite?

    this.listenForNewElementsToInitialize();

    if (typeof initReturnedCallback === 'function') {
      // Run the callback returned from the "jmb-init" hook to allow the user to do stuff after
      // Alpine's got it's grubby little paws all over everything.
      initReturnedCallback.call(this.$data);
    } // setTimeout(() => {
    //     Alpine.onComponentInitializeds.forEach(callback => callback(this))
    // }, 0)

  }

  unmount() {}

  getUnobservedData() {
    return (0, _observable.unwrap)(this.membrane, this.$data);
  }

  wrapDataInObservable(data) {
    var self = this;
    let updateDom = (0, _utils.debounce)(function () {
      self.updateElements(self.$el);
    }, 0);
    return (0, _observable.wrap)(data, (target, key) => {
      if (self.watchers[key]) {
        // If there's a watcher for this specific key, run it.
        self.watchers[key].forEach(callback => callback(target[key]));
      } else if (Array.isArray(target)) {
        // Arrays are special cases, if any of the items change, we consider the array as mutated.
        Object.keys(self.watchers).forEach(fullDotNotationKey => {
          let dotNotationParts = fullDotNotationKey.split('.'); // Ignore length mutations since they would result in duplicate calls.
          // For example, when calling push, we would get a mutation for the item's key
          // and a second mutation for the length property.

          if (key === 'length') return;
          dotNotationParts.reduce((comparisonData, part) => {
            if (Object.is(target, comparisonData[part])) {
              self.watchers[fullDotNotationKey].forEach(callback => callback(target));
            }

            return comparisonData[part];
          }, self.unobservedData);
        });
      } else {
        // Let's walk through the watchers with "dot-notation" (foo.bar) and see
        // if this mutation fits any of them.
        Object.keys(self.watchers).filter(i => i.includes('.')).forEach(fullDotNotationKey => {
          let dotNotationParts = fullDotNotationKey.split('.'); // If this dot-notation watcher's last "part" doesn't match the current
          // key, then skip it early for performance reasons.

          if (key !== dotNotationParts[dotNotationParts.length - 1]) return; // Now, walk through the dot-notation "parts" recursively to find
          // a match, and call the watcher if one's found.

          dotNotationParts.reduce((comparisonData, part) => {
            if (Object.is(target, comparisonData)) {
              // Run the watchers.
              self.watchers[fullDotNotationKey].forEach(callback => callback(target[key]));
            }

            return comparisonData[part];
          }, self.unobservedData);
        });
      } // Don't react to data changes for cases like the `jmb-created` hook.


      if (self.pauseReactivity) return;
      updateDom();
    });
  }

  walkAndSkipNestedComponents(el, callback, initializeComponentCallback = () => {}) {
    (0, _utils.walk)(el, el => {
      // We've hit a component.
      if (el.hasAttribute('jmb-name') || el.hasAttribute('jmb-placeholder')) {
        // If it's not the current one.
        if (!el.isSameNode(this.$el)) {
          // Initialize it if it's not.
          if (!el.__jmb) initializeComponentCallback(el); // Now we'll let that sub-component deal with itself.

          return false;
        }
      }

      return callback(el);
    });
  }

  initializeElements(rootEl, extraVars = () => {}, shouldRegisterListeners = true) {
    this.walkAndSkipNestedComponents(rootEl, el => {
      // Don't touch spawns from for loop
      if (el.__jmb_for_key !== undefined) return false; // Don't touch spawns from if directives

      if (el.__jmb_inserted_me !== undefined) return false;
      this.initializeElement(el, extraVars, shouldRegisterListeners);
    }, el => {
      el.__jmb = new Component(el);
    });
    this.executeAndClearRemainingShowDirectiveStack();
    this.executeAndClearNextTickStack(rootEl);
  }

  initializeElement(el, extraVars, shouldRegisterListeners = true) {
    // To support class attribute merging, we have to know what the element's
    // original class attribute looked like for reference.
    if (el.hasAttribute('class') && (0, _utils.getXAttrs)(el, this).length > 0) {
      el.__jmb_original_classes = (0, _utils.convertClassStringToArray)(el.getAttribute('class'));
    }

    shouldRegisterListeners && this.registerListeners(el, extraVars);
    this.resolveBoundAttributes(el, true, extraVars);
  }

  updateElements(rootEl, extraVars = () => {}) {
    this.walkAndSkipNestedComponents(rootEl, el => {
      // Don't touch spawns from for loop (and check if the root is actually a for loop in a parent, don't skip it.)
      if (el.__jmb_for_key !== undefined && !el.isSameNode(this.$el)) return false;
      this.updateElement(el, extraVars);
    }, el => {
      el.__jmb = new Component(el);
    });
    this.executeAndClearRemainingShowDirectiveStack();
    this.executeAndClearNextTickStack(rootEl);
  }

  executeAndClearNextTickStack(el) {
    // Skip spawns from alpine directives
    if (el === this.$el && this.nextTickStack.length > 0) {
      // We run the tick stack after the next frame to allow any
      // running transitions to pass the initial show stage.
      requestAnimationFrame(() => {
        while (this.nextTickStack.length > 0) {
          this.nextTickStack.shift()();
        }
      });
    }
  }

  executeAndClearRemainingShowDirectiveStack() {
    // The goal here is to start all the jmb-show transitions
    // and build a nested promise chain so that elements
    // only hide when the children are finished hiding.
    this.showDirectiveStack.reverse().map(handler => {
      return new Promise((resolve, reject) => {
        handler(resolve, reject);
      });
    }).reduce((promiseChain, promise) => {
      return promiseChain.then(() => {
        return promise.then(finishElement => {
          finishElement();
        });
      });
    }, Promise.resolve(() => {})).catch(e => {
      if (e !== _utils.TRANSITION_CANCELLED) throw e;
    }); // We've processed the handler stack. let's clear it.

    this.showDirectiveStack = [];
    this.showDirectiveLastElement = undefined;
  }

  updateElement(el, extraVars) {
    this.resolveBoundAttributes(el, false, extraVars);
  }

  registerListeners(el, extraVars) {
    (0, _utils.getXAttrs)(el, this).forEach(({
      type,
      value,
      modifiers,
      expression
    }) => {
      switch (type) {
        case 'on':
          (0, _on.registerListener)(this, el, value, modifiers, expression, extraVars);
          break;

        case 'model':
          (0, _model.registerModelListener)(this, el, modifiers, expression, extraVars);
          break;

        default:
          break;
      }
    });
  }

  resolveBoundAttributes(el, initialUpdate = false, extraVars) {
    let attrs = (0, _utils.getXAttrs)(el, this);
    attrs.forEach(({
      type,
      value,
      modifiers,
      expression
    }) => {
      switch (type) {
        case 'model':
          (0, _bind.handleAttributeBindingDirective)(this, el, 'value', expression, extraVars, type, modifiers);
          break;

        case 'bind':
          // The :key binding on an jmb-for is special, ignore it.
          if (el.tagName.toLowerCase() === 'template' && value === 'key') return;
          (0, _bind.handleAttributeBindingDirective)(this, el, value, expression, extraVars, type, modifiers);
          break;

        case 'text':
          var output = this.evaluateReturnExpression(el, expression, extraVars);
          (0, _text.handleTextDirective)(el, output, expression);
          break;

        case 'html':
          (0, _html.handleHtmlDirective)(this, el, expression, extraVars);
          break;

        case 'show':
          var output = this.evaluateReturnExpression(el, expression, extraVars);
          (0, _show.handleShowDirective)(this, el, output, modifiers, initialUpdate);
          break;

        case 'if':
          // If this element also has jmb-for on it, don't process jmb-if.
          // We will let the "jmb-for" directive handle the "if"ing.
          if (attrs.some(i => i.type === 'for')) return;
          var output = this.evaluateReturnExpression(el, expression, extraVars);
          (0, _if.handleIfDirective)(this, el, output, initialUpdate, extraVars);
          break;

        case 'for':
          (0, _for.handleForDirective)(this, el, expression, initialUpdate, extraVars);
          break;

        case 'cloak':
          el.removeAttribute('jmb-cloak');
          break;

        default:
          break;
      }
    });
  }

  evaluateReturnExpression(el, expression, extraVars = () => {}) {
    return (0, _utils.saferEval)(el, expression, this.$data, { ...extraVars(),
      $dispatch: this.getDispatchFunction(el)
    });
  }

  evaluateCommandExpression(el, expression, extraVars = () => {}) {
    return (0, _utils.saferEvalNoReturn)(el, expression, this.$data, { ...extraVars(),
      $dispatch: this.getDispatchFunction(el)
    });
  }

  getDispatchFunction(el) {
    return (event, detail = {}) => {
      el.dispatchEvent(new CustomEvent(event, {
        detail,
        bubbles: true
      }));
    };
  }

  listenForNewElementsToInitialize() {
    const targetNode = this.$el;
    const observerOptions = {
      childList: true,
      attributes: true,
      subtree: true
    };
    const observer = new MutationObserver(mutations => {
      for (let i = 0; i < mutations.length; i++) {
        // Filter out mutations triggered from child components.
        const closestParentComponent = mutations[i].target.closest('[jmb-name]');
        if (!(closestParentComponent && closestParentComponent.isSameNode(this.$el))) continue;

        if (mutations[i].type === 'attributes' && mutations[i].attributeName === 'jmb-local') {// @jembeModification
          // do nothing jmb-local on subsequent update should be ignore and jmb-update shold be used
          // const xAttr = mutations[i].target.getAttribute('jmb-local') || '{}';
          // const rawData = saferEval(this.$el, xAttr, { $el: this.$el })
          // Object.keys(rawData).forEach(key => {
          //     if (this.$data[key] !== rawData[key]) {
          //         this.$data[key] = rawData[key]
          //     }
          // })
        }

        if (mutations[i].addedNodes.length > 0) {
          mutations[i].addedNodes.forEach(node => {
            if (node.nodeType !== 1 || node.__jmb_inserted_me) return; // @jembeModification
            // can only create component for jembe compoennt it ignores jmb-local on
            // other components
            // if (node.matches('[jmb-local]') && !node.__jmb) {
            //     node.__jmb = new Component(node)
            //     return
            // }

            this.initializeElements(node);
          });
        }
      }
    });
    observer.observe(targetNode, observerOptions);
  }

  getRefsProxy() {
    var self = this;
    var refObj = {};
    /* IE11-ONLY:START */
    // Add any properties up-front that might be necessary for the Proxy polyfill.

    refObj.$isRefsProxy = false;
    refObj.$isAlpineProxy = false; // If we are in IE, since the polyfill needs all properties to be defined before building the proxy,
    // we just loop on the element, look for any jmb-ref and create a tmp property on a fake object.

    this.walkAndSkipNestedComponents(self.$el, el => {
      if (el.hasAttribute('jmb-ref')) {
        refObj[el.getAttribute('jmb-ref')] = true;
      }
    });
    /* IE11-ONLY:END */
    // One of the goals of this is to not hold elements in memory, but rather re-evaluate
    // the DOM when the system needs something from it. This way, the framework is flexible and
    // friendly to outside DOM changes from libraries like Vue/Livewire.
    // For this reason, I'm using an "on-demand" proxy to fake a "$refs" object.

    return new Proxy(refObj, {
      get(object, property) {
        if (property === '$isAlpineProxy') return true;
        var ref; // We can't just query the DOM because it's hard to filter out refs in
        // nested components.

        self.walkAndSkipNestedComponents(self.$el, el => {
          if (el.hasAttribute('jmb-ref') && el.getAttribute('jmb-ref') === property) {
            ref = el;
          }
        });
        return ref;
      }

    });
  }

}

exports.default = Component;
},{"./utils":"componentApi/utils.js","./directives/for":"componentApi/directives/for.js","./directives/bind":"componentApi/directives/bind.js","./directives/text":"componentApi/directives/text.js","./directives/html":"componentApi/directives/html.js","./directives/show":"componentApi/directives/show.js","./directives/if":"componentApi/directives/if.js","./directives/model":"componentApi/directives/model.js","./directives/on":"componentApi/directives/on.js","./observable":"componentApi/observable.js","./magic/jmb":"componentApi/magic/jmb.js"}],"componentApi/index.js":[function(require,module,exports) {
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;

var _component = _interopRequireDefault(require("./component"));

var _utils = require("./utils");

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

class ComponentAPI extends _component.default {
  /**
   * @param {ComponentRef} componentRef 
   */
  constructor(componentRef) {
    super(componentRef.dom);
    this.jembeClient = componentRef.jembeClient;
    this.componentRef = componentRef;
    this.execName = componentRef.execName;
  }
  /**
   * @param {ComponentRef} originalComponentRef 
   */


  mount(originalComponentRef) {
    super.mount(this.componentRef.jembeClient, this.componentRef.execName, this.componentRef.state, this.componentRef.actions, originalComponentRef !== undefined && originalComponentRef.api !== null // TODO handle page component with diferent execName`s
    && originalComponentRef.execName === this.execName ? originalComponentRef.api : undefined);
  }

  unmount() {
    super.unmount();
  }

}

var _default = ComponentAPI; // const Alpine = {
//     version: process.env.PKG_VERSION,
//     pauseMutationObserver: false,
//     magicProperties: {},
//     onComponentInitializeds: [],
//     onBeforeComponentInitializeds: [],
//     ignoreFocusedForValueBinding: false,
//     start: async function () {
//         if (! isTesting()) {
//             await domReady()
//         }
//         this.discoverComponents(el => {
//             this.initializeComponent(el)
//         })
//         // It's easier and more performant to just support Turbolinks than listen
//         // to MutationObserver mutations at the document level.
//         document.addEventListener("turbolinks:load", () => {
//             this.discoverUninitializedComponents(el => {
//                 this.initializeComponent(el)
//             })
//         })
//         this.listenForNewUninitializedComponentsAtRunTime()
//     },
//     discoverComponents: function (callback) {
//         const rootEls = document.querySelectorAll('[x-data]');
//         rootEls.forEach(rootEl => {
//             callback(rootEl)
//         })
//     },
//     discoverUninitializedComponents: function (callback, el = null) {
//         const rootEls = (el || document).querySelectorAll('[jmb-data]');
//         Array.from(rootEls)
//             .filter(el => el.__jmb === undefined)
//             .forEach(rootEl => {
//                 callback(rootEl)
//             })
//     },
//     listenForNewUninitializedComponentsAtRunTime: function () {
//         const targetNode = document.querySelector('body');
//         const observerOptions = {
//             childList: true,
//             attributes: true,
//             subtree: true,
//         }
//         const observer = new MutationObserver((mutations) => {
//             if (this.pauseMutationObserver) return;
//             for (let i=0; i < mutations.length; i++){
//                 if (mutations[i].addedNodes.length > 0) {
//                     mutations[i].addedNodes.forEach(node => {
//                         // Discard non-element nodes (like line-breaks)
//                         if (node.nodeType !== 1) return
//                         // Discard any changes happening within an existing component.
//                         // They will take care of themselves.
//                         if (node.parentElement && node.parentElement.closest('[x-data]')) return
//                         this.discoverUninitializedComponents((el) => {
//                             this.initializeComponent(el)
//                         }, node.parentElement)
//                     })
//                 }
//               }
//         })
//         observer.observe(targetNode, observerOptions)
//     },
//     initializeComponent: function (el) {
//         if (! el.__jmb) {
//             // Wrap in a try/catch so that we don't prevent other components
//             // from initializing when one component contains an error.
//             try {
//                 el.__jmb = new Component(el)
//             } catch (error) {
//                 setTimeout(() => {
//                     throw error
//                 }, 0)
//             }
//         }
//     },
//     clone: function (component, newEl) {
//         if (! newEl.__jmb) {
//             newEl.__jmb = new Component(newEl, component)
//         }
//     },
//     addMagicProperty: function (name, callback) {
//         this.magicProperties[name] = callback
//     },
//     onComponentInitialized: function (callback) {
//         this.onComponentInitializeds.push(callback)
//     },
//     onBeforeComponentInitialized: function (callback) {
//         this.onBeforeComponentInitializeds.push(callback)
//     }
// }
// if (! isTesting()) {
//     window.Alpine = Alpine
//     if (window.deferLoadingAlpine) {
//         window.deferLoadingAlpine(function () {
//             window.Alpine.start()
//         })
//    } else {
//         window.Alpine.start()
//    }
// }
// export default Alpine

exports.default = _default;
},{"./component":"componentApi/component.js","./utils":"componentApi/utils.js"}],"utils.js":[function(require,module,exports) {
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
  if (el.hasAttribute('jmb-name')) {
    return el.getAttribute('jmb-name');
  } else if (el.hasAttribute('jmb-placeholder')) {
    return el.getAttribute('jmb-placeholder');
  } else {
    return null;
  }
}

function walkComponentDom(el, callback, callbackOnNewComponent, myExecName) {
  if (myExecName === undefined) {
    myExecName = el.getAttribute('jmb-name');
  }

  let componentExecName = elIsNewComponent(el);

  if (componentExecName !== null && componentExecName !== myExecName) {
    callbackOnNewComponent(el, componentExecName);
  } else {
    if (callback !== undefined) {
      callback(el);
    }

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
},{}],"morphdom/morphAttrs.js":[function(require,module,exports) {
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

var _index = _interopRequireDefault(require("./componentApi/index.js"));

var _utils = require("./utils.js");

var _index2 = _interopRequireDefault(require("./morphdom/index.js"));

var _jmb = _interopRequireDefault(require("./componentApi/magic/jmb.js"));

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

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
    this.onDocument = onDocument;
    this.placeHolders = {};
    this.api = null;
  }

  mount(originalComponentRef = undefined) {
    this._getPlaceHolders();

    if (this.api === null) {
      this.api = new _index.default(this);
    }

    this.api.mount(originalComponentRef);
  }

  unmount() {
    if (this.api !== null) {
      this.api.unmount();
    }

    this.api = null;
    this.dom = null;
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

    if (this.isPageComponent) {
      let documentElement = this.jembeClient.document.documentElement;
      this.dom = documentElement = this._morphdom(documentElement, this.dom);
      this.dom.setAttribute("jmb-name", this.execName);
    } else {
      this.dom = this._morphdom(parentComponent.placeHolders[this.execName], this.dom);
      parentComponent.placeHolders[this.execName] = this.dom;
    }

    this.onDocument = true;
    this.mount(originalComponent !== undefined && originalComponent.execName === this.execName ? originalComponent : undefined);
  }

  _morphdom(from, to) {
    return (0, _index2.default)(from, to, {
      getNodeKey: node => {
        return node.nodeType === Node.ELEMENT_NODE && node.hasAttribute('jmb-name') ? node.getAttribute('jmb-name') : node.id;
      },
      onBeforeElUpdated: (fromEl, toEl) => {
        // spec - https://dom.spec.whatwg.org/#concept-node-equals
        if (fromEl.isEqualNode(toEl)) {
          return false;
        } // don't pass to next component or template


        if (!this.isPageComponent && fromEl.hasAttribute('jmb-name') && fromEl.getAttribute('jmb-name') !== this.execName) return false;
        if (fromEl.hasAttribute('jmb-placeholder') && fromEl.getAttribute('jmb-placeholder') !== this.execName) return false;

        if (fromEl.hasAttribute('jmb-ignore')) {
          return false;
        } // remove all existing listeners
        // api should add new one


        if (fromEl.__jmb_listeners !== undefined) {
          for (const [event, handler, options] of fromEl.__jmb_listeners) {
            fromEl.removeEventListener(event, handler, options);
          }
        }

        return true;
      },
      childrenOnly: this.isPageComponent
    });
  }

  _getPlaceHolders() {
    this.placeHolders = {};
    (0, _utils.walkComponentDom)(this.dom, undefined, (el, execName) => {
      // populate placeHolders
      this.placeHolders[execName] = el;
    });
  }

  _cleanDom(dom) {
    // if html dom has only one child use that child to put jmb-name tag
    // if not enclose html with div and put jmb-name into it
    if (typeof dom === "string") {
      let domString = dom.trim();

      if (!this.isPageComponent) {
        let template = this.jembeClient.document.createElement("template");
        template.innerHTML = domString; // check is it needed to add souranding DIV tag

        if (template.content.childNodes.length > 1 || template.content.childNodes.length === 0 || template.content.firstChild.nodeType === Node.TEXT_NODE || template.content.childNodes.length === 1 && (template.content.firstChild.hasAttribute("jmb-name") || template.content.firstChild.hasAttribute("jmb-placeholder"))) {
          let div = this.jembeClient.document.createElement("div");
          let curChild = template.content.firstChild;

          while (curChild) {
            let nextChild = curChild.nextSibling;
            div.appendChild(curChild);
            curChild = nextChild;
          }

          template.content.appendChild(div);
        } // add jmb-name tag


        template.content.firstChild.setAttribute("jmb-name", this.execName);
        dom = template.content.firstChild;
      } else {
        const doc = this.jembeClient.domParser.parseFromString(domString, "text/html");
        doc.documentElement.setAttribute("jmb-name", this.execName);
        dom = doc.documentElement;
      }
    }

    dom.removeAttribute('jmb-data');
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
   * Finds all jmb-name and associate jmb-data tags in document 
   * and create ComponentRefs
   */


  getComponentsFromDocument() {
    this.components = {};
    let componentsNodes = this.document.querySelectorAll("[jmb-name][jmb-data]");

    for (const componentNode of componentsNodes) {
      const componentRef = new ComponentRef(this, componentNode.getAttribute('jmb-name'), eval(`(${componentNode.getAttribute('jmb-data')})`), componentNode, true);
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
      currentComponent.merge(parentComponent, orignalComponent);
      newComponents[currentComponent.execName] = currentComponent;

      for (const placeHolderName of Object.keys(currentComponent.placeHolders)) {
        processingExecNames.push(placeHolderName);
      }
    } // unmount components that will be removed


    for (const [execName, component] of Object.entries(this.components)) {
      if (!Object.keys(newComponents).includes(execName) || newComponents[execName] !== component) {
        component.unmount();
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

  consolidateCommands() {
    let initCommandsExecNames = this.commands.filter(c => c.type === 'init').map(c => c.componentExecName);
    let callCommandsExecNames = this.commands.filter(c => c.type === 'call').map(c => c.componentExecName);

    for (const execName of initCommandsExecNames) {
      if (!callCommandsExecNames.includes(execName)) {
        this.addCallCommand(execName, "display");
      }
    } //TODO
    // - display error if actions over two different component are called
    //   and this components are not on ignore part of flow list, also define flow list    

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
    const componentExecName = domNode.closest('[jmb-name]').getAttribute('jmb-name');
    return new _jmb.default(this, componentExecName);
  }

}

exports.JembeClient = JembeClient;
},{"./componentApi/index.js":"componentApi/index.js","./utils.js":"utils.js","./morphdom/index.js":"morphdom/index.js","./componentApi/magic/jmb.js":"componentApi/magic/jmb.js"}],"jembe.js":[function(require,module,exports) {
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
  var ws = new WebSocket(protocol + '://' + hostname + ':' + "40259" + '/');

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