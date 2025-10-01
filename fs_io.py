import json
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import frontmatter
from dotenv import load_dotenv


load_dotenv()


CHAPTERS_ROOT: str = os.getenv("CHAPTERS_ROOT", "chapters")
CHOICES_DIR: str = os.path.join(CHAPTERS_ROOT, "choices")
CANONICAL_DIR: str = os.path.join(CHAPTERS_ROOT, "canonical")
PRUNED_DIR: str = os.path.join(CHAPTERS_ROOT, "pruned")
METADATA_DIR: str = os.getenv("METADATA_ROOT", os.path.join(".agent", "metadata"))


def ensure_directories() -> None:
    """Ensure required directories exist for output and metadata."""
    for path in [
        CHAPTERS_ROOT,
        CHOICES_DIR,
        CANONICAL_DIR,
        PRUNED_DIR,
        METADATA_DIR,
    ]:
        os.makedirs(path, exist_ok=True)


def _zero_pad(index: int) -> str:
    """Convert an integer chapter index to zero-padded string (e.g. 1 -> '0001')."""
    return f"{index:04d}"


def _list_indices_from_files(directory: str, suffix: str = ".md") -> List[int]:
    indices: List[int] = []
    if not os.path.isdir(directory):
        return indices
    for name in os.listdir(directory):
        if not name.endswith(suffix):
            continue
        base, _ = os.path.splitext(name)
        if base.isdigit():
            try:
                indices.append(int(base))
            except ValueError:
                continue
    return sorted(indices)


def get_next_chapter_index() -> int:
    """Compute the next chapter index based on existing canonical chapters."""
    ensure_directories()
    indices = _list_indices_from_files(CANONICAL_DIR)
    if not indices:
        return 1
    return max(indices) + 1


def get_latest_choices_index() -> int:
    """Return the highest chapter index that has generated choices."""
    ensure_directories()
    if not os.path.isdir(CHOICES_DIR):
        return 0
    indices: List[int] = []
    for name in os.listdir(CHOICES_DIR):
        full = os.path.join(CHOICES_DIR, name)
        if os.path.isdir(full) and name.isdigit():
            try:
                indices.append(int(name))
            except ValueError:
                continue
    return max(indices) if indices else 0


def _write_markdown_with_frontmatter(
    path: str,
    metadata: Dict,
    content: str,
) -> None:
    post = frontmatter.Post(content, **metadata)
    # frontmatter.dump writes bytes; open file in binary mode
    with open(path, "wb") as f:
        frontmatter.dump(post, f)


def write_choice_drafts(
    chapter_index: int,
    drafts: List[Dict[str, str]],
) -> List[str]:
    """Write three option drafts to `chapters/choices/<index>/A|B|C.md`.

    Args:
        chapter_index: Target chapter sequence number (1-based).
        drafts: List with fields: id ('A'|'B'|'C'), title, content.

    Returns:
        List of created file paths in order of input.
    """
    ensure_directories()
    index_str = _zero_pad(chapter_index)
    base_dir = os.path.join(CHOICES_DIR, index_str)
    os.makedirs(base_dir, exist_ok=True)

    created_paths: List[str] = []
    for draft in drafts:
        option_id = draft.get("id", "").upper()
        if option_id not in {"A", "B", "C"}:
            continue
        filename = f"{option_id}.md"
        path = os.path.join(base_dir, filename)
        metadata = {
            "title": draft.get("title") or f"Chapter {index_str} - Option {option_id}",
            "chapter_index": chapter_index,
            "option_id": option_id,
            "tags": ["choice"],
        }
        _write_markdown_with_frontmatter(path, metadata, draft.get("content", ""))
        created_paths.append(path)
    return created_paths


def write_canonical_chapter(
    chapter_index: int,
    title: str,
    content: str,
    metadata_yaml: Dict,
) -> str:
    """Write the canonical chapter markdown file.

    Also tags with `canonical` and writes supplied metadata fields to frontmatter.
    """
    ensure_directories()
    index_str = _zero_pad(chapter_index)
    path = os.path.join(CANONICAL_DIR, f"{index_str}.md")
    metadata = {
        **metadata_yaml,
        "title": title,
        "chapter_index": chapter_index,
        "tags": sorted(set(["canonical", *metadata_yaml.get("tags", [])])),
    }
    _write_markdown_with_frontmatter(path, metadata, content)
    return path


def write_pruned_chapter(
    chapter_index: int,
    option_id: str,
    title: str,
    content: str,
    metadata_yaml: Dict,
) -> str:
    """Write a tragic/pruned branch chapter markdown file."""
    ensure_directories()
    index_str = _zero_pad(chapter_index)
    base_dir = os.path.join(PRUNED_DIR, index_str)
    os.makedirs(base_dir, exist_ok=True)
    path = os.path.join(base_dir, f"{option_id.upper()}.md")
    metadata = {
        **metadata_yaml,
        "title": title,
        "chapter_index": chapter_index,
        "option_id": option_id.upper(),
        "tags": sorted(set(["tragic", *metadata_yaml.get("tags", [])])),
    }
    _write_markdown_with_frontmatter(path, metadata, content)
    return path


