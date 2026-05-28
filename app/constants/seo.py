from dataclasses import dataclass, field

from bootstrap.i18n import i18n
from enums import OGType


@dataclass
class PageMeta:
    """
    Schema for SEO metadata of a page, including Open Graph and Twitter Card information.

    Attributes:

        title (str): The title of the page, used in the  `<title>` tag and
            the `<meta property="og:title">` tag for Open Graph.
        description (str): A brief description of the page, used in the
            `<meta name="description">` tag and as the default Open Graph description.
        canonical (str | None): The canonical URL of the page, used in the
            `<link rel="canonical">` tag to indicate the preferred URL for SEO.
        robots (str): The value for the `<meta name="robots">` tag, controlling
            how search engines should index the page (default: "noindex, nofollow").
        og_type (OGType): The Open Graph type of the page, used in the
            `<meta property="og:type">` tag (default: OGType.WEBSITE).
        og_image (str | None): The URL of the Open Graph image, used in the
            `<meta property="og:image">` tag to specify the image that represents the page.
        og_image_alt (str | None): The alt text for the Open Graph image, used in the
            `<meta property="og:image:alt">` tag to provide a description of the image for accessibility and SEO.
        twitter_card (str): The type of Twitter Card to use, used in the `<meta name="twitter:card">` tag (default: "summary").
        twitter_site (str | None): The Twitter handle of the site, used in the `<meta name="twitter:site">` tag to associate the page with a Twitter account.
        theme_color (str): The theme color of the page, used in the `<meta name="theme-color">` tag to set the browser's theme color on supported devices (default: "#0e0e0e").
        extra (dict[str, str]): A dictionary of additional meta tags to include in the page, where the key is the meta tag name and the value is the content of the meta tag (default: empty dictionary).
    """

    title: str
    description: str
    canonical: str | None = None
    robots: str = "noindex, nofollow"
    og_type: OGType = OGType.WEBSITE
    og_image: str | None = None
    og_image_alt: str | None = None
    twitter_card: str = "summary"
    twitter_site: str | None = None
    theme_color: str = "#0e0e0e"
    extra: dict[str, str] = field(default_factory=dict)

    @property
    def full_title(self) -> str:
        if self.title == "Feedbase":
            return "Feedbase"

        return f"{self.title} — Feedbase"


def verify_email_meta() -> PageMeta:
    _t = i18n.get_translator()

    return PageMeta(
        title=_t("seo.verify_email.title", default="Verify email"),
        description=_t(
            "seo.verify_email.description",
            default="Verify your email address to complete registration.",
        ),
        robots="noindex, nofollow",
    )


def login_meta() -> PageMeta:
    _t = i18n.get_translator()

    return PageMeta(
        title=_t("seo.login.title", default="Sign in"),
        description=_t("seo.login.description", default="Sign in to your Feedbase instance."),
        robots="noindex, nofollow",
    )


def forgot_password_meta() -> PageMeta:
    _t = i18n.get_translator()

    return PageMeta(
        title=_t("seo.forgot_password.title", default="Forgot password"),
        description=_t(
            "seo.forgot_password.description",
            default="Reset your password if you've forgotten it.",
        ),
        robots="noindex, nofollow",
    )


def reset_password_meta() -> PageMeta:
    _t = i18n.get_translator()

    return PageMeta(
        title=_t("seo.reset_password.title", default="Reset password"),
        description=_t(
            "seo.reset_password.description",
            default="Set a new password for your account.",
        ),
        robots="noindex, nofollow",
    )


def home_meta() -> PageMeta:
    _t = i18n.get_translator()

    return PageMeta(
        title=_t("seo.home.title"),
        description=_t("seo.home.description"),
        robots="noindex, nofollow",
    )


def offline_meta() -> PageMeta:
    _t = i18n.get_translator()

    return PageMeta(
        title=_t("seo.offline.title", default="Offline"),
        description=_t(
            "seo.offline.description",
            default="You are currently offline. This page is available while offline.",
        ),
        robots="noindex, nofollow",
    )


def settings_meta() -> PageMeta:
    _t = i18n.get_translator()

    return PageMeta(
        title=_t(
            "seo.settings.title",
            default="Settings",
        ),
        description=_t(
            "seo.settings.description",
            default="Manage your settings.",
        ),
        robots="noindex, nofollow",
    )
