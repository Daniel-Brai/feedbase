export const DateTimeUtils = (function () {
    function relativeTime(dateString) {
        if (!dateString) return "";

        const date = new Date(dateString);
        if (Number.isNaN(date.getTime())) return "";

        const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
        if (seconds < 60) {
            return `${seconds}s ago`;
        }

        const minutes = Math.floor(seconds / 60);
        if (minutes < 60) {
            return `${minutes}m ago`;
        }

        const hours = Math.floor(minutes / 60);
        if (hours < 24) {
            return `${hours}h ago`;
        }

        const days = Math.floor(hours / 24);
        if (days < 7) {
            return `${days}d ago`;
        }

        const weeks = Math.floor(days / 7);
        if (weeks < 5) {
            return `${weeks}w ago`;
        }

        const months = Math.floor(days / 30);
        if (months < 12) {
            return `${months}mo ago`;
        }

        const years = Math.floor(days / 365);
        return `${years}y ago`;
    }

    function renderRelativeTimes(root = document) {
        const elements = root.querySelectorAll("[data-published-at]");
        elements.forEach((el) => {
            const value = el.getAttribute("data-published-at");
            if (value) {
                el.textContent = relativeTime(value);
            }
        });
    }

    function todayIso() {
        const now = new Date();
        now.setHours(0, 0, 0, 0);
        return now.toISOString();
    }

    return {
        relativeTime,
        renderRelativeTimes,
        todayIso,
    };
})();
