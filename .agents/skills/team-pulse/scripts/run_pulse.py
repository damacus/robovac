#!/usr/bin/env python3
import argparse,json
p=argparse.ArgumentParser();p.add_argument('--repo',required=True);p.add_argument('--dry-run',action='store_true');p.parse_args();print(json.dumps({'Boundary':'','Experiment':'','Friction':'','Keep':'','State':''},sort_keys=True))
