/**
 * Feedbase Popover system
 *
 * It provides a simple API for showing popover menus attached to trigger elements.
 * Content can be a list of options or loaded dynamically via HTMX.
 *
 * ## API
 *  ```js
 *   Popover.show(triggerElement, {
 *     options?: Array<{
 *       label?: string, 
 *       icon?: string, 
 *       url?: string, 
 *       onClick?: function|string, 
 *       danger?: boolean,
 *       content_url?: string,
 *       attributes?: Record<string, string|boolean>,
 *     }>,
 *     placement?: "bottom-start" | "bottom-end" | "top-start" | "top-end"
 *   })
 *   Popover.hide()
 *   ```
 *
 * ## Example
 * ```js
 *   Popover.show(btnElement, {
 *     options: [
 *       { label: "Profile", icon: "person", url: "/profile" },
 *       { label: "Delete", icon: "trash", danger: true, onClick: () => doDelete() },
 *       { label: "Move to Folder", icon: "arrowshape_turn_up_right", url: "/api/v1/folders" },
 *       { content_url: "/components/user-menu-extra" }
 *     ],
 *     placement: "bottom-end"
 *   });
 * ```
 * 
 * If an option has content_url, the content is loaded into the popover when the option is rendered.
 */
export const Popover = (function () {
    "use strict";

    let currentPopover = null;
    let currentTrigger = null;

    function resolveOnClick(onClick, event) {
        if (!onClick) return;
        if (typeof onClick === "function") {
            onClick(event);
        } else if (typeof onClick === "string" && typeof window[onClick] === "function") {
            window[onClick](event);
        } else {
            console.warn("Popover: onClick handler not found or not a function:", onClick);
        }
    }

    function positionPopover(popover, trigger, placement) {
        const rect = trigger.getBoundingClientRect();
        const popRect = popover.getBoundingClientRect();

        let top = 0;
        let left = 0;
        const offset = 6;

        switch (placement) {
            case "bottom-start":
                top = rect.bottom + offset;
                left = rect.left;
                break;
            case "bottom-end":
                top = rect.bottom + offset;
                left = rect.right - popRect.width;
                break;
            case "top-start":
                top = rect.top - popRect.height - offset;
                left = rect.left;
                break;
            case "top-end":
                top = rect.top - popRect.height - offset;
                left = rect.right - popRect.width;
                break;
            default:
                top = rect.bottom + offset;
                left = rect.left;
        }

        if (left < 8) left = 8;
        if (left + popRect.width > window.innerWidth - 8) {
            left = window.innerWidth - popRect.width - 8;
        }
        if (top < 8) top = 8;
        if (top + popRect.height > window.innerHeight - 8) {
            top = rect.top - popRect.height - offset;
            if (top < 8) top = 8;
        }

        popover.style.top = `${top + window.scrollY}px`;
        popover.style.left = `${left + window.scrollX}px`;
    }

    function normalizePopoverUrl(url) {
        if (!url || typeof url !== "string") return url;

        let parsedUrl;
        try {
            parsedUrl = new URL(url, window.location.href);
        } catch (err) {
            return url;
        }

        if (!parsedUrl.search) {
            return parsedUrl.toString();
        }

        const params = Array.from(parsedUrl.searchParams.entries());
        parsedUrl.search = "";

        params.forEach(([key, value]) => {
            let normalizedValue = value;
            const trimmed = String(value).trim();

            if (
                (trimmed.startsWith("{") && trimmed.endsWith("}")) ||
                (trimmed.startsWith("[") && trimmed.endsWith("]"))
            ) {
                try {
                    normalizedValue = JSON.stringify(JSON.parse(trimmed));
                } catch (err) {
                    if (trimmed.includes("'")) {
                        try {
                            const replaced = trimmed
                                .replace(/(['"])?([\w$]+)\1\s*:/g, '"$2":')
                                .replace(/'([^']*)'/g, (_, inner) => JSON.stringify(inner));
                            normalizedValue = JSON.stringify(JSON.parse(replaced));
                        } catch (err2) {
                            normalizedValue = value;
                        }
                    }
                }
            }

            parsedUrl.searchParams.set(key, normalizedValue);
        });

        return parsedUrl.toString();
    }

    function show(trigger, options = {}) {
        if (currentPopover && currentTrigger === trigger) {
            hide();
            return;
        }

        if (currentPopover) {
            hide();
        }

        const {
            options: popoverOptions = [],
            placement = "bottom-start",
        } = options;

        if (!popoverOptions || popoverOptions.length === 0) {
            console.error("Popover.show requires 'options' array to be provided");
            return;
        }

        currentTrigger = trigger;

        const popover = document.createElement("div");
        popover.className = "fb-popover fb-bg-surface fb-border fb-border-surface2 fb-rounded-lg";
        popover.setAttribute("role", "menu");

        const body = document.createElement("div");
        body.className = "fb-popover-body";
        popover.appendChild(body);

        popoverOptions.forEach((opt) => {
            if (opt.content_url) {
                const wrapper = document.createElement("div");
                wrapper.innerHTML = '<div class="fb-popover-loading"><i class="f7-icons fb-animate-spin">arrow_2_circlepath</i></div>';
                body.appendChild(wrapper);
                loadContent(wrapper, opt.content_url);
            } else {
                renderStaticOption(body, opt);
            }
        });

        document.body.appendChild(popover);
        currentPopover = popover;

        positionPopover(popover, trigger, placement);

        setTimeout(() => {
            document.addEventListener("click", handleOutsideClick);
            window.addEventListener("resize", handleResize);
        }, 0);

        function renderStaticOption(container, opt) {
            const el = document.createElement(opt.url ? "a" : "button");
            el.className = "fb-popover-option";
            if (opt.danger) el.classList.add("danger");

            if (opt.url) {
                el.href = normalizePopoverUrl(opt.url);
            }

            const attributes = opt.attributes || opt.attrs;
            if (attributes && typeof attributes === "object") {
                Object.entries(attributes).forEach(([name, value]) => {
                    if (value === null || value === undefined || value === false) {
                        return;
                    }

                    if (value === true) {
                        el.setAttribute(name, "true");
                    } else {
                        el.setAttribute(name, String(value));
                    }
                });
            }

            if (opt.icon) {
                const icon = document.createElement("i");
                icon.className = "f7-icons";
                icon.textContent = opt.icon;
                el.appendChild(icon);
            }

            if (opt.label) {
                const label = document.createElement("span");
                label.textContent = opt.label;
                el.appendChild(label);
            }

            el.addEventListener("click", (e) => {
                if (opt.onClick) {
                    e.preventDefault();
                    resolveOnClick(opt.onClick, e);
                }
                hide();
            });

            container.appendChild(el);
        }

        function getTemplateHtml(templateRef) {
            if (!templateRef) {
                return null;
            }

            if (typeof templateRef !== "string") {
                return null;
            }

            const trimmed = templateRef.trim();
            if (trimmed.startsWith("<")) {
                return templateRef;
            }

            const tpl = document.getElementById(templateRef);
            if (tpl && tpl.innerHTML) {
                return tpl.innerHTML;
            }

            return null;
        }

        function renderTemplate(templateHtml, context) {
            if (window.htmx && window.htmx.template && typeof window.htmx.template.render === "function") {
                try {
                    return window.htmx.template.render(templateHtml, context);
                } catch (err) {
                    console.warn("Popover: failed to render JSON template with htmx.template.render", err);
                }
            }

            return templateHtml;
        }

        function escapeHtml(value) {
            return String(value)
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#39;");
        }

        function loadContent(container, url) {
            fetch(normalizePopoverUrl(url), { headers: { "X-Requested-With": "XMLHttpRequest" } })
                .then((res) => {
                    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
                    return res.text();
                })
                .then((html) => {
                    container.innerHTML = html;
                    if (window.htmx) {
                        window.htmx.process(container);
                    }
                    positionPopover(currentPopover, trigger, placement);
                })
                .catch((err) => {
                    console.error("components/popover.js: Failed to load content -", err);
                    container.innerHTML = '<div style="padding: 12px; color: #f04a4a; font-size: 13px;">Failed to load.</div>';
                });
        }

        function handleOutsideClick(e) {
            if (
                currentPopover &&
                !currentPopover.contains(e.target) &&
                !trigger.contains(e.target)
            ) {
                hide();
            }
        }

        function handleResize() {
            if (currentPopover && currentTrigger) {
                positionPopover(currentPopover, currentTrigger, placement);
            }
        }

        popover._cleanup = () => {
            document.removeEventListener("click", handleOutsideClick);
            window.removeEventListener("resize", handleResize);
        };
    }

    function hide() {
        if (!currentPopover) return;

        if (currentPopover._cleanup) {
            currentPopover._cleanup();
        }

        currentPopover.remove();
        currentPopover = null;
        currentTrigger = null;
    }

    return { show, hide };
})();