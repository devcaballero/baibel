"""Gestor de estado persistente para el scraping secuencial de libros."""

from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from holy_bible.shared.settings import LIBROS, OUTPUT_DIR, PROJECT_ROOT

Status = Literal["pending", "processing", "completed", "failed"]

STATE_FILE = PROJECT_ROOT / "state.json"
VALID_STATUSES: set[str] = {"pending", "processing", "completed", "failed"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_book_entry(libro: dict[str, str]) -> dict[str, Any]:
    return {
        "id": libro["slug"],
        "slug": libro["slug"],
        "nombre": libro["nombre"],
        "testamento": libro["testamento"],
        "status": "pending",
        "attempts": 0,
        "error_log": [],
        "started_at": None,
        "completed_at": None,
        "updated_at": _utc_now(),
    }


class StateManager:
    """Persiste y controla el progreso de los 66 libros."""

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data
        self._by_id = {entry["id"]: entry for entry in data["libros"]}

    @classmethod
    def load_or_create(cls, path: Path = STATE_FILE) -> StateManager:
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                manager = cls(data)
                manager._ensure_all_books()
                manager.reset_stale_processing()
                manager.sync_with_output()
                manager.save()
                return manager
            except (json.JSONDecodeError, OSError, KeyError):
                pass

        data = {
            "version": 1,
            "created_at": _utc_now(),
            "updated_at": _utc_now(),
            "libros": [_default_book_entry(libro) for libro in LIBROS],
        }
        manager = cls(data)
        manager.sync_with_output()
        manager.save()
        return manager

    def _ensure_all_books(self) -> None:
        existing_ids = {entry["id"] for entry in self._data["libros"]}
        for libro in LIBROS:
            if libro["slug"] not in existing_ids:
                self._data["libros"].append(_default_book_entry(libro))
        self._by_id = {entry["id"]: entry for entry in self._data["libros"]}

    def reset_stale_processing(self) -> None:
        """Libros interrumpidos en 'processing' vuelven a 'pending'."""
        for entry in self._data["libros"]:
            if entry["status"] == "processing":
                entry["status"] = "pending"
                entry["updated_at"] = _utc_now()

    def sync_with_output(self) -> None:
        """Marca como completados los libros que ya tienen JSON válido en output/."""
        for entry in self._data["libros"]:
            slug = entry["id"]
            path = OUTPUT_DIR / f"{slug}.json"
            if not path.exists():
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if data.get("capitulos"):
                    entry["status"] = "completed"
                    entry["completed_at"] = entry.get("completed_at") or _utc_now()
                    entry["updated_at"] = _utc_now()
            except (json.JSONDecodeError, OSError):
                continue

    def get_books_to_process(
        self,
        max_attempts: int,
        slugs: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Libros elegibles: 'pending' o 'failed' con attempts < max_attempts.
        Opcionalmente filtrados por slug.
        """
        eligible: list[dict[str, Any]] = []
        slug_filter = set(slugs) if slugs else None

        for entry in self._data["libros"]:
            if slug_filter and entry["id"] not in slug_filter:
                continue

            status = entry["status"]
            if status == "pending":
                eligible.append(entry)
            elif status == "failed" and entry["attempts"] < max_attempts:
                eligible.append(entry)

        return eligible

    def mark_processing(self, book_id: str) -> None:
        entry = self._get_entry(book_id)
        entry["status"] = "processing"
        entry["started_at"] = _utc_now()
        entry["updated_at"] = _utc_now()
        self.save()

    def mark_completed(self, book_id: str) -> None:
        entry = self._get_entry(book_id)
        entry["status"] = "completed"
        entry["completed_at"] = _utc_now()
        entry["updated_at"] = _utc_now()
        self.save()

    def mark_failed(self, book_id: str, error_message: str) -> None:
        entry = self._get_entry(book_id)
        entry["status"] = "failed"
        entry["attempts"] = entry.get("attempts", 0) + 1
        entry.setdefault("error_log", []).append(
            {
                "timestamp": _utc_now(),
                "attempt": entry["attempts"],
                "message": error_message,
            }
        )
        entry["updated_at"] = _utc_now()
        self.save()

    def reset_book(self, book_id: str) -> None:
        """Reinicia un libro a pending (útil con --force)."""
        entry = self._get_entry(book_id)
        entry["status"] = "pending"
        entry["attempts"] = 0
        entry["error_log"] = []
        entry["started_at"] = None
        entry["completed_at"] = None
        entry["updated_at"] = _utc_now()
        self.save()

    def summary(self) -> dict[str, int]:
        counts = {status: 0 for status in VALID_STATUSES}
        for entry in self._data["libros"]:
            status = entry.get("status", "pending")
            if status in counts:
                counts[status] += 1
        return counts

    def save(self, path: Path = STATE_FILE) -> None:
        self._data["updated_at"] = _utc_now()
        path.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            delete=False,
            suffix=".tmp",
        ) as tmp:
            json.dump(self._data, tmp, ensure_ascii=False, indent=2)
            tmp_path = Path(tmp.name)

        tmp_path.replace(path)

    def _get_entry(self, book_id: str) -> dict[str, Any]:
        if book_id not in self._by_id:
            raise KeyError(f"Libro no registrado en state.json: {book_id}")
        return self._by_id[book_id]
