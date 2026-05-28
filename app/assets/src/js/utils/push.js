export const PushUtils = (function () {
    "use strict";

    const VAPID_PUBLIC_KEY = document.querySelector('meta[name="vapid-public-key"]').content;
    const NOTIFICATIONS_CONFIG = window.__NOTIFICATIONS_CONFIG__;

    function urlBase64ToUint8Array(base64String) {
        const normalized = base64String
            .replace(/\s+/g, "")
            .replace(/-/g, "+")
            .replace(/_/g, "/");

        const padding = "=".repeat((4 - (normalized.length % 4)) % 4);
        const base64 = normalized + padding;
        const rawData = atob(base64);
        return Uint8Array.from([...rawData].map((c) => c.charCodeAt(0)));
    }

    async function subscribeToPush() {
        const registration = await navigator.serviceWorker.ready;

        const existing = await registration.pushManager.getSubscription();
        if (existing) {
            return existing;
        }

        const subscription = await registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY),
        });

        try {
            const response = await fetch(NOTIFICATIONS_CONFIG.webPushUrl, {
                method: "POST",
                credentials: "same-origin",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(subscription.toJSON()),
            });

            if (!response.ok) {
                await subscription.unsubscribe();
                throw new Error(`Failed to register push subscription: ${response.status}`);
            }
        } catch (error) {
            console.error("utils/push.js: Error during push subscription:", error);
            await subscription.unsubscribe();
            throw error;
        }

        return subscription;
    }

    async function unsubscribeFromPush() {
        const registration = await navigator.serviceWorker.ready;
        const subscription = await registration.pushManager.getSubscription();

        if (!subscription) return;

        try {
            const response = await fetch(NOTIFICATIONS_CONFIG.webPushUrl, {
                method: "PATCH",
                credentials: "same-origin",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ endpoint: subscription.endpoint }),
            });

            if (!response.ok) {
                throw new Error(`Failed to unregister push subscription: ${response.status}`);
            }

            await subscription.unsubscribe();
        } catch (error) {
            console.error("utils/push.js: Error during push unsubscription:", error);
            throw error;
        }
    }

    async function registerServiceWorker() {
        if (typeof navigator === 'undefined' || !('serviceWorker' in navigator)) {
            return null;
        }

        try {
            const sw_url = new URL('/sw.js', window.location.origin).href;

            const registration = await navigator.serviceWorker.register(sw_url);

            await registration.update();

            registration.addEventListener('updatefound', () => {
                const newWorker = registration.installing;
                if (!newWorker) return;

                newWorker.addEventListener('statechange', () => {
                    if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                        newWorker.postMessage({ type: 'SKIP_WAITING' });
                    }
                });
            });

            return registration;
        } catch (error) {
            console.error('utils/push.js: Failed to register service worker', error);
            return null;
        }
    }

    async function initPush() {
        if (typeof navigator === 'undefined' || !('serviceWorker' in navigator) || !('PushManager' in window) || !('Notification' in window)) {
            return null;
        }

        const permission = Notification.permission === 'granted'
            ? 'granted'
            : await Notification.requestPermission();

        if (permission !== 'granted') {
            return null;
        }

        try {
            return await subscribeToPush();
        } catch (error) {
            console.error('utils/push.js: Failed to initialize push subscription', error);
            return null;
        }
    }


    return {
        subscribeToPush,
        unsubscribeFromPush,
        registerServiceWorker,
        initPush,
    };
})();
