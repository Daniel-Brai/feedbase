export const PaginationUtils = (function () {
    function transformToPaginationStream(payload) {
        console.debug(
            "utils/pagination.js: transformToPaginationStream called with payload:",
            payload,
        );

        if (payload.data && payload?.data?.event === "htmx-pagination:refresh" && payload?.data?.id) {
            return { id: payload.data.id };
        }

        return null;
    }

    return {
        transformToPaginationStream
    };
})();