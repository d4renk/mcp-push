"""Notification library wrapper with logging and thread pooling."""

import concurrent.futures
import logging
import os
import re
import sys
from typing import Dict

# Import legacy notify module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
import notify as _legacy

logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


def _log_print(*args, **kwargs) -> None:
    """Redirect print statements to logging."""
    sep = kwargs.get("sep", " ")
    end = kwargs.get("end", "")
    message = sep.join(str(arg) for arg in args) + end
    logger.info(message.rstrip("\n"))


_legacy.print = _log_print

push_config = _legacy.push_config


def send(title: str, content: str, ignore_default_config: bool = False, **kwargs) -> Dict[str, str]:
    """
    Send notification to all configured channels.

    Returns:
        Dict with 'errors' key containing per-channel error messages
    """
    if kwargs:
        if ignore_default_config:
            _legacy.push_config = kwargs
        else:
            _legacy.push_config.update(kwargs)

    global push_config
    push_config = _legacy.push_config

    if not content:
        logger.error("Content is empty for title: %s", title)
        return {"errors": {"input": "content is empty"}}

    skip_title = os.getenv("SKIP_PUSH_TITLE")
    if skip_title and title in re.split("\n", skip_title):
        logger.info("Skipping title blocked by SKIP_PUSH_TITLE: %s", title)
        return {"errors": {"skipped": "title skipped by SKIP_PUSH_TITLE"}}

    if _legacy.push_config.get("HITOKOTO") != "false":
        try:
            content = f"{content}\n\n{_legacy.one()}"
        except Exception as e:
            logger.warning("Failed to fetch hitokoto: %s", e)

    notify_function = _legacy.add_notify_function()
    if not notify_function:
        logger.warning("No notification channels configured")
        return {"errors": {"config": "no notification channels configured"}}

    errors: Dict[str, str] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(notify_function)) as executor:
        future_to_name = {
            executor.submit(mode, title, content): mode.__name__
            for mode in notify_function
        }
        for future in concurrent.futures.as_completed(future_to_name):
            name = future_to_name[future]
            try:
                result = future.result(timeout=30)
                if result:
                    errors[name] = str(result)
            except concurrent.futures.TimeoutError:
                errors[name] = "timeout after 30s"
                logger.error("Notification timeout on %s", name)
            except Exception as exc:
                errors[name] = str(exc)
                logger.error("Notification failure on %s: %s", name, exc)

    return {"errors": errors}
