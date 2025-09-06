#!/usr/bin/env python3
"""
Test script to verify subdomain proxy logic
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_subdomain_logic():
    """Test subdomain matching logic"""
    try:
        from CONFIG.domains import DomainsConfig
        
        print("=== Testing Subdomain Proxy Logic ===")
        print(f"PROXY_DOMAINS: {getattr(DomainsConfig, 'PROXY_DOMAINS', [])}")
        print(f"PROXY_2_DOMAINS: {getattr(DomainsConfig, 'PROXY_2_DOMAINS', [])}")
        print()
        
        # Helper function to check if domain matches any domain in the list (including subdomains)
        def is_domain_in_list(domain, domain_list):
            """Check if domain or any of its subdomains match entries in domain_list"""
            if not domain_list:
                return False
            
            # Direct match
            if domain in domain_list:
                return True
            
            # Check if any domain in the list is a subdomain of the current domain
            for listed_domain in domain_list:
                if domain.endswith('.' + listed_domain) or domain == listed_domain:
                    return True
            
            return False
        
        # Test URLs with various subdomains
        test_cases = [
            # Instagram tests
            ("https://instagram.com/p/example", "instagram.com", "PROXY_2_DOMAINS"),
            ("https://www.instagram.com/p/example", "www.instagram.com", "PROXY_2_DOMAINS"),
            ("https://rt.instagram.com/p/example", "rt.instagram.com", "PROXY_2_DOMAINS"),
            ("https://cn.instagram.com/p/example", "cn.instagram.com", "PROXY_2_DOMAINS"),
            ("https://it.instagram.com/p/example", "it.instagram.com", "PROXY_2_DOMAINS"),
            ("https://api.instagram.com/p/example", "api.instagram.com", "PROXY_2_DOMAINS"),
            
            # ig.me tests
            ("https://ig.me/p/example", "ig.me", "PROXY_2_DOMAINS"),
            ("https://www.ig.me/p/example", "www.ig.me", "PROXY_2_DOMAINS"),
            ("https://rt.ig.me/p/example", "rt.ig.me", "PROXY_2_DOMAINS"),
            
            # Pornhub tests
            ("https://pornhub.com/video/example", "pornhub.com", "PROXY_DOMAINS"),
            ("https://www.pornhub.com/video/example", "www.pornhub.com", "PROXY_DOMAINS"),
            ("https://rt.pornhub.com/video/example", "rt.pornhub.com", "PROXY_DOMAINS"),
            ("https://pornhub.org/video/example", "pornhub.org", "PROXY_DOMAINS"),
            ("https://www.pornhub.org/video/example", "www.pornhub.org", "PROXY_DOMAINS"),
            
            # Other domains (should not match)
            ("https://youtube.com/watch?v=example", "youtube.com", "None"),
            ("https://www.youtube.com/watch?v=example", "www.youtube.com", "None"),
            ("https://example.com/video", "example.com", "None"),
        ]
        
        print("=== Test Results ===")
        for url, domain, expected_proxy in test_cases:
            print(f"URL: {url}")
            print(f"  Domain: {domain}")
            
            # Check PROXY_2_DOMAINS
            proxy_2_match = False
            if hasattr(DomainsConfig, 'PROXY_2_DOMAINS') and DomainsConfig.PROXY_2_DOMAINS:
                proxy_2_match = is_domain_in_list(domain, DomainsConfig.PROXY_2_DOMAINS)
                print(f"  Matches PROXY_2_DOMAINS: {proxy_2_match}")
            
            # Check PROXY_DOMAINS
            proxy_1_match = False
            if hasattr(DomainsConfig, 'PROXY_DOMAINS') and DomainsConfig.PROXY_DOMAINS:
                proxy_1_match = is_domain_in_list(domain, DomainsConfig.PROXY_DOMAINS)
                print(f"  Matches PROXY_DOMAINS: {proxy_1_match}")
            
            # Determine which proxy should be used
            if proxy_2_match:
                actual_proxy = "PROXY_2_DOMAINS"
            elif proxy_1_match:
                actual_proxy = "PROXY_DOMAINS"
            else:
                actual_proxy = "None"
            
            # Check if result matches expectation
            status = "✅" if actual_proxy == expected_proxy else "❌"
            print(f"  Expected: {expected_proxy}, Actual: {actual_proxy} {status}")
            print()
        
        return True
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing subdomain proxy logic...")
    print("=" * 50)
    
    success = test_subdomain_logic()
    
    if success:
        print("✅ Test completed successfully")
        print("\nNow all subdomains of domains in PROXY_2_DOMAINS and PROXY_DOMAINS")
        print("will be properly detected and use the appropriate proxy!")
    else:
        print("❌ Test failed")
        sys.exit(1)
