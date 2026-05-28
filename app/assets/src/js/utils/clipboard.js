export const ClipboardUtils = (function () {
    "use strict";

    async function copyText(text) {
        const normalized = String(text || "");

        if (navigator.clipboard && typeof navigator.clipboard.writeText === "function") {
            try {
                await navigator.clipboard.writeText(normalized);
                return true;
            } catch (err) {
                console.warn("ClipboardUtils: navigator.clipboard.writeText failed", err);
            }
        }

        const textarea = document.createElement("textarea");
        textarea.value = normalized;
        textarea.setAttribute("readonly", "");
        textarea.style.position = "absolute";
        textarea.style.left = "-9999px";
        document.body.appendChild(textarea);
        textarea.select();

        let successful = false;
        try {
            successful = document.execCommand("copy");
        } catch (err) {
            console.warn("ClipboardUtils: document.execCommand(copy) failed", err);
            successful = false;
        }

        document.body.removeChild(textarea);
        return successful;
    }

    return {
        copyText,
    };
})();
