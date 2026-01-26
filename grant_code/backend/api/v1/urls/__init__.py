from django.urls import include, path
from .user import urlpatterns as user_urls
from .application import urlpatterns as application_urls

urlpatterns = [
    path('user/', include(user_urls)),
    path('', include(application_urls)),
]
