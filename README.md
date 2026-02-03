# ImageZebra API Example

A minimal example demonstrating the ImageZebra image analysis API workflow.

## Setup

1. Install dependencies:
   ```bash
   uv sync
   ```

2. Create a `.env` file with your credentials:
   ```
   IMAGEZEBRA_APPLICATION_KEY=your_application_key
   IMAGEZEBRA_USERNAME=account_username
   IMAGEZEBRA_PASSWORD=account_password
   ```

## Usage

```bash
uv run main.py [image_path]
```

If no image path is provided, defaults to `images/low_res_GT_A.jpg`.

## Workflow

The script demonstrates the complete analysis workflow:

1. **Authentication** - Exchange credentials for a bearer token via `/token`
2. **Presigned URL** - Request an S3 presigned POST URL via `/presigned-urls/{filename}`
3. **Upload** - POST the image to S3 using the presigned URL fields
4. **Request Analysis** - Trigger analysis via `/requests-for-analysis/{upload_id}`
5. **Poll Results** - Poll `/upload-results-summary/{upload_id}` until analysis completes

## API Endpoints Used

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/token` | POST | Authenticate and obtain bearer token |
| `/presigned-urls/{filename}` | GET | Get S3 presigned POST URL for upload |
| `/requests-for-analysis/{upload_id}` | POST | Request analysis of uploaded image |
| `/upload-results-summary/{upload_id}` | GET | Retrieve analysis results |
| `/user-data` | GET | Get user account info (e.g., remaining uploads) |
