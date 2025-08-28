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
        QCheckBox,
        QVBoxLayout,
        QHBoxLayout,
        QTableWidget,
        QTableWidgetItem,
        QHeaderView,
        QSplitter,
        QMessageBox,
        QTabWidget,
        QPushButton,
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
        self.tabs = QTabWidget()
        self.category_list = QListWidget()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Filter tags...")
        self.only_unlocked_cb = QCheckBox("Nur Start-Tags")
        self.only_unlocked_cb.setToolTip(
            "Nur Tags anzeigen, die zum Spielstart freigeschaltet sind (Condition DATE:>=01-01-1929 oder DATE:>=1929)"
        )
        self.only_unlocked_cb.setChecked(True)
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
        mid_layout.addWidget(self.only_unlocked_cb)
        mid_layout.addWidget(self.search_box)
        mid_layout.addWidget(self.tag_list)

        # Right panel: related table
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.addWidget(QLabel("Related (by score)"))
        right_layout.addWidget(self.related_table)

        splitter_main = QSplitter()
        splitter_main.addWidget(left_panel)
        splitter_main.addWidget(mid_panel)
        splitter_main.addWidget(right_panel)
        splitter_main.setStretchFactor(0, 1)
        splitter_main.setStretchFactor(1, 2)
        splitter_main.setStretchFactor(2, 2)

        # Settings tab (manage additional unlocked tags)
        settings_panel = QWidget()
        settings_layout = QVBoxLayout(settings_panel)
        settings_layout.addWidget(QLabel("Weitere freigeschaltete Tags (Forschung)"))
        self.settings_search = QLineEdit()
        self.settings_search.setPlaceholderText("Tags suchen...")
        settings_layout.addWidget(self.settings_search)
        self.settings_list = QListWidget()
        self.settings_list.setSelectionMode(QListWidget.NoSelection)
        settings_layout.addWidget(self.settings_list)
        hint = QLabel("Haken = zusätzlich freigeschaltet (wirkt wie Start-Tag)")
        hint.setStyleSheet("color: gray;")
        settings_layout.addWidget(hint)

        # Tabs setup
        browse_tab = QWidget()
        browse_layout = QHBoxLayout(browse_tab)
        browse_layout.addWidget(splitter_main)
        self.tabs.addTab(browse_tab, "Browser")
        self.tabs.addTab(settings_panel, "Settings")

        # Central widget is the tab widget
        self.setCentralWidget(self.tabs)

        # State
        self._all_tags_by_category: dict[str, list[str]] = {}
        for cat in sorted(self._index.categories):
            self._all_tags_by_category[cat] = sorted(self._index.items(cat))
        self._unlocked: set[str] = self._load_unlocked_tags(self._project_root)
        self._manual_unlocked: set[str] = set()
        # Precompute full tag list for settings
        self._all_tags: list[str] = sorted({t for lst in self._all_tags_by_category.values() for t in lst})

        # Populate categories
        for cat in self._all_tags_by_category.keys():
            self.category_list.addItem(QListWidgetItem(cat))

        # Populate settings list with checkable items
        self._refresh_settings_list()

        # Signals
        self.category_list.currentItemChanged.connect(self._on_category_changed)
        self.search_box.textChanged.connect(self._on_filter_changed)
        self.tag_list.currentItemChanged.connect(self._on_tag_selected)
        self.only_unlocked_cb.toggled.connect(self._on_filter_changed)
        self.settings_search.textChanged.connect(self._on_settings_filter_changed)
        self.settings_list.itemChanged.connect(self._on_settings_item_changed)

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
        if self.only_unlocked_cb.isChecked():
            effective_unlocked = self._effective_unlocked()
            items = [t for t in items if t in effective_unlocked]
        for t in items:
            self.tag_list.addItem(QListWidgetItem(t))
        if self.tag_list.count() > 0:
            self.tag_list.setCurrentRow(0)

    # --- Settings helpers ---
    def _refresh_settings_list(self) -> None:
        q = self.settings_search.text().strip().lower() if hasattr(self, "settings_search") else ""
        self.settings_list.blockSignals(True)
        self.settings_list.clear()
        for t in self._all_tags:
            if q and q not in t.lower():
                continue
            item = QListWidgetItem(t)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            # Checked if it's a start tag or previously manually unlocked
            checked = (t in self._unlocked) or (t in self._manual_unlocked)
            item.setCheckState(Qt.Checked if checked else Qt.Unchecked)
            self.settings_list.addItem(item)
        self.settings_list.blockSignals(False)

    def _on_settings_filter_changed(self, text: str) -> None:
        self._refresh_settings_list()

    def _on_settings_item_changed(self, item: QListWidgetItem) -> None:
        tag = item.text()
        if item.checkState() == Qt.Checked and tag not in self._unlocked:
            self._manual_unlocked.add(tag)
        elif item.checkState() == Qt.Unchecked and tag in self._manual_unlocked:
            self._manual_unlocked.remove(tag)
        # If only-unlocked filter is on, refresh visible tag list
        if self.only_unlocked_cb.isChecked():
            self._refresh_tag_list()

    def _effective_unlocked(self) -> set[str]:
        """Union of start-unlocked and manually unlocked tags."""
        return set(self._unlocked) | set(self._manual_unlocked)

    @staticmethod
    def _load_unlocked_tags(project_root: Path) -> set[str]:
        """Return tag IDs that are available at game start.

        Definition: Tag entries in TagData.json whose parameters.Condition contains
        either "DATE:>=01-01-1929" or "DATE:>=1929".
        """
        path = project_root / "Data" / "Configs" / "TagData.json"
        try:
            raw = path.read_text(encoding="utf-8")
        except Exception:
            return set()
        try:
            import json as _json
            data = _json.loads(raw)
        except Exception:
            return set()
        unlocked: set[str] = set()
        for tag_id, meta in data.items():
            if not isinstance(meta, dict):
                continue
            params = meta.get("parameters")
            if isinstance(params, dict):
                cond = params.get("Condition")
                if isinstance(cond, str) and ("DATE:>=01-01-1929" in cond or "DATE:>=1929" in cond):
                    unlocked.add(tag_id)
        return unlocked


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
