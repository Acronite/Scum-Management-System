from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q, Avg
import json
import psutil
import subprocess
import os
import signal
from datetime import datetime, timedelta

from .models import GameServer, ServerMetrics, ServerLog, ServerCommand, ServerConfiguration, ServerBackup
from .services import ServerManager, ServerMonitor


@login_required(login_url='account-login')
def control_dashboard(request):
    """Main dashboard showing all servers and their status"""
    servers = GameServer.objects.all()
    
    # Get latest metrics for each server
    server_data = []
    for server in servers:
        latest_metrics = server.metrics.first()
        recent_logs = server.logs.filter(log_level__in=['error', 'critical'])[:5]
        
        server_info = {
            'server': server,
            'metrics': latest_metrics,
            'error_count': recent_logs.count(),
            'recent_logs': recent_logs,
        }
        server_data.append(server_info)
    
    # System metrics
    system_metrics = {
        'cpu_usage': psutil.cpu_percent(interval=1),
        'memory': psutil.virtual_memory(),
        'disk': psutil.disk_usage('/'),
        'uptime': datetime.now() - datetime.fromtimestamp(psutil.boot_time())
    }
    
    context = {
        'page_title': ' - Server Control Dashboard',
        'servers': server_data,
        'system_metrics': system_metrics,
        'total_servers': servers.count(),
        'running_servers': servers.filter(status='running').count(),
    }
    
    return render(request, 'servercontrol/dashboard.html', context)


@login_required(login_url='account-login')
def server_detail(request, server_id):
    """Detailed view of a specific server"""
    server = get_object_or_404(GameServer, id=server_id)
    
    # Get recent metrics for charts (last 24 hours)
    since = timezone.now() - timedelta(hours=24)
    metrics = server.metrics.filter(timestamp__gte=since).order_by('timestamp')
    
    # Get recent logs
    logs = server.logs.all()[:100]
    
    # Get recent commands
    commands = server.commands.all()[:20]
    
    # Get configurations
    configurations = server.configurations.filter(is_active=True)
    
    context = {
        'page_title': f' - {server.name}',
        'server': server,
        'metrics': list(metrics.values()),
        'logs': logs,
        'commands': commands,
        'configurations': configurations,
    }
    
    return render(request, 'servercontrol/server_detail.html', context)


@login_required(login_url='account-login')
@require_http_methods(["POST"])
def server_action(request, server_id):
    """Handle server actions (start, stop, restart)"""
    server = get_object_or_404(GameServer, id=server_id)
    action = request.POST.get('action')
    
    server_manager = ServerManager(server)
    
    try:
        if action == 'start':
            result = server_manager.start_server()
            ServerLog.objects.create(
                server=server,
                message=f"Server start initiated by {request.user.username}",
                log_level='info',
                source='control_panel'
            )
            
        elif action == 'stop':
            result = server_manager.stop_server()
            ServerLog.objects.create(
                server=server,
                message=f"Server stop initiated by {request.user.username}",
                log_level='info',
                source='control_panel'
            )
            
        elif action == 'restart':
            result = server_manager.restart_server()
            ServerLog.objects.create(
                server=server,
                message=f"Server restart initiated by {request.user.username}",
                log_level='info',
                source='control_panel'
            )
            
        elif action == 'kill':
            result = server_manager.force_stop_server()
            ServerLog.objects.create(
                server=server,
                message=f"Server force stop initiated by {request.user.username}",
                log_level='warning',
                source='control_panel'
            )
        else:
            return JsonResponse({'success': False, 'error': 'Invalid action'})
        
        if result['success']:
            messages.success(request, result['message'])
        else:
            messages.error(request, result['message'])
            
        return JsonResponse(result)
        
    except Exception as e:
        error_msg = f"Error executing {action}: {str(e)}"
        ServerLog.objects.create(
            server=server,
            message=error_msg,
            log_level='error',
            source='control_panel'
        )
        return JsonResponse({'success': False, 'error': error_msg})


