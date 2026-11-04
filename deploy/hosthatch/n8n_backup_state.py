#!/usr/bin/env python3
"""Capture n8n into protected staging; never open a writable live SQLite connection.

Only the explicit production targets below are permitted. No Docker lifecycle commands.
Raw subprocess errors, paths inside data, config values and keys never reach stdout.
"""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import sqlite3
import stat
import struct
import subprocess
import time

TARGETS = {
    "standalone": {"project": "n8n", "service": "n8n", "volume": "n8n_data"},
    "public-rag-production": {"project": "abap-public-rag-production",
        "service": "public-rag-n8n", "volume": "public_rag_production_n8n"},
}
DB_NAMES = {"database.sqlite", "database.sqlite-wal", "database.sqlite-shm", "database.sqlite-journal"}

class CaptureError(Exception):
    pass

def require(condition, message):
    if not condition:
        raise CaptureError(message)

def docker(*args):
    result = subprocess.run(["/usr/bin/docker", *args], capture_output=True, text=True, timeout=20,
        env={"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "HOME": "/nonexistent",
             "DOCKER_HOST": "unix:///var/run/docker.sock"})
    require(result.returncode == 0, "Docker metadata query failed")
    return result.stdout

def discover(target):
    spec = TARGETS[target]
    ids = docker("ps", "-a", "--filter", "label=com.docker.compose.project="+spec["project"],
        "--filter", "label=com.docker.compose.service="+spec["service"], "--format", "{{.ID}}").split()
    require(len(ids) == 1, "Expected exactly one project-scoped service")
    info = json.loads(docker("inspect", ids[0]))[0]
    require(info.get("State", {}).get("Running") is True, "Required instance is not running")
    labels = info.get("Config", {}).get("Labels") or {}
    require(labels.get("com.docker.compose.project") == spec["project"] and
        labels.get("com.docker.compose.service") == spec["service"], "Service ownership mismatch")
    mounts = [m for m in info.get("Mounts", []) if m.get("Destination") == "/home/node/.n8n"]
    require(not any(m.get("Destination", "").startswith("/home/node/.n8n/") for m in info.get("Mounts", [])),
        "Nested data mounts require an explicit backup plan")
    values = dict(x.split("=", 1) for x in info.get("Config", {}).get("Env", []) if "=" in x)
    require(values.get("DB_TYPE", "sqlite") == "sqlite" and values.get("DB_SQLITE_DATABASE", "database.sqlite") == "database.sqlite",
        "External or custom database requires a separate capture plan")
    require(values.get("N8N_DEFAULT_BINARY_DATA_MODE", "default") in {"default", "filesystem", "database"},
        "External binary storage requires a separate recovery plan")
    require(len(mounts) == 1 and mounts[0].get("Type") == "volume", "Required named data volume missing")
    mount = mounts[0]
    volume = json.loads(docker("volume", "inspect", mount["Name"]))[0]
    vlabels = volume.get("Labels") or {}
    require(vlabels.get("com.docker.compose.project") == spec["project"] and
        vlabels.get("com.docker.compose.volume") == spec["volume"], "Data volume ownership mismatch")
    source = Path(volume["Mountpoint"])
    require(str(source) == mount["Source"] and source.is_dir() and
        source.resolve() == source and not source.is_symlink(), "Unexpected volume mountpoint")
    return info, source

def signature(path):
    s = path.lstat()
    return s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns, stat.S_IMODE(s.st_mode), s.st_uid, s.st_gid

def optional_signature(path):
    try:
        return signature(path)
    except FileNotFoundError:
        return None

