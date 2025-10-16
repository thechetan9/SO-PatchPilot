# 🚀 PatchPilot Deployment Guide

This guide covers deploying PatchPilot to production using AWS services.

---

## 📋 Prerequisites

- AWS Account with appropriate permissions
- AWS CLI installed and configured
- Python 3.9+
- Node.js 18+
- Git

---

## 🔧 AWS Setup

### 1. Enable AWS Bedrock Model Access

1. Go to [AWS Bedrock Console](https://console.aws.amazon.com/bedrock/)
2. Navigate to **Model access** in the left sidebar
3. Click **"Manage model access"**
4. Find **Anthropic** section and enable **Claude 3.5 Haiku**
5. Submit the use case form (approval is usually instant)

### 2. Create DynamoDB Tables

Run the provided script to create required tables:

```bash
python create_dynamodb_tables.py
```

This creates:
- `PatchPlans-dev` - Stores patch plans
- `PatchRuns-dev` - Stores execution runs
- `PatchPilotExecutions-dev` - Stores execution history

**For production**, update table names in the script to use `-prod` suffix.

### 3. Configure AWS Credentials

Create a `.env` file in the `backend/` directory:

```env
# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_SESSION_TOKEN=your_session_token_here  # Optional, for temporary credentials
AWS_REGION=us-east-1

# Bedrock Model Configuration
BEDROCK_MODEL_ID=us.anthropic.claude-3-5-haiku-20241022-v1:0

# DynamoDB Tables
DYNAMODB_TABLE_PLANS=PatchPlans-prod
DYNAMODB_TABLE_PATCH_RUNS=PatchRuns-prod
DYNAMODB_TABLE=PatchPilotExecutions-prod

# SuperOps Configuration (Optional)
SUPEROPS_API_KEY=your_superops_api_key
SUPEROPS_API_URL=https://api.superops.ai
```

**⚠️ IMPORTANT:** Never commit the `.env` file to Git! It's already in `.gitignore`.

---

## 🐳 Deployment Options

### Option 1: AWS Lambda + API Gateway (Recommended)

#### Deploy Backend as Lambda

1. **Install AWS SAM CLI:**
   ```bash
   pip install aws-sam-cli
   ```

2. **Build and Deploy:**
   ```bash
   sam build
   sam deploy --guided
   ```

3. **Configure API Gateway:**
   - The SAM template (`template.yaml`) already includes API Gateway configuration
   - Note the API endpoint URL from the deployment output

#### Deploy Frontend to AWS Amplify

1. **Push to GitHub** (see GitHub deployment section below)

2. **Connect to Amplify:**
   - Go to [AWS Amplify Console](https://console.aws.amazon.com/amplify/)
   - Click **"New app"** → **"Host web app"**
   - Connect your GitHub repository
   - Select the `frontend` directory as the root

3. **Configure Build Settings:**
   ```yaml
   version: 1
   frontend:
     phases:
       preBuild:
         commands:
           - cd frontend
           - npm ci
       build:
         commands:
           - npm run build
     artifacts:
       baseDirectory: frontend/.next
       files:
         - '**/*'
     cache:
       paths:
         - frontend/node_modules/**/*
   ```

4. **Set Environment Variables:**
   - Add `NEXT_PUBLIC_API_URL` with your API Gateway endpoint

---

### Option 2: EC2 / Container Deployment

#### Backend (Flask API)

1. **Use Production WSGI Server:**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 backend.src.api:app
   ```

2. **Or use Docker:**
   ```dockerfile
   FROM python:3.9-slim
   WORKDIR /app
   COPY backend/requirements.txt .
   RUN pip install -r requirements.txt
   COPY backend/ .
   CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "src.api:app"]
   ```

#### Frontend (Next.js)

1. **Build for Production:**
   ```bash
   cd frontend
   npm run build
   npm start
   ```

2. **Or use Docker:**
   ```dockerfile
   FROM node:18-alpine
   WORKDIR /app
   COPY frontend/package*.json ./
   RUN npm ci --only=production
   COPY frontend/ .
   RUN npm run build
   CMD ["npm", "start"]
   ```

---

## 🔐 Security Best Practices

1. **Use IAM Roles** instead of access keys when possible
2. **Enable CloudWatch Logs** for monitoring
3. **Use AWS Secrets Manager** for sensitive credentials
4. **Enable HTTPS** for all endpoints
5. **Implement API authentication** (API keys, JWT, etc.)
6. **Set up CORS** properly in production
7. **Use VPC** for database access
8. **Enable DynamoDB encryption** at rest

---

## 📊 Monitoring & Logging

### CloudWatch Integration

The application already logs events. To send to CloudWatch:

```python
import watchtower
import logging

logger = logging.getLogger(__name__)
logger.addHandler(watchtower.CloudWatchLogHandler())
```

### Metrics to Monitor

- Bedrock API latency
- DynamoDB read/write capacity
- Lambda execution duration
- API Gateway 4xx/5xx errors
- Plan generation success rate

---

## 🧪 Testing Production Deployment

1. **Test Bedrock Access:**
   ```bash
   aws bedrock-runtime invoke-model \
     --model-id us.anthropic.claude-3-5-haiku-20241022-v1:0 \
     --body '{"anthropic_version":"bedrock-2023-05-31","max_tokens":100,"messages":[{"role":"user","content":"Hello"}]}' \
     --region us-east-1 \
     output.json
   ```

2. **Test DynamoDB Access:**
   ```bash
   aws dynamodb list-tables --region us-east-1
   ```

3. **Test API Endpoint:**
   ```bash
   curl -X POST https://your-api-endpoint/webhook/superops \
     -H "Content-Type: application/json" \
     -d '{"ticket_id":"TEST-001","client_id":"test","device_ids":["srv-01"],"cve_findings":[]}'
   ```

---

## 🔄 CI/CD Pipeline

See `.github/workflows/ci.yml` for automated testing and deployment.

**Recommended workflow:**
1. Push to `main` branch
2. GitHub Actions runs tests
3. If tests pass, deploy to staging
4. Manual approval for production deployment

---

## 📝 Post-Deployment Checklist

- [ ] AWS Bedrock model access enabled
- [ ] DynamoDB tables created
- [ ] Environment variables configured
- [ ] Backend API deployed and accessible
- [ ] Frontend deployed and accessible
- [ ] HTTPS enabled
- [ ] Monitoring and logging configured
- [ ] Backup strategy implemented
- [ ] Documentation updated with production URLs

---

## 🆘 Troubleshooting

### Bedrock Access Denied
- Verify model access is enabled in AWS Console
- Check IAM permissions for `bedrock:InvokeModel`
- Ensure using correct region (us-east-1)

### DynamoDB Errors
- Verify tables exist: `aws dynamodb list-tables`
- Check IAM permissions for DynamoDB
- Verify table names match environment variables

### Lambda Timeout
- Increase timeout in `template.yaml` (default: 30s)
- Consider using Step Functions for long-running tasks

---

## 📚 Additional Resources

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [Next.js Deployment](https://nextjs.org/docs/deployment)

