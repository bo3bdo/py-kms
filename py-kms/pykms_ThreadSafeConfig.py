#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Thread-safe configuration management for py-kms."""

from __future__ import annotations

import threading
from typing import Any, Dict, Optional, TypeVar

T = TypeVar("T")


class ThreadSafeConfig:
    """Thread-safe configuration dictionary with RWLock pattern."""

    def __init__(self, initial: Optional[Dict[str, Any]] = None) -> None:
        self._data: Dict[str, Any] = initial or {}
        self._lock = threading.RLock()

    def get(self, key: str, default: Any = None) -> Any:
        """Thread-safe get operation."""
        with self._lock:
            return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Thread-safe set operation."""
        with self._lock:
            self._data[key] = value

    def update(self, other: Dict[str, Any]) -> None:
        """Thread-safe update operation."""
        with self._lock:
            self._data.update(other)

    def __getitem__(self, key: str) -> Any:
        """Support dict-like access."""
        with self._lock:
            return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """Support dict-like assignment."""
        with self._lock:
            self._data[key] = value

    def __contains__(self, key: str) -> bool:
        """Support 'in' operator."""
        with self._lock:
            return key in self._data

    def keys(self) -> list[str]:
        """Thread-safe keys access."""
        with self._lock:
            return list(self._data.keys())

    def values(self) -> list[Any]:
        """Thread-safe values access."""
        with self._lock:
            return list(self._data.values())

    def items(self) -> list[tuple[str, Any]]:
        """Thread-safe items access."""
        with self._lock:
            return list(self._data.items())

    def copy(self) -> Dict[str, Any]:
        """Thread-safe copy."""
        with self._lock:
            return self._data.copy()

    def pop(self, key: str, default: Any = None) -> Any:
        """Thread-safe pop operation."""
        with self._lock:
            return self._data.pop(key, default)
