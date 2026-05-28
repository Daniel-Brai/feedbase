from fastapi import FastAPI

from settings import settings


def configure_lib_routers(app: FastAPI) -> None:
    """
    Configure routers from the lib packages.
    """

    from lib.auth import get_auth_router, get_backend, make_auth_dependency
    from lib.i18n import get_i18n_router
    from lib.notifications import get_notifications_router

    get_current_user = make_auth_dependency(get_backend())

    app.include_router(get_auth_router(auth_dep=get_current_user))
    app.include_router(get_notifications_router(auth_dep=get_current_user))
    app.include_router(get_i18n_router(locale_cookie_name=settings.APP_LOCALE_COOKIE_NAME))


def configure_api_routers(app: FastAPI) -> None:
    """
    Configure routers from the API controllers.
    """

    from controllers.api.v1 import ArticleAnnotationController as V1ArticleAnnotationController
    from controllers.api.v1 import ArticleController as V1ArticleController
    from controllers.api.v1 import FeedController as V1FeedController
    from controllers.api.v1 import FeedSubscriptionController as V1FeedSubscriptionController
    from controllers.api.v1 import FolderController as V1FolderController
    from controllers.api.v1 import UserController as V1UserController

    V1FeedController.register(app)
    V1ArticleController.register(app)
    V1ArticleAnnotationController.register(app)
    V1FolderController.register(app)
    V1UserController.register(app)
    V1FeedSubscriptionController.register(app)


def configure_misc_routers(app: FastAPI) -> None:
    """
    Configure any additional routers that don't fit into the other categories.
    """

    from controllers.misc import FeverController, HealthController, OPMLController

    FeverController.register(app)
    HealthController.register(app)
    OPMLController.register(app)


def configure_view_routers(app: FastAPI) -> None:
    """
    Configure routers for views.
    """

    from controllers.views import AuthViewController, HomeViewController, PWAViewController, SettingsViewController

    HomeViewController.register(app)
    PWAViewController.register(app)
    SettingsViewController.register(app)
    AuthViewController.register(app)


def configure_routers(app: FastAPI) -> None:
    """
    Configure the routers for the FastAPI application.
    """

    configure_view_routers(app)
    configure_lib_routers(app)
    configure_api_routers(app)
    configure_misc_routers(app)
