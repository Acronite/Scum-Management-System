# Game Server Control Panel

A comprehensive Django-based control panel for managing game servers with real-time monitoring, performance metrics, and administrative tools.

## Features

### 🎮 Server Management
- **Start/Stop/Restart** servers with one click
- **Real-time status monitoring** with automatic updates
- **Process monitoring** and health checks
- **Crash detection** and auto-restart capabilities
- **Force stop** for unresponsive servers

### 📊 Performance Monitoring
- **Real-time metrics** collection (CPU, Memory, Network)
- **Interactive charts** with historical data (24h, 7d, 30d views)
- **Player count tracking** and statistics
- **System resource monitoring**
- **Automated health checks** and alerts

### 🔧 Server Console
- **RCON integration** for remote command execution
- **Interactive console** with command history
- **Quick action buttons** for common commands
- **Real-time command output** and error handling

### 📝 Logging & Auditing
- **Comprehensive logging** system with multiple levels
- **Real-time log streaming** in the web interface
- **Log filtering** by level, source, and content
- **Command execution tracking** with full audit trail
- **Automated log rotation** and cleanup

### ⚙️ Configuration Management
- **Web-based config editor** with syntax highlighting
- **Automatic backup** before changes
- **Version control** for configuration files
- **Hot-reload** configuration without server restart

### 💾 Backup & Recovery
- **Automated backups** on schedule
- **Full server backups** or selective (config/saves only)
- **One-click backup creation** from web interface
- **Backup management** and restoration tools

### 👥 Player Management
- **Player tracking** and statistics
- **Squad/Team management** with existing player system
- **Donation tracking** and management
- **Incident/Case management** for violations

## Installation

### Prerequisites
- Python 3.8+
- Django 3.1.2+
- PostgreSQL/MySQL (optional, SQLite works for development)

### Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

3. **Create a superuser:**
   ```bash
   python manage.py createsuperuser
   ```

4. **Collect static files:**
   ```bash
   python manage.py collectstatic
   ```

5. **Start the development server:**
   ```bash
   python manage.py runserver
   ```

## Configuration

### Adding a New Game Server

1. **Via Django Admin:**
   - Go to `/admin/servercontrol/gameserver/`
   - Click "Add Game Server"
   - Fill in the required information:
     - **Name:** Display name for your server
     - **Server IP/Port:** Network address and port
     - **Server Path:** Full path to server executable directory
     - **Executable Name:** Name of the server executable file
     - **Startup Parameters:** Command-line arguments for the server
     - **RCON Settings:** For remote console access (optional)

2. **Required Fields:**
   - `name`: Server display name
   - `server_ip`: Server IP address
   - `server_port`: Game server port
   - `query_port`: Query/monitoring port
   - `server_path`: Full path to server directory
   - `executable_name`: Server executable filename

3. **Optional Configuration:**
   - `rcon_port` and `rcon_password`: For RCON functionality
   - `startup_parameters`: Command-line arguments
   - `auto_restart`: Enable automatic restart on crash
   - `auto_restart_time`: Scheduled restart time

### Server Configuration Files

Add configuration files through the admin interface:
- Go to "Server configurations" in the admin
- Add each config file with its path and content
- Enable "Backup on change" for automatic versioning

## Usage

### Web Interface

1. **Dashboard** (`/control/`)
   - Overview of all servers and system metrics
   - Quick start/stop/restart controls
   - Real-time status updates

2. **Server Detail** (`/control/server/{id}/`)
   - Detailed server management interface
   - Performance charts and metrics
   - Interactive console for RCON commands
   - Real-time log streaming

3. **Server Logs** (`/control/server/{id}/logs/`)
   - Full log viewer with filtering
   - Export capabilities
   - Search functionality

4. **Configuration** (`/control/server/{id}/config/`)
   - Web-based configuration editor
   - Syntax highlighting for config files
   - Automatic backup before changes

### Command-Line Management

**Monitor all servers:**
```bash
# Run continuous monitoring (default 60s interval)
python manage.py monitor_servers

# Monitor once
python manage.py monitor_servers --once

# Custom interval (30 seconds)
python manage.py monitor_servers --interval 30
```

**Control individual servers:**
```bash
# Check server status
python manage.py server_control 1 status

# Start server
python manage.py server_control 1 start

# Stop server
python manage.py server_control 1 stop

# Restart server
python manage.py server_control 1 restart
```

### Automation

**Set up automatic monitoring:**
```bash
# Add to crontab for system startup
@reboot cd /path/to/project && python manage.py monitor_servers

# Or use systemd service (recommended)
```

**Systemd service example:**
```ini
[Unit]
Description=Game Server Monitor
After=network.target

[Service]
Type=simple
User=gameserver
WorkingDirectory=/path/to/project
ExecStart=/path/to/venv/bin/python manage.py monitor_servers
Restart=always

[Install]
WantedBy=multi-user.target
```

## API Endpoints

The control panel provides REST API endpoints for integration:

- `GET /control/api/server/{id}/status/` - Real-time server status
- `GET /control/api/server/{id}/logs/` - Recent log entries  
- `GET /control/api/server/{id}/metrics/` - Performance metrics data
- `POST /control/server/{id}/action/` - Server control actions
- `POST /control/server/{id}/command/` - Execute RCON commands

## Security Considerations

1. **Access Control:**
   - All views require authentication (`@login_required`)
   - Use Django's built-in user management
   - Consider implementing role-based permissions

2. **RCON Security:**
   - Store RCON passwords securely
   - Use HTTPS in production
   - Limit RCON access to trusted networks

3. **File System Access:**
   - Ensure proper file permissions on server directories
   - Validate all file paths to prevent directory traversal
   - Run server processes with limited privileges

4. **Network Security:**
   - Use firewall rules to restrict access to server ports
   - Consider VPN access for remote management
   - Monitor for unusual network activity

## Troubleshooting

### Common Issues

1. **Server won't start:**
   - Check executable path and permissions
   - Verify startup parameters
   - Check system resources (ports, memory)
   - Review server logs for errors

2. **RCON not working:**
   - Verify RCON port and password
   - Check firewall settings
   - Ensure game server has RCON enabled

3. **Metrics not updating:**
   - Ensure monitoring service is running
   - Check process permissions
   - Verify database connectivity

4. **Performance issues:**
   - Monitor system resources
   - Adjust monitoring intervals
   - Clean up old metrics data

### Log Locations

- **Django logs:** Check `DEBUG` setting and logging configuration
- **Server logs:** Stored in database and displayed in web interface
- **System logs:** `/var/log/` for systemd services

## Development

### Project Structure
```
servercontrol/
├── models.py          # Database models
├── views.py           # Web interface views
├── services.py        # Business logic and server management
├── admin.py          # Django admin configuration
├── urls.py           # URL routing
├── management/       # Django management commands
│   └── commands/
│       ├── monitor_servers.py
│       └── server_control.py
└── templates/        # HTML templates
    └── servercontrol/
        ├── dashboard.html
        └── server_detail.html
```

### Extending the System

**Add new game support:**
1. Extend `ServerManager` class for game-specific operations
2. Implement game-specific player count detection
3. Add custom RCON commands and parsing

**Custom metrics:**
1. Extend `ServerMetrics` model
2. Update `ServerMonitor.collect_metrics()`
3. Add new chart displays in templates

**Additional features:**
1. Plugin system for custom functionality
2. Webhook notifications for alerts
3. Mobile app API endpoints
4. Advanced analytics and reporting

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review existing GitHub issues
3. Create a new issue with detailed information
4. Include logs and system information

---

**Built with Django • Real-time monitoring • Production ready**