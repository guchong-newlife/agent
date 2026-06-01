(function () {
  'use strict';

  const SCROLL_THROTTLE_MS = 250;
  const SCROLL_DEBOUNCE_MS = 500;
  const SCROLL_MILESTONES = [25, 50, 75, 100];

  let sessionId = null;
  let fpId = null;
  let sessionEventCount = 0;
  let scrollTimer = null;
  let lastScrollTime = 0;
  let reachedMilestones = new Set();
  let visibilitySince = Date.now();
  let pendingFpEvents = [];

  // ── fingerprint ──────────────────────────────────────────────

  async function generateFingerprint() {
    const cached = localStorage.getItem('__fp_id');
    if (cached) return cached;

    const features = {
      user_agent: navigator.userAgent,
      platform: navigator.platform,
      language: navigator.language,
      hardware_concurrency: navigator.hardwareConcurrency,
      device_memory: navigator.deviceMemory,
      screen: screen.width + 'x' + screen.height + 'x' + screen.colorDepth,
      timezone_offset: new Date().getTimezoneOffset(),
      touch_support: 'ontouchstart' in window,
      vendor: navigator.vendor,
      plugins: Array.from(navigator.plugins || []).map(function(p) { return p.name; }).join(','),
    };

    try { features.canvas = await canvasFingerprint(); } catch (e) { features.canvas = 'err'; }
    try { features.webgl = webglFingerprint(); } catch (e) { features.webgl = 'err'; }
    try { features.audio = await audioFingerprint(); } catch (e) { features.audio = 'err'; }

    var raw = JSON.stringify(features);
    var hash = await sha256(raw);
    localStorage.setItem('__fp_id', 'fp_' + hash.substring(0, 48));
    return 'fp_' + hash.substring(0, 48);
  }

  function canvasFingerprint() {
    return new Promise(function (resolve) {
      var c = document.createElement('canvas');
      c.width = 280; c.height = 60;
      var ctx = c.getContext('2d');
      ctx.textBaseline = 'top';
      ctx.font = '16px Arial';
      ctx.fillStyle = '#f60';
      ctx.fillRect(125, 1, 62, 20);
      ctx.fillStyle = '#069';
      ctx.fillText('Browser Fingerprint 浏览器指纹  <@!>', 2, 18);
      ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
      ctx.fillText('Browser Fingerprint 浏览器指纹  <@!>', 4, 36);
      var data = c.toDataURL();
      resolve(data.substring(data.length - 64));
    });
  }

  function webglFingerprint() {
    var c = document.createElement('canvas');
    var gl = c.getContext('webgl') || c.getContext('experimental-webgl');
    if (!gl) return 'no_webgl';
    var dbg = gl.getExtension('WEBGL_debug_renderer_info');
    var vendor = dbg ? gl.getParameter(dbg.UNMASKED_VENDOR_WEBGL) : '';
    var renderer = dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : '';
    return vendor + '|' + renderer;
  }

  function audioFingerprint() {
    return new Promise(function (resolve) {
      try {
        var ctx = new (window.OfflineAudioContext || window.webkitOfflineAudioContext)(1, 44100, 44100);
        var osc = ctx.createOscillator();
        osc.type = 'triangle';
        osc.frequency.value = 10000;
        var comp = ctx.createDynamicsCompressor();
        comp.threshold.value = -50;
        comp.knee.value = 40;
        comp.ratio.value = 12;
        comp.attack.value = 0;
        comp.release.value = 0.25;
        osc.connect(comp);
        comp.connect(ctx.destination);
        osc.start(0);
        ctx.oncomplete = function (e) {
          var data = e.renderedBuffer.getChannelData(0);
          var sum = 0;
          for (var i = 0; i < 4500; i++) sum += Math.abs(data[i]);
          resolve(sum.toFixed(6));
        };
        ctx.startRendering();
      } catch (e) { resolve('audio_err'); }
    });
  }

  async function sha256(message) {
    var data = new TextEncoder().encode(message);
    var hashBuffer = await crypto.subtle.digest('SHA-256', data);
    var hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(function(b) { return b.toString(16).padStart(2, '0'); }).join('');
  }

  // ── session ──────────────────────────────────────────────────

  function getOrCreateSession() {
    var sid = sessionStorage.getItem('__track_sid');
    if (!sid) {
      sid = 'sess_' + crypto.randomUUID().replace(/-/g, '').substring(0, 18);
      sessionStorage.setItem('__track_sid', sid);
    }
    sessionEventCount = parseInt(sessionStorage.getItem('__track_cnt') || '0');
    return sid;
  }

  function bumpSessionCount() {
    sessionEventCount++;
    sessionStorage.setItem('__track_cnt', sessionEventCount.toString());
    if (!sessionStorage.getItem('__track_start')) {
      sessionStorage.setItem('__track_start', new Date().toISOString());
    }
  }

  function buildCommon(extra) {
    return Object.assign({
      event_id: 'evt_' + crypto.randomUUID().replace(/-/g, '').substring(0, 20),
      trackName: extra.trackName || 'custom',
      timestamp: new Date().toISOString(),
      fingerprint_id: fpId || '',
      session_id: sessionId || '',
      page_url: location.href,
      page_title: document.title,
      referrer: document.referrer || '',
    }, extra);
  }

  function slimBrowser() {
    return {
      user_agent: navigator.userAgent,
      platform: navigator.platform,
      language: navigator.language,
      languages: navigator.languages ? Array.from(navigator.languages) : [],
      cookie_enabled: navigator.cookieEnabled,
      do_not_track: navigator.doNotTrack,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      timezone_offset: new Date().getTimezoneOffset(),
      vendor: navigator.vendor,
      hardware_concurrency: navigator.hardwareConcurrency,
      device_memory: navigator.deviceMemory,
    };
  }

  function slimScreen() {
    return {
      width: screen.width,
      height: screen.height,
      avail_width: screen.availWidth,
      avail_height: screen.availHeight,
      color_depth: screen.colorDepth,
      pixel_ratio: window.devicePixelRatio,
      viewport_width: window.innerWidth,
      viewport_height: window.innerHeight,
    };
  }

  // ── send (GET with base64 encoding) ────────────────────────

  function encodeBase64(str) {
    var b64 = btoa(unescape(encodeURIComponent(str)));
    return b64.replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
  }

  function send(evt) {
    if (!fpId) {
      pendingFpEvents.push(evt);
      return;
    }
    bumpSessionCount();

    var body = JSON.stringify(evt);
    console.log('[tracker]', evt.trackName, body);
    var url = '/api/tracking/event?d=' + encodeBase64(body);
    fetch(url, { method: 'GET', keepalive: true }).catch(function () {});
  }

  function sendSession(sessionData) {
    var body = JSON.stringify(sessionData);
    var url = '/api/tracking/session?d=' + encodeBase64(body);
    fetch(url, { method: 'GET', keepalive: true }).catch(function () {});
  }

  // ── track functions (event happens → send immediately) ───────

  function trackPageView() {
    var p = performance.timing;
    var paintEntries = performance.getEntriesByType('paint');
    var fcp = null;
    for (var i = 0; i < paintEntries.length; i++) {
      if (paintEntries[i].name === 'first-contentful-paint') { fcp = paintEntries[i]; break; }
    }

    var evt = buildCommon({
      trackName: 'page_view',
      browser: slimBrowser(),
      screen: slimScreen(),
      load_time_ms: p.loadEventEnd - p.navigationStart,
      dom_ready_ms: p.domContentLoadedEventEnd - p.navigationStart,
      first_paint_ms: fcp ? fcp.startTime : null,
      dns_ms: p.domainLookupEnd - p.domainLookupStart,
      tcp_ms: p.connectEnd - p.connectStart,
      ttfb_ms: p.responseStart - p.requestStart,
      fetch_start_ms: p.fetchStart - p.navigationStart,
      redirect_count: performance.navigation.redirectCount,
      navigation_type: ['navigate', 'reload', 'back_forward', 'prerender'][performance.navigation.type] || 'unknown',
    });

    send(evt);
    sendSession({
      session_id: sessionId,
      fingerprint_id: fpId,
      page_url: evt.page_url,
      referrer: evt.referrer,
      browser: evt.browser || slimBrowser(),
      screen: evt.screen || slimScreen(),
      timestamp: evt.timestamp,
      event_count: sessionEventCount,
    });
  }

  function trackClick(e) {
    var el = e.target;
    if (!el || !el.tagName) return;

    var parts = [];
    var node = el;
    for (var i = 0; i < 5 && node && node !== document.body; i++) {
      var sel = node.tagName.toLowerCase();
      if (node.id) { sel = '#' + node.id; parts.unshift(sel); break; }
      if (node.className && typeof node.className === 'string') {
        sel += '.' + node.className.trim().split(/\s+/).slice(0, 2).join('.');
      }
      parts.unshift(sel);
      node = node.parentElement;
    }

    var dataAttrs = {};
    if (el.attributes) {
      for (var a = 0; a < el.attributes.length; a++) {
        var attr = el.attributes[a];
        if (attr.name.indexOf('data-') === 0) dataAttrs[attr.name] = attr.value;
      }
    }

    var evt = buildCommon({
      trackName: 'click',
      browser: slimBrowser(),
      screen: slimScreen(),
      element: {
        tag: el.tagName,
        id: el.id,
        class_list: el.className && typeof el.className === 'string' ? el.className : '',
        text: (el.textContent || '').replace(/\s+/g, ' ').trim().substring(0, 200),
        selector: parts.join(' > '),
        attributes: dataAttrs,
        href: el.tagName === 'A' ? el.href : undefined,
      },
      mouse: {
        client_x: e.clientX, client_y: e.clientY,
        page_x: e.pageX, page_y: e.pageY,
        button: e.button,
      },
      modifiers: {
        ctrl_key: e.ctrlKey, shift_key: e.shiftKey,
        alt_key: e.altKey, meta_key: e.metaKey,
      },
    });

    send(evt);
  }

  function trackScroll() {
    var now = Date.now();
    if (now - lastScrollTime < SCROLL_THROTTLE_MS) return;
    lastScrollTime = now;

    clearTimeout(scrollTimer);
    scrollTimer = setTimeout(function () {
      var docH = document.documentElement.scrollHeight;
      var vpH = window.innerHeight;
      if (docH <= vpH) return;
      var scrollY = window.scrollY;
      var pct = Math.round((scrollY / (docH - vpH)) * 100);

      var milestone = null;
      for (var i = 0; i < SCROLL_MILESTONES.length; i++) {
        var m = SCROLL_MILESTONES[i];
        if (pct >= m && !reachedMilestones.has(m)) {
          reachedMilestones.add(m);
          milestone = m;
          break;
        }
      }
      if (milestone === null) return;

      var evt = buildCommon({
        trackName: 'scroll',
        browser: {},
        screen: { viewport_height: vpH },
        scroll_depth_pct: pct,
        scroll_depth_px: scrollY,
        max_scroll_pct: Math.max.apply(null, SCROLL_MILESTONES.filter(function(x) { return reachedMilestones.has(x); })),
        document_height: docH,
        viewport_height: vpH,
        milestone: milestone,
      });

      send(evt);
    }, SCROLL_DEBOUNCE_MS);
  }

  function trackVisibility() {
    var state = document.visibilityState;
    var now = Date.now();
    var durationMs = state === 'hidden' ? now - visibilitySince : 0;

    var evt = buildCommon({
      trackName: 'visibility',
      browser: {},
      screen: {},
      state: state,
      duration_visible_ms: state === 'hidden' ? durationMs : null,
    });

    send(evt);

    if (state === 'visible') visibilitySince = now;
  }

  function trackError(e) {
    var msg = '', filename = '', lineno = 0, colno = 0, stack = '';

    if (e.error) {
      msg = e.error.message || '';
      stack = (e.error.stack || '').substring(0, 2000);
    } else if (e.reason) {
      msg = String(e.reason);
      stack = (e.reason && e.reason.stack ? e.reason.stack : '').substring(0, 2000);
    } else {
      msg = e.message || '';
      filename = e.filename || '';
      lineno = e.lineno || 0;
      colno = e.colno || 0;
    }

    var evt = buildCommon({
      trackName: 'error',
      browser: {},
      screen: {},
      error_type: e.type === 'unhandledrejection' ? 'unhandledrejection' : 'error',
      message: msg,
      filename: filename,
      lineno: lineno,
      colno: colno,
      stack: stack,
    });

    send(evt);
  }

  // ── public API ───────────────────────────────────────────────

  function track(name, payload) {
    var evt = buildCommon(Object.assign({ trackName: name }, payload || {}));
    send(evt);
  }

  // ── init ─────────────────────────────────────────────────────

  async function init() {
    fpId = await generateFingerprint();
    sessionId = getOrCreateSession();

    // Send any events that were held while fingerprint was computing
    for (var i = 0; i < pendingFpEvents.length; i++) {
      send(pendingFpEvents[i]);
    }
    pendingFpEvents = [];

    // Auto-track: page_view
    if (document.readyState === 'complete') {
      setTimeout(trackPageView, 0);
    } else {
      window.addEventListener('load', trackPageView);
    }

    // Auto-track: click (capture phase, event delegation on document)
    document.addEventListener('click', trackClick, true);

    // Auto-track: scroll (passive, throttled + debounced, milestones only)
    window.addEventListener('scroll', trackScroll, { passive: true });

    // Auto-track: visibility
    document.addEventListener('visibilitychange', trackVisibility);

    // Auto-track: error
    window.addEventListener('error', trackError);
    window.addEventListener('unhandledrejection', trackError);

    // Session end on page unload (GET with keepalive)
    window.addEventListener('beforeunload', function () {
      var unloadBody = JSON.stringify({
        session_id: sessionId,
        fingerprint_id: fpId,
        event_count: sessionEventCount,
        ended_at: new Date().toISOString(),
      });
      var url = '/api/tracking/session?d=' + encodeBase64(unloadBody);
      fetch(url, { method: 'GET', keepalive: true }).catch(function () {});
    });

    // Expose public API
    window.__tracker = {
      track: track,
      getFingerprint: function () { return fpId; },
      getSession: function () { return sessionId; },
    };
  }

  init();
})();
