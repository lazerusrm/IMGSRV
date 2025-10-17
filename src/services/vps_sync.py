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
