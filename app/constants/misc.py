from settings import settings

EXCLUDED_REQUEST_PATHS = {
    "/fever",
    "/health",
    "/ready",
    "/metrics",
    "/sw.js",
    "/.well-known",
    settings.APP_STATIC_URL,
    settings.OPENAPI_DOCS_URL,
    settings.OPENAPI_JSON_SCHEMA_URL,
}
