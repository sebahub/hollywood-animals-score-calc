from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple, Callable
import json


@dataclass(frozen=True)
class TagKey:
    category: str
    name: str

    @classmethod
    def parse(cls, key: str) -> "TagKey":
        # Split only on the first underscore to keep the rest as the tag name
        if "_" not in key:
            # Fallback: whole key is category-less
            return cls(category="UNKNOWN", name=key)
        cat, rest = key.split("_", 1)
        return cls(category=cat, name=rest)


class TagCompatibilityIndex:
    """Indexes tag compatibilities grouped by top-level category prefix.

    Example key in JSON: "PROTAGONIST_COWBOY"
    - category: PROTAGONIST
    - name: COWBOY
    """

    def __init__(self, category_resolver: Callable[[str], str] | None = None) -> None:
        # category -> full_tag_key -> (other_full_tag_key -> score)
        self._by_category: Dict[str, Dict[str, Dict[str, float]]] = {}
        # Resolver to enrich category for keys without prefixes
        self._resolve_category: Callable[[str], str] = category_resolver or (lambda key: TagKey.parse(key).category)

    @property
    def categories(self) -> Tuple[str, ...]:
        return tuple(self._by_category.keys())

    def items(self, category: str) -> Tuple[str, ...]:
        return tuple(self._by_category.get(category, {}).keys())

    def related(self, full_tag_key: str) -> Dict[str, float]:
        # Find which category this item belongs to and return its mapping
        cat = self._resolve_category(full_tag_key)
        bucket = self._by_category.get(cat, {})
        return bucket.get(full_tag_key, {})

    def add_edge(self, a: str, b: str, score: float) -> None:
        # Group by A's category (resolved via metadata if needed)
        cat = self._resolve_category(a)
        self._by_category.setdefault(cat, {})
        self._by_category[cat].setdefault(a, {})[b] = score

    @classmethod
    def from_json(cls, json_path: Path, category_resolver: Callable[[str], str] | None = None) -> "TagCompatibilityIndex":
        idx = cls(category_resolver=category_resolver)
        data = json.loads(Path(json_path).read_text(encoding="utf-8"))
        for a_key, mapping in data.items():
            # Some values in the file are strings like "3.000"; coerce to float safely
            for b_key, raw_score in mapping.items():
                try:
                    score = float(raw_score)
                except (TypeError, ValueError):
                    # If not parseable, skip but could also set to 0.0
                    continue
                idx.add_edge(a_key, b_key, score)
        return idx


def _load_tag_meta(project_root: Path) -> Dict[str, str]:
    """Load TagData.json and return tagId -> human-readable category name.

    Priority:
    - Use string `CategoryID` when present.
    - Else map numeric `category`:
        1: "Setting"
        2: "Protagonist"
        4: "SupportingCharacter"
        8: "Antagonist"
        16: "Theme"
        32: "Theme"  # EVENTS typically mapped to Theme in data
    - Fallback: "UNKNOWN"
    """
    path = project_root / "Data" / "Configs" / "TagData.json"
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}

    num_map = {
        1: "Setting",
        2: "Protagonist",
        4: "SupportingCharacter",
        8: "Antagonist",
        16: "Theme",
        32: "Theme",
    }

    result: Dict[str, str] = {}
    for tag_id, meta in raw.items():
        cat_name = meta.get("CategoryID") if isinstance(meta, dict) else None
        if isinstance(cat_name, str) and cat_name:
            result[tag_id] = cat_name
            continue
        num = meta.get("category") if isinstance(meta, dict) else None
        if isinstance(num, int) and num in num_map:
            result[tag_id] = num_map[num]
        else:
            result[tag_id] = "UNKNOWN"
    return result


def build_index(project_root: Path | str = ".") -> TagCompatibilityIndex:
    root = Path(project_root)
    path = root / "Data" / "Configs" / "TagCompatibilityData.json"
    if not path.exists():
        raise FileNotFoundError(f"Could not find TagCompatibilityData.json at {path}")
    tag_meta = _load_tag_meta(root)

    def resolver(key: str) -> str:
        # Explicit overrides for known genre tags (unprefixed)
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
        if key in GENRE_TAGS:
            return "Genre"
        # Prefer explicit prefix when present
        if "_" in key:
            prefix = key.split("_", 1)[0]
            # Normalize common known prefixes to human names
            norm = {
                "PROTAGONIST": "Protagonist",
                "ANTAGONIST": "Antagonist",
                "SUPPORTINGCHARACTER": "SupportingCharacter",
                "THEME": "Theme",
                "EVENTS": "Events",
                "FINALE": "Finale",
            }.get(prefix)
            if norm:
                return norm
        # Else try TagData.json mapping
        return tag_meta.get(key, "UNKNOWN")

    return TagCompatibilityIndex.from_json(path, category_resolver=resolver)
