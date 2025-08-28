from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, Tuple
import json


def _load_game_variables(project_root: Path) -> Tuple[float, int, Tuple[float, float]]:
    """Read max_score, score_precision and tag_compatibility_score_range from GameVariables.json.

    Returns:
        (max_score, score_precision, (min_range, max_range))
    """
    gv_path = project_root / "Data" / "Configs" / "GameVariables.json"
    try:
        raw = json.loads(gv_path.read_text(encoding="utf-8"))
    except Exception:
        # Sensible fallbacks if file missing or malformed
        return 9.9, 1, (1.0, 5.0)

    def val(key: str, default: str) -> str:
        node = raw.get(key)
        if isinstance(node, dict):
            v = node.get("Value")
            if isinstance(v, str) and v.strip():
                return v.strip()
        return default

    try:
        max_score = float(val("max_score", "9.9"))
    except Exception:
        max_score = 9.9

    try:
        score_precision = int(val("score_precision", "1"))
    except Exception:
        score_precision = 1

    rng_raw = val("tag_compatibility_score_range", "1_5")
    try:
        lo_str, hi_str = rng_raw.split("_", 1)
        rng = (float(lo_str), float(hi_str))
    except Exception:
        rng = (1.0, 5.0)

    lo, hi = rng
    if hi <= lo:
        rng = (1.0, 5.0)

    return max_score, score_precision, rng


def _load_compat_map(project_root: Path) -> Dict[str, Dict[str, float]]:
    """Load TagCompatibilityData.json into a nested mapping of floats."""
    comp_path = project_root / "Data" / "Configs" / "TagCompatibilityData.json"
    data: Dict[str, Dict[str, float]] = {}
    try:
        raw = json.loads(comp_path.read_text(encoding="utf-8"))
    except Exception:
        return data
    for a, mapping in raw.items():
        if not isinstance(mapping, dict):
            continue
        bucket: Dict[str, float] = {}
        for b, score in mapping.items():
            try:
                bucket[b] = float(score)
            except Exception:
                continue
        data[str(a)] = bucket
    return data


def _load_genre_pairs(project_root: Path) -> Dict[str, Dict[str, float]]:
    """Load GenrePairs.json and return a->b -> avg(Item1, Item2) mapping as float.

    The file structure uses string numbers. We coerce and average Item1/Item2.
    """
    path = project_root / "Data" / "Configs" / "GenrePairs.json"
    out: Dict[str, Dict[str, float]] = {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return out
    if not isinstance(raw, dict):
        return out
    for ga, mapping in raw.items():
        if not isinstance(mapping, dict):
            continue
        bucket: Dict[str, float] = {}
        for gb, pair in mapping.items():
            if not isinstance(pair, dict):
                continue
            try:
                i1 = float(pair.get("Item1", 0) or 0)
            except Exception:
                i1 = 0.0
            try:
                i2 = float(pair.get("Item2", 0) or 0)
            except Exception:
                i2 = 0.0
            bucket[str(gb)] = (i1 + i2) / 2.0
        out[str(ga)] = bucket
    return out


GENRE_TAGS = {
    "DRAMA",
    "COMEDY",
    "ACTION",
    "ROMANCE",
    "DETECTIVE",
    "ADVENTURE",
    "THRILLER",
    "HISTORICAL",
    "HORROR",
    "SCIENCE_FICTION",
    "SLAPSTICK_COMEDY",
}


def _lookup_pair(mapping: Dict[str, Dict[str, float]], a: str, b: str) -> float | None:
    """Undirected lookup a->b or b->a in a nested mapping."""
    amap = mapping.get(a, {})
    if b in amap:
        return amap[b]
    bmap = mapping.get(b, {})
    if a in bmap:
        return bmap[a]
    return None
    return data


def compute_agnostic_score(selected_tags: Iterable[str], project_root: Path | str) -> float:
    """Compute an agnostic Film Builder score (0..max_score) based purely on
    pairwise tag compatibilities (range defined by GameVariables).

    Args:
        selected_tags: collection of tag ids (e.g. ["PROTAGONIST_COWBOY", "ACTION", ...])
        project_root: path to repo root containing Data/Configs

    Returns:
        float score rounded to score_precision (from GameVariables)
    """
    root = Path(project_root)
    tags = [str(t) for t in selected_tags]
    if len(tags) < 2:
        # Not enough for pair evaluation
        max_score, score_precision, _rng = _load_game_variables(root)
        return round(0.0, ndigits=score_precision)

    max_score, score_precision, (rng_lo, rng_hi) = _load_game_variables(root)
    comp = _load_compat_map(root)
    genre_pairs = _load_genre_pairs(root)

    # Collect available pair scores (undirected lookup: a->b or b->a)
    values: list[float] = []
    n = len(tags)
    for i in range(n):
        a = tags[i]
        amap = comp.get(a, {})
        for j in range(i + 1, n):
            b = tags[j]
            # TagCompatibilityData value (undirected)
            v = None
            if b in amap:
                v = amap[b]
            else:
                bmap = comp.get(b, {})
                if a in bmap:
                    v = bmap[a]

            # Optional GenrePairs contribution if both are genre tags
            gp = None
            if (a in GENRE_TAGS) and (b in GENRE_TAGS):
                gp = _lookup_pair(genre_pairs, a, b)

            # Combine sources: average those available, append as one value
            avail = [x for x in (v, gp) if x is not None]
            if avail:
                pair_score = sum(avail) / len(avail)
                values.append(pair_score)

    if not values:
        return round(0.0, ndigits=score_precision)

    avg = sum(values) / len(values)

    # Normalize from [rng_lo, rng_hi] to [0, 1]
    span = (rng_hi - rng_lo) if (rng_hi > rng_lo) else 4.0
    norm = (avg - rng_lo) / span
    if norm < 0.0:
        norm = 0.0
    elif norm > 1.0:
        norm = 1.0

    score = norm * max_score
    return round(score, ndigits=score_precision)


if __name__ == "__main__":  # simple manual test
    import sys
    root = Path(__file__).resolve().parents[1]
    # Example usage: python -m src.score_calculator PROTAGONIST_COWBOY ACTION WILD_WEST
    args = sys.argv[1:]
    s = compute_agnostic_score(args, root)
    print(f"Agnostic score for {args}: {s}")
