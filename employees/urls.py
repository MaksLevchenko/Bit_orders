from django.urls import path
from employees.views import views

urlpatterns = [
    path('', views.employee_hierarchy, name='employee_hierarchy'),
    path('create_call/', views.create_register_calls, name='create_call'),

]