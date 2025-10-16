"""
Flask API for PatchPilot
Local testing and development
"""
import sys
import os
# Add src directory to path so imports work the same as in Lambda
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from flask import Flask, request, jsonify
from flask_cors import CORS
from agent import PatchPilotAgent
from dashboard_api import dashboard_bp
from logger import log_event, logger
import json

app = Flask(__name__)
CORS(app)
agent = PatchPilotAgent()

# Register dashboard blueprint
app.register_blueprint(dashboard_bp)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "PatchPilot"}), 200

@app.route('/webhook/superops', methods=['POST'])
def webhook_superops():
    """Receive webhook from SuperOps"""
    try:
        data = request.get_json()
        logger.info(f"Webhook received: {json.dumps(data)}")
        
        result = agent.process_webhook(data)
        
        return jsonify(result), 200
    
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/plan/approve', methods=['POST'])
def approve_plan():
    """Approve a patch plan"""
    try:
        data = request.get_json()
        plan_id = data.get('plan_id')
        ticket_id = data.get('ticket_id')
        
        log_event("plan_approved", {
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

@app.route('/health-check', methods=['POST'])
def health_check():
    """Perform health check during patch execution"""
    try:
        data = request.get_json()
        batch_id = data.get('batch_id')
        device_ids = data.get('device_ids', [])
        
        log_event("health_check_performed", {
            "batch_id": batch_id,
            "device_count": len(device_ids)
        })
        
        return jsonify({
            "status": "healthy",
            "batch_id": batch_id,
            "devices_checked": len(device_ids)
        }), 200
    
    except Exception as e:
        logger.error(f"Error performing health check: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/devices', methods=['GET'])
def get_devices():
    """Get devices from SuperOps"""
    try:
        client_id = request.args.get('client_id')
        devices = agent.superops.get_devices(client_id)
        return jsonify({"devices": devices}), 200
    
    except Exception as e:
        logger.error(f"Error fetching devices: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)

