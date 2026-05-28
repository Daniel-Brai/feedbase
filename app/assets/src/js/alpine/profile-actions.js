export function ProfileActions(settingsUrl, logoutFormUrl, settingsLabel, signOutLabel, hideSettingsOption = false) {
    return {
        settingsUrl,
        logoutFormUrl,
        settingsLabel,
        signOutLabel,
        hideSettingsOption,

        showActions(trigger) {
            const options = [];
            if (!this.hideSettingsOption) {
                options.push({
                    label: this.settingsLabel || "Settings",
                    icon: "gear",
                    url: this.settingsUrl,
                    attributes: {
                        "hx-get": this.settingsUrl,
                        "preload": "mouseover",
                        "hx-target": "body",
                        "hx-boost": "true",
                        "hx-push-url": "true",
                    },
                });
            }
            options.push({
                label: this.signOutLabel || "Sign Out",
                icon: "arrow_right_square",
                content_url: this.logoutFormUrl,
            });

            window.Popover.show(trigger, {
                options,
                placement: "bottom-end",
            });
        },
    };
}
