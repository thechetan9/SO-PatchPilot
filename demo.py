"""
PatchPilot Demo Script
Demonstrates the agent in action
"""
import json
from src.agent import PatchPilotAgent
from src.logger import logger

def demo_webhook_processing():
    """Demo: Process a webhook from SuperOps"""
    print("\n" + "="*60)
    print("DEMO: PatchPilot Webhook Processing")
    print("="*60)
    
    agent = PatchPilotAgent()
    
    # Simulate webhook from SuperOps
    webhook_data = {
        "ticket_id": "TICKET-001",
        "client_id": "client-a",
        "device_ids": ["dev-001", "dev-002"],
        "cve_findings": [
            {
                "cve_id": "CVE-2025-1234",
                "severity": "CRITICAL",
                "cvss_score": 9.8,
                "description": "Remote code execution vulnerability"
            }
        ]
    }
    
    print("\n1. Incoming Webhook from SuperOps:")
    print(json.dumps(webhook_data, indent=2))
    
    # Process webhook
    print("\n2. Processing webhook...")
    result = agent.process_webhook(webhook_data)
    
    print("\n3. Generated Plan:")
    plan = result.get("plan", {})
    print(f"   Plan ID: {plan.get('plan_id')}")
    print(f"   Canary Size: {plan.get('canary_size')} devices")
    print(f"   Batches: {plan.get('batches')}")
    print(f"   Health Check Interval: {plan.get('health_check_interval_minutes')} minutes")
    print(f"   Rollback Threshold: {plan.get('rollback_threshold_percent')}%")
    print(f"   Estimated Duration: {plan.get('estimated_duration_hours')} hours")
    print(f"   Notes: {plan.get('notes')}")
    print(f"   Status: {plan.get('status')}")
    
    print("\n4. Plan posted to ticket for approval")
    print(f"   Ticket ID: {result.get('ticket_id')}")
    
    return result

def demo_device_inventory():
    """Demo: Show device inventory from SuperOps"""
    print("\n" + "="*60)
    print("DEMO: Device Inventory")
    print("="*60)
    
    agent = PatchPilotAgent()
    
    print("\nDevices in client-a:")
    devices = agent.superops.get_devices("client-a")
    
    for device in devices:
        print(f"\n  {device['name']} ({device['os']})")
        print(f"    - ID: {device['id']}")
        print(f"    - SLA Tier: {device['sla_tier']}")
        print(f"    - Pending Patches: {device['pending_patches']}")
        print(f"    - Critical CVEs: {device['critical_cves']}")
        print(f"    - Last Patch: {device['last_patch_date']}")

def demo_cve_findings():
    """Demo: Show CVE findings for a device"""
    print("\n" + "="*60)
    print("DEMO: CVE Findings")
    print("="*60)
    
    agent = PatchPilotAgent()
    
    device_id = "dev-001"
    print(f"\nCVE findings for {device_id}:")
    
    cves = agent.superops.get_cve_findings(device_id)
    
    if cves:
        for cve in cves:
            print(f"\n  {cve['cve_id']}")
            print(f"    - Severity: {cve['severity']}")
            print(f"    - CVSS Score: {cve['cvss_score']}")
            print(f"    - Description: {cve['description']}")
    else:
        print("  No critical CVEs found")

def demo_sla_policies():
    """Demo: Show SLA policies"""
    print("\n" + "="*60)
    print("DEMO: SLA Policies")
    print("="*60)
    
    agent = PatchPilotAgent()
    
    for tier in ["critical", "standard"]:
        sla = agent.superops.get_sla_policy(tier)
        print(f"\n{tier.upper()} SLA:")
        print(f"  - Patch Window: {sla['patch_window']}")
        print(f"  - Max Exposure Hours: {sla['max_exposure_hours']}")
        print(f"  - Rollback Threshold: {sla['rollback_threshold']}")

def main():
    """Run all demos"""
    print("\n" + "="*60)
    print("PatchPilot - Agentic Patch Orchestrator")
    print("Demo Script")
    print("="*60)
    
    try:
        # Run demos
        demo_device_inventory()
        demo_sla_policies()
        demo_cve_findings()
        result = demo_webhook_processing()
        
        print("\n" + "="*60)
        print("Demo Complete!")
        print("="*60)
        print("\nNext Steps:")
        print("1. Review the generated plan")
        print("2. Approve the plan in SuperOps")
        print("3. Step Functions will orchestrate the patch execution")
        print("4. Health checks will run between batches")
        print("5. Automatic rollback if issues detected")
        
    except Exception as e:
        logger.error(f"Demo error: {str(e)}")
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

