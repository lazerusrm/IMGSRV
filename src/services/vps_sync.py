"""
VPS synchronization service for Image Sequence Server.

Handles RSYNC synchronization of generated GIFs to public-facing VPS server.
"""

import asyncio
import subprocess
import os
from pathlib import Path
from typing import Optional
import structlog

logger = structlog.get_logger(__name__)


class VPSSyncError(Exception):
    """VPS synchronization errors."""
    pass


class VPSSynchronizer:
    """Handles synchronization of content to VPS server."""
    
    def __init__(self, settings):
        self.settings = settings
        self.enabled = settings.vps_enabled
        
        if self.enabled:
            self._validate_config()
            self._setup_ssh_key()
        
        logger.info("VPS synchronizer initialized", enabled=self.enabled)
    
    def _validate_config(self):
        """Validate VPS configuration."""
        required_fields = ['vps_host', 'vps_user', 'vps_remote_path']
        
        for field in required_fields:
            if not getattr(self.settings, field):
                raise VPSSyncError(f"VPS configuration missing: {field}")
        
        logger.info("VPS configuration validated")
    
    def _setup_ssh_key(self):
        """Setup SSH key for VPS access."""
        ssh_key_path = Path(self.settings.vps_ssh_key_path)
        ssh_dir = ssh_key_path.parent
        
        # Create .ssh directory if it doesn't exist
        ssh_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        
        # Check if SSH key exists
        if not ssh_key_path.exists():
            logger.warning("SSH key not found", path=str(ssh_key_path))
            logger.info("Please ensure SSH key is placed at the configured path")
        
        # Set proper permissions
        if ssh_key_path.exists():
            ssh_key_path.chmod(0o600)
            logger.info("SSH key permissions set")
    
    async def sync_to_vps(self, local_path: Path) -> bool:
        """
        Synchronize local content to VPS server.
        
        Args:
            local_path: Local path to sync (sequences directory)
            
        Returns:
            True if sync successful, False otherwise
        """
        if not self.enabled:
            logger.debug("VPS sync disabled, skipping")
            return True
        
        try:
            # Build RSYNC command
            cmd = self._build_rsync_command(local_path)
            
            logger.info("Starting VPS synchronization", 
                       local_path=str(local_path),
                       remote_path=self.settings.vps_remote_path)
            
            # Run RSYNC command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=60)
            
            if process.returncode == 0:
                logger.info("VPS synchronization completed successfully")
                
                # Fix permissions on VPS after sync
                await self._fix_vps_permissions()
                
                # Ensure index.html exists on VPS
                await self._ensure_index_html()
                
                return True
            else:
                error_msg = stderr.decode('utf-8') if stderr else "Unknown RSYNC error"
                logger.error("VPS synchronization failed", 
                           returncode=process.returncode,
                           error=error_msg)
                return False
                
        except asyncio.TimeoutError:
            logger.error("VPS synchronization timeout")
            return False
        except Exception as e:
            logger.error("VPS synchronization error", error=str(e))
            return False
    
    def _build_rsync_command(self, local_path: Path) -> list:
        """Build RSYNC command with proper options."""
        cmd = [
            'rsync',
            *self.settings.vps_rsync_options.split(),
            '-e', f'ssh -p {self.settings.vps_port} -i {self.settings.vps_ssh_key_path} -o StrictHostKeyChecking=no',
            f'{local_path}/',
            f'{self.settings.vps_user}@{self.settings.vps_host}:{self.settings.vps_remote_path}/'
        ]
        
        logger.debug("RSYNC command built", cmd=' '.join(cmd))
        return cmd
    
    async def _fix_vps_permissions(self):
        """Fix file permissions on VPS after sync."""
        try:
            # Try multiple web server users in order of preference
            web_users = ['www-data', 'nginx', 'apache', 'httpd']
            
            for web_user in web_users:
                cmd = [
                    'ssh',
                    '-p', str(self.settings.vps_port),
                    '-i', self.settings.vps_ssh_key_path,
                    '-o', 'StrictHostKeyChecking=no',
                    '-o', 'ConnectTimeout=10',
                    f'{self.settings.vps_user}@{self.settings.vps_host}',
                    f'id {web_user} >/dev/null 2>&1 && chown -R {web_user}:{web_user} {self.settings.vps_remote_path} && chmod -R 755 {self.settings.vps_remote_path} && echo "SUCCESS:{web_user}" || echo "FAILED:{web_user}"'
                ]
                
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=15)
                
                if process.returncode == 0:
                    output = stdout.decode('utf-8').strip()
                    if 'SUCCESS:' in output:
                        web_user_used = output.split('SUCCESS:')[1]
                        logger.info("VPS permissions fixed successfully", web_user=web_user_used)
                        return
                    else:
                        logger.debug(f"Web user {web_user} not found, trying next")
                        continue
                else:
                    error_msg = stderr.decode('utf-8') if stderr else "Unknown permission error"
                    logger.debug(f"Failed to fix permissions with {web_user}", error=error_msg)
                    continue
            
            # If all web users failed, try generic approach
            logger.warning("All web user attempts failed, trying generic permission fix")
            cmd = [
                'ssh',
                '-p', str(self.settings.vps_port),
                '-i', self.settings.vps_ssh_key_path,
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'ConnectTimeout=10',
                f'{self.settings.vps_user}@{self.settings.vps_host}',
                f'chmod -R 755 {self.settings.vps_remote_path} && ls -la {self.settings.vps_remote_path}'
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=15)
            
            if process.returncode == 0:
                logger.info("VPS permissions fixed with generic approach")
                logger.debug("VPS directory listing", output=stdout.decode('utf-8'))
            else:
                error_msg = stderr.decode('utf-8') if stderr else "Unknown permission error"
                logger.error("All VPS permission fix attempts failed", error=error_msg)
                
        except asyncio.TimeoutError:
            logger.warning("VPS permission fix timeout")
        except Exception as e:
            logger.warning("VPS permission fix error", error=str(e))
    
    async def _ensure_index_html(self):
        """Ensure index.html exists on VPS with latest GIF."""
        try:
            # Get the latest GIF filename
            cmd = [
                'ssh',
                '-p', str(self.settings.vps_port),
                '-i', self.settings.vps_ssh_key_path,
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'ConnectTimeout=10',
                f'{self.settings.vps_user}@{self.settings.vps_host}',
                f'ls -t {self.settings.vps_remote_path}/sequence_*.gif 2>/dev/null | head -1 | xargs basename 2>/dev/null || echo "no_gif"'
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=15)
            
            if process.returncode == 0:
                latest_gif = stdout.decode('utf-8').strip()
                
                if latest_gif != "no_gif":
                    # Create index.html with the latest GIF
                    html_content = f'''<!DOCTYPE html>
<html>
<head>
    <title>Woodland Hills City Center - Snow Load Monitoring</title>
    <meta http-equiv="refresh" content="300">
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f0f0f0;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2em;
        }}
        .header h2 {{
            margin: 5px 0 0 0;
            font-size: 1.2em;
            opacity: 0.9;
        }}
        .content {{
            padding: 20px;
            text-align: center;
        }}
        .camera-image {{
            max-width: 100%;
            height: auto;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .info {{
            margin-top: 20px;
            color: #666;
        }}
        .refresh-info {{
            font-size: 0.9em;
            color: #888;
            margin-top: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Woodland Hills City Center</h1>
            <h2>Snow Load Monitoring</h2>
        </div>
        <div class="content">
            <img src="{latest_gif}" alt="Snow Load Monitoring GIF" class="camera-image">
            <div class="info">
                <p>GIF updates every 5 minutes</p>
                <div class="refresh-info">
                    Page refreshes automatically every 5 minutes
                </div>
            </div>
        </div>
    </div>
</body>
</html>'''
                    
                    # Write index.html to VPS
                    cmd = [
                        'ssh',
                        '-p', str(self.settings.vps_port),
                        '-i', self.settings.vps_ssh_key_path,
                        '-o', 'StrictHostKeyChecking=no',
                        '-o', 'ConnectTimeout=10',
                        f'{self.settings.vps_user}@{self.settings.vps_host}',
                        f'cat > {self.settings.vps_remote_path}/index.html'
                    ]
                    
                    process = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdin=asyncio.subprocess.PIPE,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(input=html_content.encode('utf-8')), 
                        timeout=15
                    )
                    
                    if process.returncode == 0:
                        logger.info("index.html updated on VPS", gif_file=latest_gif)
                    else:
                        logger.warning("Failed to update index.html on VPS")
                else:
                    logger.warning("No GIF files found on VPS to create index.html")
            else:
                logger.warning("Failed to get latest GIF filename from VPS")
                
        except asyncio.TimeoutError:
            logger.warning("index.html update timeout")
        except Exception as e:
            logger.warning("index.html update error", error=str(e))
    
    async def test_connection(self) -> bool:
        """Test VPS connection."""
        if not self.enabled:
            return True
        
        try:
            cmd = [
                'ssh',
                '-p', str(self.settings.vps_port),
                '-i', self.settings.vps_ssh_key_path,
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'ConnectTimeout=10',
                f'{self.settings.vps_user}@{self.settings.vps_host}',
                'echo "VPS connection test successful"'
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=15)
            
            if process.returncode == 0:
                logger.info("VPS connection test successful")
                return True
            else:
                error_msg = stderr.decode('utf-8') if stderr else "Unknown SSH error"
                logger.warning("VPS connection test failed", error=error_msg)
                return False
                
        except asyncio.TimeoutError:
            logger.warning("VPS connection test timeout")
            return False
        except Exception as e:
            logger.warning("VPS connection test error", error=str(e))
            return False
    
    def get_sync_status(self) -> dict:
        """Get VPS synchronization status."""
        return {
            "enabled": self.enabled,
            "host": self.settings.vps_host if self.enabled else None,
            "user": self.settings.vps_user if self.enabled else None,
            "remote_path": self.settings.vps_remote_path if self.enabled else None,
            "ssh_key_exists": Path(self.settings.vps_ssh_key_path).exists() if self.enabled else None
        }
