#!/usr/bin/env python
"""
ImageZebra Analysis API Example

Demonstrates the core workflow for uploading images and retrieving analysis results:
1. Authenticate with application key + user credentials to obtain a bearer token
2. Request a presigned URL for S3 upload
3. Upload the image to S3
4. Request analysis of the uploaded image
5. Poll for and display analysis results

Usage:
    uv run analysis_example.py [image_path]
"""
import argparse
import logging

from dotenv import load_dotenv

from iz_client import IZClient, upload_and_analyze, get_analysis_results

logging.basicConfig(level=logging.INFO)
load_dotenv()


def main():
    parser = argparse.ArgumentParser(description='Upload an image to ImageZebra for analysis.')
    parser.add_argument(
        'image_path',
        nargs='?',
        default='images/low_res_GT_A.jpg',
        help='Path to the image file (default: images/low_res_GT_A.jpg)'
    )
    args = parser.parse_args()

    client = IZClient()

    user_data = client.get('/user-data')
    tier_name = user_data['tierName']
    print(f'User is on the {tier_name} tier of service')
    if tier_name and tier_name.lower() == 'platinum':
        print('User has no restrictions on uploads as a platinum tier subscriber (API rate limits apply)')
    else:
        print(f'User has {user_data["analysisBalance"]} remaining uploads this billing period')

    upload_id = upload_and_analyze(client, args.image_path)

    get_analysis_results(client, upload_id)


if __name__ == '__main__':
    main()
