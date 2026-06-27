"""Deprecated compatibility adapter for legacy DNA compilation.

Maraim no longer uses a DNA Compiler architecture. The active architecture is:

    project tree / archive / repository
        -> DNAExtractorEngine
        -> MDP foundation package
        -> RuntimeObjects / RuntimeGraph

This module is intentionally kept only to avoid breaking old imports that call
`compile_dna`. It does not write to the legacy DB tables and should not be used
for new code.
"""

from pathlib import Path
from typing import Any, Dict, Iterable, List

from maraim.kernel_v2.dna_extractor_engine import DNAExtractorEngine

SUPPORTED_TEXT_EXTENSIONS = {".json", ".md", ".txt", ".jsonl", ".py", ".js", ".ts", ".tsx", ".jsx", ".mjs"}


def _collect_paths(source_dir: Path) -> List[str]:
    return [str(path.relative_to(source_dir)).replace("\\", "/") for path in source_dir.rglob("*") if path.is_file()]


def _collect_text_contents(source_dir: Path, relative_paths: Iterable[str]) -> Dict[str, str]:
    contents: Dict[str, str] = {}
    for relative in relative_paths:
        path = source_dir / relative
        if path.suffix.lower() not in SUPPORTED_TEXT_EXTENSIONS:
            continue
        try:
            contents[relative] = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
    return contents


def compile_dna(db: Any, source_dir: str) -> Dict[str, Any]:
    """Compatibility wrapper around DNAExtractorEngine.

    `db` is accepted for old callers but is intentionally ignored. New code must
    call `DNAExtractorEngine.extract_from_tree()` directly.
    """

    source = Path(source_dir)
    source.mkdir(parents=True, exist_ok=True)
    relative_paths = _collect_paths(source)
    contents = _collect_text_contents(source, relative_paths)
    extractor = DNAExtractorEngine()
    package = extractor.extract_from_tree(
        source_id=source.name or "dna_source",
        paths=relative_paths,
        metadata={"source": "legacy_compile_dna_adapter", "deprecated": True},
        file_contents=contents,
    )
    return {
        "ok": True,
        "deprecated": True,
        "adapter": "DNAExtractorEngine",
        "scanned": len(relative_paths),
        "compiled": len(package.get("runtime_objects", [])),
        "package": package,
    }
