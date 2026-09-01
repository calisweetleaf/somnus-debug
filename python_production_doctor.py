#!/usr/bin/env python3
"""Python Production Doctor diagnoses Python project readiness without modifying source code.

Modified: 2026-06-08
Modified by: Somnus operator pass
Justification: I rebuilt this internal diagnostic tool because the uploaded single-file version was
structurally corrupted, duplicated, emoji-bearing, and incapable of reliably generating reports
under syntax and report-generation failures. I kept the one-file operating model, made YAML the
native configuration surface, added local report state with rollback, added AST and import graph
diagnostics, and forced failures into structured evidence instead of silent continuation.
Provenance: snapshots/v3.0/manifest.json
Files: python_production_doctor.py, python_doctor.yaml, test/python_production_doctor/test_python_production_doctor.py
Purpose: Diagnose Python source health, dependency health, report state, and production-readiness gates.
Origin: Core native Somnus internal developer tool.
"""

from __future__ import annotations

import argparse
import ast
import concurrent.futures
import datetime as dt
import fnmatch
import hashlib
import html
import importlib.util
import io
import json
import logging
import os
import re
import shutil
import sqlite3
import sys
import tokenize
from collections import Counter, defaultdict
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable, Literal, Mapping, MutableMapping, Sequence, TypeAlias

JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject: TypeAlias = dict[str, JsonValue]
ImportKind: TypeAlias = Literal["local", "standard_library", "third_party", "missing", "unresolved_relative"]

UTC = dt.timezone.utc
LOGGER_NAME = "python_production_doctor"
DEFAULT_CONFIG_NAME = "python_doctor.yaml"
RUN_ID_FORMAT = "%Y%m%dT%H%M%SZ"
COMMANDS = {"scan", "init-config", "history", "rollback", "self-check"}


class Severity(str, Enum):
    """Severity values used by issue gates and report sorting."""

    CRITICAL = "critical"
    SERIOUS = "serious"
    MINOR = "minor"
    INFO = "info"


class DoctorError(RuntimeError):
    """Base domain error with user-facing remediation and JSON-safe context."""

    default_remediation = "Correct the input or configuration named in the diagnostic context."

    def __init__(self, message: str, remediation: str | None = None, context: JsonObject | None = None) -> None:
        """Initialize a domain error.

        Args:
            message: Human-readable failure message.
            remediation: Recovery instruction.
            context: JSON-safe context payload.
        """
        super().__init__(message)
        self.message = message
        self.remediation = remediation or self.default_remediation
        self.context = context or {}

    def render(self) -> str:
        """Render a deterministic error block.

        Returns:
            User-facing error text with no raw traceback.
        """
        payload = json.dumps(self.context, indent=2, sort_keys=True) if self.context else "{}"
        return f"Doctor failure: {self.message}\nRemediation: {self.remediation}\nContext:\n{payload}"


class ConfigurationError(DoctorError):
    """Raised when YAML, JSON, or typed configuration validation fails."""

    default_remediation = "Fix the configuration file or regenerate it with init-config."

    def __init__(self, message: str, context: JsonObject | None = None) -> None:
        """Initialize a configuration error.

        Args:
            message: Configuration failure message.
            context: File, line, key, or value context.
        """
        super().__init__(message, self.default_remediation, context)


class FileReadError(DoctorError):
    """Raised when a source file cannot be read, decoded, or hashed."""

    default_remediation = "Verify the file exists, permissions are correct, and the encoding is valid."

    def __init__(self, message: str, context: JsonObject | None = None) -> None:
        """Initialize a file read error.

        Args:
            message: Read failure message.
            context: File path and OS context.
        """
        super().__init__(message, self.default_remediation, context)


class ReportGenerationError(DoctorError):
    """Raised when markdown, JSON, or state report artifacts cannot be written."""

    default_remediation = "Check output directory permissions and disk availability, then rerun."

    def __init__(self, message: str, context: JsonObject | None = None) -> None:
        """Initialize a report generation error.

        Args:
            message: Artifact failure message.
            context: Path and serialization details.
        """
        super().__init__(message, self.default_remediation, context)


class StateStoreError(DoctorError):
    """Raised when local report-state persistence cannot complete."""

    default_remediation = "Inspect the state database and report directory permissions."

    def __init__(self, message: str, context: JsonObject | None = None) -> None:
        """Initialize a state store error.

        Args:
            message: State failure message.
            context: Database or report details.
        """
        super().__init__(message, self.default_remediation, context)


class AnalysisExecutionError(DoctorError):
    """Raised when project-level analysis cannot proceed."""

    default_remediation = "Inspect the project root and rerun with a valid path."

    def __init__(self, message: str, context: JsonObject | None = None) -> None:
        """Initialize an analysis execution error.

        Args:
            message: Analysis failure message.
            context: Project or file context.
        """
        super().__init__(message, self.default_remediation, context)


@dataclass(frozen=True)
class YamlLine:
    """One prepared YAML line with indentation metadata."""

    number: int
    indent: int
    content: str


@dataclass(frozen=True)
class DoctorConfig:
    """Typed configuration for scan, report, and local state behavior."""

    schema_version: str
    min_function_lines: int
    min_class_lines: int
    min_docstring_length: int
    max_cyclomatic_complexity: int
    max_report_evidence_lines: int
    include_patterns: tuple[str, ...]
    ignore_patterns: tuple[str, ...]
    ignore_functions: tuple[str, ...]
    ignore_classes: tuple[str, ...]
    check_private_functions: bool
    check_nested_functions: bool
    require_module_docstring: bool
    require_class_docstring: bool
    require_function_docstring: bool
    require_parameter_hints: bool
    require_return_hints: bool
    detect_unused_imports: bool
    detect_test_gaps: bool
    detect_security_risks: bool
    detect_silent_failures: bool
    detect_dependency_cycles: bool
    state_dir: str
    reports_dir: str
    report_basename: str
    severity_exit_level: str
    max_workers: int
    markdown_include_css: bool
    severity_levels: Mapping[str, Severity]


@dataclass(frozen=True)
class DiagnosticIssue:
    """Single evidence-backed diagnostic issue."""

    category: str
    severity: Severity
    file_path: str
    line_number: int
    column_offset: int
    symbol: str
    message: str
    evidence: str
    remediation: str
    details: JsonObject

    def identity(self) -> str:
        """Return a stable identity string for de-duplication.

        Returns:
            Unique identity for issue comparison.
        """
        return "|".join([self.category, self.severity.value, self.file_path, str(self.line_number), self.symbol, self.message])


@dataclass(frozen=True)
class FunctionDiagnostic:
    """Static analysis summary for a function or method."""

    qualname: str
    kind: str
    line_number: int
    end_line_number: int
    executable_line_count: int
    statement_count: int
    cyclomatic_complexity: int
    return_count: int
    argument_count: int
    missing_type_hints: tuple[str, ...]
    has_docstring: bool
    decorators: tuple[str, ...]


@dataclass(frozen=True)
class ClassDiagnostic:
    """Static analysis summary for a class."""

    qualname: str
    line_number: int
    end_line_number: int
    executable_line_count: int
    method_count: int
    public_method_count: int
    bases: tuple[str, ...]
    decorators: tuple[str, ...]
    has_docstring: bool
    is_dataclass: bool
    is_exception: bool
    is_enum: bool


@dataclass(frozen=True)
class ImportRecord:
    """Import statement collected from AST."""

    module: str
    imported_names: tuple[str, ...]
    bound_names: tuple[str, ...]
    line_number: int
    column_offset: int
    level: int
    kind: str
    raw: str


@dataclass(frozen=True)
class ImportEdge:
    """Resolved import relationship from a source file to a module or local file."""

    source_file: str
    imported_module: str
    line_number: int
    classification: ImportKind
    status: str
    target_file: str
    confidence: float
    raw: str


@dataclass(frozen=True)
class FileMetrics:
    """Quantitative metrics collected for one source file."""

    total_lines: int
    code_lines: int
    comment_lines: int
    blank_lines: int
    total_classes: int
    total_functions: int
    total_methods: int
    documented_symbols: int
    fully_type_hinted_functions: int
    import_count: int
    local_dependency_count: int
    missing_import_count: int
    max_cyclomatic_complexity: int


@dataclass(frozen=True)
class FileAnalysisResult:
    """Complete diagnostic result for one Python file."""

    file_path: str
    relative_path: str
    file_hash: str
    size_bytes: int
    modified_time: str
    syntax_valid: bool
    metrics: FileMetrics
    issues: tuple[DiagnosticIssue, ...]
    imports: tuple[ImportRecord, ...]
    import_edges: tuple[ImportEdge, ...]
    functions: tuple[FunctionDiagnostic, ...]
    classes: tuple[ClassDiagnostic, ...]
    code_map: JsonObject


@dataclass(frozen=True)
class DependencyGraphResult:
    """Project dependency graph with missing imports, cycles, and Mermaid output."""

    nodes: tuple[str, ...]
    edges: tuple[ImportEdge, ...]
    missing_imports: tuple[ImportEdge, ...]
    cycles: tuple[tuple[str, ...], ...]
    mermaid: str


@dataclass(frozen=True)
class StateDelta:
    """File-state delta compared to the previous recorded run."""

    new_files: tuple[str, ...]
    modified_files: tuple[str, ...]
    deleted_files: tuple[str, ...]
    unchanged_files: tuple[str, ...]


@dataclass(frozen=True)
class SummaryCounts:
    """Aggregate counters used by reports and exit gates."""

    files_scanned: int
    total_issues: int
    critical_issues: int
    serious_issues: int
    minor_issues: int
    info_issues: int
    syntax_error_files: int
    missing_imports: int
    dependency_cycles: int
    suspicious_short_classes: int
    suspicious_short_functions: int
    production_score: int


@dataclass(frozen=True)
class ProjectAnalysisResult:
    """Full project analysis result with summary, file results, and dependency graph."""

    run_id: str
    project_root: str
    started_at: str
    finished_at: str
    config_hash: str
    summary: SummaryCounts
    files: tuple[FileAnalysisResult, ...]
    issues: tuple[DiagnosticIssue, ...]
    dependency_graph: DependencyGraphResult
    state_delta: StateDelta


@dataclass(frozen=True)
class ReportPaths:
    """Report artifact paths for the current run."""

    markdown_path: Path
    json_path: Path
    state_markdown_path: Path
    state_json_path: Path
    latest_markdown_path: Path
    latest_json_path: Path


@dataclass(frozen=True)
class RunRecord:
    """Stored run metadata loaded from the local state database."""

    run_id: str
    project_root: str
    completed_at: str
    status: str
    files_scanned: int
    total_issues: int
    critical_issues: int
    serious_issues: int
    report_md: str
    report_json: str


DEFAULT_CONFIG_DATA: JsonObject = {
    "schema_version": "3.0",
    "min_function_lines": 5,
    "min_class_lines": 6,
    "min_docstring_length": 18,
    "max_cyclomatic_complexity": 12,
    "max_report_evidence_lines": 5,
    "include_patterns": ["*.py"],
    "ignore_patterns": ["__pycache__/*", "*.pyc", ".git/*", ".hg/*", ".mypy_cache/*", ".pytest_cache/*", ".ruff_cache/*", ".tox/*", ".venv/*", "venv/*", "env/*", "node_modules/*", ".python_doctor/*", "build/*", "dist/*"],
    "ignore_functions": ["__repr__", "__str__"],
    "ignore_classes": [],
    "check_private_functions": False,
    "check_nested_functions": True,
    "require_module_docstring": True,
    "require_class_docstring": True,
    "require_function_docstring": True,
    "require_parameter_hints": True,
    "require_return_hints": True,
    "detect_unused_imports": True,
    "detect_test_gaps": True,
    "detect_security_risks": True,
    "detect_silent_failures": True,
    "detect_dependency_cycles": True,
    "state_dir": ".python_doctor",
    "reports_dir": "reports",
    "report_basename": "production_doctor_report",
    "severity_exit_level": "serious",
    "max_workers": 4,
    "markdown_include_css": True,
    "severity_levels": {
        "analysis_read_errors": "critical",
        "syntax_errors": "critical",
        "tokenization_errors": "critical",
        "missing_imports": "serious",
        "dependency_cycles": "serious",
        "stubs": "serious",
        "placeholder_returns": "serious",
        "incomplete_methods": "serious",
        "suspicious_short_classes": "serious",
        "silent_failures": "serious",
        "broad_exceptions": "serious",
        "security_risks": "serious",
        "test_gaps": "serious",
        "todos": "minor",
        "missing_docstrings": "minor",
        "suspicious_short_functions": "minor",
        "type_hint_gaps": "minor",
        "complexity": "minor",
        "unused_imports": "minor",
        "duplicate_definitions": "minor",
    },
}

