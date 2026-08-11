#!/usr/bin/env python3
from pathlib import Path
import sys
r=Path.cwd(); sys.exit(0 if (r/'.agents/team/charter.md').is_file() and (r/'.agents/team/reports/TEMPLATE.md').is_file() else 1)
