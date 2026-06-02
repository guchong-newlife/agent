(function (global, factory) {
  'use strict';
  if (typeof exports === 'object' && typeof module !== 'undefined') {
    module.exports = factory();
  } else if (typeof define === 'function' && define.amd) {
    define(factory);
  } else {
    var existing = global.__TrackerSDK;
    var sdk = factory();
    sdk.noConflict = function () { global.__TrackerSDK = existing; return sdk; };
    global.__TrackerSDK = sdk;
  }
}(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  // ==================================================================
  // Polyfills
  // ==================================================================
  var _crypto = typeof crypto !== 'undefined' ? crypto : (typeof msCrypto !== 'undefined' ? msCrypto : null);
  var _hasCrypto = _crypto && _crypto.subtle;

  function randomUUID() {
    if (_crypto && _crypto.randomUUID) return _crypto.randomUUID();
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
      var r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  }

  function arrayFrom(x) { try { return Array.prototype.slice.call(x); } catch (e) { return []; } }

  var _console = typeof console !== 'undefined' && console.log ? console : { log: function () {} };

  // ==================================================================
  // Cookie helpers (cross-subdomain unified user)
  // ==================================================================
  function setCookie(name, value, days, domain) {
    try {
      var expires = '';
      if (days) { var d = new Date(); d.setTime(d.getTime() + days * 86400000); expires = '; expires=' + d.toUTCString(); }
      var domainPart = domain ? '; domain=' + domain : '';
      document.cookie = name + '=' + encodeURIComponent(value) + expires + domainPart + '; path=/; SameSite=Lax';
    } catch (e) {}
  }

  function getCookie(name) {
    try {
      var m = document.cookie.match(new RegExp('(?:^|; )' + name.replace(/([.$?*|{}()\[\]\\\/+^])/g, '\\$1') + '=([^;]*)'));
      return m ? decodeURIComponent(m[1]) : null;
    } catch (e) { return null; }
  }

  // ==================================================================
  // Utilities
  // ==================================================================
  function safeNum(v, fallback) {
    fallback = fallback === undefined ? 0 : fallback;
    if (v === null || v === undefined || v !== v) return fallback;
    if (typeof v === 'number' && !isFinite(v)) return fallback;
    var n = Number(v);
    return (n !== n || !isFinite(n)) ? fallback : n;
  }

  function sanitize(obj) {
    if (obj === null || obj === undefined) return obj;
    if (typeof obj === 'number') {
      if (obj !== obj) return 0;
      if (!isFinite(obj)) return obj > 0 ? Number.MAX_SAFE_INTEGER : Number.MIN_SAFE_INTEGER;
      return obj;
    }
    if (typeof obj === 'string') return obj;
    if (Array.isArray(obj)) return obj.map(sanitize);
    if (typeof obj === 'object') {
      var out = {};
      for (var k in obj) {
        if (Object.prototype.hasOwnProperty.call(obj, k)) out[k] = sanitize(obj[k]);
      }
      return out;
    }
    return obj;
  }

  function encodeBase64(str) {
    try {
      var b64 = btoa(unescape(encodeURIComponent(str)));
      return b64.replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
    } catch (e) {
      var chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_';
      var out = '', i = 0;
      try {
        var bytes = unescape(encodeURIComponent(str));
        while (i < bytes.length) {
          var c1 = bytes.charCodeAt(i++), c2 = bytes.charCodeAt(i++), c3 = bytes.charCodeAt(i++);
          out += chars.charAt(c1 >> 2);
          out += chars.charAt(((c1 & 3) << 4) | (c2 >> 4));
          out += isNaN(c2) ? '=' : chars.charAt(((c2 & 15) << 2) | (c3 >> 6));
          out += isNaN(c3) ? '=' : chars.charAt(c3 & 63);
        }
      } catch (e2) {}
      return out;
    }
  }

  function tryFn(fn) { try { return fn(); } catch (e) { return undefined; } }

  // ==================================================================
  // Fingerprint (cookie-first, localStorage fallback)
  // ==================================================================
  function sha256Fallback(message) {
    // Pure JS fallback - simple hash for older browsers without crypto.subtle
    var hash = 0, i, chr;
    if (message.length === 0) return '000000000000000000000000000000000000000000000000';
    for (i = 0; i < message.length; i++) {
      chr = message.charCodeAt(i);
      hash = ((hash << 5) - hash) + chr;
      hash |= 0;
    }
    var h = Math.abs(hash).toString(16);
    while (h.length < 48) h = '0' + h;
    return h.substring(0, 48);
  }

  var _sha256Fn = null;
  function sha256(message) {
    if (_sha256Fn) return _sha256Fn(message);
    if (_hasCrypto) {
      _sha256Fn = function (msg) {
        return _crypto.subtle.digest('SHA-256', new TextEncoder().encode(msg)).then(function (buf) {
          return Array.from(new Uint8Array(buf)).map(function (b) { return b.toString(16).padStart(2, '0'); }).join('');
        });
      };
    } else {
      _sha256Fn = function (msg) { return Promise.resolve(sha256Fallback(msg)); };
    }
    return _sha256Fn(message);
  }

  function canvasFingerprint() {
    return new Promise(function (resolve) {
      try {
        var c = document.createElement('canvas');
        c.width = 280; c.height = 60;
        var ctx = c.getContext('2d');
        if (!ctx) { resolve('no_canvas'); return; }
        ctx.textBaseline = 'top'; ctx.font = '16px Arial';
        ctx.fillStyle = '#f60'; ctx.fillRect(125, 1, 62, 20);
        ctx.fillStyle = '#069';
        ctx.fillText('Browser Fingerprint <@!>', 2, 18);
        ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
        ctx.fillText('Browser Fingerprint <@!>', 4, 36);
        resolve(c.toDataURL().substring(c.toDataURL().length - 64));
      } catch (e) { resolve('canvas_err'); }
    });
  }

  function webglFingerprint() {
    try {
      var c = document.createElement('canvas');
      var gl = c.getContext('webgl') || c.getContext('experimental-webgl');
      if (!gl) return 'no_webgl';
      var dbg = gl.getExtension('WEBGL_debug_renderer_info');
      return (dbg ? gl.getParameter(dbg.UNMASKED_VENDOR_WEBGL) : '') + '|' +
             (dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : '');
    } catch (e) { return 'webgl_err'; }
  }

  function audioFingerprint() {
    return new Promise(function (resolve) {
      try {
        var AudioCtx = window.OfflineAudioContext || window.webkitOfflineAudioContext;
        if (!AudioCtx) { resolve('no_audio'); return; }
        var ctx = new AudioCtx(1, 44100, 44100);
        var osc = ctx.createOscillator();
        osc.type = 'triangle'; osc.frequency.value = 10000;
        var comp = ctx.createDynamicsCompressor();
        comp.threshold.value = -50; comp.knee.value = 40; comp.ratio.value = 12;
        comp.attack.value = 0; comp.release.value = 0.25;
        osc.connect(comp); comp.connect(ctx.destination); osc.start(0);
        ctx.oncomplete = function (e) {
          var data = e.renderedBuffer.getChannelData(0);
          var sum = 0;
          for (var i = 0; i < Math.min(4500, data.length); i++) sum += Math.abs(data[i]);
          resolve(sum.toFixed(6));
        };
        ctx.startRendering();
      } catch (e) { resolve('audio_err'); }
    });
  }

  function gatherFeatures() {
    var nav = navigator;
    return {
      ua: nav.userAgent || '',
      plat: nav.platform || '',
      lang: nav.language || '',
      cores: safeNum(nav.hardwareConcurrency, ''),
      mem: safeNum(nav.deviceMemory, ''),
      scr: (typeof screen !== 'undefined' ? screen.width + 'x' + screen.height + 'x' + screen.colorDepth : ''),
      tz: new Date().getTimezoneOffset(),
      touch: ('ontouchstart' in window) ? '1' : '0',
      vend: nav.vendor || '',
      plugins: tryFn(function () { return arrayFrom(nav.plugins || []).map(function (p) { return p.name; }).join(','); }) || '',
    };
  }

  // ==================================================================
  // Main SDK
  // ==================================================================
  function TrackerSDK(customOptions) {
    if (window.__tracker_loaded) return window.__tracker_sdk_instance;
    window.__tracker_loaded = true;

    var defaults = {
      endpoint: '/api/tracking/event',
      sessionEndpoint: '/api/tracking/session',
      sendMode: 'get',        // 'get' | 'beacon' | 'post'
      mode: 'auto',           // 'auto' | 'manual' — manual 模式下不自动采集，需手动调用 track* 方法
      autoFingerprint: true,  // 无缓存时是否自动生成指纹；false 时需手动调用 load()
      cookieDomain: '',       // e.g. '.example.com' for cross-subdomain
      cookieDays: 365,
      debug: false,
      scrollThrottleMs: 250,
      scrollDebounceMs: 500,
      scrollMilestones: [25, 50, 75, 100],
    };

    var opts = {};
    for (var k in defaults) {
      if (Object.prototype.hasOwnProperty.call(defaults, k)) opts[k] = defaults[k];
    }
    if (customOptions) {
      for (var ck in customOptions) {
        if (Object.prototype.hasOwnProperty.call(customOptions, ck)) opts[ck] = customOptions[ck];
      }
    }

    var sessionId = null;
    var fpId = null;
    var sessionEventCount = 0;
    var _seq = 0;
    var scrollTimer = null;
    var lastScrollTime = 0;
    var reachedMilestones = {};
    var visibilitySince = Date.now();
    var pendingFpEvents = [];
    var self = this;

    // ── fingerprint ────────────────────────────────────────────
    function readCachedFingerprint() {
      var cached = getCookie('__fp_id');
      if (!cached) {
        try { cached = localStorage.getItem('__fp_id'); } catch (e) {}
      }
      return cached || null;
    }

    function persistFingerprint(val) {
      setCookie('__fp_id', val, opts.cookieDays, opts.cookieDomain);
      try { localStorage.setItem('__fp_id', val); } catch (e) {}
    }

    function flushPending() {
      for (var i = 0; i < pendingFpEvents.length; i++) send(pendingFpEvents[i]);
      pendingFpEvents = [];
    }

    function load(userFingerprint) {
      if (!userFingerprint || typeof userFingerprint !== 'string') return;
      fpId = userFingerprint;
      persistFingerprint(fpId);
      flushPending();
    }

    async function generateFingerprint() {
      // 1) read from cookie / localStorage
      var cached = readCachedFingerprint();
      if (cached) {
        fpId = cached;
        return cached;
      }

      // 2) no cache — auto-generate if enabled
      if (opts.autoFingerprint) {
        var f = gatherFeatures();
        try { f.canvas = await canvasFingerprint(); } catch (e) { f.canvas = 'err'; }
        try { f.webgl = webglFingerprint(); } catch (e) { f.webgl = 'err'; }
        try { f.audio = await audioFingerprint(); } catch (e) { f.audio = 'err'; }
        var raw = JSON.stringify(f);
        var hash = await sha256(raw);
        fpId = 'fp_' + hash.substring(0, 48);
        persistFingerprint(fpId);
        return fpId;
      }

      // 3) autoFingerprint disabled — wait for load() call
      return null;
    }

    // ── session ─────────────────────────────────────────────────
    function getOrCreateSession() {
      var sid = null;
      try { sid = sessionStorage.getItem('__track_sid'); } catch (e) {}
      if (!sid) {
        sid = 'sess_' + randomUUID().replace(/-/g, '').substring(0, 18);
        try { sessionStorage.setItem('__track_sid', sid); } catch (e) {}
      }
      try { sessionEventCount = parseInt(sessionStorage.getItem('__track_cnt') || '0') || 0; } catch (e) {}
      return sid;
    }

    function bumpSessionCount() {
      sessionEventCount++;
      try { sessionStorage.setItem('__track_cnt', sessionEventCount.toString()); } catch (e) {}
      try {
        if (!sessionStorage.getItem('__track_start')) {
          sessionStorage.setItem('__track_start', new Date().toISOString());
        }
      } catch (e) {}
    }

    var SYSTEM_DATA_FIELDS = [
      'trackName', 'timestamp', 'session_id',
      'load_time_ms', 'dom_ready_ms', 'first_paint_ms', 'dns_ms', 'tcp_ms', 'ttfb_ms',
      'fetch_start_ms', 'redirect_count', 'navigation_type',
      'element', 'mouse', 'modifiers',
      'scroll_depth_pct', 'scroll_depth_px', 'max_scroll_pct', 'document_height', 'viewport_height', 'milestone',
      'state', 'duration_visible_ms',
      'error_type', 'message', 'filename', 'lineno', 'colno', 'stack'
    ];

    function buildCommon(extra) {
      _seq++;
      var trackId = 'trk_' + Date.now().toString(36) + '_' + ('0000' + _seq).slice(-5);
      var dataFields = { track_id: trackId, trackName: extra.trackName || 'custom', timestamp: new Date().toISOString(), session_id: (sessionId || '') };
      var customFields = {};
      for (var ek in extra) {
        if (ek === 'trackName' || ek === 'browser' || ek === 'screen') continue;
        if (!Object.prototype.hasOwnProperty.call(extra, ek)) continue;
        if (SYSTEM_DATA_FIELDS.indexOf(ek) >= 0) {
          dataFields[ek] = extra[ek];
        } else {
          customFields[ek] = extra[ek];
        }
      }
      if (Object.keys(customFields).length > 0) dataFields.custom = customFields;
      return sanitize({
        user: { fingerprint_id: (fpId || '') },
        browser: Object.assign({
          user_agent: navigator.userAgent || '',
          platform: safeStr(navigator.platform),
          language: safeStr(navigator.language),
          languages: tryFn(function () { return arrayFrom(navigator.languages || []); }) || [],
          cookie_enabled: !!navigator.cookieEnabled,
          do_not_track: tryFn(function () { return navigator.doNotTrack; }) || null,
          timezone: tryFn(function () { return Intl.DateTimeFormat().resolvedOptions().timeZone; }) || '',
          timezone_offset: safeNum(new Date().getTimezoneOffset()),
          vendor: safeStr(navigator.vendor),
          hardware_concurrency: safeNum(navigator.hardwareConcurrency, ''),
          device_memory: safeNum(navigator.deviceMemory, ''),
          page_url: tryFn(function () { return location.href; }) || '',
          page_title: tryFn(function () { return document.title; }) || '',
          referrer: tryFn(function () { return document.referrer; }) || '',
        }, extra.browser || {}, {
          screen: Object.assign({
            width: safeNum(tryFn(function () { return screen.width; })),
            height: safeNum(tryFn(function () { return screen.height; })),
            avail_width: safeNum(tryFn(function () { return screen.availWidth; })),
            avail_height: safeNum(tryFn(function () { return screen.availHeight; })),
            color_depth: safeNum(tryFn(function () { return screen.colorDepth; })),
            pixel_ratio: safeNum(tryFn(function () { return window.devicePixelRatio; }), 1),
            viewport_width: safeNum(tryFn(function () { return window.innerWidth; })),
            viewport_height: safeNum(tryFn(function () { return window.innerHeight; })),
          }, extra.screen || {}),
        }),
        data: dataFields,
      });
    }

    function safeStr(v) { return v != null ? String(v) : ''; }

    // ── send ────────────────────────────────────────────────────
    function send(evt) {
      if (!fpId) { pendingFpEvents.push(evt); return; }
      bumpSessionCount();
      var clean = sanitize(evt);
      var body = JSON.stringify(clean);
      if (opts.debug) _console.log('[tracker]', clean.data.trackName, clean);

      var mode = opts.sendMode;
      var url = opts.endpoint;
      var d = encodeBase64(body);

      if (mode === 'beacon' && navigator.sendBeacon) {
        var blob = new Blob([body], { type: 'application/json' });
        navigator.sendBeacon(url, blob);
      } else if (mode === 'post') {
        try {
          fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: body, keepalive: true }).catch(function () {});
        } catch (e) {}
      } else {
        // default GET
        try {
          fetch(url + '?d=' + d, { method: 'GET', keepalive: true }).catch(function () {});
        } catch (e) {}
      }
    }

    function sendSession(sessionData) {
      var body = JSON.stringify(sanitize(sessionData));
      var url = opts.sessionEndpoint;
      var d = encodeBase64(body);
      var mode = opts.sendMode;

      if (mode === 'beacon' && navigator.sendBeacon) {
        navigator.sendBeacon(url, new Blob([body], { type: 'application/json' }));
      } else if (mode === 'post') {
        try {
          fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: body, keepalive: true }).catch(function () {});
        } catch (e) {}
      } else {
        try {
          fetch(url + '?d=' + d, { method: 'GET', keepalive: true }).catch(function () {});
        } catch (e) {}
      }
    }

    // ── track functions ─────────────────────────────────────────
    function trackPageView() {
      var p = tryFn(function () { return performance.timing; });
      var evt;
      if (!p) {
        evt = buildCommon({ trackName: 'page_view' });
      } else {
        var paintEntries = tryFn(function () { return performance.getEntriesByType('paint'); }) || [];
        var fcp = null;
        for (var i = 0; i < paintEntries.length; i++) {
          if (paintEntries[i].name === 'first-contentful-paint') { fcp = paintEntries[i]; break; }
        }
        evt = buildCommon({
          trackName: 'page_view',
          load_time_ms: safeNum(p.loadEventEnd - p.navigationStart, 0),
          dom_ready_ms: safeNum(p.domContentLoadedEventEnd - p.navigationStart, 0),
          first_paint_ms: fcp ? safeNum(fcp.startTime, null) : null,
          dns_ms: safeNum(p.domainLookupEnd - p.domainLookupStart, 0),
          tcp_ms: safeNum(p.connectEnd - p.connectStart, 0),
          ttfb_ms: safeNum(p.responseStart - p.requestStart, 0),
          fetch_start_ms: safeNum(p.fetchStart - p.navigationStart, 0),
          redirect_count: safeNum(tryFn(function () { return performance.navigation.redirectCount; }), 0),
          navigation_type: tryFn(function () { return ['navigate', 'reload', 'back_forward', 'prerender'][performance.navigation.type]; }) || 'unknown',
        });
      }

      send(evt);
      sendSession({
        session_id: sessionId,
        fingerprint_id: fpId,
        timestamp: evt.data.timestamp,
        event_count: sessionEventCount,
      });
    }

    function trackClick(e) {
      e = e || window.event;
      var el = e.target || e.srcElement;
      if (!el || !el.tagName) return;

      var parts = [];
      var node = el;
      for (var i = 0; i < 5 && node && node !== document.body; i++) {
        var sel = (node.tagName || '').toLowerCase();
        if (node.id) { sel = '#' + node.id; parts.unshift(sel); break; }
        if (node.className && typeof node.className === 'string' && node.className.trim()) {
          sel += '.' + node.className.trim().split(/\s+/).slice(0, 2).join('.');
        }
        parts.unshift(sel);
        node = node.parentElement || node.parentNode;
      }

      var dataAttrs = {};
      try {
        if (el.attributes) {
          for (var a = 0; a < el.attributes.length; a++) {
            var attr = el.attributes[a];
            if (attr.name && attr.name.indexOf('data-') === 0) dataAttrs[attr.name] = attr.value || '';
          }
        }
      } catch (ex) {}

      send(buildCommon({
        trackName: 'click',
        element: sanitize({
          tag: el.tagName || '',
          id: el.id || '',
          class_list: (typeof el.className === 'string') ? el.className : '',
          text: (el.textContent || el.innerText || '').replace(/\s+/g, ' ').trim().substring(0, 200),
          selector: parts.join(' > '),
          attributes: dataAttrs,
          href: (el.tagName === 'A' || el.tagName === 'a') ? (el.href || '') : undefined,
        }),
        mouse: sanitize({
          client_x: safeNum(e.clientX, null), client_y: safeNum(e.clientY, null),
          page_x: safeNum(e.pageX, null), page_y: safeNum(e.pageY, null),
          button: safeNum(e.button, 0),
        }),
        modifiers: sanitize({
          ctrl_key: !!e.ctrlKey, shift_key: !!e.shiftKey,
          alt_key: !!e.altKey, meta_key: !!e.metaKey,
        }),
      }));
    }

    function trackScroll() {
      var now = Date.now();
      if (now - lastScrollTime < opts.scrollThrottleMs) return;
      lastScrollTime = now;

      clearTimeout(scrollTimer);
      scrollTimer = setTimeout(function () {
        var docH = tryFn(function () { return document.documentElement.scrollHeight; }) || 0;
        var vpH = tryFn(function () { return window.innerHeight; }) || 0;
        if (docH <= vpH || vpH <= 0) return;
        var scrollY = tryFn(function () { return window.scrollY || window.pageYOffset; }) || 0;
        var pct = Math.round((scrollY / (docH - vpH)) * 100);

        var milestone = null;
        for (var i = 0; i < opts.scrollMilestones.length; i++) {
          var m = opts.scrollMilestones[i];
          if (pct >= m && !reachedMilestones[m]) {
            reachedMilestones[m] = true;
            milestone = m;
            break;
          }
        }
        if (milestone === null) return;

        var reached = [];
        for (var j = 0; j < opts.scrollMilestones.length; j++) {
          var rm = opts.scrollMilestones[j];
          if (reachedMilestones[rm]) reached.push(rm);
        }

        send(buildCommon({
          trackName: 'scroll',
          browser: {},
          screen: { viewport_height: vpH },
          scroll_depth_pct: safeNum(pct),
          scroll_depth_px: safeNum(scrollY),
          max_scroll_pct: reached.length ? Math.max.apply(null, reached) : 0,
          document_height: safeNum(docH),
          viewport_height: safeNum(vpH),
          milestone: milestone,
        }));
      }, opts.scrollDebounceMs);
    }

    function trackVisibility() {
      var state = tryFn(function () { return document.visibilityState; }) || 'visible';
      var now = Date.now();
      var durationMs = state === 'hidden' ? safeNum(now - visibilitySince, 0) : 0;

      send(buildCommon({
        trackName: 'visibility',
        browser: {},
        screen: {},
        state: state,
        duration_visible_ms: state === 'hidden' ? durationMs : null,
      }));

      if (state === 'visible') visibilitySince = now;
    }

    function trackError(e) {
      e = e || window.event;
      var msg = '', filename = '', lineno = 0, colno = 0, stack = '';

      if (e.error) {
        msg = (e.error.message || '');
        stack = (e.error.stack || '').substring(0, 2000);
      } else if (e.reason) {
        msg = String(e.reason);
        stack = (e.reason && e.reason.stack ? e.reason.stack : '').substring(0, 2000);
      } else {
        msg = (e.message || '');
        filename = (e.filename || '');
        lineno = safeNum(e.lineno, 0);
        colno = safeNum(e.colno, 0);
      }

      send(buildCommon({
        trackName: 'error',
        browser: {},
        screen: {},
        error_type: (e.type === 'unhandledrejection') ? 'unhandledrejection' : 'error',
        message: msg,
        filename: filename,
        lineno: lineno,
        colno: colno,
        stack: stack,
      }));
    }

    // ── public API ──────────────────────────────────────────────
    function track(name, payload) {
      var extra = { trackName: name };
      if (payload) { for (var pk in payload) { if (Object.prototype.hasOwnProperty.call(payload, pk)) extra[pk] = payload[pk]; } }
      send(buildCommon(extra));
    }

    function manualPageView() { trackPageView(); }
    function manualClick() { trackClick.apply(null, arguments); }
    function manualError(message, stack) {
      send(buildCommon({
        trackName: 'error',
        browser: {},
        screen: {},
        error_type: 'manual',
        message: message || '',
        filename: '',
        lineno: 0,
        colno: 0,
        stack: stack || '',
      }));
    }

    // ── init ────────────────────────────────────────────────────
    async function init() {
      fpId = await generateFingerprint();
      sessionId = getOrCreateSession();

      if (fpId) {
        for (var i = 0; i < pendingFpEvents.length; i++) send(pendingFpEvents[i]);
        pendingFpEvents = [];
      }

      var isManual = opts.mode === 'manual';

      if (!isManual) {
        if (document.readyState === 'complete') {
          setTimeout(trackPageView, 0);
        } else if (window.attachEvent) {
          window.attachEvent('onload', trackPageView);
        } else {
          window.addEventListener('load', trackPageView);
        }

        if (document.addEventListener) {
          document.addEventListener('click', trackClick, true);
          window.addEventListener('scroll', trackScroll, { passive: true });
          document.addEventListener('visibilitychange', trackVisibility);
          window.addEventListener('error', trackError);
          window.addEventListener('unhandledrejection', trackError);
        } else if (window.attachEvent) {
          document.attachEvent('onclick', function () { trackClick(window.event); });
          window.attachEvent('onscroll', trackScroll);
          window.attachEvent('onerror', function () { trackError(window.event); });
        }
      }

      // beforeunload always registered (session end tracking)
      var beforeUnloadHandler = function () {
        var endData = JSON.stringify(sanitize({
          session_id: sessionId,
          fingerprint_id: fpId,
          event_count: sessionEventCount,
          ended_at: new Date().toISOString(),
        }));
        var surl = opts.sessionEndpoint;
        var sd = encodeBase64(endData);
        var sm = opts.sendMode;

        if (sm === 'beacon' && navigator.sendBeacon) {
          navigator.sendBeacon(surl, new Blob([endData], { type: 'application/json' }));
        } else if (sm === 'post') {
          try { fetch(surl, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: endData, keepalive: true }).catch(function () {}); } catch (e) {}
        } else {
          try { fetch(surl + '?d=' + sd, { method: 'GET', keepalive: true }).catch(function () {}); } catch (e) {}
        }
      };

      if (window.addEventListener) {
        window.addEventListener('beforeunload', beforeUnloadHandler);
        window.addEventListener('unload', beforeUnloadHandler);
      } else if (window.attachEvent) {
        window.attachEvent('onbeforeunload', beforeUnloadHandler);
        window.attachEvent('onunload', beforeUnloadHandler);
      }

      // expose instance
      self.load = load;
      self.track = track;
      self.trackPageView = manualPageView;
      self.trackClick = manualClick;
      self.trackError = manualError;
      self.getFingerprint = function () { return fpId; };
      self.getSession = function () { return sessionId; };
      self.getMode = function () { return opts.mode; };
      window.__tracker = self;
      window.__tracker_sdk_instance = self;
    }

    init().catch(function (e) { if (opts.debug) _console.log('[tracker] init error:', e); });
  }

  // ==================================================================
  // Export
  // ==================================================================
  TrackerSDK.prototype.load = function (userFingerprint) {
    if (window.__tracker) window.__tracker.load(userFingerprint);
  };
  TrackerSDK.prototype.track = function (name, payload) {
    if (window.__tracker) window.__tracker.track(name, payload);
  };
  TrackerSDK.prototype.trackPageView = function () {
    if (window.__tracker) window.__tracker.trackPageView();
  };
  TrackerSDK.prototype.trackClick = function () {
    if (window.__tracker) window.__tracker.trackClick();
  };
  TrackerSDK.prototype.trackError = function (message, stack) {
    if (window.__tracker) window.__tracker.trackError(message, stack);
  };

  // Auto-init when loaded via <script> tag in browser
  if (typeof document !== 'undefined' && !window.__TrackerSDK_noAuto) {
    new TrackerSDK();
  }

  return TrackerSDK;
}));
