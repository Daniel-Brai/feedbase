from redis.asyncio import ConnectionPool
from redis.asyncio.retry import Retry
from redis.backoff import ExponentialWithJitterBackoff
from redis.exceptions import BusyLoadingError, ConnectionError, TimeoutError

from settings import settings

redis_connection_pool = ConnectionPool.from_url(
    str(settings.APP_REDIS_URL),
    max_connections=20,
    socket_timeout=10.0,
    socket_connect_timeout=10.0,
    health_check_interval=30,
    retry=Retry(
        backoff=ExponentialWithJitterBackoff(base=1, cap=10),
        retries=5,
        supported_errors=(
            ConnectionError,
            TimeoutError,
            BusyLoadingError,
        ),
    ),
    decode_responses=False,
)
