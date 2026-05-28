/**
 * Feedbase Sheet component
 *
 * It provides a bottom-sheet UI for content loading and JSON rendering.
 *
 * ## API
 *   Sheet.show({
 *     content_url: string,
 *     content_format?: "json" | "html",
 *     content_success_template_html?: string,
 *     content_success_template_id?: string,
 *     content_error_template_html?: string,
 *     content_error_template_id?: string,
 *     content_template?: string,
 *     content_template_id?: string,
 *     content_template_html?: string,
 *     content_html?: string,
 *     sheet_class?: string,
 *     sheet_style?: string,
 *     heading_title?: string,
 *     heading_icon?: string, // f7 icon name
 *     heading_alignment?: "left" | "center" | "right",
 *     on_content_load?: function(container, payload),
 *   })
 *   Sheet.hide()
 */
export const Sheet = (function () {
    "use strict";

    let currentSheet = null;

    function show(options = {}) {
        hide();

        const {
            content_url,
            content_format = "html",
            content_success_template_html,
            content_success_template_id,
            content_error_template_html,
            content_error_template_id,
            content_template,
            content_template_id,
            content_template_html,
            content_html,
            sheet_class,
            sheet_style,
            heading_title = null,
            heading_icon = null,
            heading_alignment = "left",
            on_content_load = null,
        } = options;

        const backdrop = document.createElement("div");
        backdrop.className = "fb-sheet-backdrop";

        const sheet = document.createElement("div");
        sheet.className = `fb-sheet${sheet_class ? ` ${sheet_class}` : ''}`;
        if (sheet_style) {
            sheet.style.cssText += sheet_style;
        }

        const handle = document.createElement("div");
        handle.className = "fb-sheet-handle";
        sheet.appendChild(handle);

        if (heading_title || heading_icon) {
            const header = document.createElement("div");
            header.className = `fb-sheet-header fb-sheet-header-align-${heading_alignment}`;

            if (heading_icon) {
                const icon = document.createElement("i");
                icon.className = "f7-icons fb-text-lg";
                icon.textContent = heading_icon;
                header.appendChild(icon);
            }

            if (heading_title) {
                const title = document.createElement("div");
                title.className = "fb-sheet-title";
                title.textContent = heading_title;
                header.appendChild(title);
            }

            sheet.appendChild(header);
        }

        const body = document.createElement("div");
        body.className = "fb-sheet-body";
        body.innerHTML = '<div class="fb-popover-loading"><i class="f7-icons fb-animate-spin">arrow_2_circlepath</i></div>';
        sheet.appendChild(body);

        backdrop.appendChild(sheet);
        document.body.appendChild(backdrop);
        document.body.style.overflow = "hidden";

        backdrop.addEventListener("click", (event) => {
            if (event.target === backdrop) {
                hide();
            }
        });

        const onClose = (event) => {
            if (event.key === "Escape") {
                hide();
            }
        };
        document.addEventListener("keydown", onClose);
        backdrop._escHandler = onClose;

        currentSheet = backdrop;

        loadContent(body, {
            content_url,
            content_format,
            content_success_template_html,
            content_success_template_id,
            content_error_template_html,
            content_error_template_id,
            content_template,
            content_template_id,
            content_template_html,
            content_html,
            on_content_load,
        });
    }

    function hide() {
        if (!currentSheet) {
            return;
        }

        if (currentSheet._escHandler) {
            document.removeEventListener("keydown", currentSheet._escHandler);
        }

        if (currentSheet.parentNode) {
            currentSheet.parentNode.removeChild(currentSheet);
        }

        document.body.style.overflow = "";
        currentSheet = null;
    }

    function loadContent(container, panelConfig) {
        if (panelConfig.content_html) {
            container.innerHTML = panelConfig.content_html;
            if (window.htmx && panelConfig.content_format !== "json") {
                window.htmx.process(container);
            }

            if (typeof panelConfig.on_content_load === "function") {
                panelConfig.on_content_load(container, null);
            }
            return;
        }

        if (!panelConfig.content_url) {
            container.innerHTML = renderError({ message: "No content URL provided." }, panelConfig);
            return;
        }

        const acceptType = panelConfig.content_format === "json" ? "application/json" : "text/html";

        fetch(panelConfig.content_url, {
            headers: {
                "X-Requested-With": "XMLHttpRequest",
                Accept: acceptType,
            },
        })
            .then((res) => {
                if (!res.ok) {
                    throw new Error(`HTTP error! status: ${res.status}`);
                }
                return panelConfig.content_format === "json" ? res.json() : res.text();
            })
            .then((payload) => {
                if (panelConfig.content_format === "json") {
                    container.innerHTML = renderJson(payload, panelConfig);
                } else {
                    container.innerHTML = payload;
                    if (window.htmx) {
                        window.htmx.process(container);
                    }
                }

                if (typeof panelConfig.on_content_load === "function") {
                    panelConfig.on_content_load(container, payload);
                }
            })
            .catch((err) => {
                console.error("components/sheet.js: Failed to load content -", err);
                container.innerHTML = renderError({ message: err.message || "Failed to load content." }, panelConfig);

                if (typeof panelConfig.on_content_load === "function") {
                    panelConfig.on_content_load(container, null);
                }
            });
    }

    function renderJson(payload, panelConfig) {
        if (!payload) {
            return '<div class="fb-p-3 fb-text-muted">No data available.</div>';
        }

        const ctx = {
            data: payload.data,
            metadata: payload.metadata,
            response: payload,
            error: payload.error,
        };

        const templateHtml =
            panelConfig.content_success_template_html ||
            panelConfig.content_template_html ||
            getTemplateHtml(panelConfig.content_success_template_id || panelConfig.content_template_id || panelConfig.content_template);

        if (templateHtml) {
            return renderTemplate(templateHtml, ctx);
        }

        return `<pre style="white-space: pre-wrap; word-break: break-word; padding: 12px; margin: 0;">${escapeHtml(JSON.stringify(payload, null, 2))}</pre>`;
    }

    function renderError(errorPayload, panelConfig) {
        const ctx = {
            error: errorPayload,
            response: errorPayload,
        };

        const templateHtml =
            panelConfig.content_error_template_html ||
            getTemplateHtml(panelConfig.content_error_template_id);

        if (templateHtml) {
            return renderTemplate(templateHtml, ctx);
        }

        return `<div class="fb-p-3 fb-text-red">${escapeHtml((errorPayload && errorPayload.message) || "Failed to load content.")}</div>`;
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
        return tpl && tpl.innerHTML ? tpl.innerHTML : null;
    }

    function renderTemplate(templateHtml, context) {
        if (window.htmx && window.htmx.template && typeof window.htmx.template.render === "function") {
            try {
                return window.htmx.template.render(templateHtml, context);
            } catch (err) {
                console.warn("Sheet: failed to render JSON template with htmx.template.render", err);
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

    return {
        show,
        hide,
    };
})();
