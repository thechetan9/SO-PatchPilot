"""
PatchPilot Agent - Core Logic
Handles plan generation, prioritization, and orchestration
"""
import json
from typing import Dict, List, Optional
from datetime import datetime
from decimal import Decimal
from aws_clients import get_bedrock_client
from superops_client import get_superops_client
from logger import log_event, logger
from config import BEDROCK_MODEL_ID

class PatchPilotAgent:
    """Main agent for patch orchestration"""
    
    def __init__(self):
        self.bedrock = get_bedrock_client()
        self.superops = get_superops_client()
        self.model_id = BEDROCK_MODEL_ID
    
    def process_webhook(self, webhook_data: Dict) -> Dict:
        """
        Process incoming webhook from SuperOps
        Webhook contains: ticket_id, client_id, device_ids, cve_findings
        """
        log_event("webhook_received", webhook_data)
        
        ticket_id = webhook_data.get("ticket_id")
        client_id = webhook_data.get("client_id")
        device_ids = webhook_data.get("device_ids", [])
        
        # Fetch context from SuperOps
        context = self._fetch_context(client_id, device_ids)
        
        # Generate plan using Bedrock
        plan = self._generate_plan(context)
        
        # Store plan in DynamoDB
        plan_id = self._store_plan(plan, ticket_id, client_id)
        
        # Update ticket with plan proposal
        self._post_plan_to_ticket(ticket_id, plan)
        
        return {
            "status": "success",
            "plan_id": plan_id,
            "ticket_id": ticket_id,
            "plan": plan
        }
    
    def _fetch_context(self, client_id: str, device_ids: List[str]) -> Dict:
        """Fetch context from SuperOps and Security Hub"""
        devices = self.superops.get_devices(client_id)
        sla_policy = self.superops.get_sla_policy("critical")
        maintenance_windows = self.superops.get_maintenance_windows(client_id)
        
        # Get CVE findings for each device
        cve_findings = {}
        for device_id in device_ids:
            cve_findings[device_id] = self.superops.get_cve_findings(device_id)
        
        context = {
            "client_id": client_id,
            "devices": devices,
            "sla_policy": sla_policy,
            "maintenance_windows": maintenance_windows,
            "cve_findings": cve_findings,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        log_event("context_fetched", {
            "client_id": client_id,
            "device_count": len(devices),
            "cve_count": sum(len(v) for v in cve_findings.values())
        })
        
        return context
    
    def _generate_plan(self, context: Dict) -> Dict:
        """Generate patch plan using Bedrock Claude"""
        
        # Prepare prompt for Claude
        prompt = self._build_planning_prompt(context)
        
        try:
            # Call Bedrock model (supports both Claude and Titan)
            if "claude" in self.model_id.lower():
                # Claude API format
                response = self.bedrock.invoke_model(
                    modelId=self.model_id,
                    contentType="application/json",
                    accept="application/json",
                    body=json.dumps({
                        "anthropic_version": "bedrock-2023-05-31",
                        "max_tokens": 2048,
                        "messages": [
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ]
                    })
                )
                response_body = json.loads(response['body'].read())
                plan_text = response_body['content'][0]['text']
            else:
                # Titan API format
                response = self.bedrock.invoke_model(
                    modelId=self.model_id,
                    contentType="application/json",
                    accept="application/json",
                    body=json.dumps({
                        "inputText": prompt,
                        "textGenerationConfig": {
                            "maxTokenCount": 2048,
                            "temperature": 0.7,
                            "topP": 0.9
                        }
                    })
                )
                response_body = json.loads(response['body'].read())
                plan_text = response_body['results'][0]['outputText']
            
            # Parse plan from Claude's response
            plan = self._parse_plan_response(plan_text, context)
            
            log_event("plan_generated", {
                "plan_id": plan.get("plan_id"),
                "batch_count": len(plan.get("batches", [])),
                "canary_size": plan.get("canary_size")
            })
            
            return plan
            
        except Exception as e:
            logger.error(f"Error generating plan: {str(e)}")
            # Fallback to default plan
            return self._generate_default_plan(context)
    
    def _build_planning_prompt(self, context: Dict) -> str:
        """Build prompt for Claude to generate patch plan"""
        
        devices_info = "\n".join([
            f"- {d['name']} ({d['os']}): {d['pending_patches']} patches, {d['critical_cves']} critical CVEs"
            for d in context['devices']
        ])
        
        prompt = f"""You are a patch management expert. Generate a safe, efficient patch plan based on this context:

DEVICES:
{devices_info}

SLA POLICY:
- Maintenance Window: {context['sla_policy']['patch_window']}
- Max Exposure Hours: {context['sla_policy']['max_exposure_hours']}
- Rollback Threshold: {context['sla_policy']['rollback_threshold']}

REQUIREMENTS:
1. Use canary-first approach (small batch first)
2. Divide remaining devices into 2-3 batches
3. Include health checks between batches
4. Define rollback strategy
5. Estimate total duration

Respond with a JSON object containing:
{{
    "canary_size": <number>,
    "batches": [<batch_size>, <batch_size>, ...],
    "health_check_interval_minutes": <number>,
    "rollback_threshold_percent": <number>,
    "estimated_duration_hours": <number>,
    "notes": "<safety notes>"
}}"""
        
        return prompt
    
    def _parse_plan_response(self, response_text: str, context: Dict) -> Dict:
        """Parse Claude's response into a structured plan"""
        try:
            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            json_str = response_text[json_start:json_end]
            plan_data = json.loads(json_str)
        except:
            logger.warning("Failed to parse plan response, using default")
            return self._generate_default_plan(context)
        
        plan = {
            "plan_id": f"PLAN-{datetime.utcnow().timestamp()}",
            "created_at": datetime.utcnow().isoformat(),
            "canary_size": plan_data.get("canary_size", 5),
            "batches": plan_data.get("batches", [30, 30]),
            "health_check_interval_minutes": plan_data.get("health_check_interval_minutes", 10),
            "rollback_threshold_percent": plan_data.get("rollback_threshold_percent", 5),
            "estimated_duration_hours": plan_data.get("estimated_duration_hours", 6),
            "notes": plan_data.get("notes", "Standard patch plan"),
            "status": "proposed"
        }
        
        return plan
    
    def _generate_default_plan(self, context: Dict) -> Dict:
        """Generate a default plan if Bedrock fails"""
        device_count = len(context['devices'])
        
        return {
            "plan_id": f"PLAN-{datetime.utcnow().timestamp()}",
            "created_at": datetime.utcnow().isoformat(),
            "canary_size": max(1, device_count // 10),
            "batches": [device_count // 3, device_count // 3, device_count - (device_count // 3) * 2],
            "health_check_interval_minutes": 10,
            "rollback_threshold_percent": 5,
            "estimated_duration_hours": 6,
            "notes": "Default plan - canary first, then phased rollout",
            "status": "proposed"
        }
    
    def _store_plan(self, plan: Dict, ticket_id: str, client_id: str) -> str:
        """Store plan in DynamoDB"""
        try:
            from aws_clients import get_dynamodb_resource
            from config import DYNAMODB_TABLE_PLANS

            dynamodb = get_dynamodb_resource()
            table = dynamodb.Table(DYNAMODB_TABLE_PLANS)

            # Prepare item for DynamoDB (convert floats to Decimal)
            item = {
                'plan_id': plan['plan_id'],
                'ticket_id': ticket_id,
                'client_id': client_id,
                'created_at': plan['created_at'],
                'canary_size': plan['canary_size'],
                'batches': plan['batches'],
                'health_check_interval_minutes': plan['health_check_interval_minutes'],
                'rollback_threshold_percent': Decimal(str(plan['rollback_threshold_percent'])),
                'estimated_duration_hours': Decimal(str(plan['estimated_duration_hours'])),
                'notes': plan['notes'],
                'status': plan['status']
            }

            # Store in DynamoDB
            table.put_item(Item=item)

            log_event("plan_stored", {
                "plan_id": plan["plan_id"],
                "ticket_id": ticket_id,
                "client_id": client_id,
                "storage": "dynamodb"
            })

            logger.info(f"✅ Plan {plan['plan_id']} stored in DynamoDB")

        except Exception as e:
            logger.error(f"❌ Error storing plan in DynamoDB: {e}")
            log_event("plan_storage_failed", {
                "plan_id": plan["plan_id"],
                "error": str(e)
            })

        return plan["plan_id"]
    
    def _post_plan_to_ticket(self, ticket_id: str, plan: Dict):
        """Post plan proposal to SuperOps ticket"""
        plan_summary = f"""
PROPOSED PATCH PLAN:
- Canary: {plan['canary_size']} devices
- Batches: {plan['batches']}
- Health Check Interval: {plan['health_check_interval_minutes']} min
- Rollback Threshold: {plan['rollback_threshold_percent']}%
- Estimated Duration: {plan['estimated_duration_hours']} hours
- Notes: {plan['notes']}

Status: Awaiting approval
"""
        self.superops.update_ticket(ticket_id, {
            "status": "pending_approval",
            "plan_proposal": plan_summary
        })
        
        log_event("plan_posted_to_ticket", {
            "ticket_id": ticket_id,
            "plan_id": plan["plan_id"]
        })

