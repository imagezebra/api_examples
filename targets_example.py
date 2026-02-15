#!/usr/bin/env python
"""
ImageZebra Targets API Example

Demonstrates target library management and using a target for image analysis:
1. Create a target in the library
2. Upload an image and analyze it using that target
3. Display the analysis results
4. Clean up the target

Usage:
    uv run targets_example.py [image_path]
"""
import argparse
import logging
import os
from logging import getLogger

from dotenv import load_dotenv

from main import IZClient, upload_and_analyze, get_analysis_results

logging.basicConfig(level=logging.INFO)
logger = getLogger(__name__)

load_dotenv()


def main():
    parser = argparse.ArgumentParser(description='Demonstrate target library and target-based analysis.')
    parser.add_argument(
        'image_path',
        nargs='?',
        default='images/low_res_GT_A.jpg',
        help='Path to the image file (default: images/low_res_GT_A.jpg)',
    )
    args = parser.parse_args()

    client = IZClient(
        application_key=os.getenv('IMAGEZEBRA_APPLICATION_KEY'),
        username=os.getenv('IMAGEZEBRA_USERNAME'),
        password=os.getenv('IMAGEZEBRA_PASSWORD'),
    )

    # Create a target in the library
    target = client.post('/targets', json={
        'name': 'Example Golden Thread',
        'targetType': 'golden_thread_device_level',
        'referenceDataSource': 'target_type_defaults',
    })
    target_id = target['id']
    print(f'Created target: {target["name"]} (id: {target_id})')

    # Upload an image and request analysis using the target
    upload_id = upload_and_analyze(client, args.image_path, target_id=target_id)

    # Poll for and display results
    get_analysis_results(client, upload_id)

    # Clean up
    client.delete(f'/targets/{target_id}')
    print(f'\nDeleted target {target_id}')


if __name__ == '__main__':
    main()