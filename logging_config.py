import json
import logging
from datetime import datetime
from flask import has_request_context, g


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "service": "api-backend",
            "message": record.getMessage(),
        }

        if has_request_context() and hasattr(g, "request_id"):
            log_record["request_id"] = g.request_id

        return json.dumps(log_record)


def setup_logging():
    logger = logging.getLogger("api-backend")
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())

    logger.handlers.clear()
    logger.addHandler(handler)

    return logger