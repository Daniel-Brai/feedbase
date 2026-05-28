export const HTMLUtils = (function () {
    "use strict";

    const JS_COMPONENTS = new Set(["toast", "alert", "modal", "no-op"]);

    function cancelForm(btn) {
        if (btn.closest(".fb-modal-backdrop")) {
            cancelModalForm(btn);
            return;
        }

        var form = btn.closest("form");
        if (!form) {
            console.warn("utils/html.js: no parent <form> found.");
            return;
        }

        var target = form.dataset["cancelTarget"];
        var restoreHtml = form.dataset["cancelRestore"];

        if (!target || !restoreHtml) {
            console.warn(
                "utils/html.js: form is missing data-cancel-target or data-cancel-restore. " +
                "Set cancel_target and cancel_restore_html in your FormConfigDict.",
            );
            return;
        }

        var container = document.querySelector(target);
        if (!container) {
            console.warn(`utils/html.js: target element "${target}" not found`);
            return;
        }

        while (container.firstChild) {
            container.removeChild(container.firstChild);
        }
        container.insertAdjacentHTML("afterbegin", restoreHtml);

        if (window.htmx) {
            window.htmx.process(container);
        }
    }

    function cancelModalForm(btn) {
        const modalBackdrop = btn.closest(".fb-modal-backdrop");
        if (!modalBackdrop) {
            cancelForm(btn);
            return;
        }
        if (window.Modal && window.Modal.hide) {
            window.Modal.hide(modalBackdrop);
        } else {
            modalBackdrop.parentNode?.removeChild(modalBackdrop);
            document.body.style.overflow = "";
        }
    }

    function handleFormSuccess(form, xhr, responseData) {
        let ctx = _readFormContext(form, "successContext");
        if (!ctx) return;

        const payload = { response: responseData, error: responseData, ...responseData };

        if (typeof ctx.condition === "string") {
            const conditionSatisfied = _evaluateCondition(ctx.condition, payload);
            if (conditionSatisfied) {
                if (ctx.fallback && typeof ctx.fallback === "object") {
                    ctx = ctx.fallback;
                } else {
                    return;
                }
            }
        }

        if (ctx?.context?.auto_clear_form) {
            form.reset();
        }

        const name = String(ctx.name || "");
        const resolvedCtx = _resolveFormContext(ctx.context || {}, payload);

        const hxRedirect = xhr.getResponseHeader("HX-Redirect");
        const hxLocation = xhr.getResponseHeader("HX-Location");

        if (!hxRedirect && !hxLocation && ctx.redirect_to) {
            var delay = (ctx.redirect_delay_secs || 0) * 1000;
            setTimeout(function () {
                window.location.href = ctx.redirect_to;
            }, delay);
        }

        if (!JS_COMPONENTS.has(name)) return;
        _dispatchCtxForForm(form.id, name, resolvedCtx);

        if (resolvedCtx?.auto_close_form) {
            const selector = resolvedCtx.auto_close_form_with_selector;
            if (selector) {
                const selectorEl = document.querySelector(selector);
                if (selectorEl) {
                    if (selectorEl.closest(".fb-modal-backdrop")) {
                        cancelModalForm(selectorEl);
                    } else {
                        cancelForm(selectorEl);
                    }
                }
            }
        }

        if (
            (form.closest(".fb-popover") || form.closest(".fb-popover-panel")) &&
            window.Popover &&
            typeof window.Popover.hide === "function"
        ) {
            window.Popover.hide();
        }
    }

    function handleFormError(form, responseData) {
        const ctx = _readFormContext(form, "errorContext");
        if (!ctx) return;

        if (ctx?.context?.auto_clear_form) {
            form.reset();
        }

        const name = String(ctx.name || "");
        if (!JS_COMPONENTS.has(name)) return;

        const resolvedCtx = _resolveFormContext(ctx.context || {}, { response: responseData, error: responseData, ...responseData });
        _dispatchCtxForForm(form.id, name, resolvedCtx);
    }

    function _dispatchCtxForForm(formId, component, ctx) {
        if (component === "toast") {
            if (!window.Toast) {
                console.warn("utils/html.js: window.Toast is not loaded.");
                return;
            }
            window.Toast.show(ctx);
            return;
        }

        if (component === "alert") {
            if (!window.Alert) {
                console.warn("utils/html.js: window.Alert is not loaded.");
                return;
            }
            var type = ctx.type || "error";
            var selector = "#" + formId + "--alert-" + type;
            window.Alert.show(selector, ctx);
        }

        if (component === "modal") {
            if (!window.Modal) {
                console.warn("utils/html.js: window.Modal is not loaded.");
                return;
            }
            window.Modal.show(ctx);
            return;
        }

        if (component === "no-op") {
            _redirectTo(ctx.redirect_to, ctx.redirect_delay_secs);
            return;
        }
    }

    function _redirectTo(url, delaySecs) {
        if (!url) return;
        var delay = (delaySecs || 0) * 1000;
        setTimeout(function () {
            window.location.href = url;
        }, delay);
    }

    function _readFormContext(form, dataKey) {
        var raw = form.dataset[dataKey];
        if (!raw) return null;
        try {
            return JSON.parse(raw);
        } catch {
            console.warn(
                "utils/html.js: Could not parse data-" + _toKebab(dataKey),
            );
            return null;
        }
    }


    function _resolveFormContext(ctx, data) {
        var resolved = {};
        for (var k in ctx) {
            if (!Object.prototype.hasOwnProperty.call(ctx, k)) continue;
            var v = ctx[k];
            if (typeof v === "string") {
                v = v.replace(/\{([^{}]+)\}/g, function (match, pathExpr) {
                    var value = _getValueByPath(data, pathExpr);
                    if (value !== undefined && typeof value === "object") {
                        return JSON.stringify(value);
                    }
                    return value !== undefined ? value : match;
                });
            }
            resolved[k] = v;
        }
        return resolved;
    }

    function _evaluateCondition(condition, data) {
        if (typeof condition !== "string" || !condition.trim()) {
            return true;
        }

        try {
            var fn = new Function("response", "error", "data", "return " + condition);
            return Boolean(fn(data.response, data.error, data));
        } catch (err) {
            console.warn("utils/html.js: failed to evaluate condition:", condition, err);
            return false;
        }
    }


    function _getValueByPath(obj, path) {
        var normalized = path.replace(/\[(\w+)\]/g, '.$1');
        var parts = normalized.split('.');
        var current = obj;
        for (var i = 0; i < parts.length; i++) {
            if (current === null || current === undefined) return undefined;
            var part = parts[i];
            if (part === "") continue;
            current = current[part];
        }
        return current;
    }


    function _toKebab(camel) {
        return camel.replace(/([A-Z])/g, "-$1").toLowerCase();
    }


    return {
        cancelForm,
        cancelModalForm,
        handleFormSuccess,
        handleFormError,
    };
})();
