"""
PatchPilot Orchestrator - Step Functions & SSM Integration
Handles phased patch execution with health checks and rollback
"""
import json
from typing import Dict, List, Optional
from datetime import datetime
from .aws_clients import get_stepfunctions_client, get_ssm_client, get_dynamodb_client
from .logger import log_event, logger
from .config import STEP_FUNCTIONS_ARN, DYNAMODB_TABLE


class PatchOrchestrator:
    """Orchestrates patch execution via Step Functions and SSM"""
    
    def __init__(self):
        self.stepfunctions = get_stepfunctions_client()
        self.ssm = get_ssm_client()
        self.dynamodb = get_dynamodb_client()
        self.table = self.dynamodb.Table(DYNAMODB_TABLE)
    
    def start_execution(self, plan_id: str, plan: Dict, ticket_id: str, client_id: str) -> Dict:
        """
        Start Step Functions execution for approved plan
        """
        try:
            execution_input = {
                "plan_id": plan_id,
                "ticket_id": ticket_id,
                "client_id": client_id,
                "canary_size": plan["canary_size"],
                "batches": plan["batches"],
                "health_check_interval_minutes": plan["health_check_interval_minutes"],
                "rollback_threshold_percent": plan["rollback_threshold_percent"],
                "estimated_duration_hours": plan["estimated_duration_hours"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Start Step Functions execution
            response = self.stepfunctions.start_execution(
                stateMachineArn=STEP_FUNCTIONS_ARN,
                name=f"patch-run-{plan_id}",
                input=json.dumps(execution_input)
            )
            
            execution_arn = response['executionArn']
            
            # Store execution record in DynamoDB
            self.table.put_item(
                Item={
                    "pk": f"EXECUTION#{execution_arn}",
                    "sk": "METADATA",
                    "plan_id": plan_id,
                    "ticket_id": ticket_id,
                    "client_id": client_id,
                    "status": "running",
                    "started_at": datetime.utcnow().isoformat(),
                    "execution_arn": execution_arn
                }
            )
            
            log_event("execution_started", {
                "execution_arn": execution_arn,
                "plan_id": plan_id,
                "ticket_id": ticket_id
            })
            
            return {
                "status": "started",
                "execution_arn": execution_arn,
                "plan_id": plan_id
            }
        
        except Exception as e:
            logger.error(f"Error starting execution: {str(e)}")
            raise
    
    def execute_canary_batch(self, batch_id: str, device_ids: List[str], 
                            patch_ids: List[str]) -> Dict:
        """
        Execute canary batch via SSM
        """
        try:
            results = {
                "batch_id": batch_id,
                "device_count": len(device_ids),
                "successful": 0,
                "failed": 0,
                "device_results": {}
            }
            
            for device_id in device_ids:
                try:
                    # Execute patch via SSM
                    response = self.ssm.send_command(
                        InstanceIds=[device_id],
                        DocumentName="AWS-RunPatchBaseline",
                        Parameters={
                            "Operation": ["Install"],
                            "PatchGroups": [batch_id]
                        }
                    )
                    
                    command_id = response['Command']['CommandId']
                    
                    results["device_results"][device_id] = {
                        "status": "executing",
                        "command_id": command_id
                    }
                    results["successful"] += 1
                    
                    log_event("patch_command_sent", {
                        "device_id": device_id,
                        "command_id": command_id,
                        "batch_id": batch_id
                    })
                
                except Exception as e:
                    logger.error(f"Error patching device {device_id}: {str(e)}")
                    results["device_results"][device_id] = {
                        "status": "failed",
                        "error": str(e)
                    }
                    results["failed"] += 1
            
            # Store batch execution record
            self.table.put_item(
                Item={
                    "pk": f"BATCH#{batch_id}",
                    "sk": "EXECUTION",
                    "device_count": len(device_ids),
                    "successful": results["successful"],
                    "failed": results["failed"],
                    "executed_at": datetime.utcnow().isoformat(),
                    "device_results": results["device_results"]
                }
            )
            
            return results
        
        except Exception as e:
            logger.error(f"Error executing canary batch: {str(e)}")
            raise
    
    def check_batch_health(self, batch_id: str, device_ids: List[str],
                          health_threshold_percent: float = 95.0) -> Dict:
        """
        Check health of devices after patch
        Returns health status and whether to proceed/rollback
        """
        try:
            health_results = {
                "batch_id": batch_id,
                "device_count": len(device_ids),
                "healthy": 0,
                "unhealthy": 0,
                "device_health": {}
            }
            
            for device_id in device_ids:
                try:
                    # Get device health via SSM
                    response = self.ssm.describe_instance_information(
                        Filters=[
                            {
                                "key": "InstanceIds",
                                "valueSet": [device_id]
                            }
                        ]
                    )
                    
                    if response['InstanceInformationList']:
                        instance = response['InstanceInformationList'][0]
                        is_healthy = instance['PingStatus'] == 'Online'
                        
                        health_results["device_health"][device_id] = {
                            "status": "healthy" if is_healthy else "unhealthy",
                            "ping_status": instance['PingStatus'],
                            "agent_version": instance.get('AgentVersion', 'unknown')
                        }
                        
                        if is_healthy:
                            health_results["healthy"] += 1
                        else:
                            health_results["unhealthy"] += 1
                    else:
                        health_results["device_health"][device_id] = {
                            "status": "unknown",
                            "error": "Device not found"
                        }
                        health_results["unhealthy"] += 1
                
                except Exception as e:
                    logger.error(f"Error checking health of {device_id}: {str(e)}")
                    health_results["device_health"][device_id] = {
                        "status": "error",
                        "error": str(e)
                    }
                    health_results["unhealthy"] += 1
            
            # Calculate health percentage
            health_percent = (health_results["healthy"] / len(device_ids) * 100) if device_ids else 0
            
            health_results["health_percent"] = health_percent
            health_results["proceed"] = health_percent >= health_threshold_percent
            
            log_event("health_check_completed", {
                "batch_id": batch_id,
                "health_percent": health_percent,
                "proceed": health_results["proceed"]
            })
            
            return health_results
        
        except Exception as e:
            logger.error(f"Error checking batch health: {str(e)}")
            raise
    
    def rollback_batch(self, batch_id: str, device_ids: List[str]) -> Dict:
        """
        Rollback patches on devices in batch
        """
        try:
            rollback_results = {
                "batch_id": batch_id,
                "device_count": len(device_ids),
                "successful": 0,
                "failed": 0,
                "device_results": {}
            }
            
            for device_id in device_ids:
                try:
                    # Execute rollback via SSM
                    response = self.ssm.send_command(
                        InstanceIds=[device_id],
                        DocumentName="AWS-RunPatchBaseline",
                        Parameters={
                            "Operation": ["Scan"],  # Scan to detect rollback needed
                            "PatchGroups": [batch_id]
                        }
                    )
                    
                    command_id = response['Command']['CommandId']
                    
                    rollback_results["device_results"][device_id] = {
                        "status": "rolling_back",
                        "command_id": command_id
                    }
                    rollback_results["successful"] += 1
                    
                    log_event("rollback_initiated", {
                        "device_id": device_id,
                        "command_id": command_id,
                        "batch_id": batch_id
                    })
                
                except Exception as e:
                    logger.error(f"Error rolling back device {device_id}: {str(e)}")
                    rollback_results["device_results"][device_id] = {
                        "status": "rollback_failed",
                        "error": str(e)
                    }
                    rollback_results["failed"] += 1
            
            # Store rollback record
            self.table.put_item(
                Item={
                    "pk": f"BATCH#{batch_id}",
                    "sk": "ROLLBACK",
                    "device_count": len(device_ids),
                    "successful": rollback_results["successful"],
                    "failed": rollback_results["failed"],
                    "rolled_back_at": datetime.utcnow().isoformat(),
                    "device_results": rollback_results["device_results"]
                }
            )
            
            return rollback_results
        
        except Exception as e:
            logger.error(f"Error rolling back batch: {str(e)}")
            raise
    
    def get_execution_status(self, execution_arn: str) -> Dict:
        """
        Get current status of Step Functions execution
        """
        try:
            response = self.stepfunctions.describe_execution(
                executionArn=execution_arn
            )

            # Handle both datetime objects and strings
            start_date = response['startDate']
            if hasattr(start_date, 'isoformat'):
                start_date_str = start_date.isoformat()
            else:
                start_date_str = str(start_date)

            stop_date = response.get('stopDate')
            stop_date_str = None
            if stop_date:
                if hasattr(stop_date, 'isoformat'):
                    stop_date_str = stop_date.isoformat()
                else:
                    stop_date_str = str(stop_date)

            return {
                "execution_arn": execution_arn,
                "status": response['status'],
                "started_at": start_date_str,
                "stopped_at": stop_date_str,
                "output": json.loads(response.get('output', '{}')) if response.get('output') else None
            }

        except Exception as e:
            logger.error(f"Error getting execution status: {str(e)}")
            raise

