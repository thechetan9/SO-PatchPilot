"""
Tests for PatchPilot Agent
"""
import pytest
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.agent import PatchPilotAgent
from src.superops_client import MockSuperOpsClient

@pytest.fixture
def agent():
    """Create agent instance for testing"""
    return PatchPilotAgent()

@pytest.fixture
def sample_webhook():
    """Sample webhook data"""
    return {
        "ticket_id": "TICKET-001",
        "client_id": "client-a",
        "device_ids": ["dev-001", "dev-002"],
        "cve_findings": [
            {
                "cve_id": "CVE-2025-1234",
                "severity": "CRITICAL",
                "cvss_score": 9.8
            }
        ]
    }

def test_agent_initialization(agent):
    """Test agent initializes correctly"""
    assert agent is not None
    assert agent.bedrock is not None
    assert agent.superops is not None

def test_fetch_context(agent):
    """Test context fetching from SuperOps"""
    context = agent._fetch_context("client-a", ["dev-001", "dev-002"])
    
    assert context is not None
    assert context["client_id"] == "client-a"
    assert len(context["devices"]) > 0
    assert "sla_policy" in context
    assert "maintenance_windows" in context
    assert "cve_findings" in context

def test_generate_default_plan(agent):
    """Test default plan generation"""
    context = {
        "devices": [{"id": f"dev-{i}"} for i in range(10)],
        "sla_policy": {"patch_window": "Saturday 1-3 AM"},
        "maintenance_windows": [],
        "cve_findings": {}
    }
    
    plan = agent._generate_default_plan(context)
    
    assert plan is not None
    assert "plan_id" in plan
    assert "canary_size" in plan
    assert "batches" in plan
    assert plan["status"] == "proposed"

def test_parse_plan_response(agent):
    """Test parsing Claude's plan response"""
    response_text = """{
        "canary_size": 5,
        "batches": [30, 30],
        "health_check_interval_minutes": 10,
        "rollback_threshold_percent": 5,
        "estimated_duration_hours": 6,
        "notes": "Test plan"
    }"""
    
    context = {"devices": []}
    plan = agent._parse_plan_response(response_text, context)
    
    assert plan["canary_size"] == 5
    assert plan["batches"] == [30, 30]
    assert plan["status"] == "proposed"

def test_process_webhook(agent, sample_webhook):
    """Test webhook processing"""
    result = agent.process_webhook(sample_webhook)
    
    assert result["status"] == "success"
    assert "plan_id" in result
    assert result["ticket_id"] == "TICKET-001"
    assert "plan" in result

def test_superops_client():
    """Test mock SuperOps client"""
    client = MockSuperOpsClient()
    
    # Test get_devices
    devices = client.get_devices("client-a")
    assert len(devices) > 0
    
    # Test get_device_by_id
    device = client.get_device_by_id("dev-001")
    assert device is not None
    assert device["name"] == "WIN-SERVER-01"
    
    # Test get_sla_policy
    sla = client.get_sla_policy("critical")
    assert "patch_window" in sla
    
    # Test create_ticket
    ticket = client.create_ticket("Test", "Description", "client-a")
    assert ticket["id"] is not None
    assert ticket["status"] == "open"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

