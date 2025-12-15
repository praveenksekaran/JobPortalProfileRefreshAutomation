# Node.js to Python Conversion Summary

This document summarizes the conversion of the Job Portal Profile Refresh Automation from Node.js to Python.

## Key Changes

### 1. Runtime & Dependencies

| Node.js | Python |
|---------|--------|
| `package.json` | `requirements.txt` + `setup.py` |
| `node_modules/` | `venv/` (virtual environment) |
| npm/yarn | pip |
| Node.js 18.x | Python 3.11+ |
| AWS SDK v3 | boto3 |
| Playwright (JS) | Playwright (Python async) |

### 2. Project Structure

```
Old (Node.js)          →  New (Python)
─────────────────────────────────────────
src/index.js           →  src/lambda_handler.py
src/utils/logger.js    →  src/utils/logger.py
src/utils/playwright.js →  src/utils/playwright_helpers.py
config/config.js       →  config/config.py
package.json           →  requirements.txt
```

### 3. Code Conversions

#### Module System
```javascript
// Node.js
const config = require('../config/config');
module.exports = MyClass;
```

```python
# Python
from config import config
# Classes are imported directly
```

#### Async/Await
```javascript
// Node.js - natively async
async function execute() {
  await page.click(selector);
}
```

```python
# Python - async/await syntax
async def execute(self):
    await page.click(selector)

# Lambda handler wraps async code
def lambda_handler(event, context):
    return asyncio.run(async_handler(event, context))
```

#### Error Handling
```javascript
// Node.js
try {
  // code
} catch (error) {
  logger.error('Failed', error);
}
```

```python
# Python
try:
    # code
except Exception as error:
    logger.error('Failed', error)
```

### 4. Configuration Changes

**Node.js** (`config.js`):
```javascript
module.exports = {
  aws: {
    region: process.env.AWS_REGION || 'us-east-1',
  }
}
```

**Python** (`config.py`):
```python
import os

AWS_CONFIG = {
    'region': os.getenv('AWS_REGION', 'us-east-1'),
}
```

### 5. AWS SDK Differences

#### Secrets Manager
```javascript
// Node.js
const { SecretsManagerClient, GetSecretValueCommand } = require('@aws-sdk/client-secrets-manager');
const client = new SecretsManagerClient({ region });
const response = await client.send(new GetSecretValueCommand({ SecretId: name }));
```

```python
# Python
import boto3
client = boto3.client('secretsmanager', region_name=region)
response = client.get_secret_value(SecretId=name)
```

#### Bedrock
```javascript
// Node.js
const { BedrockRuntimeClient, InvokeModelCommand } = require('@aws-sdk/client-bedrock-runtime');
const response = await client.send(new InvokeModelCommand({...}));
```

```python
# Python
import boto3
client = boto3.client('bedrock-runtime', region_name=region)
response = client.invoke_model(modelId=..., body=...)
```

### 6. Playwright Differences

```javascript
// Node.js
const { chromium } = require('playwright');
const browser = await chromium.launch();
```

```python
# Python
from playwright.async_api import async_playwright
playwright = await async_playwright().start()
browser = await playwright.chromium.launch()
```

### 7. Lambda Handler

**Node.js**:
```javascript
exports.handler = async (event, context) => {
  // async code runs directly
  return response;
};
```

**Python**:
```python
def lambda_handler(event, context):
    # Wrap async code
    return asyncio.run(async_handler(event, context))

async def async_handler(event, context):
    # async code here
    return response
```

### 8. Deployment Differences

#### SAM Template
- Runtime: `nodejs18.x` → `python3.11`
- Handler: `src/index.handler` → `src.lambda_handler.lambda_handler`
- Layers: Added Playwright layer requirement

#### Dependencies Installation
```bash
# Node.js
npm install

# Python
pip install -r requirements.txt
python -m playwright install chromium
```

## File-by-File Mapping

