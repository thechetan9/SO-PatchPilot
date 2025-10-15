"""
Tests for PatchPilot Orchestrator
"""
import pytest
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.orchestrator import PatchOrchestrator


@pytest.fixture
def orchestrator():
    """Create orchestrator instance for testing"""
    with patch('src.orchestrator.get_stepfunctions_client'), \
         patch('src.orchestrator.get_ssm_client'), \
         patch('src.orchestrator.get_dynamodb_client'):
        return PatchOrchestrator()


def test_orchestrator_initialization(orchestrator):
    """Test orchestrator initializes correctly"""
    assert orchestrator.stepfunctions is not None
    assert orchestrator.ssm is not None
    assert orchestrator.dynamodb is not None


def test_start_execution(orchestrator):
    """Test starting Step Functions execution"""
    # Mock Step Functions response
    orchestrator.stepfunctions.start_execution = Mock(return_value={
        'executionArn': 'arn:aws:states:us-east-2:123456789:execution:patch-run-001'
    })
    
    orchestrator.table = Mock()
    
    plan = {
        "canary_size": 5,
        "batches": [30, 30],
        "health_check_interval_minutes": 10,
        "rollback_threshold_percent": 5,
        "estimated_duration_hours": 6
    }
    
    result = orchestrator.start_execution(
        plan_id="PLAN-001",
        plan=plan,
        ticket_id="TICKET-001",
        client_id="client-a"
    )
    
    assert result["status"] == "started"
    assert "execution_arn" in result
    assert orchestrator.stepfunctions.start_execution.called


def test_execute_canary_batch(orchestrator):
    """Test executing canary batch"""
    orchestrator.ssm.send_command = Mock(return_value={
        'Command': {'CommandId': 'cmd-001'}
    })
    
    orchestrator.table = Mock()
    
    result = orchestrator.execute_canary_batch(
        batch_id="canary",
        device_ids=["dev-001", "dev-002"],
        patch_ids=["patch-001"]
    )
    
    assert result["batch_id"] == "canary"
    assert result["device_count"] == 2
    assert result["successful"] == 2
    assert result["failed"] == 0


def test_check_batch_health(orchestrator):
    """Test health check for batch"""
    orchestrator.ssm.describe_instance_information = Mock(return_value={
        'InstanceInformationList': [
            {
                'InstanceIds': 'dev-001',
                'PingStatus': 'Online',
                'AgentVersion': '2.4.0'
            }
        ]
    })
    
    orchestrator.table = Mock()
    
    result = orchestrator.check_batch_health(
        batch_id="batch-1",
        device_ids=["dev-001"],
        health_threshold_percent=95.0
    )
    
    assert result["batch_id"] == "batch-1"
    assert result["healthy"] == 1
    assert result["health_percent"] == 100.0
    assert result["proceed"] == True


def test_rollback_batch(orchestrator):
    """Test rollback of batch"""
    orchestrator.ssm.send_command = Mock(return_value={
        'Command': {'CommandId': 'cmd-rollback-001'}
    })
    
    orchestrator.table = Mock()
    
    result = orchestrator.rollback_batch(
        batch_id="batch-1",
        device_ids=["dev-001", "dev-002"]
    )
    
    assert result["batch_id"] == "batch-1"
    assert result["device_count"] == 2
    assert result["successful"] == 2


def test_get_execution_status(orchestrator):
    """Test getting execution status"""
    orchestrator.stepfunctions.describe_execution = Mock(return_value={
        'status': 'RUNNING',
        'startDate': '2024-01-01T00:00:00',
        'output': '{"status": "running"}'
    })
    
    result = orchestrator.get_execution_status(
        execution_arn="arn:aws:states:us-east-2:123456789:execution:patch-run-001"
    )
    
    assert result["status"] == "RUNNING"
    assert "execution_arn" in result

