#!/usr/bin/env python
"""
AWS S3 Connection Test Script for Railway
Run this on Railway to test S3 connectivity and diagnose issues
"""

import os
import sys
import django
import boto3
from botocore.exceptions import ClientError, NoCredentialsError, EndpointConnectionError

# Add the project directory to the Python path
sys.path.append('/app')  # Railway path

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'toad.settings')
django.setup()

def test_aws_credentials():
    """Test if AWS credentials are accessible"""
    print("🔑 Testing AWS Credentials...")
    print("=" * 50)
    
    # Check environment variables
    aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    bucket_name = os.environ.get('AWS_STORAGE_BUCKET_NAME')
    region = os.environ.get('AWS_S3_REGION_NAME', 'us-east-1')
    
    print(f"AWS_ACCESS_KEY_ID: {'✅ Set' if aws_access_key else '❌ Missing'}")
    print(f"AWS_SECRET_ACCESS_KEY: {'✅ Set' if aws_secret_key else '❌ Missing'}")
    print(f"AWS_STORAGE_BUCKET_NAME: {'✅ Set' if bucket_name else '❌ Missing'}")
    print(f"AWS_S3_REGION_NAME: {'✅ Set' if region else '❌ Missing'}")
    
    if not all([aws_access_key, aws_secret_key, bucket_name]):
        print("❌ Missing required AWS credentials!")
        return False
    
    print(f"Bucket: {bucket_name}")
    print(f"Region: {region}")
    return True

def test_boto3_connection():
    """Test direct boto3 connection to S3"""
    print("\n🌐 Testing Boto3 S3 Connection...")
    print("=" * 50)
    
    try:
        # Create S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            region_name=os.environ.get('AWS_S3_REGION_NAME', 'us-east-1')
        )
        
        print("✅ S3 client created successfully")
        
        # Test bucket access
        bucket_name = os.environ.get('AWS_STORAGE_BUCKET_NAME')
        try:
            response = s3_client.head_bucket(Bucket=bucket_name)
            print(f"✅ Bucket '{bucket_name}' is accessible")
            print(f"   Region: {response.get('ResponseMetadata', {}).get('HTTPHeaders', {}).get('x-amz-bucket-region', 'Unknown')}")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                print(f"❌ Bucket '{bucket_name}' not found")
            elif error_code == '403':
                print(f"❌ Access denied to bucket '{bucket_name}'")
            else:
                print(f"❌ Error accessing bucket: {error_code}")
            return False
        
        # Test file upload
        try:
            test_content = b"Test file content for S3 connectivity"
            test_key = "test/aws-test-file.txt"
            
            s3_client.put_object(
                Bucket=bucket_name,
                Key=test_key,
                Body=test_content,
                ContentType='text/plain'
            )
            print(f"✅ Test file uploaded: {test_key}")
            
            # Test file download
            response = s3_client.get_object(Bucket=bucket_name, Key=test_key)
            downloaded_content = response['Body'].read()
            if downloaded_content == test_content:
                print("✅ Test file downloaded successfully")
            else:
                print("❌ Downloaded content doesn't match")
            
            # Clean up test file
            s3_client.delete_object(Bucket=bucket_name, Key=test_key)
            print("✅ Test file cleaned up")
            
        except Exception as e:
            print(f"❌ File operation failed: {e}")
            return False
        
        return True
        
    except NoCredentialsError:
        print("❌ No AWS credentials found")
        return False
    except EndpointConnectionError as e:
        print(f"❌ Connection error: {e}")
        print("   This usually means the region is wrong or S3 is unreachable")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_django_storage():
    """Test Django's storage backend"""
    print("\n🐍 Testing Django Storage Backend...")
    print("=" * 50)
    
    try:
        from django.conf import settings
        from django.core.files.storage import default_storage
        from django.core.files.base import ContentFile
        
        print(f"Storage Backend: {default_storage.__class__.__name__}")
        print(f"Storage Location: {getattr(default_storage, 'location', 'N/A')}")
        print(f"Storage Base URL: {getattr(default_storage, 'base_url', 'N/A')}")
        
        # Test file operations
        test_content = b"Django storage test content"
        test_path = "test/django-test-file.txt"
        
        # Save file
        test_file = ContentFile(test_content, name=test_path)
        saved_path = default_storage.save(test_path, test_file)
        print(f"✅ File saved: {saved_path}")
        
        # Check if file exists
        if default_storage.exists(saved_path):
            print("✅ File exists check passed")
        else:
            print("❌ File exists check failed")
        
        # Get file URL
        try:
            file_url = default_storage.url(saved_path)
            print(f"✅ File URL generated: {file_url}")
        except Exception as e:
            print(f"❌ URL generation failed: {e}")
        
        # Clean up
        default_storage.delete(saved_path)
        print("✅ Test file deleted")
        
        return True
        
    except Exception as e:
        print(f"❌ Django storage test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_society_link_model():
    """Test if SocietyLink model can save with image"""
    print("\n🔗 Testing SocietyLink Model...")
    print("=" * 50)
    
    try:
        from CRM.models import SocietyLink
        from django.core.files.base import ContentFile
        
        # Create a test society link with a fake image
        test_image = ContentFile(b"fake image content", name="test-image.png")
        
        society_link = SocietyLink(
            name="AWS Test Society",
            image=test_image
        )
        
        print(f"✅ SocietyLink object created: {society_link}")
        print(f"   Name: {society_link.name}")
        print(f"   Image: {society_link.image}")
        
        # Try to save
        society_link.save()
        print(f"✅ SocietyLink saved successfully! ID: {society_link.pk}")
        
        # Clean up
        society_link.delete()
        print("✅ Test SocietyLink deleted")
        
        return True
        
    except Exception as e:
        print(f"❌ SocietyLink test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 AWS S3 Connection Test Suite")
    print("=" * 60)
    print(f"Environment: {'Production' if not os.environ.get('DEBUG') else 'Development'}")
    print(f"Python: {sys.version}")
    print(f"Django: {django.get_version()}")
    print("=" * 60)
    
    tests = [
        ("AWS Credentials", test_aws_credentials),
        ("Boto3 S3 Connection", test_boto3_connection),
        ("Django Storage", test_django_storage),
        ("SocietyLink Model", test_society_link_model)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! S3 is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        
        # Specific recommendations
        if not results[0][1]:  # Credentials failed
            print("\n💡 Fix: Check your AWS environment variables in Railway")
        elif not results[1][1]:  # Boto3 failed
            print("\n💡 Fix: Check S3 bucket permissions and region settings")
        elif not results[2][1]:  # Django storage failed
            print("\n💡 Fix: Check Django storage configuration")
        elif not results[3][1]:  # Model failed
            print("\n💡 Fix: Check model field definitions and database")

if __name__ == "__main__":
    main()
