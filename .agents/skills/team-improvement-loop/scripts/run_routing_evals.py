#!/usr/bin/env python3
import argparse,json
p=argparse.ArgumentParser();p.add_argument('--repo',required=True);p.add_argument('--dry-run',action='store_true');a=p.parse_args();print(json.dumps({'dry_run':a.dry_run,'route':'read-only','work_created':False},sort_keys=True))
