# 埋点 SDK 文档

## 1. 概述

企业智能搜索系统埋点 SDK，支持浏览器指纹识别、跨子域名用户统一、自动/手动事件采集、多种上报模式，以及 ES Module / Script 标签双加载方式。

**文件位置**: `src/web_ui/static/tracker.js`

---

## 2. 核心能力

| 能力 | 说明 |
|------|------|
| 浏览器指纹 | Canvas + WebGL + Audio + 插件 + 屏幕等多维特征 → SHA-256，跨会话复用 |
| 跨子域名用户统一 | Cookie 存储指纹（支持 `domain=.example.com`），localStorage 兜底 |
| 自动采集 | page_view / click / scroll / visibility / error 五种事件零配置自动上报 |
| 手动上报 | `mode: 'manual'` 关闭自动采集，提供 `track()` / `trackPageView()` / `trackError()` 手动调用 |
| 多种上报模式 | GET（Base64-URL 参数）/ POST（fetch） / sendBeacon（Blob），通过 `sendMode` 配置 |
| 低级浏览器兼容 | IE 兼容（attachEvent / srcElement），crypto.subtle 不可用时纯 JS 哈希降级 |
| NaN 兜底 | `safeNum()` + `sanitize()` 递归清理所有数值字段 |
| 防重复加载 | `window.__tracker_loaded` 标志位，同页面多次加载只初始化一次 |
| ES Module 导出 | UMD 包装，同时支持 `<script>` / CommonJS / AMD / ES Module |
| 无用户 ID | 不采集也不上报任何用户身份信息 |

---

## 3. 加载方式

### 3.1 Script 标签（自动初始化）

```html
<!-- 默认以 mode: 'auto' 自动初始化 -->
<script src="/static/tracker.js"></script>
```

此时 SDK 自动完成指纹生成、会话创建、事件监听，无需额外代码。

### 3.2 Script 标签（手动配置）

```html
<script>
  // 禁用自动初始化
  window.__TrackerSDK_noAuto = true;
</script>
<script src="/static/tracker.js"></script>
<script>
  var tracker = new __TrackerSDK({
    mode: 'manual',
    sendMode: 'post',
    cookieDomain: '.example.com',
    debug: true,
  });
</script>
```

### 3.3 ES Module

```javascript
import TrackerSDK from './tracker.js';

const tracker = new TrackerSDK({
  mode: 'manual',
  sendMode: 'beacon',
});
```

### 3.4 全局实例访问

初始化后可通过以下任意方式获取实例：

```javascript
window.__tracker              // 实例对象
window.__tracker_sdk_instance // 同上
window.__TrackerSDK           // 构造函数，可 new 创建新实例
```

---

## 4. 配置参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `endpoint` | string | `/api/tracking/event` | 事件上报接口 |
| `sessionEndpoint` | string | `/api/tracking/session` | 会话上报接口 |
| `sendMode` | string | `get` | 上报方式：`get` / `post` / `beacon` |
| `mode` | string | `auto` | 采集模式：`auto`（自动监听）/ `manual`（仅手动调用） |
| `autoFingerprint` | boolean | `true` | 无缓存时是否自动生成浏览器指纹；`false` 时需手动调用 `load()` |
| `cookieDomain` | string | `''` | Cookie 域名，如 `.example.com` 实现跨子域名 |
| `cookieDays` | number | `365` | Cookie 有效期（天） |
| `debug` | boolean | `false` | 是否在控制台打印上报 JSON |
| `scrollThrottleMs` | number | `250` | 滚动事件节流间隔（ms） |
| `scrollDebounceMs` | number | `500` | 滚动停止后触发延迟（ms） |
| `scrollMilestones` | number[] | `[25, 50, 75, 100]` | 滚动深度里程碑（%） |

---

## 5. API 方法

### 5.1 load(userFingerprint)

设置自定义浏览器指纹，替换 SDK 自动生成的值。调用后指纹持久化到 Cookie 和 localStorage，后续页面访问直接读取缓存。

```javascript
window.__tracker.load('user_zhihu_homepage');
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `userFingerprint` | string | 自定义指纹字符串，如用户 ID 或业务标识 |

**执行逻辑**：

1. 设置 `fpId = userFingerprint`
2. 写入 Cookie `__fp_id`（受 `cookieDomain` 和 `cookieDays` 控制）
3. 写入 `localStorage.__fp_id`
4. 发送所有等待中的事件（`autoFingerprint: false` 时，`load()` 调用前的事件暂存在队列中不丢失）

**与 `autoFingerprint` 配合**：

| autoFingerprint | 无缓存时的行为 |
|-----------------|---------------|
| `true`（默认） | 自动生成浏览器指纹，`load()` 可选覆盖 |
| `false` | 不自动生成，必须调用 `load()` 设置自定义指纹 |

### 5.2 track(name, payload?)

上报自定义事件。

```javascript
window.__tracker.track('purchase', {
  label: 'buy_now',
  payload: { product_id: 42, amount: 99.9, currency: 'CNY' },
});
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `name` | string | 事件名称，对应上报 JSON 的 `trackName` 字段 |
| `payload` | object | 可选，合并到上报 JSON 中 |

