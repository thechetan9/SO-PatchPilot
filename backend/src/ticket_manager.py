"""
PatchPilot Ticket Manager - Ticket Updates, Time Logging, and KPI Reporting
Handles SuperOps ticket lifecycle and reporting
"""
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from superops_client import get_superops_client
from aws_clients import get_dynamodb_client
from logger import log_event, logger
from config import DYNAMODB_TABLE


class TicketManager:
    """Manages ticket lifecycle and KPI reporting"""
    
    def __init__(self):
        self.superops = get_superops_client()
        self.dynamodb = get_dynamodb_client()
        self.table = self.dynamodb.Table(DYNAMODB_TABLE)
    
    def post_plan_proposal(self, ticket_id: str, plan: Dict, plan_id: str) -> Dict:
        """
        Post plan proposal to SuperOps ticket
        Includes approval/rejection options
        """
        try:
            plan_summary = f"""
**PATCHPILOT PLAN PROPOSAL**

Plan ID: {plan_id}
Generated: {datetime.utcnow().isoformat()}

**Execution Strategy:**
- Canary Batch: {plan['canary_size']} devices (5-10% of fleet)
- Batch 1: {plan['batches'][0] if len(plan['batches']) > 0 else 'N/A'} devices (30%)
- Batch 2: {plan['batches'][1] if len(plan['batches']) > 1 else 'N/A'} devices (remaining)

**Safety Measures:**
- Health Check Interval: {plan['health_check_interval_minutes']} minutes
- Rollback Threshold: {plan['rollback_threshold_percent']}% failure rate
- Estimated Duration: {plan['estimated_duration_hours']} hours

**Notes:**
{plan.get('notes', 'Standard patch plan')}

---
**Actions:**
- [APPROVE] - Start execution
- [REQUEST CHANGES] - Modify plan
- [DECLINE] - Reject plan
"""
            
            # Update ticket with plan proposal
            self.superops.update_ticket(ticket_id, {
                "status": "pending_approval",
                "plan_proposal": plan_summary,
                "plan_id": plan_id
            })
            
            log_event("plan_proposal_posted", {
                "ticket_id": ticket_id,
                "plan_id": plan_id
            })
            
            return {
                "status": "posted",
                "ticket_id": ticket_id,
                "plan_id": plan_id
            }
        
        except Exception as e:
            logger.error(f"Error posting plan proposal: {str(e)}")
            raise
    
    def update_execution_status(self, ticket_id: str, execution_arn: str, 
                               status: str, batch_info: Dict = None) -> Dict:
        """
        Update ticket with execution status
        Called during patch execution
        """
        try:
            status_message = f"""
**EXECUTION STATUS UPDATE**

Execution ARN: {execution_arn}
Status: {status.upper()}
Updated: {datetime.utcnow().isoformat()}

"""
            
            if batch_info:
                status_message += f"""**Current Batch:**
- Batch ID: {batch_info.get('batch_id')}
- Devices: {batch_info.get('device_count', 0)}
- Successful: {batch_info.get('successful', 0)}
- Failed: {batch_info.get('failed', 0)}
- Health: {batch_info.get('health_percent', 0):.1f}%
"""
            
            # Update ticket
            self.superops.update_ticket(ticket_id, {
                "status": f"executing_{status}",
                "execution_status": status_message,
                "execution_arn": execution_arn
            })
            
            log_event("execution_status_updated", {
                "ticket_id": ticket_id,
                "execution_arn": execution_arn,
                "status": status
            })
            
            return {
                "status": "updated",
                "ticket_id": ticket_id
            }
        
        except Exception as e:
            logger.error(f"Error updating execution status: {str(e)}")
            raise
    
    def log_technician_time(self, ticket_id: str, hours: float, 
                           description: str = "Patch execution") -> Dict:
        """
        Log technician time to SuperOps ticket
        """
        try:
            # Create time entry
            time_entry = {
                "ticket_id": ticket_id,
                "hours": hours,
                "description": description,
                "logged_at": datetime.utcnow().isoformat(),
                "logged_by": "PatchPilot Agent"
            }
            
            # Store in DynamoDB
            self.table.put_item(
                Item={
                    "pk": f"TIME_ENTRY#{ticket_id}",
                    "sk": datetime.utcnow().isoformat(),
                    "hours": hours,
                    "description": description
                }
            )
            
            # Update SuperOps ticket
            self.superops.update_ticket(ticket_id, {
                "time_logged": hours,
                "time_description": description
            })
            
            log_event("technician_time_logged", {
                "ticket_id": ticket_id,
                "hours": hours
            })
            
            return {
                "status": "logged",
                "ticket_id": ticket_id,
                "hours": hours
            }
        
        except Exception as e:
            logger.error(f"Error logging technician time: {str(e)}")
            raise
    
    def generate_post_patch_report(self, execution_arn: str, ticket_id: str,
                                  execution_result: Dict) -> Dict:
        """
        Generate post-patch report with KPIs
        """
        try:
            # Calculate KPIs
            start_time = execution_result.get('started_at')
            end_time = execution_result.get('ended_at', datetime.utcnow().isoformat())
            
            start_dt = datetime.fromisoformat(start_time)
            end_dt = datetime.fromisoformat(end_time)
            duration_hours = (end_dt - start_dt).total_seconds() / 3600
            
            total_devices = execution_result.get('total_devices', 0)
            successful_devices = execution_result.get('successful_devices', 0)
            failed_devices = execution_result.get('failed_devices', 0)
            
            success_rate = (successful_devices / total_devices * 100) if total_devices > 0 else 0
            
            # Calculate exposure hours (time devices were vulnerable)
            exposure_hours = duration_hours * total_devices
            
            report = {
                "execution_arn": execution_arn,
                "ticket_id": ticket_id,
                "generated_at": datetime.utcnow().isoformat(),
                "kpis": {
                    "total_devices": total_devices,
                    "successful_devices": successful_devices,
                    "failed_devices": failed_devices,
                    "success_rate_percent": success_rate,
                    "duration_hours": duration_hours,
                    "exposure_hours_reduced": exposure_hours,
                    "rollbacks": execution_result.get('rollbacks', 0)
                },
                "summary": f"""
**POST-PATCH REPORT**

Execution: {execution_arn}
Duration: {duration_hours:.1f} hours
Devices Patched: {successful_devices}/{total_devices}
Success Rate: {success_rate:.1f}%
Exposure Hours Reduced: {exposure_hours:.1f}
Rollbacks: {execution_result.get('rollbacks', 0)}

Status: {'SUCCESS' if success_rate >= 95 else 'PARTIAL SUCCESS' if success_rate >= 80 else 'FAILED'}
"""
            }
            
            # Store report in DynamoDB
            self.table.put_item(
                Item={
                    "pk": f"REPORT#{execution_arn}",
                    "sk": "SUMMARY",
                    "ticket_id": ticket_id,
                    "kpis": report["kpis"],
                    "generated_at": datetime.utcnow().isoformat()
                }
            )
            
            # Update ticket with report
            self.superops.update_ticket(ticket_id, {
                "status": "completed",
                "post_patch_report": report["summary"],
                "success_rate": success_rate
            })
            
            log_event("post_patch_report_generated", {
                "execution_arn": execution_arn,
                "ticket_id": ticket_id,
                "success_rate": success_rate
            })
            
            return report
        
        except Exception as e:
            logger.error(f"Error generating post-patch report: {str(e)}")
            raise
    
    def get_kpi_summary(self, client_id: str, days: int = 30) -> Dict:
        """
        Get KPI summary for a client over time period
        """
        try:
            # Query DynamoDB for reports
            cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
            
            # This is a simplified version - in production, use proper DynamoDB queries
            kpi_summary = {
                "client_id": client_id,
                "period_days": days,
                "generated_at": datetime.utcnow().isoformat(),
                "metrics": {
                    "total_patches": 0,
                    "successful_patches": 0,
                    "failed_patches": 0,
                    "average_success_rate": 0,
                    "total_exposure_hours_reduced": 0,
                    "average_duration_hours": 0,
                    "total_rollbacks": 0
                }
            }
            
            log_event("kpi_summary_generated", {
                "client_id": client_id,
                "days": days
            })
            
            return kpi_summary
        
        except Exception as e:
            logger.error(f"Error generating KPI summary: {str(e)}")
            raise

