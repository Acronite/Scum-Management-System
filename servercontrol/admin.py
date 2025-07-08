from django.contrib import admin
from .models import (
    GameServer, ServerConfiguration, ServerMetrics, 
    ServerLog, ServerCommand, ServerBackup
)


@admin.register(GameServer)
class GameServerAdmin(admin.ModelAdmin):
    list_display = ('name', 'server_ip', 'server_port', 'status', 'last_started', 'modified')
    list_filter = ('status', 'auto_restart', 'crash_restart')
    search_fields = ('name', 'server_ip', 'description')
    readonly_fields = ('process_id', 'last_started', 'last_stopped', 'created', 'modified')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'status')
        }),
        ('Network Configuration', {
            'fields': ('server_ip', 'server_port', 'query_port', 'rcon_port', 'rcon_password')
        }),
        ('Server Files', {
            'fields': ('server_path', 'executable_name', 'startup_parameters')
        }),
        ('Auto Management', {
            'fields': ('auto_restart', 'auto_restart_time', 'crash_restart')
        }),
        ('Status Information', {
            'fields': ('process_id', 'last_started', 'last_stopped'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created', 'modified', 'modified_by'),
            'classes': ('collapse',)
        })
    )


@admin.register(ServerConfiguration)
class ServerConfigurationAdmin(admin.ModelAdmin):
    list_display = ('server', 'config_name', 'file_path', 'is_active', 'modified')
    list_filter = ('is_active', 'backup_on_change', 'server')
    search_fields = ('config_name', 'file_path')
    readonly_fields = ('created', 'modified')


@admin.register(ServerMetrics)
class ServerMetricsAdmin(admin.ModelAdmin):
    list_display = ('server', 'timestamp', 'cpu_usage', 'memory_percentage', 'player_count')
    list_filter = ('server', 'timestamp')
    readonly_fields = ('timestamp',)
    
    def has_add_permission(self, request):
        return False  # Metrics are created automatically


@admin.register(ServerLog)
class ServerLogAdmin(admin.ModelAdmin):
    list_display = ('server', 'timestamp', 'log_level', 'source', 'message_preview')
    list_filter = ('log_level', 'source', 'server', 'timestamp')
    search_fields = ('message',)
    readonly_fields = ('timestamp',)
    
    def message_preview(self, obj):
        return obj.message[:100] + '...' if len(obj.message) > 100 else obj.message
    message_preview.short_description = 'Message'
    
    def has_add_permission(self, request):
        return False  # Logs are created automatically


@admin.register(ServerCommand)
class ServerCommandAdmin(admin.ModelAdmin):
    list_display = ('server', 'command_type', 'status', 'executed_by', 'created')
    list_filter = ('command_type', 'status', 'server', 'executed_by')
    search_fields = ('command', 'output')
    readonly_fields = ('created', 'executed_at', 'completed_at')


@admin.register(ServerBackup)
class ServerBackupAdmin(admin.ModelAdmin):
    list_display = ('server', 'backup_name', 'backup_type', 'file_size_mb', 'created')
    list_filter = ('backup_type', 'server', 'created')
    search_fields = ('backup_name',)
    readonly_fields = ('created', 'file_size')
    
    def file_size_mb(self, obj):
        return f"{obj.get_file_size_mb()} MB"
    file_size_mb.short_description = 'File Size'