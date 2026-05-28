import { PushUtils } from "./utils/push.js";

document.addEventListener("DOMContentLoaded", async () => {
    await PushUtils.registerServiceWorker();

    const hiddenAllowPushInput = document.querySelector(
        'input[name="allow_push_notifications"]'
    );
    let allowPushToggle = null;

    if (hiddenAllowPushInput?.nextElementSibling?.matches("input[type='checkbox']")) {
        allowPushToggle = hiddenAllowPushInput.nextElementSibling;
    } else {
        allowPushToggle = document.querySelector(
            'input[name="allow_push_notifications"] + input[type="checkbox"]'
        );
    }

    if (allowPushToggle) {
        allowPushToggle.addEventListener("change", async () => {
            if (allowPushToggle.checked) {
                const permission = await Notification.requestPermission();
                if (permission !== "granted") {
                    console.warn("Push permission not granted:", permission);
                    return;
                }
                await PushUtils.initPush();
            } else {
                await PushUtils.unsubscribeFromPush();
            }
        });
    }
});