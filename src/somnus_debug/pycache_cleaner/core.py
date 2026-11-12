#!/usr/bin/env python3
# somnus:metadata:v2
# somnus:
#   schema: "somnus://metadata/core/2.0.0"
#   id: "urn:somnus:artifact:01a19ace-7897-7158-b353-3dc7af71d00e"
#   revision: 1
#   title: "pycachecleaner.py"
#   classification:
#     category: "engineering"
#     type: "source-code"
#     role: "informative"
#     scope: "component"
#     tags: []
#   lifecycle:
#     status: "draft"
#   authority:
#     standing: "candidate"
#     scopes:
#       - target_ref: "urn:somnus:artifact:01a19ace-7897-7158-b353-3dc7af71d00e"
#         aspects: ["content"]
#   time: {}
#   names:
#     slug: "pycachecleaner-py"
#   knowledge:
#     coverage: "artifact"
#     subjects: ["urn:somnus:artifact:01a19ace-7897-7158-b353-3dc7af71d00e"]
#   access:
#     visibility: "internal"
#     allowed_uses: ["archive", "search", "reason"]
#   ingestion:
#     disposition: "candidate"
#     body_role: "source"
# somnus:end
"""
pycache_cleaner.py
===================

This script provides a configurable, production‑grade tool for finding and
removing Python bytecode caches (``__pycache__`` directories and ``*.pyc``/``*.pyo``
files) across one or more directory trees.  It was designed with
large, nested development folders in mind, including roots on multiple
Windows drive letters.

Features
--------

* **Configurable roots:** One or more root directories can be defined in a
  YAML configuration file.  The script will recurse into each root and
  operate only within those trees.
* **Exclude rules:** Directories and glob patterns can be excluded from
  traversal to avoid scanning large folders such as ``node_modules`` or
  ``.git``.
* **Target definitions:** You can specify which directory names or file
  patterns should be removed.  By default the script targets
  ``__pycache__``, ``*.pyc`` and ``*.pyo``.
* **Dry‑run mode:** Preview the actions without making changes.  The
  summary includes counts and estimated space savings.
* **Logging:** Informational output is sent to the console and can be
  written to a log file.  Warnings and errors are captured.
* **Depth limiting:** Optionally stop recursion beyond a maximum depth
  relative to each root.
* **Symlink control:** Choose whether or not to follow symbolic links when
  traversing the file system.

Usage
-----

Run the script from a terminal or command prompt.  You can override
settings from the configuration on the command line.  For example::

    # Perform a dry run using the default config.yaml in the same directory.
    python pycache_cleaner.py --dry-run

    # Use a custom config file and enable verbose logging.
    python pycache_cleaner.py --config C:\\path\\to\\config.yaml --verbose

The script returns a summary at the end with the number of items deleted
and the total size of data removed (in dry-run mode: the items that would
be deleted and the space that would be freed).  It exits 1 if a configured
root does not exist or is not a directory (the other roots are still
processed), and 1 on a configuration error.  Use the ``--dry-run`` flag to
ensure the configuration behaves as expected before performing a live
cleanup.

Configuration file
------------------

The YAML configuration controls the behaviour of the cleaner.  An example
``config.yaml`` might look like this:

```
roots:
  - C:\\Users\\treyr
  - D:\\Desktop\\Dev-Drive
exclude:
  # Names or glob patterns of directories to skip entirely.
  - node_modules
  - .git
  - venv
  - .venv
targets:
  # Directory names to delete.
  - __pycache__
  # File patterns to delete (within remaining directories).
  - "*.pyc"
  - "*.pyo"
dry_run: false
verbose: false
max_depth: null  # e.g. 10 to limit recursion; null for no limit
follow_symlinks: false
log_file: null  # Path to a log file; null to disable file logging
```

Fields
~~~~~~

* ``roots`` (list of strings): Paths to the top‑level directories to scan.
  At least one root must be provided.  Environment variables and ``~``
  are expanded automatically.
* ``exclude`` (list of strings): Directory names or glob patterns to
  exclude from traversal.  Each pattern is matched (``fnmatch``,
  case-sensitive) against the directory's name and against its path
  relative to the root, using ``/`` separators, so ``node_modules``,
  ``node_modules/*`` and ``vendor/keep`` all work.  Entire directories
  matching any of these patterns will be skipped.
* ``targets`` (list of strings): Names or glob patterns of directories or
  files to remove.  Items without a wildcard (``*`` or ``?``) are
  treated as directory names to delete wholesale.  Items containing
  wildcards are treated as file patterns.
* ``dry_run`` (bool): If true, perform a read‑only pass that reports
  actions without making changes.
* ``verbose`` (bool): Enable more chatty logging; shows each deletion.
* ``max_depth`` (int or null): Optional maximum depth of recursion.  A
  depth of ``0`` means only the root itself, ``1`` means one level down,
  etc.  ``null`` disables depth limiting.
* ``follow_symlinks`` (bool): If true, symbolic links will be followed
  during traversal.  Use with caution as it may lead to unexpected
  recursion into external trees.
* ``log_file`` (string or null): Path to a file to append log output to.
  Set to ``null`` to disable file logging.

"""

