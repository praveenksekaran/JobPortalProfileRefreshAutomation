# System Architecture

## Overview

The Job Portal Profile Refresh Automation is a serverless system built on AWS that automates profile updates across LinkedIn, Naukri, and Indeed to keep profiles fresh and improve recruiter visibility.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        AWS Cloud                                 │
│                                                                  │
│  ┌──────────────┐         ┌─────────────────────────────┐      │
│  │              │ Trigger │                             │      │
│  │ EventBridge  ├────────▶│  Lambda Function            │      │
│  │  (Schedule)  │         │  (Node.js 18)               │      │
│  │              │         │                             │      │
│  └──────────────┘         └──────┬──────────────────────┘      │
│                                   │                              │
│                                   │                              │
│            ┌──────────────────────┼──────────────────────┐      │
│            │                      │                      │      │
│            ▼                      ▼                      ▼      │
│  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────┐  │
│  │                  │  │                  │  │             │  │
│  │ Secrets Manager  │  │ Amazon Bedrock   │  │  Amazon SES │  │
│  │  (Credentials)   │  │ (Claude 3 Haiku) │  │   (Email)   │  │
│  │                  │  │                  │  │             │  │
│  └──────────────────┘  └──────────────────┘  └─────────────┘  │
│                                   │                              │
│                                   │                              │
│                                   ▼                              │
│                         ┌──────────────────┐                    │
│                         │                  │                    │
│                         │ CloudWatch Logs  │                    │
│                         │  (Audit Trail)   │                    │
│                         │                  │                    │
│                         └──────────────────┘                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                                   │
                                   │ Playwright
                                   │ Browser Automation
                                   │
                        ┌──────────┼──────────┐
                        │          │          │
                        ▼          ▼          ▼
                  ┌──────────┬──────────┬──────────┐
                  │ LinkedIn │  Naukri  │  Indeed  │
                  └──────────┴──────────┴──────────┘
