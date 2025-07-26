#!/usr/bin/env python3
"""
Diagnostic script for Binance API issues
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def diagnose_binance_setup():
    print("=" * 60)
    print("BINANCE API DIAGNOSTIC TOOL")
    print("=" * 60)
    
    # Check if .env file exists
    print("\n1. Checking .env file...")
    if os.path.exists('.env'):
        print("PASS - .env file found")
    else:
        print("FAIL - .env file not found")
        return False
    
    # Check environment variables
    print("\n2. Checking environment variables...")
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    
    if api_key:
        print(f"PASS - BINANCE_API_KEY found (length: {len(api_key)})")
        print(f"      First 10 chars: {api_key[:10]}...")
        print(f"      Last 10 chars: ...{api_key[-10:]}")
    else:
        print("FAIL - BINANCE_API_KEY not found")
        return False
    
    if api_secret:
        print(f"PASS - BINANCE_API_SECRET found (length: {len(api_secret)})")
        print(f"      First 10 chars: {api_secret[:10]}...")
        print(f"      Last 10 chars: ...{api_secret[-10:]}")
    else:
        print("FAIL - BINANCE_API_SECRET not found")
        return False
    
    # Check API key format
    print("\n3. Checking API key format...")
    if len(api_key) == 64 and api_key.startswith(('c9jjoX', 'sk-', 'binance')):
        print("PASS - API key format looks valid")
    else:
        print("WARNING - API key format might be incorrect")
        print("         Expected: 64 characters starting with specific prefix")
        print(f"         Got: {len(api_key)} characters starting with '{api_key[:6]}'")
    
    if len(api_secret) == 64:
        print("PASS - API secret format looks valid")
    else:
        print("WARNING - API secret format might be incorrect")
        print("         Expected: 64 characters")
        print(f"         Got: {len(api_secret)} characters")
    
    # Test basic ping without authentication
    print("\n4. Testing basic Binance API connectivity...")
    try:
        import requests
        response = requests.get('https://api.binance.com/api/v3/ping', timeout=10)
        if response.status_code == 200:
            print("PASS - Binance API is reachable")
        else:
            print(f"FAIL - Binance API returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"FAIL - Cannot reach Binance API: {e}")
        return False
    
    # Test server time
    print("\n5. Testing server time...")
    try:
        response = requests.get('https://api.binance.com/api/v3/time', timeout=10)
        if response.status_code == 200:
            server_time = response.json()['serverTime']
            print(f"PASS - Server time: {server_time}")
        else:
            print(f"FAIL - Cannot get server time: {response.status_code}")
    except Exception as e:
        print(f"WARNING - Server time check failed: {e}")
    
    print("\n" + "=" * 60)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 60)
    print("\nPOSSIBLE ISSUES:")
    print("1. API key might be for testnet instead of mainnet")
    print("2. API key might not have trading permissions enabled")
    print("3. IP whitelist might be configured (disable it for testing)")
    print("4. API key might be expired or disabled")
    print("5. Account might be restricted")
    
    print("\nNEXT STEPS:")
    print("1. Log into Binance account")
    print("2. Go to API Management")
    print("3. Check if API key has 'Enable Spot & Margin Trading' permission")
    print("4. Verify IP restrictions are disabled (or add your IP)")
    print("5. Make sure you're using mainnet API key, not testnet")
    print("6. Try generating a new API key if needed")
    
    return True

if __name__ == "__main__":
    diagnose_binance_setup()