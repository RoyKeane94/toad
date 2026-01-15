#!/usr/bin/env python3
"""
Script to generate SRI (Subresource Integrity) hashes for CDN resources.
Run this script to get the correct integrity hashes for your CDN scripts and stylesheets.

Usage:
    python generate_sri_hashes.py
"""

import hashlib
import base64
import urllib.request
import ssl
import sys

def calculate_sri_hash(url, algorithm='sha384'):
    """
    Calculate SRI hash for a given URL.
    
    Args:
        url: The URL of the resource
        algorithm: Hash algorithm (sha256, sha384, or sha512)
    
    Returns:
        The base64-encoded hash
    """
    try:
        print(f"Fetching {url}...")
        # Create SSL context that doesn't verify certificates (for local development)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, context=ssl_context) as response:
            content = response.read()
        
        if algorithm == 'sha256':
            hash_obj = hashlib.sha256(content)
        elif algorithm == 'sha384':
            hash_obj = hashlib.sha384(content)
        elif algorithm == 'sha512':
            hash_obj = hashlib.sha512(content)
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
        
        hash_b64 = base64.b64encode(hash_obj.digest()).decode('utf-8')
        return hash_b64
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def main():
    """Generate SRI hashes for all CDN resources."""
    
    resources = [
        {
            'url': 'https://cdn.jsdelivr.net/npm/htmx.org@1.9.10/dist/htmx.min.js',
            'type': 'script',
            'name': 'HTMX'
        },
        {
            'url': 'https://cdn.jsdelivr.net/npm/hyperscript.org@0.9.12/dist/_hyperscript.min.js',
            'type': 'script',
            'name': 'Hyperscript'
        },
        {
            'url': 'https://cdnjs.cloudflare.com/ajax/libs/Sortable/1.15.0/Sortable.min.js',
            'type': 'script',
            'name': 'SortableJS'
        },
        {
            'url': 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css',
            'type': 'stylesheet',
            'name': 'Font Awesome'
        },
        {
            'url': 'https://cdn.jsdelivr.net/npm/chart.js',
            'type': 'script',
            'name': 'Chart.js'
        },
    ]
    
    print("=" * 80)
    print("SRI Hash Generator for CDN Resources")
    print("=" * 80)
    print()
    
    results = []
    
    for resource in resources:
        hash_value = calculate_sri_hash(resource['url'], 'sha384')
        if hash_value:
            results.append({
                'name': resource['name'],
                'url': resource['url'],
                'type': resource['type'],
                'hash': hash_value
            })
            print(f"✓ {resource['name']}: {hash_value}")
        else:
            print(f"✗ {resource['name']}: Failed to generate hash")
        print()
    
    print("=" * 80)
    print("HTML Usage:")
    print("=" * 80)
    print()
    
    for result in results:
        if result['type'] == 'script':
            print(f"<!-- {result['name']} -->")
            print(f'<script src="{result["url"]}" '
                  f'integrity="sha384-{result["hash"]}" '
                  f'crossorigin="anonymous"></script>')
        elif result['type'] == 'stylesheet':
            print(f"<!-- {result['name']} -->")
            print(f'<link rel="stylesheet" href="{result["url"]}" '
                  f'integrity="sha384-{result["hash"]}" '
                  f'crossorigin="anonymous">')
        print()

if __name__ == '__main__':
    main()

