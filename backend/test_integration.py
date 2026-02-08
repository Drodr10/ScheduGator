"""
Quick integration test for ScheduGator backend
"""
import os
import sys

# Test 1: Check if data files exist
print("🧪 Test 1: Checking data files...")
current_dir = os.path.dirname(os.path.abspath(__file__))
catalog_path = os.path.join(current_dir, '..', 'data', 'universal_base_catalog.json')
bucket_path = os.path.join(current_dir, '..', 'data', 'bucket_1.json')

if os.path.exists(catalog_path):
    print(f"   ✅ Found catalog at: {catalog_path}")
else:
    print(f"   ❌ Missing catalog at: {catalog_path}")

if os.path.exists(bucket_path):
    print(f"   ✅ Found bucket at: {bucket_path}")
else:
    print(f"   ❌ Missing bucket at: {bucket_path}")

# Test 2: Import modules
print("\n🧪 Test 2: Importing modules...")
try:
    from search import search_catalog
    print("   ✅ search.py imported successfully")
except Exception as e:
    print(f"   ❌ Failed to import search: {e}")
    sys.exit(1)

try:
    from conflicts import solve_schedule, has_global_conflict
    print("   ✅ conflicts.py imported successfully")
except Exception as e:
    print(f"   ❌ Failed to import conflicts: {e}")
    sys.exit(1)

try:
    from solver_bridge import SolverBridge
    print("   ✅ solver_bridge.py imported successfully")
except Exception as e:
    print(f"   ❌ Failed to import solver_bridge: {e}")
    sys.exit(1)

# Test 3: Search function
print("\n🧪 Test 3: Testing search_catalog...")
try:
    results = search_catalog(query="COP")
    print(f"   ✅ Search returned {len(results)} results")
    if results:
        print(f"   📚 Sample: {results[0].get('code', 'N/A')} - {results[0].get('name', 'N/A')}")
except Exception as e:
    print(f"   ❌ Search failed: {e}")

# Test 4: SolverBridge initialization
print("\n🧪 Test 4: Testing SolverBridge...")
try:
    solver = SolverBridge()
    print(f"   ✅ SolverBridge initialized with {len(solver.catalog)} courses")
except Exception as e:
    print(f"   ❌ SolverBridge failed: {e}")

# Test 5: Brain (if API key exists)
print("\n🧪 Test 5: Testing GemmaBrain...")
try:
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("   ⚠️  No GEMINI_API_KEY in .env - skipping brain test")
    else:
        from brain import GemmaBrain
        print("   ✅ GemmaBrain imported successfully")
        print("   ℹ️  Brain is ready (not testing API call to save credits)")
except Exception as e:
    print(f"   ⚠️  Brain import note: {e}")

print("\n✨ Integration tests complete!")
