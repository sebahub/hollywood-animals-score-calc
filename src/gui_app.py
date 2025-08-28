from __future__ import annotations

import sys
from pathlib import Path

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QApplication,
        QMainWindow,
        QWidget,
        QListWidget,
        QListWidgetItem,
        QLineEdit,
        QLabel,
        QVBoxLayout,
        QHBoxLayout,
        QTableWidget,
        QTableWidgetItem,
        QHeaderView,
        QSplitter,
        QMessageBox,
    )
except Exception as e:  # pragma: no cover
    print("PySide6 is required to run the GUI. Install with: pip install PySide6")
    raise
try:
    # When run as a module: python -m src.gui_app
    from .compatibility_loader import build_index  # type: ignore
except Exception:  # When run as a script: python src/gui_app.py
    from compatibility_loader import build_index  # type: ignore


class CompatibilityBrowser(QMainWindow):
    def __init__(self, project_root: Path | str = ".") -> None:
        super().__init__()
        self.setWindowTitle("Tag Compatibility Browser")
        self.resize(1200, 700)

        self._project_root = Path(project_root)
        self._index = build_index(self._project_root)

        # Widgets
        self.category_list = QListWidget()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Filter tags...")
        self.tag_list = QListWidget()
        self.related_table = QTableWidget(0, 2)
        self.related_table.setHorizontalHeaderLabels(["Related Tag", "Score"])
        self.related_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.related_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.related_table.setAlternatingRowColors(True)

        # Left panel: categories
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.addWidget(QLabel("Categories"))
        left_layout.addWidget(self.category_list)

        # Middle panel: search + tags
        mid_panel = QWidget()
        mid_layout = QVBoxLayout(mid_panel)
        mid_layout.addWidget(QLabel("Tags"))
        mid_layout.addWidget(self.search_box)
        mid_layout.addWidget(self.tag_list)

        # Right panel: related table
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.addWidget(QLabel("Related (by score)"))
        right_layout.addWidget(self.related_table)

        splitter = QSplitter()
        splitter.addWidget(left_panel)
        splitter.addWidget(mid_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setStretchFactor(2, 2)

        central = QWidget()
        central_layout = QHBoxLayout(central)
        central_layout.addWidget(splitter)
        self.setCentralWidget(central)

        # State
        self._all_tags_by_category: dict[str, list[str]] = {}
        for cat in sorted(self._index.categories):
            self._all_tags_by_category[cat] = sorted(self._index.items(cat))

        # Populate categories
        for cat in self._all_tags_by_category.keys():
            self.category_list.addItem(QListWidgetItem(cat))

        # Signals
        self.category_list.currentItemChanged.connect(self._on_category_changed)
        self.search_box.textChanged.connect(self._on_filter_changed)
        self.tag_list.currentItemChanged.connect(self._on_tag_selected)

        # Select first category by default
        if self.category_list.count() > 0:
            self.category_list.setCurrentRow(0)

        self.statusBar().showMessage(
            f"Loaded: {sum(len(v) for v in self._all_tags_by_category.values())} tags across {len(self._all_tags_by_category)} categories"
        )

    # --- Slots ---
    def _on_category_changed(self, current: QListWidgetItem, previous: QListWidgetItem | None) -> None:
        self._refresh_tag_list()
        self.related_table.setRowCount(0)

    def _on_filter_changed(self, text: str) -> None:
        self._refresh_tag_list()

    def _on_tag_selected(self, current: QListWidgetItem, previous: QListWidgetItem | None) -> None:
        if not current:
            self.related_table.setRowCount(0)
            return
        full_tag = current.text()
        related = self._index.related(full_tag)
        # Sort by score descending, then by key
        rows = sorted(related.items(), key=lambda kv: (-kv[1], kv[0]))
        self.related_table.setRowCount(len(rows))
        for r, (tag, score) in enumerate(rows):
            self.related_table.setItem(r, 0, QTableWidgetItem(tag))
            score_item = QTableWidgetItem(f"{score:.3f}")
            score_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.related_table.setItem(r, 1, score_item)
        self.related_table.resizeRowsToContents()
        self.statusBar().showMessage(f"{full_tag}: {len(rows)} related tags")

    # --- Helpers ---
    def _current_category(self) -> str | None:
        item = self.category_list.currentItem()
        return item.text() if item else None

    def _refresh_tag_list(self) -> None:
        cat = self._current_category()
        self.tag_list.clear()
        if not cat:
            return
        all_items = self._all_tags_by_category.get(cat, [])
        q = self.search_box.text().strip().lower()
        if q:
            items = [t for t in all_items if q in t.lower()]
        else:
            items = all_items
        for t in items:
            self.tag_list.addItem(QListWidgetItem(t))
        if self.tag_list.count() > 0:
            self.tag_list.setCurrentRow(0)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv if argv is None else argv)
    app = QApplication(argv)
    try:
        win = CompatibilityBrowser(project_root=Path(__file__).resolve().parents[1])
    except Exception as e:
        QMessageBox.critical(None, "Error", f"Failed to load data: {e}")
        return 1
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
