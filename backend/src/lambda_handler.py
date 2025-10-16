"""
Lambda Handler for PatchPilot
Entry point for AWS Lambda functions
"""
import json
from decimal import Decimal
from datetime import datetime
from agent import PatchPilotAgent
from orchestrator import PatchOrchestrator
from logger import log_event, logger
from aws_clients import get_dynamodb
from config import DYNAMODB_TABLE, DYNAMODB_TABLE_PLANS

# Initialize agents lazily to avoid errors during Lambda cold start
agent = None
orchestrator = None

def get_agent():
    global agent
    if agent is None:
        try:
            agent = PatchPilotAgent()
        except Exception as e:
            logger.error(f"Failed to initialize agent: {str(e)}")
            agent = None
    return agent

def get_orchestrator():
    global orchestrator
    if orchestrator is None:
        try:
            orchestrator = PatchOrchestrator()
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {str(e)}")
            orchestrator = None
    return orchestrator

def decimal_to_float(obj):
    """Convert Decimal objects to float for JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_float(item) for item in obj]
    return obj

def webhook_handler(event, context):
    """
    Lambda handler for SuperOps webhook
    Receives patch/vulnerability notifications
    """
    try:
        logger.info(f"Webhook received: {json.dumps(event)}")
        
        # Parse webhook payload
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', event)
        
        # Process webhook
        agent_instance = get_agent()
        if not agent_instance:
            raise Exception("Failed to initialize agent")
        result = agent_instance.process_webhook(body)
        
        return {
            "statusCode": 200,
            "body": json.dumps(result),
            "headers": {
                "Content-Type": "application/json"
            }
        }
    
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
            "headers": {
                "Content-Type": "application/json"
            }
        }

def plan_approval_handler(event, context):
    """
    Lambda handler for plan approval
    Called when user approves a patch plan
    """
    try:
        logger.info(f"Plan approval received: {json.dumps(event)}")

        body = json.loads(event['body']) if isinstance(event.get('body'), str) else event.get('body', event)

        plan_id = body.get('plan_id')
        ticket_id = body.get('ticket_id')
        client_id = body.get('client_id')
        plan = body.get('plan', {})
        approved = body.get('approved', False)

        if approved:
            log_event("plan_approved", {
                "plan_id": plan_id,
                "ticket_id": ticket_id
            })

            # Trigger Step Functions execution
            orchestrator_instance = get_orchestrator()
            if not orchestrator_instance:
                raise Exception("Failed to initialize orchestrator")
            execution_result = orchestrator_instance.start_execution(
                plan_id=plan_id,
                plan=plan,
                ticket_id=ticket_id,
                client_id=client_id
            )

            return {
                "statusCode": 200,
                "body": json.dumps({
                    "status": "approved",
                    "plan_id": plan_id,
                    "execution_arn": execution_result.get("execution_arn"),
                    "message": "Plan approved, execution started"
                })
            }
        else:
            log_event("plan_rejected", {
                "plan_id": plan_id,
                "ticket_id": ticket_id
            })
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "status": "rejected",
                    "plan_id": plan_id,
                    "message": "Plan rejected"
                })
            }

    except Exception as e:
        logger.error(f"Error processing plan approval: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

def health_check_handler(event, context):
    """
    Lambda handler for health checks during patch execution
    Called by Step Functions to validate batch health
    """
    try:
        batch_id = event.get('batch_id')
        device_ids = event.get('device_ids', [])
        health_threshold = event.get('health_threshold_percent', 95.0)

        # Perform health check
        health_result = orchestrator.check_batch_health(
            batch_id=batch_id,
            device_ids=device_ids,
            health_threshold_percent=health_threshold
        )

        return health_result

    except Exception as e:
        logger.error(f"Error performing health check: {str(e)}")
        raise


def execute_batch_handler(event, context):
    """
    Lambda handler for executing patch batch
    Called by Step Functions to execute patches on devices
    """
    try:
        batch_id = event.get('batch_id')
        device_ids = event.get('device_ids', [])
        patch_ids = event.get('patch_ids', [])

        # Execute batch
        execution_result = orchestrator.execute_canary_batch(
            batch_id=batch_id,
            device_ids=device_ids,
            patch_ids=patch_ids
        )

        return execution_result

    except Exception as e:
        logger.error(f"Error executing batch: {str(e)}")
        raise


def rollback_handler(event, context):
    """
    Lambda handler for rollback
    Called by Step Functions when health check fails
    """
    try:
        batch_id = event.get('batch_id')
        device_ids = event.get('device_ids', [])

        # Execute rollback
        rollback_result = orchestrator.rollback_batch(
            batch_id=batch_id,
            device_ids=device_ids
        )

        return rollback_result

    except Exception as e:
        logger.error(f"Error rolling back batch: {str(e)}")
        raise


def dashboard_handler(event, context):
    """
    Lambda handler for dashboard API
    Handles all dashboard-related requests
    """
    try:
        logger.info(f"Dashboard request: {json.dumps(event)}")

        # Get HTTP method and path
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '')

        # Route to appropriate handler
        if path == '/api/dashboard/plans' and http_method == 'GET':
            try:
                # Get query parameters
                params = event.get('queryStringParameters') or {}
                status = params.get('status')

                # Query DynamoDB directly
                db = get_dynamodb()
                if not db:
                    raise Exception("Failed to initialize DynamoDB")
                plans_table = db.Table(DYNAMODB_TABLE_PLANS)
                response = plans_table.scan()
                all_plans = response.get('Items', [])

                if status == 'proposed':
                    open_plans = [
                        decimal_to_float(plan) for plan in all_plans
                        if plan.get("status") == "proposed"
                    ]
                    result = {
                        "open_plans": open_plans,
                        "total": len(open_plans)
                    }
                else:
                    result = {
                        "all_plans": [decimal_to_float(plan) for plan in all_plans],
                        "total": len(all_plans)
                    }

                return {
                    "statusCode": 200,
                    "body": json.dumps(result),
                    "headers": {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*"
                    }
                }
            except Exception as e:
                logger.error(f"Error fetching plans: {str(e)}")
                return {
                    "statusCode": 500,
                    "body": json.dumps({"error": str(e)}),
                    "headers": {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*"
                    }
                }

        elif path.startswith('/api/dashboard/plans/') and http_method == 'PUT':
            # Update plan
            plan_id = event.get('pathParameters', {}).get('plan_id')
            body = json.loads(event['body']) if isinstance(event.get('body'), str) else event.get('body', {})

            result = update_plan(plan_id, body)

            return {
                "statusCode": 200,
                "body": json.dumps(result),
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                }
            }

        elif path == '/api/dashboard/runs' and http_method == 'GET':
            try:
                # Query DynamoDB directly for patch runs
                db = get_dynamodb()
                if not db:
                    raise Exception("Failed to initialize DynamoDB")
                table = db.Table(DYNAMODB_TABLE)
                response = table.scan()
                all_runs = response.get('Items', [])

                # Filter runs
                in_progress = [
                    decimal_to_float(run) for run in all_runs
                    if run.get("status") in ["in_progress", "pending"]
                ]

                recent = [
                    decimal_to_float(run) for run in all_runs
                    if run.get("status") in ["completed", "failed"]
                ][:10]  # Last 10

                result = {
                    "in_progress": in_progress,
                    "recent": recent
                }

                return {
                    "statusCode": 200,
                    "body": json.dumps(result),
                    "headers": {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*"
                    }
                }
            except Exception as e:
                logger.error(f"Error fetching runs: {str(e)}")
                return {
                    "statusCode": 500,
                    "body": json.dumps({"error": str(e)}),
                    "headers": {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*"
                    }
                }

        elif path == '/api/dashboard/kpis' and http_method == 'GET':
            try:
                # Return KPI summary
                result = {
                    "total_plans": 0,
                    "approved_plans": 0,
                    "rejected_plans": 0,
                    "in_progress_runs": 0,
                    "completed_runs": 0,
                    "failed_runs": 0
                }
                return {
                    "statusCode": 200,
                    "body": json.dumps(result),
                    "headers": {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*"
                    }
                }
            except Exception as e:
                logger.error(f"Error fetching KPIs: {str(e)}")
                return {
                    "statusCode": 500,
                    "body": json.dumps({"error": str(e)}),
                    "headers": {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*"
                    }
                }

        elif path == '/api/dashboard/plans/history' and http_method == 'GET':
            try:
                # Query DynamoDB for all plans
                db = get_dynamodb()
                if not db:
                    raise Exception("Failed to initialize DynamoDB")
                plans_table = db.Table(DYNAMODB_TABLE_PLANS)
                response = plans_table.scan()
                all_plans = response.get('Items', [])

                result = {
                    "all_plans": [decimal_to_float(plan) for plan in all_plans],
                    "total": len(all_plans)
                }
                return {
                    "statusCode": 200,
                    "body": json.dumps(result),
                    "headers": {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*"
                    }
                }
            except Exception as e:
                logger.error(f"Error fetching plans history: {str(e)}")
                return {
                    "statusCode": 500,
                    "body": json.dumps({"error": str(e)}),
                    "headers": {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*"
                    }
                }

        elif path == '/api/dashboard/plans/generate' and http_method == 'POST':
            body = json.loads(event['body']) if isinstance(event.get('body'), str) else event.get('body', {})
            # For now, return a mock response - you can implement actual plan generation
            result = {
                "success": True,
                "message": "Plan generation endpoint - implement with your logic"
            }

            return {
                "statusCode": 200,
                "body": json.dumps(result),
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                }
            }

        elif path == '/api/dashboard/plans/update' and http_method == 'POST':
            try:
                body = json.loads(event['body']) if isinstance(event.get('body'), str) else event.get('body', {})
                plan_id = body.get('plan_id')

                # Update plan in DynamoDB
                db = get_dynamodb()
                if not db:
                    raise Exception("Failed to initialize DynamoDB")
                plans_table = db.Table(DYNAMODB_TABLE_PLANS)
                plans_table.update_item(
                    Key={'plan_id': plan_id, 'created_at': body.get('created_at', '')},
                    UpdateExpression='SET #status = :status, #updated_at = :updated_at',
                    ExpressionAttributeNames={'#status': 'status', '#updated_at': 'updated_at'},
                    ExpressionAttributeValues={':status': body.get('status', 'proposed'), ':updated_at': datetime.utcnow().isoformat()}
                )

                result = {"success": True, "message": f"Plan {plan_id} updated"}
                return {
                    "statusCode": 200,
                    "body": json.dumps(result),
                    "headers": {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*"
                    }
                }
            except Exception as e:
                logger.error(f"Error updating plan: {str(e)}")
                return {
                    "statusCode": 500,
                    "body": json.dumps({"error": str(e)}),
                    "headers": {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*"
                    }
                }

        elif path == '/api/dashboard/approve-plan' and http_method == 'POST':
            body = json.loads(event['body']) if isinstance(event.get('body'), str) else event.get('body', {})
            plan_id = body.get('plan_id')
            # For now, return a mock response - implement actual approval logic
            result = {
                "success": True,
                "message": f"Plan {plan_id} approved"
            }

            return {
                "statusCode": 200,
                "body": json.dumps(result),
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                }
            }

        elif path == '/api/dashboard/reject-plan' and http_method == 'POST':
            body = json.loads(event['body']) if isinstance(event.get('body'), str) else event.get('body', {})
            plan_id = body.get('plan_id')
            # For now, return a mock response - implement actual rejection logic
            result = {
                "success": True,
                "message": f"Plan {plan_id} rejected"
            }

            return {
                "statusCode": 200,
                "body": json.dumps(result),
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                }
            }

        else:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "Not found", "path": path, "method": http_method}),
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                }
            }

    except Exception as e:
        logger.error(f"Error in dashboard handler: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            }
        }

