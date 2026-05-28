from constants import TEMPLATE_RENDER_DURATION


def template_render_callback(template: str, duration: float) -> None:
    TEMPLATE_RENDER_DURATION.labels(name=template).observe(duration)