TODO_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\bTODO\b", "Action Required"),
    (r"\bFIXME\b", "Critical Fix Needed"),
    (r"\bHACK\b", "Technical Debt"),
    (r"\bXXX\b", "Urgent Review"),
    (r"\bTEMP\b", "Temporary Code"),
    (r"\bWIP\b", "Work In Progress"),
)

PLACEHOLDER_CONSTANTS: tuple[object, ...] = (None, False, True, 0, -1, "")
SECURITY_CALLS: frozenset[str] = frozenset({"eval", "exec", "compile", "pickle.load", "pickle.loads", "subprocess.call", "subprocess.run", "subprocess.Popen", "os.system", "os.popen", "yaml.load", "marshal.load", "marshal.loads"})

SOMNUS_MARKDOWN_STYLE = """<style>
.t{background:#141414;border-radius:10px;box-shadow:0 12px 40px rgba(0,0,0,.45),0 0 0 1px #2a2a2a;margin:22px 0;font-family:Menlo,Monaco,Cascadia Code,Courier New,monospace;overflow:hidden}
.t-hdr{background:#252525;padding:11px 16px;display:flex;align-items:center;border-bottom:1px solid #1e1e1e}
.t-btn{width:13px;height:13px;border-radius:50%;margin-right:8px;flex-shrink:0}.t-btn.r{background:#ff5f57}.t-btn.y{background:#febc2e}.t-btn.g{background:#28c840}
.t-title{color:#888;font-size:12.5px;margin-left:10px;letter-spacing:.4px}.t-tag{margin-left:auto;background:#1e1e1e;border:1px solid #333;color:#777;font-size:10px;padding:2px 8px;border-radius:3px;letter-spacing:1px;text-transform:uppercase}
.t-body{padding:18px 20px;font-size:13px;line-height:1.65;color:#d4d4d4;overflow-x:auto}.prompt{color:#28c840}.dim{color:#777}.info{color:#8ec5fc}.warn{color:#febc2e}.err{color:#ff5f57}.accent{color:#c9a0dc}
</style>"""


def utc_now() -> dt.datetime:
    """Return a timezone-aware UTC timestamp."""
    return dt.datetime.now(UTC)


def utc_now_text() -> str:
    """Return a compact UTC timestamp for run identifiers."""
    return utc_now().strftime(RUN_ID_FORMAT)


def isoformat_utc(value: dt.datetime) -> str:
    """Render a datetime with stable UTC suffix."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def stable_hash_text(text: str) -> str:
    """Return SHA-256 hex digest for text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def stable_hash_file(path: Path) -> str:
    """Return SHA-256 hex digest for a file."""
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as error:
        raise FileReadError("Unable to hash source file.", {"path": str(path), "os_error": str(error)}) from error
    return digest.hexdigest()


def to_json_value(value: object) -> JsonValue:
    """Convert dataclasses, paths, enums, mappings, sequences, and scalars to JSON-safe values."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Enum):
        return str(value.value)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dt.datetime):
        return isoformat_utc(value)
    if is_dataclass(value):
        return {field.name: to_json_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Mapping):
        return {str(key): to_json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [to_json_value(item) for item in value]
    return str(value)


def dumps_json(value: object, *, indent: int = 2) -> str:
    """Serialize a supported object to deterministic JSON."""
    return json.dumps(to_json_value(value), indent=indent, sort_keys=True)


def safe_relpath(path: Path, root: Path) -> str:
    """Return a POSIX relative path when possible."""
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def table_escape(value: object) -> str:
    """Escape a value for markdown tables."""
    return str(value).replace("\n", " ").replace("|", "\\|").strip()


def strip_yaml_comment(line: str) -> str:
    """Remove YAML comments outside quoted strings."""
    in_single = False
    in_double = False
    escaped = False
    for index, char in enumerate(line):
        if escaped:
            escaped = False
            continue
        if char == "\\" and in_double:
            escaped = True
            continue
        if char == "'" and not in_double:
            in_single = not in_single
            continue
        if char == '"' and not in_single:
            in_double = not in_double
            continue
        if char == "#" and not in_single and not in_double:
            return line[:index]
    return line


def parse_yaml_scalar(value: str, line_number: int) -> JsonValue:
    """Parse one scalar or inline sequence from the native YAML subset."""
    text = value.strip()
    if text == "":
        return ""
    lowered = text.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "none", "~"}:
        return None
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        try:
            return ast.literal_eval(text)
        except (SyntaxError, ValueError) as error:
            raise ConfigurationError("Invalid quoted YAML scalar.", {"line": line_number, "value": text, "error": str(error)}) from error
    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].strip()
        if not inner:
            return []
        return [parse_yaml_scalar(part.strip(), line_number) for part in inner.split(",") if part.strip()]
    if re.fullmatch(r"[-+]?\d+", text):
        return int(text)
    if re.fullmatch(r"[-+]?\d+\.\d+", text):
        return float(text)
    return text


class MinimalYamlParser:
    """Strict native parser for the YAML subset used by doctor configs."""

    def __init__(self, path: Path) -> None:
        """Initialize parser for a config path."""
        self.path = path

    def parse(self) -> JsonObject:
        """Parse YAML file and return a JSON-safe mapping."""
        try:
            raw_lines = self.path.read_text(encoding="utf-8").splitlines()
        except OSError as error:
            raise ConfigurationError("Unable to read configuration file.", {"path": str(self.path), "os_error": str(error)}) from error
        lines = self._prepare_lines(raw_lines)
        if not lines:
            return {}
        parsed, next_index = self._parse_block(lines, 0, lines[0].indent)
        if next_index != len(lines):
            extra = lines[next_index]
            raise ConfigurationError("Unexpected YAML content after document.", {"path": str(self.path), "line": extra.number, "content": extra.content})
        if not isinstance(parsed, dict):
            raise ConfigurationError("Configuration root must be a mapping.", {"path": str(self.path), "root_type": type(parsed).__name__})
        return parsed

    def _prepare_lines(self, raw_lines: Sequence[str]) -> list[YamlLine]:
        """Prepare non-empty YAML lines."""
        prepared: list[YamlLine] = []
        for number, raw_line in enumerate(raw_lines, start=1):
            text = strip_yaml_comment(raw_line).rstrip()
            if not text.strip():
                continue
            indent = len(text) - len(text.lstrip(" "))
            prepared.append(YamlLine(number, indent, text.strip()))
        return prepared

    def _parse_block(self, lines: Sequence[YamlLine], index: int, indent: int) -> tuple[JsonValue, int]:
        """Parse a mapping or sequence block."""
        container: JsonObject | list[JsonValue] | None = None
        while index < len(lines):
            line = lines[index]
            if line.indent < indent:
                break
            if line.indent > indent:
                raise ConfigurationError("Unexpected indentation.", {"path": str(self.path), "line": line.number, "indent": line.indent, "expected": indent})
            if line.content.startswith("- "):
                if container is None:
                    container = []
                if not isinstance(container, list):
                    raise ConfigurationError("Cannot mix sequence items with mapping keys.", {"path": str(self.path), "line": line.number})
                item_text = line.content[2:].strip()
                if item_text == "":
                    value, index = self._parse_child(lines, index, indent, line.number)
                else:
                    value = parse_yaml_scalar(item_text, line.number)
                    index += 1
                container.append(value)
                continue
            if container is None:
                container = {}
            if not isinstance(container, dict):
                raise ConfigurationError("Cannot mix mapping keys with sequence items.", {"path": str(self.path), "line": line.number})
            key, separator, raw_value = line.content.partition(":")
            if separator != ":" or not key.strip():
                raise ConfigurationError("Expected key followed by colon.", {"path": str(self.path), "line": line.number, "content": line.content})
            if raw_value.strip() == "":
                value, index = self._parse_child(lines, index, indent, line.number)
            else:
                value = parse_yaml_scalar(raw_value.strip(), line.number)
                index += 1
            container[key.strip()] = value
        return (container if container is not None else {}), index

    def _parse_child(self, lines: Sequence[YamlLine], index: int, indent: int, line_number: int) -> tuple[JsonValue, int]:
        """Parse an indented child block."""
        next_index = index + 1
        if next_index >= len(lines) or lines[next_index].indent <= indent:
            raise ConfigurationError("Expected an indented child block.", {"path": str(self.path), "line": line_number})
        return self._parse_block(lines, next_index, lines[next_index].indent)


def deep_merge(base: JsonObject, override: JsonObject) -> JsonObject:
    """Merge config mappings recursively without mutating inputs."""
    merged: JsonObject = {key: to_json_value(value) for key, value in base.items()}
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def require_bool(data: Mapping[str, JsonValue], key: str) -> bool:
    """Read a required boolean config value."""
    value = data.get(key)
    if not isinstance(value, bool):
        raise ConfigurationError("Configuration value must be boolean.", {"key": key, "value": str(value)})
    return value


def require_int(data: Mapping[str, JsonValue], key: str, minimum: int) -> int:
    """Read a required integer config value with lower bound."""
    value = data.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise ConfigurationError("Configuration value must be an integer above minimum.", {"key": key, "value": str(value), "minimum": minimum})
    return value


def require_str(data: Mapping[str, JsonValue], key: str) -> str:
    """Read a required non-empty string config value."""
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigurationError("Configuration value must be a non-empty string.", {"key": key, "value": str(value)})
    return value.strip()


def require_str_tuple(data: Mapping[str, JsonValue], key: str) -> tuple[str, ...]:
    """Read a required list of strings config value."""
    value = data.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise ConfigurationError("Configuration value must be a list of non-empty strings.", {"key": key})
    return tuple(str(item).strip() for item in value)


def parse_severities(raw: JsonValue) -> Mapping[str, Severity]:
    """Parse severity mapping from raw config."""
    if not isinstance(raw, dict):
        raise ConfigurationError("severity_levels must be a mapping.", {"value": str(raw)})
    parsed: dict[str, Severity] = {}
    allowed = {severity.value for severity in Severity}
    for category, severity_value in raw.items():
        if not isinstance(category, str) or not isinstance(severity_value, str) or severity_value not in allowed:
            raise ConfigurationError("Invalid severity mapping entry.", {"category": str(category), "severity": str(severity_value), "allowed": sorted(allowed)})
        parsed[category] = Severity(severity_value)
    return parsed


class ConfigManager:
    """Loads, validates, and exposes YAML-first configuration."""

    def __init__(self, config_path: Path | None) -> None:
        """Load configuration from YAML, JSON, or defaults."""
        self.config_path = config_path
        self.raw_config = self._load_raw(config_path)
        self.config = self._validate(self.raw_config)
        self.config_hash = stable_hash_text(dumps_json(self.raw_config))

    def severity(self, category: str) -> Severity:
        """Return configured severity for a category."""
        return self.config.severity_levels.get(category, Severity.MINOR)

    def _load_raw(self, config_path: Path | None) -> JsonObject:
        """Load raw merged configuration."""
        if config_path is None:
            return deep_merge(DEFAULT_CONFIG_DATA, {})
        if not config_path.exists():
            raise ConfigurationError("Configuration file does not exist.", {"path": str(config_path)})
        if config_path.suffix.lower() == ".json":
            try:
                loaded = json.loads(config_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as error:
                raise ConfigurationError("JSON configuration is malformed.", {"path": str(config_path), "line": error.lineno, "column": error.colno, "message": error.msg}) from error
            except OSError as error:
                raise ConfigurationError("Unable to read JSON configuration.", {"path": str(config_path), "os_error": str(error)}) from error
            if not isinstance(loaded, dict):
                raise ConfigurationError("JSON configuration root must be an object.", {"path": str(config_path)})
            return deep_merge(DEFAULT_CONFIG_DATA, loaded)
        if config_path.suffix.lower() in {".yaml", ".yml"}:
            return deep_merge(DEFAULT_CONFIG_DATA, MinimalYamlParser(config_path).parse())
        raise ConfigurationError("Configuration path must end with .yaml, .yml, or .json.", {"path": str(config_path)})

    def _validate(self, data: JsonObject) -> DoctorConfig:
        """Validate raw mapping into DoctorConfig."""
        gate = require_str(data, "severity_exit_level")
        if gate not in {"critical", "serious", "minor", "info", "none"}:
            raise ConfigurationError("Invalid severity_exit_level.", {"value": gate})
        return DoctorConfig(
            schema_version=require_str(data, "schema_version"),
            min_function_lines=require_int(data, "min_function_lines", 1),
            min_class_lines=require_int(data, "min_class_lines", 1),
            min_docstring_length=require_int(data, "min_docstring_length", 1),
            max_cyclomatic_complexity=require_int(data, "max_cyclomatic_complexity", 1),
            max_report_evidence_lines=require_int(data, "max_report_evidence_lines", 1),
            include_patterns=require_str_tuple(data, "include_patterns"),
            ignore_patterns=require_str_tuple(data, "ignore_patterns"),
            ignore_functions=require_str_tuple(data, "ignore_functions"),
            ignore_classes=require_str_tuple(data, "ignore_classes"),
            check_private_functions=require_bool(data, "check_private_functions"),
            check_nested_functions=require_bool(data, "check_nested_functions"),
            require_module_docstring=require_bool(data, "require_module_docstring"),
            require_class_docstring=require_bool(data, "require_class_docstring"),
            require_function_docstring=require_bool(data, "require_function_docstring"),
            require_parameter_hints=require_bool(data, "require_parameter_hints"),
            require_return_hints=require_bool(data, "require_return_hints"),
            detect_unused_imports=require_bool(data, "detect_unused_imports"),
            detect_test_gaps=require_bool(data, "detect_test_gaps"),
            detect_security_risks=require_bool(data, "detect_security_risks"),
            detect_silent_failures=require_bool(data, "detect_silent_failures"),
            detect_dependency_cycles=require_bool(data, "detect_dependency_cycles"),
            state_dir=require_str(data, "state_dir"),
            reports_dir=require_str(data, "reports_dir"),
            report_basename=require_str(data, "report_basename"),
            severity_exit_level=gate,
            max_workers=require_int(data, "max_workers", 1),
            markdown_include_css=require_bool(data, "markdown_include_css"),
            severity_levels=parse_severities(data.get("severity_levels")),
        )

    @staticmethod
    def default_yaml() -> str:
        """Return the default YAML configuration text."""
        return """schema_version: "3.0"
