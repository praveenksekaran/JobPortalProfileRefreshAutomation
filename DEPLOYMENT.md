# Deployment Guide

Complete guide to deploy the Job Portal Profile Refresh Automation system to AWS.

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** installed and configured
3. **AWS SAM CLI** installed (recommended) or CloudFormation
4. **Node.js 18.x** or higher
5. **Portal Credentials** for LinkedIn, Naukri, and Indeed

## Step 1: Prepare Credentials

### 1.1 Create Credentials Secret

Create a secret in AWS Secrets Manager with your portal credentials:

```bash
aws secretsmanager create-secret \
  --name job-portal-credentials \
  --description "Credentials for job portal automation" \
  --secret-string file://secrets.json
```

**secrets.json** format:
```json
{
  "linkedin": {
    "email": "your-linkedin-email@example.com",
    "password": "your-linkedin-password"
  },
  "naukri": {
    "email": "your-naukri-email@example.com",
    "password": "your-naukri-password"
  },
  "indeed": {
    "email": "your-indeed-email@example.com",
    "password": "your-indeed-password"
  },
  "notification_email": "your-notification-email@example.com"
}
```

**IMPORTANT**: Never commit `secrets.json` to version control!

### 1.2 Verify SES Email Address

Verify the sender email address in Amazon SES:

```bash
aws ses verify-email-identity --email-address your-notification-email@example.com
```

Check your email for the verification link and click it.

**Note**: If your AWS account is in SES Sandbox mode, you also need to verify recipient email addresses.

## Step 2: Enable Bedrock Model Access

Enable access to Claude 3 Haiku model in Amazon Bedrock:

1. Go to AWS Console → Amazon Bedrock → Model access
2. Request access to **Anthropic Claude 3 Haiku**
3. Wait for approval (usually instant)

Or via CLI:
```bash
aws bedrock put-model-invocation-logging-configuration \
  --region us-east-1
```

## Step 3: Install Dependencies

```bash
npm install
```

## Step 4: Deploy Using SAM (Recommended)

### 4.1 Build the Application

```bash
sam build
```

### 4.2 Deploy

First-time deployment:
```bash
sam deploy --guided
```

You'll be prompted for:
- **Stack Name**: `job-portal-profile-refresh`
- **AWS Region**: Your preferred region (e.g., `us-east-1`)
- **SecretName**: `job-portal-credentials`
- **NotificationEmail**: Your verified email address
- **ScheduleExpression**: `cron(0 9 * * ? *)` (9 AM UTC daily)
- **LogLevel**: `info`
- Confirm changes and deploy

Subsequent deployments:
```bash
sam deploy
```

### 4.3 Verify Deployment

```bash
aws lambda get-function --function-name job-portal-profile-refresh
```

## Step 5: Alternative - Manual Deployment

If not using SAM, follow these manual steps:

### 5.1 Create Deployment Package

```bash
# Install production dependencies
npm install --production

# Create deployment package
zip -r function.zip . -x "*.git*" "tests/*" "*.md" "secrets.json"
```

### 5.2 Create IAM Role

Create an IAM role for Lambda with these policies:
- `AWSLambdaBasicExecutionRole`
- Custom policy for Secrets Manager, Bedrock, and SES

```bash
aws iam create-role \
  --role-name JobPortalRefreshLambdaRole \
  --assume-role-policy-document file://trust-policy.json

aws iam attach-role-policy \
  --role-name JobPortalRefreshLambdaRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam put-role-policy \
  --role-name JobPortalRefreshLambdaRole \
  --policy-name JobPortalRefreshPolicy \
  --policy-document file://permissions-policy.json
```

### 5.3 Create Lambda Function

```bash
aws lambda create-function \
  --function-name job-portal-profile-refresh \
  --runtime nodejs18.x \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/JobPortalRefreshLambdaRole \
  --handler src/index.handler \
  --zip-file fileb://function.zip \
  --timeout 300 \
  --memory-size 1024 \
  --environment Variables="{SECRET_NAME=job-portal-credentials,LOG_LEVEL=info,FROM_EMAIL=your-email@example.com}"
```

### 5.4 Create EventBridge Rule

```bash
aws events put-rule \
  --name job-portal-refresh-schedule \
  --schedule-expression "cron(0 9 * * ? *)" \
  --description "Daily trigger for job portal profile refresh"

aws events put-targets \
  --rule job-portal-refresh-schedule \
  --targets "Id"="1","Arn"="arn:aws:lambda:REGION:ACCOUNT_ID:function:job-portal-profile-refresh"

aws lambda add-permission \
  --function-name job-portal-profile-refresh \
  --statement-id AllowEventBridgeInvoke \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn arn:aws:events:REGION:ACCOUNT_ID:rule/job-portal-refresh-schedule
```

