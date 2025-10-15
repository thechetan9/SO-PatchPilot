# PatchPilot - Agentic Patch & Vulnerability Orchestrator

An AI-powered patch management system that uses AWS Bedrock (Claude) to intelligently orchestrate patch deployments across your infrastructure.

## Features

- **AI-Powered Planning**: Uses Claude 3.5 Haiku to generate intelligent patch plans
- **Canary-First Approach**: Automatically proposes safe, phased rollout strategies
- **SuperOps Integration**: Integrates with SuperOps for device inventory and SLA management
- **AWS Native**: Built on AWS Lambda, Step Functions, and DynamoDB
- **Mock SuperOps**: Includes mock SuperOps client for demo/testing

## Architecture

```text
SuperOps Webhook
    ↓
Lambda (webhook_handler)
    ↓
PatchPilot Agent
    ├─ Fetch Context (SuperOps, Security Hub)
    ├─ Generate Plan (Bedrock Claude)
    └─ Store Plan (DynamoDB)
    ↓
Update Ticket (SuperOps)
    ↓
User Approval
    ↓
Step Functions Execution
    ├─ Canary Batch
    ├─ Health Check
    ├─ Batch 1
    ├─ Health Check
    └─ Batch 2
```

## Project Structure

```text
patchpilot/
├── backend/                    # Python API & Core Logic
│   ├── src/                    # Source code
│   │   ├── agent.py           # AI-powered plan generation
│   │   ├── orchestrator.py    # Step Functions & SSM integration
│   │   ├── dashboard_api.py   # Flask API endpoints
│   │   ├── ticket_manager.py  # SuperOps integration
│   │   ├── lambda_handler.py  # AWS Lambda entry point
│   │   ├── config.py          # Configuration
│   │   ├── aws_clients.py     # AWS service clients
│   │   ├── superops_client.py # SuperOps client
│   │   └── logger.py          # Logging utilities
│   ├── tests/                 # Test suite
│   │   ├── test_agent.py
│   │   ├── test_orchestrator.py
│   │   └── test_ticket_manager.py
│   └── requirements.txt       # Python dependencies
├── frontend/                   # React/TypeScript UI
│   ├── src/
│   ├── package.json
│   └── ...
├── .github/workflows/         # CI/CD pipelines
├── README.md
└── LICENSE
```

## Setup

### Prerequisites

- Python 3.9+
- Node.js 18+
- AWS Account with Bedrock access
- Windows 11 (or any OS)

### Installation

1. **Clone the repository**

```bash
git clone <repo-url>
cd patchpilot
```

1. **Backend Setup**

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # On Windows
pip install -r requirements.txt
```

1. **Frontend Setup**

```bash
cd ../frontend
npm install
```

1. **Configure AWS credentials** (in `backend/` directory)

On Windows PowerShell:

```powershell
$env:AWS_ACCESS_KEY_ID = "your_access_key"
$env:AWS_SECRET_ACCESS_KEY = "your_secret_key"
$env:AWS_SESSION_TOKEN = "your_session_token"
$env:AWS_REGION = "us-east-2"
```

Or create `backend/.env` file:

```bash
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_SESSION_TOKEN=your_session_token
AWS_REGION=us-east-2
BEDROCK_MODEL_ID=anthropic.claude-3-5-haiku-20241022-v1:0
```

1. **Run tests** (from `backend/` directory)

```bash
pytest tests/ -v
```

1. **Start local API** (from `backend/` directory)

```bash
python -m src.api
```

## Usage

### Local Testing

```bash
# Start the Flask API
python -m src.api

# In another terminal, test the webhook
curl -X POST http://localhost:5000/webhook/superops \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "TICKET-001",
    "client_id": "client-a",
    "device_ids": ["dev-001", "dev-002"],
    "cve_findings": []
  }'
```

### Deploy to AWS

```bash
# Package Lambda functions
sam build

# Deploy
sam deploy --guided
```

## Key Components

### PatchPilotAgent

Main orchestrator that:

1. Receives webhooks from SuperOps
2. Fetches context (devices, SLAs, CVEs)
3. Generates intelligent patch plans using Claude
4. Stores plans in DynamoDB
5. Posts proposals to SuperOps tickets

### MockSuperOpsClient

Simulates SuperOps API for demo:

- Device inventory
- SLA policies
- Maintenance windows
- Ticket management
- CVE findings

### AWS Integration

- **Bedrock**: Claude model for plan generation
- **Lambda**: Serverless execution
- **Step Functions**: Orchestrate patch execution
- **DynamoDB**: Store plans and execution history
- **Systems Manager**: Execute patch commands
- **Security Hub**: CVE findings

## Next Steps

1. **Real SuperOps Integration**: Replace mock client with actual API calls
2. **Step Functions Workflow**: Implement patch execution orchestration
3. **Health Checks**: Add device health monitoring during patches
4. **Rollback Logic**: Implement automatic rollback on failures
5. **Notifications**: Add email/Slack notifications
6. **Dashboard**: Build web UI for plan review and approval

## Security Notes

- ✅ Credentials stored in environment variables (never in code)
- ✅ `.env` file excluded from git
- ✅ AWS IAM roles for Lambda execution
- ✅ DynamoDB encryption at rest
- ✅ All API calls logged for audit trail

## License

MIT
