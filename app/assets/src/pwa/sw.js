const SHELL_CACHE = "feedbase-shell-v1";
const CONTENT_CACHE = "feedbase-content-v1";

const SHELL_ASSETS = [
    "/offline",
    "/static/css/app.css",
    "/static/js/app.js",
    "/static/js/pwa.js",
    "/static/vendor/alpinejs/alpinejs.3.15.9.js",
    "/static/vendor/framework7-icons/framework7-icons.5.0.5.css",
    "/static/vendor/framework7-icons/fonts/Framework7Icons-Regular.woff2",
    "/static/images/favicon.ico",
    "/static/images/favicon.png",
    "/static/images/apple-touch-icon.png",
    "/static/images/favicon-16x16.png",
    "/static/images/favicon-32x32.png",
    "/static/images/favicon-192x192.png",
    "/static/images/favicon-512x512.png",
    "/static/images/svgs/primary-20x20.svg",
    "/static/images/svgs/primary-32x32.svg",
    "/static/images/svgs/primary-48x48.svg",
    "/static/images/svgs/primary-56x56.svg",
    "/static/images/pwa/badge-72.png",
    "/static/images/pwa/icon-72.png",
    "/static/images/pwa/icon-192.png",
    "/static/images/pwa/icon-512.png",
];


self.addEventListener("install", (event) => {
    event.waitUntil(
        caches.open(SHELL_CACHE).then((cache) => cache.addAll(SHELL_ASSETS))
    );
});

self.addEventListener("activate", (event) => {
    event.waitUntil(
        caches.keys().then((keys) =>
            Promise.all(
                keys
                    .filter((k) => k !== SHELL_CACHE && k !== CONTENT_CACHE)
                    .map((k) => caches.delete(k))
            )
        )
    );
    self.clients.claim();
});


self.addEventListener("message", (event) => {
    if (event.data?.type === "SKIP_WAITING") {
        self.skipWaiting();
    }
});


self.addEventListener("fetch", (event) => {
    const { request } = event;
    const url = new URL(request.url);

    if (url.pathname === "/offline") {
        event.respondWith(
            fetch(request)
                .then((response) => {
                    const responseClone = response.clone();
                    caches.open(CONTENT_CACHE).then((cache) => cache.put(request, responseClone));
                    return response;
                })
                .catch(() => caches.match("/offline"))
        );
        return;
    }

    if (SHELL_ASSETS.includes(url.pathname)) {
        event.respondWith(
            caches.match(request).then((cached) => cached ?? fetch(request))
        );
        return;
    }

    event.respondWith(
        fetch(request).catch(() => caches.match("/offline"))
    );
});


self.addEventListener("push", (event) => {
    if (!event.data) return;

    event.waitUntil((async () => {
        if (Notification.permission !== "granted") {
            return;
        }

        let data;
        try {
            data = event.data.json();
        } catch (error) {
            const text = event.data.text();
            data = {
                title: "Feedbase",
                body: text,
                url: "/",
                notification_id: null,
            };
        }

        let notificationOptions =  {
            body: data?.body || "",
            icon: data?.icon || "/static/images/pwa/icon-192.png",
            badge: data?.badge || "/static/images/pwa/badge-72.png",
            data: {
                url: data?.url || "/",
                recordId: data?.notification_id  || null,
            }
        }

        if (data?.vibrate) {
            notificationOptions.vibrate = data.vibrate;
        }

        if (data?.require_interaction) {
            notificationOptions.requireInteraction = true;
        }

        await self.registration.showNotification(data.title || "Feedbase", notificationOptions);
    })());
});


self.addEventListener("notificationclick", (event) => {
    event.notification.close();

    const { url, recordId } = event.notification.data;

    if (!url || !recordId) return;

    event.waitUntil(
        fetch(`/api/v1/notifications/${recordId}/read`, {
            method: "PATCH",
            credentials: "same-origin",
            headers: { "Content-Type": "application/json" },
        }).then(() =>
            clients
                .matchAll({ type: "window", includeUncontrolled: true })
                .then((windowClients) => {
                    const existing = windowClients.find((c) =>
                        c.url.includes(self.location.origin)
                    );
                    if (existing) {
                        existing.focus();
                        return existing.navigate(url);
                    }
                    return clients.openWindow(url);
                })
        )
    );
});