min_function_lines: 5
min_class_lines: 6
min_docstring_length: 18
max_cyclomatic_complexity: 12
max_report_evidence_lines: 5
include_patterns:
  - "*.py"
ignore_patterns:
  - "__pycache__/*"
  - "*.pyc"
  - ".git/*"
  - ".hg/*"
  - ".mypy_cache/*"
  - ".pytest_cache/*"
  - ".ruff_cache/*"
  - ".tox/*"
  - ".venv/*"
  - "venv/*"
  - "env/*"
  - "node_modules/*"
  - ".python_doctor/*"
  - "build/*"
  - "dist/*"
ignore_functions:
  - "__repr__"
  - "__str__"
ignore_classes: []
check_private_functions: false
check_nested_functions: true
require_module_docstring: true
require_class_docstring: true
require_function_docstring: true
require_parameter_hints: true
require_return_hints: true
detect_unused_imports: true
detect_test_gaps: true
detect_security_risks: true
detect_silent_failures: true
detect_dependency_cycles: true
state_dir: ".python_doctor"
reports_dir: "reports"
report_basename: "production_doctor_report"
severity_exit_level: "serious"
max_workers: 4
markdown_include_css: true
severity_levels:
  analysis_read_errors: "critical"
  syntax_errors: "critical"
  tokenization_errors: "critical"
  missing_imports: "serious"
  dependency_cycles: "serious"
  stubs: "serious"
  placeholder_returns: "serious"
  incomplete_methods: "serious"
  suspicious_short_classes: "serious"
  silent_failures: "serious"
  broad_exceptions: "serious"
  security_risks: "serious"
  test_gaps: "serious"
  todos: "minor"
  missing_docstrings: "minor"
  suspicious_short_functions: "minor"
  type_hint_gaps: "minor"
  complexity: "minor"
  unused_imports: "minor"
  duplicate_definitions: "minor"
"""


class ProjectFileIndex:
    """Indexes Python files and importable module names for a project."""

    def __init__(self, project_root: Path, config: DoctorConfig) -> None:
        """Initialize project index from a root and config."""
        self.project_root = project_root.resolve()
        self.config = config
        self.python_files = self._discover()
        self.module_to_file = self._modules(self.python_files)
        self.file_to_module = {path: module for module, path in self.module_to_file.items()}

    def should_ignore(self, path: Path) -> bool:
        """Return true when path matches ignore configuration."""
        rel = safe_relpath(path, self.project_root)
        parts = set(rel.split("/"))
        for pattern in self.config.ignore_patterns:
            normalized = pattern.replace("\\", "/")
            if fnmatch.fnmatch(rel, normalized) or fnmatch.fnmatch(path.name, normalized):
                return True
            if normalized.endswith("/*") and normalized[:-2] in parts:
                return True
        return False

    def should_include(self, path: Path) -> bool:
        """Return true when path matches include configuration."""
        rel = safe_relpath(path, self.project_root)
        return any(fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(path.name, pattern) for pattern in self.config.include_patterns)

    def module_for_file(self, path: Path) -> str:
        """Return best importable module name for a file."""
        resolved = path.resolve()
        known = self.file_to_module.get(resolved)
        if known:
            return known
        rel = resolved.relative_to(self.project_root)
        return ".".join(rel.parent.parts) if rel.name == "__init__.py" else ".".join(rel.with_suffix("").parts)

    def resolve_local_module(self, module_name: str) -> Path | None:
        """Resolve an importable module name to a local file."""
        return self.module_to_file.get(module_name)

    def _discover(self) -> tuple[Path, ...]:
        """Discover Python files under project root."""
        if not self.project_root.exists():
            raise AnalysisExecutionError("Project root does not exist.", {"project_root": str(self.project_root)})
        if not self.project_root.is_dir():
            raise AnalysisExecutionError("Project root must be a directory.", {"project_root": str(self.project_root)})
        found: list[Path] = []
        for root, dirs, files in os.walk(self.project_root):
            root_path = Path(root)
            dirs[:] = [directory for directory in dirs if not self.should_ignore(root_path / directory)]
            for name in files:
                path = root_path / name
                if self.should_ignore(path) or not self.should_include(path):
                    continue
                found.append(path.resolve())
        return tuple(sorted(found, key=lambda item: safe_relpath(item, self.project_root)))

    def _modules(self, python_files: Sequence[Path]) -> dict[str, Path]:
        """Build module-name to file-path mapping."""
        modules: dict[str, Path] = {}
        for path in python_files:
            rel = path.relative_to(self.project_root)
            parts = rel.parent.parts if rel.name == "__init__.py" else rel.with_suffix("").parts
            if parts:
                modules[".".join(parts)] = path
        return modules


class ImportResolver:
    """Resolves import records as local, standard library, third-party, or missing."""

    def __init__(self, index: ProjectFileIndex) -> None:
        """Initialize resolver with project index."""
        self.index = index
        self.stdlib = set(getattr(sys, "stdlib_module_names", frozenset())) | set(sys.builtin_module_names)

    def resolve(self, source_path: Path, record: ImportRecord) -> ImportEdge:
        """Resolve one import record into an ImportEdge."""
        module_name = self._absolute_module(source_path, record)
        if module_name == "":
            return ImportEdge(safe_relpath(source_path, self.index.project_root), record.module, record.line_number, "unresolved_relative", "relative import could not be converted to an absolute module", "", 0.2, record.raw)
        local = self._resolve_local(module_name, record)
        if local:
            return ImportEdge(safe_relpath(source_path, self.index.project_root), module_name, record.line_number, "local", "resolved", safe_relpath(local, self.index.project_root), 1.0, record.raw)
        top = module_name.split(".")[0]
        if top in self.stdlib:
            return ImportEdge(safe_relpath(source_path, self.index.project_root), module_name, record.line_number, "standard_library", "resolved", "", 0.95, record.raw)
        if self._third_party_exists(top):
            return ImportEdge(safe_relpath(source_path, self.index.project_root), module_name, record.line_number, "third_party", "resolved", "", 0.85, record.raw)
        return ImportEdge(safe_relpath(source_path, self.index.project_root), module_name, record.line_number, "missing", "not found in project index, standard library, or active environment", "", 0.9, record.raw)

    def _absolute_module(self, source_path: Path, record: ImportRecord) -> str:
        """Convert relative import records to absolute module names."""
        if record.level == 0:
            return record.module
        source_module = self.index.module_for_file(source_path)
        package_parts = source_module.split(".")
        if source_path.name != "__init__.py" and package_parts:
            package_parts = package_parts[:-1]
        ascend = record.level - 1
        if ascend > len(package_parts):
            return ""
        module_parts = [part for part in record.module.split(".") if part]
        return ".".join(package_parts[: len(package_parts) - ascend] + module_parts)

    def _resolve_local(self, module_name: str, record: ImportRecord) -> Path | None:
        """Resolve exact module or from-import child module locally."""
        exact = self.index.resolve_local_module(module_name)
        if exact:
            return exact
        if record.kind == "from_import":
            for imported in record.imported_names:
                target = self.index.resolve_local_module(f"{module_name}.{imported}" if module_name else imported)
                if target:
                    return target
        parts = module_name.split(".")
        while len(parts) > 1:
            parts.pop()
            target = self.index.resolve_local_module(".".join(parts))
            if target:
                return target
        return None

    def _third_party_exists(self, top_level: str) -> bool:
        """Return true when an import exists in active environment."""
        try:
            return importlib.util.find_spec(top_level) is not None
        except (ImportError, ModuleNotFoundError, ValueError, AttributeError):
            return False


class SourceReader:
    """Reads Python source with declared encoding support."""

    def read(self, path: Path) -> str:
        """Read Python source text."""
        try:
            with tokenize.open(path) as handle:
                return handle.read()
        except (OSError, SyntaxError, UnicodeDecodeError) as error:
            raise FileReadError("Unable to read or decode source file.", {"path": str(path), "error_type": type(error).__name__, "error": str(error)}) from error


class DiagnosticIssueFactory:
    """Creates normalized issues with bounded source evidence."""

    def __init__(self, config_manager: ConfigManager, relative_path: str, lines: Sequence[str]) -> None:
        """Initialize factory for a file."""
        self.config_manager = config_manager
        self.relative_path = relative_path
        self.lines = lines

    def create(self, category: str, line: int, column: int, symbol: str, message: str, remediation: str, details: JsonObject | None = None) -> DiagnosticIssue:
        """Create a normalized diagnostic issue."""
        return DiagnosticIssue(category, self.config_manager.severity(category), self.relative_path, line, column, symbol, message, self._evidence(line), remediation, details or {})

    def _evidence(self, line: int) -> str:
        """Extract bounded evidence around line."""
        if line <= 0 or not self.lines:
            return ""
        radius = max(0, self.config_manager.config.max_report_evidence_lines // 2)
        start = max(1, line - radius)
        end = min(len(self.lines), line + radius)
        return "\n".join(f"{'>' if number == line else ' '} {number}: {self.lines[number - 1]}" for number in range(start, end + 1))


class ImportCollector(ast.NodeVisitor):
    """Collects static and literal dynamic import records."""

    def __init__(self) -> None:
        """Initialize import collection."""
        self.records: list[ImportRecord] = []

    def visit_Import(self, node: ast.Import) -> None:
        """Collect import statement records."""
        for alias in node.names:
            bound = alias.asname or alias.name.split(".")[0]
            self.records.append(ImportRecord(alias.name, (), (bound,), node.lineno, node.col_offset, 0, "import", ast.unparse(node)))

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Collect from-import statement records."""
        names = tuple(alias.name for alias in node.names if alias.name != "*")
        bound = tuple(alias.asname or alias.name for alias in node.names if alias.name != "*")
        self.records.append(ImportRecord(node.module or "", names, bound, node.lineno, node.col_offset, node.level, "from_import", ast.unparse(node)))

    def visit_Call(self, node: ast.Call) -> None:
        """Collect literal dynamic import calls."""
        call_name = dotted_name(node.func)
        if call_name in {"__import__", "importlib.import_module"} and node.args:
            first = node.args[0]
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                self.records.append(ImportRecord(first.value, (), (), node.lineno, node.col_offset, 0, "dynamic_import", ast.unparse(node)))
        self.generic_visit(node)


