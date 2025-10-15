"""
AWS Service Clients
Handles connections to Lambda, Step Functions, DynamoDB, Bedrock, etc.
"""
import boto3
from src.config import (
    AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 
    AWS_SESSION_TOKEN, DYNAMODB_TABLE_PATCH_RUNS, DYNAMODB_TABLE_PLANS
)
from src.logger import logger

# Initialize AWS clients
def get_bedrock_client():
    """Get Bedrock client for Claude model"""
    return boto3.client(
        'bedrock-runtime',
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        aws_session_token=AWS_SESSION_TOKEN
    )

def get_dynamodb_client():
    """Get DynamoDB client"""
    return boto3.client(
        'dynamodb',
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        aws_session_token=AWS_SESSION_TOKEN
    )

def get_dynamodb_resource():
    """Get DynamoDB resource for table operations"""
    return boto3.resource(
        'dynamodb',
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        aws_session_token=AWS_SESSION_TOKEN
    )

def get_ssm_client():
    """Get Systems Manager client"""
    return boto3.client(
        'ssm',
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        aws_session_token=AWS_SESSION_TOKEN
    )

def get_stepfunctions_client():
    """Get Step Functions client"""
    return boto3.client(
        'stepfunctions',
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        aws_session_token=AWS_SESSION_TOKEN
    )

def get_lambda_client():
    """Get Lambda client"""
    return boto3.client(
        'lambda',
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        aws_session_token=AWS_SESSION_TOKEN
    )

def get_cloudwatch_client():
    """Get CloudWatch client"""
    return boto3.client(
        'cloudwatch',
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        aws_session_token=AWS_SESSION_TOKEN
    )

def get_securityhub_client():
    """Get Security Hub client"""
    return boto3.client(
        'securityhub',
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        aws_session_token=AWS_SESSION_TOKEN
    )

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