## Step 6: Test the Deployment

### 6.1 Manual Test Invocation

```bash
aws lambda invoke \
  --function-name job-portal-profile-refresh \
  --invocation-type RequestResponse \
  --log-type Tail \
  --payload '{}' \
  response.json

cat response.json
```

### 6.2 View Logs

```bash
aws logs tail /aws/lambda/job-portal-profile-refresh --follow
```

## Step 7: Configure Schedule

The default schedule is daily at 9 AM UTC. To change it:

### Recommended Schedules

- **Daily at 9 AM UTC**: `cron(0 9 * * ? *)`
- **Every Monday at 8 AM UTC**: `cron(0 8 ? * MON *)`
- **Every 3 days at 10 AM UTC**: `cron(0 10 */3 * ? *)`
- **Twice weekly (Mon & Thu at 9 AM UTC)**: `cron(0 9 ? * 2,5 *)`

Update via SAM:
```bash
# Edit template.yaml and change ScheduleExpression parameter
sam deploy
```

Or update EventBridge rule directly:
```bash
aws events put-rule \
  --name job-portal-refresh-schedule \
  --schedule-expression "cron(0 10 */3 * ? *)"
```

## Step 8: Monitoring and Maintenance

### View CloudWatch Logs
```bash
aws logs tail /aws/lambda/job-portal-profile-refresh --follow
```

### Check Recent Executions
```bash
aws lambda list-function-event-invoke-configs \
  --function-name job-portal-profile-refresh
```

### Update Function Code
```bash
# Make changes to code
npm install --production
zip -r function.zip . -x "*.git*" "tests/*" "*.md"

aws lambda update-function-code \
  --function-name job-portal-profile-refresh \
  --zip-file fileb://function.zip
```

### Update Environment Variables
```bash
aws lambda update-function-configuration \
  --function-name job-portal-profile-refresh \
  --environment Variables="{SECRET_NAME=job-portal-credentials,LOG_LEVEL=debug}"
```

## Troubleshooting

### Common Issues

1. **Login Failures**
   - Check credentials in Secrets Manager
   - Verify no CAPTCHA is required
   - Check CloudWatch logs for specific errors

2. **Email Not Received**
   - Verify SES email address is verified
   - Check spam folder
   - Review CloudWatch logs for SES errors

3. **Bedrock Access Denied**
   - Ensure model access is enabled in Bedrock console
   - Check IAM role has `bedrock:InvokeModel` permission

4. **Timeout Errors**
   - Increase Lambda timeout (current: 5 minutes)
   - Check if portals are responding slowly

5. **Selector Not Found Errors**
   - Portal UI may have changed
   - Update selectors in portal modules
   - Enable debug logging to capture screenshots

### Enable Debug Logging

```bash
aws lambda update-function-configuration \
  --function-name job-portal-profile-refresh \
  --environment Variables="{SECRET_NAME=job-portal-credentials,LOG_LEVEL=debug}"
```

## Security Best Practices

1. **Credentials**
   - Always use AWS Secrets Manager
   - Enable automatic rotation if possible
   - Use unique passwords for each portal

2. **IAM Permissions**
   - Follow principle of least privilege
   - Review and audit IAM policies regularly

3. **Logging**
   - Never log credentials
   - Enable CloudWatch Logs encryption
   - Set appropriate log retention period

4. **Network**
   - Consider using VPC for Lambda if needed
   - Use AWS PrivateLink for service access

## Cost Estimation

Estimated monthly costs (assuming daily execution):
- **Lambda**: ~$0.50 (30 invocations × 3 min × $0.0000166667/GB-second)
- **Bedrock**: ~$0.15 (90 API calls × $0.00025/1K tokens)
- **Secrets Manager**: $0.40/secret/month
- **SES**: Free for first 62,000 emails
- **CloudWatch Logs**: ~$0.50/month

**Total**: ~$1.55/month

## Cleanup

To delete all resources:

```bash
# Using SAM
sam delete

# Or manually
aws events remove-targets --rule job-portal-refresh-schedule --ids "1"
aws events delete-rule --name job-portal-refresh-schedule
aws lambda delete-function --function-name job-portal-profile-refresh
aws iam delete-role-policy --role-name JobPortalRefreshLambdaRole --policy-name JobPortalRefreshPolicy
aws iam detach-role-policy --role-name JobPortalRefreshLambdaRole --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
aws iam delete-role --role-name JobPortalRefreshLambdaRole
aws secretsmanager delete-secret --secret-id job-portal-credentials --force-delete-without-recovery
```
