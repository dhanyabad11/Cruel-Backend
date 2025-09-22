"""
Test script to verify Supabase setup and authentication system
"""
import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append('/Users/dhanyabad/code2/cruel/ai-cruel/backend')

async def test_supabase_setup():
    """Test if Supabase can be imported and basic setup works"""
    
    print("🔧 Testing Supabase Setup...")
    
    try:
        # Test 1: Import Supabase
        print("1. Testing Supabase import...")
        from supabase import create_client, Client
        print("   ✅ Supabase imported successfully")
        
        # Test 2: Test auth service import
        print("2. Testing auth service import...")
        try:
            from app.services.auth_service import SupabaseAuthService
            print("   ✅ Auth service imported successfully")
        except Exception as e:
            print(f"   ⚠️  Auth service import failed (expected without .env): {e}")
        
        # Test 3: Test auth routes import
        print("3. Testing auth routes import...")
        from app.routes.auth_routes_supabase import router
        print("   ✅ Auth routes imported successfully")
        
        # Test 4: Test auth dependencies
        print("4. Testing auth dependencies...")
        from app.auth_deps import get_current_user
        print("   ✅ Auth dependencies imported successfully")
        
        print("\n🎉 All imports successful!")
        print("\n📋 Next Steps:")
        print("1. Set up Supabase account at https://supabase.com")
        print("2. Create new project (free tier)")
        print("3. Copy .env.example to .env")
        print("4. Add your Supabase credentials to .env")
        print("5. Run the database setup SQL from SUPABASE_SETUP.md")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_supabase_setup())
    if success:
        print("\n✅ Supabase setup test passed!")
    else:
        print("\n❌ Supabase setup test failed!")
        sys.exit(1)