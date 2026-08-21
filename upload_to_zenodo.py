#!/usr/bin/env python3
"""
Zenodo Deposit & Upload Tool for Robust Portfolio Project
"""

import os
import sys
import json
import argparse
import requests

def upload_zenodo(token=None, sandbox=False, zip_file="zenodo_bundle_v1.0.6.zip", metadata_file="zenodo_bundle_v1.0.6/.zenodo.json"):
    base_url = "https://sandbox.zenodo.org/api" if sandbox else "https://zenodo.org/api"
    
    if not token:
        token = os.environ.get("ZENODO_TOKEN")
    
    if not token:
        print("[-] Error: No Zenodo Personal Access Token provided.")
        print("    You can provide it via:")
        print("    1. Environment variable: export ZENODO_TOKEN='your_token'")
        print("    2. CLI argument: python upload_to_zenodo.py --token YOUR_TOKEN")
        print("\n    To create a token on Zenodo:")
        print("    - Log into https://zenodo.org/account/settings/applications/tokens/new/")
        print("    - Select scopes: 'deposit:actions' and 'deposit:write'")
        print("    - Copy the generated token.")
        return False

    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"[*] Connecting to Zenodo API ({'Sandbox' if sandbox else 'Production'})...")
    
    # 1. Load metadata
    if not os.path.exists(metadata_file):
        print(f"[-] Error: Metadata file {metadata_file} not found.")
        return False
    
    with open(metadata_file, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    # 2. Create deposition
    print("[*] Creating new deposition draft...")
    r = requests.post(
        f"{base_url}/deposit/depositions",
        params={"access_token": token} if not headers.get("Authorization") else {},
        headers={"Content-Type": "application/json", **headers},
        json={"metadata": metadata}
    )
    
    if r.status_code not in (200, 201):
        print(f"[-] Failed to create deposition: {r.status_code} - {r.text}")
        return False
    
    deposition = r.json()
    deposition_id = deposition["id"]
    bucket_url = deposition["links"]["bucket"]
    html_url = deposition["links"]["html"]
    prereserve_doi = deposition.get("metadata", {}).get("prereserve_doi", {}).get("doi", "N/A")
    
    print(f"[+] Deposition created successfully!")
    print(f"    - ID: {deposition_id}")
    print(f"    - Pre-reserved DOI: {prereserve_doi}")
    print(f"    - Web link: {html_url}")
    
    # 3. Upload file to bucket
    if not os.path.exists(zip_file):
        print(f"[-] Error: Zip archive {zip_file} not found.")
        return False
    
    filename = os.path.basename(zip_file)
    file_size = os.path.getsize(zip_file)
    print(f"[*] Uploading {filename} ({file_size / (1024*1024):.2f} MB) to bucket...")
    
    with open(zip_file, "rb") as fp:
        upload_r = requests.put(
            f"{bucket_url}/{filename}",
            data=fp,
            headers=headers
        )
    
    if upload_r.status_code not in (200, 201):
        print(f"[-] File upload failed: {upload_r.status_code} - {upload_r.text}")
        return False
    
    print(f"[+] Archive {filename} uploaded successfully!")
    
    print("\n" + "="*60)
    print(">>> ZENODO DEPOSIT DRAFT CREATED & FILES UPLOADED <<<")
    print(f"Deposition URL: {html_url}")
    print(f"DOI (Pre-reserved): {prereserve_doi}")
    print("="*60)
    print("Next step:")
    print(f"1. Open {html_url} to review your metadata and files.")
    print("2. Click 'Publish' on the Zenodo web interface to mint the DOI and make it permanently public.")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload dataset and code bundle to Zenodo")
    parser.add_argument("--token", help="Zenodo Personal Access Token", default=None)
    parser.add_argument("--sandbox", action="store_true", help="Use Zenodo sandbox environment")
    parser.add_argument("--zip", help="Path to zip bundle", default="zenodo_bundle_v1.0.6.zip")
    
    args = parser.parse_args()
    upload_zenodo(token=args.token, sandbox=args.sandbox, zip_file=args.zip)
