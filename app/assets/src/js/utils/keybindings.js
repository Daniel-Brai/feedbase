export const KeybindingsUtils = (function () {
    "use strict";

    function renderKeybindingsHtml(keybindings) {
        const data = Array.isArray(keybindings) && keybindings.length ? keybindings : defaultKeybindings();

        let html =
            '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0 32px; padding: 0 4px; padding-bottom: 8px;">';

        for (const col of data) {
            html += `<div>`;
            for (const cat of col.categories) {
                html += `<div class="fb-kb-group-title">${cat.title}</div>`;
                for (const item of cat.items) {
                    html += `
                        <div class="fb-kb-row">
                            <div class="fb-kb-keys">
                                ${item.keys.map((k) => `<kbd>${k}</kbd>`).join('')}
                            </div>
                            <div class="fb-kb-desc">${item.label}</div>
                        </div>
                    `;
                }
            }
            html += `</div>`;
        }

        html += '</div>';
        return html;
    }

    function defaultKeybindings() {
        return [
            {
                categories: [
                    {
                        title: 'Navigation',
                        items: [
                            { keys: ['j', 'k'], label: 'Next / prev article' },
                            { keys: ['J', 'K'], label: 'Next / prev feed' },
                            { keys: ['g', 'g'], label: 'Scroll to top' },
                            { keys: ['G'], label: 'Scroll to bottom' },
                            { keys: ['h'], label: 'Home' },
                            { keys: ['e'], label: 'Settings' },
                        ],
                    },
                    {
                        title: 'Go-To',
                        items: [
                            { keys: ['g', 'a'], label: 'All articles' },
                            { keys: ['g', 's'], label: 'Starred' },
                            { keys: ['g', 'b'], label: 'Bookmarks' },
                            { keys: ['g', 'u'], label: 'Unread' },
                            { keys: ['g', 't'], label: 'Today' },
                        ],
                    },
                ],
            },
            {
                categories: [
                    {
                        title: 'Actions',
                        items: [
                            { keys: ['r'], label: 'Toggle read' },
                            { keys: ['s'], label: 'Toggle star' },
                            { keys: ['b'], label: 'Bookmark' },
                            { keys: ['o'], label: 'Open Original URL' },
                            { keys: ['y', 'y'], label: 'Copy Original URL' },
                            { keys: ['d', 'd'], label: 'Unsubscribe feed' },
                        ],
                    },
                    {
                        title: 'UI',
                        items: [
                            { keys: ['u'], label: 'Add feed' },
                            { keys: ['/'], label: 'Search' },
                            { keys: ['n', 'N'], label: 'Next / prev result' },
                            { keys: ['?'], label: 'This overlay' },
                            { keys: ['Esc'], label: 'Close / back' },
                        ],
                    },
                ],
            },
        ];
    }

    return {
        renderKeybindingsHtml
    };
})();
