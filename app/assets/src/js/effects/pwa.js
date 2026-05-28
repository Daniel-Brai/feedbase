function handleHtmxOfflineRedirect(event) {
    const xhr = event.detail?.xhr;
    if (!xhr) {
        return;
    }

    if (xhr.status === 0 && window.navigator && window.navigator.onLine === false) {
        window.location.href = '/offline';
    }
}

document.addEventListener('htmx:afterRequest', handleHtmxOfflineRedirect);
