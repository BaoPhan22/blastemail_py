from django.urls import path
from . import views
from .views import SkipSiteView, SkipExtensionView

urlpatterns = [
    path('members/', views.members, name='members'),
    path('stop-crawling/', views.stop_crawling, name='stop-crawling'),
    path('fetch-emails/', views.fetch_emails, name='fetch-emails'),
    path('hide-email/<int:id>', views.hide_email, name='hide-email'),
    path('skip_site/', SkipSiteView.as_view(), name='skip_site'),
    path('skip_extension/', SkipExtensionView.as_view(), name='skip_extension'),
]