class LoadedNameCollector(ast.NodeVisitor):
    """Collects loaded names while skipping import binding sites."""

    def __init__(self) -> None:
        """Initialize loaded-name collection."""
        self.loaded: set[str] = set()

    def visit_Import(self, node: ast.Import) -> None:
        """Skip import binding site."""
        return

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Skip from-import binding site."""
        return

    def visit_Name(self, node: ast.Name) -> None:
        """Collect loaded name."""
        if isinstance(node.ctx, ast.Load):
            self.loaded.add(node.id)


class CodeQualityVisitor(ast.NodeVisitor):
    """Performs AST quality, completeness, typing, and safety analysis."""

    def __init__(self, config_manager: ConfigManager, issue_factory: DiagnosticIssueFactory) -> None:
        """Initialize AST visitor for one file."""
        self.config_manager = config_manager
        self.config = config_manager.config
        self.issue_factory = issue_factory
        self.issues: list[DiagnosticIssue] = []
        self.functions: list[FunctionDiagnostic] = []
        self.classes: list[ClassDiagnostic] = []
        self.scope_stack: list[str] = []
        self.definition_stack: list[MutableMapping[str, list[ast.AST]]] = [defaultdict(list)]
        self.abstract_methods: dict[str, set[str]] = {}
        self.concrete_methods: dict[str, set[str]] = {}
        self.class_bases: dict[str, tuple[str, ...]] = {}

    def analyze(self, tree: ast.AST) -> tuple[tuple[DiagnosticIssue, ...], tuple[FunctionDiagnostic, ...], tuple[ClassDiagnostic, ...]]:
        """Analyze tree and return issues, functions, and classes."""
        self.visit(tree)
        self._check_duplicates()
        self._check_abstracts()
        return tuple(dedupe_issues(self.issues)), tuple(self.functions), tuple(self.classes)

    def visit_Module(self, node: ast.Module) -> None:
        """Analyze module-level docs and definitions."""
        if self.config.require_module_docstring and not meaningful_doc(node, self.config.min_docstring_length):
            self.issues.append(self.issue_factory.create("missing_docstrings", 1, 0, "<module>", "Module is missing a meaningful docstring.", "Add purpose, provenance, and operational boundaries to the module docstring.", {"entity_type": "module"}))
        self._record_definitions(node.body)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Analyze class definitions."""
        qualname = self._qualname(node.name)
        self.definition_stack[-1][node.name].append(node)
        self.scope_stack.append(node.name)
        self.definition_stack.append(defaultdict(list))
        bases = tuple(ast.unparse(base) for base in node.bases)
        decorators = tuple(ast.unparse(item) for item in node.decorator_list)
        info = ClassDiagnostic(
            qualname=qualname,
            line_number=node.lineno,
            end_line_number=node.end_lineno or node.lineno,
            executable_line_count=executable_line_count(node.body),
            method_count=sum(isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) for item in node.body),
            public_method_count=sum(isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and not item.name.startswith("_") for item in node.body),
            bases=bases,
            decorators=decorators,
            has_docstring=meaningful_doc(node, self.config.min_docstring_length),
            is_dataclass=any(name.endswith("dataclass") or name == "dataclass" for name in decorators),
            is_exception=any(base.endswith("Error") or base.endswith("Exception") for base in bases) or node.name.endswith("Error"),
            is_enum=any(base.endswith("Enum") for base in bases),
        )
        self.classes.append(info)
        self.class_bases[qualname] = bases
        self.abstract_methods[qualname] = self._abstract_methods(node)
        self.concrete_methods[qualname] = {item.name for item in node.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))}
        self._analyze_class(node, info)
        self._record_definitions(node.body)
        self.generic_visit(node)
        self._check_duplicates()
        self.definition_stack.pop()
        self.scope_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Analyze synchronous functions."""
        self._visit_function(node, "function")

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Analyze asynchronous functions."""
        self._visit_function(node, "async_function")

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        """Analyze exception handlers."""
        if node.type is None:
            self.issues.append(self.issue_factory.create("broad_exceptions", node.lineno, node.col_offset, self._current_symbol(), "Bare except handler catches every exception class.", "Catch domain-specific exception types and log structured context.", {"handler": "bare except"}))
        elif dotted_name(node.type) in {"Exception", "BaseException"}:
            name = dotted_name(node.type)
            self.issues.append(self.issue_factory.create("broad_exceptions", node.lineno, node.col_offset, self._current_symbol(), f"Broad exception handler catches {name}.", "Catch specific domain exceptions or convert known library exceptions at the boundary.", {"handler": name}))
        if self.config.detect_silent_failures and handler_is_silent(node):
            self.issues.append(self.issue_factory.create("silent_failures", node.lineno, node.col_offset, self._current_symbol(), "Exception handler can suppress failure without actionable diagnostics.", "Log structured context, raise a domain-specific error, or return a structured failure result.", {"handler_body_length": len(node.body)}))
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Analyze high-risk calls."""
        name = dotted_name(node.func)
        if self.config.detect_security_risks and name in SECURITY_CALLS:
            self.issues.append(self.issue_factory.create("security_risks", node.lineno, node.col_offset, self._current_symbol(), f"High-risk call detected: {name}.", "Replace dynamic execution or shell invocation with typed APIs and constrained inputs.", {"call": name}))
        self.generic_visit(node)

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef, kind: str) -> None:
        """Analyze one function-like node."""
        if self._inside_function() and not self.config.check_nested_functions:
            return
        if node.name in self.config.ignore_functions:
            return
        if not self.config.check_private_functions and is_private_function(node.name):
            self.generic_visit(node)
            return
        qualname = self._qualname(node.name)
        self.definition_stack[-1][node.name].append(node)
        self.scope_stack.append(node.name)
        self.definition_stack.append(defaultdict(list))
        body = body_without_docstring(node.body)
        info = FunctionDiagnostic(
            qualname=qualname,
            kind=kind,
            line_number=node.lineno,
            end_line_number=node.end_lineno or node.lineno,
            executable_line_count=executable_line_count(node.body),
            statement_count=len(body),
            cyclomatic_complexity=cyclomatic_complexity(node),
            return_count=sum(isinstance(item, ast.Return) for item in ast.walk(node)),
            argument_count=function_argument_count(node),
            missing_type_hints=missing_type_hints(node, self.config),
            has_docstring=meaningful_doc(node, self.config.min_docstring_length),
            decorators=tuple(ast.unparse(item) for item in node.decorator_list),
        )
        self.functions.append(info)
        self._analyze_function(node, info, body)
        self._record_definitions(body)
        self.generic_visit(node)
        self._check_duplicates()
        self.definition_stack.pop()
        self.scope_stack.pop()

    def _analyze_class(self, node: ast.ClassDef, info: ClassDiagnostic) -> None:
        """Emit class diagnostics."""
        if node.name in self.config.ignore_classes:
            return
        if self.config.require_class_docstring and not info.has_docstring:
            self.issues.append(self.issue_factory.create("missing_docstrings", node.lineno, node.col_offset, info.qualname, f"Class {info.qualname} is missing a meaningful docstring.", "Add purpose, origin, and operational contract to the class docstring.", {"entity_type": "class"}))
        body = body_without_docstring(node.body)
        if body_is_stub(body):
            self.issues.append(self.issue_factory.create("stubs", node.lineno, node.col_offset, info.qualname, f"Class {info.qualname} has a stub body.", "Replace the class body with real state, behavior, or an explicit dataclass/enum contract.", {"entity_type": "class"}))
        if self._short_class(info, body):
            self.issues.append(self.issue_factory.create("suspicious_short_classes", node.lineno, node.col_offset, info.qualname, f"Class {info.qualname} is suspiciously short.", "Verify the class has real responsibility, merge it into its owner, or expand the contract with production behavior.", {"line_count": info.executable_line_count, "method_count": info.method_count, "public_method_count": info.public_method_count}))

    def _analyze_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef, info: FunctionDiagnostic, body: Sequence[ast.stmt]) -> None:
        """Emit function diagnostics."""
        if self.config.require_function_docstring and not info.has_docstring:
            self.issues.append(self.issue_factory.create("missing_docstrings", node.lineno, node.col_offset, info.qualname, f"Function {info.qualname} is missing a meaningful docstring.", "Add Args and Returns blocks for non-trivial signatures and state side effects for private methods.", {"entity_type": "function"}))
        if info.missing_type_hints:
            self.issues.append(self.issue_factory.create("type_hint_gaps", node.lineno, node.col_offset, info.qualname, f"Function {info.qualname} has incomplete type hints.", "Add explicit parameter and return type hints.", {"missing_hints": list(info.missing_type_hints)}))
        if body_is_stub(body):
            self.issues.append(self.issue_factory.create("stubs", node.lineno, node.col_offset, info.qualname, f"Function {info.qualname} has a stub implementation.", "Replace pass, ellipsis, or NotImplementedError with a real diagnostic path or domain exception.", {"entity_type": "function"}))
        placeholder = placeholder_return_kind(body)
        if placeholder:
            self.issues.append(self.issue_factory.create("placeholder_returns", node.lineno, node.col_offset, info.qualname, f"Function {info.qualname} returns a placeholder value as its only result.", "Return a structured diagnostic result or raise a domain-specific exception with context.", {"return_kind": placeholder}))
        if info.executable_line_count < self.config.min_function_lines:
            self.issues.append(self.issue_factory.create("suspicious_short_functions", node.lineno, node.col_offset, info.qualname, f"Function {info.qualname} is suspiciously short.", "Confirm this is a real adapter or expand it until the control path is auditable.", {"line_count": info.executable_line_count, "minimum": self.config.min_function_lines}))
        if info.cyclomatic_complexity > self.config.max_cyclomatic_complexity:
            self.issues.append(self.issue_factory.create("complexity", node.lineno, node.col_offset, info.qualname, f"Function {info.qualname} has high cyclomatic complexity.", "Split validation, collection, and rendering paths into named units with typed result objects.", {"complexity": info.cyclomatic_complexity, "maximum": self.config.max_cyclomatic_complexity}))

    def _short_class(self, info: ClassDiagnostic, body: Sequence[ast.stmt]) -> bool:
        """Return true when a class deserves suspicious-short review."""
        if info.is_dataclass or info.is_enum or info.is_exception:
            return False
        if not body:
            return True
        if info.executable_line_count >= self.config.min_class_lines:
            return False
        if info.method_count == 0:
            return True
        return info.public_method_count == 0 and not any(isinstance(item, (ast.Assign, ast.AnnAssign)) for item in body)

    def _record_definitions(self, statements: Sequence[ast.stmt]) -> None:
        """Record function and class definitions in current scope."""
        for statement in statements:
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                self.definition_stack[-1][statement.name].append(statement)

    def _check_duplicates(self) -> None:
        """Emit duplicate definition issues for current scope."""
        scope = self.definition_stack[-1]
        for name, nodes in scope.items():
            lines = sorted({getattr(node, "lineno", 0) for node in nodes})
            if len(lines) > 1:
                self.issues.append(self.issue_factory.create("duplicate_definitions", lines[1], 0, self._qualname(name), f"Name {name} is defined multiple times in the same scope.", "Rename or remove duplicate definitions so runtime binding is unambiguous.", {"definition_lines": lines}))
        scope.clear()

    def _check_abstracts(self) -> None:
        """Check same-file subclasses against same-file abstract contracts."""
        for class_name, bases in self.class_bases.items():
            inherited: set[str] = set()
            for base in bases:
                short = base.split(".")[-1]
                for abstract_class, methods in self.abstract_methods.items():
                    if abstract_class.endswith(f".{short}") or abstract_class == short:
                        inherited.update(methods)
            missing = sorted(inherited - self.concrete_methods.get(class_name, set()))
            if missing:
                found = next((item for item in self.classes if item.qualname == class_name), None)
                self.issues.append(self.issue_factory.create("incomplete_methods", found.line_number if found else 1, 0, class_name, f"Class {class_name} does not implement inherited abstract methods.", "Implement each abstract method or keep the subclass abstract with explicit decorators.", {"missing_methods": missing}))

    def _abstract_methods(self, node: ast.ClassDef) -> set[str]:
        """Return abstract method names in a class."""
        methods: set[str] = set()
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                decorators = {dotted_name(decorator) for decorator in item.decorator_list}
                if decorators & {"abstractmethod", "abc.abstractmethod", "abstractproperty", "abc.abstractproperty"}:
                    methods.add(item.name)
        return methods

    def _qualname(self, name: str) -> str:
        """Build qualified name from current scope."""
        return ".".join(self.scope_stack + [name]) if self.scope_stack else name

    def _current_symbol(self) -> str:
        """Return current scope symbol."""
        return ".".join(self.scope_stack) if self.scope_stack else "<module>"

    def _inside_function(self) -> bool:
        """Return whether current scope is inside a function."""
        return bool(self.scope_stack and self.functions and self.functions[-1].qualname == ".".join(self.scope_stack))


def dedupe_issues(issues: Iterable[DiagnosticIssue]) -> list[DiagnosticIssue]:
    """Remove duplicate issues while preserving diagnostic order."""
    seen: set[str] = set()
    unique: list[DiagnosticIssue] = []
    for issue in issues:
        key = issue.identity()
        if key in seen:
            continue
        seen.add(key)
        unique.append(issue)
    return sorted(unique, key=lambda item: (item.file_path, item.line_number, item.severity.value, item.category, item.symbol))


def meaningful_doc(node: ast.AST, min_length: int) -> bool:
    """Return true when node has a docstring at configured minimum length."""
    return len((ast.get_docstring(node) or "").strip()) >= min_length


def body_without_docstring(body: Sequence[ast.stmt]) -> tuple[ast.stmt, ...]:
    """Return body with leading docstring removed."""
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
        return tuple(body[1:])
    return tuple(body)


def executable_line_count(body: Sequence[ast.stmt]) -> int:
    """Count unique executable lines in a body."""
    lines: set[int] = set()
    for statement in body_without_docstring(body):
        start = getattr(statement, "lineno", 0)
        end = getattr(statement, "end_lineno", start) or start
        if start > 0:
            lines.update(range(start, end + 1))
    return len(lines)


def function_argument_count(node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    """Count all explicit function arguments."""
    return len(node.args.posonlyargs) + len(node.args.args) + len(node.args.kwonlyargs) + (1 if node.args.vararg else 0) + (1 if node.args.kwarg else 0)


def is_private_function(name: str) -> bool:
    """Return true for private but non-dunder function names."""
    return name.startswith("_") and not (name.startswith("__") and name.endswith("__"))


def missing_type_hints(node: ast.FunctionDef | ast.AsyncFunctionDef, config: DoctorConfig) -> tuple[str, ...]:
    """Return missing type-hint labels for a function."""
    missing: list[str] = []
    if config.require_return_hints and node.returns is None:
        missing.append("return")
    if config.require_parameter_hints:
        for argument in [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]:
            if argument.arg not in {"self", "cls"} and argument.annotation is None:
                missing.append(f"param:{argument.arg}")
        if node.args.vararg and node.args.vararg.annotation is None:
            missing.append(f"vararg:{node.args.vararg.arg}")
        if node.args.kwarg and node.args.kwarg.annotation is None:
            missing.append(f"kwarg:{node.args.kwarg.arg}")
    return tuple(missing)


def cyclomatic_complexity(node: ast.AST) -> int:
    """Calculate conservative cyclomatic complexity."""
    score = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, ast.ExceptHandler, ast.IfExp, ast.Match)):
            score += 1
        elif isinstance(child, ast.BoolOp):
            score += max(1, len(child.values) - 1)
        elif isinstance(child, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            score += sum(1 + len(generator.ifs) for generator in child.generators)
    return score


def body_is_stub(body: Sequence[ast.stmt]) -> bool:
    """Return true when body is a direct stub."""
    if len(body) != 1:
        return False
    statement = body[0]
    if isinstance(statement, ast.Pass):
        return True
    if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant) and statement.value.value is Ellipsis:
        return True
    if isinstance(statement, ast.Raise) and statement.exc is not None:
        exc = statement.exc
        return (isinstance(exc, ast.Call) and dotted_name(exc.func) == "NotImplementedError") or (isinstance(exc, ast.Name) and exc.id == "NotImplementedError")
    return False


def placeholder_return_kind(body: Sequence[ast.stmt]) -> str:
    """Return placeholder kind when a body only returns a trivial value."""
    if len(body) != 1 or not isinstance(body[0], ast.Return):
        return ""
    value = body[0].value
    if value is None:
        return "implicit None"
    if isinstance(value, ast.Constant) and value.value in PLACEHOLDER_CONSTANTS:
        return repr(value.value)
    if isinstance(value, ast.List) and not value.elts:
        return "empty list"
    if isinstance(value, ast.Dict) and not value.keys:
        return "empty dict"
    if isinstance(value, ast.Tuple) and not value.elts:
        return "empty tuple"
    if isinstance(value, ast.Set) and not value.elts:
        return "empty set"
    return ""


def handler_is_silent(node: ast.ExceptHandler) -> bool:
    """Return true when an exception handler suppresses diagnostics."""
    body = body_without_docstring(node.body)
    if not body:
        return True
    if len(body) == 1:
        statement = body[0]
        if isinstance(statement, ast.Pass):
            return True
        if isinstance(statement, ast.Return) and placeholder_return_kind((statement,)):
            return True
        if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call) and dotted_name(statement.value.func) in {"print", "logging.debug", "logging.info"}:
            return True
    module = ast.Module(body=list(body), type_ignores=[])
    has_raise = any(isinstance(statement, ast.Raise) for statement in ast.walk(module))
    has_log = any(isinstance(statement, ast.Call) and dotted_name(statement.func) in {"logging.error", "logging.exception", "logger.error", "logger.exception"} for statement in ast.walk(module))
    return not (has_raise or has_log)


def dotted_name(node: ast.AST | None) -> str:
    """Return dotted name for Name and Attribute nodes."""
    if node is None:
        return ""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = dotted_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    if isinstance(node, ast.Call):
        return dotted_name(node.func)
    try:
        return ast.unparse(node)
    except (ValueError, TypeError, AttributeError):
        return ""


class FileAnalyzer:
    """Analyzes one Python file for syntax, AST, imports, and diagnostics."""

    def __init__(self, path: Path, index: ProjectFileIndex, config_manager: ConfigManager) -> None:
        """Initialize analyzer for one file."""
        self.path = path.resolve()
        self.index = index
        self.config_manager = config_manager
        self.config = config_manager.config
        self.relative_path = safe_relpath(self.path, self.index.project_root)
        self.reader = SourceReader()
        self.resolver = ImportResolver(index)

    def analyze(self) -> FileAnalysisResult:
        """Run file analysis and return a complete result."""
        try:
            source = self.reader.read(self.path)
        except FileReadError as error:
            return self._read_error(error)
        lines = source.splitlines()
        factory = DiagnosticIssueFactory(self.config_manager, self.relative_path, lines)
        issues = self._token_diagnostics(source, factory)
        try:
            tree = ast.parse(source, filename=str(self.path))
        except SyntaxError as error:
            issues.append(factory.create("syntax_errors", error.lineno or 1, error.offset or 0, "<syntax>", f"SyntaxError: {error.msg}", "Fix Python syntax before AST, import, and dependency checks can run for this file.", {"text": (error.text or "").strip(), "offset": error.offset or 0}))
            return self._assemble(source, lines, False, issues, (), (), (), (), {})
        except ValueError as error:
            issues.append(factory.create("syntax_errors", 1, 0, "<syntax>", f"AST parser rejected source: {error}", "Inspect source encoding and parser-compatible Python syntax.", {"error_type": type(error).__name__}))
            return self._assemble(source, lines, False, issues, (), (), (), (), {})
        collector = ImportCollector()
        collector.visit(tree)
        imports = tuple(collector.records)
        edges = tuple(self.resolver.resolve(self.path, record) for record in imports)
        issues.extend(self._import_diagnostics(edges, tree, imports, factory))
        visitor = CodeQualityVisitor(self.config_manager, factory)
        ast_issues, functions, classes = visitor.analyze(tree)
        issues.extend(ast_issues)
        code_map = {"module": self.index.module_for_file(self.path), "docstring_present": bool(ast.get_docstring(tree)), "imports": [to_json_value(record) for record in imports], "classes": [to_json_value(item) for item in classes], "functions": [to_json_value(item) for item in functions]}
        return self._assemble(source, lines, True, issues, imports, edges, functions, classes, code_map)

    def _token_diagnostics(self, source: str, factory: DiagnosticIssueFactory) -> list[DiagnosticIssue]:
        """Run token-level diagnostics including technical debt comments."""
        issues: list[DiagnosticIssue] = []
        try:
            tokens = tokenize.generate_tokens(io.StringIO(source).readline)
            for token in tokens:
                if token.type != tokenize.COMMENT:
                    continue
                comment = token.string.lstrip("#").strip()
                for pattern, marker_type in TODO_PATTERNS:
                    if re.search(pattern, comment, re.IGNORECASE):
                        issues.append(factory.create("todos", token.start[0], token.start[1], "<comment>", f"Technical debt marker found: {marker_type}.", "Resolve or move the debt into a tracked issue with owner and deadline.", {"marker_type": marker_type, "comment": comment}))
                        break
        except tokenize.TokenError as error:
            line = error.args[1][0] if len(error.args) > 1 and isinstance(error.args[1], tuple) else 1
            issues.append(factory.create("tokenization_errors", int(line), 0, "<tokenize>", f"Tokenization failed: {error.args[0]}", "Fix unterminated strings, brackets, or encoding directives before deeper diagnostics run.", {"error": str(error)}))
        return issues

    def _import_diagnostics(self, edges: Sequence[ImportEdge], tree: ast.AST, imports: Sequence[ImportRecord], factory: DiagnosticIssueFactory) -> list[DiagnosticIssue]:
        """Run import resolution and unused import diagnostics."""
        issues: list[DiagnosticIssue] = []
        for edge in edges:
            if edge.classification in {"missing", "unresolved_relative"}:
                issues.append(factory.create("missing_imports", edge.line_number, 0, edge.imported_module, f"Import could not be resolved: {edge.imported_module}.", "Add the dependency, correct the import path, or move the module under the project root.", {"status": edge.status, "raw": edge.raw, "classification": edge.classification}))
        if self.config.detect_unused_imports:
            loaded = LoadedNameCollector()
            loaded.visit(tree)
            for record in imports:
                if record.kind == "dynamic_import":
                    continue
                for bound in record.bound_names:
                    if bound != "*" and not bound.startswith("_") and bound not in loaded.loaded:
                        issues.append(factory.create("unused_imports", record.line_number, record.column_offset, bound, f"Imported name appears unused: {bound}.", "Remove the import or use it in a visible code path.", {"raw": record.raw, "module": record.module}))
        return issues

    def _read_error(self, error: FileReadError) -> FileAnalysisResult:
        """Build result for unreadable file."""
        issue = DiagnosticIssue("analysis_read_errors", self.config_manager.severity("analysis_read_errors"), self.relative_path, 1, 0, "<read>", error.message, "", error.remediation, error.context)
        return FileAnalysisResult(str(self.path), self.relative_path, "", 0, "unavailable", False, FileMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0), (issue,), (), (), (), (), {})

    def _assemble(self, source: str, lines: Sequence[str], syntax_valid: bool, issues: Sequence[DiagnosticIssue], imports: Sequence[ImportRecord], edges: Sequence[ImportEdge], functions: Sequence[FunctionDiagnostic], classes: Sequence[ClassDiagnostic], code_map: JsonObject) -> FileAnalysisResult:
        """Assemble result from analyzed parts."""
        try:
            stat = self.path.stat()
        except OSError as error:
            raise FileReadError("Unable to stat source file after analysis.", {"path": str(self.path), "os_error": str(error)}) from error
        metrics = self._metrics(lines, imports, edges, functions, classes)
        return FileAnalysisResult(str(self.path), self.relative_path, stable_hash_file(self.path), stat.st_size, isoformat_utc(dt.datetime.fromtimestamp(stat.st_mtime, UTC)), syntax_valid, metrics, tuple(dedupe_issues(issues)), tuple(imports), tuple(edges), tuple(functions), tuple(classes), code_map)

    def _metrics(self, lines: Sequence[str], imports: Sequence[ImportRecord], edges: Sequence[ImportEdge], functions: Sequence[FunctionDiagnostic], classes: Sequence[ClassDiagnostic]) -> FileMetrics:
        """Calculate file metrics."""
        blanks = sum(1 for line in lines if not line.strip())
        comments = sum(1 for line in lines if line.lstrip().startswith("#"))
        return FileMetrics(
            total_lines=len(lines),
            code_lines=max(0, len(lines) - blanks - comments),
            comment_lines=comments,
            blank_lines=blanks,
            total_classes=len(classes),
            total_functions=len(functions),
            total_methods=sum(1 for function in functions if "." in function.qualname),
            documented_symbols=sum(1 for function in functions if function.has_docstring) + sum(1 for item in classes if item.has_docstring),
            fully_type_hinted_functions=sum(1 for function in functions if not function.missing_type_hints),
            import_count=len(imports),
            local_dependency_count=sum(1 for edge in edges if edge.classification == "local"),
            missing_import_count=sum(1 for edge in edges if edge.classification in {"missing", "unresolved_relative"}),
            max_cyclomatic_complexity=max((function.cyclomatic_complexity for function in functions), default=0),
        )


class DependencyGraphBuilder:
    """Builds local import graph, cycles, and Mermaid diagram."""

    def __init__(self, config: DoctorConfig) -> None:
        """Initialize graph builder."""
        self.config = config

    def build(self, files: Sequence[FileAnalysisResult]) -> DependencyGraphResult:
        """Build dependency graph result."""
        nodes = tuple(sorted(file.relative_path for file in files))
        edges = tuple(edge for file in files for edge in file.import_edges)
        local_edges = tuple(edge for edge in edges if edge.classification == "local" and edge.target_file)
        missing = tuple(edge for edge in edges if edge.classification in {"missing", "unresolved_relative"})
        cycles = self._cycles(nodes, local_edges) if self.config.detect_dependency_cycles else ()
        return DependencyGraphResult(nodes, edges, missing, cycles, self._mermaid(nodes, local_edges, missing, cycles))

    def _cycles(self, nodes: Sequence[str], edges: Sequence[ImportEdge]) -> tuple[tuple[str, ...], ...]:
        """Detect directed cycles."""
        graph: dict[str, set[str]] = {node: set() for node in nodes}
        for edge in edges:
            graph.setdefault(edge.source_file, set()).add(edge.target_file)
        cycles: set[tuple[str, ...]] = set()
        for node in sorted(graph):
            self._visit(node, node, graph, [], set(), cycles)
            if len(cycles) >= 100:
                break
        return tuple(sorted(cycles))

    def _visit(self, start: str, current: str, graph: Mapping[str, set[str]], path: list[str], visiting: set[str], cycles: set[tuple[str, ...]]) -> None:
        """Traverse graph for cycles."""
        path.append(current)
        visiting.add(current)
        for neighbor in sorted(graph.get(current, set())):
            if neighbor == start and len(path) > 1:
                cycles.add(canonical_cycle(tuple(path)))
            elif neighbor not in visiting and len(path) < 30:
                self._visit(start, neighbor, graph, path, visiting, cycles)
        visiting.discard(current)
        path.pop()

    def _mermaid(self, nodes: Sequence[str], edges: Sequence[ImportEdge], missing: Sequence[ImportEdge], cycles: Sequence[tuple[str, ...]]) -> str:
        """Render Mermaid dependency graph."""
        lines = ["graph TD"]
        if not nodes:
            return "graph TD\n    empty[No Python files discovered]"
        ids = {node: f"N{index}" for index, node in enumerate(nodes, 1)}
        for node, identifier in ids.items():
            lines.append(f'    {identifier}["{mermaid_escape(node)}"]')
        for edge in edges:
            source = ids.get(edge.source_file)
            target = ids.get(edge.target_file)
            if source and target:
                lines.append(f"    {source} --> {target}")
        for index, edge in enumerate(missing, 1):
            source = ids.get(edge.source_file)
            if source:
                missing_id = f"M{index}"
                lines.append(f'    {missing_id}(["missing: {mermaid_escape(edge.imported_module)}"])')
                lines.append(f"    {source} -.-> {missing_id}")
        for index, cycle in enumerate(cycles, 1):
            lines.append(f'    C{index}{{"cycle: {mermaid_escape(" -> ".join(cycle))}"}}')
        return "\n".join(lines)


def canonical_cycle(cycle: Sequence[str]) -> tuple[str, ...]:
    """Return canonical representation of a cycle."""
    if not cycle:
        return ()
    items = list(cycle)
    return min(tuple(items[index:] + items[:index]) for index in range(len(items)))


def mermaid_escape(value: str) -> str:
    """Escape Mermaid label text."""
    return value.replace('"', "'").replace("[", "(").replace("]", ")")


class ProjectScanner:
    """Coordinates project scan, graph generation, state delta, and summary."""

    def __init__(self, project_root: Path, config_manager: ConfigManager) -> None:
        """Initialize project scanner."""
        self.project_root = project_root.resolve()
        self.config_manager = config_manager
        self.config = config_manager.config
        self.index = ProjectFileIndex(self.project_root, self.config)

    def scan(self, previous_index: Mapping[str, str]) -> ProjectAnalysisResult:
        """Run a complete project scan."""
        started = utc_now()
        run_id = utc_now_text()
        files = self._analyze_files()
        graph = DependencyGraphBuilder(self.config).build(files)
        files = self._attach_cycles(files, graph)
        issues = tuple(issue for file in files for issue in file.issues)
        summary = self._summary(files, issues, graph)
        return ProjectAnalysisResult(run_id, str(self.project_root), isoformat_utc(started), isoformat_utc(utc_now()), self.config_manager.config_hash, summary, tuple(files), tuple(sorted(issues, key=lambda item: (item.file_path, item.line_number, item.category))), graph, self._state_delta(files, previous_index))

    def _analyze_files(self) -> tuple[FileAnalysisResult, ...]:
        """Analyze all discovered Python files."""
        if not self.index.python_files:
            return ()
        max_workers = min(self.config.max_workers, max(1, len(self.index.python_files)))
        if max_workers == 1:
            return tuple(FileAnalyzer(path, self.index, self.config_manager).analyze() for path in self.index.python_files)
        results: list[FileAnalysisResult] = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_path = {executor.submit(FileAnalyzer(path, self.index, self.config_manager).analyze): path for path in self.index.python_files}
            for future in concurrent.futures.as_completed(future_to_path):
                path = future_to_path[future]
                try:
                    results.append(future.result())
                except (DoctorError, OSError, RuntimeError, TypeError, ValueError, LookupError) as error:
                    results.append(self._execution_error(path, error))
        return tuple(sorted(results, key=lambda item: item.relative_path))

    def _execution_error(self, path: Path, error: BaseException) -> FileAnalysisResult:
        """Build explicit result for worker failure."""
        rel = safe_relpath(path, self.project_root)
        issue = DiagnosticIssue("analysis_read_errors", self.config_manager.severity("analysis_read_errors"), rel, 1, 0, "<analysis>", f"Analyzer execution failed: {type(error).__name__}: {error}", "", "Inspect the analyzer log and source file, then rerun with verbose logging.", {"error_type": type(error).__name__, "path": str(path)})
        return FileAnalysisResult(str(path), rel, "", 0, "unavailable", False, FileMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0), (issue,), (), (), (), (), {})

    def _attach_cycles(self, files: Sequence[FileAnalysisResult], graph: DependencyGraphResult) -> tuple[FileAnalysisResult, ...]:
        """Attach dependency cycle issues to first file in each cycle."""
        if not graph.cycles:
            return tuple(files)
        issue_map: dict[str, list[DiagnosticIssue]] = defaultdict(list)
        for cycle in graph.cycles:
            first = cycle[0]
            issue_map[first].append(DiagnosticIssue("dependency_cycles", self.config_manager.severity("dependency_cycles"), first, 1, 0, first, "Local dependency cycle detected.", "", "Break the cycle by moving shared contracts into a lower-level module or inverting the import boundary.", {"cycle": list(cycle)}))
        updated: list[FileAnalysisResult] = []
        for file in files:
            extra = issue_map.get(file.relative_path, [])
            if not extra:
                updated.append(file)
                continue
            updated.append(FileAnalysisResult(file.file_path, file.relative_path, file.file_hash, file.size_bytes, file.modified_time, file.syntax_valid, file.metrics, tuple(dedupe_issues([*file.issues, *extra])), file.imports, file.import_edges, file.functions, file.classes, file.code_map))
        return tuple(sorted(updated, key=lambda item: item.relative_path))

    def _state_delta(self, files: Sequence[FileAnalysisResult], previous: Mapping[str, str]) -> StateDelta:
        """Compare current hashes with previous run."""
        current = {file.relative_path: file.file_hash for file in files if file.file_hash}
        previous_paths = set(previous)
        current_paths = set(current)
        return StateDelta(tuple(sorted(current_paths - previous_paths)), tuple(sorted(path for path in current_paths & previous_paths if current[path] != previous[path])), tuple(sorted(previous_paths - current_paths)), tuple(sorted(path for path in current_paths & previous_paths if current[path] == previous[path])))

    def _summary(self, files: Sequence[FileAnalysisResult], issues: Sequence[DiagnosticIssue], graph: DependencyGraphResult) -> SummaryCounts:
        """Build aggregate summary counts."""
        severities = Counter(issue.severity for issue in issues)
        categories = Counter(issue.category for issue in issues)
        critical = severities[Severity.CRITICAL]
        serious = severities[Severity.SERIOUS]
        minor = severities[Severity.MINOR]
        info = severities[Severity.INFO]
        score = max(0, 100 - critical * 20 - serious * 8 - minor * 2 - info)
        return SummaryCounts(len(files), len(issues), critical, serious, minor, info, sum(1 for file in files if not file.syntax_valid), len(graph.missing_imports), len(graph.cycles), categories["suspicious_short_classes"], categories["suspicious_short_functions"], score)


class MarkdownReportWriter:
    """Renders project diagnostics into Somnus-styled markdown."""

    def __init__(self, config: DoctorConfig) -> None:
        """Initialize markdown writer."""
        self.config = config

    def render(self, result: ProjectAnalysisResult) -> str:
        """Render full markdown report."""
        lines: list[str] = []
        if self.config.markdown_include_css:
            lines.extend([SOMNUS_MARKDOWN_STYLE, ""])
        lines.extend(self._header(result))
        lines.extend(self._terminal(result))
        lines.extend(self._summary(result))
        lines.extend(self._state(result.state_delta))
        lines.extend(self._dependency(result))
        lines.extend(self._short_sections(result))
        lines.extend(self._issue_index(result))
        lines.extend(self._file_sections(result))
        lines.extend(self._action_plan(result))
        lines.extend(["---", "", "Generated by Python Production Doctor. This tool diagnoses; it does not modify source code."])
        return "\n".join(lines).rstrip() + "\n"

    def _header(self, result: ProjectAnalysisResult) -> list[str]:
        """Render report header."""
        return ["# Python Production Doctor Report", "", f"Run ID: `{result.run_id}`", f"Project: `{result.project_root}`", f"Started: `{result.started_at}`", f"Finished: `{result.finished_at}`", f"Config hash: `{result.config_hash}`", ""]

    def _terminal(self, result: ProjectAnalysisResult) -> list[str]:
        """Render terminal-style executive block."""
        summary = result.summary
        return [
            '<div class="t">',
            '  <div class="t-hdr"><div class="t-btn r"></div><div class="t-btn y"></div><div class="t-btn g"></div><span class="t-title">python-production-doctor</span><span class="t-tag">DIAGNOSIS</span></div>',
            '  <div class="t-body">',
            f'    <div><span class="prompt">doctor@somnus:~$</span> scan {html.escape(result.project_root)}</div>',
            f'    <div class="out info">files scanned: {summary.files_scanned}</div>',
            f'    <div class="out err">critical: {summary.critical_issues}</div>',
            f'    <div class="out warn">serious: {summary.serious_issues}</div>',
            f'    <div class="out dim">minor: {summary.minor_issues} | info: {summary.info_issues}</div>',
            f'    <div class="out accent">production score: {summary.production_score}/100</div>',
            "  </div>",
            "</div>",
            "",
        ]

    def _summary(self, result: ProjectAnalysisResult) -> list[str]:
        """Render summary and categories."""
        counts = Counter(issue.category for issue in result.issues)
        lines = ["## Summary", "", "| Metric | Value |", "|---|---:|"]
        for label, value in [
            ("Files scanned", result.summary.files_scanned),
            ("Total issues", result.summary.total_issues),
            ("Critical issues", result.summary.critical_issues),
            ("Serious issues", result.summary.serious_issues),
            ("Minor issues", result.summary.minor_issues),
            ("Syntax-error files", result.summary.syntax_error_files),
            ("Missing imports", result.summary.missing_imports),
            ("Dependency cycles", result.summary.dependency_cycles),
            ("Suspiciously short classes", result.summary.suspicious_short_classes),
            ("Suspiciously short functions", result.summary.suspicious_short_functions),
        ]:
            lines.append(f"| {label} | {value} |")
        lines.extend(["", "## Issue Categories", "", "| Category | Count |", "|---|---:|"])
        if counts:
            for category, count in sorted(counts.items()):
                lines.append(f"| `{table_escape(category)}` | {count} |")
        else:
            lines.append("| none | 0 |")
        lines.append("")
        return lines

    def _state(self, delta: StateDelta) -> list[str]:
        """Render local state delta."""
        return ["## Local State Delta", "", "| Delta | Count | Files |", "|---|---:|---|", f"| New | {len(delta.new_files)} | {table_escape(', '.join(delta.new_files[:12]) or 'none')} |", f"| Modified | {len(delta.modified_files)} | {table_escape(', '.join(delta.modified_files[:12]) or 'none')} |", f"| Deleted | {len(delta.deleted_files)} | {table_escape(', '.join(delta.deleted_files[:12]) or 'none')} |", f"| Unchanged | {len(delta.unchanged_files)} | {table_escape(', '.join(delta.unchanged_files[:12]) or 'none')} |", ""]

    def _dependency(self, result: ProjectAnalysisResult) -> list[str]:
        """Render dependency graph section."""
        lines = ["## Dependency Map", "", "```mermaid", result.dependency_graph.mermaid, "```", "", "### Missing or Unresolved Imports", "", "| Source | Line | Import | Status |", "|---|---:|---|---|"]
        if result.dependency_graph.missing_imports:
            for edge in result.dependency_graph.missing_imports:
                lines.append(f"| `{table_escape(edge.source_file)}` | {edge.line_number} | `{table_escape(edge.imported_module)}` | {table_escape(edge.status)} |")
        else:
            lines.append("| none | 0 | none | all imports resolved or classified |")
        lines.extend(["", "### Dependency Cycles", "", "| Cycle |", "|---|"])
        if result.dependency_graph.cycles:
            for cycle in result.dependency_graph.cycles:
                lines.append(f"| `{table_escape(' -> '.join(cycle))}` |")
        else:
            lines.append("| none |")
        lines.append("")
        return lines

    def _short_sections(self, result: ProjectAnalysisResult) -> list[str]:
        """Render mandatory short class and function sections."""
        short_classes = [issue for issue in result.issues if issue.category == "suspicious_short_classes"]
        short_functions = [issue for issue in result.issues if issue.category == "suspicious_short_functions"]
        lines = ["## Suspiciously Short Classes", ""]
        lines.extend([f"- `{issue.file_path}:{issue.line_number}` `{issue.symbol}`: {issue.message}" for issue in short_classes] or ["No suspiciously short classes detected."])
        lines.extend(["", "## Suspiciously Short Functions", ""])
        lines.extend([f"- `{issue.file_path}:{issue.line_number}` `{issue.symbol}`: {issue.message}" for issue in short_functions] or ["No suspiciously short functions detected."])
        lines.append("")
        return lines

    def _issue_index(self, result: ProjectAnalysisResult) -> list[str]:
        """Render every issue in a sortable table."""
        lines = ["## Full Issue Index", "", "| Severity | Category | File | Line | Symbol | Message |", "|---|---|---|---:|---|---|"]
        if not result.issues:
            lines.append("| info | none | none | 0 | none | No issues detected. |")
        for issue in result.issues:
            lines.append(f"| {issue.severity.value} | `{table_escape(issue.category)}` | `{table_escape(issue.file_path)}` | {issue.line_number} | `{table_escape(issue.symbol)}` | {table_escape(issue.message)} |")
        lines.append("")
        return lines

    def _file_sections(self, result: ProjectAnalysisResult) -> list[str]:
        """Render per-file evidence and details."""
        lines = ["## File Diagnostics", ""]
        for file in result.files:
            lines.extend([f"### `{file.relative_path}`", "", "| Metric | Value |", "|---|---:|", f"| Lines | {file.metrics.total_lines} |", f"| Code lines | {file.metrics.code_lines} |", f"| Classes | {file.metrics.total_classes} |", f"| Functions | {file.metrics.total_functions} |", f"| Imports | {file.metrics.import_count} |", f"| Local dependencies | {file.metrics.local_dependency_count} |", f"| Missing imports | {file.metrics.missing_import_count} |", f"| Max complexity | {file.metrics.max_cyclomatic_complexity} |", ""])
            if not file.issues:
                lines.extend(["No issues detected in this file.", ""])
                continue
            for index, issue in enumerate(file.issues, 1):
                lines.extend([f"#### Issue {index}: `{issue.category}` at line {issue.line_number}", "", f"Severity: `{issue.severity.value}`", f"Symbol: `{issue.symbol}`", f"Message: {issue.message}", f"Remediation: {issue.remediation}", "", "Evidence:", "```text", issue.evidence or "No source evidence available.", "```", "Details:", "```json", dumps_json(issue.details), "```", ""])
        return lines

    def _action_plan(self, result: ProjectAnalysisResult) -> list[str]:
        """Render action plan from severity gates."""
        lines = ["## Recommended Action Plan", ""]
        if result.summary.critical_issues:
            lines.extend(["### Critical", "- Fix syntax, tokenization, and read errors first. AST and import checks depend on parseable source.", ""])
        if result.summary.serious_issues:
            lines.extend(["### Serious", "- Resolve stubs, placeholder returns, missing imports, suspicious classes, broad handlers, silent failures, test gaps, and dependency cycles before release.", ""])
        if result.summary.minor_issues:
            lines.extend(["### Minor", "- Complete docstrings, type hints, unused import cleanup, duplicate definitions, and complexity reductions.", ""])
        if result.summary.total_issues == 0:
            lines.extend(["No action required by the configured checks.", ""])
        return lines


class StateStore:
    """Persists scan history, report aliases, and file hashes for report rollback."""

    def __init__(self, project_root: Path, config: DoctorConfig) -> None:
        """Initialize state store under project root."""
        self.project_root = project_root.resolve()
        self.config = config
        self.state_root = self.project_root / config.state_dir
        self.db = self.state_root / "state.sqlite3"
        self.reports_root = self.state_root / config.reports_dir

    def initialize(self) -> None:
        """Create state directories and SQLite schema."""
        try:
            self.reports_root.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            raise StateStoreError("Unable to create state report directory.", {"path": str(self.reports_root), "error": str(error)}) from error
        try:
            with sqlite3.connect(self.db) as conn:
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("CREATE TABLE IF NOT EXISTS runs (run_id TEXT PRIMARY KEY, project_root TEXT NOT NULL, config_hash TEXT NOT NULL, started_at TEXT NOT NULL, completed_at TEXT NOT NULL, status TEXT NOT NULL, files_scanned INTEGER NOT NULL, total_issues INTEGER NOT NULL, critical_issues INTEGER NOT NULL, serious_issues INTEGER NOT NULL, minor_issues INTEGER NOT NULL, info_issues INTEGER NOT NULL, report_md TEXT NOT NULL, report_json TEXT NOT NULL, report_hash TEXT NOT NULL)")
                conn.execute("CREATE TABLE IF NOT EXISTS file_snapshots (run_id TEXT NOT NULL, relative_path TEXT NOT NULL, file_hash TEXT NOT NULL, size_bytes INTEGER NOT NULL, modified_time TEXT NOT NULL, PRIMARY KEY (run_id, relative_path), FOREIGN KEY (run_id) REFERENCES runs(run_id))")
                conn.execute("CREATE TABLE IF NOT EXISTS report_aliases (alias TEXT PRIMARY KEY, run_id TEXT NOT NULL, report_md TEXT NOT NULL, report_json TEXT NOT NULL, updated_at TEXT NOT NULL, FOREIGN KEY (run_id) REFERENCES runs(run_id))")
        except sqlite3.Error as error:
            raise StateStoreError("Unable to initialize state database.", {"path": str(self.db), "error": str(error)}) from error

    def previous_file_index(self) -> Mapping[str, str]:
        """Load previous latest file hash index."""
        self.initialize()
        try:
            with sqlite3.connect(self.db) as conn:
                latest = conn.execute("SELECT run_id FROM report_aliases WHERE alias = 'latest'").fetchone()
                if latest is None:
                    return {}
                rows = conn.execute("SELECT relative_path, file_hash FROM file_snapshots WHERE run_id = ?", (latest[0],)).fetchall()
        except sqlite3.Error as error:
            raise StateStoreError("Unable to load previous state index.", {"path": str(self.db), "error": str(error)}) from error
        return {str(path): str(file_hash) for path, file_hash in rows}

    def report_paths(self, run_id: str, output: Path | None, json_output: Path | None) -> ReportPaths:
        """Resolve all report paths for a run."""
        run_dir = self.reports_root / run_id
        state_md = run_dir / f"{self.config.report_basename}.md"
        state_json = run_dir / f"{self.config.report_basename}.json"
        md = output.resolve() if output else self.project_root / f"{self.config.report_basename}.md"
        js = json_output.resolve() if json_output else md.with_suffix(".json")
        return ReportPaths(md, js, state_md, state_json, self.reports_root / "latest.md", self.reports_root / "latest.json")

    def persist(self, result: ProjectAnalysisResult, markdown: str, json_text: str, paths: ReportPaths) -> None:
        """Write artifacts and record the run."""
        self.initialize()
        write_text_atomic(paths.markdown_path, markdown)
        write_text_atomic(paths.json_path, json_text)
        write_text_atomic(paths.state_markdown_path, markdown)
        write_text_atomic(paths.state_json_path, json_text)
        write_text_atomic(paths.latest_markdown_path, markdown)
        write_text_atomic(paths.latest_json_path, json_text)
        try:
            with sqlite3.connect(self.db) as conn:
                conn.execute("INSERT OR REPLACE INTO runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (result.run_id, result.project_root, result.config_hash, result.started_at, result.finished_at, "complete", result.summary.files_scanned, result.summary.total_issues, result.summary.critical_issues, result.summary.serious_issues, result.summary.minor_issues, result.summary.info_issues, str(paths.state_markdown_path), str(paths.state_json_path), stable_hash_text(markdown + json_text)))
                conn.executemany("INSERT OR REPLACE INTO file_snapshots VALUES (?, ?, ?, ?, ?)", [(result.run_id, file.relative_path, file.file_hash, file.size_bytes, file.modified_time) for file in result.files])
                conn.execute("INSERT OR REPLACE INTO report_aliases VALUES ('latest', ?, ?, ?, ?)", (result.run_id, str(paths.state_markdown_path), str(paths.state_json_path), isoformat_utc(utc_now())))
        except sqlite3.Error as error:
            raise StateStoreError("Unable to persist run state.", {"run_id": result.run_id, "error": str(error)}) from error

    def history(self, limit: int) -> tuple[RunRecord, ...]:
        """Return recent run records."""
        self.initialize()
        try:
            with sqlite3.connect(self.db) as conn:
                rows = conn.execute("SELECT run_id, project_root, completed_at, status, files_scanned, total_issues, critical_issues, serious_issues, report_md, report_json FROM runs ORDER BY completed_at DESC LIMIT ?", (limit,)).fetchall()
        except sqlite3.Error as error:
            raise StateStoreError("Unable to read run history.", {"error": str(error)}) from error
        return tuple(RunRecord(str(row[0]), str(row[1]), str(row[2]), str(row[3]), int(row[4]), int(row[5]), int(row[6]), int(row[7]), str(row[8]), str(row[9])) for row in rows)

    def rollback(self, run_id: str) -> RunRecord:
        """Make a previous run the latest report alias."""
        self.initialize()
        try:
            with sqlite3.connect(self.db) as conn:
                row = conn.execute("SELECT run_id, project_root, completed_at, status, files_scanned, total_issues, critical_issues, serious_issues, report_md, report_json FROM runs WHERE run_id = ?", (run_id,)).fetchone()
                if row is None:
                    raise StateStoreError("Run ID does not exist in state history.", {"run_id": run_id})
                record = RunRecord(str(row[0]), str(row[1]), str(row[2]), str(row[3]), int(row[4]), int(row[5]), int(row[6]), int(row[7]), str(row[8]), str(row[9]))
                source_md = Path(record.report_md)
                source_json = Path(record.report_json)
                if not source_md.exists() or not source_json.exists():
                    raise StateStoreError("Cannot roll back because stored report artifacts are missing.", {"run_id": run_id, "report_md": str(source_md), "report_json": str(source_json)})
                copy_file_atomic(source_md, self.reports_root / "latest.md")
                copy_file_atomic(source_json, self.reports_root / "latest.json")
                conn.execute("INSERT OR REPLACE INTO report_aliases VALUES ('latest', ?, ?, ?, ?)", (run_id, str(source_md), str(source_json), isoformat_utc(utc_now())))
        except sqlite3.Error as error:
            raise StateStoreError("Unable to roll back report state.", {"run_id": run_id, "error": str(error)}) from error
        return record


def write_text_atomic(path: Path, text: str) -> None:
    """Write text atomically to path."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_name(f".{path.name}.tmp")
        temp.write_text(text, encoding="utf-8")
        temp.replace(path)
    except OSError as error:
        raise ReportGenerationError("Unable to write artifact.", {"path": str(path), "error": str(error)}) from error


