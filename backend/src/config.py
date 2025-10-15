import os
from dotenv import load_dotenv

load_dotenv()

# AWS Configuration
AWS_REGION = os.getenv("AWS_REGION", "us-east-2")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_SESSION_TOKEN = os.getenv("AWS_SESSION_TOKEN")

# Bedrock Configuration
# Using Haiku for cost-effective intelligent planning
# Cost: $0.001 per 1K input tokens (vs $0.003 for Sonnet)
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-5-haiku-20241022-v1:0")

# SuperOps Configuration (Mock)
SUPEROPS_API_URL = os.getenv("SUPEROPS_API_URL", "https://api.superops.ai")
SUPEROPS_API_KEY = os.getenv("SUPEROPS_API_KEY", "mock_key_for_demo")

# DynamoDB Configuration
DYNAMODB_TABLE_PATCH_RUNS = os.getenv("DYNAMODB_TABLE_PATCH_RUNS", "PatchRuns")
DYNAMODB_TABLE_PLANS = os.getenv("DYNAMODB_TABLE_PLANS", "PatchPlans")
DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE", "PatchPilotExecutions")

# Step Functions Configuration
STEP_FUNCTIONS_ARN = os.getenv("STEP_FUNCTIONS_ARN", "arn:aws:states:us-east-2:ACCOUNT_ID:stateMachine:PatchPilotOrchestrator")

# Application Configuration
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

