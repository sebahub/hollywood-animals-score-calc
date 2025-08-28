from __future__ import annotations

from pathlib import Path
from typing import List

from compatibility_loader import build_index


def main(args: List[str] | None = None) -> None:
    idx = build_index(Path(__file__).resolve().parents[1])

    print("Categories found:")
    for cat in sorted(idx.categories):
        count = len(idx.items(cat))
        print(f"- {cat}: {count} items")

    # Show a few sample keys per category
    print("\nSamples:")
    for cat in sorted(idx.categories):
        keys = idx.items(cat)[:5]
        print(f"[{cat}] -> {', '.join(keys) if keys else '(none)'}")
        if keys:
            related = idx.related(keys[0])
            # take up to 5 related
            rel_items = list(related.items())[:5]
            preview = ", ".join(f"{k}:{v:.3f}" for k, v in rel_items)
            print(f"  related({keys[0]}): {preview if preview else '(none)'}")
        print()


if __name__ == "__main__":
    main()
