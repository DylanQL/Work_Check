"""
URL configuration for Work_Check project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from System import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.home, name='home'),

    # Rutas para gestión de usuarios
    path('users/', views.manage_users, name='manage_users'),
    path('add_user/', views.add_user, name='add_user'),
    path('update_user/<int:user_id>/', views.update_user, name='update_user'),

    # Rutas para la gestión de cuentas existentes
    path('accounts/', views.list_accounts, name='list_accounts'),
    path('accounts/update/<int:account_id>/', views.update_account, name='update_account'),

    # Rutas para gestión de Timesheet Scores
    path('timesheets/', views.list_timesheets, name='list_timesheets'),
    path('timesheets/update/<int:timesheet_id>/', views.update_timesheet, name='update_timesheet'),

    # Rutas para gestión de ciclos de evaluación
    path('evaluation_cycles/', views.list_evaluation_cycles, name='list_evaluation_cycles'),
    path('evaluation_cycles/create/', views.create_evaluation_cycle, name='create_evaluation_cycle'),
    path('evaluation_cycles/update/<int:cycle_id>/', views.update_evaluation_cycle, name='update_evaluation_cycle'),
    path('evaluation_cycles/delete/<int:cycle_id>/', views.delete_evaluation_cycle, name='delete_evaluation_cycle'),

    # Rutas para asignación de evaluaciones (Temp_EvaluationAssignment)
    path('temp_assignments/', views.list_temp_evaluation_assignments, name='list_temp_assignments'),
    path('temp_assignments/create/', views.create_temp_evaluation_assignment, name='create_temp_assignment'),
    path('temp_assignments/update/<int:assignment_id>/', views.update_temp_evaluation_assignment, name='update_temp_assignment'),
    path('temp_assignments/delete/<int:assignment_id>/', views.delete_temp_evaluation_assignment, name='delete_temp_assignment'),
    path('temp_assignments/send/', views.send_assignments_to_historic, name='send_temp_assignments'),

    # Rutas para registros históricos
    path('permanent_assignments/', views.list_permanent_assignments, name='list_permanent_assignments'),
    path('summary/<int:summary_id>/', views.detail_summary, name='detail_summary'),
    path('evaluation_details/<int:evaluation_details_id>/', views.detail_evaluation_details, name='detail_evaluation_details'),

    # Ruta para evaluaciones de líderes
    path('leaders_evaluations/', views.leaders_evaluations, name='leaders_evaluations'),

    # Ruta para evaluaciones de empleados
    path('employees_evaluations/', views.employees_evaluations, name='employees_evaluations'),

    # Ruta para evaluación de líderes
    path('evaluate_leaders/', views.evaluate_leaders, name='evaluate_leaders'),

    # Ruta para evaluación de empleados
    path('evaluate_employees/', views.evaluate_employees, name='evaluate_employees'),

]