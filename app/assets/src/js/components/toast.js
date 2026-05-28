/**
 * Feedbase toast notifications
 *
 * It provides a simple API for showing transient toast messages in Feedbase.
 *
 * ## API
 *  ```js
 *   Toast.show({
 *     title?    : string,
 *     message?  : string,
 *     type?     : "success" | "error" | "warning" | "info",   default "success"
 *     position? : "top-right" | "bottom-right" | "top-middle" | "bottom-middle",
 *                 default "top-right"
 *     offset?   : Record<string, string> (CSS overrides for the container)
 *     duration? : number (ms)  0 = sticky, default 4000
 *     actions?  : Array<{label: string, onClick: function}> (optional action buttons)
 *     bordered? : boolean (adds left accent border, default false)
 *   })
 *   ```
 *
 * ## Example
 * ```js
 *   Toast.show({
 *    title: "Settings saved",
 *    message: "Your changes have been saved."
 *   });
 * ```
 */
export const Toast = (function () {
    "use strict";

    const POSITIONS = {
        "top-right": {
            top: "1rem",
            right: "1rem",
            bottom: "auto",
            left: "auto",
            transform: "none",
        },
        "bottom-right": {
            bottom: "1rem",
            right: "1rem",
            top: "auto",
            left: "auto",
            transform: "none",
        },
        "top-middle": {
            top: "1rem",
            left: "50%",
            bottom: "auto",
            right: "auto",
            transform: "translateX(-50%)",
        },
        "bottom-middle": {
            bottom: "1rem",
            left: "50%",
            top: "auto",
            right: "auto",
            transform: "translateX(-50%)",
        },
    };

    const ICONS = {
        success: "checkmark_circle_fill",
        error: "xmark_circle_fill",
        warning: "exclamationmark_triangle_fill",
        info: "info_circle_fill",
    };

    const ANIMATION_MS = 180;
    let _container = null;
    let _lastPosition = null;

    function show(opts) {
        opts = opts || {};
        const title = opts.title || "";
        const message = String(opts.message || "");
        const type = opts.type || "success";
        const position = opts.position || "top-right";
        const offset = opts.offset || null;
        const duration = opts.duration !== undefined ? opts.duration : 4000;
        const actions = opts.actions || [];
        const bordered = opts.bordered || false;
        const autoCloseModal = opts.auto_close_modal || false;

        if (autoCloseModal && window.Modal) {
            window.Modal.close();
        }

        const container = _getContainer(position, offset);
        const iconName = ICONS[type] || ICONS.success;

        const toast = document.createElement("div");
        let className = `fb-toast fb-toast-${type}`;
        if (bordered) className += " fb-toast-bordered";
        toast.className = className;

        const icon = document.createElement("i");
        icon.className = "f7-icons fb-toast-icon";
        icon.textContent = iconName;
        toast.appendChild(icon);

        let body;
        if (title) {
            body = document.createElement("div");
            body.className = "fb-toast-body";
            const titleEl = document.createElement("div");
            titleEl.className = "fb-toast-title";
            titleEl.textContent = title;
            const descEl = document.createElement("div");
            descEl.className = "fb-toast-desc";
            descEl.textContent = message;
            body.appendChild(titleEl);
            body.appendChild(descEl);
        } else if (message) {
            body = document.createElement("span");
            body.textContent = message;
        } else {
            body = document.createElement("span");
        }
        toast.appendChild(body);

        actions.forEach((action) => {
            const btn = document.createElement("button");
            btn.className = "fb-toast-action";
            btn.textContent = action.label;
            btn.addEventListener("click", async (e) => {
                e.stopPropagation();
                if (btn.disabled) return;
                btn.disabled = true;
                try {
                    const result = action.onClick(e);
                    if (result && typeof result.then === "function") {
                        await result;
                    }
                } catch (err) {
                    console.error("components/toast.js: Toast action error -", err);
                } finally {
                    if (toast.parentNode) {
                        btn.disabled = false;
                    }
                }
            });
            toast.appendChild(btn);
        });

        const closeBtn = document.createElement("button");
        closeBtn.className = "fb-toast-close";
        closeBtn.setAttribute("aria-label", "Dismiss");
        const closeIcon = document.createElement("i");
        closeIcon.className = "f7-icons fb-text-lg";
        closeIcon.textContent = "xmark";
        closeBtn.appendChild(closeIcon);
        closeBtn.addEventListener("click", () => _dismiss(toast));
        toast.appendChild(closeBtn);

        container.appendChild(toast);

        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                toast.style.opacity = "1";
                toast.style.transform = "translateY(0)";
            });
        });

        if (duration > 0) {
            setTimeout(() => _dismiss(toast), duration);
        }
    }

    function _getContainer(position, offset) {
        if (!_container) {
            _container = document.createElement("div");
            _container.className = "fb-toast-container";
            document.body.appendChild(_container);
        }
        if (position !== _lastPosition || offset) {
            const pos = POSITIONS[position] || POSITIONS["top-right"];
            Object.assign(_container.style, pos, offset || {});
            _lastPosition = position;
        }
        return _container;
    }

    function _dismiss(toast) {
        toast.style.opacity = "0";
        toast.style.transform = "translateY(-6px)";
        setTimeout(() => {
            if (toast.parentNode) toast.parentNode.removeChild(toast);
        }, ANIMATION_MS);
    }

    return { show };
})();