### 5.3 trackPageView()

手动上报页面浏览事件，含性能指标。

```javascript
// SPA 路由切换时调用
router.afterEach(function () {
  window.__tracker.trackPageView();
});
```

### 5.4 trackError(message, stack?)

手动上报错误事件。

```javascript
try {
  riskyOperation();
} catch (e) {
  window.__tracker.trackError(e.message, e.stack);
}
```

### 5.5 getFingerprint()

获取当前浏览器指纹 ID。

```javascript
var fpId = window.__tracker.getFingerprint();
// "fp_a3f7c2d9e1b506482a91c78f3d45e0678b2c1d9a0f4e5b6789"
```

### 5.6 getSession()

获取当前会话 ID。

```javascript
var sid = window.__tracker.getSession();
// "sess_x8k2m7p1q4w9r"
```

### 5.7 getMode()

获取当前采集模式。

```javascript
window.__tracker.getMode(); // "auto" 或 "manual"
```

---

## 6. 上报方式（sendMode）

| 值 | 传输方式 | 数据编码 | 适用场景 |
|----|----------|----------|----------|
| `get` | `fetch GET` + `keepalive` | URL-safe Base64 参数 `?d=...` | 默认，兼容性最好 |
| `post` | `fetch POST` + `keepalive` | JSON Body | 数据量大，需避免 URL 长度限制 |
| `beacon` | `navigator.sendBeacon` | Blob（JSON） | 非阻塞，页面关闭时最可靠 |

`beforeunload` 时会话结束事件自动跟随配置的 `sendMode`。

---

## 7. 自动采集事件

### 7.1 page_view

- **触发**: 页面 `load` 事件
- **性能指标**: `load_time_ms`, `dom_ready_ms`, `first_paint_ms`, `dns_ms`, `tcp_ms`, `ttfb_ms`
- **导航类型**: `navigate` / `reload` / `back_forward`

### 7.2 click

- **触发**: `document` 捕获阶段
- **采集数据**: 元素 tag/id/class/selector/text/data-* 属性、鼠标坐标 (client/page)、按钮 (左/中/右键)、修饰键 (Ctrl/Shift/Alt/Meta)

### 7.3 scroll

- **触发**: window scroll，`passive: true`
- **性能优化**: rAF 节流 250ms + debounce 500ms + 仅里程碑触发
- **里程碑**: 25% / 50% / 75% / 100%（每页每个里程碑只触发一次）

### 7.4 visibility

- **触发**: `visibilitychange` 事件
- **采集数据**: `state` (visible/hidden)、`duration_visible_ms`（hidden 时记录可见时长）

### 7.5 error

- **触发**: `window.onerror` + `unhandledrejection`
- **采集数据**: `message`, `filename`, `lineno`, `colno`, `stack`（截断至 2000 字符）

---

## 8. 浏览器指纹

### 8.1 采集特征

| 特征 | 来源 | 降级值 |
|------|------|--------|
| User Agent | `navigator.userAgent` | `''` |
| Platform | `navigator.platform` | `''` |
| Language | `navigator.language` | `''` |
| CPU 核心数 | `navigator.hardwareConcurrency` | `''` |
| 设备内存 | `navigator.deviceMemory` | `''` |
| 屏幕分辨率 | `screen.width x height x colorDepth` | `''` |
| 时区偏移 | `new Date().getTimezoneOffset()` | - |
| 触摸支持 | `'ontouchstart' in window` | - |
| 浏览器厂商 | `navigator.vendor` | `''` |
| 插件列表 | `navigator.plugins` | `''` |
| Canvas 指纹 | 隐藏 canvas 渲染文字 → toDataURL 尾 64 字符 | `'canvas_err'` |
| WebGL 指纹 | `UNMASKED_VENDOR_WEBGL` + `UNMASKED_RENDERER_WEBGL` | `'no_webgl'` / `'webgl_err'` |
| Audio 指纹 | OfflineAudioContext → 4500 采样绝对值求和 | `'audio_err'` |

### 8.2 存储优先级

1. Cookie `__fp_id`（支持 `domain` 跨子域名）
2. `localStorage.__fp_id`
3. 新生成 → 同时写入 Cookie + localStorage

### 8.3 哈希算法

