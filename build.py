from pathlib import Path
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parent
module = root / "site/tools/fde"
subprocess.run([sys.executable, "build_html.py"], cwd=module, check=True)
shutil.copytree(root / "site", root / "dist", dirs_exist_ok=True,
                ignore=shutil.ignore_patterns("*.py", "__pycache__", ".DS_Store"))
