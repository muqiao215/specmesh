"""Bounded, descriptor-anchored document observations for the optional machine port."""
from __future__ import annotations

import os
import stat
from dataclasses import dataclass
from pathlib import Path

MAX_DOCUMENT_BYTES = 256 * 1024
MAX_DOCUMENTS = 64


def identity(value):
    return (value.st_dev, value.st_ino, value.st_mode, value.st_size,
            value.st_mtime_ns, value.st_ctime_ns)


@dataclass(frozen=True)
class Observation:
    path: Path
    identity: tuple
    content: bytes
    alias_identity: tuple
    git_mode: str
    git_content: bytes


class DocumentSnapshot:
    """Read once for discovery and inspection, then revalidate every observed input.

    POSIX dir_fd and O_NOFOLLOW are required by this optional executable profile.
    The Markdown standard itself has no such platform requirement.
    """
    def __init__(self, root: Path):
        if os.open not in os.supports_dir_fd or not hasattr(os, "O_NOFOLLOW"):
            raise ValueError("secure_snapshot_platform_unavailable")
        self.root = root
        self.fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        value = os.fstat(self.fd)
        self.root_identity = (value.st_dev, value.st_ino)
        self.files: dict[str, Observation | None] = {}
        self.directories: dict[str, tuple] = {}

    def __enter__(self):
        return self

    def __exit__(self, *_):
        os.close(self.fd)

    def _root_current(self):
        value = self.root.stat()
        if self.root.resolve(strict=True) != self.root or (value.st_dev, value.st_ino) != self.root_identity:
            raise ValueError("repository_changed_during_check")

    def _canonical(self, relative: str):
        candidate = Path(relative)
        if not relative or candidate.is_absolute() or ".." in candidate.parts:
            raise ValueError("relative_in_repo_path_required")
        self._root_current()
        target = (self.root / candidate).resolve(strict=True)
        if not target.is_relative_to(self.root):
            raise ValueError("symlink_path_escape")
        return target

    def _open(self, target: Path, directory=False):
        # Canonicalization permits internal links; openat traversal cannot follow a link
        # substituted in any canonical path component between resolution and open.
        current = os.dup(self.fd)
        try:
            parts = target.relative_to(self.root).parts
            for index, component in enumerate(parts):
                is_directory = directory or index < len(parts) - 1
                flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
                if is_directory:
                    flags |= os.O_DIRECTORY
                child = os.open(component, flags, dir_fd=current)
                os.close(current)
                current = child
            result, current = current, -1
            return result
        finally:
            if current >= 0:
                os.close(current)

    def _capture(self, relative: str):
        target = self._canonical(relative)
        alias = self.root / relative
        alias_before = alias.lstat()
        link = os.fsencode(os.readlink(alias)) if stat.S_ISLNK(alias_before.st_mode) else None
        fd = self._open(target)
        try:
            before = os.fstat(fd)
            if not stat.S_ISREG(before.st_mode):
                raise ValueError("document_must_be_regular_file")
            if before.st_size > MAX_DOCUMENT_BYTES:
                raise ValueError("document_too_large")
            chunks, size = [], 0
            while size <= MAX_DOCUMENT_BYTES:
                part = os.read(fd, min(64 * 1024, MAX_DOCUMENT_BYTES + 1 - size))
                if not part:
                    break
                chunks.append(part)
                size += len(part)
            if size > MAX_DOCUMENT_BYTES:
                raise ValueError("document_too_large")
            content = b"".join(chunks)
            if (identity(os.fstat(fd)) != identity(before) or self._canonical(relative) != target
                    or identity(target.stat()) != identity(before) or len(content) != before.st_size
                    or identity(alias.lstat()) != identity(alias_before)):
                raise ValueError("document_changed_during_check")
            mode = "120000" if link is not None else "100755" if before.st_mode & stat.S_IXUSR else "100644"
            return Observation(target, identity(before), content, identity(alias_before), mode, link if link is not None else content)
        finally:
            os.close(fd)

    def read(self, relative: str, *, optional=False):
        if relative not in self.files:
            if len(self.files) >= MAX_DOCUMENTS:
                raise ValueError("progressive_reference_limit")
            try:
                self.files[relative] = self._capture(relative)
            except FileNotFoundError:
                self.files[relative] = None
        observed = self.files[relative]
        if observed is None and not optional:
            raise FileNotFoundError(relative)
        return observed.content if observed else None

    def directory(self, relative: str):
        target = self._canonical(relative)
        fd = self._open(target, directory=True)
        try:
            value = os.fstat(fd)
            self.directories[relative] = (target, value.st_dev, value.st_ino)
        finally:
            os.close(fd)
        return target

    def verify(self):
        self._root_current()
        for relative, observed in self.files.items():
            try:
                current = self._capture(relative)
            except FileNotFoundError:
                current = None
            if current != observed:
                raise ValueError("document_changed_during_check")
        for relative, observed in self.directories.items():
            target = self._canonical(relative)
            fd = self._open(target, directory=True)
            try:
                value = os.fstat(fd)
                if (target, value.st_dev, value.st_ino) != observed:
                    raise ValueError("task_directory_changed_during_check")
            finally:
                os.close(fd)