@login_required(login_url='account-login')
@require_http_methods(["POST"])
def execute_command(request, server_id):
    """Execute a command on the server via RCON or system"""
    server = get_object_or_404(GameServer, id=server_id)
    command = request.POST.get('command', '').strip()
    command_type = request.POST.get('type', 'rcon')
    
    if not command:
        return JsonResponse({'success': False, 'error': 'Command cannot be empty'})
    
    # Create command record
    cmd_record = ServerCommand.objects.create(
        server=server,
        command=command,
        command_type=command_type,
        executed_by=request.user,
        status='pending'
    )
    
    server_manager = ServerManager(server)
    
    try:
        cmd_record.status = 'executing'
        cmd_record.executed_at = timezone.now()
        cmd_record.save()
        
        if command_type == 'rcon':
            result = server_manager.execute_rcon_command(command)
        else:
            result = server_manager.execute_system_command(command)
        
        cmd_record.output = result.get('output', '')
        cmd_record.error_message = result.get('error', '')
        cmd_record.status = 'completed' if result['success'] else 'failed'
        cmd_record.completed_at = timezone.now()
        cmd_record.save()
        
        # Log the command execution
        ServerLog.objects.create(
            server=server,
            message=f"Command executed by {request.user.username}: {command}",
            log_level='info' if result['success'] else 'error',
            source='rcon' if command_type == 'rcon' else 'system'
        )
        
        return JsonResponse(result)
        
    except Exception as e:
        cmd_record.status = 'failed'
        cmd_record.error_message = str(e)
        cmd_record.completed_at = timezone.now()
        cmd_record.save()
        
        return JsonResponse({'success': False, 'error': str(e)})


@login_required(login_url='account-login')
def server_logs(request, server_id):
    """View and filter server logs"""
    server = get_object_or_404(GameServer, id=server_id)
    
    logs = server.logs.all()
    
    # Filtering
    log_level = request.GET.get('level')
    search = request.GET.get('search')
    source = request.GET.get('source')
    
    if log_level:
        logs = logs.filter(log_level=log_level)
    
    if search:
        logs = logs.filter(message__icontains=search)
    
    if source:
        logs = logs.filter(source=source)
    
    # Pagination
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': f' - {server.name} Logs',
        'server': server,
        'logs': page_obj,
        'log_levels': ServerLog.LOG_LEVEL_CHOICES,
        'sources': ServerLog.objects.filter(server=server).values_list('source', flat=True).distinct(),
        'current_filters': {
            'level': log_level,
            'search': search,
            'source': source,
        }
    }
    
    return render(request, 'servercontrol/server_logs.html', context)


@login_required(login_url='account-login')
def server_config(request, server_id):
    """View and edit server configurations"""
    server = get_object_or_404(GameServer, id=server_id)
    configurations = server.configurations.filter(is_active=True)
    
    context = {
        'page_title': f' - {server.name} Configuration',
        'server': server,
        'configurations': configurations,
    }
    
    return render(request, 'servercontrol/server_config.html', context)


@login_required(login_url='account-login')
@require_http_methods(["POST"])
def save_config(request, server_id, config_id):
    """Save configuration file changes"""
    server = get_object_or_404(GameServer, id=server_id)
    config = get_object_or_404(ServerConfiguration, id=config_id, server=server)
    
    new_content = request.POST.get('content', '')
    
    try:
        # Backup current configuration if enabled
        if config.backup_on_change:
            backup_name = f"{config.config_name}_backup_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
            ServerBackup.objects.create(
                server=server,
                backup_name=backup_name,
                backup_type='config',
                file_path=config.file_path,
                file_size=len(config.config_content.encode('utf-8')),
                created_by=request.user
            )
        
        # Save new content
        config.config_content = new_content
        config.modified_by = request.user
        config.save()
        
        # Write to actual file
        with open(config.file_path, 'w') as f:
            f.write(new_content)
        
        ServerLog.objects.create(
            server=server,
            message=f"Configuration {config.config_name} updated by {request.user.username}",
            log_level='info',
            source='control_panel'
        )
        
        return JsonResponse({'success': True, 'message': 'Configuration saved successfully'})
        
    except Exception as e:
        ServerLog.objects.create(
            server=server,
            message=f"Error saving configuration {config.config_name}: {str(e)}",
            log_level='error',
            source='control_panel'
        )
        return JsonResponse({'success': False, 'error': str(e)})


