export function ArticleStats(apiUrl) {
    return {
        apiUrl,
        loading: false,
        loaded: false,
        error: null,
        selectedView: 'all',
        stats: {
            total: 0,
            unread: 0,
            starred: 0,
            bookmarked: 0,
            today: 0,
        },

        init() {
            if (this.loading || this.loaded) {
                return;
            }
            this._statsRefreshListener = this.load.bind(this);
            this._articleFilterListener = (event) => {
                this.onArticleFilter(event.detail);
            };
            window.addEventListener('article-stats-refresh', this._statsRefreshListener);
            window.addEventListener('article-filter', this._articleFilterListener);
            this.load();
        },

        async load() {
            if (this.loading) {
                return;
            }

            if (!this.apiUrl) {
                this.error = "Article stats endpoint is not configured.";
                this.loading = false;
                return;
            }

            this.loading = true;

            try {
                const response = await fetch(this.apiUrl, {
                    headers: {
                        "X-Requested-With": "XMLHttpRequest",
                        "Accept": "application/json",
                    },
                    credentials: "include",
                });

                if (!response.ok) {
                    throw new Error(`Failed to load stats (${response.status})`);
                }

                const payload = await response.json();
                const data = payload?.data || {};

                this.stats = {
                    total: data.total ?? 0,
                    unread: data.unread ?? 0,
                    starred: data.starred ?? 0,
                    bookmarked: data.bookmarked ?? 0,
                    today: data.today ?? 0,
                };
                this.loaded = true;
                window.dispatchEvent(
                    new CustomEvent('article-stats-updated', {
                        detail: { unread: this.stats.unread },
                    })
                );
            } catch (err) {
                this.error = err?.message || "Unable to load article stats.";
            } finally {
                this.loading = false;
            }
        },

        selectView(view, title, params) {
            this.selectedView = view;
            window.dispatchEvent(
                new CustomEvent('article-filter', {
                    detail: { view, filter: params || {}, title },
                })
            );

            if (window.MobileUtils?.isMobile()) {
                window.dispatchEvent(
                    new CustomEvent('switch-pane', { detail: 1 })
                );
            }
        },

        format(value) {
            return new Intl.NumberFormat().format(value ?? 0);
        },

        onArticleFilter(detail) {
            if (!detail) {
                return;
            }
            if (detail.view) {
                this.selectedView = detail.view;
                return;
            }
            const filter = detail.filter || {};
            if (filter.statuses__is_read === false) {
                this.selectedView = 'unread';
            } else if (filter.statuses__is_starred === true) {
                this.selectedView = 'starred';
            } else if (filter.statuses__is_bookmarked === true) {
                this.selectedView = 'bookmarked';
            } else if (filter.published_at__gte) {
                this.selectedView = 'today';
            } else {
                this.selectedView = 'all';
            }
        },

        destroy() {
            if (this._statsRefreshListener) {
                window.removeEventListener('article-stats-refresh', this._statsRefreshListener);
                this._statsRefreshListener = null;
            }
            if (this._articleFilterListener) {
                window.removeEventListener('article-filter', this._articleFilterListener);
                this._articleFilterListener = null;
            }
        },
    };
}
