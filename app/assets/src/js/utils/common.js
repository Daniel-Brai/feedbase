export const CommonUtils = (function () {
    function truncate(value, maxLength, ellipsis = '…') {
        if (typeof value !== 'string') return '';
        if (maxLength <= 0) return '';
        if (value.length <= maxLength) return value;
        return value.slice(0, Math.max(0, maxLength - ellipsis.length)).trimEnd() + ellipsis;
    }

    function titleize(value) {
        if (typeof value !== 'string') return '';
        return value
            .toLowerCase()
            .split(' ')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    }

    function interpolate(template, params = {}) {
        if (typeof template !== 'string') return '';
        if (params == null || typeof params !== 'object') {
            return template;
        }

        return template.replace(/\{([^}]+)\}/g, (match, key) => {
            if (Object.prototype.hasOwnProperty.call(params, key)) {
                const value = params[key];
                return value != null ? String(value) : '';
            }
            return match;
        });
    }

    function debounce(fn, wait = 250) {
        let timeoutId = null;

        function cancel() {
            if (timeoutId !== null) {
                clearTimeout(timeoutId);
                timeoutId = null;
            }
        }

        function debounced(...args) {
            cancel();
            timeoutId = setTimeout(() => {
                timeoutId = null;
                fn(...args);
            }, wait);
        }

        debounced.cancel = cancel;
        return debounced;
    }

    function getLocalStorage(key, defaultValue = null) {
        if (typeof key !== 'string' || key === '') {
            return defaultValue;
        }

        try {
            const rawValue = localStorage.getItem(key);
            if (rawValue === null) {
                return defaultValue;
            }

            return JSON.parse(rawValue);
        } catch (error) {
            return defaultValue;
        }
    }

    function setLocalStorage(key, value) {
        if (typeof key !== 'string' || key === '') {
            return false;
        }

        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (error) {
            return false;
        }
    }

    function updateLocalStorage(key, updater, defaultValue = null) {
        if (typeof key !== 'string' || key === '') {
            return false;
        }

        const currentValue = getLocalStorage(key, defaultValue);
        const nextValue = typeof updater === 'function' ? updater(currentValue) : updater;

        return setLocalStorage(key, nextValue);
    }

    return {
        truncate,
        titleize,
        interpolate,
        debounce,
        getLocalStorage,
        setLocalStorage,
        updateLocalStorage,
    };

})();
