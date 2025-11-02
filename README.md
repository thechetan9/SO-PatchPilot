# PatchPilot - Agentic Patch & Vulnerability Orchestrator

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 15](https://img.shields.io/badge/Next.js-15-black)](https://nextjs.org/)
[![AWS Bedrock](https://img.shields.io/badge/AWS-Bedrock-orange)](https://aws.amazon.com/bedrock/)
[![Tests](https://img.shields.io/badge/tests-18%20passing-brightgreen)](./backend/tests/)

An AI-powered patch management system that uses AWS Bedrock (Claude) to intelligently orchestrate patch deployments across your infrastructure.

## 🚀 Live Demo

**Frontend Dashboard**: https://frontend-p3j6s21fk-thechetan9s-projects.vercel.app/
**Backend API**: https://byeh9xee0k.execute-api.us-east-1.amazonaws.com/dev

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
SO-PatchPilot/
├── backend/                    # Python API & Core Logic
│   ├── src/                    # Source code
│   │   ├── agent.py           # AI-powered plan generation
│   │   ├── orchestrator.py    # Step Functions & SSM integration
│   │   ├── dashboard_api.py   # Flask API endpoints
│   │   ├── ticket_manager.py  # SuperOps integration
│   │   ├── lambda_handler.py  # AWS Lambda entry point
│   │   ├── api.py             # Flask API server
│   │   ├── config.py          # Configuration
│   │   ├── aws_clients.py     # AWS service clients
│   │   ├── superops_client.py # SuperOps client (Mock)
│   │   └── logger.py          # Logging utilities
│   ├── tests/                 # Test suite (18 tests)
│   │   ├── test_agent.py
│   │   ├── test_orchestrator.py
│   │   └── test_ticket_manager.py
│   ├── venv/                  # Virtual environment (not in git)
│   └── requirements.txt       # Python dependencies
├── frontend/                   # Next.js 15 + React 19 + TypeScript
│   ├── src/
│   │   ├── app/               # Next.js app directory
│   │   └── components/        # React components
│   ├── public/                # Static assets
│   ├── package.json
│   └── ...
├── .github/workflows/         # CI/CD pipelines
│   ├── ci.yml                 # Continuous Integration
│   └── deploy.yml             # Deployment workflow
├── .gitignore                 # Git ignore rules
├── .env.example               # Environment variables template
├── README.md                  # This file
├── LICENSE                    # MIT License
├── template.yaml              # AWS SAM template
├── quickstart.ps1             # PowerShell script for quick start
└── create_dynamodb_tables.py  # DynamoDB setup script
```

## Setup

### Prerequisites

- Python 3.9+
- Node.js 18+
- AWS Account with Bedrock access
- Windows 11 (or any OS)

### Quick Start (Windows)

**Using PowerShell Quick Start Script:**

```powershell
.\quickstart.ps1
```

**Or Manual Setup:**

#### 1. Clone the repository

```bash
git clone https://github.com/thechetan9/SO-PatchPilot.git
cd SO-PatchPilot
```

#### 2. Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows CMD
# or
.\venv\Scripts\Activate.ps1  # PowerShell
# or
source venv/Scripts/activate  # Git Bash

pip install -r requirements.txt
```

#### 3. Frontend Setup

**Note**: Use PowerShell or CMD (npm doesn't work in Git Bash)

```powershell
cd frontend
npm install
```

#### 4. Configure AWS credentials (Optional for local testing)

Create `backend/.env` file (copy from `.env.example`):

```bash
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_SESSION_TOKEN=your_session_token
AWS_REGION=us-east-2
BEDROCK_MODEL_ID=anthropic.claude-3-5-haiku-20241022-v1:0
```

**Note**: The app works with mock data even without AWS credentials!

#### 5. Run tests

```bash
cd backend
pytest tests/ -v
# Expected: 18 tests should pass
```

#### 6. Start the application

**Backend** (Terminal 1):

```bash
cd backend
python -m src.api
# Runs on http://localhost:5000
```

**Frontend** (Terminal 2 - use PowerShell/CMD):

```powershell
cd frontend
npm run dev
# Runs on http://localhost:3000
```

## Usage

### Local Testing

#### Test Backend API

```bash
# Start the Flask API (if not already running)
cd backend
python -m src.api
```

Visit <http://localhost:5000/health> to verify it's running.

#### Test with Sample Webhook

Use curl to test the webhook:

```bash
curl -X POST http://localhost:5000/webhook/superops \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "TICKET-001",
    "client_id": "client-a",
    "device_ids": ["dev-001", "dev-002"],
    "cve_findings": []
  }'
```

#### Test Frontend

**Local Development**: Open <http://localhost:3000> in your browser to see the dashboard.

**Live Production**: Visit the deployed dashboard at <https://frontend-p3j6s21fk-thechetan9s-projects.vercel.app/>

### Deploy to AWS

```bash
# Package Lambda functions
sam build

# Deploy
sam deploy --guided
```

After deployment, update your SuperOps webhook URL to point to the API Gateway endpoint.

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

## AWS Setup

### AWS Prerequisites

- AWS Account with Administrator access
- AWS Bedrock access enabled (request access to Claude 3.5 Haiku in AWS Console)

### Quick AWS Setup

1. **Configure AWS credentials** in `backend/.env`:

   ```env
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AWS_REGION=us-east-1
   BEDROCK_MODEL_ID=us.anthropic.claude-3-5-haiku-20241022-v1:0
   ```

2. **Create DynamoDB tables**:

   ```bash
   python create_dynamodb_tables.py
   ```

3. **Enable Bedrock access**:
   - Go to AWS Bedrock Console
   - Navigate to "Model access"
   - Request access to Claude 3.5 Haiku

### AWS Services Used

- **AWS Bedrock** - Claude 3.5 Sonnet for AI-powered plan generation
- **DynamoDB** - Storage for patch plans and execution history
- **Lambda** - Serverless function execution (for production deployment)
- **Step Functions** - Workflow orchestration (for production deployment)
- **Systems Manager** - Patch execution on EC2 instances

## API Endpoints

### Backend API (Port 5000)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/devices?client_id=<id>` | GET | Get devices for a client |
| `/webhook/superops` | POST | Receive SuperOps webhook |
| `/plan/approve` | POST | Approve a patch plan |
| `/health-check` | POST | Perform health check |
| `/api/dashboard/plans` | GET | Get all patch plans |
| `/api/dashboard/runs` | GET | Get all patch runs |
| `/api/dashboard/kpis` | GET | Get KPI summary |

## Testing

### Run All Tests

```bash
cd backend
pytest tests/ -v
```

**Expected Output**: 18 tests should pass

### Test Coverage

- `test_agent.py` - 6 tests for AI agent functionality
- `test_orchestrator.py` - 6 tests for patch orchestration
- `test_ticket_manager.py` - 6 tests for ticket management

## Roadmap

- [x] AI-powered patch plan generation
- [x] Mock SuperOps client for testing
- [x] Flask API with dashboard endpoints
- [x] Unit tests (18 tests)
- [x] Next.js dashboard UI
- [ ] Real SuperOps API integration
- [ ] Step Functions workflow implementation
- [ ] Device health monitoring
- [ ] Automatic rollback on failures
- [ ] Email/Slack notifications
- [ ] AWS deployment automation

## Security Notes

- ✅ Credentials stored in environment variables (never in code)
- ✅ `.env` file excluded from git
- ✅ AWS IAM roles for Lambda execution
- ✅ DynamoDB encryption at rest
- ✅ All API calls logged for audit trail
- ✅ Mock data used for local testing (no real credentials needed)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Additional Resources

- **AWS SAM Template**: See [template.yaml](template.yaml) for Lambda deployment
- **DynamoDB Setup**: See [create_dynamodb_tables.py](create_dynamodb_tables.py)
- **Quick Start Script**: See [quickstart.ps1](quickstart.ps1)

## Support

For issues, questions, or contributions, please open an issue on GitHub.

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

**Built with ❤️ using AWS Bedrock, Claude 3.5 Haiku, Next.js, and Python**