- 优先：`crypto.subtle.digest('SHA-256', ...)`
- 降级：纯 JS 简单哈希（兼容 IE 等无 Web Crypto API 的浏览器）

输出格式：`fp_` + 48 位十六进制字符。

---

## 9. 上报事件 JSON 格式

事件数据分为三层：用户信息 `user`、浏览器信息 `browser`、上报数据 `data`。每条事件由 SDK 自动生成唯一 `track_id`（格式 `trk_<时间戳36进制>_<序号>`）。

### 9.1 公共结构

```json
{
  "user": {
    "fingerprint_id": "fp_a3f7c2d9e1b506482a91c78f3d45e0678b2c1d9a0f4e5b6789"
  },
  "browser": {
    "user_agent": "Mozilla/5.0 ...",
    "platform": "Win32",
    "language": "zh-CN",
    "languages": ["zh-CN", "zh", "en"],
    "cookie_enabled": true,
    "do_not_track": null,
    "timezone": "Asia/Shanghai",
    "timezone_offset": -480,
    "vendor": "Google Inc.",
    "hardware_concurrency": 16,
    "device_memory": 8,
    "page_url": "http://localhost:8000/",
    "page_title": "企业智能搜索系统",
    "referrer": "",
    "screen": {
      "width": 1920, "height": 1080,
      "avail_width": 1920, "avail_height": 1040,
      "color_depth": 24, "pixel_ratio": 1.25,
      "viewport_width": 1680, "viewport_height": 920
    }
  },
  "data": {
    "track_id": "trk_m7x2a3p1_00001",
    "trackName": "page_view",
    "timestamp": "2026-06-02T12:00:00.000Z",
    "session_id": "sess_x8k2m7p1q4w9r",
    // ... 事件特有系统字段
    "custom": {
      // ... 用户自定义字段
    }
  }
}
```

### 9.2 page_view

```json
{
  "user": { "fingerprint_id": "fp_..." },
  "browser": { "...": "...", "screen": { "...": "..." } },
  "data": {
    "trackName": "page_view",
    "timestamp": "2026-06-02T12:00:00.000Z",
    "session_id": "sess_x8k2m7p1q4w9r",
    "load_time_ms": 287,
    "dom_ready_ms": 134,
    "first_paint_ms": 198,
    "dns_ms": 1, "tcp_ms": 3, "ttfb_ms": 38,
    "fetch_start_ms": 0, "redirect_count": 0,
    "navigation_type": "navigate"
  }
}
```

### 9.3 click

```json
{
  "user": { "fingerprint_id": "fp_..." },
  "browser": { "...": "...", "screen": { "...": "..." } },
  "data": {
    "trackName": "click",
    "timestamp": "2026-06-02T12:01:00.000Z",
    "session_id": "sess_...",
    "element": {
      "tag": "BUTTON", "id": "sendBtn", "class_list": "",
      "text": "", "selector": "div.input-area > button#sendBtn",
      "attributes": { "data-action": "disable", "data-idx": "0" }
    },
    "mouse": { "client_x": 1250, "client_y": 340, "page_x": 1250, "page_y": 780, "button": 0 },
    "modifiers": { "ctrl_key": false, "shift_key": false, "alt_key": false, "meta_key": false }
  }
}
```

### 9.4 scroll

```json
{
  "user": { "fingerprint_id": "fp_..." },
  "browser": { "page_url": "...", "screen": { "viewport_height": 920 } },
  "data": {
    "trackName": "scroll",
    "timestamp": "...",
    "session_id": "sess_...",
    "scroll_depth_pct": 75,
    "scroll_depth_px": 840,
    "max_scroll_pct": 75,
    "document_height": 1120,
    "viewport_height": 920,
    "milestone": 75
  }
}
```

### 9.5 visibility

```json
{
  "user": { "fingerprint_id": "fp_..." },
  "browser": { "page_url": "...", "screen": {} },
  "data": {
    "trackName": "visibility",
    "timestamp": "...",
    "session_id": "sess_...",
    "state": "hidden",
    "duration_visible_ms": 253780
  }
}
```

### 9.6 error

```json
{
  "user": { "fingerprint_id": "fp_..." },
  "browser": { "page_url": "...", "screen": {} },
  "data": {
    "trackName": "error",
    "timestamp": "...",
    "session_id": "sess_...",
    "error_type": "error | unhandledrejection | manual",
    "message": "Uncaught TypeError: Cannot read properties of null",
    "filename": "app.js",
    "lineno": 142,
    "colno": 17,
    "stack": "TypeError: ..."
  }
}
```

### 9.7 自定义事件

