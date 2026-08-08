"""Collector interface."""
from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime, timezone


class Collector(ABC):
    """A collector gathers one data surface and returns a pushable payload."""

    name: str = "base"

    @abstractmethod
    def collect(self) -> dict:
        """Return payload for POST body. Called on each interval."""


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
