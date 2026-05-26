"""Async worker that pretends to consume analytics events from a queue.

Pinned-vulnerable deps in requirements.txt are intentional — they exist
to demonstrate `Failed_SupplyChain` against the strict SCA branch (Kill
on fixable). Never use this image in production; the package versions
are known-bad on purpose.
"""

from __future__ import annotations

import logging
import os
import signal
import sys
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("analytics-worker")

_STOPPING = False


def _handle_signal(signum: int, _frame: object) -> None:
    global _STOPPING
    logger.info("received signal %s, shutting down", signum)
    _STOPPING = True


def main() -> int:
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)
    interval = float(os.environ.get("TICK_INTERVAL", "2"))
    logger.info("analytics-worker starting (tick=%ss)", interval)
    while not _STOPPING:
        logger.info("drained analytics batch")
        time.sleep(interval)
    logger.info("analytics-worker stopped")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
