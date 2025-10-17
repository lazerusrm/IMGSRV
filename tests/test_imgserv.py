# Image Sequence Server - Test Suite

import asyncio
import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from src.config import Settings
from src.services.camera import ONVIFCamera, CameraError
from src.services.image_processor import ImageProcessor
from src.services.storage import StorageManager
from src.services.sequence_service import ImageSequenceService


class TestONVIFCamera:
    """Test ONVIF camera functionality."""
    
    @pytest.fixture
    def camera(self):
        return ONVIFCamera(
            ip="192.168.1.110",
            username="admin",
            password="123456"
        )
    
    @pytest.mark.asyncio
    async def test_camera_initialization(self, camera):
        """Test camera initialization."""
        assert camera.ip == "192.168.1.110"
        assert camera.username == "admin"
        assert camera.password == "123456"
        assert camera.snapshot_url == "http://192.168.1.110:80/snapshot.cgi"
    
    @pytest.mark.asyncio
    async def test_camera_info(self, camera):
        """Test camera info retrieval."""
        info = camera.get_camera_info()
        assert info["ip"] == "192.168.1.110"
        assert info["username"] == "admin"
        assert "password" not in info  # Security: password not in info
    
    @pytest.mark.asyncio
    async def test_capture_snapshot_success(self, camera):
        """Test successful snapshot capture."""
        mock_image_data = b"fake_image_data"
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.read = AsyncMock(return_value=mock_image_data)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            with patch('PIL.Image.open') as mock_pil:
                mock_img = MagicMock()
                mock_img.verify.return_value = None
                mock_pil.return_value.__enter__.return_value = mock_img
                
                image_data, timestamp = await camera.capture_snapshot()
                
                assert image_data == mock_image_data
                assert timestamp is not None
    
    @pytest.mark.asyncio
    async def test_capture_snapshot_failure(self, camera):
        """Test snapshot capture failure."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 404
            mock_get.return_value.__aenter__.return_value = mock_response
            
            with pytest.raises(CameraError):
                await camera.capture_snapshot()


class TestImageProcessor:
    """Test image processing functionality."""
    
    @pytest.fixture
    def processor(self):
        return ImageProcessor()
    
    @pytest.mark.asyncio
    async def test_add_timestamp_overlay(self, processor):
        """Test timestamp overlay addition."""
        # Create a simple test image
        from PIL import Image
        import io
        
        test_image = Image.new('RGB', (100, 100), color='red')
        image_bytes = io.BytesIO()
        test_image.save(image_bytes, format='JPEG')
        image_data = image_bytes.getvalue()
        
        from datetime import datetime
        timestamp = datetime.now()
        
        result = await processor.add_timestamp_overlay(image_data, timestamp)
        
        assert result != image_data  # Should be modified
        assert len(result) > 0  # Should not be empty
    
    @pytest.mark.asyncio
    async def test_create_image_sequence(self, processor):
        """Test image sequence creation."""
        from PIL import Image
        import io
        from datetime import datetime
        
        # Create test images
        images = []
        for i in range(3):
            test_image = Image.new('RGB', (100, 100), color=f'hsl({i*120}, 50%, 50%)')
            image_bytes = io.BytesIO()
            test_image.save(image_bytes, format='JPEG')
            images.append((image_bytes.getvalue(), datetime.now()))
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_sequence.gif"
            
            result_path = await processor.create_image_sequence(
                images, output_path, duration_seconds=2
            )
            
            assert result_path == output_path
            assert output_path.exists()
            assert output_path.stat().st_size > 0


class TestStorageManager:
    """Test storage management functionality."""
    
    @pytest.fixture
    def storage_manager(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            return StorageManager(
                images_dir=temp_path / "images",
                sequences_dir=temp_path / "sequences"
            )
    
    @pytest.mark.asyncio
    async def test_save_image(self, storage_manager):
        """Test image saving."""
        from datetime import datetime
        
        test_data = b"test_image_data"
        timestamp = datetime.now()
        
        result_path = await storage_manager.save_image(test_data, timestamp)
        
        assert result_path.exists()
        assert result_path.read_bytes() == test_data
    
    @pytest.mark.asyncio
    async def test_get_recent_images(self, storage_manager):
        """Test recent images retrieval."""
        from datetime import datetime
        
        # Save some test images
        for i in range(3):
            test_data = f"test_image_{i}".encode()
            timestamp = datetime.now()
            await storage_manager.save_image(test_data, timestamp)
        
        recent_images = await storage_manager.get_recent_images(minutes=60)
        
        assert len(recent_images) == 3
    
    @pytest.mark.asyncio
    async def test_storage_usage(self, storage_manager):
        """Test storage usage calculation."""
        usage = await storage_manager.get_storage_usage()
        
        assert "total_size_mb" in usage
        assert "image_count" in usage
        assert "sequence_count" in usage


class TestImageSequenceService:
    """Test main sequence service."""
    
    @pytest.fixture
    def settings(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            return Settings(
                images_dir=temp_path / "images",
                sequences_dir=temp_path / "sequences",
                camera_ip="192.168.1.110",
                camera_username="admin",
                camera_password="123456"
            )
    
    @pytest.fixture
    def service(self, settings):
        return ImageSequenceService(settings)
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, service):
        """Test service initialization."""
        assert service.settings is not None
        assert service.camera is not None
        assert service.image_processor is not None
        assert service.storage is not None
        assert not service.is_running
    
    @pytest.mark.asyncio
    async def test_get_status(self, service):
        """Test status retrieval."""
        status = await service.get_status()
        
        assert "is_running" in status
        assert "camera_info" in status
        assert "storage_usage" in status
        assert "settings" in status


class TestSecurityUtils:
    """Test security utilities."""
    
    def test_validate_ip_address(self):
        """Test IP address validation."""
        from src.utils.security import SecurityUtils
        
        assert SecurityUtils.validate_ip_address("192.168.1.1")
        assert SecurityUtils.validate_ip_address("127.0.0.1")
        assert not SecurityUtils.validate_ip_address("invalid_ip")
        assert not SecurityUtils.validate_ip_address("192.168.1.256")
    
    def test_validate_filename(self):
        """Test filename validation."""
        from src.utils.security import SecurityUtils
        
        assert SecurityUtils.validate_filename("valid_file.jpg")
        assert not SecurityUtils.validate_filename("../etc/passwd")
        assert not SecurityUtils.validate_filename("file<name>.jpg")
        assert not SecurityUtils.validate_filename("a" * 300)  # Too long
    
    def test_sanitize_input(self):
        """Test input sanitization."""
        from src.utils.security import SecurityUtils
        
        assert SecurityUtils.sanitize_input("normal text") == "normal text"
        assert SecurityUtils.sanitize_input("text<script>") == "text"
        assert SecurityUtils.sanitize_input("a" * 2000, 100) == "a" * 100


# Integration tests
class TestIntegration:
    """Integration tests."""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete workflow from camera to web."""
        # This would test the full integration
        # For now, just verify imports work
        from src.app import create_app
        from src.config import Settings
        
        settings = Settings()
        app = create_app(settings)
        
        assert app is not None
        assert app.title == "Image Sequence Server"


if __name__ == "__main__":
    pytest.main([__file__])
