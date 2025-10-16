"""
Create DynamoDB tables for PatchPilot
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'src'))

from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError

# Load environment variables
load_dotenv('backend/.env')

def create_patch_plans_table():
    """Create PatchPlans table"""
    dynamodb = boto3.client('dynamodb', region_name=os.getenv('AWS_REGION', 'us-east-1'))
    table_name = os.getenv('DYNAMODB_TABLE_PLANS', 'PatchPlans-dev')
    
    try:
        print(f"Creating table: {table_name}...")
        
        response = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'plan_id', 'KeyType': 'HASH'},  # Partition key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'plan_id', 'AttributeType': 'S'},
                {'AttributeName': 'ticket_id', 'AttributeType': 'S'},
                {'AttributeName': 'created_at', 'AttributeType': 'S'},
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'ticket_id-index',
                    'KeySchema': [
                        {'AttributeName': 'ticket_id', 'KeyType': 'HASH'},
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                },
                {
                    'IndexName': 'created_at-index',
                    'KeySchema': [
                        {'AttributeName': 'created_at', 'KeyType': 'HASH'},
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            },
            Tags=[
                {'Key': 'Project', 'Value': 'PatchPilot'},
                {'Key': 'Environment', 'Value': 'dev'}
            ]
        )
        
        print(f"✅ Table {table_name} created successfully!")
        return True
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"⚠️  Table {table_name} already exists")
            return True
        else:
            print(f"❌ Error creating table: {e}")
            return False

def create_patch_runs_table():
    """Create PatchRuns table"""
    dynamodb = boto3.client('dynamodb', region_name=os.getenv('AWS_REGION', 'us-east-1'))
    table_name = os.getenv('DYNAMODB_TABLE_PATCH_RUNS', 'PatchRuns-dev')
    
    try:
        print(f"Creating table: {table_name}...")
        
        response = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'run_id', 'KeyType': 'HASH'},  # Partition key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'run_id', 'AttributeType': 'S'},
                {'AttributeName': 'plan_id', 'AttributeType': 'S'},
                {'AttributeName': 'started_at', 'AttributeType': 'S'},
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'plan_id-index',
                    'KeySchema': [
                        {'AttributeName': 'plan_id', 'KeyType': 'HASH'},
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                },
                {
                    'IndexName': 'started_at-index',
                    'KeySchema': [
                        {'AttributeName': 'started_at', 'KeyType': 'HASH'},
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            },
            Tags=[
                {'Key': 'Project', 'Value': 'PatchPilot'},
                {'Key': 'Environment', 'Value': 'dev'}
            ]
        )
        
        print(f"✅ Table {table_name} created successfully!")
        return True
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"⚠️  Table {table_name} already exists")
            return True
        else:
            print(f"❌ Error creating table: {e}")
            return False

def create_executions_table():
    """Create PatchPilotExecutions table"""
    dynamodb = boto3.client('dynamodb', region_name=os.getenv('AWS_REGION', 'us-east-1'))
    table_name = os.getenv('DYNAMODB_TABLE', 'PatchPilotExecutions-dev')
    
    try:
        print(f"Creating table: {table_name}...")
        
        response = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'execution_id', 'KeyType': 'HASH'},  # Partition key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'execution_id', 'AttributeType': 'S'},
                {'AttributeName': 'ticket_id', 'AttributeType': 'S'},
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'ticket_id-index',
                    'KeySchema': [
                        {'AttributeName': 'ticket_id', 'KeyType': 'HASH'},
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            },
            Tags=[
                {'Key': 'Project', 'Value': 'PatchPilot'},
                {'Key': 'Environment', 'Value': 'dev'}
            ]
        )
        
        print(f"✅ Table {table_name} created successfully!")
        return True
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"⚠️  Table {table_name} already exists")
            return True
        else:
            print(f"❌ Error creating table: {e}")
            return False

def wait_for_tables():
    """Wait for tables to become active"""
    dynamodb = boto3.client('dynamodb', region_name=os.getenv('AWS_REGION', 'us-east-1'))
    
    tables = [
        os.getenv('DYNAMODB_TABLE_PLANS', 'PatchPlans-dev'),
        os.getenv('DYNAMODB_TABLE_PATCH_RUNS', 'PatchRuns-dev'),
        os.getenv('DYNAMODB_TABLE', 'PatchPilotExecutions-dev')
    ]
    
    print("\nWaiting for tables to become active...")
    
    for table_name in tables:
        try:
            waiter = dynamodb.get_waiter('table_exists')
            waiter.wait(TableName=table_name)
            print(f"✅ {table_name} is active")
        except Exception as e:
            print(f"⚠️  Error waiting for {table_name}: {e}")

def main():
    print("\n🚀 PatchPilot - DynamoDB Table Creation\n")
    print("=" * 50)
    
    # Create tables
    plans_ok = create_patch_plans_table()
    runs_ok = create_patch_runs_table()
    exec_ok = create_executions_table()
    
    if plans_ok and runs_ok and exec_ok:
        wait_for_tables()
        
        print("\n" + "=" * 50)
        print("🎉 All DynamoDB tables are ready!")
        print("=" * 50)
        print("\nYou can now use PatchPilot with real AWS services!")
        print("\nNext steps:")
        print("1. Test the backend: cd backend && python -m src.api")
        print("2. Send a test webhook to trigger AI plan generation")
        print("3. Check DynamoDB tables in AWS Console")
    else:
        print("\n❌ Some tables failed to create. Check errors above.")

if __name__ == "__main__":
    main()

