"""
Quick API test script - verifies endpoints work without starting server
"""
import sys
import os

# Test imports
print("🧪 Testing API imports...")
try:
    from api import app, solver, major_requirements
    print("   ✅ API module imported successfully")
    print(f"   📚 Catalog size: {len(solver.catalog)}")
    print(f"   🎓 Majors loaded: {len(major_requirements)}")
except Exception as e:
    print(f"   ❌ Import failed: {e}")
    sys.exit(1)

# Test Flask app
print("\n🧪 Testing Flask app...")
try:
    with app.test_client() as client:
        # Test 1: Health check
        response = client.get('/api/health')
        assert response.status_code == 200
        data = response.get_json()
        print(f"   ✅ Health check: {data['status']}")
        
        # Test 2: Search endpoint
        response = client.post('/api/search', json={
            'query': 'COP'
        })
        assert response.status_code == 200
        data = response.get_json()
        print(f"   ✅ Search: Found {data['count']} courses")
        
        # Test 3: Majors endpoint
        response = client.get('/api/majors')
        assert response.status_code == 200
        data = response.get_json()
        print(f"   ✅ Majors: {data['count']} available")
        
        # Test 4: Schedule generation
        response = client.post('/api/generate-schedule', json={
            'courses': ['COP3502', 'MAC2312']
        })
        assert response.status_code == 200
        data = response.get_json()
        if data['success']:
            print(f"   ✅ Schedule: Generated with {data['courses_scheduled']} courses")
        else:
            print(f"   ⚠️  Schedule: {data.get('message', 'No solution found')}")
        
except Exception as e:
    print(f"   ❌ API test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✨ All API tests passed! Ready to run: python backend/api.py")
