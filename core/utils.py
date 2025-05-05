import asyncio
import sys
from pathlib import Path
from typing import Any, Dict

import yaml
from loguru import logger


def configure_logging(logfile: str | None = None, level: str = "INFO") -> None:
    logger.remove()  # reset default
    fmt = "{time} | {level} | {message}"
    logger.add(sys.stderr, level=level, format=fmt)
    if logfile:
        logger.add(logfile, level=level, serialize=True)


def load_config(file: Path | None, overrides: Dict[str, Any] | None) -> Dict[str, Any]:
    cfg: Dict[str, Any] = {}
    if file and file.exists():
        with file.open() as f:
            cfg = yaml.safe_load(f) or {}
    cfg.update(overrides or {})
    return cfg


async def async_backoff(fn, *args, retries: int = 3, **kwargs):
    delay = 1
    for attempt in range(retries):
        try:
            return await fn(*args, **kwargs)
        except Exception as e:  # noqa: BLE001
            if attempt == retries - 1:
                raise
            logger.warning(f"retrying after error: {e}")
            await asyncio.sleep(delay)
            delay *= 2
