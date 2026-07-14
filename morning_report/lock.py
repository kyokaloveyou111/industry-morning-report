from __future__ import annotations

import json
import os
import time
from pathlib import Path


class RunLock:
    def __init__(self, path: Path, stale_after_seconds: int = 7200):
        self.path = path
        self.stale_after_seconds = stale_after_seconds
        self.acquired = False

    @staticmethod
    def _process_exists(pid: int) -> bool:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        except OSError:
            return False
        return True

    def __enter__(self) -> "RunLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            try:
                state = json.loads(self.path.read_text(encoding="utf-8"))
                age = time.time() - float(state["created_at"])
                if age < self.stale_after_seconds and self._process_exists(int(state["pid"])):
                    raise RuntimeError(f"Another report run is active with PID {state['pid']}")
            except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                pass
            self.path.unlink(missing_ok=True)

        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        fd = os.open(self.path, flags)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump({"pid": os.getpid(), "created_at": time.time()}, handle)
        self.acquired = True
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        if self.acquired:
            self.path.unlink(missing_ok=True)