def copy_file_atomic(source: Path, destination: Path) -> None:
    """Copy file atomically."""
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        temp = destination.with_name(f".{destination.name}.tmp")
        shutil.copy2(source, temp)
        temp.replace(destination)
    except OSError as error:
        raise StateStoreError("Unable to copy report artifact during rollback.", {"source": str(source), "destination": str(destination), "error": str(error)}) from error


def render_history(records: Sequence[RunRecord]) -> str:
    """Render run history for CLI output."""
    if not records:
        return "No recorded runs found."
    lines = ["Run history:"]
    for record in records:
        lines.append(f"- {record.run_id} | {record.completed_at} | files={record.files_scanned} | issues={record.total_issues} | critical={record.critical_issues} | serious={record.serious_issues}")
        lines.append(f"  markdown={record.report_md}")
        lines.append(f"  json={record.report_json}")
    return "\n".join(lines)


def exit_code_for_summary(summary: SummaryCounts, gate: str) -> int:
    """Calculate process exit code from severity gate."""
    if gate == "none":
        return 0
    if gate == "critical":
        return 2 if summary.critical_issues else 0
    if gate == "serious":
        return 2 if summary.critical_issues else (1 if summary.serious_issues else 0)
    if gate == "minor":
        return 1 if summary.critical_issues or summary.serious_issues or summary.minor_issues else 0
    if gate == "info":
        return 1 if summary.total_issues else 0
    return 1


