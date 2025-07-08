from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('front.urls')),
    path('account/', include('accounts.urls')),
    path('players/', include('players.urls')),
    path('settings/', include('settings.urls')),
]
