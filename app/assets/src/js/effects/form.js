/**
 * Effects for Forms
 * 
 * 1. It intercepts every HTMX form submission response and coordinates:
 *      • Client-side redirects (with optional countdown)
 *      • Toast notifications  (window.Toast)
 *      • Alert banner updates (window.Alert)
 *      • Modal (window.Modal)
 *      • No operation (no-op) 
 *
 * 2. It also auto-submits any form with the data attribute `data-submit-on-page-load="true"`
 * 
 * Configuration is read from data attributes embedded by the server on the
 * <form> element:
 *
 *   data-success-context   JSON: FormSubmissionSuccessContext
 *   data-error-context     JSON: FormSubmissionErrorContext
 *
 * The server returns a JSON body of
 * the service result (or error detail). Context values that start with
 * "{response." or "{error." are resolved against this payload.
 *
 * SUCCESS (HTTP 200–399)
 *   1. If the server sent HX-Redirect or HX-Location → HTMX handles it, done.
 *   2. If success context has redirect_to, we perform client-side redirect after
 *      redirect_delay_secs seconds (0 = immediate).
 *   3. If success context name is "toast", call  window.Toast.show(ctx)
 *   4. If success context name is "alert", call window.Alert.show(selector, ctx)
 *
 * ERROR (HTTP ≥ 400)
 *  We reset the form and then:
 *   Additionally:
 *   1. If error context name is "toast", call window.Toast.show(ctx)
 *   2. If error context name is "alert", call window.Alert.show(selector, ctx)
 */


function setupEnableOnChangedValueFields(root) {
    root = root || document;
    const inputs = root.querySelectorAll('[data-enable-on-changed-value]');
    const forms = new Set();
    inputs.forEach((input) => {
        const form = input.closest('form');
        if (form) {
            forms.add(form);
        }
    });

    forms.forEach((form) => {
        if (form.dataset.enableOnChangedValueInitialized === 'true') {
            if (typeof form._enableOnChangedValueUpdate === 'function') {
                form._enableOnChangedValueUpdate();
            }
            return;
        }

        const trackedInputs = Array.from(
            form.querySelectorAll('[data-enable-on-changed-value]')
        );
        if (!trackedInputs.length) return;

        form.dataset.enableOnChangedValueInitialized = 'true';
        const originalValues = new WeakMap();
        trackedInputs.forEach((trackedInput) => {
            if (!originalValues.has(trackedInput)) {
                originalValues.set(trackedInput, trackedInput.value);
            }
        });

        const submitButtons = Array.from(
            form.querySelectorAll("button[type='submit'], input[type='submit']")
        );
        if (!submitButtons.length) return;

        const updateSubmitState = () => {
            const allChanged = trackedInputs.every((trackedInput) => {
                const originalValue = originalValues.get(trackedInput);
                return trackedInput.value !== originalValue;
            });

            const allValid = trackedInputs.every((trackedInput) => {
                const fieldError = form.querySelector(
                    `#${CSS.escape(trackedInput.name)}-error`
                );
                const hasServerError = fieldError
                    ? fieldError.textContent.trim().length > 0
                    : false;
                return trackedInput.checkValidity() && !hasServerError;
            });

            const isEnabled = allChanged && allValid;
            submitButtons.forEach((btn) => {
                if (isEnabled) {
                    btn.removeAttribute('disabled');
                } else {
                    btn.setAttribute('disabled', '');
                }
            });
        };

        trackedInputs.forEach((trackedInput) => {
            trackedInput.addEventListener('input', updateSubmitState);
            trackedInput.addEventListener('change', updateSubmitState);
        });

        updateSubmitState();
    });
}

function setupAutoSubmitOnChange(root) {
    root = root || document;
    const elements = root.querySelectorAll('[data-auto-submit-on-change="true"]');
    elements.forEach((element) => {
        if (element.dataset.autoSubmitOnChangeInitialized === 'true') return;
        element.dataset.autoSubmitOnChangeInitialized = 'true';

        const submitForm = () => {
            const form = element.closest('form');
            if (!form) return;
            if (typeof form.requestSubmit === 'function') {
                form.requestSubmit();
            } else {
                form.submit();
            }
        };

        element.addEventListener('change', submitForm);
    });
}

document.addEventListener("htmx:afterRequest", function (event) {
    if (event.target !== event.detail.elt) {
        return;
    }
    const elt = event.detail.elt;
    const form = elt.tagName === "FORM" ? elt : elt.closest("form");
    if (!form) return;

    if (!window.HTMLUtils) {
        console.warn("effects/form.js: window.HTMLUtils is not loaded.");
        return;
    }

    const xhr = event.detail.xhr;
    const status = xhr.status;

    const contentType = xhr.getResponseHeader("Content-Type") || null;
    const formSuccessResponseHeader =
        xhr.getResponseHeader("X-Form-Submit-Success-Response") || null;
    const formErrorResponseHeader =
        xhr.getResponseHeader("X-Form-Submit-Error-Response") || null;

    const isFormServiceResponse =
        formSuccessResponseHeader || formErrorResponseHeader;
    const isFormJsonResponse =
        contentType &&
        (contentType.includes("application/json") ||
            contentType.includes("application/problem+json"));

    if (isFormJsonResponse || isFormServiceResponse) {
        let responseData = null;

        const parseJson = (payload) => {
            if (!payload) return null;
            try {
                return JSON.parse(payload);
            } catch (e) {
                return null;
            }
        };

        responseData = parseJson(formSuccessResponseHeader) || parseJson(formErrorResponseHeader);
        if (responseData === null) {
            responseData = parseJson(xhr.responseText);
            if (responseData === null && (formSuccessResponseHeader || formErrorResponseHeader)) {
                console.warn(
                    "effects/form.js: Could not parse service response header, falling back to responseText."
                );
            }
        }

        if (
            (responseData !== null && status >= 200 && status < 400) ||
            (formSuccessResponseHeader &&
                formErrorResponseHeader === null &&
                responseData !== null)
        ) {
            window.HTMLUtils.handleFormSuccess(form, xhr, responseData);
        } else if (
            (responseData !== null && status >= 400) ||
            (formErrorResponseHeader &&
                formSuccessResponseHeader === null &&
                responseData !== null)
        ) {
            window.HTMLUtils.handleFormError(form, responseData);
        }
    }
});

document.addEventListener("DOMContentLoaded", function () {
    setupEnableOnChangedValueFields(document);
    setupAutoSubmitOnChange(document);

    const formsToSubmit = document.querySelectorAll("form[data-submit-on-page-load='true']");
    formsToSubmit.forEach(function (form) {
        const submitBtn = form.querySelector("button[type='submit'], input[type='submit']");
        if (submitBtn) {
            submitBtn.click();
        }
    });
});

document.addEventListener("htmx:afterSwap", function (event) {
    if (event.detail && event.detail.target) {
        setupEnableOnChangedValueFields(event.detail.target);
        setupAutoSubmitOnChange(event.detail.target);
    }
});


