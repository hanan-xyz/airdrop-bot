from urllib.parse import urlparse
from typing import Optional
import logging

logger = logging.getLogger(__name__)

def is_valid_url(url: str) -> bool:
    """Memvalidasi URL"""
    try:
        result = urlparse(url.strip())
        valid = all([result.scheme in ['http', 'https'], result.netloc])
        if not valid:
            logger.debug("URL tidak valid: %s", url)
        return valid
    except Exception as e:
        logger.debug("Error memvalidasi URL %s: %s", url, e)
        return False