def write_metadata_json(filename: str, data: Dict) -> str:
    """Write JSON metadata mirror to `METADATA_DIR/filename`.

    Args:
        filename: File name only (e.g. `chapter-0001.json`).
        data: Metadata dict to persist.

    Returns:
        Full path written.
    """
    ensure_directories()
    path = os.path.join(METADATA_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


def read_last_n_metadata(n: int) -> List[Tuple[str, Dict]]:
    """Load the last N metadata JSON files by chapter index.

    Returns list of (filename, dict) sorted ascending by index.
    """
    if not os.path.isdir(METADATA_DIR):
        return []
    files = [
        name for name in os.listdir(METADATA_DIR) if name.endswith(".json")
    ]
    # Extract chapter index for sorting; canonical files are `chapter-0001.json`.
    def key(name: str) -> Tuple[int, int]:
        parts = name.replace(".json", "").split("-")
        idx_part = parts[1] if len(parts) > 1 else "0000"
        try:
            idx = int(idx_part)
        except ValueError:
            idx = 0
        # Canonical before branch variants (A/B) for same index
        variant_weight = 0 if len(parts) == 2 else 1
        return idx, variant_weight

    files_sorted = sorted(files, key=key)
    selected = files_sorted[-n:] if n > 0 else files_sorted
    result: List[Tuple[str, Dict]] = []
    for name in selected:
        full = os.path.join(METADATA_DIR, name)
        try:
            with open(full, "r", encoding="utf-8") as f:
                result.append((name, json.load(f)))
        except Exception:
            continue
    return result


def read_last_n_canonical_metadata(n: int) -> List[Tuple[str, Dict]]:
    """Load the last N canonical metadata JSON files only (exclude branch variants).

    Canonical filenames are `chapter-0001.json` (no trailing option like -A).
    Returns list of (filename, dict) sorted ascending by index.
    """
    if not os.path.isdir(METADATA_DIR):
        return []
    files = [
        name
        for name in os.listdir(METADATA_DIR)
        if name.endswith(".json") and name.count("-") == 1
    ]
    def key(name: str) -> int:
        idx_part = name.replace(".json", "").split("-")[1]
        try:
            return int(idx_part)
        except ValueError:
            return 0
    files_sorted = sorted(files, key=key)
    selected = files_sorted[-n:] if n > 0 else files_sorted
    result: List[Tuple[str, Dict]] = []
    for name in selected:
        full = os.path.join(METADATA_DIR, name)
        try:
            with open(full, "r", encoding="utf-8") as f:
                result.append((name, json.load(f)))
        except Exception:
            continue
    return result


def read_last_n_pruned_metadata(n: int) -> List[Tuple[str, Dict]]:
    """Load metadata for the last N chapter indices that have pruned branches.

    Includes all pruned variants (e.g., -A, -B) for each selected index.
    Returns list of (filename, dict) ordered by chapter index ascending, then variant.
    """
    if not os.path.isdir(METADATA_DIR):
        return []
    files = [
        name for name in os.listdir(METADATA_DIR)
        if name.endswith(".json") and name.count("-") >= 2
    ]

    # Group by chapter index
    index_to_files: Dict[int, List[str]] = {}
    for name in files:
        base = name.replace(".json", "")
        parts = base.split("-")  # ["chapter", "0001", "A"]
        if len(parts) < 3:
            continue
        try:
            idx = int(parts[1])
        except ValueError:
            continue
        index_to_files.setdefault(idx, []).append(name)

    if not index_to_files:
        return []

    indices_sorted = sorted(index_to_files.keys())
    selected_indices = indices_sorted[-n:] if n > 0 else indices_sorted

    result: List[Tuple[str, Dict]] = []
    for idx in selected_indices:
        for name in sorted(index_to_files[idx]):
            full = os.path.join(METADATA_DIR, name)
            try:
                with open(full, "r", encoding="utf-8") as f:
                    result.append((name, json.load(f)))
            except Exception:
                continue
    return result


def list_history() -> Dict[str, List[str]]:
    """Return filesystem paths for canonical, pruned, and choice drafts."""
    ensure_directories()
    result: Dict[str, List[str]] = {
        "canonical": [],
        "pruned": [],
        "choices": [],
    }
    # Canonical
    if os.path.isdir(CANONICAL_DIR):
        result["canonical"] = [
            os.path.join(CANONICAL_DIR, name)
            for name in sorted(os.listdir(CANONICAL_DIR))
            if name.endswith(".md")
        ]
    # Pruned
    if os.path.isdir(PRUNED_DIR):
        for idx_dir in sorted(os.listdir(PRUNED_DIR)):
            full = os.path.join(PRUNED_DIR, idx_dir)
            if not os.path.isdir(full):
                continue
            for name in sorted(os.listdir(full)):
                if name.endswith(".md"):
                    result["pruned"].append(os.path.join(full, name))
    # Choices
    if os.path.isdir(CHOICES_DIR):
        for idx_dir in sorted(os.listdir(CHOICES_DIR)):
            full = os.path.join(CHOICES_DIR, idx_dir)
            if not os.path.isdir(full):
                continue
            for name in sorted(os.listdir(full)):
                if name.endswith(".md"):
                    result["choices"].append(os.path.join(full, name))
    return result


