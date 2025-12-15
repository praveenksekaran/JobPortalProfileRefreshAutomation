# Testing Guide

Guide for testing the Job Portal Profile Refresh Automation system.

## Testing Strategy

### 1. Local Testing
### 2. AWS Testing
### 3. Integration Testing
### 4. Production Validation

## 1. Local Testing

### Prerequisites
- Node.js 18+ installed
- Valid portal credentials
- AWS credentials configured locally

### Setup

1. **Create local environment file**:
```bash
cp .env.example .env
```

Edit `.env`:
```
AWS_REGION=us-east-1
SECRET_NAME=job-portal-credentials
FROM_EMAIL=your-email@example.com
LOG_LEVEL=debug
```

2. **Create test secrets file**:
```bash
cp secrets.json.template secrets.json
```

Edit `secrets.json` with your credentials.

3. **Upload secrets to AWS Secrets Manager**:
```bash
./scripts/update-secrets.sh secrets.json
```

### Run Local Tests

**Test the Lambda handler**:
```bash
npm run local
```

Or directly:
```bash
node src/index.js
```

**Expected Output**:
```json
{
  "statusCode": 200,
  "body": {
    "message": "All portals updated successfully",
    "summary": {
      "success": true,
      "results": [...],
      "startTime": 1234567890,
      "endTime": 1234567890,
      "totalDuration": 180000
    }
  }
}
```

### Test Individual Components

**Test Secrets Manager**:
```javascript
const secretsManager = require('./src/services/secretsManager');

(async () => {
  const credentials = await secretsManager.getCredentials();
  console.log('Credentials retrieved:', Object.keys(credentials));
})();
```

**Test Bedrock Service**:
```javascript
const bedrockService = require('./src/services/bedrock');

(async () => {
  const original = "I am a software engineer with 5 years of experience.";
  const mutated = await bedrockService.mutateContent(original, "Profile Summary");
  console.log('Original:', original);
  console.log('Mutated:', mutated);
})();
```

**Test Individual Portal** (LinkedIn example):
```javascript
const linkedinAutomation = require('./src/portals/linkedin');
const secretsManager = require('./src/services/secretsManager');

(async () => {
  const credentials = await secretsManager.getPortalCredentials('linkedin');
  const result = await linkedinAutomation.execute(credentials);
  console.log('Result:', result);
})();
```

## 2. AWS Testing

### Deploy to AWS

```bash
# Build and deploy
sam build
sam deploy --guided
```

### Invoke Lambda Manually

**Synchronous invocation**:
```bash
aws lambda invoke \
  --function-name job-portal-profile-refresh \
  --payload '{}' \
  --cli-binary-format raw-in-base64-out \
  response.json

cat response.json
```

**Check logs**:
```bash
aws logs tail /aws/lambda/job-portal-profile-refresh --follow
```

### Test Individual Portals

**Test LinkedIn only** (modify code temporarily):
```javascript
// In config/config.js, disable other portals:
portals: {
  linkedin: {
    enabled: true,
    // ...
  },
  naukri: {
    enabled: false, // Disable for testing
    // ...
  },
  indeed: {
    enabled: false, // Disable for testing
    // ...
  },
}
```

Redeploy and invoke.

## 3. Integration Testing

### Test Email Notifications

1. **Verify SES email**:
```bash
aws ses verify-email-identity \
  --email-address your-test-email@example.com
```

2. **Check verification status**:
```bash
aws ses get-identity-verification-attributes \
  --identities your-test-email@example.com
```

3. **Invoke Lambda and check inbox**

### Test Bedrock Integration

1. **Verify model access**:
```bash
aws bedrock list-foundation-models \
  --region us-east-1 \
  --query 'modelSummaries[?modelId==`anthropic.claude-3-haiku-20240307-v1:0`]'
```

2. **Test direct invocation**:
```bash
aws bedrock-runtime invoke-model \
  --model-id anthropic.claude-3-haiku-20240307-v1:0 \
  --body '{"anthropic_version":"bedrock-2023-05-31","max_tokens":100,"messages":[{"role":"user","content":"Hello"}]}' \
  --cli-binary-format raw-in-base64-out \
  output.txt

cat output.txt
```

### Test Secrets Manager

1. **Retrieve secret**:
```bash
aws secretsmanager get-secret-value \
  --secret-id job-portal-credentials \
  --query 'SecretString' \
  --output text
```

2. **Validate JSON structure**:
```bash
aws secretsmanager get-secret-value \
  --secret-id job-portal-credentials \
  --query 'SecretString' \
  --output text | jq .
```

## 4. Production Validation

### Pre-Production Checklist

- [ ] Secrets Manager contains valid credentials
- [ ] SES email address is verified
- [ ] Bedrock model access is enabled
- [ ] Lambda function is deployed successfully
- [ ] EventBridge rule is created and enabled
- [ ] IAM roles have correct permissions
- [ ] CloudWatch log group exists
- [ ] All environment variables are set

### Smoke Test

**Run a manual invocation**:
```bash
aws lambda invoke \
  --function-name job-portal-profile-refresh \
  --payload '{}' \
  response.json && cat response.json
```

**Verify**:
- [ ] Lambda executes without errors
- [ ] All enabled portals are processed
- [ ] Email notification is received
- [ ] CloudWatch logs show successful execution
- [ ] No error messages in logs

