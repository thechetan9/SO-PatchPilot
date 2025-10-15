"""
Mock SuperOps API Client
For hackathon demo - replace with real API calls later
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from src.logger import log_event

class MockSuperOpsClient:
    """Mock SuperOps client for demo purposes"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.mock_devices = self._init_mock_devices()
        self.mock_slas = self._init_mock_slas()
        self.mock_tickets = {}
        
    def _init_mock_devices(self) -> List[Dict]:
        """Initialize mock device inventory"""
        return [
            {
                "id": "dev-001",
                "name": "WIN-SERVER-01",
                "os": "Windows Server 2022",
                "client_id": "client-a",
                "sla_tier": "critical",
                "last_patch_date": "2025-09-15",
                "pending_patches": 5,
                "critical_cves": 2
            },
            {
                "id": "dev-002",
                "name": "WIN-SERVER-02",
                "os": "Windows Server 2022",
                "client_id": "client-a",
                "sla_tier": "critical",
                "last_patch_date": "2025-09-15",
                "pending_patches": 3,
                "critical_cves": 1
            },
            {
                "id": "dev-003",
                "name": "LINUX-WEB-01",
                "os": "Ubuntu 22.04",
                "client_id": "client-b",
                "sla_tier": "standard",
                "last_patch_date": "2025-09-10",
                "pending_patches": 8,
                "critical_cves": 0
            },
            {
                "id": "dev-004",
                "name": "WIN-WORKSTATION-01",
                "os": "Windows 11",
                "client_id": "client-c",
                "sla_tier": "standard",
                "last_patch_date": "2025-09-01",
                "pending_patches": 12,
                "critical_cves": 3
            },
        ]
    
    def _init_mock_slas(self) -> Dict:
        """Initialize mock SLA policies"""
        return {
            "critical": {
                "patch_window": "Saturday 1-3 AM",
                "max_exposure_hours": 24,
                "rollback_threshold": 0.05
            },
            "standard": {
                "patch_window": "Sunday 2-4 AM",
                "max_exposure_hours": 72,
                "rollback_threshold": 0.10
            }
        }
    
    def get_devices(self, client_id: Optional[str] = None) -> List[Dict]:
        """Get devices from SuperOps inventory"""
        if client_id:
            return [d for d in self.mock_devices if d["client_id"] == client_id]
        return self.mock_devices
    
    def get_device_by_id(self, device_id: str) -> Optional[Dict]:
        """Get a specific device"""
        for device in self.mock_devices:
            if device["id"] == device_id:
                return device
        return None
    
    def get_sla_policy(self, sla_tier: str) -> Dict:
        """Get SLA policy for a tier"""
        return self.mock_slas.get(sla_tier, self.mock_slas["standard"])
    
    def get_maintenance_windows(self, client_id: str) -> List[Dict]:
        """Get maintenance windows for a client"""
        return [
            {
                "client_id": client_id,
                "day": "Saturday",
                "start_time": "01:00",
                "end_time": "03:00",
                "timezone": "UTC"
            }
        ]
    
    def create_ticket(self, title: str, description: str, client_id: str) -> Dict:
        """Create a ticket in SuperOps"""
        ticket_id = f"TICKET-{len(self.mock_tickets) + 1}"
        ticket = {
            "id": ticket_id,
            "title": title,
            "description": description,
            "client_id": client_id,
            "status": "open",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        self.mock_tickets[ticket_id] = ticket
        log_event("ticket_created", {"ticket_id": ticket_id, "client_id": client_id})
        return ticket
    
    def update_ticket(self, ticket_id: str, updates: Dict) -> Dict:
        """Update a ticket"""
        if ticket_id in self.mock_tickets:
            self.mock_tickets[ticket_id].update(updates)
            self.mock_tickets[ticket_id]["updated_at"] = datetime.utcnow().isoformat()
            log_event("ticket_updated", {"ticket_id": ticket_id, "updates": updates})
            return self.mock_tickets[ticket_id]
        return None
    
    def log_time_entry(self, ticket_id: str, hours: float, description: str) -> Dict:
        """Log time entry for a ticket"""
        entry = {
            "ticket_id": ticket_id,
            "hours": hours,
            "description": description,
            "logged_at": datetime.utcnow().isoformat()
        }
        log_event("time_entry_logged", entry)
        return entry
    
    def get_cve_findings(self, device_id: str) -> List[Dict]:
        """Get CVE findings for a device (mock from Security Hub)"""
        device = self.get_device_by_id(device_id)
        if not device:
            return []
        
        # Mock CVE data
        cves = [
            {
                "cve_id": "CVE-2025-1234",
                "severity": "CRITICAL",
                "cvss_score": 9.8,
                "description": "Remote code execution vulnerability",
                "affected_device": device_id
            },
            {
                "cve_id": "CVE-2025-5678",
                "severity": "HIGH",
                "cvss_score": 8.2,
                "description": "Privilege escalation vulnerability",
                "affected_device": device_id
            }
        ]
        return cves[:device.get("critical_cves", 0)]

# Singleton instance
_superops_client = None

def get_superops_client() -> MockSuperOpsClient:
    """Get or create SuperOps client"""
    global _superops_client
    if _superops_client is None:
        _superops_client = MockSuperOpsClient()
    return _superops_client

