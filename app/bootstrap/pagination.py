from typing import Any

from lib.pagination import add_pagination


def configure_pagination(app: Any):
    """
    Configure pagination for the application
    """

    add_pagination(app)
