from django.core.management.base import BaseCommand, CommandError

from servercontrol.models import GameServer


class Command(BaseCommand):
    help = 'Start/stop/restart a specific game server'

    def add_arguments(self, parser):
        parser.add_argument('server_id', type=int, help='Server ID to control')
        parser.add_argument(
            'action',
            choices=['start', 'stop', 'restart', 'status'],
            help='Action to perform'
        )

    def handle(self, *args, **options):
        server_id = options['server_id']
        action = options['action']
        
        try:
            server = GameServer.objects.get(id=server_id)
        except GameServer.DoesNotExist:
            raise CommandError(f'Server with ID {server_id} does not exist')
        
        self.stdout.write(f'Performing {action} on server: {server.name}')
        
        from servercontrol.services import ServerManager
        manager = ServerManager(server)
        
        if action == 'start':
            result = manager.start_server()
        elif action == 'stop':
            result = manager.stop_server()
        elif action == 'restart':
            result = manager.restart_server()
        elif action == 'status':
            self.stdout.write(f'Server status: {server.get_status_display()}')
            if server.process_id:
                self.stdout.write(f'Process ID: {server.process_id}')
            if server.last_started:
                self.stdout.write(f'Last started: {server.last_started}')
            return
        
        if result['success']:
            self.stdout.write(
                self.style.SUCCESS(f'✓ {result["message"]}')
            )
        else:
            self.stdout.write(
                self.style.ERROR(f'✗ {result["message"]}')
            )