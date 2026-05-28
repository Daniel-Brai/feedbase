from enums import ThrottlerBackend
from lib.auth import AUTH_THROTTLER_LIMITS
from lib.throttler import MemoryStorage, RedisStorage
from lib.throttler import configure_throttler as _configure_throttler
from settings import settings


def configure_throttler():
    """
    Configure the throttler for the application.
    """

    backend = settings.USE_THROTTLER_BACKEND

    if backend == ThrottlerBackend.MEMORY:
        return _configure_throttler(
            storage=MemoryStorage(),
            namespace_limits={
                **AUTH_THROTTLER_LIMITS,
            },
        )
    elif backend == ThrottlerBackend.REDIS:
        from bootstrap.redis import redis_connection_pool

        return _configure_throttler(
            storage=RedisStorage(str(settings.APP_REDIS_URL), connection_pool=redis_connection_pool),
            namespace_limits={
                **AUTH_THROTTLER_LIMITS,
            },
        )
    else:
        return