@login_required(login_url='account-login')
def api_server_status(request, server_id):
    """API endpoint for real-time server status"""
    server = get_object_or_404(GameServer, id=server_id)
    
    # Get latest metrics
    latest_metrics = server.metrics.first()
    
    # Check if process is actually running
    is_running = False
    if server.process_id:
        try:
            os.kill(server.process_id, 0)
            is_running = True
        except OSError:
            # Process not found, update server status
            server.status = 'stopped'
            server.process_id = None
            server.save()
    
    data = {
        'status': server.status,
        'is_running': is_running,
        'player_count': latest_metrics.player_count if latest_metrics else 0,
        'max_players': latest_metrics.max_players if latest_metrics else 0,
        'uptime_minutes': latest_metrics.uptime_minutes if latest_metrics else 0,
        'cpu_usage': latest_metrics.cpu_usage if latest_metrics else 0,
        'memory_usage': latest_metrics.memory_usage if latest_metrics else 0,
        'memory_percentage': latest_metrics.memory_percentage if latest_metrics else 0,
        'last_updated': latest_metrics.timestamp.isoformat() if latest_metrics else None,
    }
    
    return JsonResponse(data)


@login_required(login_url='account-login')
def api_recent_logs(request, server_id):
    """API endpoint for recent log entries"""
    server = get_object_or_404(GameServer, id=server_id)
    
    # Get logs from the last minute
    since = timezone.now() - timedelta(minutes=1)
    logs = server.logs.filter(timestamp__gte=since).order_by('-timestamp')
    
    log_data = []
    for log in logs:
        log_data.append({
            'timestamp': log.timestamp.isoformat(),
            'level': log.log_level,
            'message': log.message,
            'source': log.source,
        })
    
    return JsonResponse({'logs': log_data})


@login_required(login_url='account-login')
def create_backup(request, server_id):
    """Create a server backup"""
    server = get_object_or_404(GameServer, id=server_id)
    
    if request.method == 'POST':
        backup_type = request.POST.get('backup_type', 'full')
        backup_name = request.POST.get('backup_name', f"{server.name}_backup_{timezone.now().strftime('%Y%m%d_%H%M%S')}")
        
        try:
            server_manager = ServerManager(server)
            result = server_manager.create_backup(backup_type, backup_name, request.user)
            
            if result['success']:
                messages.success(request, result['message'])
            else:
                messages.error(request, result['message'])
                
        except Exception as e:
            messages.error(request, f"Error creating backup: {str(e)}")
    
    return redirect('server_detail', server_id=server_id)


@login_required(login_url='account-login')
def server_metrics_api(request, server_id):
    """API endpoint for server metrics chart data"""
    server = get_object_or_404(GameServer, id=server_id)
    
    # Get metrics for the last specified hours (default 24)
    hours = int(request.GET.get('hours', 24))
    since = timezone.now() - timedelta(hours=hours)
    
    metrics = server.metrics.filter(timestamp__gte=since).order_by('timestamp')
    
    data = {
        'timestamps': [m.timestamp.isoformat() for m in metrics],
        'cpu_usage': [m.cpu_usage or 0 for m in metrics],
        'memory_percentage': [m.memory_percentage or 0 for m in metrics],
        'player_count': [m.player_count for m in metrics],
        'network_in': [m.network_in or 0 for m in metrics],
        'network_out': [m.network_out or 0 for m in metrics],
    }
    
    return JsonResponse(data)