import argparse
import fnmatch
import logging
import os
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

try:
    import yaml  # type: ignore
except ImportError as e:
    # Raised (not printed) so the somnus-debug dispatcher reports it once,
    # cleanly; direct script use shows this message as the final error line.
    raise ImportError(
        "pycache-clean requires PyYAML. Install it via `pip install pyyaml`.", name="yaml"
    ) from e


class ConfigError(ValueError):
    """Raised when a cleaner configuration value has the wrong type or range."""


def _is_str_list(value: object) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


@dataclass
class CleanerConfig:
    """Configuration structure for the cleaner."""
    roots: List[str] = field(default_factory=list)
    exclude: List[str] = field(default_factory=list)
    targets: List[str] = field(default_factory=lambda: ["__pycache__", "*.pyc", "*.pyo"])
    dry_run: bool = False
    verbose: bool = False
    max_depth: Optional[int] = None
    follow_symlinks: bool = False
    log_file: Optional[str] = None

    @staticmethod
    def load(path: Path) -> Tuple["CleanerConfig", List[str]]:
        """Load and validate a YAML configuration without logging anything.

        Returns the validated config and a list of warning messages (unknown
        keys) for the caller to emit once logging is configured; emitting
        them here would implicitly configure the root logger at WARNING and
        silence the cleaner's own INFO output and log file.  Raises
        ConfigError for values of the wrong type or range.
        """
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if data is None:
            data = {}
        if not isinstance(data, dict):
            raise ConfigError(
                f"configuration must be a mapping of keys to values, got {type(data).__name__}"
            )
        cfg = CleanerConfig()
        warnings: List[str] = []
        for key, value in data.items():
            if isinstance(key, str) and key in CleanerConfig.__dataclass_fields__:
                setattr(cfg, key, value)
            else:
                warnings.append(f"Ignoring unknown config key '{key}'")
        cfg.validate()
        return cfg, warnings

    @staticmethod
    def from_yaml(path: Path) -> "CleanerConfig":
        """Load configuration from a YAML file (warnings go to ``logging``)."""
        cfg, warnings = CleanerConfig.load(path)
        for message in warnings:
            logging.warning("%s", message)
        return cfg

    def validate(self) -> None:
        """Reject values whose type or range would change what gets deleted.

        A scalar ``roots: /path`` would otherwise be iterated per character
        (yielding ``/``), and a string ``dry_run: "false"`` is truthy, so
        these are hard errors rather than coercions.
        """
        errors: List[str] = []
        if not _is_str_list(self.roots):
            errors.append(f"'roots' must be a list of path strings, got {self.roots!r}")
        for key in ("exclude", "targets"):
            value = getattr(self, key)
            if not _is_str_list(value):
                errors.append(f"'{key}' must be a list of strings, got {value!r}")
        for key in ("dry_run", "verbose", "follow_symlinks"):
            value = getattr(self, key)
            if not isinstance(value, bool):
                errors.append(f"'{key}' must be true or false, got {value!r}")
        depth = self.max_depth
        if depth is not None and (isinstance(depth, bool) or not isinstance(depth, int) or depth < 0):
            errors.append(f"'max_depth' must be an integer >= 0 or null, got {depth!r}")
        if self.log_file is not None and not isinstance(self.log_file, str):
            errors.append(f"'log_file' must be a path string or null, got {self.log_file!r}")
        if errors:
            raise ConfigError("invalid configuration: " + "; ".join(errors))

    def normalize(self) -> None:
        """Normalize and expand paths in the configuration.

        ``$VARS``/``${VARS}`` and ``~`` are expanded.  Relative roots resolve
        against the current working directory (not the config file's
        directory), as they always have.
        """
        self.roots = [
            str(Path(os.path.expandvars(p)).expanduser().resolve()) for p in self.roots
        ]
        if self.log_file:
            self.log_file = str(Path(os.path.expandvars(self.log_file)).expanduser().resolve())


