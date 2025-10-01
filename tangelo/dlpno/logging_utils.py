# Copyright SandboxAQ 2021-2024.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Logging utilities for DLPNO-CCSD(T) calculations."""

import logging
import json
from datetime import datetime


class JsonFormatter(logging.Formatter):
    """Simple JSON formatter for log records."""
    
    def format(self, record):
        """Format log record as JSON.
        
        Args:
            record: logging.LogRecord instance
            
        Returns:
            str: JSON-formatted log message
        """
        log_data = {
            'time': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'name': record.name,
            'msg': record.getMessage()
        }
        return json.dumps(log_data)


def init_dlpno_logger(name: str = "dlpno", level: int = logging.INFO, json: bool = False) -> logging.Logger:
    """Initialize a logger for DLPNO calculations.
    
    Args:
        name: Logger name (default: "dlpno")
        level: Logging level (default: logging.INFO)
        json: Use JSON formatting if True (default: False)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create console handler
    handler = logging.StreamHandler()
    handler.setLevel(level)
    
    # Set formatter
    if json:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger
