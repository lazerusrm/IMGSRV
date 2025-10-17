#!/usr/bin/env python3
"""
Basic functionality test for Image Sequence Server.

This script tests the core components without requiring a camera.
"""

import asyncio
import tempfile
from pathlib import Path
from datetime import datetime

# Test imports
try:
    from src.config import Settings
    from src.services.image_processor import ImageProcessor
    from src.services.storage import StorageManager
    from src.utils.security import SecurityUtils
    print("✓ All imports successful")
except ImportError as e:
    print(f"X Import error: {e}")
    exit(1)

async def test_config():
    """Test configuration loading."""
    print("\n--- Testing Configuration ---")
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            settings = Settings(
                images_dir=temp_path / "images",
                sequences_dir=temp_path / "sequences"
            )
            print(f"✓ Configuration loaded: {settings.camera_ip}")
            print(f"✓ Image dimensions: {settings.image_width}x{settings.image_height}")
            return True
    except Exception as e:
        print(f"X Configuration test failed: {e}")
        return False

async def test_image_processor():
    """Test image processing."""
    print("\n--- Testing Image Processor ---")
    try:
        processor = ImageProcessor()
        
        # Create a simple test image
        from PIL import Image
        import io
        
        test_image = Image.new('RGB', (100, 100), color='red')
        image_bytes = io.BytesIO()
        test_image.save(image_bytes, format='JPEG')
        image_data = image_bytes.getvalue()
        
        # Test timestamp overlay
        timestamp = datetime.now()
        result = await processor.add_timestamp_overlay(image_data, timestamp)
        
        print(f"✓ Image processor initialized")
        print(f"✓ Timestamp overlay added (original: {len(image_data)} bytes, result: {len(result)} bytes)")
        return True
    except Exception as e:
        print(f"X Image processor test failed: {e}")
        return False

async def test_storage_manager():
    """Test storage management."""
    print("\n--- Testing Storage Manager ---")
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            storage = StorageManager(
                images_dir=temp_path / "images",
                sequences_dir=temp_path / "sequences"
            )
            
            # Test saving an image
            test_data = b"test_image_data"
            timestamp = datetime.now()
            result_path = await storage.save_image(test_data, timestamp)
            
            print(f"✓ Storage manager initialized")
            print(f"✓ Image saved to: {result_path}")
            
            # Test getting recent images
            recent_images = await storage.get_recent_images()
            print(f"✓ Recent images retrieved: {len(recent_images)}")
            
            # Test storage usage
            usage = await storage.get_storage_usage()
            print(f"✓ Storage usage calculated: {usage.get('total_size_mb', 0)} MB")
            
            return True
    except Exception as e:
        print(f"X Storage manager test failed: {e}")
        return False

def test_security_utils():
    """Test security utilities."""
    print("\n--- Testing Security Utils ---")
    try:
        # Test IP validation
        assert SecurityUtils.validate_ip_address("192.168.1.1")
        assert not SecurityUtils.validate_ip_address("invalid_ip")
        print("✓ IP address validation works")
        
        # Test filename validation
        assert SecurityUtils.validate_filename("valid_file.jpg")
        assert not SecurityUtils.validate_filename("../etc/passwd")
        print("✓ Filename validation works")
        
        # Test input sanitization
        result = SecurityUtils.sanitize_input("test<script>input")
        assert "<script>" not in result
        print("✓ Input sanitization works")
        
        return True
    except Exception as e:
        print(f"X Security utils test failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("Image Sequence Server - Basic Functionality Test")
    print("=" * 50)
    
    tests = [
        test_config(),
        test_image_processor(),
        test_storage_manager(),
    ]
    
    # Run async tests
    results = await asyncio.gather(*tests, return_exceptions=True)
    
    # Run sync test
    security_result = test_security_utils()
    
    # Count results
    passed = sum(1 for r in results if r is True) + (1 if security_result else 0)
    total = len(results) + 1
    
    print(f"\n--- Test Results ---")
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed! The application is ready for deployment.")
        return 0
    else:
        print("X Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