class PycacheCleaner:
    """Implements the logic for finding and deleting Python cache artefacts."""

    def __init__(self, config: CleanerConfig) -> None:
        config.validate()
        config.normalize()
        if not config.roots:
            raise ValueError("No roots specified in configuration.")
        self.cfg = config
        # Separate targets into directory names and file patterns
        self.target_dirs = [t for t in config.targets if not any(c in t for c in "*?")]
        self.file_patterns = [t for t in config.targets if any(c in t for c in "*?")]
        # Exclude patterns are matched with "/" separators on every platform.
        self.exclude_patterns = [pat.replace("\\", "/") for pat in config.exclude]
        # Statistics
        self.deleted_dirs: int = 0
        self.deleted_files: int = 0
        self.deleted_bytes: int = 0
        # Roots that could not be scanned (missing or not a directory).
        self.failed_roots: List[str] = []

    def run(self) -> None:
        """Run the cleaner across all configured root directories."""
        for root in self.cfg.roots:
            path = Path(root)
            if not path.exists() or not path.is_dir():
                logging.error("Root path does not exist or is not a directory: %s", root)
                self.failed_roots.append(root)
                continue
            logging.info("Scanning root: %s", root)
            self._scan_root(path)
        # Summary
        if self.cfg.dry_run:
            logging.info("Summary: would delete %d directories, %d files; would free %.2f MiB",
                         self.deleted_dirs, self.deleted_files, self.deleted_bytes / (1024 * 1024))
        else:
            logging.info("Summary: deleted %d directories, %d files; freed %.2f MiB", self.deleted_dirs,
                         self.deleted_files, self.deleted_bytes / (1024 * 1024))

    def _scan_root(self, root: Path) -> None:
        """Recursively scan a root directory and delete matching targets."""
        # Use a stack for iterative traversal to avoid deep recursion
        stack: List[Tuple[Path, int]] = [(root, 0)]
        while stack:
            current, depth = stack.pop()
            try:
                with os.scandir(current) as it:
                    entries = list(it)
            except PermissionError:
                logging.warning("Skipping %s due to permission error", current)
                continue
            # Check for depth limiting
            if self.cfg.max_depth is not None and depth > self.cfg.max_depth:
                continue
            # First, handle directory targets directly under current
            for entry in entries:
                if entry.is_dir(follow_symlinks=self.cfg.follow_symlinks):
                    # Determine whether to delete this directory
                    if self._is_excluded(entry.name, self._relative(root, entry.path)):
                        logging.debug("Skipping excluded directory: %s", entry.path)
                        continue
                    if entry.name in self.target_dirs:
                        self._delete_directory(Path(entry.path))
                        continue
            # Now process files and collect subdirectories to traverse
            for entry in entries:
                try:
                    if entry.is_dir(follow_symlinks=self.cfg.follow_symlinks):
                        if (
                            self._is_excluded(entry.name, self._relative(root, entry.path))
                            or entry.name in self.target_dirs
                        ):
                            # Already handled or excluded; skip
                            continue
                        stack.append((Path(entry.path), depth + 1))
                    elif entry.is_file(follow_symlinks=self.cfg.follow_symlinks):
                        if self._match_file(entry.name):
                            self._delete_file(Path(entry.path))
                except OSError:
                    # Some entries may disappear between scandir and stat
                    logging.debug("Ignoring disappearing entry: %s", entry.path)

    @staticmethod
    def _relative(root: Path, path: str) -> str:
        """Return ``path`` relative to ``root`` with "/" separators."""
        return Path(os.path.relpath(path, root)).as_posix()

    def _is_excluded(self, name: str, rel_path: Optional[str] = None) -> bool:
        """Check whether a directory matches any exclude pattern.

        A pattern matches the directory's bare name (``node_modules``), its
        path relative to the scanned root (``vendor/keep``), or that path
        with a trailing slash, so ``node_modules/*`` -- "everything inside
        node_modules" -- excludes the directory itself.
        """
        candidates = [name]
        if rel_path is not None:
            candidates += [rel_path, rel_path + "/"]
        for pat in self.exclude_patterns:
            if any(fnmatch.fnmatchcase(candidate, pat) for candidate in candidates):
                return True
        return False

    def _match_file(self, name: str) -> bool:
        """Check whether a file name matches any target file pattern."""
        for pat in self.file_patterns:
            if fnmatch.fnmatchcase(name, pat):
                return True
        return False

    def _delete_directory(self, path: Path) -> None:
        """Delete a directory tree and update statistics."""
        try:
            size = self._get_dir_size(path)
        except Exception:
            size = 0
        logging.debug("%s directory: %s (%.2f MiB)", "Would delete" if self.cfg.dry_run else "Deleting",
                      path, size / (1024 * 1024))
        if not self.cfg.dry_run:
            try:
                shutil.rmtree(path)
            except Exception as e:
                logging.warning("Failed to delete %s: %s", path, e)
                return
        self.deleted_dirs += 1
        self.deleted_bytes += size
        if self.cfg.verbose:
            logging.info("%s directory %s", "Would remove" if self.cfg.dry_run else "Removed", path)

    def _delete_file(self, path: Path) -> None:
        """Delete a single file and update statistics."""
        try:
            size = path.stat().st_size
        except Exception:
            size = 0
        logging.debug("%s file: %s (%.2f KiB)", "Would delete" if self.cfg.dry_run else "Deleting",
                      path, size / 1024)
        if not self.cfg.dry_run:
            try:
                path.unlink()
            except Exception as e:
                logging.warning("Failed to delete file %s: %s", path, e)
                return
        self.deleted_files += 1
        self.deleted_bytes += size
        if self.cfg.verbose:
            logging.info("%s file %s", "Would remove" if self.cfg.dry_run else "Removed", path)

    @staticmethod
    def _get_dir_size(path: Path) -> int:
        """Compute total size of files under a directory tree."""
        total = 0
        for root, _, files in os.walk(path, onerror=lambda e: None):
            for fname in files:
                fpath = os.path.join(root, fname)
                try:
                    total += os.path.getsize(fpath)
                except Exception:
                    continue
        return total


