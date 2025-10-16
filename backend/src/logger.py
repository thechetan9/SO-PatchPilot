import logging
import json
from datetime import datetime
from config import LOG_LEVEL

# Configure logging
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("PatchPilot")

def log_event(event_type: str, data: dict):
    """Log structured events for debugging and audit trail"""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "data": data
    }
    logger.info(json.dumps(log_entry))

