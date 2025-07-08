from django.db import models
from django.contrib.auth.models import User
import json


class GameServer(models.Model):
    """Model representing a game server instance"""
    
    SERVER_STATUS_CHOICES = (
        ('stopped', 'Stopped'),
        ('starting', 'Starting'),
        ('running', 'Running'),
        ('stopping', 'Stopping'),
        ('crashed', 'Crashed'),
        ('maintenance', 'Maintenance'),
    )
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    server_ip = models.GenericIPAddressField()
    server_port = models.IntegerField()
    query_port = models.IntegerField()
    rcon_port = models.IntegerField(blank=True, null=True)
    rcon_password = models.CharField(max_length=100, blank=True, null=True)
    
    # Server paths and commands
    server_path = models.CharField(max_length=500)
    executable_name = models.CharField(max_length=100)
    startup_parameters = models.TextField(blank=True, null=True)
    
    # Status and monitoring
    status = models.CharField(max_length=20, choices=SERVER_STATUS_CHOICES, default='stopped')
    last_started = models.DateTimeField(blank=True, null=True)
    last_stopped = models.DateTimeField(blank=True, null=True)
    process_id = models.IntegerField(blank=True, null=True)
    
    # Auto-management settings
    auto_restart = models.BooleanField(default=False)
    auto_restart_time = models.TimeField(blank=True, null=True)
    crash_restart = models.BooleanField(default=True)
    
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.server_ip}:{self.server_port})"
    
    def is_online(self):
        return self.status == 'running'


class ServerConfiguration(models.Model):
    """Model for server configuration files"""
    
    server = models.ForeignKey(GameServer, on_delete=models.CASCADE, related_name='configurations')
    config_name = models.CharField(max_length=100)
    file_path = models.CharField(max_length=500)
    config_content = models.TextField()
    is_active = models.BooleanField(default=True)
    backup_on_change = models.BooleanField(default=True)
    
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, blank=True)
    
    def __str__(self):
        return f"{self.server.name} - {self.config_name}"


class ServerMetrics(models.Model):
    """Model for storing server performance metrics"""
    
    server = models.ForeignKey(GameServer, on_delete=models.CASCADE, related_name='metrics')
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Performance metrics
    cpu_usage = models.FloatField(blank=True, null=True)
    memory_usage = models.FloatField(blank=True, null=True)  # in MB
    memory_percentage = models.FloatField(blank=True, null=True)
    disk_usage = models.FloatField(blank=True, null=True)  # in GB
    
    # Game-specific metrics
    player_count = models.IntegerField(default=0)
    max_players = models.IntegerField(default=0)
    uptime_minutes = models.IntegerField(default=0)
    
    # Network metrics
    network_in = models.FloatField(blank=True, null=True)  # in MB/s
    network_out = models.FloatField(blank=True, null=True)  # in MB/s
    
    def __str__(self):
        return f"{self.server.name} - {self.timestamp}"


class ServerLog(models.Model):
    """Model for server log entries"""
    
    LOG_LEVEL_CHOICES = (
        ('debug', 'Debug'),
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    )
    
    server = models.ForeignKey(GameServer, on_delete=models.CASCADE, related_name='logs')
    timestamp = models.DateTimeField(auto_now_add=True)
    log_level = models.CharField(max_length=10, choices=LOG_LEVEL_CHOICES, default='info')
    message = models.TextField()
    source = models.CharField(max_length=100, blank=True, null=True)  # e.g., 'server', 'rcon', 'system'
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.server.name} - {self.log_level} - {self.timestamp}"


class ServerCommand(models.Model):
    """Model for tracking server commands and their execution"""
    
    COMMAND_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('executing', 'Executing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    
    server = models.ForeignKey(GameServer, on_delete=models.CASCADE, related_name='commands')
    command = models.TextField()
    command_type = models.CharField(max_length=50)  # e.g., 'rcon', 'system', 'restart'
    status = models.CharField(max_length=20, choices=COMMAND_STATUS_CHOICES, default='pending')
    output = models.TextField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    
    executed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    executed_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created']
    
    def __str__(self):
        return f"{self.server.name} - {self.command_type} - {self.status}"


class ServerBackup(models.Model):
    """Model for server backup management"""
    
    BACKUP_TYPE_CHOICES = (
        ('full', 'Full Server Backup'),
        ('config', 'Configuration Backup'),
        ('save', 'Save Game Backup'),
        ('logs', 'Logs Backup'),
    )
    
    server = models.ForeignKey(GameServer, on_delete=models.CASCADE, related_name='backups')
    backup_name = models.CharField(max_length=200)
    backup_type = models.CharField(max_length=20, choices=BACKUP_TYPE_CHOICES)
    file_path = models.CharField(max_length=500)
    file_size = models.BigIntegerField()  # in bytes
    
    created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.server.name} - {self.backup_name}"
    
    def get_file_size_mb(self):
        return round(self.file_size / (1024 * 1024), 2)