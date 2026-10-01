"""Choose mjpython only for macOS GUI; forward script/module args unchanged."""
from pathlib import Path
import os
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
os.chdir(root)
os.environ.setdefault("MPLCONFIGDIR", str(root / ".cache/matplotlib"))
os.environ.setdefault("PYTHONUTF8", "1")
args = sys.argv[1:]
if not args:
    raise SystemExit("Usage: scripts/run.sh examples/00_view.py [--headless] / scripts/run.ps1 ...")
gui = "--headless" not in args and (Path(args[0]).name == "00_view.py" or "--viewer" in args)
program = Path(sys.executable)
if sys.platform == "darwin" and gui:
    program = Path(sys.prefix) / "bin/mjpython"
    if not program.exists():
        raise SystemExit("mjpython missing; rerun scripts/install.sh")
    # Use installed standalone Command Line Tools when available. This only
    # changes the child process, not the system-wide Xcode developer selection.
    tool_dir = Path("/Library/Developer/CommandLineTools/usr/bin")
    if (tool_dir / "otool").exists():
        os.environ["PATH"] = str(tool_dir) + os.pathsep + os.environ.get("PATH", "")
    # uv/python-build-standalone may use @rpath/libpython*.dylib. mjpython moves
    # the executable location, so preserve the original Python library path.
    lib_dir = Path(sys.base_prefix) / "lib"
    if list(lib_dir.glob("libpython*.dylib")):
        prior = os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", "/usr/local/lib:/usr/lib")
        os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = str(lib_dir) + os.pathsep + prior
raise SystemExit(subprocess.call([str(program), *args], env=os.environ.copy()))
