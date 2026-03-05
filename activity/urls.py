from django.urls import path
from .views import ActivityFeedView

urlpatterns = [
    path("feed/", ActivityFeedView.as_view()),
]
