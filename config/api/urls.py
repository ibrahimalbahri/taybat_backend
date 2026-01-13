from django.urls import path

from config.api.views import AppVersionView, AppLegalLinksView


urlpatterns = [
    path("config/version", AppVersionView.as_view(), name="config-version"),
    path("config/legal", AppLegalLinksView.as_view(), name="config-legal"),
]