```json
{
  "user": { "fingerprint_id": "fp_..." },
  "browser": { "...": "...", "screen": { "...": "..." } },
  "data": {
    "trackName": "purchase",
    "timestamp": "...",
    "session_id": "sess_...",
    "label": "buy_now",
    "payload": { "product_id": 42, "amount": 99.9, "currency": "CNY" }
  }
}
```

---

## 10. 数据编码

- JSON 序列化 → UTF-8 字节 → Base64 编码 → `+` → `-`, `/` → `_`, 去 `=` → URL-safe
- 解码方向：补 `=` padding → URL-safe Base64 解码 → UTF-8 解码 → JSON 解析

```
GET /api/tracking/event?d=eyJldmVudF9pZCI6...  (URL-safe Base64)
POST /api/tracking/event  Content-Type: application/json  (原始 JSON)
```

---

## 11. 服务端接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/tracking/event?d=<base64>` | 接收 GET 模式事件 |
| `POST` | `/api/tracking/event` | 接收 POST/Beacon 模式事件 |
| `GET` | `/api/tracking/session?d=<base64>` | 会话创建/更新（GET） |
| `POST` | `/api/tracking/session` | 会话创建/更新（POST） |
| `GET` | `/api/tracking/stats?days_back=7` | 统计汇总 |
| `GET` | `/api/tracking/admin` | 埋点管理界面 |
| `GET` | `/api/tracking/admin/events` | 事件列表（支持筛选） |
| `GET` | `/api/tracking/admin/event/{id}` | 事件详情 |
| `GET` | `/api/tracking/admin/sessions` | 会话列表 |

服务端自动去重（`event_id` 唯一约束），重复事件返回 `{"saved": 0, "duplicate": true}`。

---

## 12. 数据存储

| 存储位置 | 键名 | 生命周期 | 作用域 |
|----------|------|----------|--------|
| Cookie | `__fp_id` | cookieDays 配置（默认 365 天） | domain 配置决定 |
| localStorage | `__fp_id` | 永久（除非清除） | 当前域名 |
| sessionStorage | `__track_sid` | 标签页关闭 | 当前标签页 |
| sessionStorage | `__track_cnt` | 标签页关闭 | 当前标签页 |
| sessionStorage | `__track_start` | 标签页关闭 | 当前标签页 |

后端存储表：

- `tracking_events` — 事件明细（event_id 唯一索引，track_name / fingerprint_id / session_id / timestamp 独立列便于查询，完整 JSON 存 payload）
- `tracking_sessions` — 会话汇总（session_id 主键，含 user_agent、browser_info、screen_info、起止时间、事件计数）

---

## 13. 兼容性

| 浏览器 | 指纹 | 自动采集 | 备注 |
|--------|------|----------|------|
| Chrome 80+ | 完整 | 完整 | - |
| Firefox 80+ | 完整 | 完整 | - |
| Safari 14+ | 完整 | 完整 | Audio 指纹需用户手势后可用 |
| Edge 80+ | 完整 | 完整 | - |
| IE 11 | 降级 | 降级 | Canvas 正常，WebGL/Audio 降级，事件用 attachEvent |
| IE 10 | 降级 | 降级 | 同上 |
| 移动端 Chrome/Safari | 完整 | 完整 | scroll 使用 passive 监听 |

---

## 14. 典型场景

### 14.1 常规 Web 页面

```html
<script src="/static/tracker.js"></script>
```
零配置，自动采集所有事件。

### 14.2 SPA 应用

```html
<script>
window.__TrackerSDK_noAuto = true;
</script>
<script src="/static/tracker.js"></script>
<script>
var tracker = new __TrackerSDK({ mode: 'manual', sendMode: 'post' });

// 路由切换时手动上报页面浏览
router.afterEach(function () {
  tracker.trackPageView();
});

// 关键操作手动上报
tracker.track('search', { label: 'keyword', payload: { query: '张鹏' } });
</script>
```

### 14.3 跨子域名统一

```html
<!-- a.example.com / b.example.com 均使用相同配置 -->
<script>
window.__TrackerSDK_noAuto = true;
</script>
<script src="/static/tracker.js"></script>
<script>
new __TrackerSDK({ cookieDomain: '.example.com', sendMode: 'post' });
</script>
```

同一用户在 `a.example.com` 和 `b.example.com` 的 `fingerprint_id` 一致。

### 14.4 ES Module 引入

```javascript
import TrackerSDK from './tracker.js';

const tracker = new TrackerSDK({
  mode: 'manual',
  sendMode: 'beacon',
  debug: true,
});

tracker.track('page_ready', { label: 'home' });
```

### 14.5 错误边界上报

```javascript
try {
  await apiCall();
} catch (e) {
  window.__tracker.trackError(e.message, e.stack);
  window.__tracker.track('api_error', {
    payload: { endpoint: '/api/chat', status: e.status },
  });
}
```
