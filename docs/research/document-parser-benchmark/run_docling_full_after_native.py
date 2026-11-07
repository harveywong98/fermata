"""Keep CPU timing serial while allowing the orchestrator to stay responsive."""
import os,time,subprocess,sys
from pathlib import Path
B=Path(__file__).resolve().parent
pid=int(sys.argv[1])
while True:
 try:os.kill(pid,0)
 except ProcessLookupError:break
 time.sleep(2)
print('Native batch complete; starting standard PDF batch',flush=True)
env={**os.environ,'HF_HUB_OFFLINE':'1','BENCH_EXTENSIONS':'.pdf'}
raise SystemExit(subprocess.run([str(B/'.venv-docling/bin/python'),str(B/'run.py'),'docling-full-selection.json','docling'],cwd=B,env=env).returncode)
