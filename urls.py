from django.contrib import admin
from django.urls import path, include

from start.views.start import start

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', start, name='start'),
    path('deals/', include('deals.urls')),
]