def setup_logging(cfg: CleanerConfig) -> None:
    """Configure logging based on the configuration and CLI options."""
    level = logging.DEBUG if cfg.verbose else logging.INFO
    handlers: List[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    if cfg.log_file:
        try:
            file_handler = logging.FileHandler(cfg.log_file, mode="a", encoding="utf-8")
            handlers.append(file_handler)
        except Exception as e:
            print(f"Could not open log file {cfg.log_file}: {e}", file=sys.stderr)
    logging.basicConfig(level=level, format="%(asctime)s [%(levelname)s] %(message)s", handlers=handlers)


def _non_negative_int(text: str) -> int:
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid int value: {text!r}") from None
    if value < 0:
        raise argparse.ArgumentTypeError(f"must be >= 0, got {value}")
    return value


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command‑line arguments."""
    parser = argparse.ArgumentParser(description="Remove Python bytecode caches across directory trees.")
    parser.add_argument("--config", type=str, default="config.yaml",
                        help="Path to YAML configuration file (default: config.yaml)")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without deleting anything")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging output")
    parser.add_argument("--max-depth", type=_non_negative_int, default=None, help="Maximum recursion depth (overrides config)")
    parser.add_argument("--follow-symlinks", action="store_true", help="Follow symbolic links during traversal")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    config_path = Path(args.config).expanduser().resolve()
    if not config_path.exists():
        print(f"Configuration file not found: {config_path}", file=sys.stderr)
        return 1
    try:
        cfg, config_warnings = CleanerConfig.load(config_path)
    except (ConfigError, yaml.YAMLError, OSError) as e:
        print(f"Configuration error in {config_path}: {e}", file=sys.stderr)
        return 1
    # CLI flags override config
    if args.dry_run:
        cfg.dry_run = True
    if args.verbose:
        cfg.verbose = True
    if args.max_depth is not None:
        cfg.max_depth = args.max_depth
    if args.follow_symlinks:
        cfg.follow_symlinks = True
    # Logging is configured before any warning is emitted (see load()).
    setup_logging(cfg)
    for message in config_warnings:
        logging.warning("%s", message)
    logging.info("Starting pycache cleaner (dry_run=%s)", cfg.dry_run)
    try:
        cleaner = PycacheCleaner(cfg)
        cleaner.run()
    except Exception as e:
        logging.exception("An unexpected error occurred: %s", e)
        return 1
    return 1 if cleaner.failed_roots else 0


if __name__ == "__main__":
    raise SystemExit(main())