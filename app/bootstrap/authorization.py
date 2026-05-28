from lib.auth import RBACBackend

authorization = RBACBackend(
    {
        "superadmin": ["*"],
        "admin": [
            "users:*",
            "feeds:*",
            "folders:*",
            "articles:*",
            "subscriptions:*",
            "settings:*",
        ],
        "editor": [
            "feeds:*",
            "users:read",
            "users:update",
            "folders:*",
            "articles:read",
            "articles:update",
            "subscriptions:*",
        ],
        "viewer": [
            "users:read",
            "feeds:read",
            "folders:read",
            "articles:read",
            "subscriptions:read",
        ],
    },
    default_roles=["viewer"],
)
