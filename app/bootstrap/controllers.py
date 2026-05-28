from hooks import template_render_callback

from bootstrap.templates import template_engine
from lib.ext.fastapi import configure_controllers as _configure_controllers


def configure_controllers():
    """
    Configure the controllers for the FastAPI application.
    """

    return _configure_controllers(
        template_engine=template_engine,
        template_render_callback=template_render_callback,
    )
