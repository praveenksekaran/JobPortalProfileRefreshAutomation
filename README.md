<<<<<<< HEAD
# Job Portal Profile Refresh Automation (Python)

Serverless automation system to periodically update profile fields on job portals (LinkedIn, Naukri, Indeed) to improve recruiter visibility.

## Architecture

- **AWS Lambda**: Serverless execution environment (Python 3.11)
- **AWS EventBridge**: Scheduled triggers
- **AWS Secrets Manager**: Secure credential storage
- **Amazon Bedrock**: AI-powered content mutation
- **AWS SES**: Email notifications
- **Playwright**: Browser automation

## Project Structure

```
.
├── src/
│   ├── lambda_handler.py        # Lambda entry point
│   ├── portals/
│   │   ├── linkedin.py          # LinkedIn automation
│   │   ├── naukri.py            # Naukri automation
│   │   └── indeed.py            # Indeed automation
│   ├── services/
│   │   ├── secrets_manager.py   # Secrets retrieval
│   │   ├── bedrock.py           # AI content mutation
│   │   └── notifications.py     # Email notifications
│   └── utils/
│       ├── logger.py            # Logging utilities
│       └── playwright_helpers.py # Browser automation helpers
├── config/
│   └── config.py                # Configuration management
├── requirements.txt             # Python dependencies
├── setup.py                     # Package setup
└── template.yaml                # AWS SAM template
```

## Setup

### Prerequisites

- AWS Account with appropriate permissions
- Python 3.11 or higher
- AWS CLI configured
- AWS SAM CLI installed

### Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers (for local testing)
python -m playwright install chromium
```

### AWS Resources Setup

1. **Secrets Manager**: Store credentials as JSON:
   ```json
   {
     "linkedin": {
       "email": "your-email@example.com",
       "password": "your-password"
     },
     "naukri": {
       "email": "your-email@example.com",
       "password": "your-password"
     },
     "indeed": {
       "email": "your-email@example.com",
       "password": "your-password"
     },
     "notification_email": "your-email@example.com"
   }
   ```

2. **SES**: Verify sender email address

3. **Lambda**: Create function with:
   - Runtime: Python 3.11
   - Timeout: 5 minutes
   - Memory: 1024 MB
   - Environment variables:
     - `SECRET_NAME`: Name of secret in Secrets Manager
     - `AWS_REGION`: Your AWS region
     - `LOG_LEVEL`: INFO (or DEBUG for troubleshooting)

4. **EventBridge**: Create rule with cron schedule

### Deployment

```bash
# Using deployment script
chmod +x scripts/deploy.sh
./scripts/deploy.sh

# Or manually
sam build
sam deploy --guided
```

## Configuration

Edit `config/config.py` to customize:
- Portal selection (enable/disable)
- Browser behavior settings
- Bedrock model parameters
- Logging levels

## Local Testing

Use this command: python -m src.lambda_handler

```bash
# Set up environment
cp .env.example .env
# Edit .env with your settings

# Run local test
chmod +x scripts/test-local.sh
./scripts/test-local.sh

# Or directly
PYTHONPATH=. python src/lambda_handler.py
```

## Python-Specific Notes

### Dependencies
- **boto3**: AWS SDK for Python
- **playwright**: Browser automation (async API)

### Async/Await
The Python version uses async/await for Playwright operations. The Lambda handler wraps async code using `asyncio.run()`.

### Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

## Troubleshooting

### Import Errors
If you encounter import errors, ensure PYTHONPATH includes the project root:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Playwright Issues
```bash
# Reinstall browsers
python -m playwright install chromium --force

# Check installation
python -m playwright --version
```

### AWS Lambda Layer for Playwright
For deployment, Playwright requires a Lambda layer with Chromium. The SAM template includes a placeholder for this. You can:

1. Use a pre-built layer (search "playwright python lambda layer")
2. Build your own following AWS Lambda layer guidelines
3. Use container images instead (requires Docker)

## Monitoring

```bash
# View logs
aws logs tail /aws/lambda/job-portal-profile-refresh --follow

# Test invocation
aws lambda invoke \
  --function-name job-portal-profile-refresh \
  --payload '{}' \
  response.json && cat response.json
```

## Cost Estimation

Estimated monthly costs (assuming daily execution):
- **Lambda**: ~$0.50
- **Bedrock**: ~$0.15
- **Secrets Manager**: $0.40
- **SES**: Free (first 62,000 emails)
- **CloudWatch**: ~$0.50

**Total**: ~$1.55/month

## Documentation

- **README.md** - This file
- **DEPLOYMENT.md** - Detailed deployment guide
- **ARCHITECTURE.md** - System architecture
- **TESTING.md** - Testing strategies

## License

MIT
=======
# JobPortalProfileRefreshAutomation
>>>>>>> f5f98e21ba8e52f8805ce73bf11759def1c2e035
