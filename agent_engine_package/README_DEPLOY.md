# GCP Agent Engine Deployment Guide

This package contains all necessary files for deploying the Voice Stock Analytics Agent to Google Cloud Platform's Agent Engine.

## Package Contents

```
agent_engine_package/
├── manifest.json           # Agent configuration and metadata
├── entrypoint.py          # Main orchestration entry point
├── prompts/               # Agent prompt files
│   ├── data_agent_marketaux_yahoo.prompt
│   ├── calculation_agent.prompt
│   ├── ratio_analysis_agent.prompt
│   ├── valuation_agent.prompt
│   ├── risk_agent.prompt
│   ├── summarization_agent.prompt
│   ├── presentation_agent.prompt
│   ├── voice_agent.prompt
│   ├── infra_agent.prompt
│   ├── fingpt_example.prompt
│   └── gemini_example.prompt
└── README_DEPLOY.md       # This file
```

## Prerequisites

1. Google Cloud Project with billing enabled
2. GCP CLI (`gcloud`) installed and configured
3. Required APIs enabled:
   - Cloud Functions
   - Cloud Run
   - Cloud Logging
   - Secret Manager
   - Speech-to-Text
   - Text-to-Speech
   - Vertex AI (for Gemini)

## Deployment Steps

### 1. Build Deployment Package

```bash
cd agent_engine_package
zip -r agent_engine_bundle.zip *
```

### 2. Upload to GCP Storage

```bash
gsutil mb gs://your-project-stock-analytics-agents
gsutil cp agent_engine_bundle.zip gs://your-project-stock-analytics-agents/
```

### 3. Deploy via GCP Console

1. Navigate to Cloud Functions
2. Create new function
3. Upload `agent_engine_bundle.zip`
4. Set entry point: `main`
5. Set runtime: Python 3.11
6. Configure environment variables (see below)
7. Deploy

### 4. Configure Environment Variables

Required:
```
GEMINI_API_KEY=<your-gemini-key>
MARKETAUX_API_KEY=<your-marketaux-key>
SENTRY_DSN=<your-sentry-dsn>
```

Optional:
```
LOG_LEVEL=INFO
TIMEOUT=300
MAX_WORKERS=10
```

### 5. Set Up Secret Manager

```bash
# Create secrets
echo -n "your-gemini-key" | gcloud secrets create gemini-api-key --data-file=-
echo -n "your-marketaux-key" | gcloud secrets create marketaux-api-key --data-file=-

# Grant access to Cloud Function service account
gcloud secrets add-iam-policy-binding gemini-api-key \
    --member="serviceAccount:YOUR_SERVICE_ACCOUNT@YOUR_PROJECT.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

## Testing the Deployment

### Test Event

```json
{
  "ticker": "AAPL",
  "config": {
    "period": "1y",
    "wacc": 0.10,
    "terminal_growth": 0.025,
    "forecast_years": 5
  }
}
```

### cURL Test

```bash
curl -X POST https://REGION-PROJECT_ID.cloudfunctions.net/stock-analytics \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "config": {
      "period": "1y",
      "wacc": 0.10,
      "terminal_growth": 0.025,
      "forecast_years": 5
    }
  }'
```

## Monitoring

### View Logs

```bash
gcloud functions logs read stock-analytics --limit=50
```

### View Metrics

Navigate to Cloud Console → Monitoring → Metrics Explorer

Key metrics:
- `cloudfunctions.googleapis.com/function/execution_count`
- `cloudfunctions.googleapis.com/function/execution_times`
- `cloudfunctions.googleapis.com/function/user_memory_bytes`

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure all dependencies are in `requirements.txt`
   - Check Python version compatibility (3.11)

2. **Timeout Errors**
   - Increase function timeout (max 540s for Cloud Functions)
   - Consider Cloud Run for longer-running tasks

3. **Memory Issues**
   - Increase memory allocation (max 8GB)
   - Optimize calculation modules

4. **API Rate Limits**
   - Implement exponential backoff
   - Use caching where appropriate

## Scaling Considerations

- **Horizontal Scaling**: Cloud Functions auto-scales
- **Concurrent Executions**: Set max instances to control costs
- **Cold Starts**: Use min instances for critical paths
- **Cost Optimization**: Use Cloud Run for predictable workloads

## Security Best Practices

1. Use Secret Manager for all credentials
2. Enable VPC connector for private resources
3. Implement IAM least privilege
4. Rotate API keys regularly
5. Enable Cloud Armor for DDoS protection
6. Use signed URLs for temporary access

## Support

For issues:
- Check Cloud Logging for errors
- Review Sentry dashboard
- Consult monitoring dashboards
- Contact support team

## License

MIT License - See LICENSE file in root directory
