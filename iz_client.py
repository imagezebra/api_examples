"""
Shared ImageZebra API client and helper functions.

Provides authenticated access to the ImageZebra API, image upload via S3
presigned URLs, and polling for analysis results.
"""
import logging
import os
from enum import StrEnum
from pathlib import Path
from time import sleep

import requests

logger = logging.getLogger(__name__)

BASE_URL = 'https://imagezebra.com/api'


class TargetType(StrEnum):
    """Supported color target types."""
    GOLDEN_THREAD_OBJECT_LEVEL = "golden_thread_object_level"
    GOLDEN_THREAD_DEVICE_LEVEL = "golden_thread_device_level"
    COLOR_CHECKER_CLASSIC = "color_checker_classic"
    COLOR_CHECKER_SG = "color_checker_sg"
    DT_NEXT_GEN_2 = "dt_next_gen_2"
    FADGI_19264 = "fadgi_19264"
    REZ_CHECKER = "rez_checker"


class IZClient:
    """Authenticated client for the ImageZebra API."""

    def __init__(
        self,
        application_key: str = None,
        username: str = None,
        password: str = None,
    ):
        """Authenticate and store bearer token for subsequent requests."""
        application_key = application_key or os.getenv('IMAGEZEBRA_APPLICATION_KEY')
        username = username or os.getenv('IMAGEZEBRA_USERNAME')
        password = password or os.getenv('IMAGEZEBRA_PASSWORD')
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
        if response.status_code == 204:
            return None
        return response.json()

    def get(self, path: str, **kwargs):
        return self._request('GET', path, **kwargs)

    def post(self, path: str, **kwargs):
        return self._request('POST', path, **kwargs)

    def delete(self, path: str, **kwargs):
        return self._request('DELETE', path, **kwargs)


def upload_and_analyze(client: IZClient, image_path: str, target_id: str = None) -> str:
    """
    Upload an image and request analysis.

    Args:
        target_id: Optional target library ID. If omitted, the target type is
                   auto-detected from the image.

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
    params = {'target_id': target_id} if target_id else {}
    client.post(f'/requests-for-analysis/{presigned_url_response["uploadId"]}', params=params)
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
