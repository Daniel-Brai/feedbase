/**
 * pagination.js  v0.1.0
 *
 * A HTMX v2 extension for cursor, page, and offset-based pagination with
 * micro-template rendering, infinite scroll, and SSE‑driven background
 * reconciliation
 *
 *   ## REQUIRED
 * 
 *   pagination-url             Relative ("/api/items") or absolute ("https://…")
 *   pagination-template        ID of the <template> element used per item
 *
 *   ## PAGINATION MODE
 *   pagination-mode            "cursor" (default) | "page" | "offset"
 *   pagination-limit           Items per request. Default: 20
 *   pagination-limit-param     Default: "limit"
 *   pagination-cursor-param    Default: "cursor"
 *   pagination-page-param      Default: "page"
 *   pagination-offset-param    Default: "offset"
 *
 *   ## RESPONSE SHAPE (dot-paths into the JSON response)
 *   pagination-data-field      Path to the items array. Default: "data"
 *   pagination-cursor-field    Path to the next cursor. Default: "next_cursor"
 *   pagination-has-more-field  Path to boolean. Default: "has_more"
 *   pagination-total-field     Path to total count. Default: "total"
 *
 *   ## RENDERING
 *   pagination-custom-render   "true" → skip DOM manipulation; use events only.
 *   pagination-target          CSS selector override for the insert container
 *   pagination-append-mode     "append" (default) | "prepend" | "replace"
 *   pagination-template        Item template ID (ignored if custom render)
 *   pagination-error-template  Error template ID (ignored if custom render)
 *   pagination-empty-template  Empty template ID (ignored if custom render)
 *   pagination-loading-template Loading skeleton (ignored if custom render)
 *
 *   ## TEMPLATE SYNTAX (only when not using custom render)
 *   [[field]]                   HTML-escaped interpolation
 *   [[[field]]]                 Raw HTML interpolation (unescaped)
 *   [[object.nested.key]]       Dot-path field access
 *   [[#if field]]…[[/if]]       Conditional block
 *   [[#each arrayField]]…[[/each]]  Iteration block
 *     [[@index]]                Zero-based loop index
 *     [[@parent.field]]         Access outer scope from inside #each
 *
 *   ## NETWORK
 *   pagination-method           HTTP method. Default: "GET"
 *   pagination-headers          JSON object of extra request headers
 *   pagination-params           JSON object of static extra query params
 *   pagination-retry-limit      Auto-retry count on error. Default: 0
 *   pagination-retry-delay      Retry delay in ms. Default: 1000
 *
 *   ## BEHAVIOUR 
 *   pagination-infinite         "true" : IntersectionObserver infinite scroll
 *   pagination-autoload         "false" : skip auto-loading the first page
 *   pagination-threshold        IO threshold. Default: 0.1
 *
 *   ## LIVE REFRESH (SSE)
 *   pagination-refresh-stream   URL of the SSE endpoint.
 *   pagination-refresh-stream-with-credentials  "true" to send cookies / auth
 *   pagination-refresh-stream-shared  "true" : share one EventSource among multiple components
 *   pagination-refresh-stream-event-transformer  Function | null
 *                               Global function path. Receives (parsedPayload, rawEvent)
 *                               and must return { id: "..." } or falsy to ignore.
 *                               For shared streams, the first component's transformer is used.
 *
 *   pagination-item-key         Item field used for DOM reconciliation. Default: "id".
 *
 *   SSE server push format:
 *     event: htmx-pagination:refresh\n
 *     data: {"id":"<element-id>"}\n\n
 *
 *   ## DOM MARKERS (boolean attributes no value needed)
 *   pagination-list             Items container (ignored if custom render)
 *   pagination-trigger          Clickable element that calls loadMore()
 *   pagination-sentinel         Custom IO anchor for infinite scroll
 *   pagination-end              Shown when hasMore becomes false (ignored if custom render)
 *   pagination-loading-indicator Shown while a fetch is in flight (ignored if custom render)
 *
 *   ## EVENTS (bubble on root element; detail includes { controller, state })
 * 
 *   pagination:before-load      detail: { params }
 *   pagination:after-load       detail: { items, response, totalLoaded }
 *   pagination:error            detail: { error }
 *   pagination:end              detail: { totalLoaded }
 *   pagination:reset
 *   pagination:destroy
 *   pagination:refresh-start
 *   pagination:refresh-end      detail: { items }
 *   pagination:refresh-error    detail: { error }
 *   pagination:stream-connected detail: { url, type }
 *
 *   ## JS API
 * 
 *   htmx.pagination.getInstance(el)   - controller
 *   htmx.pagination.mount(el)         - controller
 *   htmx.pagination.render(tpl, data) - string (proxy to htmx.template.render)
 *   htmx.pagination.silentRefresh(el) - void
 * 
 *   ### Controller API
 *   controller.loadMore(), .reset(), .reload(), .setParams(), .setUrl(), .configure(), .destroy()
 */

