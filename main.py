#!/usr/bin/env python
"""
ImageZebra API Example

Demonstrates the core workflow for uploading images and retrieving analysis results:
1. Authenticate with application key + user credentials to obtain a bearer token
2. Request a presigned URL for S3 upload
3. Upload the image to S3
4. Request analysis of the uploaded image
5. Poll for and display analysis results

Usage:
    uv run main.py [image_path]
"""
import argparse
import logging
import os
from logging import getLogger
from pathlib import Path
from time import sleep

import requests
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = getLogger(__name__)

load_dotenv()

BASE_URL = 'https://imagezebra.com/api'


class IZClient:
    """Authenticated client for the ImageZebra API."""

    def __init__(self, application_key: str, username: str, password: str):
        """Authenticate and store bearer token for subsequent requests."""
        response = requests.post(
            f'{BASE_URL}/token',
            json={'username': username, 'password': password},
            headers={'X-Application-Key': application_key},
        )
        response.raise_for_status()
        self.token = response.json()['token']
        self._auth_headers = {
            'Authorization': f'Bearer {self.token}',
            'X-Application-Key': application_key,
        }

    def _request(self, method: str, path: str, **kwargs):
        """Make an authenticated request to the API."""
        headers = {**self._auth_headers, **kwargs.pop('headers', {})}
        response = requests.request(method, f'{BASE_URL}{path}', headers=headers, **kwargs)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            # Attach response body to exception for caller inspection (often contains
            # validation errors or status messages from the API)
            try:
                e.response_content = response.json()
            except requests.exceptions.JSONDecodeError:
                e.response_content = {}
            raise
        return response.json()

    def get(self, path: str, **kwargs):
        return self._request('GET', path, **kwargs)

    def post(self, path: str, **kwargs):
        return self._request('POST', path, **kwargs)


def upload_and_analyze(client: IZClient, image_path: str) -> str:
    """
    Upload an image and request analysis.

    Returns the upload ID for use with get_analysis_results().
    """
    filename = Path(image_path).name
    presigned_url_response = client.get(f'/presigned-urls/{filename}')

    # Upload image to S3 using presigned POST
    fields = presigned_url_response['fields']
    # Map field names to S3 expected format
    form_data = {e['key']: e['value'] for e in fields}

    with open(image_path, 'rb') as f:
        # File must be the last field in the multipart form
        files = {'file': (filename, f, 'image/jpeg')}
        upload_response = requests.post(
            presigned_url_response['url'],
            data=form_data,
            files=files
        )
        upload_response.raise_for_status()
        logger.info(f'Upload successful!')

    logger.info('Requesting analysis')
    client.post(f'/requests-for-analysis/{presigned_url_response["uploadId"]}')
    return presigned_url_response['uploadId']


def get_analysis_results(client: IZClient, upload_id: str) -> None:
    """Poll for analysis completion and print the results summary."""
    while True:
        try:
            logger.info('Requesting summary')
            response = client.get(f'/upload-results-summary/{upload_id}')
            break
        except requests.exceptions.HTTPError as e:
            if e.response_content.get('error') != 'Image analysis not complete':
                raise
            logger.info('Image analysis not complete')
            sleep(5)

    print(f'\nAnalysis for {response["filePath"]}')
    print('*' * 80)
    print(f'Passing quality thresholds: {response["passing"]}')
    print(f'Reference values used: {response["referenceValuesUsed"]}')
    print(f'Specification used: {response["spec"]}')
    print(f'Target type: {response["targetType"]}')

    for metric_group in response['metricGroups']:
        print(f'\n{metric_group["name"]}\n{"-" * 80}')
        for metric in metric_group['metrics']:
            print(f'{metric["name"]:40}{metric["stars"]} stars, passing: {metric["isPassing"]}')


def main():
    parser = argparse.ArgumentParser(description='Upload an image to ImageZebra for analysis.')
    parser.add_argument(
        'image_path',
        nargs='?',
        default='images/low_res_GT_A.jpg',
        help='Path to the image file (default: images/low_res_GT_A.jpg)'
    )
    args = parser.parse_args()

    client = IZClient(
        application_key=os.getenv('IMAGEZEBRA_APPLICATION_KEY'),
        username=os.getenv('IMAGEZEBRA_USERNAME'),
        password=os.getenv('IMAGEZEBRA_PASSWORD')
    )

    user_data = client.get('/user-data')
    print(f'User has {user_data["analysisBalance"]} remaining uploads this billing period')

    upload_id = upload_and_analyze(client, args.image_path)

    get_analysis_results(client, upload_id)


if __name__ == '__main__':
    main()