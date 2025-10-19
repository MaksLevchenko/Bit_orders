from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings
from django.urls import path, include

from start.views.start import start

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', start, name='start'),
    path('deals/', include('deals.urls')),
    path('products/', include('products.urls')),
    path('employees/', include('employees.urls')),
    path('map/', include('companies_on_maps.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)