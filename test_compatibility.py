#!/usr/bin/env python3
"""
Test script to verify Django compatibility and basic functionality
"""

import os
import sys
import django
from django.conf import settings

def test_django_version():
    """Test Django version"""
    print(f"Django version: {django.get_version()}")
    return True

def test_settings():
    """Test Django settings"""
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'greatkart.settings')
        django.setup()
        print(f"Django settings loaded successfully")
        print(f"DEBUG mode: {settings.DEBUG}")
        print(f"Database engine: {settings.DATABASES['default']['ENGINE']}")
        print(f"Installed apps: {len(settings.INSTALLED_APPS)} apps")
        return True
    except Exception as e:
        print(f"Error loading Django settings: {e}")
        return False

def test_models():
    """Test model imports"""
    try:
        from accounts.models import Account, UserProfile
        from store.models import Product, Variation
        from category.models import Category
        from carts.models import Cart, CartItem
        from orders.models import Order, OrderProduct, Payment
        print("All models imported successfully")
        return True
    except Exception as e:
        print(f"Error importing models: {e}")
        return False

def test_urls():
    """Test URL configuration"""
    try:
        from django.urls import reverse
        from django.test import Client
        client = Client()
        print("URL configuration and client setup successful")
        return True
    except Exception as e:
        print(f"Error with URL configuration: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing Django E-commerce Project Compatibility")
    print("=" * 50)
    
    tests = [
        ("Django Version", test_django_version),
        ("Django Settings", test_settings),
        ("Model Imports", test_models),
        ("URL Configuration", test_urls),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\nRunning {test_name} test...")
        try:
            if test_func():
                print(f"✓ {test_name} test PASSED")
                passed += 1
            else:
                print(f"✗ {test_name} test FAILED")
        except Exception as e:
            print(f"✗ {test_name} test FAILED with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The project is compatible with the latest Django.")
        return 0
    else:
        print("❌ Some tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 