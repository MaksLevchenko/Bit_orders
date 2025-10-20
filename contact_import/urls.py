from django.urls import path
from contact_import.views import views

urlpatterns = [
    path('import/', views.import_contacts, name='import_contacts'),
    path('export/', views.export_contacts, name='export_contacts'),
    path('api/companies/autocomplete/', views.CompanyAutocompleteView.as_view(), name='company_autocomplete'),
]