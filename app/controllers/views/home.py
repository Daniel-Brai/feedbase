from fastapi import Request
from fastapi.responses import HTMLResponse

from constants import NOTIFICATION_CTX, home_meta
from dependencies import AuthSafeDep
from forms import (
    AddFolderForm,
    ChangeLanguageForm,
    DeleteFolderForm,
    DiscoverFeedForm,
    EditFolderForm,
    LogoutForm,
    RefreshFeedSubscriptionsForm,
    RenameFeedSubscriptionForm,
)
from lib.ext.fastapi import Controller, before_action, get


class HomeViewController(Controller):
    """
    Controller for handling requests to the home view.
    """

    include_in_schema = False

    @before_action
    def authenticate(self, user: AuthSafeDep):
        """
        Dependency to ensure that the user is authenticated before accessing the home view.
        """
        if user is None:
            return self.redirect("/auth/login")

        self.current_user = user

    @get("/")
    async def home(
        self,
        request: Request,
    ) -> HTMLResponse:
        return await self.render(
            "pages/home.html",
            request=request,
            user=self.current_user,
            meta=home_meta(),
            notifications=NOTIFICATION_CTX,
            navbar={
                "urls": {
                    "logout_form_url": LogoutForm.get_form_url(),
                    "settings_url": "/settings",
                },
                "forms": {
                    "change_language_form": ChangeLanguageForm.get_form_name(),
                    "refresh_feeds_form": RefreshFeedSubscriptionsForm.get_form_name(),
                },
                "current_path": request.url.path,
            },
            panes={
                "sidebar": {
                    "urls": {
                        "article_stats_url": "/api/v1/articles/stats",
                        "folders_url": "/api/v1/folders",
                        "folder_edit_url": "/api/v1/folders/{folder_id}",
                        "subscription_edit_url": "/api/v1/subscriptions/{subscription_id}",
                        "subscriptions_url": "/api/v1/subscriptions",
                        "subscription_delete_url": "/api/v1/subscriptions/{subscription_id}",
                        "settings_url": "/settings",
                    },
                    "forms": {
                        "discover_feed_form": DiscoverFeedForm.get_form_name(),
                        "add_folder_form": AddFolderForm.get_form_name(),
                        "logout_form": LogoutForm.get_form_name(),
                    },
                    "form_urls": {
                        "rename_subscription_form_url": RenameFeedSubscriptionForm.get_form_url(),
                        "edit_folder_form_url": EditFolderForm.get_form_url(),
                        "delete_folder_form_url": DeleteFolderForm.get_form_url(),
                    },
                },
                "articles": {
                    "urls": {
                        "articles_url": "/api/v1/articles",
                        "article_status_update_url": "/api/v1/articles/{article_id}/status",
                        "article_annotations_count_url": "/api/v1/articles/{article_id}/annotations/count",
                        "annotations_url": "/api/v1/articles/{article_id}/annotations",
                        "annotations_create_url": "/api/v1/annotations",
                        "annotation_update_url": "/api/v1/annotations/{annotation_id}",
                        "annotation_delete_url": "/api/v1/annotations/{annotation_id}",
                    },
                },
                "reader": {
                    "urls": {
                        "annotations_url": "/api/v1/{article_id}/annotations",
                        "annotations_create_url": "/api/v1/annotations",
                        "annotation_delete_url": "/api/v1/annotations/{annotation_id}",
                        "annotation_update_url": "/api/v1/annotations/{annotation_id}",
                    },
                },
            },
        )
