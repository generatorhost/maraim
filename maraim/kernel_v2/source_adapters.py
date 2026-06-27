import hashlib
import time
from typing import Any, Dict, Iterable, List, Optional

from .dna_extractor_engine import DNAExtractorEngine


class RuntimeSourceAdapter:
    """Source adapter foundation for DNA extraction.

    This layer normalizes source descriptors into extractor-ready file trees. It
    does not download remote repos, unzip archives, call APIs, write files, or
    mutate databases. Production adapters can later replace the manifest-only
    behavior while preserving this contract.
    """

    source_type = "source"

    def __init__(self, kernel: Any = None, extractor: Optional[DNAExtractorEngine] = None):
        self.kernel = kernel
        self.extractor = extractor or DNAExtractorEngine(kernel)
        self.imports: List[Dict[str, Any]] = []

    def prepare(self, source: str, paths: Iterable[str], metadata: Optional[Dict[str, Any]] = None, file_contents: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        normalized_paths = sorted({self._normalize_path(path) for path in paths if path})
        source_id = self._source_id(source, normalized_paths)
        manifest = {
            "ok": True,
            "source_type": self.source_type,
            "source": source,
            "source_id": source_id,
            "paths": normalized_paths,
            "metadata": metadata or {},
            "prepared_at": time.time(),
        }
        package = self.extractor.extract_from_tree(
            source_id=source_id,
            paths=normalized_paths,
            metadata={"adapter": self.source_type, "source": source, **(metadata or {})},
            file_contents={self._normalize_path(k): v for k, v in (file_contents or {}).items()},
        )
        result = {"ok": True, "manifest": manifest, "package": package}
        self.imports.append(result)
        self._emit("prepared", {"source_id": source_id, "paths": len(normalized_paths)})
        return result

    def status(self) -> Dict[str, Any]:
        return {"source_type": self.source_type, "imports": len(self.imports), "last": self.imports[-1] if self.imports else None}

    def _source_id(self, source: str, paths: List[str]) -> str:
        digest = hashlib.sha256()
        digest.update(self.source_type.encode("utf-8"))
        digest.update(b"\n")
        digest.update(source.encode("utf-8", errors="ignore"))
        for path in paths:
            digest.update(b"\n")
            digest.update(path.encode("utf-8", errors="ignore"))
        return f"{self.source_type}:{digest.hexdigest()[:16]}"

    def _normalize_path(self, path: str) -> str:
        return path.replace("\\", "/").lstrip("/")

    def _emit(self, suffix: str, payload: Dict[str, Any]) -> None:
        if self.kernel is not None and hasattr(self.kernel, "emit"):
            self.kernel.emit(f"source_adapter.{self.source_type}.{suffix}", payload)


class GitSourceAdapter(RuntimeSourceAdapter):
    source_type = "git"

    def prepare_git_url(self, url: str, branch: str = "main", paths: Optional[Iterable[str]] = None, file_contents: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        metadata = {"url": url, "branch": branch, "mode": "manifest_only"}
        return self.prepare(url, paths or [], metadata=metadata, file_contents=file_contents)


class ArchiveSourceAdapter(RuntimeSourceAdapter):
    source_type = "archive"

    def prepare_archive(self, archive_name: str, paths: Iterable[str], file_contents: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        metadata = {"archive_name": archive_name, "mode": "manifest_only"}
        return self.prepare(archive_name, paths, metadata=metadata, file_contents=file_contents)


class FolderSourceAdapter(RuntimeSourceAdapter):
    source_type = "folder"

    def prepare_folder(self, folder_name: str, paths: Iterable[str], file_contents: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        metadata = {"folder_name": folder_name, "mode": "manifest_only"}
        return self.prepare(folder_name, paths, metadata=metadata, file_contents=file_contents)
