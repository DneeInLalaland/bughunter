import requests
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration
SCANNER_URL = "http://localhost:5001"
TEST_URL = "http://testphp.vulnweb.com"
NUM_REQUESTS = 50
CONCURRENT_USERS = 5

def test_health_endpoint():
    """Test /health endpoint"""
    start_time = time.time()
    try:
        response = requests.get(f"{SCANNER_URL}/health", timeout=5)
        elapsed = time.time() - start_time
        return {
            "success": response.status_code == 200,
            "time": elapsed,
            "status_code": response.status_code
        }
    except Exception as e:
        return {
            "success": False,
            "time": time.time() - start_time,
            "error": str(e)
        }

def test_scan_endpoint():
    """Test /scan/sql endpoint"""
    start_time = time.time()
    try:
        response = requests.post(
            f"{SCANNER_URL}/scan/sql",
            json={"target_url": TEST_URL},
            timeout=30
        )
        elapsed = time.time() - start_time
        return {
            "success": response.status_code == 200,
            "time": elapsed,
            "status_code": response.status_code
        }
    except Exception as e:
        return {
            "success": False,
            "time": time.time() - start_time,
            "error": str(e)
        }

def run_load_test(test_func, num_requests, concurrent_users):
    """Run load test with multiple concurrent users"""
    print(f"\n{'='*60}")
    print(f"Running {test_func.__name__}")
    print(f"Requests: {num_requests}, Concurrent Users: {concurrent_users}")
    print('='*60)
    
    results = []
    
    with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
        futures = [executor.submit(test_func) for _ in range(num_requests)]
        
        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()
            results.append(result)
            
            status = "✓" if result["success"] else "✗"
            print(f"  [{i}/{num_requests}] {status} {result['time']:.2f}s")
    
    return results

def analyze_results(results):
    """Analyze and print test results"""
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    if successful:
        times = [r["time"] for r in successful]
        
        print(f"\n{'='*60}")
        print("Results Summary")
        print('='*60)
        print(f"Total Requests:     {len(results)}")
        print(f"Successful:         {len(successful)} ({len(successful)/len(results)*100:.1f}%)")
        print(f"Failed:             {len(failed)} ({len(failed)/len(results)*100:.1f}%)")
        print(f"\nResponse Times:")
        print(f"  Min:              {min(times):.2f}s")
        print(f"  Max:              {max(times):.2f}s")
        print(f"  Average:          {statistics.mean(times):.2f}s")
        print(f"  Median:           {statistics.median(times):.2f}s")
        
        if len(times) > 1:
            print(f"  Std Dev:          {statistics.stdev(times):.2f}s")
    else:
        print("\n❌ All requests failed!")
        if failed and "error" in failed[0]:
            print(f"Error: {failed[0]['error']}")

def main():
    """Main load test execution"""
    print("="*60)
    print("Load Test Suite - Scanner API")
    print("="*60)
    
    # Check if Scanner API is running
    print("\nChecking Scanner API...")
    health_result = test_health_endpoint()
    
    if not health_result["success"]:
        print("❌ Scanner API is not running!")
        print(f"   Error: {health_result.get('error', 'Unknown error')}")
        print("\nPlease start Scanner API:")
        print("  docker-compose up -d scanner")
        return
    
    print("✓ Scanner API is running")
    
    # Test 1: Health endpoint load test
    print(f"\n{'='*60}")
    print("Test 1: Health Endpoint Load Test")
    print('='*60)
    health_results = run_load_test(test_health_endpoint, NUM_REQUESTS, CONCURRENT_USERS)
    analyze_results(health_results)
    
    # Test 2: Scan endpoint load test (fewer requests, it's slower)
    print(f"\n{'='*60}")
    print("Test 2: Scan Endpoint Load Test")
    print('='*60)
    scan_results = run_load_test(test_scan_endpoint, 10, 2)  # Fewer requests for scan
    analyze_results(scan_results)
    
    print(f"\n{'='*60}")
    print("✅ Load Testing Complete!")
    print('='*60)

if __name__ == "__main__":
    main()