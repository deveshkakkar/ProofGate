"""Set per-process output bounds after the CI transport drops privileges."""
import os
import resource
import sys

if os.getuid() == 0:
    raise SystemExit('Candidate execution as root is prohibited')
resource.setrlimit(resource.RLIMIT_FSIZE, (2 * 1024 * 1024, 2 * 1024 * 1024))
resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
os.execv(sys.argv[1], sys.argv[1:])
