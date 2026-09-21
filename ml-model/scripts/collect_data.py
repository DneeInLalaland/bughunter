import requests
import json
import pandas as pd
import time
from datetime import datetime

class NVDDataCollector:
    """
    Download vulnerability data from NVD (National Vulnerability Database)
    API Documentation: https://nvd.nist.gov/developers/vulnerabilities
    """
    
    def __init__(self, api_key=None):
        self.base_url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
        self.api_key = api_key
        self.headers = {}
        if api_key:
            # Try different header formats
            self.headers = {
                'apiKey': api_key,
                'Accept': 'application/json'
            }
            print(f"✅ API Key configured: {api_key[:10]}...")
    
    def fetch_cves(self, start_date, end_date, results_per_page=2000):
        """
        Fetch CVE data for a specific date range
        
        Args:
            start_date (str): Start date (YYYY-MM-DD)
            end_date (str): End date (YYYY-MM-DD)
            results_per_page (int): Number of results per page
            
        Returns:
            list: List of CVE data
        """
        all_cves = []
        start_index = 0
        
        print(f"Fetching CVEs from {start_date} to {end_date}...")
        
        while True:
            # Build URL with query parameters
            url = f"{self.base_url}?pubStartDate={start_date}T00:00:00.000&pubEndDate={end_date}T23:59:59.999&resultsPerPage={results_per_page}&startIndex={start_index}"
            
            # Add API key to URL if available
            if self.api_key:
                url += f"&apiKey={self.api_key}"
            
            print(f"DEBUG: Requesting: {url[:100]}...")
            
            try:
                response = requests.get(url, timeout=30)
                
                print(f"DEBUG: Status code: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    vulnerabilities = data.get('vulnerabilities', [])
                    
                    if not vulnerabilities:
                        print("No more results.")
                        break
                    
                    all_cves.extend(vulnerabilities)
                    print(f"Fetched {len(all_cves)} CVEs so far...")
                    
                    # Check if there are more pages
                    total_results = data.get('totalResults', 0)
                    if start_index + results_per_page >= total_results:
                        break
                    
                    start_index += results_per_page
                    
                    # Rate limiting: 5 requests/30 seconds (without API key)
                    # or 50 requests/30 seconds (with API key)
                    time.sleep(6 if not self.api_key else 0.6)
                    
                else:
                    print(f"Error: {response.status_code}")
                    print(f"Response: {response.text[:200]}")
                    break
                    
            except Exception as e:
                print(f"Exception occurred: {e}")
                import traceback
                traceback.print_exc()
                break
        
        print(f"Total CVEs fetched: {len(all_cves)}")
        return all_cves
    
    def parse_cve(self, cve_data):
        """
        Parse CVE data into a clean dictionary format
        
        Args:
            cve_data (dict): Raw CVE data from API
            
        Returns:
            dict: Parsed CVE information
        """
        cve = cve_data.get('cve', {})
        
        # Extract CVE ID
        cve_id = cve.get('id', 'N/A')
        
        # Extract description
        descriptions = cve.get('descriptions', [])
        description = descriptions[0].get('value', '') if descriptions else ''
        
        # Extract CVSS scores
        metrics = cve.get('metrics', {})
        
        # Try CVSS v3.1 first
        cvss_v31 = metrics.get('cvssMetricV31', [])
        if cvss_v31:
            cvss_data = cvss_v31[0].get('cvssData', {})
            base_score = cvss_data.get('baseScore', 0)
            base_severity = cvss_data.get('baseSeverity', 'NONE')
            exploitability_score = cvss_v31[0].get('exploitabilityScore', 0)
            impact_score = cvss_v31[0].get('impactScore', 0)
            attack_vector = cvss_data.get('attackVector', 'UNKNOWN')
            attack_complexity = cvss_data.get('attackComplexity', 'UNKNOWN')
            privileges_required = cvss_data.get('privilegesRequired', 'UNKNOWN')
            user_interaction = cvss_data.get('userInteraction', 'UNKNOWN')
        else:
            # Try CVSS v3.0 if v3.1 not available
            cvss_v30 = metrics.get('cvssMetricV30', [])
            if cvss_v30:
                cvss_data = cvss_v30[0].get('cvssData', {})
                base_score = cvss_data.get('baseScore', 0)
                base_severity = cvss_data.get('baseSeverity', 'NONE')
                exploitability_score = cvss_v30[0].get('exploitabilityScore', 0)
                impact_score = cvss_v30[0].get('impactScore', 0)
                attack_vector = cvss_data.get('attackVector', 'UNKNOWN')
                attack_complexity = cvss_data.get('attackComplexity', 'UNKNOWN')
                privileges_required = cvss_data.get('privilegesRequired', 'UNKNOWN')
                user_interaction = cvss_data.get('userInteraction', 'UNKNOWN')
            else:
                # No CVSS data available
                base_score = 0
                base_severity = 'NONE'
                exploitability_score = 0
                impact_score = 0
                attack_vector = 'UNKNOWN'
                attack_complexity = 'UNKNOWN'
                privileges_required = 'UNKNOWN'
                user_interaction = 'UNKNOWN'
        
        # Extract publish date
        published = cve.get('published', '')
        
        # Extract CWE (weakness type)
        weaknesses = cve.get('weaknesses', [])
        cwe_ids = []
        if weaknesses:
            for weakness in weaknesses:
                descriptions = weakness.get('description', [])
                for desc in descriptions:
                    if desc.get('lang') == 'en':
                        cwe_ids.append(desc.get('value', ''))
        cwe_id = cwe_ids[0] if cwe_ids else 'N/A'
        
        return {
            'cve_id': cve_id,
            'description': description,
            'cvss_base_score': base_score,
            'cvss_severity': base_severity,
            'exploitability_score': exploitability_score,
            'impact_score': impact_score,
            'attack_vector': attack_vector,
            'attack_complexity': attack_complexity,
            'privileges_required': privileges_required,
            'user_interaction': user_interaction,
            'cwe_id': cwe_id,
            'published_date': published
        }
    
    def collect_and_save(self, start_year, end_year, output_file):
        """
        Collect data for multiple years and save as CSV
        
        Args:
            start_year (int): Start year
            end_year (int): End year
            output_file (str): Output filename
        """
        all_parsed_cves = []
        
        for year in range(start_year, end_year + 1):
            print(f"\n{'='*60}")
            print(f"Collecting data for year {year}...")
            print(f"{'='*60}\n")
            
            start_date = f"{year}-01-01"
            end_date = f"{year}-12-31"
            
            cves = self.fetch_cves(start_date, end_date)
            
            # Parse each CVE
            for cve_data in cves:
                parsed = self.parse_cve(cve_data)
                all_parsed_cves.append(parsed)
            
            print(f"Year {year}: {len(cves)} CVEs collected")
        
        # Convert to DataFrame
        df = pd.DataFrame(all_parsed_cves)
        
        # Save as CSV
        df.to_csv(output_file, index=False)
        print(f"\n✅ Data saved to {output_file}")
        print(f"Total records: {len(df)}")
           # Display summary
        if len(df) > 0:
            print(f"\nDataset Summary:")
            print(f"  Total CVEs: {len(df)}")
            print(f"  Date range: {df['published_date'].min()} to {df['published_date'].max()}")
            print(f"  CVSS score range: {df['cvss_base_score'].min():.1f} - {df['cvss_base_score'].max():.1f}")
            print(f"\nSeverity distribution:")
            print(df['cvss_severity'].value_counts())
        else:
            print("\n⚠️  No data collected. Please check your API key and date range.")


# Main execution
if __name__ == "__main__":
    # Insert your API key here
    API_KEY = "7051000a-ef67-40b8-a10c-aff490251335"
    
    collector = NVDDataCollector(api_key=API_KEY)
    
    # Test with just one day first
    print("\n🧪 Testing with one day of data first...")
    collector.collect_and_save(
        start_year=2024,
        end_year=2024,
        output_file='data/raw/nvd_vulnerabilities.csv'
    )
    
    print("\n🎉 Test completed!")
    print("\nIf this works, change start_year to 2020 for full data collection.")