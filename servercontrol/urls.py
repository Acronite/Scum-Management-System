from django.urls import path
from . import views

urlpatterns = [
    # Main dashboard
    path('', views.control_dashboard, name='control_dashboard'),
    
    # Server management
    path('server/<int:server_id>/', views.server_detail, name='server_detail'),
    path('server/<int:server_id>/action/', views.server_action, name='server_action'),
    path('server/<int:server_id>/command/', views.execute_command, name='execute_command'),
    path('server/<int:server_id>/logs/', views.server_logs, name='server_logs'),
    path('server/<int:server_id>/config/', views.server_config, name='server_config'),
    path('server/<int:server_id>/config/<int:config_id>/save/', views.save_config, name='save_config'),
    path('server/<int:server_id>/backup/', views.create_backup, name='create_backup'),
    
    # API endpoints
    path('api/server/<int:server_id>/status/', views.api_server_status, name='api_server_status'),
    path('api/server/<int:server_id>/logs/', views.api_recent_logs, name='api_recent_logs'),
    path('api/server/<int:server_id>/metrics/', views.server_metrics_api, name='server_metrics_api'),
]