def run_scan(args: argparse.Namespace) -> int:
    """Execute scan command and write reports."""
    config_manager = ConfigManager(Path(args.config).resolve() if args.config else None)
    project_root = Path(args.project_root).resolve()
    store = StateStore(project_root, config_manager.config)
    previous = store.previous_file_index() if not args.no_state else {}
    result = ProjectScanner(project_root, config_manager).scan(previous)
    markdown = MarkdownReportWriter(config_manager.config).render(result)
    json_text = dumps_json(result)
    paths = store.report_paths(result.run_id, Path(args.output).resolve() if args.output else None, Path(args.json_output).resolve() if args.json_output else None)
    if args.no_state:
        write_text_atomic(paths.markdown_path, markdown)
        write_text_atomic(paths.json_path, json_text)
    else:
        store.persist(result, markdown, json_text, paths)
    print(f"Scan complete: files={result.summary.files_scanned}, issues={result.summary.total_issues}, critical={result.summary.critical_issues}, serious={result.summary.serious_issues}")
    print(f"Markdown report: {paths.markdown_path}")
    print(f"JSON report: {paths.json_path}")
    if not args.no_state:
        print(f"State latest markdown: {paths.latest_markdown_path}")
        print(f"Run ID: {result.run_id}")
    return exit_code_for_summary(result.summary, config_manager.config.severity_exit_level)


