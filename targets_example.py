#!/usr/bin/env python
"""
ImageZebra Targets API Example

Demonstrates target library management and using a target for image analysis:
1. List existing targets in the library
2. Check whether a matching target already exists
3. Create a new target only if needed
4. Upload an image and analyze it using that target
5. Display the analysis results
6. Clean up the target

Usage:
    uv run targets_example.py [image_path]
"""
import argparse
import logging

from dotenv import load_dotenv

from iz_client import IZClient, TargetType, upload_and_analyze, get_analysis_results

logging.basicConfig(level=logging.INFO)
load_dotenv()

TARGET_NAME = 'Example Golden Thread'
TARGET_TYPE = TargetType.GOLDEN_THREAD_DEVICE_LEVEL
REFERENCE_DATA_SOURCE = 'target_type_defaults'


def find_matching_target(targets, name):
    """Find an existing target that matches by name."""
    for target in targets:
        if target['name'] == name:
            return target
    return None


def main():
    parser = argparse.ArgumentParser(description='Demonstrate target library and target-based analysis.')
    parser.add_argument(
        'image_path',
        nargs='?',
        default='images/low_res_GT_A.jpg',
        help='Path to the image file (default: images/low_res_GT_A.jpg)',
    )
    args = parser.parse_args()

    client = IZClient()

    # List all targets in the library
    response = client.get('/targets')
    targets = response['targets']
    print(f'Found {len(targets)} existing target(s) in library:')
    for t in targets:
        print(f'  - {t["name"]} (type: {t["targetType"]}, id: {t["id"]})')

    # Check whether a matching target already exists
    created = False
    existing = find_matching_target(targets, TARGET_NAME)
    if existing:
        target = existing
        print(f'\nUsing existing target: {target["name"]} (id: {target["id"]})')
    else:
        print(f'\nNo existing target matches name={TARGET_NAME!r}. Creating one.')
        target = client.post('/targets', json={
            'name': TARGET_NAME,
            'targetType': TARGET_TYPE,
            'referenceDataSource': REFERENCE_DATA_SOURCE,
        })
        created = True
        print(f'Created target: {target["name"]} (id: {target["id"]})')

    # Upload an image and request analysis using the target
    upload_id = upload_and_analyze(client, args.image_path, target_id=target['id'])

    # Poll for and display results
    get_analysis_results(client, upload_id)

    # Clean up only if we created the target in this run
    if created:
        client.delete(f'/targets/{target["id"]}')
        print(f'\nDeleted target {target["id"]}')


if __name__ == '__main__':
    main()