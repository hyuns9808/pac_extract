'''
File that stores all functions related to downloading pac data from repos
'''
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional

# Regexes to detect progress lines from git
PHASE_PATTERNS = {
    "Enumerating objects": re.compile(r"Enumerating objects:\s+(\d+)%"),
    "Receiving objects":   re.compile(r"Receiving objects:\s+(\d+)%"),
    "Compressing objects": re.compile(r"Compressing objects:\s+(\d+)%"),
    "Resolving deltas":    re.compile(r"Resolving deltas:\s+(\d+)%"),
    "Updating files":      re.compile(r"Updating files:\s+(\d+)%"),
}

def _make_progress():
    """Return (use_tqdm, factory) where factory(name) -> (update(pct), close())."""
    try:
        from tqdm import tqdm
        def factory(name: str):
            bar = tqdm(total=100, desc=name, unit="%", leave=True, dynamic_ncols=True)
            current = 0
            def update(pct: int):
                nonlocal current
                pct = max(0, min(100, int(pct)))
                delta = pct - current
                if delta > 0:
                    bar.update(delta)
                    current = pct
            def close():
                if current < 100:
                    bar.update(100 - current)
                bar.close()
            return update, close
        return True, factory
    except Exception:
        def factory(name: str):
            current = -1
            def update(pct: int):
                nonlocal current
                pct = max(0, min(100, int(pct)))
                if pct != current:
                    print(f"{name}: {pct}%")
                    current = pct
            def close():
                if current != 100:
                    print(f"{name}: 100%")
            return update, close
        return False, factory

def run_git_with_progress(args: List[str], cwd: Optional[str] = None, env: Optional[dict] = None) -> None:
    """Run a git command with --progress, show progress bars, raise on failure."""
    if "--progress" not in args:
        args = args + ["--progress"]

    base_env = os.environ.copy()
    base_env["GIT_PROGRESS_DELAY"] = base_env.get("GIT_PROGRESS_DELAY", "0")
    if env:
        base_env.update(env)

    use_tqdm, factory = _make_progress()
    updaters, closers = {}, {}

    def get_handlers(phase: str):
        if phase not in updaters:
            upd, cls = factory(phase)
            updaters[phase] = upd
            closers[phase] = cls
        return updaters[phase], closers[phase]

    proc = subprocess.Popen(
        args,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,   # git progress comes via stderr
        text=True,
        bufsize=1,
        universal_newlines=True,
    )

    try:
        assert proc.stderr is not None
        for raw in proc.stderr:
            line = raw.rstrip("\n")
            matched = False
            for phase, pat in PHASE_PATTERNS.items():
                m = pat.search(line)
                if m:
                    pct = int(m.group(1))
                    upd, _ = get_handlers(phase)
                    upd(pct)
                    matched = True
                    break
            if not matched and not use_tqdm and line.strip():
                print(line)

        if proc.stdout:
            proc.stdout.read()

        ret = proc.wait()
        for cls in list(closers.values()):
            cls()
        if ret != 0:
            raise subprocess.CalledProcessError(ret, args)
    finally:
        try:
            if proc.poll() is None:
                proc.terminate()
        except Exception:
            pass

# ---- main helper: get subtree only ----
def get_pac_folder(
    tool_name: str,
    repo_git: str,
    folder: str,
    dest: str,
    ref: str = "main",
    include_folder_dir: bool = True,
):
    """
    Fetch ONLY `folder` (its files and subfolders) from the repo and place it at `dest`.

    - Uses sparse-checkout so network/data is minimized.
    - Copies just the requested subtree into `dest` (no .git left behind).
    - If include_folder_dir=True, you'll get dest/<folder_basename>/... ;
      otherwise the folder's *contents* are copied directly under dest.
    """
    print(f"Cloning PaC folder of tool:  {tool_name}")
    folder = folder.strip("/")

    # Clone into a temp dir, so we can extract just the subtree afterwards
    temp_root = Path(tempfile.mkdtemp(prefix="sparse_subtree_"))
    try:
        # 1) partial clone (no checkout)
        run_git_with_progress([
            "git", "clone",
            "--filter=blob:none",
            "--no-checkout",
            repo_git,
            str(temp_root)
        ])

        # 2) enable sparse checkout (cone mode) and set the path
        subprocess.run(["git", "-C", str(temp_root), "sparse-checkout", "init", "--cone"], check=True)
        subprocess.run(["git", "-C", str(temp_root), "sparse-checkout", "set", folder], check=True)

        # 3) checkout the desired ref
        run_git_with_progress(["git", "-C", str(temp_root), "checkout", ref])

        # 4) copy the subtree out to `dest`
        src = temp_root / folder
        if not src.exists():
            raise FileNotFoundError(f"Path '{folder}' does not exist in the repo at ref '{ref}'.")

        dest_path = Path(dest)
        dest_path.mkdir(parents=True, exist_ok=True)

        if include_folder_dir:
            # Copy as dest/<folder_basename>/...
            target = dest_path / src.name
            shutil.copytree(src, target, dirs_exist_ok=True)
            return str(target.resolve())
        else:
            # Copy contents of folder directly under dest/
            for entry in src.iterdir():
                tgt = dest_path / entry.name
                if entry.is_dir():
                    shutil.copytree(entry, tgt, dirs_exist_ok=True)
                else:
                    shutil.copy2(entry, tgt)
            return str(dest_path.resolve())
    finally:
        # Remove temporary clone (keeps disk clean)
        shutil.rmtree(temp_root, ignore_errors=True)
        print(f"✅ Download complete:  {tool_name}\n")

'''
if __name__ == "__main__":
    save_dir = create_base_dir()
    
    get_pac_folder(
        tool_name="Checkov",
        repo_git="https://github.com/bridgecrewio/checkov.git",
        folder="checkov/terraform/checks/resource",
        dest=os.path.join(save_dir, "Checkvo"),
        ref="main",
        )
    get_pac_folder(
        tool_name="KICS",
        repo_git="https://github.com/Checkmarx/kics.git",
        folder="assets/queries/terraform",
        dest=os.path.join(save_dir, "KICS"),
        ref="master",
        )
'''   