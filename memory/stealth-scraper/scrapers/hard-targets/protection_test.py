#!/usr/bin/env python3
"""
Protection analysis for RISE Manhattan and Curaleaf NYC
Testing different approaches to understand their defenses
"""

import requests
import time
from playwright.sync_api import sync_playwright
import json

def test_basic_fetch():
    """Test basic requests to both sites"""
    sites = {
        "RISE Manhattan": "https://risecannabis.com",
        "Curaleaf NYC": "https://curaleaf.com"
    }
    
    results = {}
    
    for name, url in sites.items():
        print(f"\n=== {name} ===")
        try:
            response = requests.get(url, timeout=10)
            results[name] = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content_length": len(response.content),
                "url": response.url,
                "success": response.status_code == 200
            }
            print(f"Status: {response.status_code}")
            print(f"Final URL: {response.url}")
            print(f"Content-Length: {len(response.content)}")
            
            # Check for Cloudflare
            if 'cf-ray' in response.headers:
                print("✓ Cloudflare detected")
            
            # Check for protection indicators
            if response.status_code == 403:
                print("🚫 403 Forbidden - likely bot protection")
            elif response.status_code in [307, 302]:
                print(f"🔀 Redirect to: {response.url}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            results[name] = {"error": str(e), "success": False}
    
    return results

def test_playwright_stealth():
    """Test both sites with Playwright stealth mode"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        page = context.new_page()
        
        sites = {
            "RISE Manhattan": "https://risecannabis.com",
            "Curaleaf NYC": "https://curaleaf.com"
        }
        
        results = {}
        
        for name, url in sites.items():
            print(f"\n=== Playwright test: {name} ===")
            try:
                response = page.goto(url, wait_until='load', timeout=30000)
                
                # Wait a bit to see if we get challenged
                page.wait_for_timeout(3000)
                
                current_url = page.url
                title = page.title()
                
                results[name] = {
                    "initial_status": response.status if response else None,
                    "final_url": current_url,
                    "title": title,
                    "success": response and response.status == 200
                }
                
                print(f"Status: {response.status if response else 'None'}")
                print(f"Final URL: {current_url}")
                print(f"Title: {title}")
                
                # Check for specific challenge indicators
                content = page.content()
                if "cloudflare" in content.lower():
                    print("🔒 Cloudflare challenge detected")
                if "checking your browser" in content.lower():
                    print("🔄 Browser check in progress")
                
                # Save screenshot for analysis
                screenshot_path = f"/tmp/{name.lower().replace(' ', '_')}_screenshot.png"
                page.screenshot(path=screenshot_path)
                print(f"📸 Screenshot saved: {screenshot_path}")
                
            except Exception as e:
                print(f"❌ Error: {e}")
                results[name] = {"error": str(e), "success": False}
        
        browser.close()
        return results

if __name__ == "__main__":
    print("=== HARD TARGETS PROTECTION ANALYSIS ===")
    
    print("\n1. Testing basic HTTP requests...")
    basic_results = test_basic_fetch()
    
    print("\n2. Testing with Playwright...")
    playwright_results = test_playwright_stealth()
    
    # Save results
    all_results = {
        "timestamp": time.time(),
        "basic_requests": basic_results,
        "playwright_results": playwright_results
    }
    
    with open("memory/stealth-scraper/scrapers/hard-targets/protection_analysis.json", "w") as f:
        json.dump(all_results, f, indent=2)
    
    print("\n=== SUMMARY ===")
    print(f"Results saved to: memory/stealth-scraper/scrapers/hard-targets/protection_analysis.json")
    
    for site in ["RISE Manhattan", "Curaleaf NYC"]:
        print(f"\n{site}:")
        basic = basic_results.get(site, {})
        playwright = playwright_results.get(site, {})
        
        print(f"  Basic request: {'✓' if basic.get('success') else '✗'}")
        print(f"  Playwright: {'✓' if playwright.get('success') else '✗'}")