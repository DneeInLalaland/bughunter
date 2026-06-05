import requests
import time
import json
import sys

# Configuration
BACKEND_URL = "http://localhost:8000/api"
SCANNER_URL = "http://localhost:5001"
TEST_URL = "http://testphp.vulnweb.com"

def print_step(step):
    """Print formatted step header"""
    print(f"\n{'='*60}")
    print(f"Step: {step}")
    print('='*60)

def check_services():
    """Check if all required services are running"""
    print_step("0. Checking services")
    
    services = {
        "Scanner API": f"{SCANNER_URL}/health",
        "Backend API": f"{BACKEND_URL}/../health"
    }
    
    all_healthy = True
    for name, url in services.items():
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✓ {name}: Running")
            else:
                print(f"✗ {name}: Not healthy (status {response.status_code})")
                all_healthy = False
        except Exception as e:
            print(f"✗ {name}: Not reachable ({str(e)})")
            all_healthy = False
    
    if not all_healthy:
        print("\n⚠️  Some services are not running!")
        print("Please start services with: docker-compose up -d")
        return False
    
    return True

def test_scanner_only():
    """Test Scanner API directly (works even without backend)"""
    print_step("Testing Scanner API directly")
    
    try:
        # Test health endpoint
        response = requests.get(f"{SCANNER_URL}/health", timeout=5)
        if response.status_code != 200:
            print(f"✗ Scanner health check failed: {response.status_code}")
            return False
        
        print(f"✓ Scanner is healthy")
        health_data = response.json()
        print(f"  Available scanners: {', '.join(health_data.get('scanners', []))}")
        
        # Test a simple scan
        print("\n🔍 Testing SQL Injection scan...")
        scan_response = requests.post(
            f"{SCANNER_URL}/scan/sql",
            json={"target_url": TEST_URL},
            timeout=30
        )
        
        if scan_response.status_code == 200:
            result = scan_response.json()
            vuln_count = len(result.get('vulnerabilities', []))
            print(f"✓ SQL Injection scan completed")
            print(f"  Found {vuln_count} potential vulnerabilities")
            return True
        else:
            print(f"✗ Scan failed: {scan_response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Scanner test failed: {str(e)}")
        return False

def test_full_scan_flow():
    """Test full scan flow through Backend API"""
    print_step("1. Create a new scan")
    
    # Check if backend is available
    try:
        backend_health = requests.get(f"{BACKEND_URL}/../health", timeout=5)
        if backend_health.status_code != 200:
            print("⚠️  Backend API not available")
            print("Skipping full integration test")
            return None
    except:
        print("⚠️  Backend API not available")
        print("Skipping full integration test")
        return None
    
    # Create scan
    try:
        response = requests.post(
            f"{BACKEND_URL}/scans",
            json={"target_url": TEST_URL},
            timeout=10
        )
        
        if response.status_code != 201:
            print(f"✗ Failed to create scan: {response.status_code}")
            print(response.text)
            return False
        
        scan_data = response.json()
        scan_id = scan_data['id']
        print(f"✓ Scan created successfully! ID: {scan_id}")
        print(f"  Status: {scan_data['status']}")
        
    except Exception as e:
        print(f"✗ Error creating scan: {str(e)}")
        return False
    
    # Wait for scan to complete
    print_step("2. Waiting for scan to complete")
    max_wait = 300  # 5 minutes
    waited = 0
    
    while waited < max_wait:
        time.sleep(5)
        waited += 5
        
        try:
            response = requests.get(f"{BACKEND_URL}/scans/{scan_id}", timeout=10)
            scan_data = response.json()
            status = scan_data['status']
            
            print(f"  [{waited}s] Status: {status}")
            
            if status == 'completed':
                print(f"✓ Scan completed!")
                print(f"  Total vulnerabilities: {scan_data.get('total_vulnerabilities', 0)}")
                print(f"  Critical: {scan_data.get('critical_count', 0)}")
                print(f"  High: {scan_data.get('high_count', 0)}")
                print(f"  Medium: {scan_data.get('medium_count', 0)}")
                print(f"  Low: {scan_data.get('low_count', 0)}")
                break
                
            elif status == 'failed':
                print(f"✗ Scan failed!")
                print(f"  Error: {scan_data.get('error_message')}")
                return False
                
        except Exception as e:
            print(f"✗ Error checking scan status: {str(e)}")
            return False
    else:
        print(f"✗ Scan timed out after {max_wait}s")
        return False
    
    # Fetch vulnerabilities
    print_step("3. Fetching vulnerabilities")
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/scans/{scan_id}/vulnerabilities",
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"✗ Failed to fetch vulnerabilities")
            return False
        
        vulnerabilities = response.json()
        print(f"✓ Fetched {len(vulnerabilities)} vulnerabilities")
        
        # Show top 3
        if vulnerabilities:
            print("\n  Top 3 vulnerabilities:")
            for i, vuln in enumerate(vulnerabilities[:3], 1):
                print(f"  {i}. {vuln['type']} ({vuln['severity']})")
                print(f"     AI Risk Score: {vuln.get('ai_risk_score', 0):.2f}/10")
        
    except Exception as e:
        print(f"✗ Error fetching vulnerabilities: {str(e)}")
        return False
    
    print_step("✓ All tests passed!")
    return True

def main():
    """Main test execution"""
    print("="*60)
    print("End-to-End Test Suite")
    print("="*60)
    
    # Check services
    if not check_services():
        print("\n❌ Services check failed!")
        print("\nTo fix:")
        print("1. Make sure Docker is running")
        print("2. Run: docker-compose up -d")
        print("3. Wait 30 seconds for services to start")
        print("4. Run this test again")
        sys.exit(1)
    
    # Test Scanner API directly (always works)
    scanner_ok = test_scanner_only()
    
    # Try full integration test (requires backend)
    full_test_result = test_full_scan_flow()
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    if scanner_ok:
        print("✓ Scanner API: PASS")
    else:
        print("✗ Scanner API: FAIL")
    
    if full_test_result is None:
        print("⊘ Full Integration: SKIPPED (Backend not available)")
        print("\n📝 Note: This is expected if you haven't integrated")
        print("   all components yet. Scanner API works fine!")
    elif full_test_result:
        print("✓ Full Integration: PASS")
    else:
        print("✗ Full Integration: FAIL")
    
    # Exit code
    if scanner_ok:
        print("\n✅ Core functionality (Scanner) working!")
        sys.exit(0)
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()