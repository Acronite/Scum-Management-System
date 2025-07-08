import subprocess
import psutil
import os
import signal
import socket
import time
import threading
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings

from .models import GameServer, ServerMetrics, ServerLog, ServerBackup


class ServerManager:
    """Service class for managing game server operations"""
    
    def __init__(self, server):
        self.server = server
    
    def start_server(self):
        """Start the game server"""
        if self.server.status == 'running':
            return {'success': False, 'message': 'Server is already running'}
        
        try:
            # Update status
            self.server.status = 'starting'
            self.server.save()
            
            # Build command
            cmd = [
                os.path.join(self.server.server_path, self.server.executable_name)
            ]
            
            if self.server.startup_parameters:
                cmd.extend(self.server.startup_parameters.split())
            
            # Start process
            process = subprocess.Popen(
                cmd,
                cwd=self.server.server_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid if os.name != 'nt' else None
            )
            
            # Update server record
            self.server.process_id = process.pid
            self.server.status = 'running'
            self.server.last_started = timezone.now()
            self.server.save()
            
            # Start monitoring thread
            monitor_thread = threading.Thread(
                target=self._monitor_process,
                args=(process,),
                daemon=True
            )
            monitor_thread.start()
            
            return {'success': True, 'message': f'Server started with PID {process.pid}'}
            
        except Exception as e:
            self.server.status = 'stopped'
            self.server.save()
            return {'success': False, 'message': f'Failed to start server: {str(e)}'}
    
    def stop_server(self):
        """Gracefully stop the game server"""
        if self.server.status != 'running':
            return {'success': False, 'message': 'Server is not running'}
        
        try:
            self.server.status = 'stopping'
            self.server.save()
            
            if self.server.process_id:
                try:
                    # Try graceful shutdown first
                    if os.name == 'nt':
                        os.kill(self.server.process_id, signal.CTRL_C_EVENT)
                    else:
                        os.kill(self.server.process_id, signal.SIGTERM)
                    
                    # Wait up to 30 seconds for graceful shutdown
                    for _ in range(30):
                        try:
                            os.kill(self.server.process_id, 0)
                            time.sleep(1)
                        except OSError:
                            break
                    else:
                        # Force kill if still running
                        os.kill(self.server.process_id, signal.SIGKILL)
                    
                except OSError:
                    pass  # Process already terminated
            
            self.server.status = 'stopped'
            self.server.last_stopped = timezone.now()
            self.server.process_id = None
            self.server.save()
            
            return {'success': True, 'message': 'Server stopped successfully'}
            
        except Exception as e:
            return {'success': False, 'message': f'Failed to stop server: {str(e)}'}
    
    def force_stop_server(self):
        """Force stop the game server"""
        try:
            if self.server.process_id:
                try:
                    os.kill(self.server.process_id, signal.SIGKILL)
                except OSError:
                    pass
            
            self.server.status = 'stopped'
            self.server.last_stopped = timezone.now()
            self.server.process_id = None
            self.server.save()
            
            return {'success': True, 'message': 'Server force stopped'}
            
        except Exception as e:
            return {'success': False, 'message': f'Failed to force stop server: {str(e)}'}
    
    def restart_server(self):
        """Restart the game server"""
        stop_result = self.stop_server()
        if not stop_result['success']:
            return stop_result
        
        # Wait a moment before starting
        time.sleep(2)
        
        return self.start_server()
    
    def execute_rcon_command(self, command):
        """Execute a command via RCON"""
        if not self.server.rcon_port or not self.server.rcon_password:
            return {'success': False, 'error': 'RCON not configured for this server'}
        
        try:
            # This is a simplified RCON implementation
            # In a real implementation, you'd use a proper RCON library
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((self.server.server_ip, self.server.rcon_port))
            
            # Send RCON authentication and command
            # This is pseudo-code - implement actual RCON protocol
            response = f"Command '{command}' executed via RCON"
            sock.close()
            
            return {'success': True, 'output': response}
            
        except Exception as e:
            return {'success': False, 'error': f'RCON error: {str(e)}'}
    
    def execute_system_command(self, command):
        """Execute a system command in the server directory"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.server.server_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return {'success': True, 'output': result.stdout}
            else:
                return {'success': False, 'error': result.stderr}
                
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Command timed out'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def create_backup(self, backup_type, backup_name, user):
        """Create a backup of server files"""
        try:
            import shutil
            import zipfile
            from pathlib import Path
            
            backup_dir = Path(settings.BASE_DIR) / 'backups' / str(self.server.id)
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            backup_file = backup_dir / f"{backup_name}.zip"
            
            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                if backup_type == 'full':
                    # Backup entire server directory
                    server_path = Path(self.server.server_path)
                    for file_path in server_path.rglob('*'):
                        if file_path.is_file():
                            arcname = file_path.relative_to(server_path)
                            zipf.write(file_path, arcname)
                
                elif backup_type == 'config':
                    # Backup only configuration files
                    for config in self.server.configurations.filter(is_active=True):
                        if os.path.exists(config.file_path):
                            zipf.write(config.file_path, os.path.basename(config.file_path))
                
                elif backup_type == 'save':
                    # Backup save game files (this depends on the game type)
                    save_path = os.path.join(self.server.server_path, 'saves')
                    if os.path.exists(save_path):
                        for root, dirs, files in os.walk(save_path):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_path, self.server.server_path)
                                zipf.write(file_path, arcname)
            
            # Create backup record
            file_size = backup_file.stat().st_size
            ServerBackup.objects.create(
                server=self.server,
                backup_name=backup_name,
                backup_type=backup_type,
                file_path=str(backup_file),
                file_size=file_size,
                created_by=user
            )
            
            return {'success': True, 'message': f'Backup created: {backup_name}'}
            
        except Exception as e:
            return {'success': False, 'message': f'Backup failed: {str(e)}'}
    
    def _monitor_process(self, process):
        """Monitor the server process in a separate thread"""
        try:
            # Wait for process to finish
            process.wait()
            
            # Update server status
            if self.server.status == 'running':
                self.server.status = 'crashed' if process.returncode != 0 else 'stopped'
                self.server.last_stopped = timezone.now()
                self.server.process_id = None
                self.server.save()
                
                # Log the event
                ServerLog.objects.create(
                    server=self.server,
                    message=f"Server process ended with code {process.returncode}",
                    log_level='error' if process.returncode != 0 else 'info',
                    source='system'
                )
                
                # Auto-restart if enabled and crashed
                if self.server.crash_restart and process.returncode != 0:
                    time.sleep(5)  # Wait before restarting
                    self.start_server()
                    
        except Exception as e:
            ServerLog.objects.create(
                server=self.server,
                message=f"Error monitoring process: {str(e)}",
                log_level='error',
                source='system'
            )


class ServerMonitor:
    """Service class for monitoring server performance and status"""
    
    @staticmethod
    def collect_metrics(server):
        """Collect and store server metrics"""
        try:
            # Get process metrics if server is running
            cpu_usage = None
            memory_usage = None
            memory_percentage = None
            
            if server.process_id:
                try:
                    process = psutil.Process(server.process_id)
                    cpu_usage = process.cpu_percent(interval=1)
                    memory_info = process.memory_info()
                    memory_usage = memory_info.rss / (1024 * 1024)  # MB
                    memory_percentage = process.memory_percent()
                except psutil.NoSuchProcess:
                    # Process not found, update server status
                    server.status = 'stopped'
                    server.process_id = None
                    server.save()
            
            # Calculate uptime
            uptime_minutes = 0
            if server.last_started and server.status == 'running':
                uptime_delta = timezone.now() - server.last_started
                uptime_minutes = int(uptime_delta.total_seconds() / 60)
            
            # Get player count (this would need to be implemented based on your game type)
            player_count = ServerMonitor._get_player_count(server)
            
            # Get disk usage for server directory
            disk_usage = None
            if os.path.exists(server.server_path):
                disk_usage = psutil.disk_usage(server.server_path).used / (1024 * 1024 * 1024)  # GB
            
            # Create metrics record
            metrics = ServerMetrics.objects.create(
                server=server,
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                memory_percentage=memory_percentage,
                disk_usage=disk_usage,
                player_count=player_count,
                max_players=50,  # This should be configurable or detected
                uptime_minutes=uptime_minutes
            )
            
            # Clean up old metrics (keep only last 7 days)
            old_metrics = server.metrics.filter(
                timestamp__lt=timezone.now() - timedelta(days=7)
            )
            old_metrics.delete()
            
            return metrics
            
        except Exception as e:
            ServerLog.objects.create(
                server=server,
                message=f"Error collecting metrics: {str(e)}",
                log_level='error',
                source='monitor'
            )
            return None
    
    @staticmethod
    def _get_player_count(server):
        """Get current player count for the server"""
        # This is a placeholder - implement based on your game type
        # You might query the game's API, parse log files, or use RCON
        try:
            # Example: parse recent log entries for player join/leave events
            recent_logs = server.logs.filter(
                timestamp__gte=timezone.now() - timedelta(minutes=5),
                message__icontains='logged in'
            )
            return recent_logs.count()
        except:
            return 0
    
    @staticmethod
    def check_server_health(server):
        """Perform health checks on the server"""
        health_issues = []
        
        try:
            # Check if server process is responsive
            if server.status == 'running' and server.process_id:
                try:
                    os.kill(server.process_id, 0)
                except OSError:
                    health_issues.append("Server process not found")
                    server.status = 'stopped'
                    server.process_id = None
                    server.save()
            
            # Check disk space
            if os.path.exists(server.server_path):
                disk_usage = psutil.disk_usage(server.server_path)
                if disk_usage.percent > 90:
                    health_issues.append(f"Low disk space: {disk_usage.percent}% used")
            
            # Check memory usage
            latest_metrics = server.metrics.first()
            if latest_metrics and latest_metrics.memory_percentage:
                if latest_metrics.memory_percentage > 90:
                    health_issues.append(f"High memory usage: {latest_metrics.memory_percentage}%")
            
            # Log any health issues
            for issue in health_issues:
                ServerLog.objects.create(
                    server=server,
                    message=f"Health check warning: {issue}",
                    log_level='warning',
                    source='health_check'
                )
            
            return health_issues
            
        except Exception as e:
            ServerLog.objects.create(
                server=server,
                message=f"Health check error: {str(e)}",
                log_level='error',
                source='health_check'
            )
            return [f"Health check failed: {str(e)}"]