/**
 * Feedbase alert system 
 *
 * ## API
 *  ```js
 *   Alert.show(selector, {
 *     variant?    : "inline" | "field" | "banner",  // default "inline"
 *     type?       : "success" | "error" | "warning" | "info", default "error"
 *     title?      : string,        // for inline and banner (banner uses strong internally)
 *     message?    : string,        // main text
 *     strong?     : string,        // (banner only) text to wrap in <strong>
 *     actions?    : Array<{label: string, onClick: function|string, primary?: boolean}>,
 *     dismissible?: boolean,       // default true for inline/banner, false for field
 *   })
 *   Alert.hide(selector)
 *   ```
 *
 * ## Examples
 *  ```js
 *   // Inline with function
 *   Alert.show("#my-alert", {
 *     title: "Feed subscribed",
 *     message: "1,240 articles fetched.",
 *     type: "success",
 *     actions: [{ label: "View", onClick: () => console.log("view") }]
 *   });
 *
 *   // Inline with string (global function name)
 *   Alert.show("#my-alert", {
 *     title: "Feed unreachable",
 *     message: "502 Bad Gateway",
 *     type: "error",
 *     actions: [{ label: "Retry", onClick: "globalRetryFunction" }]
 *   });
 *
 *   // Field-level compact
 *   Alert.show("#field-error", {
 *     variant: "field",
 *     type: "error",
 *     message: "That email is already registered."
 *   });
 *
 *   // System banner with string onClick
 *   Alert.show("#banner-area", {
 *     variant: "banner",
 *     type: "warning",
 *     strong: "Disk usage at 82%.",
 *     message: "Pruning will run Monday.",
 *     actions: [{ label: "See storage", onClick: "openStorageSettings" }],
 *     dismissible: true
 *   });
 *  ```
 */
