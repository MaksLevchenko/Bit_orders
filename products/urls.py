from django.urls import path
from products.views import views
from products.views.views import product_search_view, generate_qr_view, product_qr_detail_view

urlpatterns = [
    path('generate/', product_search_view, name='generate_qr'),
    path('generate/step2/', generate_qr_view, name='generate_qr_step2'),
    path('qr/<str:signed_token>/', product_qr_detail_view, name='product_qr_detail'),
    path('autocomplete/', views.product_autocomplete, name='product_autocomplete'),
]