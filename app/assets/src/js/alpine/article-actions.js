export function ArticleActions() {
    let articleId = null;
    let apiUrl = null;
    let initialStarredValue = false;
    let initialBookmarkedValue = false;
    let starTitleValue = 'Star';
    let bookmarkTitleValue = 'Bookmark';
    let starredMessageValue = 'Article starred';
    let unstarredMessageValue = 'Article unstarred';
    let bookmarkedMessageValue = 'Article bookmarked';
    let unbookmarkedMessageValue = 'Article unbookmarked';

    function initFromElement(el) {
        if (!el) return;
        articleId = el.dataset.articleId || el.closest('.fb-article-card')?.dataset.articleId || null;
        apiUrl = el.dataset.articleStatusUpdateUrl || apiUrl;
        initialStarredValue = el.dataset.initialStarred;
        initialBookmarkedValue = el.dataset.initialBookmarked;
        starTitleValue = el.dataset.starTitle || starTitleValue;
        bookmarkTitleValue = el.dataset.bookmarkTitle || bookmarkTitleValue;
        starredMessageValue = el.dataset.starredMessage || starredMessageValue;
        unstarredMessageValue = el.dataset.unstarredMessage || unstarredMessageValue;
        bookmarkedMessageValue = el.dataset.bookmarkedMessage || bookmarkedMessageValue;
        unbookmarkedMessageValue = el.dataset.unbookmarkedMessage || unbookmarkedMessageValue;
    }
    function parseBool(value) {
        return value === true || value === 'true' || value === '1' || value === 1;
    }

    function resolveUrl(url, articleId) {
        if (!url || !articleId) return null;
        if (window.CommonUtils && typeof window.CommonUtils.interpolate === 'function') {
            return window.CommonUtils.interpolate(url, { article_id: encodeURIComponent(articleId) });
        }
        return url.replace('{article_id}', encodeURIComponent(articleId));
    }

    async function refreshArticles() {
        const paginationEl = document.getElementById('articles');
        if (!paginationEl || !window.htmx || !window.htmx.pagination || typeof window.htmx.pagination.silentRefresh !== 'function') {
            return;
        }
        window.htmx.pagination.getInstance(paginationEl)?.reload();
    }

    async function showToast(message, type = 'success') {
        if (window.Toast && typeof window.Toast.show === 'function') {
            window.Toast.show({
                message,
                type,
                position: 'bottom-middle',
            });
        }
    }

    async function updateArticleStatus(payload, successMessage) {
        if (!articleId) {
            console.warn('ArticleActions: missing article ID');
            return false;
        }

        const url = resolveUrl(apiUrl, articleId);
        if (!url) {
            console.warn('ArticleActions: missing articleStatusUpdateUrl');
            return false;
        }

        try {
            const response = await fetch(url, {
                method: 'PATCH',
                credentials: 'same-origin',
                headers: {
                    Accept: 'application/json',
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                const text = await response.text();
                const message = text || 'Unable to update article status.';
                showToast(message, 'error');
                return false;
            }

            showToast(successMessage, 'success');
            await refreshArticles();
            window.dispatchEvent(
                new CustomEvent('article-stats-refresh', {
                    detail: { articleId: articleId },
                }),
            );
            return true;
        } catch (error) {
            console.error('ArticleActions: status update failed', error);
            showToast('Unable to update article status.', 'error');
            return false;
        }
    }

    return {
        articleId,
        articleStatusUpdateUrl: apiUrl,
        isStarred: parseBool(initialStarredValue),
        isBookmarked: parseBool(initialBookmarkedValue),
        starTitle: starTitleValue,
        bookmarkTitle: bookmarkTitleValue,
        starredMessage: starredMessageValue,
        unstarredMessage: unstarredMessageValue,
        bookmarkedMessage: bookmarkedMessageValue,
        unbookmarkedMessage: unbookmarkedMessageValue,

        init() {
            initFromElement(this.$el);
            this.articleId = articleId;
            this.articleStatusUpdateUrl = apiUrl;
            this.isStarred = parseBool(initialStarredValue);
            this.isBookmarked = parseBool(initialBookmarkedValue);
            this.starTitle = starTitleValue;
            this.bookmarkTitle = bookmarkTitleValue;
            this.starredMessage = starredMessageValue;
            this.unstarredMessage = unstarredMessageValue;
            this.bookmarkedMessage = bookmarkedMessageValue;
            this.unbookmarkedMessage = unbookmarkedMessageValue;
        },

        async toggleStar() {
            const target = !this.isStarred;
            const success = await updateArticleStatus(
                { is_starred: target },
                target ? this.starredMessage : this.unstarredMessage,
            );
            if (success) {
                this.isStarred = target;
            }
        },

        async toggleBookmark() {
            const target = !this.isBookmarked;
            const success = await updateArticleStatus(
                { is_bookmarked: target },
                target ? this.bookmarkedMessage : this.unbookmarkedMessage,
            );
            if (success) {
                this.isBookmarked = target;
            }
        },
    };
}
