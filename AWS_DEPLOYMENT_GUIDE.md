# 🚀 AWS Deployment Guide - PatchPilot

Complete guide to deploy PatchPilot to AWS using Lambda + API Gateway (Serverless)

---

## 📋 **Prerequisites**

### 1. AWS Account Setup
- ✅ AWS Account with Administrator access
- ✅ AWS CLI installed and configured
- ✅ AWS SAM CLI installed
- ✅ AWS Bedrock access enabled (Claude 3.5 Haiku)
- ✅ DynamoDB tables created (or will be created by SAM)

### 2. Local Tools Required
- Python 3.9+
- Node.js 18+
- AWS CLI v2
- AWS SAM CLI
- Git

---

## 🔧 **Step 1: Install AWS SAM CLI**

### Windows (Using MSI Installer):

1. Download AWS SAM CLI:
   ```powershell
   # Download from: https://github.com/aws/aws-sam-cli/releases/latest/download/AWS_SAM_CLI_64_PY3.msi
   ```

2. Run the installer and follow the wizard

3. Verify installation:
   ```bash
   sam --version
   # Should show: SAM CLI, version 1.x.x
   ```

### Alternative (Using pip):

```bash
pip install aws-sam-cli
sam --version
```

---

## 🔧 **Step 2: Configure AWS Credentials**

### Option A: AWS Academy Learner Lab

1. Go to AWS Academy Learner Lab
2. Click "AWS Details"
3. Copy credentials and update `backend/.env`:

```env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_SESSION_TOKEN=your_session_token
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=us.anthropic.claude-3-5-haiku-20241022-v1:0
```

### Option B: AWS IAM User

```bash
aws configure
# Enter:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region: us-east-1
# - Default output format: json
```

---

## 🔧 **Step 3: Prepare Backend for Deployment**

### 1. Create requirements.txt for Lambda

The `backend/requirements.txt` should include:

```txt
boto3>=1.28.0
flask>=2.3.0
python-dotenv>=1.0.0
```

### 2. Verify Backend Structure

```
backend/
├── src/
│   ├── __init__.py
│   ├── agent.py
│   ├── api.py
│   ├── aws_clients.py
│   ├── config.py
│   ├── dashboard_api.py
│   ├── lambda_handler.py  ← Entry point
│   ├── logger.py
│   ├── orchestrator.py
│   ├── superops_client.py
│   └── ticket_manager.py
└── requirements.txt
```

---

## 🚀 **Step 4: Deploy Backend to AWS Lambda**

### 1. Build the SAM Application

```bash
# From project root
sam build --use-container
```

This will:
- Package Python dependencies
- Prepare Lambda deployment packages
- Validate template.yaml

### 2. Deploy to AWS

**First-time deployment (guided):**

```bash
sam deploy --guided
```

You'll be prompted for:
- **Stack Name**: `patchpilot-stack`
- **AWS Region**: `us-east-1`
- **Parameter Environment**: `dev`
- **Confirm changes before deploy**: `Y`
- **Allow SAM CLI IAM role creation**: `Y`
- **Disable rollback**: `N`
- **Save arguments to samconfig.toml**: `Y`

**Subsequent deployments:**

```bash
sam deploy
```

### 3. Get API Gateway URL

After deployment, SAM will output:

```
Outputs:
WebhookUrl: https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/dev/webhook/superops
PlanApprovalUrl: https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/dev/plan/approve
DashboardApiUrl: https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/dev/api/dashboard
```

**Save these URLs!** You'll need them for the frontend.

---

## 🔧 **Step 5: Test Backend Deployment**

### 1. Test Health Check

```bash
curl https://YOUR_API_GATEWAY_URL/dev/health-check
```

### 2. Test Dashboard API

```bash
curl https://YOUR_API_GATEWAY_URL/dev/api/dashboard/plans
```

### 3. Test Webhook

```bash
curl -X POST https://YOUR_API_GATEWAY_URL/dev/webhook/superops \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "TEST-001",
    "client_id": "test-client",
    "device_ids": ["dev-001"],
    "cve_findings": []
  }'
```

---

## 🎨 **Step 6: Deploy Frontend**

### Option A: Deploy to Vercel (Recommended - Easiest)

1. **Install Vercel CLI:**

```bash
npm install -g vercel
```

2. **Deploy Frontend:**

```bash
cd frontend
vercel
```

3. **Configure Environment Variables in Vercel:**

Go to Vercel Dashboard → Your Project → Settings → Environment Variables

Add:
```
NEXT_PUBLIC_API_URL=https://YOUR_API_GATEWAY_URL/dev
```

4. **Redeploy:**

```bash
vercel --prod
```

### Option B: Deploy to AWS Amplify

