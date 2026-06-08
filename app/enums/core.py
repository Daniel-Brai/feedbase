from enum import StrEnum


class Environment(StrEnum):
    """
    Enumeration for different application environments.

    Attributes:
        DEVELOPMENT (str, "development"): Represents the development environment.
        PRODUCTION (str, "production"): Represents the production environment.
        STAGING (str, "staging"): Represents the staging environment.
        TEST (str, "test"): Represents the testing environment.
    """

    DEVELOPMENT = "development"
    PRODUCTION = "production"
    STAGING = "staging"
    TEST = "test"


class JobBackend(StrEnum):
    """
    Enumeration for different job backends.

    Attributes:
        CELERY (str, "celery"): Represents the Celery job backend.
        DATABASE (str, "db"): Represents a custom database-backed job backend.
    """

    CELERY = "celery"
    DATABASE = "db"


class MailerBackend(StrEnum):
    """
    Enumeration for different mailer backends.

    Attributes:
        SMTP (str, "smtp"): Represents the SMTP mailer backend.
        CONSOLE (str, "console"): Represents a console mailer backend that prints emails to the console.
        SES (str, "ses"): Represents the SES mailer backend.
    """

    SMTP = "smtp"
    CONSOLE = "console"
    SES = "ses"


class ThrottlerBackend(StrEnum):
    """
    Enumeration for different throttler backends.

    Attributes:
        MEMORY (str, "memory"): Represents an in-memory throttler backend.
        REDIS (str, "redis"): Represents a Redis-based throttler backend.
        NOOP (str, "noop"): Represents a no-op throttler backend that performs no throttling.
    """

    MEMORY = "memory"
    REDIS = "redis"
    NOOP = "noop"


class NotificationEventEmitterBackend(StrEnum):
    """
    Enumeration for different notification event stream backends.

    Attributes:
        REDIS (str, "redis"): Represents a Redis-based notification event stream backend.
        MEMORY (str, "memory"): Represents an in-memory notification event stream backend.
    """

    REDIS = "redis"
    MEMORY = "memory"
