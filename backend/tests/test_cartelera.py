"""Tests básicos del seed y la cartelera (no requieren red ni BD)."""
from __future__ import annotations

from app.seed import worldcup2026 as seed


def test_seed_has_12_groups_48_teams():
    assert len(seed.GROUPS) == 12
    total = sum(len(v) for v in seed.GROUPS.values())
    assert total == 48


def test_seed_generates_72_group_matches():
    matches = seed.all_matches()
    assert len(matches) == 72
    assert all(m["group"] in seed.GROUPS for m in matches)


def test_no_more_than_10_matches_per_day():
    from collections import Counter
    by_day = Counter(m["date"] for m in seed.all_matches())
    assert max(by_day.values()) <= 10


def test_group_tables_shape():
    tables = seed.group_tables()
    assert len(tables) == 12
    for t in tables:
        assert len(t["rows"]) == 4
        assert [r["position"] for r in t["rows"]] == [1, 2, 3, 4]


def test_build_cartelera_seed_mode(monkeypatch):
    from app.services import cartelera_service as cs
    monkeypatch.setattr(cs.settings, "cartelera_source", "seed")
    payload = cs.build_cartelera("2026-06-11")
    assert payload["is_demo"] is True
    assert payload["source"] == "seed"
    assert len(payload["agenda"]) > 0
    assert len(payload["groups"]) == 12
