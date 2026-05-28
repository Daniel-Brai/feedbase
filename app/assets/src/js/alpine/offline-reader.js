export function OfflineReader(labelParams = {}) {
    const { defaultLabel = '', checkingLabel = '' } = labelParams;

    return {
        key: 'feedbase_user_cached_articles',
        articles: [],
        selectedArticle: null,
        emptyTitle: '',
        emptyHint: '',
        defaultLabel,
        checkingLabel,
        label: defaultLabel,

        init() {
            this.emptyTitle = document.getElementById('offline-empty-title')?.textContent || '';
            this.emptyHint = document.getElementById('offline-empty-hint')?.textContent || '';
            this.loadArticles();
        },

        resetButtonLabel() {
            setTimeout(() => {
                this.label = this.defaultLabel;
            }, 1800);
        },

        async checkConnection() {
            this.label = this.checkingLabel;

            if (!window.navigator.onLine) {
                this.resetButtonLabel();
                return;
            }

            try {
                await fetch('https://example.com/', {
                    cache: 'no-store',
                    mode: 'no-cors',
                });

                window.location.href = '/';
                return;
            } catch (error) { }

            this.resetButtonLabel();
        },

        loadArticles() {
            let data = [];
            if (window.CommonUtils && typeof window.CommonUtils.getLocalStorage === 'function') {
                data = window.CommonUtils.getLocalStorage(this.key, []);
            } else {
                try {
                    const raw = window.localStorage.getItem(this.key);
                    if (raw) {
                        const parsed = JSON.parse(raw);
                        data = Array.isArray(parsed) ? parsed : [];
                    }
                } catch (error) {
                    data = [];
                }
            }

            this.articles = Array.isArray(data) ? data : [];
        },

        openArticle(index) {
            const article = this.articles[index] || null;
            if (!article || !window.Sheet) {
                return;
            }

            const content = article.content || article.summary || `<div class="fb-reader-empty-text">${this.emptyTitle}</div>`;
            const html = `
                <div class="fb-reader-article">
                    <div id="reader-content">${content}</div>
                </div>
            `;

            window.Sheet.show({
                sheet_class: 'fb-sheet-reader',
                content_format: 'html',
                content_html: html,
            });
        },

        closeReader() {
            if (window.Sheet && typeof window.Sheet.hide === 'function') {
                window.Sheet.hide();
            }
            this.selectedArticle = null;
        },

        get hasArticles() {
            return this.articles.length > 0;
        },

        get renderedContent() {
            if (!this.selectedArticle) {
                return '';
            }
            return this.selectedArticle.content || this.selectedArticle.summary || `<div class="fb-reader-empty-text">${this.emptyTitle}</div>`;
        },

        truncate(value, maxLength) {
            if (window.CommonUtils && typeof window.CommonUtils.truncate === 'function') {
                return window.CommonUtils.truncate(value, maxLength);
            }
            if (typeof value !== 'string') {
                return '';
            }
            if (maxLength <= 0) {
                return '';
            }
            if (value.length <= maxLength) {
                return value;
            }
            return value.slice(0, maxLength - 1).trimEnd() + '…';
        },
    };
}
