import { Alert } from './components/alert.js';
import { Modal } from './components/modal.js';
import { Toast } from './components/toast.js';
import { Popover } from './components/popover.js';
import { Sheet } from './components/sheet.js';

import { ArticleStats } from './alpine/article-stats.js';
import { ArticleActions } from './alpine/article-actions.js';
import { FeedActions } from './alpine/feed-actions.js';
import { FolderActions } from './alpine/folder-actions.js';
import { ProfileActions } from './alpine/profile-actions.js';
import { ArticlePane } from './alpine/article-pane.js';
import { OfflineReader } from './alpine/offline-reader.js';
import { PullRefresh } from './alpine/pull-refresh.js';

import { ClipboardUtils } from './utils/clipboard.js';
import { CommonUtils } from './utils/common.js';
import { DateTimeUtils } from './utils/datetime.js';
import { HTMLUtils } from './utils/html.js';
import { KeybindingsUtils } from './utils/keybindings.js';
import { PaginationUtils } from './utils/pagination.js';
import { MobileUtils } from './utils/mobile.js';

// General JS components
window.Toast = Toast;
window.Modal = Modal;
window.Alert = Alert;
window.Popover = Popover;
window.Sheet = Sheet;

// Alpine based components 
window.ArticleStats = ArticleStats;
window.ArticleActions = ArticleActions;
window.FeedActions = FeedActions;
window.FolderActions = FolderActions;
window.ProfileActions = ProfileActions;
window.ArticlePane = ArticlePane;
window.OfflineReader = OfflineReader;
window.PullRefresh = PullRefresh;


// Utils
window.ClipboardUtils = ClipboardUtils;
window.CommonUtils = CommonUtils;
window.DateTimeUtils = DateTimeUtils;
window.MobileUtils = MobileUtils;
window.HTMLUtils = HTMLUtils;
window.KeybindingsUtils = KeybindingsUtils;
window.PaginationUtils = PaginationUtils;

// JS Effects
import './effects/form.js';
import './effects/keyboard.js';
import './effects/pwa.js';

