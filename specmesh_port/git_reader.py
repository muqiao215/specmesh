"""Bounded Git plumbing; never invoke worktree filters, hooks, or transports."""
from __future__ import annotations

import os
import selectors
import shutil
import subprocess
import time

MAX_GIT_OUTPUT = 512 * 1024


def read_git(root, *args):
    if not args or args[0] not in {"rev-parse", "ls-files", "ls-tree"}:
        raise ValueError("git_operation_not_read_only")
    binary = shutil.which("git")
    if not binary:
        raise ValueError("git_unavailable")
    env = {"PATH": os.environ.get("PATH", ""), "LC_ALL": "C", "GIT_OPTIONAL_LOCKS": "0",
           "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
           "GIT_NO_LAZY_FETCH": "1", "GIT_ALLOW_PROTOCOL": "", "GIT_TERMINAL_PROMPT": "0"}
    command = [binary, "--no-optional-locks", "--no-replace-objects", "--literal-pathspecs",
               "-c", "core.fsmonitor=false", "-c", "core.hooksPath=" + os.devnull,
               "-c", "protocol.allow=never", "-C", str(root), *args]
    child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    deadline, total, chunks = time.monotonic() + 5, 0, []
    try:
        with selectors.DefaultSelector() as selector:
            for stream in (child.stdout, child.stderr):
                os.set_blocking(stream.fileno(), False)
                selector.register(stream, selectors.EVENT_READ)
            while selector.get_map():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise ValueError("git_observation_timeout")
                for key, _ in selector.select(remaining):
                    part = os.read(key.fd, min(64 * 1024, MAX_GIT_OUTPUT + 1 - total))
                    if not part:
                        selector.unregister(key.fileobj)
                        continue
                    total += len(part)
                    if total > MAX_GIT_OUTPUT:
                        raise ValueError("git_observation_too_large")
                    if key.fileobj is child.stdout:
                        chunks.append(part)
            code = child.wait(timeout=max(0.001, deadline - time.monotonic()))
            if code != 0:
                raise ValueError("git_observation_unavailable")
            return b"".join(chunks)
    finally:
        if child.poll() is None:
            child.kill()
        child.wait()
        child.stdout.close()
        child.stderr.close()
