#!/usr/bin/env python3

import argparse
import logging
import re
import requests
import time
import datetime
import json

requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

SPACELIFT_PUBLIC_API="https://app.spacelift.io"

def authenticate(base_url, api_key_id, api_key_secret, skip_tls_verification):
    GET_API_TOKEN_QUERY = f"""
    mutation GetToken {{
    apiKeyUser(id: "{api_key_id}", secret: "{api_key_secret}") {{
        jwt
    }}
    }}
    """
    response = requests.post(f"{base_url}/graphql", json={"query": GET_API_TOKEN_QUERY}, verify=not skip_tls_verification)
    response.raise_for_status()
    data = response.json()
    return data.get("data", {}).get("apiKeyUser", {}).get("jwt", "")

def get_presigned_url(object_key):
    response = requests.get(f"{SPACELIFT_PUBLIC_API}/selfhosted/metrics/upload_url?object_key={object_key}")
    response.raise_for_status()
    return response.json()

def file_path(usage_data):
    account_ulid = usage_data.get('account',{}).get('ulid',"")
    account_ulid = account_ulid if account_ulid else "unknown_ulid"
    license_id = usage_data.get('account',{}).get('license_id',"")
    license_id = license_id if license_id else "unknown_license_id"
    name = file_name(usage_data)
    return f"{account_ulid}/{license_id}/{name}"

def file_name(usage_data):
    time_range = usage_data.get('time_range',{})
    start = time_range.get('start',"")
    # extract date part
    start = start if len(start) < 10 else start[:10]
    end = time_range.get('end',"")
    end = end if len(end) < 10 else end[:10]
    return f"usage_data_{start}_{end}.json"

def save(usage_data):
    with open(file_name(usage_data), "w") as f:
        json.dump(usage_data, f)

def send(usage_data):
    presigned = get_presigned_url(file_path(usage_data))
    presigned_url = presigned.get("URL")
    presigned_headers = presigned.get("Headers")
    response = requests.put(presigned_url, headers=presigned_headers, json=usage_data)
    response.raise_for_status()

def handle_response(response, send_to_spacelift):
    response.raise_for_status()
    usage_data = response.json()
    if not send_to_spacelift:
        save(usage_data)
        return
    
    logging.info("Sending data to Spacelift")
    send(usage_data)

def validate_date(date_str):
    match = re.match(r"\d{4}-\d{2}-\d{2}", date_str)
    if not match:
        raise ValueError(f"Invalid date format: {date_str}, expected format: YYYY-MM-DD")

def export_single(base_url, api_key_id, api_key_secret, current_start, current_end, skip_tls_verification, send_to_spacelift):
    url = f"{base_url}/selfhosted/metrics?start_timestamp={current_start}&end_timestamp={current_end}"
    try:
        logging.info("Requesting API Token")
        token = authenticate(base_url, api_key_id, api_key_secret, skip_tls_verification)
        logging.info("API Token received")
        
        logging.info(f"Requesting data since {datetime.datetime.fromtimestamp(current_start, tz=datetime.timezone.utc)} until {datetime.datetime.fromtimestamp(current_end, tz=datetime.timezone.utc)}")
        response = requests.get(url, headers={"Authorization": f"Bearer {token}"}, verify=not skip_tls_verification)
        logging.info("Data received")
        
        handle_response(response, send_to_spacelift)
        response.raise_for_status()
        logging.info("Data processed")
        
    except requests.RequestException as e:
        logging.error(f"Request error: {e}")

def export(base_url, api_key_id, api_key_secret, start_date_str, end_date_str, batch_days, skip_tls_verification, send_to_spacelift):
    try:
        validate_date(start_date_str)
        validate_date(end_date_str)
        # Convert input dates to datetime then to a timestamp
        date_format = "%Y-%m-%d"
        start_timestamp = int(datetime.datetime.strptime(start_date_str, date_format).replace(tzinfo=datetime.timezone.utc).timestamp())
        end_timestamp = int(datetime.datetime.strptime(end_date_str, date_format).replace(tzinfo=datetime.timezone.utc).timestamp())
    except ValueError as e:
        logging.error(f"Invalid date: {e}")
        return

    current_start = start_timestamp

    while current_start < end_timestamp:
        current_end = current_start + (batch_days * 24 * 60 * 60)
        if current_end > end_timestamp:
            current_end = end_timestamp

        export_single(base_url, api_key_id, api_key_secret, current_start, current_end, skip_tls_verification, send_to_spacelift)

        # Move to the next batch
        current_start = current_end

def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

def main():
    setup_logger()
    
    parser = argparse.ArgumentParser(
                    prog='Usage data exporter',
                    description='Exports usage data from selfhosted Spacelift instance')
    # required
    parser.add_argument('--base-url', required=True, help="Base URL of your Spacelift instance e.g. `https://spacelift.companyname.com`")
    parser.add_argument('--api-key-id', required=True, help="API key Id used for export purposes. Requires admin permissions")
    parser.add_argument('--api-key-secret', required=True, help="API key secret used for export purposes. Requires admin permissions")
    parser.add_argument('--start-date', required=True, help="Export start date, format: YYYY-MM-DD")
    parser.add_argument('--end-date', required=True, help="Export end date, this day is not included in the exported data, format: YYYY-MM-DD")
    
    # optional
    parser.add_argument('--batch-size', default=7, type=int, help="Number of days to export in a single batch")
    parser.add_argument('--skip-tls-verification', action='store_true', help="Skip TLS verification")
    parser.add_argument('--send-to-spacelift', action='store_true', help="Send data directly to Spacelift instead of saving it locally")
    args = parser.parse_args()

    export(args.base_url, args.api_key_id, args.api_key_secret, args.start_date, args.end_date, args.batch_size, args.skip_tls_verification, args.send_to_spacelift)

if __name__ == "__main__":
    main()