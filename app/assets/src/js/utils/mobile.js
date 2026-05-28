export const MobileUtils = (function () {
    function isTouchDevice() {
        return (
            typeof window !== 'undefined' &&
            ('ontouchstart' in window || navigator.maxTouchPoints > 0 || navigator.msMaxTouchPoints > 0)
        );
    }

    function isViewportMobile() {
        return typeof window !== 'undefined' && window.matchMedia('(max-width: 768px)').matches;
    }

    function isMobile() {
        return isViewportMobile() || isTouchDevice();
    }

    return {
        isTouchDevice,
        isViewportMobile,
        isMobile,
    };
})();