```

## Component Details

### 1. EventBridge Scheduler
- **Purpose**: Triggers Lambda execution on a scheduled basis
- **Configuration**: Cron expression (default: daily at 9 AM UTC)
- **Flexibility**: Can be adjusted to run at different frequencies

### 2. Lambda Function
- **Runtime**: Node.js 18.x
- **Memory**: 1024 MB
- **Timeout**: 5 minutes (300 seconds)
- **Execution Flow**:
  1. Retrieve credentials from Secrets Manager
  2. For each enabled portal:
     - Launch headless browser
     - Login using Playwright
     - Navigate to profile section
     - Read current content
     - Generate mutated content via Bedrock
     - Update profile
     - Close browser
  3. Compile execution summary
  4. Send notification email
  5. Log results to CloudWatch

### 3. Secrets Manager
- **Purpose**: Secure storage of portal credentials
- **Content**: JSON structure with credentials for all portals
- **Security**: Encrypted at rest, accessed via IAM role
- **Rotation**: Manual (can be automated in future)

### 4. Amazon Bedrock
- **Model**: Claude 3 Haiku (anthropic.claude-3-haiku-20240307-v1:0)
- **Purpose**: AI-powered content mutation
- **Input**: Original profile text + context
- **Output**: Minimally modified text preserving meaning
- **Parameters**:
  - Temperature: 0.7
  - Max tokens: 500

### 5. Amazon SES
- **Purpose**: Email notifications
- **Trigger**: After each execution (success or failure)
- **Content**: HTML and plain text execution summary
- **Setup**: Requires email verification

### 6. CloudWatch Logs
- **Purpose**: Audit trail and debugging
- **Retention**: 30 days (configurable)
- **Log Level**: Configurable (debug, info, warn, error)
- **Structure**: JSON-formatted log entries

### 7. Playwright Browser Automation
- **Engine**: Chromium (headless)
- **Framework**: playwright-aws-lambda (optimized for Lambda)
- **Features**:
  - Human-like behavior (delays, typing speed)
  - Error handling and retries
  - Screenshot capture for debugging
  - Cookie and session management

## Data Flow

### Execution Sequence

1. **Initialization** (0-5s)
   - EventBridge triggers Lambda
   - Lambda starts execution
   - Environment variables loaded

2. **Credential Retrieval** (1-2s)
   - Fetch credentials from Secrets Manager
   - Cache credentials for session
   - Validate credential structure

3. **Portal Automation Loop** (60-180s per portal)

   **For Each Portal:**

   a. **Browser Launch** (5-10s)
      - Start headless Chromium
      - Configure user agent and viewport
      - Set timeouts and navigation settings

   b. **Login** (10-20s)
      - Navigate to login page
      - Enter credentials with human-like delays
      - Handle potential CAPTCHA/OTP
      - Verify successful login

   c. **Profile Navigation** (5-10s)
      - Navigate to profile edit page
      - Wait for page load
      - Locate target section

   d. **Content Reading** (2-5s)
      - Click edit button
      - Read current content from field
      - Validate content exists

   e. **AI Content Mutation** (2-5s)
      - Send content to Bedrock
      - Receive mutated content
      - Validate mutation quality

   f. **Content Update** (5-10s)
      - Clear existing content
      - Type new content
      - Click save button
      - Verify save success

   g. **Browser Cleanup** (1-2s)
      - Close browser
      - Free resources

   h. **Inter-Portal Delay** (5s)
      - Wait before next portal

4. **Notification** (1-3s)
   - Compile execution summary
   - Format email (HTML + text)
   - Send via SES
   - Log notification status

5. **Completion** (0-1s)
   - Log final summary
   - Return response
   - Lambda terminates

## Security Architecture

### 1. Authentication & Authorization
- Lambda execution role with least-privilege IAM policies
- Secrets Manager for credential storage (no plaintext in code/logs)
- SES email verification to prevent spoofing

### 2. Data Protection
- Secrets encrypted at rest in Secrets Manager
- TLS/HTTPS for all AWS service communication
- No credential logging (only masked in logs)
- Temporary browser data deleted after execution

### 3. Network Security
- Lambda runs in AWS-managed VPC (default)
- Outbound internet access for portal connections
- No inbound connections required
- Optional: Can run in custom VPC with NAT Gateway

### 4. Audit & Monitoring
- All actions logged to CloudWatch
- Execution metrics tracked
- Email notifications for all executions
- CloudTrail integration for API calls

## Scalability & Performance

### Current Limitations (Single-User Design)
- **Concurrency**: 1 (sequential portal execution)
- **Throughput**: ~3 portals per execution
- **Frequency**: Once per day (configurable)

### Performance Optimizations
- Credentials caching (5-minute TTL)
- Parallel-ready architecture (can be extended)
- Efficient browser automation (playwright-aws-lambda)
- Minimal AI token usage (Haiku model)

### Resource Sizing
- **Lambda Memory**: 1024 MB (adequate for Chromium)
- **Lambda Timeout**: 300s (handles slow portal responses)
- **Browser Timeout**: 30s (per action), 60s (navigation)

## Error Handling & Resilience

### Retry Strategy
- **Portal-level**: 2 retries with exponential backoff
- **Action-level**: 3 attempts for element waits
- **Bedrock failover**: Fallback to simple text mutation

### Failure Scenarios

1. **Login Failure**
   - Cause: Invalid credentials, CAPTCHA, OTP required
   - Handling: Log error, skip portal, continue with others
   - Notification: Email includes failure details

2. **Content Read/Write Failure**
   - Cause: UI changes, slow loading, selector mismatch
   - Handling: Retry with alternative selectors, screenshot capture
   - Notification: Email includes error message

3. **Bedrock API Failure**
   - Cause: Service unavailable, quota exceeded
   - Handling: Use fallback mutation (simple text change)
   - Notification: Warning in email

4. **Complete Execution Failure**
   - Cause: Secrets unavailable, Lambda timeout
   - Handling: Log error, send failure notification
   - Recovery: Next scheduled run will retry

### Monitoring & Alerts

**CloudWatch Metrics** (Auto-generated):
- Lambda invocations
- Lambda errors
- Lambda duration
- Lambda throttles

**Custom Logging**:
- Portal success/failure rates
- Execution duration per portal
- Bedrock API usage
- Browser automation errors

**Email Notifications**:
- Success summary (all portals updated)
- Partial failure (some portals failed)
- Complete failure (execution error)

## Cost Analysis

### Monthly Cost Breakdown (30 executions/month)

| Service | Usage | Cost |
|---------|-------|------|
| Lambda | 30 invocations × 3 min × 1 GB | ~$0.50 |
| Bedrock | 90 API calls × ~500 tokens | ~$0.15 |
| Secrets Manager | 1 secret | $0.40 |
| SES | 30 emails | Free |
| CloudWatch Logs | ~500 MB/month | ~$0.50 |
| EventBridge | 30 events | Free |
| **Total** | | **~$1.55/month** |

### Cost Optimization Tips
- Use Haiku model (cheaper than Sonnet/Opus)
- Set appropriate log retention (30 days)
- Delete old Lambda versions
- Monitor Bedrock token usage

## Future Enhancements (Out of Scope for v1)

1. **Multi-User Support**
   - DynamoDB for user management
   - Per-user scheduling
   - User-specific configurations

2. **Additional Portals**
   - Glassdoor
   - Monster
   - ZipRecruiter

3. **Advanced Features**
   - Resume optimization suggestions
   - Job auto-apply
   - Profile analytics dashboard
   - Mobile app for monitoring

4. **Improved Resilience**
   - AI-assisted selector discovery
   - CAPTCHA solving integration
   - OTP email parsing
   - Dead letter queue for failures

5. **Enhanced Automation**
   - A/B testing different profile versions
   - Automatic profile image updates
   - Skills gap analysis
   - Industry trend integration
