from fastapi import FastAPI


def fastapi_app() -> FastAPI:
    """
    Return the configured FastAPI application instance.
    """

    from bootstrap.assets import configure_asset_manager
    from bootstrap.auth import configure_auth
    from bootstrap.controllers import configure_controllers
    from bootstrap.errors import configure_exceptions
    from bootstrap.fastapi import create_fastapi_app
    from bootstrap.form import configure_forms
    from bootstrap.i18n import configure_i18n
    from bootstrap.jobs import configure_jobs
    from bootstrap.mailer import configure_mailer
    from bootstrap.middlewares import configure_middlewares
    from bootstrap.monitoring import configure_monitoring
    from bootstrap.notifications import configure_notifications
    from bootstrap.openapi import configure_openapi
    from bootstrap.pagination import configure_pagination
    from bootstrap.routers import configure_routers
    from bootstrap.static import configure_static
    from bootstrap.storage import configure_storage
    from bootstrap.throttler import configure_throttler

    app = create_fastapi_app()

    configure_pagination(app)

    configure_throttler()

    configure_exceptions(app)

    configure_static(app)

    configure_asset_manager()

    configure_controllers()

    configure_middlewares(app)

    configure_mailer()

    configure_i18n(app)

    configure_monitoring(app)

    configure_auth()

    configure_storage()

    configure_jobs()

    configure_forms(app)

    configure_notifications()

    configure_routers(app)

    configure_openapi(app)

    return app
