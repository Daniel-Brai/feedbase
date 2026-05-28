export function FolderActions(folderId, editFolderFormUrl, deleteFolderFormUrl, folderName, renameLabel, deleteLabel) {
    return {
        folderId,
        editFolderFormUrl,
        deleteFolderFormUrl,
        folderName,
        renameLabel,
        deleteLabel,

        showActions(trigger) {
            if (!this.folderId) {
                console.warn("FolderActions: missing folder ID");
                return;
            }

            const options = [
                {
                    label: this.renameLabel || "Rename",
                    icon: "pencil",
                    onClick: () => {
                        const url = this.buildUrl(this.editFolderFormUrl, true);
                        if (url) {
                            window.Modal.show({
                                heading_title: this.renameLabel || "Rename Folder",
                                heading_icon: "pencil",
                                content_url: url,
                            });
                        } else {
                            console.warn("FolderActions: editFolderFormUrl is not set");
                        }
                    }
                },
                {
                    label: this.deleteLabel || "Delete",
                    content_url: this.buildUrl(this.deleteFolderFormUrl),
                },
            ];

            window.Popover.show(trigger, {
                options,
                placement: "bottom-end",
            });
        },

        buildUrl(baseUrl, withFolderName = false) {
            if (!baseUrl) {
                return baseUrl;
            }

            let params = new URLSearchParams();

            if (!withFolderName) {
                params.set(
                    "_config_submit_url__format",
                    JSON.stringify({
                        folder_id: this.folderId,
                    }),
                );
            } else {
                params.set(
                    "name",
                    this.folderName,
                );
                params.set(
                    "_config_submit_url__format",
                    JSON.stringify({
                        folder_id: this.folderId,
                    }),
                );
            }

            return `${baseUrl}?${params.toString()}`;
        },
    };
}
