export function FeedActions(
    feedUrl,
    subscriptionId,
    subscriptionName,
    renameFormUrl,
    foldersUrl,
    subscriptionDeleteUrl,
    subscriptionUpdateUrl,
    unsubscribeSuccessMessage,
    unsubscribeErrorMessage,
    moveToFolderSuccessMessage = "Feed moved to folder successfully.",
    moveToFolderErrorMessage = "Unable to move feed to folder.",
    moveToFolderLabel = "Move to Folder",
    renameLabel = "Rename",
    copyFeedUrlLabel = "Copy feed URL",
    openFeedUrlLabel = "Open Feed URL",
    unsubscribeLabel = "Unsubscribe",
    renameFeedHeading = "Rename Feed",
    copyFeedUrlSuccessMessage = "Feed URL copied to clipboard",
    copyFeedUrlErrorMessage = "Unable to copy feed URL",
) {
    return {
        feedUrl,
        subscriptionId,
        subscriptionName,
        renameFormUrl,
        foldersUrl,
        subscriptionDeleteUrl,
        subscriptionUpdateUrl,
        unsubscribeSuccessMessage,
        unsubscribeErrorMessage,
        moveToFolderSuccessMessage,
        moveToFolderErrorMessage,
        moveToFolderLabel,
        renameLabel,
        copyFeedUrlLabel,
        openFeedUrlLabel,
        unsubscribeLabel,
        renameFeedHeading,
        copyFeedUrlSuccessMessage,
        copyFeedUrlErrorMessage,

        showActions(trigger) {
            if (!this.feedUrl) {
                console.warn("FeedActions: missing feed URL");
                return;
            }

            window.Popover.show(trigger, {
                options: [
                    {
                        label: this.moveToFolderLabel,
                        icon: "arrowshape_turn_up_right",
                        onClick: () => {
                            if (!this.foldersUrl) {
                                console.warn("FeedActions: missing folders URL");
                                return;
                            }

                            if (window.Popover && typeof window.Popover.hide === "function") {
                                window.Popover.hide();
                            }

                            if (!window.Sheet || typeof window.Sheet.show !== "function") {
                                console.warn("FeedActions: Sheet component is not available.");
                                return;
                            }

                            const currentFolderIdRaw = trigger.closest(".fb-sidebar-folder")?.dataset.folderId;
                            const currentFolderId = currentFolderIdRaw === undefined || currentFolderIdRaw === "" || currentFolderIdRaw === "null"
                                ? null
                                : currentFolderIdRaw;

                            window.Sheet.show({
                                content_url: this.foldersUrl,
                                content_format: "json",
                                heading_title: this.moveToFolderLabel,
                                heading_icon: "folder_badge_plus",
                                heading_alignment: "center",
                                content_success_template_html: `
                                    <div class="fb-sheet-list fb-sheet-list-separated">
                                        [[#each data]]
                                            <button
                                                type="button"
                                                class="fb-sheet-item fb-w-full fb-text-center fb-p-3"
                                                data-folder-id="[[id]]"
                                            >
                                                [[name]]
                                            </button>
                                        [[/each]]
                                    </div>
                                `,
                                content_error_template_html: `
                                    <div class="fb-p-3 fb-text-red">
                                        Unable to load folders. Please try again.
                                    </div>
                                `,
                                on_content_load: (container) => {
                                    container.querySelectorAll("[data-folder-id]").forEach((btn) => {
                                        const folderIdRaw = btn.dataset.folderId;
                                        const folderId = folderIdRaw === undefined || folderIdRaw === "" || folderIdRaw === "null"
                                            ? null
                                            : folderIdRaw;

                                        if (folderId === currentFolderId) {
                                            btn.remove();
                                            return;
                                        }

                                        btn.addEventListener("click", async () => {
                                            if (!this.subscriptionUpdateUrl) {
                                                console.warn("FeedActions: missing subscription update URL");
                                                return;
                                            }

                                            if (window.Sheet && typeof window.Sheet.hide === "function") {
                                                window.Sheet.hide();
                                            }

                                            const updateUrl = window.CommonUtils && typeof window.CommonUtils.interpolate === "function"
                                                ? window.CommonUtils.interpolate(this.subscriptionUpdateUrl, { subscription_id: encodeURIComponent(this.subscriptionId) })
                                                : this.subscriptionUpdateUrl.replace(
                                                    "{subscription_id}",
                                                    encodeURIComponent(this.subscriptionId),
                                                );

                                            try {
                                                const response = await fetch(updateUrl, {
                                                    method: "PATCH",
                                                    credentials: "same-origin",
                                                    headers: {
                                                        "Accept": "application/json",
                                                        "Content-Type": "application/json",
                                                    },
                                                    body: JSON.stringify({ folder_id: folderId }),
                                                });

                                                const payload = await response.json().catch(() => null);
                                                if (response.ok) {
                                                    window.Toast.show({
                                                        message: this.moveToFolderSuccessMessage,
                                                        type: "success",
                                                        position: "bottom-middle",
                                                    });

                                                    const subscriptionsEl = document.getElementById("subscriptions");
                                                    if (
                                                        subscriptionsEl &&
                                                        window.htmx &&
                                                        window.htmx.pagination &&
                                                        typeof window.htmx.pagination.getInstance === "function"
                                                    ) {
                                                        const ctrl = window.htmx.pagination.getInstance(subscriptionsEl);
                                                        if (ctrl && typeof ctrl.reload === "function") {
                                                            ctrl.reload();
                                                        }
                                                    }
                                                } else {
                                                    const message = payload?.message || this.moveToFolderErrorMessage;
                                                    window.Toast.show({
                                                        message,
                                                        type: "error",
                                                        position: "bottom-middle",
                                                    });
                                                }
                                            } catch (err) {
                                                window.Toast.show({
                                                    message: this.moveToFolderErrorMessage,
                                                    type: "error",
                                                    position: "bottom-middle",
                                                });
                                                console.error("FeedActions: move to folder failed", err);
                                            }
                                        });
                                    });
                                },
                            });
                        },
                    },
                    {
                        label: this.renameLabel,
                        icon: "pencil",
                        onClick: () => {
                            if (!this.renameFormUrl) {
                                console.warn("FeedActions: missing rename form URL");
                                return;
                            }
                            if (!this.subscriptionId) {
                                console.warn("FeedActions: missing subscription ID");
                                return;
                            }

                            const params = new URLSearchParams();
                            if (this.subscriptionName) {
                                params.set("title", this.subscriptionName);
                            }
                            params.set(
                                "_config_submit_url__format",
                                JSON.stringify({ subscription_id: this.subscriptionId }),
                            );

                            window.Modal.show({
                                heading_icon: "pencil",
                                heading_title: this.renameFeedHeading,
                                content_url: `${this.renameFormUrl}?${params.toString()}`,
                            });
                        },
                    },
                    {
                        label: this.copyFeedUrlLabel,
                        icon: "doc_on_doc",
                        onClick: async () => {
                            const copied = await window.ClipboardUtils.copyText(this.feedUrl);
                            if (copied) {
                                window.Toast.show({
                                    message: this.copyFeedUrlSuccessMessage,
                                    type: "success",
                                    position: "bottom-middle",
                                });
                            } else {
                                window.Toast.show({
                                    message: this.copyFeedUrlErrorMessage,
                                    type: "error",
                                    position: "top-middle",
                                });
                            }
                        },
                    },
                    {
                        label: this.openFeedUrlLabel,
                        icon: "external_link",
                        onClick: () => {
                            window.open(this.feedUrl, "_blank", "noopener,noreferrer");
                        },
                    },
                    {
                        label: this.unsubscribeLabel,
                        icon: "trash",
                        danger: true,
                        onClick: async () => {
                            if (!this.subscriptionDeleteUrl) {
                                console.warn("FeedActions: missing delete URL");
                                return;
                            }
                            if (!this.subscriptionId) {
                                console.warn("FeedActions: missing subscription ID");
                                return;
                            }

                            const deleteUrl = window.CommonUtils && typeof window.CommonUtils.interpolate === "function"
                                ? window.CommonUtils.interpolate(this.subscriptionDeleteUrl, { subscription_id: encodeURIComponent(this.subscriptionId) })
                                : this.subscriptionDeleteUrl.replace(
                                    "{subscription_id}",
                                    encodeURIComponent(this.subscriptionId),
                                );

                            try {
                                const response = await fetch(deleteUrl, {
                                    method: "DELETE",
                                    credentials: "same-origin",
                                    headers: {
                                        "Accept": "application/json",
                                    },
                                });

                                if (response.ok) {
                                    window.Toast.show({
                                        message: this.unsubscribeSuccessMessage || "Subscription removed successfully.",
                                        type: "success",
                                        position: "bottom-middle",
                                    });

                                    const subscriptionsEl = document.getElementById("subscriptions");
                                    if (
                                        subscriptionsEl &&
                                        window.htmx &&
                                        window.htmx.pagination &&
                                        typeof window.htmx.pagination.getInstance === "function"
                                    ) {
                                        const ctrl = window.htmx.pagination.getInstance(subscriptionsEl);
                                        if (ctrl && typeof ctrl.reload === "function") {
                                            ctrl.reload();
                                        }
                                    }
                                } else {
                                    let message = this.unsubscribeErrorMessage || "Unable to unsubscribe. Please try again.";
                                    window.Toast.show({
                                        message,
                                        type: "error",
                                        position: "top-middle",
                                    });
                                }
                            } catch (err) {
                                window.Toast.show({
                                    message: this.unsubscribeErrorMessage || "Unable to unsubscribe. Please try again.",
                                    type: "error",
                                    position: "top-middle",
                                });
                                console.error("FeedActions: unsubscribe failed", err);
                            }
                        },
                    },
                ],
                placement: "bottom-end",
            });
        },
    };
}
