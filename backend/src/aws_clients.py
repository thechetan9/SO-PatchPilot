"""
AWS Service Clients
Handles connections to Lambda, Step Functions, DynamoDB, Bedrock, etc.
"""
import boto3
import os
from config import AWS_REGION, DYNAMODB_TABLE_PATCH_RUNS, DYNAMODB_TABLE_PLANS
from logger import logger

# In Lambda, use IAM role credentials. For local dev, use explicit credentials
def _get_boto3_kwargs():
    """Get boto3 client kwargs - use IAM role in Lambda, explicit creds locally"""
    kwargs = {'region_name': AWS_REGION}

    # Only add explicit credentials if they're available (local dev)
    access_key = os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    session_token = os.getenv("AWS_SESSION_TOKEN")

    if access_key and secret_key:
        kwargs['aws_access_key_id'] = access_key
        kwargs['aws_secret_access_key'] = secret_key
        if session_token:
            kwargs['aws_session_token'] = session_token

    return kwargs

# Initialize AWS clients
def get_bedrock_client():
    """Get Bedrock client for Claude model"""
    return boto3.client('bedrock-runtime', **_get_boto3_kwargs())

def get_dynamodb_client():
    """Get DynamoDB client"""
    return boto3.client('dynamodb', **_get_boto3_kwargs())

def get_dynamodb_resource():
    """Get DynamoDB resource for table operations"""
    return boto3.resource('dynamodb', **_get_boto3_kwargs())

def get_ssm_client():
    """Get Systems Manager client"""
    return boto3.client('ssm', **_get_boto3_kwargs()
    )

def get_stepfunctions_client():
    """Get Step Functions client"""
    return boto3.client('stepfunctions', **_get_boto3_kwargs())

def get_lambda_client():
    """Get Lambda client"""
    return boto3.client('lambda', **_get_boto3_kwargs())

def get_cloudwatch_client():
    """Get CloudWatch client"""
    return boto3.client('cloudwatch', **_get_boto3_kwargs())

def get_securityhub_client():
    """Get Security Hub client"""
    return boto3.client('securityhub', **_get_boto3_kwargs())

# Initialize DynamoDB resource lazily
_dynamodb = None

def get_dynamodb():
    """Get or initialize DynamoDB resource"""
    global _dynamodb
    if _dynamodb is None:
        try:
            _dynamodb = get_dynamodb_resource()
        except Exception as e:
            logger.error(f"Failed to initialize DynamoDB: {str(e)}")
            _dynamodb = None
    return _dynamodb

# Alias for backward compatibility
dynamodb = get_dynamodb

def ensure_dynamodb_tables():
    """Ensure DynamoDB tables exist"""
    dynamodb = get_dynamodb_resource()
    
    # Create PatchRuns table if it doesn't exist
    try:
        table = dynamodb.Table(DYNAMODB_TABLE_PATCH_RUNS)
        table.load()
        logger.info(f"Table {DYNAMODB_TABLE_PATCH_RUNS} already exists")
    except:
        logger.info(f"Creating table {DYNAMODB_TABLE_PATCH_RUNS}")
        dynamodb.create_table(
            TableName=DYNAMODB_TABLE_PATCH_RUNS,
            KeySchema=[
                {'AttributeName': 'patch_run_id', 'KeyType': 'HASH'},
                {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'patch_run_id', 'AttributeType': 'S'},
                {'AttributeName': 'created_at', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
    
    # Create PatchPlans table if it doesn't exist
    try:
        table = dynamodb.Table(DYNAMODB_TABLE_PLANS)
        table.load()
        logger.info(f"Table {DYNAMODB_TABLE_PLANS} already exists")
    except:
        logger.info(f"Creating table {DYNAMODB_TABLE_PLANS}")
        dynamodb.create_table(
            TableName=DYNAMODB_TABLE_PLANS,
            KeySchema=[
                {'AttributeName': 'plan_id', 'KeyType': 'HASH'},
                {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'plan_id', 'AttributeType': 'S'},
                {'AttributeName': 'created_at', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )

