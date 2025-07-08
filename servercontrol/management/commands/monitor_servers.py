from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
import time
import logging

from servercontrol.models import GameServer
from servercontrol.services import ServerMonitor

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Continuously monitor all game servers and collect metrics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=60,
            help='Monitoring interval in seconds (default: 60)'
        )
        parser.add_argument(
            '--once',
            action='store_true',
            help='Run monitoring once instead of continuously'
        )

    def handle(self, *args, **options):
        interval = options['interval']
        run_once = options['once']
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Starting server monitoring (interval: {interval}s, once: {run_once})'
            )
        )
        
        if run_once:
            self.monitor_all_servers()
        else:
            self.continuous_monitoring(interval)

    def continuous_monitoring(self, interval):
        """Run continuous monitoring loop"""
        try:
            while True:
                start_time = time.time()
                
                self.monitor_all_servers()
                
                # Calculate sleep time to maintain consistent interval
                elapsed = time.time() - start_time
                sleep_time = max(0, interval - elapsed)
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Monitoring took {elapsed:.2f}s, longer than interval {interval}s'
                        )
                    )
                    
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS('Monitoring stopped by user'))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Monitoring error: {str(e)}')
            )
            raise

    def monitor_all_servers(self):
        """Monitor all configured servers"""
        servers = GameServer.objects.all()
        
        if not servers.exists():
            self.stdout.write(
                self.style.WARNING('No servers configured for monitoring')
            )
            return
        
        self.stdout.write(f'Monitoring {servers.count()} server(s)...')
        
        for server in servers:
            try:
                # Collect metrics
                metrics = ServerMonitor.collect_metrics(server)
                if metrics:
                    self.stdout.write(
                        f'✓ {server.name}: CPU {metrics.cpu_usage or "N/A"}%, '
                        f'Memory {metrics.memory_percentage or "N/A"}%, '
                        f'Players {metrics.player_count}'
                    )
                
                # Perform health checks
                health_issues = ServerMonitor.check_server_health(server)
                if health_issues:
                    self.stdout.write(
                        self.style.WARNING(
                            f'⚠ {server.name}: {len(health_issues)} health issue(s)'
                        )
                    )
                    for issue in health_issues:
                        self.stdout.write(f'  - {issue}')
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Error monitoring {server.name}: {str(e)}')
                )
                logger.exception(f'Error monitoring server {server.name}')
        
        self.stdout.write(f'Monitoring completed at {timezone.now()}')