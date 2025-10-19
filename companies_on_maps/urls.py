from django.urls import path
from companies_on_maps.views import views

urlpatterns = [
    path('', views.company_map, name='company_map'),
    # path('sync/', views.sync_companies, name='sync_companies'),
    # path('api/companies/', views.get_companies_json, name='companies_json'),
]