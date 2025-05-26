#!/usr/bin/env python3
"""
Simple script to fetch the latest shuttle bus location for Sungkyunkwan University
"""

import requests
import json

def get_shuttle_bus_location():
    url = "http://route.hellobus.co.kr:8787/pub/routeView/skku/getSkkuLoc.aspx"
    
    try:
        # Request data from the URL
        response = requests.get(url)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the JSON response
            data = response.json()
            return data
        else:
            print(f"Error: Received status code {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

if __name__ == "__main__":
    print("Fetching latest Sungkyunkwan University shuttle bus location...")
    bus_data = get_shuttle_bus_location()
    
    if bus_data:
        print("\nLatest shuttle bus information:")
        print(json.dumps(bus_data, indent=2, ensure_ascii=False))
    else:
        print("Failed to retrieve shuttle bus information.")