def hash_file(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def persistent_tree(source):
    result = {}
    for root, dirs, files in os.walk(source, followlinks=False):
        for name in sorted(dirs+files):
            p = Path(root)/name
            relative = p.relative_to(source).as_posix()
            # n8n event logs are not needed to restore workflows/credentials/executions.
            if "/" not in relative and (name in DB_NAMES or name.startswith("n8nEventLog")):
                continue
            s = p.lstat()
            require(stat.S_ISREG(s.st_mode) or stat.S_ISDIR(s.st_mode) or stat.S_ISLNK(s.st_mode),
                "Unsupported persistent file type")
            if p.is_symlink():
                target = os.readlink(p)
                require(not os.path.isabs(target) and p.resolve().is_relative_to(source.resolve()),
                    "External persistent symlink is not recoverable")
                result[relative] = {"kind": "symlink", "target": target, "signature": signature(p)}
            elif p.is_dir():
                result[relative] = {"kind": "directory", "signature": signature(p)}
            else:
                before = signature(p)
                result[relative] = {"kind": "file", "signature": before, "sha256": hash_file(p)}
                require(before == signature(p), "Persistent data changed during capture")
    return result

def preserve(source, target):
    s = source.lstat()
    if not target.is_symlink():
        os.chmod(target, stat.S_IMODE(s.st_mode))
    os.chown(target, s.st_uid, s.st_gid, follow_symlinks=False)

def copy_persistent(source, destination, tree, limit):
    used = 0
    for relative, item in sorted(tree.items(), key=lambda pair: (pair[0].count("/"), pair[0])):
        src, dst = source/relative, destination/relative
        if item["kind"] == "directory":
            dst.mkdir(exist_ok=False)
        elif item["kind"] == "symlink":
            dst.symlink_to(item["target"])
        else:
            used += src.stat().st_size
            require(used <= limit, "Protected staging limit exceeded")
            shutil.copyfile(src, dst, follow_symlinks=False)
            require(hash_file(dst) == item["sha256"], "Persistent data changed during copy")
        preserve(src, dst)
    return used

def copy_bounded(source, target, limit):
    require(stat.S_ISREG(source.lstat().st_mode), "SQLite source must be a regular file")
    used = 0
    with source.open("rb") as src, target.open("xb") as dst:
        for chunk in iter(lambda: src.read(1024*1024), b""):
            used += len(chunk)
            require(used <= limit, "Protected staging limit exceeded")
            dst.write(chunk)
    return used

def capture_database(source, data, bundle, limit, deadline):
    db = source/"database.sqlite"
    wal = source/"database.sqlite-wal"
    shm = source/"database.sqlite-shm"
    for path in [db]+[p for p in (wal, shm) if p.exists() or p.is_symlink()]:
        require(stat.S_ISREG(path.lstat().st_mode) and path.resolve() == path, "Unexpected SQLite source file")
    # systemd ProtectSystem=strict makes source data read-only in this service's
    # namespace. SQLite's native online backup then handles concurrent WAL writers;
    # the kernel also prohibits creating/updating any source DB or SHM sidecar.
    protected = bool(os.statvfs(db).f_flag & os.ST_RDONLY)
    if protected and wal.is_file() and shm.is_file():
        require(all(os.statvfs(p).f_flag & os.ST_RDONLY for p in (wal, shm)), "Unprotected SQLite sidecar mount")
        reader = sqlite3.connect(db.as_uri()+"?mode=ro", uri=True, timeout=5)
        writer = sqlite3.connect(str(data/"database.sqlite"))
        try:
            reader.execute("PRAGMA query_only=ON")
            reader.execute("BEGIN")
            reader.execute("SELECT count(*) FROM sqlite_schema").fetchone()
            size = reader.execute("PRAGMA page_size").fetchone()[0]
            def progress(status, remaining, total):
                require(time.monotonic() < deadline and total*size <= limit, "Online backup resource limit exceeded")
            reader.backup(writer, pages=128, progress=progress, sleep=0.05)
        finally:
            writer.close(); reader.close()
        require(not (data/"database.sqlite-wal").exists() or (data/"database.sqlite-wal").stat().st_size == 0,
            "Destination backup did not finish consolidating")
        for name in ("database.sqlite-wal", "database.sqlite-shm"):
            if (data/name).exists(): (data/name).unlink()
        with (data/"database.sqlite").open("r+b") as output:
            output.seek(18); output.write(b"\1\1")
        return "sqlite-online-kernel-readonly-source"
    # Outside the sandbox, never open the live DB through SQLite (even mode=ro
    # could write SHM metadata). A stable, checksum-verified raw copy is fail-closed.
    before = [optional_signature(source/x) for x in ("database.sqlite", "database.sqlite-wal")]
    journal = source/"database.sqlite-journal"
    require(not journal.exists() or journal.stat().st_size == 0, "Rollback journal needs separate review")
    used = copy_bounded(db, data/"database.sqlite", limit)
    copied_wal = bundle/"captured-wal"
    if before[1]:
        used += copy_bounded(wal, copied_wal, limit-used)
    require(before == [optional_signature(source/x) for x in ("database.sqlite", "database.sqlite-wal")], "SQLite changed during file capture; use protected online backup")
    require(not journal.exists() or journal.stat().st_size == 0, "Rollback journal appeared during capture")
    apply_committed_wal(data/"database.sqlite", copied_wal, limit-(copied_wal.stat().st_size if copied_wal.exists() else 0), deadline)
    if copied_wal.exists(): copied_wal.unlink()
    return "stable-committed-stream-copy"

def apply_committed_wal(db, wal, limit, deadline):
    """SQLite WAL specification: checksum every current-generation frame before replay.

    Source files are NEVER replayed or opened by SQLite. Only the new staged copy changes.
    """
    with db.open("rb") as stream:
        header = stream.read(100)
    require(header.startswith(b"SQLite format 3\0"), "Invalid staged database")
    page_size = int.from_bytes(header[16:18], "big")
    page_size = 65536 if page_size == 1 else page_size
    require(512 <= page_size <= 65536 and not page_size & (page_size-1), "Invalid page size")
    require(db.stat().st_size % page_size == 0, "Incomplete database copy")
    if wal.exists() and wal.stat().st_size:
        with wal.open("rb") as stream:
            raw = stream.read(32)
            require(len(raw) == 32, "Incomplete WAL")
            magic, version, size, _, salt1, salt2, check1, check2 = struct.unpack(">8I", raw)
            require(magic in (0x377f0682, 0x377f0683) and version == 3007000 and size == page_size, "Unsupported WAL")
            order = "<" if magic == 0x377f0682 else ">"
            def checksum(data, previous=(0, 0)):
                a, b = previous
                for x, y in struct.iter_unpack(order+"II", data):
                    a=(a+x+b)&0xffffffff; b=(b+y+a)&0xffffffff
                return a, b
            previous = checksum(raw[:24])
            require(previous == (check1, check2), "WAL header checksum mismatch")
            committed_end, committed_pages = None, None
            while True:
                require(time.monotonic() < deadline, "Capture time limit exceeded")
                frame = stream.read(24)
                if len(frame) < 24:
                    break
                number, final_size, a, b, c, d = struct.unpack(">6I", frame)
                if (a, b) != (salt1, salt2):
                    break
                page = stream.read(page_size)
                if len(page) < page_size:
                    break  # An incomplete final frame has no commit marker.
                require(number and number*page_size <= limit and final_size*page_size <= limit, "Staging page limit exceeded")
                previous = checksum(page, checksum(frame[:8], previous))
                require(previous == (c, d), "WAL frame checksum mismatch")
                if final_size:
                    committed_end, committed_pages = stream.tell(), final_size
            require(committed_end is not None, "No valid committed WAL prefix")
            stream.seek(32)
            with db.open("r+b") as output:
                while stream.tell() < committed_end:
                    frame, page = stream.read(24), stream.read(page_size)
                    number = int.from_bytes(frame[:4], "big")
                    if number <= committed_pages:
                        output.seek((number-1)*page_size)
                        output.write(page)
                output.truncate(committed_pages*page_size)
    with db.open("r+b") as output:
        output.seek(18)
        output.write(b"\1\1")

def key_check(info, source):
    require((source/"config").is_file() and not (source/"config").is_symlink()
        and (source/"config").stat().st_size <= 65536, "Persistent config must be a bounded regular file")
    config = json.loads((source/"config").read_text())
    stored = config.get("encryptionKey")
    require(isinstance(stored, str) and stored, "Persistent encryption key unavailable")
    values = dict(x.split("=", 1) for x in info.get("Config", {}).get("Env", []) if "=" in x)
    if values.get("N8N_ENCRYPTION_KEY"):
        require(values["N8N_ENCRYPTION_KEY"] == stored, "Stored and environment encryption keys differ")
    if values.get("N8N_ENCRYPTION_KEY_FILE"):
        mounts = [m for m in info.get("Mounts", []) if m.get("Destination") == values["N8N_ENCRYPTION_KEY_FILE"]]
        require(len(mounts) == 1, "Encryption-key secret mount unavailable")
        p = Path(mounts[0]["Source"])
        require(p.is_file() and not p.is_symlink() and p.stat().st_size < 16384, "Invalid key secret source")
        require(p.read_text().strip() == stored, "Stored and secret-file encryption keys differ")

def verify(bundle):
    manifest = json.loads((bundle/"capture.json").read_text())
    require(manifest.get("format") == "abap-n8n-online-v2", "Unsupported capture format")
    require(manifest.get("target") in TARGETS and all(manifest.get(key) == value
        for key, value in TARGETS[manifest["target"]].items()), "Restored capture target ownership mismatch")
    require({"data/database.sqlite", "data/config", "runtime.json"} <= set(manifest["files"]), "Required recovery files omitted")
    for name, expected in manifest["files"].items():
        path = bundle/name
        require(not Path(name).is_absolute() and ".." not in Path(name).parts and not path.is_symlink()
            and path.resolve().is_relative_to(bundle.resolve()), "Invalid manifest path")
        require(hash_file(path) == expected, "Restored capture checksum mismatch")
    for name, expected in manifest.get("symlinks", {}).items():
        path = bundle/name
        require(not Path(name).is_absolute() and ".." not in Path(name).parts and path.is_symlink()
            and path.resolve().is_relative_to(bundle.resolve()) and os.readlink(path) == expected, "Restored symlink mismatch")
    connection = sqlite3.connect((bundle/"data/database.sqlite").as_uri()+"?mode=ro&immutable=1", uri=True)
    try:
        require(connection.execute("PRAGMA integrity_check").fetchall() == [("ok",)], "Staged database integrity check failed")
        rows = connection.execute("SELECT id, active FROM workflow_entity ORDER BY id").fetchall()
        require(hashlib.sha256(json.dumps(rows).encode()).hexdigest() == manifest["workflow_fingerprint"], "Restored workflow inventory mismatch")
    finally:
        connection.close()
    require(bool(json.loads((bundle/"data/config").read_text()).get("encryptionKey")), "Restored persistent key missing")
    return {"target": manifest["target"], "workflow_count": len(rows), "active_workflow_count": sum(x[1] == 1 for x in rows)}

def capture(target, bundle, limit, info=None, source=None):
    require(target in TARGETS, "Unapproved backup target")
    discovered = info is None
    if discovered:
        info, source = discover(target)
    require(not bundle.exists(), "Refusing to overwrite an existing capture")
    require(bundle.parent.is_dir() and not bundle.parent.is_symlink(), "Protected staging parent missing")
    bundle.mkdir(mode=0o700)
    data = bundle/"data"
    data.mkdir(mode=0o700)
    deadline = time.monotonic()+300
    try:
        key_check(info, source)
        secret_sources = []
        for mount in info.get("Mounts", []):
            if mount.get("Destination", "").startswith("/run/secrets/"):
                p = Path(mount["Source"])
                require(p.is_file() and not p.is_symlink() and p.stat().st_size <= 65536, "Unsupported mounted secret source")
                secret_sources.append((p, mount["Destination"], signature(p), hash_file(p)))
        tree = persistent_tree(source)
        require("config" in tree, "Required persistent config omitted")
        method = capture_database(source, data, bundle, limit, deadline)
        used = (data/"database.sqlite").stat().st_size
        used += copy_persistent(source, data, tree, limit-used)
        require(tree == persistent_tree(source), "Persistent files changed across database capture")
        key_check(info, source)
        secret_map = []
        secret_bytes = sum(item[2][1] for item in secret_sources)
        require(used+secret_bytes <= limit, "Secret capture exceeds staging budget")
        if secret_sources:
            (bundle/"secrets").mkdir(mode=0o700)
        for number, (path, destination, sig, expected) in enumerate(secret_sources):
            copied = bundle/"secrets"/str(number)
            copy_bounded(path, copied, 65536); copied.chmod(0o600)
            require(signature(path) == sig and hash_file(path) == expected and hash_file(copied) == expected,
                "Mounted secret changed during capture")
            secret_map.append({"destination": destination, "captured_file": "secrets/"+str(number)})
        if discovered:
            current, current_source = discover(target)
            require(current.get("Id") == info.get("Id") and current_source == source, "Container identity changed during capture")
        runtime = {"image_id": info.get("Image"), "configuration": info.get("Config", {}),
            "mount_requirements": info.get("Mounts", []), "captured_secrets": secret_map}
        runtime_bytes = (json.dumps(runtime, indent=2)+"\n").encode()
        require(used+secret_bytes+len(runtime_bytes) <= limit, "Runtime capture exceeds staging budget")
        (bundle/"runtime.json").write_bytes(runtime_bytes)
        (bundle/"runtime.json").chmod(0o600)
        require(time.monotonic() < deadline, "Capture time limit exceeded")
        preserve(source/"database.sqlite", data/"database.sqlite")
        preserve(source, data)
        connection = sqlite3.connect((data/"database.sqlite").as_uri()+"?mode=ro&immutable=1", uri=True)
        try:
            rows = connection.execute("SELECT id, active FROM workflow_entity ORDER BY id").fetchall()
        finally:
            connection.close()
        manifest = {"format": "abap-n8n-online-v2", "target": target, **TARGETS[target], "database_capture_method": method,
            "image_id": info.get("Image"), "captured_at_utc": time.time(),
            "retention": {"daily": 14, "weekly": 8, "monthly": 12},
            "files": {p.relative_to(bundle).as_posix(): hash_file(p) for p in data.rglob("*") if p.is_file() and not p.is_symlink()},
            "symlinks": {"data/"+name: item["target"] for name, item in tree.items() if item["kind"] == "symlink"},
            "workflow_fingerprint": hashlib.sha256(json.dumps(rows).encode()).hexdigest()}
        manifest["files"]["runtime.json"] = hash_file(bundle/"runtime.json")
        for number in range(len(secret_sources)):
            manifest["files"]["secrets/"+str(number)] = hash_file(bundle/"secrets"/str(number))
        manifest_bytes = (json.dumps(manifest, indent=2)+"\n").encode()
        require(used+secret_bytes+len(runtime_bytes)+len(manifest_bytes) <= limit, "Manifest exceeds staging budget")
        (bundle/"capture.json").write_bytes(manifest_bytes)
        os.chmod(bundle/"capture.json", 0o600)
        return verify(bundle)
    except Exception:
        # Preserve the failed protected capture for diagnosis; never delete unrelated data.
        raise

def run_identity(bundle, run_id):
    require(isinstance(run_id, str) and re.fullmatch(r"run-[0-9a-f]{32}", run_id), "Invalid run identity")
    parent = Path('/var/backups/n8n/runs')
    require(bundle == parent/run_id and parent.resolve() == parent and not parent.is_symlink(), "Unapproved run path")
    info = parent.stat()
    require(stat.S_ISDIR(info.st_mode) and info.st_uid == 0 and stat.S_IMODE(info.st_mode) == 0o700, "Untrusted run parent")
    require(bundle.resolve() == bundle and not bundle.is_symlink(), "Untrusted run directory")


def create_run(bundle, run_id):
    run_identity(bundle, run_id)
    require(not bundle.exists(), "Existing run must not be overwritten")
    bundle.mkdir(mode=0o700)
    with (bundle/'.run.json').open('x') as stream:
        os.chmod(stream.name, 0o600)
        json.dump({'run_id': run_id}, stream)


def cleanup_run(bundle, run_id):
    run_identity(bundle, run_id)
    info = bundle.stat()
    require(info.st_uid == 0 and stat.S_IMODE(info.st_mode) == 0o700, "Untrusted run directory owner or permissions")
    marker = bundle/'.run.json';info = marker.lstat()
    require(stat.S_ISREG(info.st_mode) and info.st_uid == 0 and stat.S_IMODE(info.st_mode) == 0o600
            and info.st_size < 128, "Untrusted run marker")
    require(json.loads(marker.read_text()) == {'run_id': run_id}, "Run marker identity changed")
    require({p.name for p in bundle.iterdir()} == {'.run.json', *TARGETS}, "Unexpected run contents retained")
    for target in TARGETS:
        child = bundle/target
        require(not child.is_symlink() and child.resolve() == child and child.stat().st_uid == 0, "Untrusted capture directory")
        require(verify(child)['target'] == target, "Capture target mismatch")
    # Only a new UUID run whose two captures passed verification; never legacy staging.
    shutil.rmtree(bundle)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=["capture", "verify", "check", "create-run", "cleanup"])
    parser.add_argument("--run-id")
    parser.add_argument("--target", choices=list(TARGETS))
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--limit-bytes", type=int, default=2_000_000_000)
    args = parser.parse_args()
    try:
        if args.operation == "check":
            for target in ([args.target] if args.target else TARGETS):
                info, source = discover(target)
                key_check(info, source)
            print('{"status":"required-production-targets-verified"}')
            raise SystemExit(0)
        require(args.bundle and args.bundle.is_absolute(), "Absolute protected bundle path required")
        require(args.limit_bytes > 0, "Positive staging limit required")
        if args.operation == "create-run":
            create_run(args.bundle, args.run_id)
            print('{"status":"owned-run-created"}')
            raise SystemExit(0)
        if args.operation == "cleanup":
            cleanup_run(args.bundle, args.run_id)
            print('{"status":"owned-staging-cleaned"}')
            raise SystemExit(0)
        summary = capture(args.target, args.bundle, args.limit_bytes) if args.operation == "capture" else verify(args.bundle)
        print(json.dumps({"status": "verified-capture", **summary}))
    except CaptureError as error:
        # CaptureError messages are fixed strings from require(), never raw backend data.
        print(json.dumps({"status": "failed", "reason": str(error)}))
        raise SystemExit(1)
    except Exception:
        print('{"status":"failed","reason":"Capture/verification failed; no raw errors or secrets printed"}')
        raise SystemExit(1)
