function closeModalIfOpen() {
    if (window.Modal && typeof window.Modal.close === 'function') {
        window.Modal.close();
    }
}

function getSearchInput() {
    return document.querySelector('#articles-pane [x-ref="searchInput"]');
}

function focusSearchInput() {
    const input = getSearchInput();
    if (input) {
        input.focus();
    }
}

function openSearchPanel() {
    closeModalIfOpen();
    const button = document.getElementById('search-button-icon');
    if (button) {
        button.click();
    }
    setTimeout(focusSearchInput, 50);
}

function openAddFeed() {
    closeModalIfOpen();
    const button = document.getElementById('discover-feed-form-retrieve-btn');
    if (button) {
        button.click();
    }
}

function openHtmxLink(url) {
    closeModalIfOpen();

    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('hx-boost', 'true');
    link.setAttribute('hx-push-url', 'true');
    link.style.position = 'absolute';
    link.style.left = '-9999px';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function openSettingsPage() {
    openHtmxLink('/settings');
}

function openHomePage() {
    openHtmxLink('/');
}

function openKeyboardShortcuts() {
    closeModalIfOpen();
    const button = document.getElementById('keyboard-shortcuts-btn');
    if (button) {
        button.click();
    }
}

function showToast(message, type = 'info') {
    if (window.Toast && typeof window.Toast.show === 'function') {
        window.Toast.show({
            message,
            type,
            position: 'bottom-middle',
        });
    }
}

function getKeyboardMessage(key, fallback) {
    return window.KeyboardTranslations?.messages?.[key] || fallback;
}

function getSelectedArticleCard() {
    return document.querySelector('.fb-article-card.fb-article-card-selected');
}

function getSelectedArticleUrl() {
    return getSelectedArticleCard()?.dataset.url || null;
}

function getSelectedArticleFeedTitle() {
    return getSelectedArticleCard()?.querySelector('.fb-article-card-feed-title')?.textContent?.trim() || null;
}

function getSelectedArticleStatusUpdateUrl() {
    return getSelectedArticleCard()?.querySelector('[data-article-status-update-url]')?.dataset.articleStatusUpdateUrl || null;
}

function getSelectedArticleId() {
    return getSelectedArticleCard()?.dataset.articleId || null;
}

function getSelectedArticleReadStatus() {
    return getSelectedArticleCard()?.dataset.statusIsRead === 'true';
}

function updateSelectedArticleReadStatus(value) {
    const card = getSelectedArticleCard();
    if (card) {
        card.dataset.statusIsRead = String(value);
    }
}

function getArticleCards() {
    return Array.from(document.querySelectorAll('.fb-article-card'));
}

function selectArticleCard(card) {
    if (!card) {
        return false;
    }

    card.scrollIntoView({ block: 'nearest', inline: 'nearest' });
    card.dispatchEvent(new MouseEvent('click', {
        bubbles: true,
        cancelable: true,
        view: window,
    }));
    return true;
}

function navigateArticle(delta) {
    const cards = getArticleCards();
    if (!cards.length) {
        return false;
    }

    const selected = getSelectedArticleCard();
    let index = cards.indexOf(selected);

    if (index === -1) {
        index = delta > 0 ? 0 : cards.length - 1;
        return selectArticleCard(cards[index]);
    }

    const nextIndex = Math.max(0, Math.min(cards.length - 1, index + delta));
    if (nextIndex === index) {
        return false;
    }

    return selectArticleCard(cards[nextIndex]);
}

function getScrollableContainer() {
    const readerContent = document.getElementById('reader-content');
    if (readerContent && !readerContent.hidden) {
        return readerContent;
    }

    return document.scrollingElement || document.documentElement || document.body;
}

function scrollToTopContainer() {
    const container = getScrollableContainer();
    if (container === document.scrollingElement || container === document.documentElement || container === document.body) {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    } else {
        container.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

function scrollToBottomContainer() {
    const container = getScrollableContainer();
    if (container === document.scrollingElement || container === document.documentElement || container === document.body) {
        window.scrollTo({ top: document.documentElement.scrollHeight, behavior: 'smooth' });
    } else {
        container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
    }
}

function handleSearchResultNavigation(event) {
    const key = event.key;
    if (key === 'n') {
        event.preventDefault();
        return navigateArticle(1);
    }
    if (key === 'N') {
        event.preventDefault();
        return navigateArticle(-1);
    }
    return false;
}

function clickSelectedArticleActionButton(index) {
    const card = getSelectedArticleCard();
    if (!card) {
        return false;
    }

    const button = card.querySelectorAll('.fb-article-card-actions .fb-article-action-icon')[index];
    if (button) {
        button.click();
        return true;
    }

    return false;
}

async function toggleReadSelectedArticle() {
    const articleId = getSelectedArticleId();
    const statusUrl = getSelectedArticleStatusUpdateUrl();
    if (!articleId || !statusUrl) {
        showToast(getKeyboardMessage('no_selected_article_toggle_read', 'No selected article available to toggle read.'), 'error');
        return false;
    }

    const currentRead = getSelectedArticleReadStatus();
    const url = window.CommonUtils && typeof window.CommonUtils.interpolate === 'function'
        ? window.CommonUtils.interpolate(statusUrl, { article_id: encodeURIComponent(articleId) })
        : statusUrl.replace('{article_id}', encodeURIComponent(articleId));

    try {
        const response = await fetch(url, {
            method: 'PATCH',
            credentials: 'same-origin',
            headers: {
                Accept: 'application/json',
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ is_read: !currentRead }),
        });

        if (!response.ok) {
            throw new Error(`Failed to toggle read status (${response.status})`);
        }

        updateSelectedArticleReadStatus(!currentRead);
        showToast(
            currentRead
                ? getKeyboardMessage('article_marked_as_unread', 'Article marked as unread.')
                : getKeyboardMessage('article_marked_as_read', 'Article marked as read.'),
            'success',
        );
        window.dispatchEvent(new CustomEvent('article-stats-refresh'));
        return true;
    } catch (err) {
        console.error('keyboard.js: toggleReadSelectedArticle failed', err);
        showToast(getKeyboardMessage('unable_to_toggle_read_status', 'Unable to toggle read status.'), 'error');
        return false;
    }
}

function toggleStarSelectedArticle() {
    if (!clickSelectedArticleActionButton(0)) {
        showToast(getKeyboardMessage('no_selected_article_to_star', 'No selected article available to star.'), 'error');
        return false;
    }
    return true;
}

function toggleBookmarkSelectedArticle() {
    if (!clickSelectedArticleActionButton(1)) {
        showToast(getKeyboardMessage('no_selected_article_to_bookmark', 'No selected article available to bookmark.'), 'error');
        return false;
    }
    return true;
}

function openSelectedArticleOriginalUrl() {
    const originalLink = document.getElementById('reader-open-original-link');
    const selectedUrl = getSelectedArticleUrl();
    const url = originalLink && !originalLink.hidden && originalLink.href && originalLink.href !== '#' ? originalLink.href : selectedUrl;

    if (!url) {
        showToast(getKeyboardMessage('no_article_url_to_open', 'No article URL available to open.'), 'error');
        return false;
    }

    window.open(url, '_blank', 'noopener,noreferrer');
    return true;
}

async function copySelectedArticleOriginalUrl() {
    const url = getSelectedArticleUrl();
    if (!url) {
        showToast(getKeyboardMessage('no_article_url_to_copy', 'No article URL available to copy.'), 'error');
        return false;
    }

    const copied = await window.ClipboardUtils?.copyText?.(url);
    if (copied) {
        showToast(getKeyboardMessage('article_url_copied', 'Article URL copied to clipboard.'), 'success');
        return true;
    }

    showToast(getKeyboardMessage('unable_to_copy_article_url', 'Unable to copy the article URL.'), 'error');
    return false;
}

function findSidebarFeedItemByTitle(title) {
    if (!title) {
        return null;
    }

    const items = Array.from(document.querySelectorAll('.fb-sidebar-feed-item'));
    return items.find((item) => {
        const titleElement = item.querySelector('.fb-text-sm2');
        return titleElement && titleElement.textContent.trim() === title;
    }) || null;
}

function unsubscribeSelectedArticleFeed() {
    const feedTitle = getSelectedArticleFeedTitle();
    if (!feedTitle) {
        showToast('No feed selected to unsubscribe.', 'error');
        return false;
    }

    const feedItem = findSidebarFeedItemByTitle(feedTitle);
    if (!feedItem) {
        showToast('Unable to find feed in sidebar.', 'error');
        return false;
    }

    const button = feedItem.querySelector('.fb-sidebar-feed-menu-btn');
    if (!button) {
        showToast('Unable to open feed actions.', 'error');
        return false;
    }

    button.click();
    setTimeout(() => {
        const dangerOption = document.querySelector('.fb-popover-option.danger');
        if (dangerOption) {
            dangerOption.click();
        }
    }, 100);

    return true;
}

function scrollToTop() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function scrollDownHalfPage() {
    window.scrollBy({ top: window.innerHeight * 0.5, behavior: 'smooth' });
}

function getGoToTitle(key, fallback) {
    return window.KeyboardTranslations?.go_to?.[key] || fallback;
}

const goToShortcuts = {
    a: {
        view: 'all',
        title: getGoToTitle('all', 'All articles'),
        filter: {},
    },
    s: {
        view: 'starred',
        title: getGoToTitle('starred', 'Starred'),
        filter: { statuses__is_starred: true },
    },
    b: {
        view: 'bookmarked',
        title: getGoToTitle('bookmarks', 'Bookmarks'),
        filter: { statuses__is_bookmarked: true },
    },
    u: {
        view: 'unread',
        title: getGoToTitle('unread', 'Unread'),
        filter: { statuses__is_read: false },
    },
    t: {
        view: 'today',
        title: getGoToTitle('today', 'Today'),
        filter: { published_at__gte: window.DateTimeUtils?.todayIso() || new Date().toISOString() },
    },
};

function dispatchGoToShortcut(key) {
    const shortcut = goToShortcuts[key];
    if (!shortcut) {
        return false;
    }

    closeModalIfOpen();
    window.dispatchEvent(
        new CustomEvent('article-filter', {
            detail: {
                view: shortcut.view,
                title: shortcut.title,
                filter: shortcut.filter,
            },
        }),
    );
    return true;
}

let sequencePrefix = null;
let sequenceTimer = null;

function resetSequence() {
    sequencePrefix = null;
    if (sequenceTimer) {
        clearTimeout(sequenceTimer);
        sequenceTimer = null;
    }
}

function startSequence(prefix) {
    resetSequence();
    sequencePrefix = prefix;
    sequenceTimer = setTimeout(resetSequence, 800);
}

function handleSequenceKey(key) {
    if (!sequencePrefix) {
        return false;
    }

    if (sequencePrefix === 'g') {
        if (key === 'g') {
            scrollToTopContainer();
            resetSequence();
            return true;
        }

        const handled = dispatchGoToShortcut(key);
        if (handled) {
            resetSequence();
            return true;
        }

        return false;
    }

    if (sequencePrefix === 'y' && key === 'y') {
        copySelectedArticleOriginalUrl();
        resetSequence();
        return true;
    }

    if (sequencePrefix === 'd' && key === 'd') {
        unsubscribeSelectedArticleFeed();
        resetSequence();
        return true;
    }

    return false;
}

function isTypingInInput(event) {
    const target = event.target;
    return (
        target instanceof Element &&
        (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable)
    );
}

window.addEventListener('keydown', (event) => {
    if (event.defaultPrevented) {
        return;
    }

    if (event.ctrlKey || event.metaKey || event.altKey || event.shiftKey) {
        resetSequence();
        return;
    }

    const searchInput = getSearchInput();
    const isSearchInputFocused = searchInput && document.activeElement === searchInput;
    const isTyping = isTypingInInput(event) && !isSearchInputFocused;
    if (isTyping) {
        resetSequence();
        return;
    }

    if (isSearchInputFocused) {
        if (event.key === 'n' || event.key === 'N') {
            handleSearchResultNavigation(event);
        }
        resetSequence();
        return;
    }

    if (sequencePrefix) {
        if (handleSequenceKey(event.key)) {
            event.preventDefault();
            return;
        }
        resetSequence();
    }

    switch (event.key) {
        case 'u':
            event.preventDefault();
            openAddFeed();
            break;
        case '/':
            event.preventDefault();
            openSearchPanel();
            break;
        case 'r':
            event.preventDefault();
            toggleReadSelectedArticle();
            break;
        case 's':
            event.preventDefault();
            toggleStarSelectedArticle();
            break;
        case 'b':
            event.preventDefault();
            toggleBookmarkSelectedArticle();
            break;
        case 'o':
            event.preventDefault();
            openSelectedArticleOriginalUrl();
            break;
        case 'h':
            event.preventDefault();
            openHomePage();
            break;
        case 'e':
            event.preventDefault();
            openSettingsPage();
            break;
        case 'j':
            event.preventDefault();
            navigateArticle(1);
            break;
        case 'k':
            event.preventDefault();
            navigateArticle(-1);
            break;
        case 'g':
            event.preventDefault();
            startSequence('g');
            break;
        case 'y':
            event.preventDefault();
            startSequence('y');
            break;
        case 'd':
            event.preventDefault();
            startSequence('d');
            break;
        case '?':
            event.preventDefault();
            openKeyboardShortcuts();
            break;
        case 'G':
            event.preventDefault();
            scrollToBottomContainer();
            break;
        case 'D':
            if (event.shiftKey) {
                event.preventDefault();
                scrollDownHalfPage();
            }
            break;
        default:
            resetSequence();
            break;
    }
});
