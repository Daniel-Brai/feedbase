export function PullRefresh(config = {}) {
    return {
        enabled: config.enabled ?? (window.MobileUtils?.isMobile() ?? false),
        threshold: config.threshold ?? 80,
        maxDistance: config.maxDistance ?? 120,
        refreshFn: config.refreshFn || (() => window.location.reload()),

        pulling: false,
        refreshing: false,
        distance: 0,
        startY: 0,
        activeTouchId: null,

        init() {
            if (!this.enabled || typeof window === 'undefined') {
                return;
            }

            this.handleTouchStart = this.handleTouchStart.bind(this);
            this.handleTouchMove = this.handleTouchMove.bind(this);
            this.handleTouchEnd = this.handleTouchEnd.bind(this);

            window.addEventListener('touchstart', this.handleTouchStart, { passive: true });
            window.addEventListener('touchmove', this.handleTouchMove, { passive: false });
            window.addEventListener('touchend', this.handleTouchEnd, { passive: true });
            window.addEventListener('touchcancel', this.handleTouchEnd, { passive: true });
        },

        destroy() {
            window.removeEventListener('touchstart', this.handleTouchStart);
            window.removeEventListener('touchmove', this.handleTouchMove);
            window.removeEventListener('touchend', this.handleTouchEnd);
            window.removeEventListener('touchcancel', this.handleTouchEnd);
        },

        get iconName() {
            return 'arrow_2_circlepath';
        },

        get indicatorStyle() {
            const offset = Math.min(this.distance, this.maxDistance);
            return `transform: translateX(-50%) translateY(calc(-100% + ${offset}px));`;
        },

        handleTouchStart(event) {
            if (this.refreshing || !this.enabled || !this.isAtTop()) {
                return;
            }

            const touch = event.changedTouches[0];
            if (!touch) {
                return;
            }

            this.activeTouchId = touch.identifier;
            this.startY = touch.clientY;
            this.pulling = true;
            this.distance = 0;
        },

        handleTouchMove(event) {
            if (!this.pulling || this.refreshing || this.activeTouchId === null) {
                return;
            }

            const touch = Array.from(event.changedTouches).find(
                (touchItem) => touchItem.identifier === this.activeTouchId,
            );
            if (!touch) {
                return;
            }

            const delta = touch.clientY - this.startY;
            if (delta <= 0) {
                this.distance = 0;
                return;
            }

            if (!this.isAtTop()) {
                return;
            }

            this.distance = Math.min(delta, this.maxDistance);
            event.preventDefault();
        },

        handleTouchEnd(event) {
            if (!this.pulling || this.activeTouchId === null) {
                return;
            }

            const touch = Array.from(event.changedTouches).find(
                (touchItem) => touchItem.identifier === this.activeTouchId,
            );
            if (!touch) {
                this.reset();
                return;
            }

            if (this.distance >= this.threshold) {
                this.refreshing = true;
                this.pulling = false;
                this.distance = this.threshold;

                Promise.resolve(this.refreshFn()).finally(() => {
                    this.refreshing = false;
                    this.reset();
                });
            } else {
                this.reset();
            }
        },

        reset() {
            this.pulling = false;
            this.distance = 0;
            this.activeTouchId = null;
            this.startY = 0;
        },

        isAtTop() {
            return (window.scrollY || window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop) <= 0;
        },
    };
}
