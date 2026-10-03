#!/usr/bin/env python
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE","django_backend.config.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
if __name__=="__main__": main()
