#!/usr/bin/env python3
import json,sys
from pathlib import Path
root=Path(__file__).resolve().parent.parent
required=['README.md','AGENTS.md','requirements.txt','scripts/kit.py','scripts/render-page.py','scripts/verify-output.py','.claude/skills/codemap/scripts/codemap.py']
bad=[x for x in required if not(root/x).exists()]
for f in root.rglob('*.json'):
 if any(p in {'.git','.venv','node_modules'} for p in f.parts):continue
 try:json.loads(f.read_text(encoding='utf-8'))
 except Exception:bad.append(f'Invalid JSON {f.relative_to(root)}')
if bad:print('\n'.join(f'- Missing or invalid: {x}' for x in bad),file=sys.stderr);raise SystemExit(1)
print('Layerlift Python kit structure is valid.')
