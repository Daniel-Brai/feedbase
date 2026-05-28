import json
from datetime import datetime

from anyio import Path

from bootstrap.i18n import i18n
from lib.notifications import load_url_safe_vapid_public_key
from lib.templates import create_template_engine
from settings import settings

template_engine = create_template_engine(
    async_mode=True,
    template_dir=Path(settings.APP_WEB_TEMPLATES_DIR),
    env_globals={
        "now": datetime.now,
        "tojson": lambda obj: (obj.model_dump() if hasattr(obj, "model_dump") else json.dumps(obj)),
        "_t": lambda key, **kwargs: i18n.get_translator()(key, **kwargs),
        "APP_LOCALE": lambda: i18n.get_current_locale() or settings.APP_DEFAULT_LOCALE,
        "APP_NAME": settings.APP_NAME,
        "APP_VERSION": settings.APP_VERSION,
        "APP_VAPID_PUBLIC_KEY": load_url_safe_vapid_public_key(settings.VAPID_PUBLIC_KEY_PATH, format="base64"),
    },
)
