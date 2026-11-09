"""Publish complete JSON records atomically; never expose an empty reservation."""
import json
import os
from pathlib import Path
import tempfile

from framework.errors import EvaluationError


class ReportDestination:
    def __init__(self, path):
        self.path = Path(path)
        self.owned_inode = None

    def publish(self, payload, reserve=False):
        # A signal during serialization leaves either no destination (reserve)
        # or the previous complete record (update). Temporary files are private.
        with tempfile.TemporaryDirectory(prefix='.proofgate-report-', dir=self.path.parent) as temp:
            pending = Path(temp) / 'record.json'
            fd = os.open(pending, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(fd, 'w', encoding='utf-8') as stream:
                json.dump(payload, stream, sort_keys=True, indent=2, allow_nan=False)
                stream.write('\n')
                stream.flush()
                os.fsync(stream.fileno())
                inode = os.fstat(stream.fileno())
            if reserve:
                # Link creation is atomic and rejects every existing destination,
                # including symlinks. Both names refer to already-fsynced bytes.
                os.link(pending, self.path)
            else:
                current = self.path.lstat()
                if (current.st_dev, current.st_ino) != self.owned_inode:
                    raise EvaluationError('report_changed', 'report',
                                          'Report destination changed; unrelated evidence was preserved.')
                os.replace(pending, self.path)
            self.owned_inode = (inode.st_dev, inode.st_ino)
