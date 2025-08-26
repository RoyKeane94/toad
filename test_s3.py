#!/usr/bin/env python
"""
Test S3 connectivity and configuration
Run this script to verify your S3 setup is working correctly
"""

import os
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_s3_connection():
    """Test basic S3 connectivity"""
    print("🔍 Testing S3 Configuration...")
    
    # Get credentials from environment
    access_key = os.environ.get('AWS_ACCESS_KEY_ID')
    secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    bucket_name = os.environ.get('AWS_STORAGE_BUCKET_NAME')
    region = os.environ.get('AWS_S3_REGION_NAME', 'us-east-1')
    
    print(f"📍 Region: {region}")
    print(f"🪣 Bucket: {bucket_name}")
    print(f"🔑 Access Key: {access_key[:8]}..." if access_key else "❌ No Access Key")
    print(f"🔐 Secret Key: {'*' * 8}..." if secret_key else "❌ No Secret Key")
    
    if not all([access_key, secret_key, bucket_name]):
        print("❌ Missing required environment variables!")
        return False
    
    try:
        # Create S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        
        print("✅ S3 client created successfully")
        
        # Test bucket access
        response = s3_client.head_bucket(Bucket=bucket_name)
        print(f"✅ Bucket '{bucket_name}' is accessible")
        
        # List objects (first 5)
        response = s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=5)
        objects = response.get('Contents', [])
        print(f"📁 Bucket contains {len(objects)} objects")
        
        if objects:
            print("📋 Sample objects:")
            for obj in objects[:3]:
                print(f"   - {obj['Key']} ({obj['Size']} bytes)")
        
        # Test file upload (small test file)
        test_content = b"Hello S3! This is a test file."
        test_key = "test/connection-test.txt"
        
        s3_client.put_object(
            Bucket=bucket_name,
            Key=test_key,
            Body=test_content,
            ContentType='text/plain'
        )
        print(f"✅ Test file uploaded: {test_key}")
        
        # Clean up test file
        s3_client.delete_object(Bucket=bucket_name, Key=test_key)
        print(f"🧹 Test file cleaned up: {test_key}")
        
        print("\n🎉 S3 configuration is working perfectly!")
        return True
        
    except NoCredentialsError:
        print("❌ No AWS credentials found")
        return False
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchBucket':
            print(f"❌ Bucket '{bucket_name}' does not exist")
        elif error_code == 'AccessDenied':
            print(f"❌ Access denied to bucket '{bucket_name}'")
        else:
            print(f"❌ AWS Error: {error_code}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_django_storage():
    """Test Django storage backend"""
    print("\n🔍 Testing Django Storage Backend...")
    
    try:
        # Set environment for testing
        os.environ['FORCE_S3_TESTING'] = 'true'
        
        # Import Django settings
        import django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'toad.settings')
        django.setup()
        
        from django.conf import settings
        from django.core.files.storage import default_storage
        
        print(f"📁 Storage Backend: {default_storage.__class__.__name__}")
        print(f"🌐 Media URL: {getattr(settings, 'MEDIA_URL', 'Not set')}")
        
        # Test storage operations
        from django.core.files.base import ContentFile
        test_content = ContentFile(b"Django storage test content", name="test-file.txt")
        test_path = "django-test/test-file.txt"
        
        # Save file
        saved_path = default_storage.save(test_path, test_content)
        print(f"✅ File saved: {saved_path}")
        
        # Check if file exists
        exists = default_storage.exists(test_path)
        print(f"🔍 File exists: {exists}")
        
        # Get file URL
        url = default_storage.url(test_path)
        print(f"🔗 File URL: {url}")
        
        # Delete test file
        default_storage.delete(test_path)
        print(f"🧹 Test file deleted")
        
        print("🎉 Django storage backend is working!")
        return True
        
    except Exception as e:
        print(f"❌ Django storage error: {e}")
        return False
    finally:
        # Clean up environment
        os.environ.pop('FORCE_S3_TESTING', None)

if __name__ == "__main__":
    print("🚀 S3 Configuration Test Suite")
    print("=" * 40)
    
    # Test basic S3 connectivity
    s3_ok = test_s3_connection()
    
    if s3_ok:
        # Test Django integration
        django_ok = test_django_storage()
        
        if django_ok:
            print("\n🎉 All tests passed! Your S3 configuration is ready for production.")
        else:
            print("\n⚠️  S3 works but Django integration has issues.")
    else:
        print("\n❌ S3 configuration failed. Please check your credentials and bucket settings.")
    
    print("\n💡 To test in Django, set: FORCE_S3_TESTING=true")
    print("💡 Remember to set it back to false after testing!")