| Node.js File | Python File | Notes |
|--------------|-------------|-------|
| `package.json` | `requirements.txt` | Dependencies |
| `src/index.js` | `src/lambda_handler.py` | Main handler |
| `src/utils/logger.js` | `src/utils/logger.py` | Logging utility |
| `src/utils/playwright.js` | `src/utils/playwright_helpers.py` | Browser helpers |
| `src/services/secretsManager.js` | `src/services/secrets_manager.py` | Secrets Manager |
| `src/services/bedrock.js` | `src/services/bedrock.py` | Bedrock service |
| `src/services/notifications.js` | `src/services/notifications.py` | Email notifications |
| `src/portals/linkedin.js` | `src/portals/linkedin.py` | LinkedIn automation |
| `src/portals/naukri.js` | `src/portals/naukri.py` | Naukri automation |
| `src/portals/indeed.js` | `src/portals/indeed.py` | Indeed automation |
| `config/config.js` | `config/config.py` | Configuration |

## New Files Added

1. **`setup.py`** - Python package setup file
2. **`Dockerfile`** - Container deployment option
3. **`src/__init__.py`** - Python package marker
4. **`config/__init__.py`** - Config package marker
5. **`src/services/__init__.py`** - Services package marker
6. **`src/portals/__init__.py`** - Portals package marker
7. **`src/utils/__init__.py`** - Utils package marker

## Testing

### Local Testing

**Node.js**:
```bash
npm run local
# or
node src/index.js
```

**Python**:
```bash
./scripts/test-local.sh
# or
PYTHONPATH=. python src/lambda_handler.py
```

### Deployment

**Node.js**:
```bash
npm run build
npm run deploy
```

**Python**:
```bash
pip install -r requirements.txt
sam build
sam deploy
```

## Important Python Considerations

### 1. Virtual Environment (Recommended)
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

### 2. PYTHONPATH
For imports to work correctly:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### 3. Playwright Installation
Playwright requires browser binaries:
```bash
python -m playwright install chromium
```

### 4. Lambda Layer for Playwright
Python Playwright in Lambda requires a custom layer with Chromium. Options:
- Use pre-built layer from AWS community
- Build custom layer
- Use Docker container deployment (recommended for Playwright)

### 5. Async Context
All Playwright operations are async in Python and require proper async/await handling.

## Advantages of Python Version

1. **Cleaner Syntax**: Python's syntax is often more concise
2. **Better Type Hints**: Python 3.11+ has excellent type hint support
3. **Familiar to Data Scientists**: Python is more common in ML/AI workflows
4. **boto3 Simplicity**: boto3 is more mature and simpler than AWS SDK v3
5. **Strong Community**: Large Python serverless community

## Potential Challenges

1. **Playwright Layer**: Requires custom Lambda layer (larger deployment package)
2. **Cold Starts**: Python cold starts can be slightly longer
3. **Async Complexity**: Async/await requires more careful handling in Python
4. **Import System**: Python imports can be tricky in Lambda (need proper PYTHONPATH)

## Migration Checklist

- [x] Convert all JavaScript files to Python
- [x] Update package manager (npm → pip)
- [x] Convert async/await patterns
- [x] Update AWS SDK calls (AWS SDK v3 → boto3)
- [x] Update Playwright calls (sync → async)
- [x] Update SAM template (runtime, handler)
- [x] Update deployment scripts
- [x] Update documentation
- [x] Add Python-specific files (__init__.py, setup.py)
- [x] Add Dockerfile for container deployment

## Next Steps

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   python -m playwright install chromium
   ```

2. Test locally:
   ```bash
   chmod +x scripts/test-local.sh
   ./scripts/test-local.sh
   ```

3. Deploy to AWS:
   ```bash
   chmod +x scripts/deploy.sh
   ./scripts/deploy.sh
   ```

## Support

Both versions (Node.js and Python) are functionally equivalent. Choose based on:
- **Node.js**: If you prefer JavaScript, smaller Lambda packages
- **Python**: If you prefer Python syntax, integration with ML/data workflows
