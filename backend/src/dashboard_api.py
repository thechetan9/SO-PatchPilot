"""
PatchPilot Dashboard API
Provides endpoints for dashboard UI to display plans, runs, and KPIs
"""
from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from decimal import Decimal
from aws_clients import get_dynamodb_resource
from logger import log_event, logger
from config import DYNAMODB_TABLE, DYNAMODB_TABLE_PLANS

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

dynamodb = get_dynamodb_resource()
table = dynamodb.Table(DYNAMODB_TABLE)
plans_table = dynamodb.Table(DYNAMODB_TABLE_PLANS)


# Helper function to convert Decimal to float for JSON serialization
def decimal_to_float(obj):
    """Convert Decimal objects to float for JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_float(item) for item in obj]
    return obj

@dashboard_bp.route('/plans', methods=['GET'])
def get_open_plans():
    """
    Get all open patch plans from DynamoDB
    Returns: List of plans awaiting approval
    """
    try:
        client_id = request.args.get('client_id')

        # Scan DynamoDB for all plans
        response = plans_table.scan()
        all_plans = response.get('Items', [])

        # Filter for pending approval plans
        open_plans = [
            decimal_to_float(plan) for plan in all_plans
            if plan.get("status") == "proposed"
        ]

        plans = {
            "open_plans": open_plans,
            "total": len(open_plans)
        }

        log_event("open_plans_retrieved", {
            "client_id": client_id,
            "count": len(plans["open_plans"])
        })

        return jsonify(plans), 200

    except Exception as e:
        logger.error(f"Error retrieving open plans: {str(e)}")
        return jsonify({"error": str(e)}), 500


@dashboard_bp.route('/plans/history', methods=['GET'])
def get_plans_history():
    """
    Get all plans from DynamoDB (proposed, approved, rejected)
    Returns: Complete plan history
    """
    try:
        client_id = request.args.get('client_id')

        # Scan DynamoDB for all plans
        response = plans_table.scan()
        all_plans = [decimal_to_float(plan) for plan in response.get('Items', [])]

        history = {
            "all_plans": all_plans,
            "total": len(all_plans),
            "pending": len([p for p in all_plans if p.get("status") == "proposed"]),
            "approved": len([p for p in all_plans if p.get("status") == "approved"]),
            "rejected": len([p for p in all_plans if p.get("status") == "rejected"])
        }

        log_event("plans_history_retrieved", {
            "client_id": client_id,
            "total": len(all_plans)
        })

        return jsonify(history), 200

    except Exception as e:
        logger.error(f"Error retrieving plans history: {str(e)}")
        return jsonify({"error": str(e)}), 500


@dashboard_bp.route('/plans/generate', methods=['POST'])
def generate_new_plan():
    """
    Generate a new patch plan (simulates webhook from SuperOps)
    """
    try:
        global _plan_counter
        data = request.get_json() or {}

        _plan_counter += 1
        plan_id = f"PLAN-{_plan_counter:03d}"

        # Allow customization via request body
        new_plan = {
            "plan_id": plan_id,
            "client_id": data.get("client_id", "client-a"),
            "created_at": datetime.utcnow().isoformat(),
            "status": "pending_approval",
            "canary_size": data.get("canary_size", 5),
            "batches": data.get("batches", [30, 30]),
            "estimated_duration_hours": data.get("estimated_duration_hours", 6),
            "device_count": data.get("device_count", 65),
            "devices_affected": data.get("devices_affected", ["device-001", "device-002", "device-003"]),
            "strategy": data.get("strategy", "canary_then_batch"),
            "patches": data.get("patches", 0),
            "health_check_interval_minutes": data.get("health_check_interval_minutes", 10),
            "rollback_threshold_percent": data.get("rollback_threshold_percent", 5)
        }

        _all_plans[plan_id] = new_plan

        log_event("plan_generated", {
            "plan_id": plan_id,
            "client_id": new_plan["client_id"]
        })

        return jsonify({
            "status": "created",
            "plan": new_plan
        }), 201

    except Exception as e:
        logger.error(f"Error generating plan: {str(e)}")
        return jsonify({"error": str(e)}), 500


@dashboard_bp.route('/plans/update', methods=['POST'])
def update_plan():
    """
    Update an existing patch plan in DynamoDB
    """
    try:
        data = request.get_json()
        plan_id = data.get('plan_id')

        # Get existing plan from DynamoDB
        response = plans_table.get_item(Key={'plan_id': plan_id})

        if 'Item' not in response:
            return jsonify({"error": "Plan not found"}), 404

        existing_plan = response['Item']

        # Update plan fields
        update_expression = "SET "
        expression_values = {}
        expression_names = {}

        if 'status' in data:
            update_expression += "#status = :status, "
            expression_values[':status'] = data['status']
            expression_names['#status'] = 'status'

        if 'canary_size' in data:
            update_expression += "canary_size = :canary_size, "
            expression_values[':canary_size'] = data['canary_size']

        if 'batches' in data:
            update_expression += "batches = :batches, "
            expression_values[':batches'] = data['batches']

        # Remove trailing comma and space
        update_expression = update_expression.rstrip(', ')

        # Update in DynamoDB
        plans_table.update_item(
            Key={'plan_id': plan_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values,
            ExpressionAttributeNames=expression_names if expression_names else None
        )

        log_event("plan_updated", {
            "plan_id": plan_id
        })

        # Get updated plan
        response = plans_table.get_item(Key={'plan_id': plan_id})
        updated_plan = decimal_to_float(response['Item'])

        return jsonify({
            "status": "updated",
            "plan": updated_plan
        }), 200

    except Exception as e:
        logger.error(f"Error updating plan: {str(e)}")
        return jsonify({"error": str(e)}), 500


@dashboard_bp.route('/runs', methods=['GET'])
def get_patch_runs():
    """
    Get in-progress and recent patch runs
    Returns: List of patch executions
    """
    try:
        client_id = request.args.get('client_id')
        status = request.args.get('status', 'all')  # all, running, completed, failed
        
        runs = {
            "in_progress": [
                {
                    "run_id": "PATCHRUN-124",
                    "plan_id": "PLAN-001",
                    "client_id": client_id or "client-a",
                    "status": "executing",
                    "current_batch": "batch-1",
                    "started_at": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                    "estimated_completion": (datetime.utcnow() + timedelta(hours=4)).isoformat(),
                    "progress": {
                        "canary": {"status": "completed", "devices": 5, "successful": 5},
                        "batch_1": {"status": "in_progress", "devices": 30, "successful": 28},
                        "batch_2": {"status": "queued", "devices": 30, "successful": 0}
                    }
                }
            ],
            "recent": [
                {
                    "run_id": "PATCHRUN-123",
                    "plan_id": "PLAN-000",
                    "client_id": client_id or "client-a",
                    "status": "completed",
                    "started_at": (datetime.utcnow() - timedelta(days=1)).isoformat(),
                    "completed_at": (datetime.utcnow() - timedelta(hours=20)).isoformat(),
                    "duration_hours": 4.5,
                    "success_rate": 97.0,
                    "devices_patched": 60
                }
            ]
        }
        
        log_event("patch_runs_retrieved", {
            "client_id": client_id,
            "status": status
        })
        
        return jsonify(runs), 200
    
    except Exception as e:
        logger.error(f"Error retrieving patch runs: {str(e)}")
        return jsonify({"error": str(e)}), 500


@dashboard_bp.route('/runs/<run_id>', methods=['GET'])
def get_run_details(run_id):
    """
    Get detailed information about a specific patch run
    """
    try:
        run_details = {
            "run_id": run_id,
            "plan_id": "PLAN-001",
            "status": "executing",
            "started_at": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
            "batches": [
                {
                    "batch_id": "canary",
                    "status": "completed",
                    "devices": 5,
                    "successful": 5,
                    "failed": 0,
                    "health_percent": 100.0,
                    "duration_minutes": 15,
                    "completed_at": (datetime.utcnow() - timedelta(hours=2)).isoformat()
                },
                {
                    "batch_id": "batch-1",
                    "status": "in_progress",
                    "devices": 30,
                    "successful": 28,
                    "failed": 0,
                    "health_percent": 93.3,
                    "duration_minutes": 45,
                    "started_at": (datetime.utcnow() - timedelta(minutes=45)).isoformat()
                },
                {
                    "batch_id": "batch-2",
                    "status": "queued",
                    "devices": 30,
                    "successful": 0,
                    "failed": 0,
                    "health_percent": 0,
                    "duration_minutes": 0
                }
            ],
            "kpis": {
                "total_devices": 65,
                "successful_devices": 33,
                "failed_devices": 0,
                "success_rate": 100.0,
                "exposure_hours_reduced": 132.0,
                "rollbacks": 0
            }
        }
        
        log_event("run_details_retrieved", {"run_id": run_id})
        
        return jsonify(run_details), 200
    
    except Exception as e:
        logger.error(f"Error retrieving run details: {str(e)}")
        return jsonify({"error": str(e)}), 500


@dashboard_bp.route('/kpis', methods=['GET'])
def get_kpis():
    """
    Get KPI summary for dashboard
    """
    try:
        client_id = request.args.get('client_id')
        days = int(request.args.get('days', 30))
        
        kpis = {
            "period_days": days,
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_patches": 12,
                "successful_patches": 11,
                "failed_patches": 1,
                "average_success_rate": 97.0,
                "total_exposure_hours_reduced": 1440.0,
                "average_duration_hours": 5.5,
                "total_rollbacks": 1,
                "manual_touches_reduced_percent": 68
            },
            "trends": {
                "success_rate_trend": [95, 96, 97, 97, 98, 97],
                "duration_trend": [6.2, 6.0, 5.8, 5.5, 5.3, 5.5],
                "exposure_hours_trend": [390, 360, 330, 300, 270, 240]
            }
        }
        
        log_event("kpis_retrieved", {
            "client_id": client_id,
            "days": days
        })
        
        return jsonify(kpis), 200
    
    except Exception as e:
        logger.error(f"Error retrieving KPIs: {str(e)}")
        return jsonify({"error": str(e)}), 500


@dashboard_bp.route('/approve-plan', methods=['POST'])
def approve_plan():
    """
    Approve a patch plan from dashboard
    """
    try:
        data = request.get_json()
        plan_id = data.get('plan_id')
        ticket_id = data.get('ticket_id')

        # Update plan status
        if plan_id in _all_plans:
            _all_plans[plan_id]["status"] = "approved"
            _all_plans[plan_id]["approved_at"] = datetime.utcnow().isoformat()
            _all_plans[plan_id]["approved_by"] = data.get("approved_by", "user@company.com")

        log_event("plan_approved_from_dashboard", {
            "plan_id": plan_id,
            "ticket_id": ticket_id
        })

        return jsonify({
            "status": "approved",
            "plan_id": plan_id,
            "message": "Plan approved, execution started"
        }), 200

    except Exception as e:
        logger.error(f"Error approving plan: {str(e)}")
        return jsonify({"error": str(e)}), 500


@dashboard_bp.route('/reject-plan', methods=['POST'])
def reject_plan():
    """
    Reject a patch plan from dashboard
    """
    try:
        data = request.get_json()
        plan_id = data.get('plan_id')
        ticket_id = data.get('ticket_id')
        reason = data.get('reason', 'No reason provided')

        # Update plan status
        if plan_id in _all_plans:
            _all_plans[plan_id]["status"] = "rejected"
            _all_plans[plan_id]["rejected_at"] = datetime.utcnow().isoformat()
            _all_plans[plan_id]["rejected_by"] = data.get("rejected_by", "user@company.com")
            _all_plans[plan_id]["rejection_reason"] = reason

        log_event("plan_rejected_from_dashboard", {
            "plan_id": plan_id,
            "ticket_id": ticket_id,
            "reason": reason
        })

        return jsonify({
            "status": "rejected",
            "plan_id": plan_id,
            "message": "Plan rejected"
        }), 200

    except Exception as e:
        logger.error(f"Error rejecting plan: {str(e)}")
        return jsonify({"error": str(e)}), 500

