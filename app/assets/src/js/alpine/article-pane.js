export function ArticlePane(
    articlesUrl,
    initialTitle = 'All Articles',
    articleAnnotationsCountUrl = '',
    annotationsUrl = '',
    annotationsCreateUrl = '',
    annotationUpdateUrl = '',
    annotationDeleteUrl = '',
) {
    return {
        articlesUrl,
        articleAnnotationsCountUrl,
        annotationsUrl,
        annotationsCreateUrl,
        annotationUpdateUrl,
        annotationDeleteUrl,
        title: initialTitle,
        searchVisible: false,
        searchQuery: '',
        currentView: 'all',
        selectedArticleId: null,
        currentContent: '',
        originalUrl: '',
        annotationActive: false,
        annotationsVisible: false,
        annotations: [],
        annotationSelection: null,
        annotationPopover: null,
        annotationPointerDown: false,
        annotationKeyboardActive: false,
        annotationCountFetchedFor: null,
        articleTextNodes: [],
        articleTextLength: 0,
        articleText: '',
        debouncedSearch: null,

        init() {
            this.debouncedSearch = window.CommonUtils.debounce(this.applySearch.bind(this), 250);
            this.titleizeFeedTitles();
            this.updateAnnotationToggleVisibility();
            this.bindAnnotationToolbar();

            const persistedSelection = this.loadSelectedArticleFromStorage();
            if (persistedSelection) {
                this.selectedArticleId = persistedSelection.id;
                this.originalUrl = persistedSelection.url;
                this.currentContent = persistedSelection.content;
                this.updateOpenOriginalLink(this.originalUrl);
                this.updateSelectedArticleCard();
                this.updateAnnotationToggleVisibility();
                if (this.currentContent) {
                    this.renderArticleContent(this.currentContent);
                    if (this.annotationCountFetchedFor !== this.selectedArticleId) {
                        this.fetchArticleAnnotationCount(this.selectedArticleId);
                    }
                    if (this.annotationsVisible) {
                        this.fetchArticleAnnotations(this.selectedArticleId);
                    }
                }
            }

            document.addEventListener('pointerdown', (event) => {
                if (!this.annotationActive) {
                    return;
                }

                if (document.getElementById('reader-content')?.contains(event.target)) {
                    this.annotationPointerDown = true;
                }
            });

            document.addEventListener('pointerup', () => {
                if (!this.annotationActive) {
                    return;
                }

                if (this.annotationPointerDown) {
                    this.annotationPointerDown = false;
                    requestAnimationFrame(() => {
                        this.handleReaderSelection();
                    });
                }
            });

            document.addEventListener('keydown', (event) => {
                if (!this.annotationActive) {
                    return;
                }

                if (event.key === 'Shift') {
                    this.annotationKeyboardActive = true;
                }
            });

            document.addEventListener('keyup', (event) => {
                if (!this.annotationActive) {
                    return;
                }

                if (event.key === 'Shift') {
                    this.annotationKeyboardActive = false;
                    requestAnimationFrame(() => {
                        this.handleReaderSelection();
                    });
                }
            });

            document.addEventListener('selectionchange', () => {
                if (!this.annotationActive || this.annotationPointerDown || this.annotationKeyboardActive) {
                    return;
                }

                requestAnimationFrame(() => {
                    this.handleReaderSelection();
                });
            });

            const articlesEl = this.$el?.querySelector('#articles') || document.getElementById('articles');
            if (articlesEl) {
                articlesEl.addEventListener('click', (event) => {
                    const card = event.target.closest('.fb-article-card');
                    if (!card || !articlesEl.contains(card)) {
                        return;
                    }

                    const articleId = card.dataset.articleId;
                    const content = card.dataset.content || '';
                    const articleUrl = card.dataset.url || '';
                    if (!articleId) {
                        return;
                    }

                    this.markArticleRead(articleId, card);
                    this.selectArticle(articleId, content, articleUrl);
                });
            }

            this.isMobileViewport = window.MobileUtils?.isViewportMobile() ?? false;
            this._handleMobileResize = () => {
                const isMobileViewport = window.MobileUtils?.isViewportMobile() ?? false;
                if (!this.isMobileViewport && isMobileViewport && this.selectedArticleId) {
                    window.dispatchEvent(new CustomEvent('switch-pane', { detail: 2 }));
                }
                this.isMobileViewport = isMobileViewport;
            };
            window.addEventListener('resize', this._handleMobileResize);
        },

        onFilter(detail) {
            if (!detail || !detail.filter) {
                return;
            }

            this.currentView = detail.view || this.deriveViewFromFilters(detail.filter);
            this.title = detail.title || initialTitle;
            const paginationEl = document.getElementById('articles');
            if (!paginationEl || !window.htmx || !window.htmx.pagination) {
                return;
            }

            const controller = window.htmx.pagination.getInstance(paginationEl);
            if (!controller) {
                return;
            }

            this.setPaginationParams(controller, this.buildSearchParams(detail.filter));
        },

        deriveViewFromFilters(filters) {
            if (!filters) {
                return 'all';
            }

            if (filters.statuses__is_read === false) {
                return 'unread';
            }
            if (filters.statuses__is_starred === true) {
                return 'starred';
            }
            if (filters.statuses__is_bookmarked === true) {
                return 'bookmarked';
            }
            if (filters.published_at__gte) {
                return 'today';
            }

            return 'all';
        },

        getViewFilter(view) {
            switch (view) {
                case 'unread':
                    return { statuses__is_read: false };
                case 'starred':
                    return { statuses__is_starred: true };
                case 'bookmarked':
                    return { statuses__is_bookmarked: true };
                case 'today':
                    return { published_at__gte: window.DateTimeUtils?.todayIso() };
                default:
                    return {};
            }
        },

        buildSearchParams(filter) {
            const params = Object.assign({}, filter || {});
            const query = this.searchQuery?.trim();
            params.search = query || undefined;
            return params;
        },

        onSearchInput(value) {
            this.searchQuery = value;
            this.debouncedSearch();
        },

        setPaginationParams(controller, params) {
            if (controller && controller.config) {
                controller.config.extraParams = {};
            }
            controller.setParams(params);
        },

        applySearch() {
            const paginationEl = document.getElementById('articles');
            if (!paginationEl || !window.htmx || !window.htmx.pagination) {
                return;
            }

            const controller = window.htmx.pagination.getInstance(paginationEl);
            if (!controller) {
                return;
            }

            const params = this.getViewFilter(this.currentView);
            params.search = this.searchQuery?.trim() || undefined;

            this.setPaginationParams(controller, params);
        },

        clearOrCloseSearch() {
            const query = this.searchQuery.trim();
            if (query) {
                this.searchQuery = '';
                this.applySearch();
                this.searchVisible = false;
                return;
            }

            this.searchVisible = false;
            this.applySearch();
        },

        toggleSearch() {
            this.searchVisible = !this.searchVisible;
            if (this.searchVisible) {
                this.$nextTick(() => {
                    if (this.$refs?.searchInput) {
                        this.$refs.searchInput.focus();
                    }
                });
            }
        },

        renderRelativeTimes() {
            const root = this.$el || document.getElementById('articles-pane');
            if (window.DateTimeUtils) {
                window.DateTimeUtils.renderRelativeTimes(root);
            }
            this.titleizeFeedTitles(root);
            this.truncateArticleText(root);
            this.restoreSelectedArticle();
        },

        titleizeFeedTitles(root = document) {
            if (!window.CommonUtils || typeof window.CommonUtils.titleize !== 'function') {
                return;
            }

            document.querySelectorAll('.fb-article-card-feed-title')?.forEach((el) => {
                const text = el.textContent?.trim();
                if (text) {
                    el.textContent = window.CommonUtils.titleize(text);
                }
            });
        },

        truncateArticleText(root = document) {
            if (!window.CommonUtils) {
                return;
            }
            const container = root || document;

            container.querySelectorAll('.fb-article-summary').forEach((el) => {
                const text = el.textContent || '';
                el.textContent = window.CommonUtils.truncate(text, 130);
            });

            container.querySelectorAll('.fb-article-title').forEach((el) => {
                const text = el.textContent || '';
                el.textContent = window.CommonUtils.truncate(text, 70);
            });
        },

        selectArticle(articleId, content, articleUrl) {
            if (!articleId) {
                return;
            }

            const isSameArticle = this.selectedArticleId === articleId;
            if (isSameArticle) {
                if (window.MobileUtils?.isMobile()) {
                    window.dispatchEvent(new CustomEvent('switch-pane', { detail: 2 }));
                }
                return;
            }

            this.selectedArticleId = articleId;
            this.originalUrl = articleUrl || '';
            this.updateOpenOriginalLink(this.originalUrl);
            this.currentContent = this.normalizeRelativeLinks(content || '', articleUrl);
            this.persistSelectedArticle();
            this.updateSelectedArticleCard();
            this.updateAnnotationToggleVisibility();
            this.renderArticleContent(this.currentContent);
            if (this.annotationCountFetchedFor !== articleId) {
                this.fetchArticleAnnotationCount(articleId);
            }
            if (this.annotationsVisible) {
                this.fetchArticleAnnotations(articleId);
            }
            this.bindAnnotationToolbar();
            this.updateAnnotationToolbarState();

            if (window.MobileUtils?.isMobile()) {
                window.dispatchEvent(new CustomEvent('switch-pane', { detail: 2 }));
            }
        },

        updateOpenOriginalLink(url) {
            const wrapper = document.getElementById('reader-open-original-link');
            if (!wrapper) {
                return;
            }

            const link = wrapper.querySelector('a');
            if (!link) {
                return;
            }

            if (url) {
                link.href = url;
                wrapper.hidden = false;
                link.removeAttribute('aria-disabled');
            } else {
                link.href = '#';
                wrapper.hidden = true;
                link.setAttribute('aria-disabled', 'true');
            }
        },

        updateAnnotationToggleVisibility() {
            const count = document.getElementById('reader-annotation-count');
            const isVisible = Boolean(this.selectedArticleId);

            if (count) {
                count.hidden = !isVisible;
                if (!isVisible) {
                    count.textContent = '';
                    count.dataset.count = '0';
                    count.title = '';
                }
            }

            this.updateAnnotationToolbarState();
        },

        async fetchArticleAnnotationCount(articleId, force = false) {
            const countEl = document.getElementById('reader-annotation-count');
            if (!this.articleAnnotationsCountUrl || !countEl || (!force && this.annotationCountFetchedFor === articleId)) {
                return;
            }

            const url = window.CommonUtils?.interpolate(
                this.articleAnnotationsCountUrl,
                { article_id: encodeURIComponent(articleId) }
            );

            if (!url) {
                return;
            }

            try {
                const response = await fetch(url, {
                    method: 'GET',
                    credentials: 'same-origin',
                    headers: { Accept: 'application/json' },
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                const json = await response.json();
                const count = typeof json?.data === 'number' ? json.data : null;

                if (count === null) {
                    throw new Error('Invalid annotation count response');
                }


                countEl.dataset.count = String(count);
                countEl.textContent = `${count}`;
                countEl.title = `${count} annotations`;
                countEl.hidden = false;
                countEl.classList.add('fb-bg-accent');

                this.annotationCountFetchedFor = articleId;
                this.updateAnnotationToggleVisibility();
            } catch (error) {
                console.error('ArticlePane: failed to load annotation count', error);
                if (countEl) {
                    countEl.hidden = true;
                }
            }
        },

        bindAnnotationToolbar() {
            const showButton = document.getElementById('reader-annotation-show-btn');
            const modeButton = document.getElementById('reader-annotation-mode-btn');

            if (showButton && !showButton.dataset.listenerAttached) {
                showButton.addEventListener('click', this.toggleAnnotationVisibility.bind(this));
                showButton.dataset.listenerAttached = 'true';
            }

            if (modeButton && !modeButton.dataset.listenerAttached) {
                modeButton.addEventListener('click', this.toggleAnnotationMode.bind(this));
                modeButton.dataset.listenerAttached = 'true';
            }
        },

        async toggleAnnotationVisibility() {
            this.annotationsVisible = !this.annotationsVisible;
            if (this.annotationsVisible && this.selectedArticleId) {
                await this.fetchArticleAnnotations(this.selectedArticleId);
                this.clearAnnotationHighlights();
                this.renderAnnotations();
            } else {
                this.clearAnnotationHighlights();
            }

            this.closeAnnotationPopover();
            this.updateAnnotationToolbarState();
        },

        toggleAnnotationMode() {
            this.annotationActive = !this.annotationActive;
            if (!this.annotationActive) {
                this.closeAnnotationPopover(true);
                window.getSelection()?.removeAllRanges();
            }
            this.updateAnnotationToolbarState();
        },

        updateAnnotationToolbarState() {
            const toolbar = document.getElementById('reader-annotation-toolbar');
            const showButton = document.getElementById('reader-annotation-show-btn');
            const modeButton = document.getElementById('reader-annotation-mode-btn');

            if (!toolbar || !showButton || !modeButton) {
                return;
            }

            if (!this.selectedArticleId) {
                toolbar.hidden = true;
                return;
            }

            toolbar.hidden = false;

            const showIcon = showButton.querySelector('i.f7-icons');
            if (this.annotationsVisible) {
                showButton.classList.add('fb-annotation-toggle-btn-active');
                showButton.setAttribute('aria-pressed', 'true');
                showButton.title = showButton.dataset.annotationOnTitle || 'Hide annotations';
                if (showIcon) {
                    showIcon.textContent = 'eye_slash';
                }
            } else {
                showButton.classList.remove('fb-annotation-toggle-btn-active');
                showButton.setAttribute('aria-pressed', 'false');
                showButton.title = showButton.dataset.annotationOffTitle || 'Show annotations';
                if (showIcon) {
                    showIcon.textContent = 'eye';
                }
            }

            if (this.annotationActive) {
                modeButton.classList.add('fb-annotation-toggle-btn-active');
                modeButton.setAttribute('aria-pressed', 'true');
                modeButton.title = modeButton.dataset.annotationModeOnTitle || 'Annotation mode on';
            } else {
                modeButton.classList.remove('fb-annotation-toggle-btn-active');
                modeButton.setAttribute('aria-pressed', 'false');
                modeButton.title = modeButton.dataset.annotationModeOffTitle || 'Enable annotation mode';
            }
        },

        async fetchArticleAnnotations(articleId) {
            if (!this.annotationsUrl || !articleId) {
                this.annotations = [];
                return;
            }

            const url = window.CommonUtils?.interpolate(
                this.annotationsUrl,
                { article_id: encodeURIComponent(articleId) }
            );
            if (!url) {
                this.annotations = [];
                return;
            }

            try {
                const countEl = document.getElementById('reader-annotation-count');
                const savedCount = countEl ? parseInt(countEl.dataset.count, 10) : NaN;
                const size = Number.isInteger(savedCount) && savedCount > 0 ? savedCount : 20;
                const response = await fetch(`${url}?size=${size}`, {
                    method: 'GET',
                    credentials: 'same-origin',
                    headers: { Accept: 'application/json' },
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                const json = await response.json();
                this.annotations = Array.isArray(json?.data) ? json.data : [];
                if (this.annotationsVisible) {
                    this.clearAnnotationHighlights();
                    this.renderAnnotations();
                }
            } catch (error) {
                console.error('ArticlePane: failed to load annotations', error);
                this.annotations = [];
            }
        },

        handleReaderSelection() {
            if (!this.annotationActive) {
                return;
            }

            const selection = window.getSelection();
            if (!selection || selection.isCollapsed) {
                return;
            }

            const anchorNode = selection.anchorNode;
            if (!anchorNode || !document.getElementById('reader-content')?.contains(anchorNode)) {
                return;
            }

            const range = selection.getRangeAt(0);
            if (!range || range.collapsed) {
                return;
            }

            let start = this.getTextOffset(range.startContainer, range.startOffset);
            let end = this.getTextOffset(range.endContainer, range.endOffset);
            if (start === null || end === null || start >= end) {
                const selectedText = (range.toString() || '').trim();
                if (selectedText) {
                    const found = this.articleText?.indexOf(selectedText) ?? -1;
                    if (found !== -1) {
                        start = found;
                        end = found + selectedText.length;
                    }
                }
            }
            if (start === null || end === null || start >= end) {
                return;
            }

            const text = this.articleText?.slice(start, end)?.trim();
            if (!text) {
                return;
            }

            const rect = range.getBoundingClientRect();
            if (!rect.width && !rect.height) {
                return;
            }

            this.annotationSelection = { start, end, text, rect };
            this.createAnnotationPreview(range);
            this.openAnnotationCreationPopover();
        },

        closeAnnotationPopover(clearPreview = false) {
            if (!this.annotationPopover) {
                if (clearPreview) {
                    this.clearAnnotationPreview();
                }
                return;
            }

            if (this.annotationPopover.dismissHandler) {
                document.removeEventListener('mousedown', this.annotationPopover.dismissHandler);
                document.removeEventListener('touchstart', this.annotationPopover.dismissHandler);
            }
            if (this.annotationPopover.escapeHandler) {
                document.removeEventListener('keydown', this.annotationPopover.escapeHandler);
            }

            const popoverEl = this.annotationPopover.el || this.annotationPopover;
            if (popoverEl && typeof popoverEl.remove === 'function') {
                popoverEl.remove();
            }

            this.annotationPopover = null;
            if (clearPreview) {
                this.clearAnnotationPreview();
                this.annotationSelection = null;
            }
        },

        openAnnotationCreationPopover() {
            if (!this.annotationSelection) {
                return;
            }

            this.closeAnnotationPopover();

            const popover = document.createElement('div');
            popover.className = 'fb-popover fb-reader-annotation-popover fb-bg-surface fb-border fb-border-surface2 fb-rounded-lg';
            popover.setAttribute('role', 'dialog');
            popover.style.position = 'absolute';
            popover.style.zIndex = '9999';
            popover.style.width = '280px';
            popover.style.padding = '0.5rem';
            popover.style.color = 'var(--text)';

            const translations = window.ArticlePaneTranslations || {};
            const body = document.createElement('div');
            body.className = 'fb-popover-body';

            const title = document.createElement('div');
            title.className = 'fb-text-sm fb-font-medium fb-text-text fb-mb-2';
            title.textContent = translations.createHighlightTitle || 'Create highlight';
            body.appendChild(title);

            const colorGroup = document.createElement('div');
            colorGroup.className = 'fb-flex fb-items-center fb-gap-2 fb-mt-3';
            const colorMap = {
                yellow: 'rgba(250,204,21,0.9)',
                green: 'rgba(74,222,128,0.9)',
                blue: 'rgba(96,165,250,0.9)',
                red: 'rgba(248,113,113,0.9)',
            };
            const ringMap = {
                yellow: 'rgba(250,204,21,0.18)',
                green: 'rgba(74,222,128,0.18)',
                blue: 'rgba(96,165,250,0.18)',
                red: 'rgba(248,113,113,0.18)',
            };
            let selectedColor = 'yellow';
            let noteInput;

            const pickColor = (button, color) => {
                colorGroup.querySelectorAll('button').forEach((btn) => {
                    btn.style.border = '2px solid transparent';
                    btn.style.boxShadow = 'none';
                });
                button.style.border = '2px solid var(--text)';
                button.style.boxShadow = `0 0 0 6px ${ringMap[color]}`;
                selectedColor = color;
                if (noteInput) {
                    noteInput.dataset.selectedColor = color;
                }
            };

            ['yellow', 'green', 'blue', 'red'].forEach((color) => {
                const button = document.createElement('button');
                button.type = 'button';
                button.dataset.color = color;
                button.className = 'fb-reader-annotation-color-option';
                button.style.background = colorMap[color];
                button.style.border = '2px solid transparent';
                button.style.width = '1rem';
                button.style.height = '1rem';
                button.style.borderRadius = '50%';
                button.style.cursor = 'pointer';
                button.style.padding = '0';
                button.addEventListener('click', () => pickColor(button, color));
                colorGroup.appendChild(button);
                if (color === selectedColor) {
                    pickColor(button, color);
                }
            });
            body.appendChild(colorGroup);

            noteInput = document.createElement('textarea');
            noteInput.className = 'fb-textarea fb-w-full';
            noteInput.rows = 3;
            noteInput.placeholder = translations.notePlaceholder || 'Add a note (optional)';
            noteInput.dataset.selectedColor = selectedColor;
            noteInput.style.marginTop = '0.75rem';
            noteInput.style.resize = 'vertical';
            body.appendChild(noteInput);

            const actions = document.createElement('div');
            actions.className = 'fb-flex fb-justify-end fb-gap-2 fb-mt-4';

            const cancelButton = document.createElement('button');
            cancelButton.type = 'button';
            cancelButton.className = 'fb-btn fb-btn-ghost fb-text-sm';
            cancelButton.textContent = translations.cancelButton || 'Cancel';
            cancelButton.addEventListener('click', () => this.closeAnnotationPopover(true));
            actions.appendChild(cancelButton);

            const saveButton = document.createElement('button');
            saveButton.type = 'button';
            saveButton.className = 'fb-btn fb-text-sm fb-bg-accent fb-text-bg fb-rounded-full fb-px-3 fb-py-2';
            saveButton.textContent = translations.highlightButton || 'Highlight';
            saveButton.addEventListener('click', () => {
                const color = noteInput.dataset.selectedColor || 'yellow';
                const note = noteInput.value.trim() || null;
                this.saveAnnotation(color, note);
            });
            actions.appendChild(saveButton);
            body.appendChild(actions);

            popover.appendChild(body);
            document.body.appendChild(popover);
            this.positionPopover(popover, this.annotationSelection.rect);

            const dismissHandler = (event) => {
                if (!popover.contains(event.target)) {
                    this.closeAnnotationPopover(true);
                }
            };
            const escapeHandler = (event) => {
                if (event.key === 'Escape') {
                    this.closeAnnotationPopover(true);
                }
            };
            document.addEventListener('mousedown', dismissHandler);
            document.addEventListener('touchstart', dismissHandler, { passive: true });
            document.addEventListener('keydown', escapeHandler);

            this.annotationPopover = { el: popover, dismissHandler, escapeHandler };
            noteInput.focus();
        },

        createAnnotationPreview(range) {
            this.clearAnnotationPreview();
            if (!range) {
                return;
            }

            const wrapper = document.createElement('span');
            wrapper.className = 'fb-reader-annotation-preview';
            wrapper.style.background = 'rgba(250, 204, 21, 0.30)';
            wrapper.style.boxShadow = 'inset 0 -2px 0 #ca8a04';
            wrapper.style.borderRadius = '0.35rem';

            try {
                range.surroundContents(wrapper);
            } catch (error) {
                const fragment = range.extractContents();
                wrapper.appendChild(fragment);
                range.insertNode(wrapper);
            }

            this.annotationSelection = {
                ...this.annotationSelection,
                previewWrapper: wrapper,
            };
            window.getSelection()?.removeAllRanges();
        },

        clearAnnotationPreview() {
            if (!this.annotationSelection?.previewWrapper) {
                return;
            }

            const wrapper = this.annotationSelection.previewWrapper;
            const parent = wrapper.parentNode;
            if (!parent) {
                return;
            }

            while (wrapper.firstChild) {
                parent.insertBefore(wrapper.firstChild, wrapper);
            }
            parent.removeChild(wrapper);
            delete this.annotationSelection.previewWrapper;
        },

        normalizeNestedPreElements(container) {
            const nestedPres = container.querySelectorAll('pre > pre');
            nestedPres.forEach((innerPre) => {
                const outerPre = innerPre.parentNode;
                while (outerPre.firstChild !== innerPre) {
                    outerPre.parentNode.insertBefore(outerPre.firstChild, outerPre);
                }
                outerPre.parentNode.replaceChild(innerPre, outerPre);
            });
        },

        attachCodeCopyButtons(contentPane) {
            if (!contentPane) {
                return;
            }

            contentPane.querySelectorAll('pre').forEach((pre) => {
                if (pre.closest('pre') !== pre) return;
                if (pre.dataset.copyButtonAttached) return;

                pre.style.position = 'relative';
                const button = document.createElement('button');
                button.type = 'button';
                button.className = 'fb-code-copy-button';
                const translations = window.ArticlePaneTranslations || {};
                const copyButtonLabel = translations.copyButtonLabel || 'Copy code';
                button.setAttribute('aria-label', copyButtonLabel);
                button.title = copyButtonLabel;
                const icon = document.createElement('i');
                icon.className = 'f7-icons';
                icon.textContent = 'square_on_square';
                button.appendChild(icon);
                button.style.position = 'absolute';
                button.style.top = '0.75rem';
                button.style.right = '0.75rem';
                button.style.zIndex = '10';
                button.style.opacity = '0.95';
                button.style.background = 'rgba(255, 255, 255, 0.16)';
                button.style.color = 'var(--text)';
                button.style.border = '1px solid rgba(255, 255, 255, 0.12)';
                button.style.borderRadius = '0.5rem';
                button.style.padding = '0 0.5rem';
                button.style.minWidth = '2rem';
                button.style.height = '2rem';
                button.style.display = 'inline-flex';
                button.style.alignItems = 'center';
                button.style.justifyContent = 'center';
                button.style.cursor = 'pointer';
                button.style.transition = 'background 0.15s ease, color 0.15s ease';
                button.addEventListener('mouseenter', () => {
                    button.style.background = 'rgba(255, 255, 255, 0.24)';
                });
                button.addEventListener('mouseleave', () => {
                    button.style.background = 'rgba(255, 255, 255, 0.16)';
                });
                button.addEventListener('click', async (event) => {
                    event.preventDefault();
                    event.stopPropagation();
                    const codeElement = pre.querySelector('code');
                    const text = codeElement ? codeElement.textContent : pre.textContent;
                    if (!text) {
                        return;
                    }

                    const success = window.ClipboardUtils?.copyText
                        ? await window.ClipboardUtils.copyText(text)
                        : await navigator.clipboard?.writeText(text).then(() => true).catch(() => false);

                    if (success && window.Toast && typeof window.Toast.show === 'function') {
                        window.Toast.show({
                            message: translations.copySuccessMessage || 'Code copied to clipboard.',
                            type: 'success',
                            position: 'top-middle',
                        });
                    }

                    const originalIconHTML = button.innerHTML;
                    button.textContent = success
                        ? translations.copyButtonCopied || 'Copied'
                        : translations.copyButtonFailed || 'Copy failed';
                    setTimeout(() => {
                        button.innerHTML = originalIconHTML;
                    }, 1200);
                });

                pre.appendChild(button);
                pre.dataset.copyButtonAttached = 'true';
            });
        },

        positionPopover(popover, anchorRect) {
            if (!popover || !anchorRect) {
                return;
            }

            const gap = 10;
            const pw = popover.offsetWidth || 280;
            const ph = popover.offsetHeight || 180;
            let left = anchorRect.left + anchorRect.width / 2 - pw / 2;
            left = Math.max(gap, Math.min(left, window.innerWidth - pw - gap));

            let top = anchorRect.bottom + gap;
            if (top + ph > window.innerHeight - gap) {
                top = anchorRect.top - gap - ph;
            }
            top = Math.max(gap, top);

            popover.style.left = `${left + window.scrollX}px`;
            popover.style.top = `${top + window.scrollY}px`;
        },

        async saveAnnotation(color, body) {
            if (!this.annotationSelection || !this.annotationsCreateUrl || !this.selectedArticleId) {
                return;
            }

            const url = this.annotationsCreateUrl;
            const payload = {
                article_id: this.selectedArticleId,
                kind: 'highlight',
                highlight_text: this.annotationSelection.text,
                highlight_start: this.annotationSelection.start,
                highlight_end: this.annotationSelection.end,
                color,
                body,
            };

            try {
                const response = await fetch(url, {
                    method: 'POST',
                    credentials: 'same-origin',
                    headers: {
                        Accept: 'application/json',
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(payload),
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                const json = await response.json();
                let created = json?.data;
                if (Array.isArray(created)) {
                    created = created[0] || null;
                }
                if (!created || typeof created !== 'object') {
                    throw new Error('Invalid annotation response');
                }

                this.annotations.push(created);
                this.annotationsVisible = true;
                this.clearAnnotationPreview();
                this.annotationSelection = null;
                this.closeAnnotationPopover();
                this.renderArticleContent(this.currentContent);
                await this.fetchArticleAnnotationCount(this.selectedArticleId, true);
                if (this.annotationsVisible) {
                    await this.fetchArticleAnnotations(this.selectedArticleId);
                }
            } catch (error) {
                console.error('ArticlePane: failed to save annotation', error);
            }
        },

        getTextOffset(node, nodeOffset) {
            if (!node) {
                return null;
            }

            if (node.nodeType === Node.TEXT_NODE) {
                for (const entry of this.articleTextNodes) {
                    if (entry.node === node) {
                        return Math.min(entry.end, entry.start + nodeOffset);
                    }
                }
                return null;
            }

            if (node.nodeType === Node.ELEMENT_NODE) {
                const child = node.childNodes[nodeOffset] || node.childNodes[node.childNodes.length - 1];
                if (!child) {
                    return null;
                }

                if (nodeOffset >= node.childNodes.length) {
                    let last = child;
                    while (last && last.nodeType !== Node.TEXT_NODE) {
                        last = last.lastChild;
                    }
                    return last ? this.getTextOffset(last, last.nodeValue?.length || 0) : null;
                }

                let first = child;
                while (first && first.nodeType !== Node.TEXT_NODE) {
                    first = first.firstChild;
                }
                return first ? this.getTextOffset(first, 0) : null;
            }

            return null;
        },

        getTextNodeIndex(root) {
            this.articleTextNodes = [];
            this.articleText = '';
            this.articleTextLength = 0;

            if (!root) {
                return;
            }

            const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
                acceptNode(node) {
                    if (node.nodeValue === null || node.nodeValue.length === 0) {
                        return NodeFilter.FILTER_REJECT;
                    }
                    return NodeFilter.FILTER_ACCEPT;
                },
            });

            let currentNode;
            let offset = 0;
            while (walker.nextNode()) {
                currentNode = walker.currentNode;
                const text = currentNode.nodeValue || '';
                this.articleTextNodes.push({ node: currentNode, start: offset, end: offset + text.length });
                offset += text.length;
            }

            this.articleTextLength = offset;
            this.articleText = root.textContent || '';
        },

        renderAnnotations() {
            if (!this.annotationsVisible || !this.annotations.length) {
                return;
            }

            const contentPane = document.getElementById('reader-content');
            if (!contentPane) {
                return;
            }

            this.clearAnnotationHighlights();

            const annotations = [...this.annotations]
                .filter((ann) => ann.kind === 'highlight' && typeof ann.highlight_start === 'number' && typeof ann.highlight_end === 'number')
                .sort((a, b) => b.highlight_start - a.highlight_start);

            annotations.forEach((ann) => {
                try {
                    this.getTextNodeIndex(contentPane);
                    const wrapper = this.wrapAnnotationRange(ann);
                    if (Array.isArray(wrapper)) {
                        wrapper.forEach((segment) => {
                            segment.addEventListener('click', (event) => {
                                event.stopPropagation();
                                this.openAnnotationDetailPopover(ann, event.currentTarget.getBoundingClientRect());
                            });
                        });
                    } else if (wrapper) {
                        wrapper.addEventListener('click', (event) => {
                            event.stopPropagation();
                            this.openAnnotationDetailPopover(ann, event.currentTarget.getBoundingClientRect());
                        });
                    }
                } catch (error) {
                    console.error('ArticlePane: failed to render annotation', error, ann);
                }
            });
        },

        clearAnnotationHighlights() {
            const contentPane = document.getElementById('reader-content');
            if (!contentPane) {
                return;
            }

            const wrappers = Array.from(contentPane.querySelectorAll('.fb-reader-annotation-highlight'));
            wrappers.forEach((wrapper) => {
                const parent = wrapper.parentNode;
                if (!parent) {
                    return;
                }
                while (wrapper.firstChild) {
                    parent.insertBefore(wrapper.firstChild, wrapper);
                }
                parent.removeChild(wrapper);
            });
        },

        wrapAnnotationRange(annotation) {
            const contentPane = document.getElementById('reader-content');
            if (!contentPane) {
                return null;
            }

            let start = annotation.highlight_start;
            let end = annotation.highlight_end;
            if (typeof start !== 'number' || typeof end !== 'number' || start >= end) {
                return null;
            }

            let startInfo = this.findTextNodeAtOffset(start);
            let endInfo = this.findTextNodeAtOffset(end);

            if (!startInfo || !endInfo) {
                const text = this.articleText || '';
                const needle = annotation.highlight_text;
                if (typeof needle === 'string' && needle.length > 0) {
                    const foundIndex = text.indexOf(needle);
                    if (foundIndex !== -1) {
                        start = foundIndex;
                        end = foundIndex + needle.length;
                        startInfo = this.findTextNodeAtOffset(start);
                        endInfo = this.findTextNodeAtOffset(end);
                    }
                }
            }

            const normalizeHighlightText = (value) =>
                typeof value === 'string' ? value.replace(/\s+/g, ' ').trim() : '';

            if (startInfo && endInfo && typeof annotation.highlight_text === 'string' && annotation.highlight_text.length > 0) {
                const actual = (this.articleText || '').slice(start, end);
                if (normalizeHighlightText(actual) !== normalizeHighlightText(annotation.highlight_text)) {
                    startInfo = null;
                    endInfo = null;
                }
            }

            if (!startInfo || !endInfo) {
                if (annotation.highlight_text) {
                    const fallback = this.findTextRangeByText(contentPane, annotation.highlight_text);
                    if (fallback) {
                        startInfo = fallback.startInfo;
                        endInfo = fallback.endInfo;
                        start = this.getTextOffset(startInfo.node, startInfo.offset);
                        end = this.getTextOffset(endInfo.node, endInfo.offset);
                    }
                }
            }

            if (!startInfo || !endInfo) {
                return null;
            }

            const createHighlightWrapper = () => {
                const element = document.createElement('span');
                element.className = 'fb-reader-annotation-highlight';
                element.dataset.annotationId = annotation.id;
                element.dataset.annotationColor = annotation.color || 'yellow';
                element.title = annotation.body ? annotation.body : annotation.highlight_text || '';

                const colorMap = {
                    yellow: 'rgba(250, 204, 21, 0.3)',
                    green: 'rgba(74, 222, 128, 0.25)',
                    blue: 'rgba(96, 165, 250, 0.25)',
                    red: 'rgba(248, 113, 113, 0.25)',
                };
                const shadowMap = {
                    yellow: '#ca8a04',
                    green: '#16a34a',
                    blue: '#3b82f6',
                    red: '#ef4444',
                };
                const highlightColor = annotation.color || 'yellow';
                element.style.display = 'inline';
                element.style.background = colorMap[highlightColor] || colorMap.yellow;
                element.style.boxShadow = `inset 0 -2px 0 ${shadowMap[highlightColor] || shadowMap.yellow}`;
                element.style.borderRadius = '0.1rem';
                element.style.boxDecorationBreak = 'slice';
                element.style.WebkitBoxDecorationBreak = 'slice';
                return element;
            };

            const wrappers = [];
            const startNode = startInfo.node;
            const endNode = endInfo.node;

            if (startNode === endNode) {
                const node = startNode;
                const textLength = node.nodeValue?.length || 0;
                if (endInfo.offset < textLength) {
                    node.splitText(endInfo.offset);
                }
                const selected = startInfo.offset > 0 ? node.splitText(startInfo.offset) : node;
                const wrapper = createHighlightWrapper();
                selected.parentNode.insertBefore(wrapper, selected);
                wrapper.appendChild(selected);
                wrappers.push(wrapper);
                return wrappers;
            }

            let adjustedStart = startNode;
            if (startInfo.offset > 0 && startNode.nodeValue) {
                adjustedStart = startNode.splitText(startInfo.offset);
            }

            let adjustedEnd = endNode;
            const endNodeLength = endNode.nodeValue?.length || 0;
            const endNodeWasSplit = endInfo.offset > 0 && endInfo.offset < endNodeLength;
            if (endNodeWasSplit) {
                adjustedEnd = endNode.splitText(endInfo.offset);
            }

            const range = document.createRange();
            range.setStart(adjustedStart, 0);
            if (endNodeWasSplit) {
                range.setEnd(adjustedEnd, 0);
            } else {
                range.setEnd(endNode, endInfo.offset);
            }

            const wrapper = createHighlightWrapper();
            try {
                range.surroundContents(wrapper);
                wrappers.push(wrapper);
                return wrappers;
            } catch (error) {
                // Fall back to node-by-node wrapping when range wrapping is not possible.
            }

            const nodesToWrap = [];
            const walker = document.createTreeWalker(contentPane, NodeFilter.SHOW_TEXT, null);
            let isInRange = false;
            while (walker.nextNode()) {
                const node = walker.currentNode;
                if (node === adjustedStart) {
                    isInRange = true;
                }
                if (isInRange) {
                    const shouldExcludeEndNode = node === adjustedEnd && (endNodeWasSplit || endInfo.offset === 0);
                    if (shouldExcludeEndNode) {
                        break;
                    }
                    nodesToWrap.push(node);
                }
                if (node === adjustedEnd && !endNodeWasSplit && endInfo.offset > 0) {
                    break;
                }
            }

            if (!nodesToWrap.length) {
                return null;
            }

            nodesToWrap.forEach((node) => {
                const fallbackWrapper = createHighlightWrapper();
                node.parentNode.insertBefore(fallbackWrapper, node);
                fallbackWrapper.appendChild(node);
                wrappers.push(fallbackWrapper);
            });

            return wrappers;
        },

        findTextNodeAtOffset(offset) {
            for (let i = 0; i < this.articleTextNodes.length; i += 1) {
                const entry = this.articleTextNodes[i];
                if (offset >= entry.start && offset < entry.end) {
                    return {
                        node: entry.node,
                        offset: Math.min(entry.end - entry.start, offset - entry.start),
                    };
                }

                if (offset === entry.end) {
                    const nextEntry = this.articleTextNodes[i + 1];
                    if (nextEntry) {
                        return { node: nextEntry.node, offset: 0 };
                    }
                    return { node: entry.node, offset: entry.end - entry.start };
                }
            }
            return null;
        },

        findTextRangeByText(root, highlightText) {
            if (!root || typeof highlightText !== 'string' || !highlightText.trim()) {
                return null;
            }

            const needle = highlightText.replace(/\s+/g, ' ').trim();
            if (!needle) {
                return null;
            }

            const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
                acceptNode(node) {
                    if (!node.nodeValue || node.nodeValue.trim().length === 0) {
                        return NodeFilter.FILTER_REJECT;
                    }
                    return NodeFilter.FILTER_ACCEPT;
                },
            });

            const mapping = [];
            let normalized = '';
            let currentNode;
            let prevWasSpace = false;
            while (walker.nextNode()) {
                currentNode = walker.currentNode;
                const text = currentNode.nodeValue || '';
                for (let i = 0; i < text.length; i += 1) {
                    const ch = text[i];
                    const isSpace = /\s/.test(ch);
                    if (isSpace) {
                        if (prevWasSpace) {
                            continue;
                        }
                        normalized += ' ';
                        mapping.push({ node: currentNode, offset: i });
                        prevWasSpace = true;
                        continue;
                    }
                    normalized += ch;
                    mapping.push({ node: currentNode, offset: i });
                    prevWasSpace = false;
                }
            }

            const startIndex = normalized.indexOf(needle);
            if (startIndex === -1) {
                return null;
            }

            const endIndex = startIndex + needle.length - 1;
            const startMap = mapping[startIndex];
            const endMap = mapping[endIndex];
            if (!startMap || !endMap) {
                return null;
            }

            return {
                startInfo: { node: startMap.node, offset: startMap.offset },
                endInfo: { node: endMap.node, offset: endMap.offset + 1 },
            };
        },

        openAnnotationDetailPopover(annotation, rect) {
            const translations = window.ArticlePaneTranslations || {};
            this.closeAnnotationPopover();
            this.annotationPopover = null;

            const popover = document.createElement('div');
            popover.className = 'fb-popover fb-reader-annotation-popover fb-bg-surface fb-border fb-border-surface2 fb-rounded-lg';
            popover.setAttribute('role', 'dialog');
            popover.style.position = 'absolute';
            popover.style.zIndex = '9999';
            popover.style.width = '280px';
            popover.style.padding = '0.5rem';
            popover.style.color = 'var(--text)';

            const body = document.createElement('div');
            body.className = 'fb-popover-body';

            const truncateText = (value, maxLength = 140) => {
                if (typeof value !== 'string') {
                    return '';
                }
                const normalized = value.replace(/\s+/g, ' ').trim();
                if (normalized.length <= maxLength) {
                    return normalized;
                }
                return `${normalized.slice(0, maxLength).trim()}…`;
            };

            const header = document.createElement('div');
            header.className = 'fb-flex fb-items-center fb-gap-2 fb-mb-2';

            const dot = document.createElement('span');
            dot.style.width = '0.65rem';
            dot.style.height = '0.65rem';
            dot.style.borderRadius = '50%';
            dot.style.background = {
                yellow: '#ca8a04',
                green: '#16a34a',
                blue: '#3b82f6',
                red: '#ef4444',
            }[annotation.color] || '#ca8a04';
            header.appendChild(dot);

            body.appendChild(header);

            const snippet = document.createElement('div');
            snippet.className = 'fb-text-sm fb-text-muted fb-my-2';
            snippet.textContent = truncateText(annotation.highlight_text || translations.selectedText || 'Selected text', 100);
            snippet.title = annotation.highlight_text || translations.selectedText || 'Selected text';
            body.appendChild(snippet);

            const noteContainer = document.createElement('div');
            noteContainer.style.marginTop = '14px';
            noteContainer.style.whiteSpace = 'normal';
            noteContainer.style.lineHeight = '1.5';
            noteContainer.style.maxHeight = '150px';  
            noteContainer.style.overflowY = 'auto';

            const note = document.createElement('p');
            note.className = 'fb-text-sm';
            note.style.margin = '0';
            note.style.whiteSpace = 'pre-wrap';
            note.style.lineHeight = '1.5';
            note.style.color = annotation.body ? 'var(--text)' : 'var(--muted)';
            note.textContent = annotation.body || translations.noNote || 'No note';
            noteContainer.appendChild(note);
            body.appendChild(noteContainer);

            let textarea = null;
            let isEditing = false;

            const updateNoteDisplay = (text) => {
                note.textContent = text || translations.noNote || 'No note';
                note.style.color = text ? 'var(--text)' : 'var(--muted)';
            };

            const exitEditMode = () => {
                if (!isEditing || !textarea) {
                    return;
                }

                noteContainer.replaceChild(note, textarea);
                textarea = null;
                editSaveButton.title = translations.editButton || 'Edit';
                editSaveButton.innerHTML = '<i class="f7-icons">pencil</i>';
                cancelEditButton.style.display = 'none';
                isEditing = false;
            };

            const enterEditMode = () => {
                if (isEditing) {
                    return;
                }

                textarea = document.createElement('textarea');
                textarea.className = 'fb-input fb-text-sm';
                textarea.style.width = '100%';
                textarea.style.minHeight = '90px';
                textarea.style.marginTop = '0';
                textarea.style.color = 'var(--text)';
                textarea.placeholder = translations.notePlaceholder || 'Add a note (optional)';
                textarea.value = annotation.body || '';
                noteContainer.replaceChild(textarea, note);

                editSaveButton.title = translations.saveButton || translations.highlightButton || 'Save';
                editSaveButton.innerHTML = '<i class="f7-icons">checkmark</i>';
                cancelEditButton.style.display = 'inline-flex';
                isEditing = true;
                textarea.focus();
            };

            const saveEdit = async () => {
                if (!textarea) {
                    return;
                }

                const value = textarea.value.trim();
                const bodyValue = value.length ? value : null;
                const updated = await this.updateAnnotation(annotation.id, { body: bodyValue });
                if (!updated) {
                    return;
                }

                annotation.body = updated.body ?? null;
                const existing = this.annotations.find((ann) => ann.id === annotation.id);
                if (existing) {
                    existing.body = updated.body ?? null;
                }
                updateNoteDisplay(annotation.body);
                exitEditMode();
            };

            const actions = document.createElement('div');
            actions.className = 'fb-flex fb-justify-end fb-gap-2 fb-mt-3';

            const editSaveButton = document.createElement('button');
            editSaveButton.type = 'button';
            editSaveButton.className = 'fb-btn fb-btn-ghost fb-text-sm';
            editSaveButton.title = translations.editButton || 'Edit';
            editSaveButton.innerHTML = '<i class="f7-icons">pencil</i>';
            editSaveButton.addEventListener('click', async () => {
                if (!isEditing) {
                    enterEditMode();
                    return;
                }
                await saveEdit();
            });
            actions.appendChild(editSaveButton);

            const deleteButton = document.createElement('button');
            deleteButton.type = 'button';
            deleteButton.className = 'fb-btn fb-btn-ghost fb-text-sm fb-text-red';
            deleteButton.style.color = 'var(--red)';
            deleteButton.title = translations.deleteButton || 'Delete';
            deleteButton.innerHTML = '<i class="f7-icons">trash</i>';
            deleteButton.addEventListener('click', async () => {
                await this.deleteAnnotation(annotation.id);
                this.closeAnnotationPopover();
            });
            actions.appendChild(deleteButton);

            const cancelEditButton = document.createElement('button');
            cancelEditButton.type = 'button';
            cancelEditButton.className = 'fb-btn fb-btn-ghost fb-text-sm';
            cancelEditButton.style.display = 'none';
            cancelEditButton.title = translations.cancelButton || 'Cancel';
            cancelEditButton.textContent = translations.cancelButton || 'Cancel';
            cancelEditButton.addEventListener('click', () => exitEditMode());
            actions.appendChild(cancelEditButton);

            const closeButton = document.createElement('button');
            closeButton.type = 'button';
            closeButton.className = 'fb-btn fb-btn-ghost fb-text-sm';
            closeButton.title = translations.closeButton || 'Close';
            closeButton.innerHTML = '<i class="f7-icons">xmark</i>';
            closeButton.addEventListener('click', () => this.closeAnnotationPopover());
            actions.appendChild(closeButton);

            body.appendChild(actions);
            popover.appendChild(body);
            document.body.appendChild(popover);
            this.positionPopover(popover, rect);

            const dismissHandler = (event) => {
                if (!popover.contains(event.target)) {
                    this.closeAnnotationPopover();
                }
            };
            const escapeHandler = (event) => {
                if (event.key === 'Escape') {
                    this.closeAnnotationPopover();
                }
            };
            document.addEventListener('mousedown', dismissHandler);
            document.addEventListener('touchstart', dismissHandler, { passive: true });
            document.addEventListener('keydown', escapeHandler);
            this.annotationPopover = { el: popover, dismissHandler, escapeHandler };
        },

        async deleteAnnotation(annotationId) {
            if (!annotationId || !this.annotationDeleteUrl) {
                return;
            }

            const url = window.CommonUtils?.interpolate(
                this.annotationDeleteUrl,
                { annotation_id: encodeURIComponent(annotationId) }
            );
            if (!url) {
                return;
            }

            try {
                const response = await fetch(url, {
                    method: 'DELETE',
                    credentials: 'same-origin',
                    headers: { Accept: 'application/json' },
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                this.annotations = this.annotations.filter((ann) => ann.id !== annotationId);
                this.renderArticleContent(this.currentContent);
                await this.fetchArticleAnnotationCount(this.selectedArticleId, true);
                if (this.annotationsVisible) {
                    await this.fetchArticleAnnotations(this.selectedArticleId);
                }
            } catch (error) {
                console.error('ArticlePane: failed to delete annotation', error);
            }
        },

        async updateAnnotation(annotationId, data) {
            if (!annotationId || !this.annotationUpdateUrl) {
                return null;
            }

            const url = window.CommonUtils?.interpolate(
                this.annotationUpdateUrl,
                { annotation_id: encodeURIComponent(annotationId) }
            );
            if (!url) {
                return null;
            }

            try {
                const response = await fetch(url, {
                    method: 'PATCH',
                    credentials: 'same-origin',
                    headers: {
                        Accept: 'application/json',
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data),
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                const json = await response.json();
                const updated = json?.data;
                if (!updated || typeof updated !== 'object') {
                    throw new Error('Invalid annotation update response');
                }

                this.annotations = this.annotations.map((ann) =>
                    ann.id === annotationId ? { ...ann, ...updated } : ann
                );
                this.renderArticleContent(this.currentContent);
                if (this.annotationsVisible) {
                    this.renderAnnotations();
                }
                return updated;
            } catch (error) {
                console.error('ArticlePane: failed to update annotation', error);
                return null;
            }
        },

        normalizeRelativeLinks(content, articleUrl) {
            if (!content || !articleUrl || typeof DOMParser === 'undefined') {
                return content;
            }

            let baseUrl;
            try {
                baseUrl = new URL(articleUrl).origin;
            } catch {
                return content;
            }

            const parser = new DOMParser();
            const doc = parser.parseFromString(content, 'text/html');
            doc.querySelectorAll('[href], [src]').forEach((el) => {
                ['href', 'src'].forEach((attr) => {
                    const value = el.getAttribute(attr);
                    if (!value) {
                        return;
                    }

                    if (/^[a-zA-Z][a-zA-Z\d+\-.]*:/.test(value) || value.startsWith('//') || value.startsWith('#')) {
                        return;
                    }

                    try {
                        el.setAttribute(attr, new URL(value, baseUrl).toString());
                    } catch (_) {
                        console.warning('components/article-pane.js: Failed to resolve URL:', value, 'with base', baseUrl);
                    }
                });
            });

            return doc.body.innerHTML;
        },

        updateSelectedArticleCard() {
            document.querySelectorAll('.fb-article-card.fb-article-card-selected').forEach((el) => {
                el.classList.remove('fb-article-card-selected');
            });

            if (!this.selectedArticleId) {
                return;
            }

            const selected = document.querySelector(`.fb-article-card[data-article-id="${this.selectedArticleId}"]`);
            if (selected) {
                selected.classList.add('fb-article-card-selected');
            }
        },

        renderArticleContent(content) {
            this.closeAnnotationPopover();

            const emptyPane = document.getElementById('reader-empty');
            const contentPane = document.getElementById('reader-content');

            if (emptyPane) {
                emptyPane.style.display = content ? 'none' : '';
            }

            if (!contentPane) {
                return;
            }

            if (!content) {
                this.updateOpenOriginalLink('');
                contentPane.innerHTML = '<div class="fb-reader-empty-text">No article content available.</div>';
                contentPane.hidden = false;
                return;
            }

            contentPane.innerHTML = content;
            this.normalizeNestedPreElements(contentPane);
            this.getTextNodeIndex(contentPane);
            contentPane.querySelectorAll('img').forEach((img) => {
                const wrapper = document.createElement('div');
                wrapper.className = 'fb-reader-image-wrap';
                img.parentNode.insertBefore(wrapper, img);
                wrapper.appendChild(img);

                img.classList.remove('image-loaded');
                wrapper.classList.remove('image-broken');
                img.style.display = 'block';

                const markLoaded = () => {
                    wrapper.classList.remove('image-broken');
                    img.classList.add('image-loaded');
                    img.style.display = '';
                };

                const markBroken = () => {
                    wrapper.classList.add('image-broken');
                    img.style.display = 'none';
                };

                if (img.complete) {
                    if (img.naturalWidth > 0 || img.naturalHeight > 0) {
                        markLoaded();
                    } else {
                        markBroken();
                    }
                } else {
                    img.addEventListener('load', markLoaded, { once: true });
                    img.addEventListener('error', markBroken, { once: true });
                }
            });

            this.getTextNodeIndex(contentPane);
            if (this.readerMouseUpHandler) {
                contentPane.removeEventListener('mouseup', this.readerMouseUpHandler);
            }
            this.readerMouseUpHandler = () => {
                if (this.annotationActive) {
                    requestAnimationFrame(() => this.handleReaderSelection());
                }
            };
            contentPane.addEventListener('mouseup', this.readerMouseUpHandler);

            this.attachCodeCopyButtons(contentPane);
            if (this.annotationsVisible) {
                this.renderAnnotations();
            }

            contentPane.hidden = false;
        },

        async markArticleRead(articleId, card) {
            const statusIsRead = card.dataset.statusIsRead === 'true';
            if (statusIsRead) {
                return;
            }

            const statusUrl = card.querySelector('[data-article-status-update-url]')?.dataset.articleStatusUpdateUrl;
            if (!statusUrl) {
                return;
            }

            const url = this.resolveArticleStatusUrl(statusUrl, articleId);
            if (!url) {
                return;
            }

            try {
                const response = await fetch(url, {
                    method: 'PATCH',
                    credentials: 'same-origin',
                    headers: {
                        Accept: 'application/json',
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ is_read: true }),
                });

                if (!response.ok) {
                    throw new Error(`Failed to mark article read (${response.status})`);
                }

                this.cacheReadArticle(articleId, card);
                card.dataset.statusIsRead = 'true';
            } catch (error) {
                console.error('ArticlePane: failed to mark article read', error);
            } finally {
                this.refreshArticleStats();
            }
        },

        cacheReadArticle(articleId, card) {
            if (!articleId || !window.CommonUtils || typeof window.CommonUtils.updateLocalStorage !== 'function') {
                return;
            }

            const key = 'feedbase_user_cached_articles';
            const title = card.querySelector('.fb-article-title')?.textContent?.trim() || '';
            const feedTitle = card.querySelector('.fb-article-card-feed-title')?.textContent?.trim() || '';
            const summary = card.querySelector('.fb-article-summary')?.textContent?.trim() || '';
            const url = card.dataset.url || '';
            const content = card.dataset.content || '';
            const entry = {
                id: articleId,
                title,
                feed_title: feedTitle,
                summary,
                url,
                content,
                read_at: new Date().toISOString(),
            };

            window.CommonUtils.updateLocalStorage(key, (currentValue) => {
                const articles = Array.isArray(currentValue) ? currentValue : [];
                const updatedArticles = articles.filter((item) => item && item.id !== articleId);
                updatedArticles.unshift(entry);
                return updatedArticles.slice(0, 3);
            }, []);
        },

        resolveArticleStatusUrl(url, articleId) {
            if (!url || !articleId) {
                return null;
            }

            if (window.CommonUtils && typeof window.CommonUtils.interpolate === 'function') {
                return window.CommonUtils.interpolate(url, { article_id: encodeURIComponent(articleId) });
            }

            return url.replace('{article_id}', encodeURIComponent(articleId));
        },

        persistSelectedArticle() {
            if (!this.selectedArticleId || !window.localStorage) {
                return;
            }

            try {
                window.localStorage.setItem(
                    'feedbase_selected_article',
                    JSON.stringify({
                        id: this.selectedArticleId,
                        url: this.originalUrl,
                        content: this.currentContent,
                    }),
                );
            } catch (error) {
                console.warn('ArticlePane: could not persist selected article', error);
            }
        },

        loadSelectedArticleFromStorage() {
            if (!window.localStorage) {
                return null;
            }

            try {
                const raw = window.localStorage.getItem('feedbase_selected_article');
                if (!raw) {
                    return null;
                }

                const data = JSON.parse(raw);
                if (!data || typeof data !== 'object' || !data.id) {
                    return null;
                }

                return {
                    id: String(data.id),
                    url: typeof data.url === 'string' ? data.url : '',
                    content: typeof data.content === 'string' ? data.content : '',
                };
            } catch (error) {
                return null;
            }
        },

        refreshArticleStats() {
            window.dispatchEvent(new CustomEvent('article-stats-refresh'));
        },

        restoreSelectedArticle() {
            if (!this.selectedArticleId) {
                return;
            }

            const selected = document.querySelector(`.fb-article-card[data-article-id="${this.selectedArticleId}"]`);
            if (selected && !this.currentContent) {
                const content = selected.dataset.content || '';
                const articleUrl = selected.dataset.url || '';
                this.originalUrl = articleUrl;
                this.currentContent = this.normalizeRelativeLinks(content, articleUrl);
                this.updateOpenOriginalLink(this.originalUrl);
            }

            this.updateSelectedArticleCard();
            this.updateAnnotationToggleVisibility();
            if (this.currentContent) {
                this.renderArticleContent(this.currentContent);
                if (this.annotationCountFetchedFor !== this.selectedArticleId) {
                    this.fetchArticleAnnotationCount(this.selectedArticleId);
                }
                if (this.annotationsVisible) {
                    this.fetchArticleAnnotations(this.selectedArticleId);
                }
            }
        },
    };
}
