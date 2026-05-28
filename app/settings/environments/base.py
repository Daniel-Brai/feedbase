import secrets
from pathlib import Path
from typing import Annotated, Any, Literal, Self

from dotenv import load_dotenv
from pydantic import (
    AnyUrl,
    BeforeValidator,
    EmailStr,
    PositiveFloat,
    PositiveInt,
    PostgresDsn,
    RedisDsn,
    StringConstraints,
    computed_field,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

from enums import Environment, JobBackend, MailerBackend, ThrottlerBackend
from lib.auth.types import Password
from lib.validators import validate_bool, validate_list

load_dotenv()


class Settings(BaseSettings):
    """
    Base configuration settings for the application.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="forbid",
    )

    APP_DIR: str = str(Path(__file__).resolve().parents[2])
    APP_WEB_TEMPLATES_DIR: str = str(Path(APP_DIR) / "views" / "web")
    APP_MAILER_TEMPLATES_DIR: str = str(Path(APP_DIR) / "views" / "mailer")
    APP_LOCALES_DIR: str = str(Path(APP_DIR) / "locales")
    APP_LOCALE_COOKIE_NAME: str = "feedbase_locale"
    APP_DEFAULT_LOCALE: str = "en"
    APP_FALLBACK_LOCALE: str = "en"

    APP_STATIC_URL: str = "/static"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def APP_ASSETS_DIR(self) -> str:

        if self.APP_ENVIRONMENT == Environment.PRODUCTION:
            return str(Path(self.APP_DIR) / "assets" / "dist")

        return str(Path(self.APP_DIR) / "assets" / "src")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def APP_ASSETS_DEV_MODE(self) -> bool:
        return self.APP_ENVIRONMENT == Environment.DEVELOPMENT

    APP_NAME: str = "Feedbase"
    APP_DESCRIPTION: str = "A self-hosted RSS Feed reader with a focus on simplicity, speed and privacy."
    APP_VERSION: str = "0.1.0"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def APP_USER_AGENT(self) -> str:
        return f"Feedbase/{self.APP_VERSION}"

    APP_DOMAIN: str = "localhost"
    APP_PORT: PositiveInt = 5555
    APP_ENVIRONMENT: Environment = Environment.DEVELOPMENT
    APP_SUPERUSER_NAME: Annotated[str, StringConstraints(max_length=500, strip_whitespace=True)] = "Adminstrator"
    APP_SUPERUSER_EMAIL: Annotated[EmailStr, StringConstraints(to_lower=True, strip_whitespace=True)] = (
        "admin@feedbase.app"
    )
    APP_SUPERUSER_PASSWORD: Password = Password("Password@123")
    APP_CORS_ORIGINS: Annotated[list[AnyUrl | str], BeforeValidator(validate_list())] = []
    APP_MONITORING_ENABLED: bool = False
    APP_LOG_LEVEL: Literal[
        "FATAL",
        "WARN",
        "CRITICAL",
        "ERROR",
        "WARNING",
        "INFO",
        "DEBUG",
    ] = "INFO"

    VAPID_CREDENTIALS_PATH: str = "credentials/vapid"
    VAPID_CLAIMS_SUBJECT: str = "mailto:hello@feedbase.app"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def VAPID_PRIVATE_KEY_PATH(self) -> str:
        return str(Path(self.APP_DIR) / self.VAPID_CREDENTIALS_PATH / "private_key.pem")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def VAPID_PUBLIC_KEY_PATH(self) -> str:
        return str(Path(self.APP_DIR) / self.VAPID_CREDENTIALS_PATH / "public_key.txt")

    APP_HTTP_CLIENT_TIMEOUT_SECONDS: PositiveFloat = 2.5 * 60  # 2.5 minute
    APP_FEED_POLLING_INTERVAL_SECONDS: PositiveInt = 45 * 60  # 45 minutes
    APP_ARTICLE_SWEEP_ENABLED: bool = False
    APP_ARTICLE_RETENTION_DAYS: PositiveInt = 30  # 30 days
    APP_INVITATIONS_ENABLED: bool = False

    OPENAPI_USERNAME: str = "Administrator"
    OPENAPI_PASSWORD: str = "Password@123"
    OPENAPI_DOCS_URL: str = "/docs"
    OPENAPI_JSON_SCHEMA_URL: str = "/openapi.json"

    API_V1_STR: str = "/api/v1"

    AUTH_SESSION_SECRET_KEY: str = secrets.token_hex(64)
    AUTH_SESSION_COOKIE_NAME: str = "feedbase_auth_session"

    SENTRY_DSN: Annotated[str, StringConstraints(strip_whitespace=True)] | None = None
    GRAFANA_ADMIN_USERNAME: str = "Adminstrator"
    GRAFANA_ADMIN_EMAIL: str = "admin@feedbase.app"
    GRAFANA_ADMIN_PASSWORD: str = "Password@123"
    PROMETHEUS_METRICS_ENABLED: Annotated[bool, BeforeValidator(validate_bool())] = False
    PROMETHEUS_METRICS_URL: str = "/metrics"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def APP_WORKERS_COUNT(self) -> int:
        if self.APP_ENVIRONMENT == Environment.DEVELOPMENT or self.APP_ENVIRONMENT == Environment.TEST:
            return 1

        return 4

    @computed_field  # type: ignore[prop-decorator]
    @property
    def APP_SITE_URL(self) -> str:
        if self.APP_DOMAIN.startswith("http") or self.APP_DOMAIN.startswith("https"):
            return self.APP_DOMAIN

        if (
            self.APP_DOMAIN.startswith("localhost")
            or self.APP_DOMAIN.startswith("127.0.0.1")
            or self.APP_DOMAIN.startswith("::1")
            or self.APP_DOMAIN.startswith("0.0.0.0")
        ):
            return f"http://{self.APP_DOMAIN}:{self.APP_PORT}"

        return f"https://{self.APP_DOMAIN}"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def APP_DOMAIN_SECURE(self) -> bool:
        return self.APP_SITE_URL.startswith("https://")

    APP_POSTGRES_HOST: str = "localhost"
    APP_POSTGRES_PORT: int | None = None
    APP_POSTGRES_USER: str
    APP_POSTGRES_PASSWORD: str
    APP_POSTGRES_DB: str
    APP_POSTGRES_QUERY: str | None = None

    APP_REDIS_HOST: str = "localhost"
    APP_REDIS_PORT: int = 6379
    APP_REDIS_PASSWORD: str | None = None
    APP_REDIS_DB: str = "0"
    APP_REDIS_SCHEME: str = "redis"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def APP_SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        scheme = "postgresql+asyncpg"

        return PostgresDsn.build(
            scheme=scheme,
            username=self.APP_POSTGRES_USER,
            password=self.APP_POSTGRES_PASSWORD,
            host=self.APP_POSTGRES_HOST,
            port=self.APP_POSTGRES_PORT,
            path=self.APP_POSTGRES_DB,
            query=None,
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def APP_SQLALCHEMY_DATABASE_SYNC_URI(self) -> PostgresDsn:
        scheme = "postgresql+psycopg"

        return PostgresDsn.build(
            scheme=scheme,
            username=self.APP_POSTGRES_USER,
            password=self.APP_POSTGRES_PASSWORD,
            host=self.APP_POSTGRES_HOST,
            port=self.APP_POSTGRES_PORT,
            path=self.APP_POSTGRES_DB,
            query=self.APP_POSTGRES_QUERY,
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def APP_REDIS_URL(self) -> RedisDsn:
        return RedisDsn.build(
            scheme=self.APP_REDIS_SCHEME,
            host=self.APP_REDIS_HOST,
            port=self.APP_REDIS_PORT,
            password=self.APP_REDIS_PASSWORD,
            path=self.APP_REDIS_DB,
        )

    USE_THROTTLER_BACKEND: ThrottlerBackend = ThrottlerBackend.MEMORY

    USE_JOB_BACKEND: JobBackend = JobBackend.DATABASE

    CELERY_REDIS_HOST: str = "localhost"
    CELERY_REDIS_PORT: int = 6379
    CELERY_REDIS_USER: str | None = None
    CELERY_REDIS_PASSWORD: str | None = None
    CELERY_REDIS_DB: str = "0"
    CELERY_REDIS_SCHEME: str = "redis"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def CELERY_BROKER_DSN(self) -> RedisDsn:
        return RedisDsn.build(
            scheme=self.CELERY_REDIS_SCHEME,
            host=self.CELERY_REDIS_HOST,
            port=self.CELERY_REDIS_PORT,
            username=self.CELERY_REDIS_USER,
            password=self.CELERY_REDIS_PASSWORD,
            path=self.CELERY_REDIS_DB,
        )

    CELERY_CONCURRENCY: PositiveInt = 4

    FILE_STORAGE_MEDIA_ROOT: str = str(Path(APP_DIR) / "media")
    FILE_STORAGE_MAX_SIZE: int = 1024 * 1024 * 50  # 50 MB
    FILE_STORAGE_PRESIGNGED_EXPIRY_TIME: int = 2 * 60 * 60  # 2 hours
    FILE_STORAGE_PRESIGNED_UPLOAD_EXPIRY_TIME: int = 10 * 60  # 10 minutes
    FILE_STORAGE_S3_BUCKET_NAME: str | None = None
    FILE_STORAGE_S3_REGION_NAME: str = "us-east-1"
    FILE_STORAGE_S3_ACCESS_KEY_ID: str | None = None
    FILE_STORAGE_S3_SECRET_ACCESS_KEY: str | None = None
    FILE_STORAGE_S3_ENDPOINT_URL: str | None = None
    FILE_STORAGE_CLOUDINARY_CLOUD_NAME: str | None = None
    FILE_STORAGE_CLOUDINARY_API_KEY: str | None = None
    FILE_STORAGE_CLOUDINARY_API_SECRET: str | None = None

    USE_MAILER_BACKEND: MailerBackend = MailerBackend.CONSOLE
    MAILER_VERIFY_ON_STARTUP: bool = False
    MAILER_DEFAULT_SENDER_NAME: str | None = None
    MAILER_DEFAULT_SENDER_EMAIL: EmailStr = "no-reply@feedbase.app"
    MAILER_SMTP_TLS: bool = True
    MAILER_SMTP_SSL: bool = False
    MAILER_SMTP_AUTH_SURPPORT: bool = False
    MAILER_SMTP_PORT: int = 587
    MAILER_SMTP_HOST: str = "localhost"
    MAILER_SMTP_USER: str | None = None
    MAILER_SMTP_TIMEOUT: int = 30
    MAILER_SMTP_PASSWORD: str | None = None
    MAILER_SES_REGION_NAME: str = "us-east-1"
    MAILER_SES_ACCESS_KEY_ID: str | None = None
    MAILER_SES_SECRET_ACCESS_KEY: str | None = None

    @model_validator(mode="after")
    def _set_default_emails_from(self) -> Self:
        if not self.MAILER_DEFAULT_SENDER_NAME:
            self.MAILER_DEFAULT_SENDER_NAME = self.APP_NAME

        return self

    @model_validator(mode="after")
    def _enforce_non_default_values(self) -> Self:
        self._check_default_values("OPENAPI_PASSWORD", "Password@123", self.OPENAPI_PASSWORD)
        self._check_default_values(
            "APP_SUPERUSER_PASSWORD",
            "Password@123",
            self.APP_SUPERUSER_PASSWORD,
            raise_error=False,
        )
        self._check_default_values(
            "APP_SUPERUSER_EMAIL",
            "admin@feedbase.app",
            self.APP_SUPERUSER_EMAIL,
            raise_error=False,
        )

        return self

    @model_validator(mode="after")
    def _enforce_monitoring_check(self) -> Self:
        if self.APP_MONITORING_ENABLED and (not self.SENTRY_DSN and not self.PROMETHEUS_METRICS_ENABLED):
            raise ValueError(
                "APP_MONITORING_ENABLED is True, but SENTRY_DSN or PROMETHEUS_METRICS_ENABLED is not set. "
                "Please set SENTRY_DSN and/or PROMETHEUS_METRICS_ENABLED to enable monitoring."
            )

        return self

    @model_validator(mode="after")
    def _enforce_mailer_backend_requirements(self) -> Self:
        if self.USE_MAILER_BACKEND == MailerBackend.SMTP:
            self._check_values_existence_on_condition(
                condition=True,
                var_names_and_values=[
                    ("MAILER_SMTP_HOST", self.MAILER_SMTP_HOST),
                    ("MAILER_SMTP_PORT", self.MAILER_SMTP_PORT),
                    ("MAILER_SMTP_USER", self.MAILER_SMTP_USER),
                    ("MAILER_SMTP_PASSWORD", self.MAILER_SMTP_PASSWORD),
                ],
            )
        elif self.USE_MAILER_BACKEND == MailerBackend.SES:
            self._check_values_existence_on_condition(
                condition=True,
                var_names_and_values=[
                    ("MAILER_SES_REGION_NAME", self.MAILER_SES_REGION_NAME),
                    ("MAILER_SES_ACCESS_KEY_ID", self.MAILER_SES_ACCESS_KEY_ID),
                    ("MAILER_SES_SECRET_ACCESS_KEY", self.MAILER_SES_SECRET_ACCESS_KEY),
                ],
            )

        return self

    def _check_values_existence_on_condition(
        self,
        condition: bool,
        var_names_and_values: list[tuple[str, Any | None]],
    ) -> None:
        if condition:
            for var_name, value in var_names_and_values:
                if not value:
                    raise ValueError(f"{var_name} must be set when the condition is met.")

    def _check_default_values(
        self,
        var_name: str,
        default_value: str,
        current_value: str | None,
        raise_error: bool = True,
    ) -> None:
        if current_value == default_value:
            message = (
                f'The value of {var_name} is "{default_value}", '
                "for security, please change it, at least for deployments."
            )
            if self.APP_ENVIRONMENT in [
                Environment.PRODUCTION,
                Environment.STAGING,
            ]:
                if raise_error:
                    raise ValueError(message)
                else:
                    import warnings

                    warnings.warn(message, stacklevel=2)
