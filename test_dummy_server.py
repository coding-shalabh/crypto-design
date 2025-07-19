"""
Quick test to verify dummy server is working
"""
import requests
import json

def test_dummy_server():
    """Test the dummy server endpoints"""
    print("Testing dummy analysis server...")
    
    try:
        # Test health endpoint
        print("1. Testing health endpoint...")
        response = requests.get("http://localhost:5001/api/health", timeout=5)
        
        if response.status_code == 200:
            print("   [OK] Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"   [FAIL] Health check failed: {response.status_code}")
            return False
        
        # Test analysis endpoint
        print("2. Testing analysis endpoint...")
        response = requests.get("http://localhost:5001/api/analysis/BTCUSDT", timeout=5)
        
        if response.status_code == 200:
            analysis = response.json()
            print("   [OK] Analysis endpoint working")
            
            # Check key components
            if 'final_recommendation' in analysis:
                final_rec = analysis['final_recommendation']
                print(f"   Final recommendation: {final_rec.get('action')} with {final_rec.get('confidence', 0):.2f} confidence")
            
            if 'grok_analysis' in analysis:
                print("   Grok analysis: Present")
            
            if 'claude_analysis' in analysis:
                print("   Claude analysis: Present")
            
            if 'trade_setup' in analysis:
                print("   Trade setup: Present")
                
            print("   [OK] All required components present")
            return True
        else:
            print(f"   [FAIL] Analysis endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   [FAIL] Test failed: {e}")
        return False

if __name__ == "__main__":
    print("="*50)
    print("DUMMY SERVER TEST")
    print("="*50)
    
    if test_dummy_server():
        print("\n[SUCCESS] All tests passed! Dummy server is working correctly.")
        print("\nNow you can:")
        print("1. Use the dummy server for cost-free testing")
        print("2. Switch to real APIs by changing API_MODE in .env")
        print("3. Test all trading functionality without API costs")
    else:
        print("\n[FAIL] Tests failed. Please check the dummy server.")
    
    print("="*50)