### Monitoring Setup

1. **Create CloudWatch Dashboard** (optional):
```bash
aws cloudwatch put-dashboard \
  --dashboard-name JobPortalProfileRefresh \
  --dashboard-body file://cloudwatch-dashboard.json
```

2. **Set up CloudWatch Alarms**:

**Lambda Errors**:
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name job-portal-lambda-errors \
  --alarm-description "Alert on Lambda errors" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --evaluation-periods 1 \
  --dimensions Name=FunctionName,Value=job-portal-profile-refresh
```

**Lambda Throttles**:
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name job-portal-lambda-throttles \
  --alarm-description "Alert on Lambda throttles" \
  --metric-name Throttles \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --evaluation-periods 1 \
  --dimensions Name=FunctionName,Value=job-portal-profile-refresh
```

### Test Failure Scenarios

1. **Invalid Credentials Test**:
   - Update secret with wrong password
   - Invoke Lambda
   - Verify error handling and notification

2. **Bedrock Unavailable Test**:
   - Remove Bedrock permissions temporarily
   - Invoke Lambda
   - Verify fallback mutation works

3. **SES Failure Test**:
   - Use unverified email temporarily
   - Invoke Lambda
   - Verify Lambda completes despite notification failure

4. **Timeout Test**:
   - Reduce Lambda timeout to 30 seconds
   - Invoke Lambda
   - Verify timeout handling

## Common Test Scenarios

### Scenario 1: Fresh Profile Update

**Goal**: Verify complete flow with valid credentials

**Steps**:
1. Ensure credentials are valid
2. Invoke Lambda
3. Check execution logs
4. Verify email notification received
5. Manually check portals for updates

**Expected**:
- All portals updated successfully
- Email shows success for all portals
- Profile fields show minor changes

### Scenario 2: One Portal Fails

**Goal**: Verify partial failure handling

**Steps**:
1. Temporarily break one portal's credentials
2. Invoke Lambda
3. Check execution continues with other portals

**Expected**:
- Failed portal logged as error
- Other portals complete successfully
- Email shows partial failure

### Scenario 3: CAPTCHA Encountered

**Goal**: Verify graceful CAPTCHA handling

**Steps**:
1. Invoke Lambda during high-security period
2. Monitor for CAPTCHA detection
3. Check error handling

**Expected**:
- CAPTCHA detected and logged
- Portal skipped with appropriate error
- Other portals continue

### Scenario 4: Content Mutation Quality

**Goal**: Verify AI mutations are minimal and appropriate

**Steps**:
1. Enable debug logging
2. Invoke Lambda
3. Examine logs for original vs mutated content

**Expected**:
- Mutations preserve meaning
- Length change < 15%
- Professional tone maintained
- No hallucinations or added information

## Debugging Tips

### Enable Debug Logging

```bash
aws lambda update-function-configuration \
  --function-name job-portal-profile-refresh \
  --environment Variables="{SECRET_NAME=job-portal-credentials,LOG_LEVEL=debug}"
```

### View Detailed Logs

```bash
aws logs tail /aws/lambda/job-portal-profile-refresh \
  --follow \
  --format short
```

### Download Screenshots

When errors occur, screenshots are saved to `/tmp/` in Lambda.

To retrieve (requires enabling Lambda ephemeral storage logging):
```bash
# Screenshots are logged in debug mode
# Check CloudWatch logs for base64-encoded screenshots
```

### Common Issues

**Issue**: "Selector not found"
- **Cause**: Portal UI changed
- **Solution**: Update selectors in portal module, enable debug logging, capture screenshots

**Issue**: "Login failed: CAPTCHA detected"
- **Cause**: Too many login attempts or suspicious activity
- **Solution**: Wait 24 hours, use different IP, add more human-like delays

**Issue**: "Bedrock API error: Access Denied"
- **Cause**: Model access not enabled
- **Solution**: Enable Claude 3 Haiku in Bedrock console

**Issue**: "SES sending failed: Email address not verified"
- **Cause**: SES email not verified or sandbox mode
- **Solution**: Verify email, request production access for SES

## Performance Benchmarks

### Expected Timings

| Phase | Expected Duration |
|-------|-------------------|
| Credential retrieval | 1-2s |
| LinkedIn automation | 60-90s |
| Naukri automation | 60-90s |
| Indeed automation | 60-120s |
| Email notification | 1-3s |
| **Total** | **180-300s** |

### Performance Optimization

If execution is slow:
1. Check CloudWatch Logs for bottlenecks
2. Verify network latency to portals
3. Reduce `slowMo` delay in config (for testing only)
4. Increase Lambda memory (faster CPU)

## Cleanup After Testing

```bash
# Delete test Lambda function
aws lambda delete-function --function-name job-portal-profile-refresh

# Delete test secrets (if using separate test secret)
aws secretsmanager delete-secret \
  --secret-id job-portal-credentials-test \
  --force-delete-without-recovery

# Delete CloudWatch log groups
aws logs delete-log-group \
  --log-group-name /aws/lambda/job-portal-profile-refresh

# Delete EventBridge rule
aws events remove-targets \
  --rule job-portal-refresh-schedule \
  --ids "1"

aws events delete-rule \
  --name job-portal-refresh-schedule
```