export const Alert = (function () {
  "use strict";

  const INLINE_ICONS = {
    success: "checkmark_circle_fill",
    error: "xmark_circle_fill",
    warning: "exclamationmark_triangle_fill",
    info: "info_circle_fill",
  };
  const FIELD_ICONS = {
    success: "checkmark_circle",
    error: "exclamationmark_circle",
    warning: "exclamationmark_triangle",
    info: "info_circle",
  };
  const BANNER_ICONS = {
    success: "checkmark_circle_fill",
    error: "xmark_octagon_fill",
    warning: "exclamationmark_triangle_fill",
    info: "info_circle_fill",
  };

  function resolveOnClick(onClick, event) {
    if (typeof onClick === "function") {
      return onClick(event);
    }
    if (typeof onClick === "string") {
      if (onClick.includes(".")) {
        const parts = onClick.split(".");
        let fn = window;
        for (const part of parts) {
          fn = fn[part];
          if (typeof fn === "undefined") {
            console.error(`components/alerts.js: Global function "${onClick}" not found.`);
            return;
          }
        }
        if (typeof fn === "function") {
          return fn(event);
        }
        console.error(`components/alerts.js: Global function "${onClick}" is not a function.`);
        return;
      }

      const fn = window[onClick];
      if (typeof fn === "function") {
        return fn(event);
      }
      console.error(`components/alerts.js: Global function "${onClick}" not found.`);
      return;
    }
    console.error("components/alerts.js: onClick must be a function or a string (global function name).");
  }

  function show(selector, opts) {
    const el = document.querySelector(selector);
    if (!el) {
      console.warn(
        'components/alerts.js: Unable to show alert, element not found for "' + selector + '"',
      );
      return;
    }

    opts = opts || {};
    const variant = opts.variant || "inline";
    const type = opts.type || "error";
    const title = opts.title || "";
    const message = String(opts.message || "");
    const strong = opts.strong || "";
    const actions = opts.actions || [];
    const dismissible = opts.dismissible !== undefined ? opts.dismissible : (variant !== "field");

    el.innerHTML = "";
    el.className = "";

    if (variant === "field") {
      el.className = `fb-field-alert ${type}`;
      const icon = document.createElement("i");
      icon.className = "f7-icons";
      icon.textContent = FIELD_ICONS[type] || FIELD_ICONS.error;
      el.appendChild(icon);
      const textSpan = document.createElement("span");
      textSpan.textContent = message;
      el.appendChild(textSpan);
    }
    else if (variant === "banner") {
      // System banner
      el.className = `fb-banner ${type}`;
      const icon = document.createElement("i");
      icon.className = "f7-icons";
      icon.textContent = BANNER_ICONS[type] || BANNER_ICONS.error;
      el.appendChild(icon);
      const textSpan = document.createElement("span");
      textSpan.className = "fb-banner-text";
      if (strong) {
        const strongEl = document.createElement("strong");
        strongEl.textContent = strong;
        textSpan.appendChild(strongEl);
        if (message) {
          textSpan.appendChild(document.createTextNode(" " + message));
        }
      } else if (title) {
        const strongEl = document.createElement("strong");
        strongEl.textContent = title;
        textSpan.appendChild(strongEl);
        if (message) {
          textSpan.appendChild(document.createTextNode(" " + message));
        }
      } else {
        textSpan.textContent = message;
      }
      el.appendChild(textSpan);

      // Actions
      actions.forEach((action) => {
        const btn = document.createElement("button");
        btn.className = "fb-banner-action";
        btn.textContent = action.label;
        btn.addEventListener("click", async (e) => {
          if (btn.disabled) return;
          btn.disabled = true;
          try {
            const result = resolveOnClick(action.onClick, e);
            if (result && typeof result.then === "function") {
              await result;
            }
          } catch (err) {
            console.error("components/alerts.js: Banner action error - ", err);
          } finally {
            if (el.parentNode) {
              btn.disabled = false;
            }
          }
        });
        el.appendChild(btn);
      });

      // Dismiss button
      if (dismissible) {
        const closeBtn = document.createElement("button");
        closeBtn.className = "fb-banner-close";
        closeBtn.setAttribute("aria-label", "Dismiss");
        const closeIcon = document.createElement("i");
        closeIcon.className = "f7-icons fb-text-lg";
        closeIcon.textContent = "xmark";
        closeBtn.appendChild(closeIcon);
        closeBtn.addEventListener("click", () => hide(selector));
        el.appendChild(closeBtn);
      }
    }
    else {
      // Default: inline alert
      el.className = `fb-alert fb-alert-${type}`;
      const icon = document.createElement("i");
      icon.className = `f7-icons fb-alert-icon`;
      icon.textContent = INLINE_ICONS[type] || INLINE_ICONS.error;
      el.appendChild(icon);
      const body = document.createElement("div");
      body.className = "fb-alert-body";
      if (title) {
        const titleEl = document.createElement("div");
        titleEl.className = "fb-alert-title";
        titleEl.textContent = title;
        body.appendChild(titleEl);
      }
      if (message) {
        const descEl = document.createElement("div");
        descEl.className = "fb-alert-desc";
        descEl.textContent = message;
        body.appendChild(descEl);
      }
      if (actions.length) {
        const actionsDiv = document.createElement("div");
        actionsDiv.className = "fb-alert-actions";
        actions.forEach((action) => {
          const btn = document.createElement("button");
          btn.className = `fb-alert-action ${action.primary ? "primary" : "secondary"}`;
          btn.textContent = action.label;
          btn.addEventListener("click", async (e) => {
            if (btn.disabled) return;
            btn.disabled = true;
            try {
              const result = resolveOnClick(action.onClick, e);
              if (result && typeof result.then === "function") {
                await result;
              }
            } catch (err) {
              console.error("components/alerts.js: Alert action error - ", err);
            } finally {
              if (el.parentNode) {
                btn.disabled = false;
              }
            }
          });
          actionsDiv.appendChild(btn);
        });
        body.appendChild(actionsDiv);
      }
      el.appendChild(body);
      if (dismissible) {
        const closeBtn = document.createElement("button");
        closeBtn.className = "fb-alert-close";
        closeBtn.setAttribute("aria-label", "Dismiss");
        const closeIcon = document.createElement("i");
        closeIcon.className = "f7-icons fb-alert-icon";
        closeIcon.textContent = "xmark";
        closeBtn.appendChild(closeIcon);
        closeBtn.addEventListener("click", () => hide(selector));
        el.appendChild(closeBtn);
      }
    }
  }

  function hide(selector) {
    const el = document.querySelector(selector);
    if (!el) return;
    el.innerHTML = "";
    el.className = "";
  }

  return { show: show, hide: hide };
})();