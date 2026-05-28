/**
 * Feedbase Modal system
 *
 * It provides a simple API for showing modal dialogs that load content via HTMX.
 *
 * ## API
 *  ```js
 *   Modal.show({
 *     heading_icon?    : string | null,      // f7-icons name
 *     heading_title?   : string | null,
 *     heading_subtitle?: string | null,
 *     content_url      : string,              // Endpoint returning the HTML
 *   })
 *   Modal.hide(modalElement)
 *   ```
 *
 * ## Example
 * ```js
 *   Modal.show({
 *     heading_icon: "folder_badge_plus",
 *     heading_title: "Create folder",
 *     heading_subtitle: "Folders help you organise feeds.",
 *     content_url: "/forms/create_folder_form"
 *   });
 * ```
 */
export const Modal = (function () {
  "use strict";

  let currentModal = null;

  function show(options) {
    if (currentModal) {
      hide(currentModal);
    }

    const {
      heading_icon = null,
      heading_title = null,
      heading_subtitle = null,
      content_url,
      render_fn,
      auto_close_form = false,
      auto_close_form_with_selector = null,
    } = options;

    if (auto_close_form && auto_close_form_with_selector) {
      const selectorEl = document.querySelector(auto_close_form_with_selector);

      if (selectorEl && window.HTMLUtils) {
        if (selectorEl.closest(".fb-modal-backdrop")) {
          window.HTMLUtils.cancelModalForm(selectorEl);
        } else {
          window.HTMLUtils.cancelForm(selectorEl);
        }
      }
    }

    if (!content_url && typeof render_fn !== "function") {
      console.error("components/modal.js: content_url or render_fn is required");
      return;
    }

    const backdrop = document.createElement("div");
    backdrop.className = "fb-modal-backdrop";

    const modal = document.createElement("div");
    modal.className = "fb-modal";
    modal.setAttribute("role", "dialog");
    modal.setAttribute("aria-modal", "true");

    const header = document.createElement("div");
    header.className = "fb-modal-header";

    if (heading_icon) {
      const iconDiv = document.createElement("div");
      iconDiv.className = "fb-modal-header-icon neutral";
      const icon = document.createElement("i");
      icon.className = "f7-icons";
      icon.textContent = heading_icon;
      iconDiv.appendChild(icon);
      header.appendChild(iconDiv);
    }

    const headerText = document.createElement("div");
    headerText.className = "fb-modal-header-text";

    if (heading_title) {
      const title = document.createElement("div");
      title.className = "fb-modal-title";
      title.textContent = heading_title;
      headerText.appendChild(title);
    }
    if (heading_subtitle) {
      const subtitle = document.createElement("div");
      subtitle.className = "fb-modal-subtitle";
      subtitle.textContent = heading_subtitle;
      headerText.appendChild(subtitle);
    }
    header.appendChild(headerText);

    const closeBtn = document.createElement("button");
    closeBtn.className = "fb-modal-close";
    closeBtn.setAttribute("aria-label", "Close");
    const closeIcon = document.createElement("i");
    closeIcon.className = "f7-icons fb-text-lg";
    closeIcon.textContent = "xmark";
    closeBtn.appendChild(closeIcon);
    closeBtn.addEventListener("click", () => hide(backdrop));
    header.appendChild(closeBtn);

    modal.appendChild(header);

    const body = document.createElement("div");
    body.className = "fb-modal-body";
    body.innerHTML = `
            <div style="display: flex; justify-content: center; align-items: center; padding: 2rem;">
                <svg style="width: 32px; height: 32px; color: var(--accent);" fill="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12,1A11,11,0,1,0,23,12,11,11,0,0,0,12,1Zm0,19a8,8,0,1,1,8-8A8,8,0,0,1,12,20Z" opacity=".25"/>
                    <path d="M12,4a8,8,0,0,1,7.89,6.7A1.53,1.53,0,0,0,21.38,12h0a1.5,1.5,0,0,0,1.48-1.75,11,11,0,0,0-21.72,0A1.5,1.5,0,0,0,2.62,12h0a1.53,1.53,0,0,0,1.49-1.3A8,8,0,0,1,12,4Z">
                        <animateTransform attributeName="transform" type="rotate" dur="0.75s" values="0 12 12;360 12 12" repeatCount="indefinite"/>
                    </path>
                </svg>
            </div>
        `;
    modal.appendChild(body);

    backdrop.appendChild(modal);
    document.body.appendChild(backdrop);

    document.body.style.overflow = "hidden";

    const loadContent = () => {
      if (render_fn) {
        const content = render_fn();
        if (content instanceof Promise) {
          content.then((html) => {
            body.innerHTML = html;
            if (window.htmx) {
              window.htmx.process(body);
            }
          }).catch((err) => {
            console.error("components/modal.js: render_fn failed -", err);
            body.innerHTML = '<div class="fb-field-alert error">Failed to load content.</div>';
          });
        } else if (content instanceof HTMLElement) {
          body.innerHTML = "";
          body.appendChild(content);
          if (window.htmx) {
            window.htmx.process(body);
          }
        } else {
          body.innerHTML = content;
          if (window.htmx) {
            window.htmx.process(body);
          }
        }
        return;
      }

      body.innerHTML = `
                <div style="display: flex; justify-content: center; align-items: center; padding: 2rem;">
                    <svg style="width: 32px; height: 32px; color: var(--accent);" fill="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path d="M12,1A11,11,0,1,0,23,12,11,11,0,0,0,12,1Zm0,19a8,8,0,1,1,8-8A8,8,0,0,1,12,20Z" opacity=".25"/>
                        <path d="M12,4a8,8,0,0,1,7.89,6.7A1.53,1.53,0,0,0,21.38,12h0a1.5,1.5,0,0,0,1.48-1.75,11,11,0,0,0-21.72,0A1.5,1.5,0,0,0,2.62,12h0a1.53,1.53,0,0,0,1.49-1.3A8,8,0,0,1,12,4Z">
                            <animateTransform attributeName="transform" type="rotate" dur="0.75s" values="0 12 12;360 12 12" repeatCount="indefinite"/>
                        </path>
                    </svg>
                </div>
            `;

      fetch(content_url, {
        headers: { "HX-Request": "true" },
      })
        .then((res) => {
          if (!res.ok) {
            throw new Error(`HTTP ${res.status}`);
          }
          return res.text();
        })
        .then((html) => {
          body.innerHTML = html;
          if (window.htmx) {
            window.htmx.process(body);
          }
        })
        .catch((err) => {
          console.error("components/modal.js: Failed to load content -", err);
          if (!window.Alert) {
            body.innerHTML = '<div class="fb-field-alert error">Failed to load form. Please try again.</div>';
            return;
          }
          body.innerHTML = '<div id="modal-error-banner"></div>';
          window.Alert.show("#modal-error-banner", {
            variant: "banner",
            type: "error",
            strong: "Failed to load form",
            message: "Could not reach the server. Please check your connection and try again.",
            actions: [
              {
                label: "Retry",
                onClick: () => loadContent(),
                primary: true,
              },
            ],
            dismissible: false,
          });
        });
    };

    loadContent();

    currentModal = backdrop;

    backdrop.addEventListener("click", (e) => {
      if (e.target === backdrop) {
        hide(backdrop);
      }
    });

    const escHandler = (e) => {
      if (e.key === "Escape") {
        hide(backdrop);
        document.removeEventListener("keydown", escHandler);
      }
    };

    document.addEventListener("keydown", escHandler);
    backdrop._escHandler = escHandler;
  }

  function hide(modalElement) {
    if (!modalElement && currentModal) {
      modalElement = currentModal;
    }
    if (!modalElement) return;
    if (modalElement.parentNode) {
      modalElement.parentNode.removeChild(modalElement);
    }
    document.body.style.overflow = "";
    if (modalElement._escHandler) {
      document.removeEventListener("keydown", modalElement._escHandler);
    }
    if (currentModal === modalElement) {
      currentModal = null;
    }
  }

  function close() {
    if (currentModal !== null) {
      hide(currentModal);
    }
  }

  return { show, hide, close };
})();