1. **Push code to GitHub** (already done!)

2. **Go to AWS Amplify Console:**
   - https://console.aws.amazon.com/amplify/

3. **Connect Repository:**
   - Click "New app" → "Host web app"
   - Choose GitHub
   - Select `thechetan9/SO-PatchPilot`
   - Select `main` branch

4. **Configure Build Settings:**

```yaml
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - cd frontend
        - npm install
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

5. **Add Environment Variables:**
   - `NEXT_PUBLIC_API_URL` = `https://YOUR_API_GATEWAY_URL/dev`

6. **Deploy!**

### Option C: Deploy to S3 + CloudFront

1. **Build Static Export:**

```bash
cd frontend
npm run build
```

2. **Create S3 Bucket:**

```bash
aws s3 mb s3://patchpilot-frontend
```

3. **Upload to S3:**

```bash
aws s3 sync .next/static s3://patchpilot-frontend/static
```

4. **Configure CloudFront** (manual setup in AWS Console)

---

## 🔐 **Step 7: Configure CORS**

Update `template.yaml` to add CORS configuration:

```yaml
PatchPilotApi:
  Type: AWS::Serverless::Api
  Properties:
    Name: !Sub 'patchpilot-api-${Environment}'
    StageName: !Ref Environment
    Cors:
      AllowMethods: "'GET,POST,PUT,OPTIONS'"
      AllowHeaders: "'Content-Type,Authorization'"
      AllowOrigin: "'*'"  # Change to your frontend URL in production
```

Redeploy:

```bash
sam build && sam deploy
```

---

## 📊 **Step 8: Verify Full Deployment**

### 1. Check Lambda Functions

```bash
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `patchpilot`)].FunctionName'
```

Should show:
- `patchpilot-webhook-dev`
- `patchpilot-plan-approval-dev`
- `patchpilot-health-check-dev`
- `patchpilot-dashboard-dev`

### 2. Check DynamoDB Tables

```bash
aws dynamodb list-tables --query 'TableNames[?contains(@, `Patch`)]'
```

Should show:
- `PatchPlans-dev`
- `PatchRuns-dev`

### 3. Check API Gateway

```bash
aws apigateway get-rest-apis --query 'items[?name==`patchpilot-api-dev`]'
```

### 4. Test End-to-End

1. Open frontend URL (Vercel/Amplify)
2. Dashboard should load
3. Create a test plan via webhook
4. Verify it appears in dashboard

---

## 💰 **Cost Estimation**

### AWS Free Tier (First 12 months):
- **Lambda**: 1M requests/month free
- **API Gateway**: 1M requests/month free
- **DynamoDB**: 25 GB storage free
- **Bedrock**: Pay per use (~$0.003 per 1K tokens)

### Estimated Monthly Cost (After Free Tier):
- **Lambda**: ~$0.20 (assuming 10K requests/month)
- **API Gateway**: ~$3.50 (assuming 10K requests/month)
- **DynamoDB**: ~$1.25 (assuming 1GB storage)
- **Bedrock**: ~$5-10 (depending on usage)
- **Total**: ~$10-15/month

---

## 🔍 **Monitoring & Logs**

### View Lambda Logs

```bash
sam logs -n WebhookFunction --stack-name patchpilot-stack --tail
```

### CloudWatch Logs

Go to: https://console.aws.amazon.com/cloudwatch/

Navigate to: Logs → Log groups → `/aws/lambda/patchpilot-*`

---

## 🚨 **Troubleshooting**

### Issue: SAM build fails

**Solution:**
```bash
# Use Docker container for consistent builds
sam build --use-container
```

### Issue: Lambda timeout

**Solution:** Increase timeout in `template.yaml`:
```yaml
Globals:
  Function:
    Timeout: 900  # 15 minutes max
```

### Issue: Bedrock access denied

**Solution:** Verify IAM role has Bedrock permissions and model access is enabled

### Issue: CORS errors

**Solution:** Add CORS configuration to API Gateway (see Step 7)

---

## 🎉 **Deployment Complete!**

Your PatchPilot is now live on AWS! 🚀

- **Backend**: AWS Lambda + API Gateway
- **Frontend**: Vercel/Amplify/S3
- **Database**: DynamoDB
- **AI**: AWS Bedrock (Claude 3.5 Haiku)

---

## 📞 **Next Steps**

1. ✅ Set up custom domain (Route 53)
2. ✅ Configure SSL certificates (ACM)
3. ✅ Set up monitoring alerts (CloudWatch)
4. ✅ Enable AWS WAF for security
5. ✅ Set up CI/CD pipeline (GitHub Actions)
6. ✅ Configure backup strategy (DynamoDB backups)

---

**Happy Deploying! 🎊**