(function (htmx) {
    "use strict";

    function resolveGlobalFunction(path) {
        if (!path || typeof path !== "string") return null;
        var parts = path.split(".");
        var obj = window;
        for (var i = 0; i < parts.length; i++) {
            if (obj == null) return null;
            obj = obj[parts[i]];
        }
        return typeof obj === "function" ? obj : null;
    }

    function resolvePath(obj, path) {
        if (path === "this") return obj;
        return path.split(".").reduce(function (acc, k) {
            return acc != null ? acc[k] : undefined;
        }, obj);
    }

    function render(tpl, data, extra) {
        if (htmx && htmx.template && typeof htmx.template.render === "function") {
            return htmx.template.render(tpl, data, extra);
        }
        return tpl;
    }

    var ABS_URL_RE = /^https?:\/\//i;

    function buildUrl(base, params) {
        var resolved = ABS_URL_RE.test(base)
            ? new URL(base)
            : new URL(base, window.location.href);

        var keys = Object.keys(params);
        for (var i = 0; i < keys.length; i++) {
            var v = params[keys[i]];
            if (v !== undefined && v !== null && v !== "")
                resolved.searchParams.set(keys[i], String(v));
        }
        return resolved.toString();
    }

    function syncAttributes(oldEl, newEl) {
        var newAttrs = newEl.attributes;
        for (var i = 0; i < newAttrs.length; i++) {
            var a = newAttrs[i];
            if (oldEl.getAttribute(a.name) !== a.value)
                oldEl.setAttribute(a.name, a.value);
        }
        var oldAttrs = oldEl.attributes;
        for (var j = oldAttrs.length - 1; j >= 0; j--) {
            var name = oldAttrs[j].name;
            if (!newEl.hasAttribute(name)) {
                if (
                    name === "style" &&
                    (oldEl.hasAttribute("x-show") || oldEl.hasAttribute("x-data") || newEl.hasAttribute("x-show") || newEl.hasAttribute("x-data"))
                ) {
                    continue;
                }
                oldEl.removeAttribute(name);
            }
        }
    }

    function patchNode(oldNode, newNode) {
        if (oldNode.nodeType !== 1) {
            if (oldNode.nodeValue !== newNode.nodeValue)
                oldNode.nodeValue = newNode.nodeValue;
            return;
        }

        if (oldNode.tagName !== newNode.tagName) {
            oldNode.parentNode.replaceChild(newNode.cloneNode(true), oldNode);
            return;
        }

        syncAttributes(oldNode, newNode);

        var oldKids = Array.from(oldNode.childNodes);
        var newKids = Array.from(newNode.childNodes);
        var max = Math.max(oldKids.length, newKids.length);

        for (var i = 0; i < max; i++) {
            var o = oldKids[i];
            var n = newKids[i];

            if (!o) { oldNode.appendChild(n.cloneNode(true)); continue; }
            if (!n) { oldNode.removeChild(o); continue; }

            if (
                o.nodeType !== n.nodeType ||
                (o.nodeType === 1 && o.tagName !== n.tagName)
            ) {
                oldNode.replaceChild(n.cloneNode(true), o);
                continue;
            }

            patchNode(o, n);
        }
    }

    class PaginationState {
        constructor(config) {
            this.config = config;
            this.cursor = null;
            this.page = 1;
            this.offset = 0;
            this.hasMore = true;
            this.loading = false;
            this.totalLoaded = 0;
            this.error = null;
        }

        buildRequestParams() {
            var c = this.config;
            var params = {};
            params[c.limitParam] = c.limit;

            if (c.mode === "cursor") {
                if (this.cursor) params[c.cursorParam] = this.cursor;
            } else if (c.mode === "page") {
                params[c.pageParam] = this.page;
            } else {
                params[c.offsetParam] = this.offset;
            }

            return Object.assign({}, c.extraParams, params);
        }

        advance(response) {
            var c = this.config;

            if (c.mode === "cursor") {
                var nextCursor = resolvePath(response, c.cursorField);
                if (c.hasMoreField) {
                    var hm = resolvePath(response, c.hasMoreField);
                    this.hasMore =
                        hm !== undefined
                            ? !!hm
                            : nextCursor != null && nextCursor !== "";
                } else {
                    this.hasMore = nextCursor != null && nextCursor !== "";
                }
                this.cursor = nextCursor || null;
            } else if (c.mode === "page") {
                this.page += 1;
                if (c.hasMoreField && resolvePath(response, c.hasMoreField) !== undefined) {
                    this.hasMore = !!resolvePath(response, c.hasMoreField);
                } else if (c.totalField) {
                    this.hasMore =
                        this.totalLoaded < (resolvePath(response, c.totalField) || 0);
                }
            } else {
                this.offset += c.limit;
                if (c.hasMoreField && resolvePath(response, c.hasMoreField) !== undefined) {
                    this.hasMore = !!resolvePath(response, c.hasMoreField);
                } else if (c.totalField) {
                    this.hasMore =
                        this.offset < (resolvePath(response, c.totalField) || 0);
                }
            }
        }

        reset() {
            this.cursor = null;
            this.page = 1;
            this.offset = 0;
            this.hasMore = true;
            this.loading = false;
            this.totalLoaded = 0;
            this.error = null;
        }
    }


    var _sharedStreamManagers = new Map();

    class PaginationController {
        constructor(el) {
            this.el = el;
            this.config = this._parseConfig(el);
            this.state = new PaginationState(this.config);
            this._observer = null;
            this._eventSource = null;
            this._sharedManagerKey = null;
            this._refreshing = false;
            this._retryCount = 0;
            this._init();
        }

        _parseConfig(el) {
            function attr(name, fallback) {
                return el.getAttribute("pagination-" + name) || fallback;
            }
            function jsonAttr(name, fallback) {
                var raw = el.getAttribute("pagination-" + name);
                if (!raw) return fallback;
                try {
                    return JSON.parse(raw);
                } catch (e) {
                    console.error("[pagination] Invalid JSON in pagination-" + name, e);
                    return fallback;
                }
            }
            function boolAttr(name, fallback) {
                var raw = el.getAttribute("pagination-" + name);
                if (raw === null) return fallback;
                return raw !== "false";
            }

            var transformerPath = attr("refresh-stream-event-transformer", null);
            var refreshTransformer = null;
            if (transformerPath) {
                refreshTransformer = resolveGlobalFunction(transformerPath);
                if (!refreshTransformer) {
                    console.warn("[pagination] Could not resolve transformer function: " + transformerPath);
                }
            }

            return {
                url: attr("url", ""),
                mode: attr("mode", "cursor"),
                method: attr("method", "GET").toUpperCase(),
                limit: parseInt(attr("limit", "20"), 10),
                limitParam: attr("limit-param", "limit"),
                cursorParam: attr("cursor-param", "cursor"),
                pageParam: attr("page-param", "page"),
                offsetParam: attr("offset-param", "offset"),
                cursorField: attr("cursor-field", "next_cursor"),
                hasMoreField: attr("has-more-field", "has_more"),
                totalField: attr("total-field", "total"),
                dataField: attr("data-field", "data"),
                template: attr("template", null),
                errorTemplate: attr("error-template", null),
                emptyTemplate: attr("empty-template", null),
                loadingTemplate: attr("loading-template", null),
                target: attr("target", null),
                appendMode: attr("append-mode", "append"),
                infinite: boolAttr("infinite", false),
                autoload: boolAttr("autoload", true),
                threshold: parseFloat(attr("threshold", "0.1")),
                retryLimit: parseInt(attr("retry-limit", "0"), 10),
                retryDelay: parseInt(attr("retry-delay", "1000"), 10),
                headers: jsonAttr("headers", {}),
                extraParams: jsonAttr("params", {}),
                refreshStream: attr("refresh-stream", null),
                refreshStreamWithCredentials: boolAttr("refresh-stream-with-credentials", false),
                refreshShared: boolAttr("refresh-stream-shared", false),
                refreshTransformer: refreshTransformer,
                itemKey: attr("item-key", "id"),
                customRender: boolAttr("custom-render", false),
            };
        }

        _getTarget() {
            if (this.config.target) {
                return document.querySelector(this.config.target) || this.el;
            }
            return this.el.querySelector("[pagination-list]") || this.el;
        }

        _getTemplate(id) {
            if (!id) return null;
            var el = document.getElementById(id);
            if (!el) {
                console.warn("[pagination] Template element not found: #" + id);
                return null;
            }
            if (el.tagName === "TEMPLATE") {
                var scratch = document.createElement("div");
                scratch.appendChild(el.content.cloneNode(true));
                return scratch.innerHTML;
            }
            return el.innerHTML;
        }

        _emit(name, detail) {
            detail = Object.assign(
                { controller: this, state: this.state },
                detail || {},
            );
            var ev = new CustomEvent("pagination:" + name, {
                detail: detail,
                bubbles: true,
                cancelable: true,
            });
            return this.el.dispatchEvent(ev);
        }

        _setLoading(on) {
            this.state.loading = on;
            this.el.toggleAttribute("pagination-loading", on);

            var btn = this.el.querySelector("[pagination-trigger]");
            if (btn) {
                btn.disabled = on;
                if (on) btn.setAttribute("aria-busy", "true");
                else btn.removeAttribute("aria-busy");
            }

            var ind = this.el.querySelector("[pagination-loading-indicator]");
            if (ind) ind.style.display = on ? "" : "none";

            if (!this.config.customRender && this.config.loadingTemplate && on) {
                var tpl = this._getTemplate(this.config.loadingTemplate);
                if (tpl) this._getTarget().insertAdjacentHTML("beforeend", tpl);
            }
        }

        _renderItemToElement(item) {
            var tplHtml = this._getTemplate(this.config.template);
            if (!tplHtml) return null;
            var wrap = document.createElement("div");
            wrap.innerHTML = render(tplHtml, item);
            var el = wrap.firstElementChild;
            if (!el) return null;
            var keyVal = resolvePath(item, this.config.itemKey);
            if (keyVal !== undefined && keyVal !== null)
                el.setAttribute("data-pagination-key", String(keyVal));
            return el;
        }

        _renderItemsToElements(items) {
            var self = this;
            var els = [];
            for (var i = 0; i < items.length; i++) {
                var el = self._renderItemToElement(items[i]);
                if (el) els.push(el);
            }
            return els;
        }

        _renderItems(items) {
            if (this.config.customRender) return;
            var target = this._getTarget();
            target.querySelectorAll("[pagination-skeleton]").forEach(function (s) {
                s.remove();
            });

            var elements = this._renderItemsToElements(items);
            var frag = document.createDocumentFragment();
            elements.forEach(function (el) { frag.appendChild(el); });

            if (this.config.appendMode === "prepend")
                target.insertBefore(frag, target.firstChild);
            else if (this.config.appendMode === "replace") {
                target.innerHTML = "";
                target.appendChild(frag);
            } else {
                target.appendChild(frag);
            }

            if (typeof htmx !== "undefined") htmx.process(target);
            if (typeof window !== "undefined" && window.Alpine && typeof window.Alpine.initTree === "function") {
                window.Alpine.initTree(target);
            }
        }

        _renderError(err) {
            if (this.config.customRender) return;
            var tplHtml = this._getTemplate(this.config.errorTemplate);
            if (!tplHtml) return;
            var body = err.body || {};
            var detailText = body.detail || body.message || err.detail || err.message || String(err);
            var ctx = {
                detail: detailText,
                message: err.message || detailText,
                title: err.title || "Error",
                status: String(err.status || ""),
                type: err.type || "error",
                errors: (err.errors || [])
                    .map(function (e) { return e.message || e; })
                    .join("; "),
            };
            this._getTarget().insertAdjacentHTML("beforeend", render(tplHtml, ctx));
        }

        _renderEmpty() {
            if (this.config.customRender) return;
            var tplHtml = this._getTemplate(this.config.emptyTemplate);
            if (!tplHtml) return;
            this._getTarget().innerHTML = render(tplHtml, {});
        }

        _updateControls() {
            if (this.config.customRender) return;
            var btn = this.el.querySelector("[pagination-trigger]");
            if (btn) {
                btn.style.display = this.state.hasMore ? "" : "none";
                btn.disabled = !this.state.hasMore;
            }
            var endEl = this.el.querySelector("[pagination-end]");
            if (endEl) endEl.style.display = this.state.hasMore ? "none" : "";
        }

        _reconcile(target, newElements) {
            if (this.config.customRender) return;

            function isAlpineElement(el) {
                return (
                    el &&
                    (el.hasAttribute("x-data") ||
                        el.hasAttribute("x-show") ||
                        el.hasAttribute("x-text") ||
                        el.hasAttribute("x-model") ||
                        el.hasAttribute("x-bind") ||
                        el.hasAttribute("x-on"))
                );
            }

            var oldByKey = Object.create(null);
            var oldChildren = Array.from(target.children);
            for (var i = 0; i < oldChildren.length; i++) {
                var k = oldChildren[i].getAttribute("data-pagination-key");
                if (k) oldByKey[k] = oldChildren[i];
            }

            var seen = Object.create(null);
            var hasKeys = false;
            for (var ni = 0; ni < newElements.length; ni++) {
                if (newElements[ni].getAttribute("data-pagination-key")) {
                    hasKeys = true;
                    break;
                }
            }

            if (!hasKeys) {
                for (var ni = 0; ni < newElements.length; ni++) {
                    var newEl = newElements[ni];
                    var oldEl = target.children[ni];
                    if (oldEl) {
                        if (isAlpineElement(oldEl) || isAlpineElement(newEl)) {
                            target.replaceChild(newEl, oldEl);
                        } else {
                            patchNode(oldEl, newEl);
                        }
                    } else {
                        target.appendChild(newEl);
                    }
                }
                while (target.children.length > newElements.length) {
                    target.removeChild(target.lastChild);
                }
            } else {
                for (var ni = 0; ni < newElements.length; ni++) {
                    var newEl = newElements[ni];
                    var newKey = newEl.getAttribute("data-pagination-key");
                    var anchor = target.children[ni] || null;

                    if (newKey && oldByKey[newKey]) {
                        var oldEl = oldByKey[newKey];
                        seen[newKey] = true;
                        if (isAlpineElement(oldEl) || isAlpineElement(newEl)) {
                            target.replaceChild(newEl, oldEl);
                        } else {
                            patchNode(oldEl, newEl);
                            if (target.children[ni] !== oldEl)
                                target.insertBefore(oldEl, anchor);
                        }
                    } else {
                        if (newKey) seen[newKey] = true;
                        target.insertBefore(newEl, anchor);
                    }
                }

                for (var key in oldByKey) {
                    if (!seen[key]) target.removeChild(oldByKey[key]);
                }
            }

            if (typeof htmx !== "undefined") htmx.process(target);
            if (typeof window !== "undefined" && window.Alpine && typeof window.Alpine.initTree === "function") {
                window.Alpine.initTree(target);
            }
        }

        silentRefresh() {
            var self = this;
            var config = self.config;
            var state = self.state;

            if (self._refreshing || state.totalLoaded === 0) return;
            self._refreshing = true;
            self._emit("refresh-start");

            var params = Object.assign({}, config.extraParams);
            params[config.limitParam] = config.limit;

            if (config.mode === "offset") params[config.offsetParam] = 0;
            else if (config.mode === "page") params[config.pageParam] = 1;

            var url = buildUrl(config.url, params);

            fetch(url, {
                method: "GET",
                headers: Object.assign({ Accept: "application/json" }, config.headers),
            })
                .then(function (res) {
                    if (!res.ok) throw new Error("HTTP " + res.status);
                    return res.json();
                })
                .then(function (data) {
                    var items = config.dataField
                        ? resolvePath(data, config.dataField)
                        : data;
                    if (!Array.isArray(items)) return;

                    if (config.customRender) {
                        self._emit("refresh-end", { items: items });
                    } else {
                        var target = self._getTarget();
                        var newElements = self._renderItemsToElements(items);
                        self._reconcile(target, newElements);
                        state.totalLoaded = items.length;
                        self._emit("refresh-end", { items: items });
                    }
                })
                .catch(function (err) {
                    console.warn("[pagination] Silent refresh failed:", err);
                    self._emit("refresh-error", { error: err });
                })
                .finally(function () {
                    self._refreshing = false;
                });
        }

        _registerSharedStream() {
            var url = this.config.refreshStream;
            if (!url) return;
            var resolvedUrl = buildUrl(url, {});
            var withCreds = this.config.refreshStreamWithCredentials;
            var key = resolvedUrl + "|" + withCreds;
            var manager = _sharedStreamManagers.get(key);
            var self = this;

            if (!manager) {
                var es = new EventSource(resolvedUrl, { withCredentials: withCreds });
                var controllers = new Set();
                var transformer = this.config.refreshTransformer; // first controller's transformer
                manager = {
                    eventSource: es,
                    controllers: controllers,
                    url: resolvedUrl,
                    withCredentials: withCreds,
                    transformer: transformer
                };
                _sharedStreamManagers.set(key, manager);

                var handleSharedRefreshEvent = function (evt) {
                    var payload;
                    try {
                        payload = JSON.parse(evt.data);
                    } catch (e) {
                        console.warn("[pagination] Invalid JSON in shared SSE data", evt.data);
                        return;
                    }

                    var effectivePayload = payload;
                    if (manager.transformer) {
                        try {
                            var transformed = manager.transformer(payload, evt);
                            if (!transformed) return;
                            effectivePayload = transformed;
                        } catch (err) {
                            console.error("[pagination] Transformer in shared stream threw an error", err);
                            return;
                        }
                    } else if (
                        payload &&
                        payload.event === "htmx-pagination:refresh" &&
                        payload.id
                    ) {
                        effectivePayload = payload;
                    } else if (
                        payload &&
                        payload.data &&
                        payload.data.event === "htmx-pagination:refresh" &&
                        payload.data.id
                    ) {
                        effectivePayload = payload.data;
                    }

                    var eventId = effectivePayload && effectivePayload.id;
                    if (!eventId) return;

                    var controllersCopy = Array.from(controllers);
                    for (var i = 0; i < controllersCopy.length; i++) {
                        var ctrl = controllersCopy[i];
                        if (ctrl.el.id === eventId) {
                            ctrl.silentRefresh();
                        }
                    }
                };

                es.addEventListener("htmx-pagination:refresh", handleSharedRefreshEvent);
                es.addEventListener("message", handleSharedRefreshEvent);

                es.addEventListener("error", function () {
                    if (es.readyState === EventSource.CLOSED) {
                        console.warn("[pagination] Shared SSE stream closed:", resolvedUrl);
                    }
                });

                // Emit stream-connected on the first controller that created the manager
                this._emit("stream-connected", { url: resolvedUrl, type: "sse" });
            } else {
                // Manager already exists, we check if the transformer exists and is the same transformer function. 
                // If not, we warn that the new transform will be ignored, and the existing one will be used for all controllers sharing the stream.
                var existingTransformer = manager.transformer;
                var myTransformer = this.config.refreshTransformer;
                if ((existingTransformer || myTransformer) && existingTransformer !== myTransformer) {
                    console.warn(
                        "[pagination] Shared stream at " + resolvedUrl +
                        " already has a transformer. Ignoring different transformer from component " +
                        this.el.id
                    );
                }
            }
            manager.controllers.add(this);
            this._sharedManagerKey = key;
        }

        _unregisterSharedStream() {
            if (this._sharedManagerKey) {
                var manager = _sharedStreamManagers.get(this._sharedManagerKey);
                if (manager) {
                    manager.controllers.delete(this);
                    if (manager.controllers.size === 0) {
                        manager.eventSource.close();
                        _sharedStreamManagers.delete(this._sharedManagerKey);
                    }
                }
                this._sharedManagerKey = null;
            }
        }

        _connectSSEStream() {
            var self = this;
            var resolvedUrl = buildUrl(self.config.refreshStream, {});
            var es = new EventSource(resolvedUrl, { withCredentials: self.config.refreshStreamWithCredentials });
            self._eventSource = es;

            var transformer = self.config.refreshTransformer;

            var handleRefreshEvent = function (evt) {
                var payload;
                try {
                    payload = JSON.parse(evt.data);
                } catch (e) {
                    console.warn("[pagination] Invalid JSON in SSE data", evt.data);
                    return;
                }

                var effectivePayload = payload;
                if (transformer) {
                    try {
                        var transformed = transformer(payload, evt);
                        if (!transformed) return;
                        effectivePayload = transformed;
                    } catch (err) {
                        console.error("[pagination] Transformer function threw an error", err);
                        return;
                    }
                } else if (
                    payload &&
                    payload.event === "htmx-pagination:refresh" &&
                    payload.id
                ) {
                    effectivePayload = payload;
                } else if (
                    payload &&
                    payload.data &&
                    payload.data.event === "htmx-pagination:refresh" &&
                    payload.data.id
                ) {
                    effectivePayload = payload.data;
                }

                if (effectivePayload.id && effectivePayload.id !== self.el.id) return;
                self.silentRefresh();
            };

            es.addEventListener("htmx-pagination:refresh", handleRefreshEvent);
            es.addEventListener("message", handleRefreshEvent);

            es.addEventListener("error", function () {
                if (es.readyState === EventSource.CLOSED) {
                    console.warn("[pagination] SSE stream closed:", resolvedUrl);
                }
            });

            self._emit("stream-connected", { url: resolvedUrl, type: "sse" });
        }

        _connectRefreshStream() {
            if (!this.config.refreshStream) return;
            if (this.config.refreshShared) {
                this._registerSharedStream();
            } else {
                this._connectSSEStream();
            }
        }

        async loadMore() {
            if (this.state.loading || !this.state.hasMore)
                return Promise.resolve();

            var self = this;
            var config = this.config;
            var state = this.state;

            var params = state.buildRequestParams();

            self._setLoading(true);
            self._emit("before-load", { params: params });

            var sendInUrl = config.method === "GET" || config.method === "HEAD";
            var url = buildUrl(config.url, sendInUrl ? params : {});

            var fetchOpts = {
                method: config.method,
                headers: Object.assign({ Accept: "application/json" }, config.headers),
            };
            if (!sendInUrl) {
                fetchOpts.headers["Content-Type"] = "application/json";
                fetchOpts.body = JSON.stringify(params);
            }

            try {
                var res = await fetch(url, fetchOpts);

                if (!res.ok) {
                    var body = await res.text();
                    var parsed;
                    try { parsed = JSON.parse(body); }
                    catch (e) { parsed = { message: body }; }
                    throw Object.assign(
                        new Error(parsed.message || parsed.error || "HTTP " + res.status),
                        { status: res.status, body: parsed, type: "http" },
                    );
                }

                var data = await res.json();

                var items = config.dataField
                    ? resolvePath(data, config.dataField)
                    : data;
                if (!Array.isArray(items)) {
                    throw new Error(
                        '[pagination] "' + config.dataField + '" is ' + typeof items +
                        ", expected array. Verify pagination-data-field.",
                    );
                }

                state.totalLoaded += items.length;
                state.advance(data);
                state.error = null;
                self._retryCount = 0;

                if (state.totalLoaded === 0) {
                    self._renderEmpty();
                } else {
                    self._renderItems(items);
                }

                self._updateControls();
                self._emit("after-load", {
                    items: items,
                    response: data,
                    totalLoaded: state.totalLoaded,
                });

                if (!state.hasMore) {
                    self._emit("end", { totalLoaded: state.totalLoaded });
                    if (self._observer) {
                        self._observer.disconnect();
                        self._observer = null;
                    }
                }
            } catch (err) {
                state.error = err;
                self._emit("error", { error: err });
                console.error("[pagination]", err);

                if (self._retryCount < config.retryLimit) {
                    self._retryCount++;
                    console.log(
                        "[pagination] Retry " +
                        self._retryCount + "/" + config.retryLimit + "…",
                    );
                    return new Promise(function (resolve) {
                        setTimeout(function () { resolve(self.loadMore()); }, config.retryDelay);
                    });
                }

                self._renderError(err);
            } finally {
                self._setLoading(false);
            }
        }

        reset() {
            this._getTarget().innerHTML = "";
            this.state.reset();
            this._retryCount = 0;
            this._updateControls();
            this._emit("reset");
            if (this.config.infinite) this._setupInfiniteScroll();
            if (this.config.autoload) this.loadMore();
            return this;
        }

        reload() {
            return this.reset();
        }

        setParams(newParams) {
            var merged = Object.assign({}, this.config.extraParams);
            var keys = Object.keys(newParams);
            for (var i = 0; i < keys.length; i++) {
                if (newParams[keys[i]] === undefined) delete merged[keys[i]];
                else merged[keys[i]] = newParams[keys[i]];
            }
            this.config.extraParams = merged;
            return this.reset();
        }

        setUrl(url) {
            this.config.url = url;
            return this.reset();
        }

        configure(changes) {
            if ("url" in changes) this.config.url = changes.url;
            if ("params" in changes) {
                var merged = Object.assign({}, this.config.extraParams);
                var keys = Object.keys(changes.params || {});
                for (var i = 0; i < keys.length; i++) {
                    if (changes.params[keys[i]] === undefined) delete merged[keys[i]];
                    else merged[keys[i]] = changes.params[keys[i]];
                }
                this.config.extraParams = merged;
            }
            return this.reset();
        }

        destroy() {
            if (this._observer) { this._observer.disconnect(); this._observer = null; }
            if (this._eventSource) { this._eventSource.close(); this._eventSource = null; }
            if (this.config.refreshShared) {
                this._unregisterSharedStream();
            }
            this._emit("destroy");
        }

        _setupInfiniteScroll() {
            var self = this;
            if (self._observer) {
                self._observer.disconnect();
                self._observer = null;
            }

            var sentinel = self.el.querySelector("[pagination-sentinel]");
            if (!sentinel) {
                sentinel = document.createElement("div");
                sentinel.setAttribute("pagination-sentinel", "");
                sentinel.setAttribute("aria-hidden", "true");
                sentinel.style.cssText = "height:2px;width:100%;pointer-events:none;";
                self.el.appendChild(sentinel);
            }

            var observerOptions = {
                threshold: self.config.threshold,
                root: self.el,
                rootMargin: "0px 0px 100px 0px",
            };

            self._observer = new IntersectionObserver(
                function (entries) {
                    if (
                        entries[0].isIntersecting &&
                        !self.state.loading &&
                        self.state.hasMore
                    )
                        self.loadMore();
                },
                observerOptions,
            );

            self._observer.observe(sentinel);
        }

        _init() {
            var self = this;

            if (!self.config.url) {
                console.error("[pagination] pagination-url is required.");
                return;
            }

            var btn = self.el.querySelector("[pagination-trigger]");
            if (btn)
                btn.addEventListener("click", function () { self.loadMore(); });

            var endEl = self.el.querySelector("[pagination-end]");
            if (endEl) endEl.style.display = "none";

            var ind = self.el.querySelector("[pagination-loading-indicator]");
            if (ind) ind.style.display = "none";

            if (self.config.infinite) self._setupInfiniteScroll();
            if (self.config.refreshStream) self._connectRefreshStream();
            if (self.config.autoload) self.loadMore();
        }
    }

    var registry = new WeakMap();

    function mountController(el) {
        if (registry.has(el)) return registry.get(el);
        var ctrl = new PaginationController(el);
        registry.set(el, ctrl);
        return ctrl;
    }

    function tryMount(node) {
        if (!node || !node.getAttribute) return;
        var ext = node.getAttribute("hx-ext") || "";
        if (ext.split(/[\s,]+/).indexOf("pagination") !== -1)
            mountController(node);
    }

    htmx.defineExtension("pagination", {
        onEvent: function (name, evt) {
            if (name !== "htmx:afterProcessNode") return;
            var el = evt.detail.elt;
            tryMount(el);
            if (el.querySelectorAll) {
                var nodes = el.querySelectorAll("[hx-ext]");
                for (var i = 0; i < nodes.length; i++) tryMount(nodes[i]);
            }
        },
    });

    htmx.pagination = {
        getInstance: function (el) { return registry.get(el) || null; },
        mount: mountController,
        render: render,
        silentRefresh: function (el) {
            var c = registry.get(el);
            if (c) c.silentRefresh();
        },
    };

})(window.htmx);