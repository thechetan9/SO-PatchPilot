"""
Tests for PatchPilot Ticket Manager
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.ticket_manager import TicketManager


@pytest.fixture
def ticket_manager():
    """Create ticket manager instance for testing"""
    with patch('src.ticket_manager.get_superops_client'), \
         patch('src.ticket_manager.get_dynamodb_client'):
        return TicketManager()


def test_ticket_manager_initialization(ticket_manager):
    """Test ticket manager initializes correctly"""
    assert ticket_manager.superops is not None
    assert ticket_manager.dynamodb is not None


def test_post_plan_proposal(ticket_manager):
    """Test posting plan proposal to ticket"""
    ticket_manager.superops.update_ticket = Mock()
    
    plan = {
        "canary_size": 5,
        "batches": [30, 30],
        "health_check_interval_minutes": 10,
        "rollback_threshold_percent": 5,
        "estimated_duration_hours": 6,
        "notes": "Test plan"
    }
    
    result = ticket_manager.post_plan_proposal(
        ticket_id="TICKET-001",
        plan=plan,
        plan_id="PLAN-001"
    )
    
    assert result["status"] == "posted"
    assert result["ticket_id"] == "TICKET-001"
    assert ticket_manager.superops.update_ticket.called


def test_update_execution_status(ticket_manager):
    """Test updating execution status on ticket"""
    ticket_manager.superops.update_ticket = Mock()
    
    batch_info = {
        "batch_id": "canary",
        "device_count": 5,
        "successful": 5,
        "failed": 0,
        "health_percent": 100.0
    }
    
    result = ticket_manager.update_execution_status(
        ticket_id="TICKET-001",
        execution_arn="arn:aws:states:us-east-2:123456789:execution:patch-run-001",
        status="canary_complete",
        batch_info=batch_info
    )
    
    assert result["status"] == "updated"
    assert ticket_manager.superops.update_ticket.called


def test_log_technician_time(ticket_manager):
    """Test logging technician time"""
    ticket_manager.superops.update_ticket = Mock()
    ticket_manager.table = Mock()
    
    result = ticket_manager.log_technician_time(
        ticket_id="TICKET-001",
        hours=2.5,
        description="Patch execution"
    )
    
    assert result["status"] == "logged"
    assert result["hours"] == 2.5
    assert ticket_manager.superops.update_ticket.called


def test_generate_post_patch_report(ticket_manager):
    """Test generating post-patch report"""
    ticket_manager.superops.update_ticket = Mock()
    ticket_manager.table = Mock()
    
    execution_result = {
        "started_at": "2024-01-01T00:00:00",
        "ended_at": "2024-01-01T06:00:00",
        "total_devices": 65,
        "successful_devices": 63,
        "failed_devices": 2,
        "rollbacks": 0
    }
    
    result = ticket_manager.generate_post_patch_report(
        execution_arn="arn:aws:states:us-east-2:123456789:execution:patch-run-001",
        ticket_id="TICKET-001",
        execution_result=execution_result
    )
    
    assert "kpis" in result
    assert result["kpis"]["success_rate_percent"] > 0
    assert result["kpis"]["exposure_hours_reduced"] > 0
    assert ticket_manager.superops.update_ticket.called


def test_get_kpi_summary(ticket_manager):
    """Test getting KPI summary"""
    result = ticket_manager.get_kpi_summary(
        client_id="client-a",
        days=30
    )
    
    assert result["client_id"] == "client-a"
    assert result["period_days"] == 30
    assert "metrics" in result