def run_init_config(args: argparse.Namespace) -> int:
    """Write default YAML configuration."""
    output = Path(args.output).resolve()
    if output.exists() and not args.force:
        raise ConfigurationError("Configuration file already exists.", {"path": str(output), "remediation": "Use --force to replace it."})
    write_text_atomic(output, ConfigManager.default_yaml())
    print(f"Wrote default configuration: {output}")
    return 0


def run_history(args: argparse.Namespace) -> int:
    """Print local scan history."""
    config_manager = ConfigManager(Path(args.config).resolve() if args.config else None)
    print(render_history(StateStore(Path(args.project_root).resolve(), config_manager.config).history(args.limit)))
    return 0


def run_rollback(args: argparse.Namespace) -> int:
    """Roll latest report alias back to a previous run."""
    config_manager = ConfigManager(Path(args.config).resolve() if args.config else None)
    record = StateStore(Path(args.project_root).resolve(), config_manager.config).rollback(args.run_id)
    print(f"Rolled latest report state back to run {record.run_id}.")
    print(f"Markdown report: {record.report_md}")
    print(f"JSON report: {record.report_json}")
    return 0


def run_self_check(args: argparse.Namespace) -> int:
    """Run doctor against directory containing this file."""
    module_path = Path(__file__).resolve()
    scan_args = argparse.Namespace(project_root=str(module_path.parent), config=args.config, output=args.output or str(module_path.parent / "self_check_report.md"), json_output=args.json_output, no_state=args.no_state)
    return run_scan(scan_args)


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser."""
    parser = argparse.ArgumentParser(description="Python Production Doctor - production readiness diagnostics")
    sub = parser.add_subparsers(dest="command", required=True)
    scan = sub.add_parser("scan", help="scan a Python project")
    scan.add_argument("project_root", nargs="?", default=".", help="project root directory to scan")
    scan.add_argument("-c", "--config", help="YAML or JSON configuration path")
    scan.add_argument("-o", "--output", help="markdown output path")
    scan.add_argument("--json-output", help="JSON output path")
    scan.add_argument("--no-state", action="store_true", help="write reports without SQLite state tracking")
    scan.add_argument("-v", "--verbose", action="store_true", help="enable debug logging")
    scan.set_defaults(func=run_scan)
    init = sub.add_parser("init-config", help="write default YAML configuration")
    init.add_argument("-o", "--output", default=DEFAULT_CONFIG_NAME, help="configuration output path")
    init.add_argument("--force", action="store_true", help="replace existing configuration")
    init.set_defaults(func=run_init_config)
    history = sub.add_parser("history", help="show scan history")
    history.add_argument("project_root", nargs="?", default=".", help="project root directory")
    history.add_argument("-c", "--config", help="YAML or JSON configuration path")
    history.add_argument("--limit", type=int, default=10, help="maximum records to show")
    history.set_defaults(func=run_history)
    rollback = sub.add_parser("rollback", help="restore a previous report as latest")
    rollback.add_argument("project_root", nargs="?", default=".", help="project root directory")
    rollback.add_argument("--run-id", required=True, help="run identifier to restore")
    rollback.add_argument("-c", "--config", help="YAML or JSON configuration path")
    rollback.set_defaults(func=run_rollback)
    self_check = sub.add_parser("self-check", help="scan the directory containing this doctor")
    self_check.add_argument("-c", "--config", help="YAML or JSON configuration path")
    self_check.add_argument("-o", "--output", help="markdown output path")
    self_check.add_argument("--json-output", help="JSON output path")
    self_check.add_argument("--no-state", action="store_true", help="write reports without SQLite state tracking")
    self_check.set_defaults(func=run_self_check)
    return parser


def normalize_argv(argv: Sequence[str]) -> list[str]:
    """Normalize legacy positional invocation into scan subcommand."""
    if not argv:
        return ["scan", "."]
    first = argv[0]
    if first in ("-h", "--help"):
        return list(argv)
    if first in COMMANDS:
        return list(argv)
    if first.startswith("-"):
        return ["scan", ".", *argv]
    return ["scan", *argv]


def setup_logging(verbose: bool = False) -> None:
    """Configure diagnostic logging."""
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s", handlers=[logging.FileHandler("production_doctor.log", encoding="utf-8")], force=True)


def main(argv: Sequence[str] | None = None) -> int:
    """Run command-line interface."""
    setup_logging("--verbose" in (argv or sys.argv[1:]))
    parser = build_parser()
    args = parser.parse_args(normalize_argv(list(argv) if argv is not None else sys.argv[1:]))
    try:
        return int(args.func(args))
    except DoctorError as error:
        logging.getLogger(LOGGER_NAME).error(error.render())
        print(error.render(), file=sys.stderr)
        return 4
    except (OSError, RuntimeError, TypeError, ValueError, sqlite3.Error) as error:
        logging.getLogger(LOGGER_NAME).critical("Unclassified doctor runtime failure", exc_info=True)
        diagnostic = DoctorError(f"Unclassified runtime failure: {type(error).__name__}: {error}", "Inspect production_doctor.log for the stack trace, then correct the failing path or report the analyzer defect.", {"error_type": type(error).__name__})
        print(diagnostic.render(), file=sys.stderr)
        return 5


if __name__ == "__main__":
    raise SystemExit(main())
