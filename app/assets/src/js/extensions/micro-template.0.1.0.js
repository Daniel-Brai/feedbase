(function (htmx) {
    "use strict";

    if (!htmx) return;

    function resolvePath(obj, path) {
        if (path === "this") return obj;
        return path.split(".").reduce(function (acc, k) {
            return acc != null ? acc[k] : undefined;
        }, obj);
    }

    function escapeHtml(str) {
        return String(str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/\"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function render(tpl, data, extra) {
        extra = extra || {};
        var html = tpl;

        html = html.replace(
            /\[\[#each\s+([\w.]+)\]\]([\s\S]*?)\[\[\/each\]\]/g,
            function (_, path, inner) {
                var arr = resolvePath(data, path);
                if (!Array.isArray(arr)) return "";
                return arr
                    .map(function (item, i) {
                        var ctx =
                            item && typeof item === "object"
                                ? Object.assign({ "@index": i, "@parent": data }, item)
                                : { this: item, "@index": i, "@parent": data };
                        return render(inner, ctx, {});
                    })
                    .join("");
            },
        );

        html = html.replace(
            /\[\[#if\s+([\w.@]+)\]\]([\s\S]*?)\[\[\/if\]\]/g,
            function (_, path, inner) {
                var val = resolvePath(data, path);
                if (val === undefined) val = extra[path];
                return val ? render(inner, data, extra) : "";
            },
        );

        html = html.replace(/\[\[\[([\w.@]+)\]\]\]/g, function (_, path) {
            var val = resolvePath(data, path);
            if (val === undefined && path.indexOf('.') === -1) val = extra[path];
            if (val !== undefined && val !== null) return String(val);
            if (path.indexOf('.') !== -1) return "null";
            return "";
        });

        html = html.replace(/\[\[([\w.@]+)\]\]/g, function (_, path) {
            var val = resolvePath(data, path);
            if (val === undefined && path.indexOf('.') === -1) val = extra[path];
            if (val !== undefined && val !== null) return escapeHtml(String(val));
            if (path.indexOf('.') !== -1) return "null";
            return "";
        });

        return html;
    }

    htmx.defineExtension("micro-template", {
        onEvent: function () { },
    });

    htmx.template = htmx.template || {};
    htmx.template.render = render;
})(window.htmx);
