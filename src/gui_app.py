from __future__ import annotations

import sys
from pathlib import Path

try:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor
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
    from .score_calculator import compute_agnostic_score  # type: ignore
except Exception:  # When run as a script: python src/gui_app.py
    from compatibility_loader import build_index  # type: ignore
    from score_calculator import compute_agnostic_score  # type: ignore


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

        # Film Builder tab (agnostic score)
        fb_panel = QWidget()
        fb_layout = QHBoxLayout(fb_panel)
        # Left: all tags with search
        fb_left = QWidget()
        fb_left_layout = QVBoxLayout(fb_left)
        fb_left_layout.addWidget(QLabel("Alle Tags"))
        self.fb_search = QLineEdit()
        self.fb_search.setPlaceholderText("Tags filtern...")
        fb_left_layout.addWidget(self.fb_search)
        from PySide6.QtWidgets import QCheckBox as _QCB  # local alias to avoid top import shuffle
        self.fb_only_unlocked_cb = _QCB("Nur freigeschaltete Tags")
        self.fb_only_unlocked_cb.setChecked(True)
        fb_left_layout.addWidget(self.fb_only_unlocked_cb)
        # Toggle: Delta vs Score
        self.fb_show_delta_cb = _QCB("Delta statt Score anzeigen")
        self.fb_show_delta_cb.setChecked(True)
        fb_left_layout.addWidget(self.fb_show_delta_cb)
        # Two side-by-side lists for categories to reduce vertical space
        fb_lists_row = QWidget()
        fb_lists_row_layout = QHBoxLayout(fb_lists_row)
        self.fb_all_tags_list_left = QListWidget()
        self.fb_all_tags_list_left.setSelectionMode(QListWidget.ExtendedSelection)
        self.fb_all_tags_list_right = QListWidget()
        self.fb_all_tags_list_right.setSelectionMode(QListWidget.ExtendedSelection)
        fb_lists_row_layout.addWidget(self.fb_all_tags_list_left)
        fb_lists_row_layout.addWidget(self.fb_all_tags_list_right)
        fb_left_layout.addWidget(fb_lists_row)
        # Middle: add/remove buttons
        fb_mid = QWidget()
        fb_mid_layout = QVBoxLayout(fb_mid)
        fb_mid_layout.addStretch(1)
        self.fb_add_btn = QPushButton("→ Hinzufügen")
        self.fb_remove_btn = QPushButton("← Entfernen")
        fb_mid_layout.addWidget(self.fb_add_btn)
        fb_mid_layout.addWidget(self.fb_remove_btn)
        fb_mid_layout.addStretch(2)
        # We switch to checkbox-based selection, hide buttons
        self.fb_add_btn.hide()
        self.fb_remove_btn.hide()
        # Right: selected tags and score
        fb_right = QWidget()
        fb_right_layout = QVBoxLayout(fb_right)
        self.fb_selected_label = QLabel("Ausgewählte Tags (0)")
        fb_right_layout.addWidget(self.fb_selected_label)
        self.fb_selected_list = QListWidget()
        self.fb_selected_list.setSelectionMode(QListWidget.ExtendedSelection)
        fb_right_layout.addWidget(self.fb_selected_list)
        self.fb_score_label = QLabel("Score: –")
        f = self.fb_score_label.font()
        f.setPointSize(f.pointSize() + 2)
        f.setBold(True)
        self.fb_score_label.setFont(f)
        fb_right_layout.addWidget(self.fb_score_label)
        fb_right_layout.addWidget(QLabel("Zielgruppe"))
        # Audience breakdown table
        self.fb_audience_table = QTableWidget(0, 2)
        self.fb_audience_table.setHorizontalHeaderLabels(["Audience", "%"])
        self.fb_audience_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.fb_audience_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.fb_audience_table.setAlternatingRowColors(True)
        fb_right_layout.addWidget(self.fb_audience_table)
        self.fb_clear_btn = QPushButton("Auswahl leeren")
        fb_right_layout.addWidget(self.fb_clear_btn)
        # Make the right panel much narrower
        try:
            fb_right.setMaximumWidth(360)
        except Exception:
            pass
        # Assemble
        fb_layout.addWidget(fb_left)
        fb_layout.addWidget(fb_mid)
        fb_layout.addWidget(fb_right)
        # Favor the left area; keep right compact
        try:
            fb_layout.setStretch(0, 1)
            fb_layout.setStretch(1, 0)
            fb_layout.setStretch(2, 0)
        except Exception:
            pass

        # Tabs setup
        browse_tab = QWidget()
        browse_layout = QHBoxLayout(browse_tab)
        browse_layout.addWidget(splitter_main)
        # Order: Film Builder first
        self.tabs.addTab(fb_panel, "Film Builder")
        self.tabs.addTab(browse_tab, "Browser")
        self.tabs.addTab(settings_panel, "Settings")

        # Central widget is the tab widget
        self.setCentralWidget(self.tabs)

        # State
        self._all_tags_by_category: dict[str, list[str]] = {}
        for cat in sorted(self._index.categories):
            self._all_tags_by_category[cat] = sorted(self._index.items(cat))
        self._unlocked: set[str] = self._load_unlocked_tags(self._project_root)
        self._manual_unlocked: set[str] = self._load_manual_unlocked(self._project_root)
        # Precompute full tag list for settings
        self._all_tags: list[str] = sorted({t for lst in self._all_tags_by_category.values() for t in lst})
        # Tag meta: art/commercial per tag (from TagData.json)
        self._tag_meta: dict[str, tuple[float, float]] = self._load_tag_meta(self._project_root)
        # Audience groups config
        self._audience_groups: dict[str, dict[str, float]] = self._load_audience_groups(self._project_root)
        # Film Builder state
        self._fb_selected: list[str] = []
        self._fb_current_score: float | None = None
        self._fb_recommended_tag: str | None = None
        self._fb_candidate_scores: dict[str, float] = {}
        self._fb_candidate_deltas: dict[str, float] = {}
        self._fb_pos_max_delta: float = 0.0
        self._fb_neg_min_delta: float = 0.0

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
        # Film Builder signals
        self.fb_search.textChanged.connect(self._on_fb_filter_changed)
        self.fb_add_btn.clicked.connect(self._on_fb_add_clicked)
        self.fb_remove_btn.clicked.connect(self._on_fb_remove_clicked)
        self.fb_clear_btn.clicked.connect(self._on_fb_clear_clicked)
        self.fb_all_tags_list_left.itemDoubleClicked.connect(self._on_fb_add_item)
        self.fb_all_tags_list_right.itemDoubleClicked.connect(self._on_fb_add_item)
        self.fb_selected_list.itemDoubleClicked.connect(self._on_fb_remove_item)
        self.fb_only_unlocked_cb.toggled.connect(self._on_fb_filter_changed)
        self.fb_show_delta_cb.toggled.connect(self._on_fb_filter_changed)
        self.fb_all_tags_list_left.itemChanged.connect(self._on_fb_left_item_changed)
        self.fb_all_tags_list_right.itemChanged.connect(self._on_fb_left_item_changed)

        # Select first category by default
        if self.category_list.count() > 0:
            self.category_list.setCurrentRow(0)

        # Populate Film Builder lists
        self._fb_recompute_recommendation()
        self._refresh_fb_all_tags()
        self._refresh_fb_selected()

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
        full_tag = current.data(Qt.UserRole) or current.text()
        related = self._index.related(full_tag)
        # Sort by score descending, then by key
        rows = sorted(related.items(), key=lambda kv: (-kv[1], kv[0]))
        self.related_table.setRowCount(len(rows))
        for r, (tag, score) in enumerate(rows):
            self.related_table.setItem(r, 0, QTableWidgetItem(self._pretty_tag_name(tag)))
            score_item = QTableWidgetItem(f"{score:.3f}")
            score_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.related_table.setItem(r, 1, score_item)
        self.related_table.resizeRowsToContents()
        self.statusBar().showMessage(f"{self._pretty_tag_name(full_tag)}: {len(rows)} related tags")

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
            pretty = self._pretty_tag_name(t)
            it = QListWidgetItem(pretty)
            it.setData(Qt.UserRole, t)
            self.tag_list.addItem(it)
        if self.tag_list.count() > 0:
            self.tag_list.setCurrentRow(0)

    # --- Settings helpers ---
    def _refresh_settings_list(self) -> None:
        q = self.settings_search.text().strip().lower() if hasattr(self, "settings_search") else ""
        self.settings_list.blockSignals(True)
        self.settings_list.clear()
        # Iterate by category and add a non-checkable header per category
        for cat in sorted(self._all_tags_by_category.keys()):
            tags = self._all_tags_by_category[cat]
            # Apply text filter within category
            filtered = [t for t in tags if (q in t.lower())] if q else list(tags)
            if not filtered:
                continue
            # Header
            header = QListWidgetItem(cat)
            f = header.font()
            f.setBold(True)
            header.setFont(f)
            header.setFlags(Qt.ItemIsEnabled)  # non-selectable, non-checkable header
            self.settings_list.addItem(header)
            # Items under header
            for t in filtered:
                item = QListWidgetItem(f"  {t}")  # indent for visual hierarchy
                # Make checkable
                item.setFlags((item.flags() | Qt.ItemIsUserCheckable) & ~Qt.ItemIsSelectable)
                # Checked if it's a start tag or previously manually unlocked
                checked = (t in self._unlocked) or (t in self._manual_unlocked)
                item.setCheckState(Qt.Checked if checked else Qt.Unchecked)
                # Store the real tag id for handling (strip indent later)
                item.setData(Qt.UserRole, t)
                self.settings_list.addItem(item)
        self.settings_list.blockSignals(False)

    def _on_settings_filter_changed(self, text: str) -> None:
        self._refresh_settings_list()

    def _on_settings_item_changed(self, item: QListWidgetItem) -> None:
        # Ignore headers (not user-checkable)
        if not (item.flags() & Qt.ItemIsUserCheckable):
            return
        tag = item.data(Qt.UserRole) or item.text().strip()
        if item.checkState() == Qt.Checked and tag not in self._unlocked:
            self._manual_unlocked.add(tag)
        elif item.checkState() == Qt.Unchecked and tag in self._manual_unlocked:
            self._manual_unlocked.remove(tag)
        # Persist changes
        self._save_manual_unlocked(self._project_root, self._manual_unlocked)
        # If only-unlocked filter is on, refresh visible tag list
        if self.only_unlocked_cb.isChecked():
            self._refresh_tag_list()

    def _effective_unlocked(self) -> set[str]:
        """Union of start-unlocked and manually unlocked tags."""
        return set(self._unlocked) | set(self._manual_unlocked)

    # --- Film Builder helpers ---
    def _refresh_fb_all_tags(self) -> None:
        q = self.fb_search.text().strip().lower() if hasattr(self, "fb_search") else ""
        only_unlocked = getattr(self, "fb_only_unlocked_cb", None)
        unlocked = self._effective_unlocked() if (only_unlocked and only_unlocked.isChecked()) else None
        # Prepare both lists
        self.fb_all_tags_list_left.blockSignals(True)
        self.fb_all_tags_list_right.blockSignals(True)
        self.fb_all_tags_list_left.clear()
        self.fb_all_tags_list_right.clear()
        # Group by category with headers in custom order
        desired_order = [
            "Genre",
            "Setting",
            "Protagonist",
            "Antagonist",
            "SupportingCharacter",
            "Theme",
            "Events",
            "Finale",
        ]
        # Compose ordered list: first desired ones that exist, then any remaining
        cats_all = list(self._all_tags_by_category.keys())
        seen = set()
        ordered_cats = []
        for c in desired_order:
            if c in self._all_tags_by_category and c not in seen:
                ordered_cats.append(c)
                seen.add(c)
        for c in sorted(cats_all):
            if c not in seen:
                ordered_cats.append(c)
                seen.add(c)

        # Build (cat, filtered_tags) for non-empty categories
        non_empty: list[tuple[str, list[str]]] = []
        for cat in ordered_cats:
            tags = self._all_tags_by_category[cat]
            # filter by search and unlocked
            filtered = [t for t in tags if ((not q or (q in t.lower())) and (unlocked is None or t in unlocked))]
            if not filtered:
                continue
            non_empty.append((cat, filtered))

        # Split non-empty categories across two columns
        half = (len(non_empty) + 1) // 2
        cols = [non_empty[:half], non_empty[half:]]
        targets = [self.fb_all_tags_list_left, self.fb_all_tags_list_right]
        for target, groups in zip(targets, cols):
            for cat, filtered in groups:
                # header
                pretty = "Supporting Character" if cat == "SupportingCharacter" else cat
                header = QListWidgetItem(pretty)
                hf = header.font()
                hf.setBold(True)
                header.setFont(hf)
                header.setFlags(Qt.ItemIsEnabled)  # non-selectable header
                target.addItem(header)
                # items
                for t in filtered:
                    next_score = self._fb_candidate_scores.get(t)
                    delta = self._fb_candidate_deltas.get(t)
                    show_delta = getattr(self, "fb_show_delta_cb", None)
                    if show_delta and show_delta.isChecked() and isinstance(delta, (int, float)):
                        suffix = f"  ({delta:+.2f})"
                    else:
                        suffix = f"  ({next_score:.2f})" if isinstance(next_score, (int, float)) else ""
                    pretty = self._pretty_tag_name(t)
                    it = QListWidgetItem(f"  {pretty}{suffix}")
                    it.setData(Qt.UserRole, t)
                    it.setFlags(it.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                    it.setCheckState(Qt.Checked if t in self._fb_selected else Qt.Unchecked)
                    if isinstance(delta, (int, float)):
                        color = self._fb_color_for_delta(delta)
                        if color is not None:
                            it.setForeground(color)
                    if self._fb_recommended_tag and t == self._fb_recommended_tag:
                        it.setForeground(QColor("#34c759"))
                    target.addItem(it)
        self.fb_all_tags_list_left.blockSignals(False)
        self.fb_all_tags_list_right.blockSignals(False)

    def _refresh_fb_selected(self) -> None:
        self.fb_selected_list.blockSignals(True)
        self.fb_selected_list.clear()
        for t in self._fb_selected:
            it = QListWidgetItem(self._pretty_tag_name(t))
            it.setData(Qt.UserRole, t)
            self.fb_selected_list.addItem(it)
        self.fb_selected_list.blockSignals(False)
        # Update count label
        if hasattr(self, "fb_selected_label"):
            self.fb_selected_label.setText(f"Ausgewählte Tags ({len(self._fb_selected)})")
        self._fb_update_score()

    def _on_fb_filter_changed(self, text: str) -> None:
        self._fb_recompute_recommendation()
        self._refresh_fb_all_tags()

    def _on_fb_add_clicked(self) -> None:
        tags: list[str] = []
        for it in list(self.fb_all_tags_list_left.selectedItems()) + list(self.fb_all_tags_list_right.selectedItems()):
            t = it.data(Qt.UserRole)
            if t:
                tags.append(t)
        self._fb_add_items(tags)

    def _on_fb_remove_clicked(self) -> None:
        tags: list[str] = []
        for it in self.fb_selected_list.selectedItems():
            t = it.data(Qt.UserRole) or it.text()
            tags.append(t)
        self._fb_remove_items(tags)

    def _on_fb_add_item(self, item: QListWidgetItem) -> None:
        t = item.data(Qt.UserRole)
        if t:
            self._fb_add_items([t])

    def _on_fb_remove_item(self, item: QListWidgetItem) -> None:
        t = item.data(Qt.UserRole) or item.text()
        self._fb_remove_items([t])

    def _on_fb_left_item_changed(self, item: QListWidgetItem) -> None:
        # Ignore headers (no user role payload)
        t = item.data(Qt.UserRole)
        if not t:
            return
        checked = item.checkState() == Qt.Checked
        if checked and t not in self._fb_selected:
            self._fb_add_items([t])
        elif (not checked) and t in self._fb_selected:
            self._fb_remove_items([t])

    def _fb_add_items(self, tags: list[str]) -> None:
        changed = False
        for t in tags:
            if t not in self._fb_selected:
                self._fb_selected.append(t)
                changed = True
        if changed:
            self._fb_recompute_recommendation()
            self._refresh_fb_selected()
            self._refresh_fb_all_tags()

    def _fb_remove_items(self, tags: list[str]) -> None:
        if not tags:
            return
        before = set(self._fb_selected)
        self._fb_selected = [t for t in self._fb_selected if t not in tags]
        if set(self._fb_selected) != before:
            self._fb_recompute_recommendation()
            self._refresh_fb_selected()
            self._refresh_fb_all_tags()

    def _on_fb_clear_clicked(self) -> None:
        if self._fb_selected:
            self._fb_selected.clear()
            self._fb_recompute_recommendation()
            self._refresh_fb_selected()
            self._refresh_fb_all_tags()

    def _fb_update_score(self) -> None:
        try:
            score = compute_agnostic_score(self._fb_selected, self._project_root)
            self._fb_current_score = score
            self.fb_score_label.setText(f"Score: {score}")
        except Exception as e:
            self.fb_score_label.setText("Score: –")
            self._fb_current_score = None
        # Update audience after score computation
        self._fb_update_audience()

    def _fb_visible_candidates(self) -> list[str]:
        q = self.fb_search.text().strip().lower()
        only_unlocked = self.fb_only_unlocked_cb.isChecked()
        unlocked = self._effective_unlocked() if only_unlocked else None
        candidates: list[str] = []
        for cat in self._all_tags_by_category.keys():
            for t in self._all_tags_by_category[cat]:
                if q and (q not in t.lower()):
                    continue
                if unlocked is not None and t not in unlocked:
                    continue
                candidates.append(t)
        return candidates

    def _fb_recompute_recommendation(self) -> None:
        candidates = self._fb_visible_candidates()
        current_set = set(self._fb_selected)
        best_tag: str | None = None
        best_score: float | None = None
        # Ensure current score is computed
        try:
            current_score = compute_agnostic_score(self._fb_selected, self._project_root)
        except Exception:
            current_score = 0.0
        self._fb_current_score = current_score
        # compute candidate next scores and deltas
        cand_scores: dict[str, float] = {}
        cand_deltas: dict[str, float] = {}
        pos_max = 0.0
        neg_min = 0.0
        for t in candidates:
            if t in current_set:
                continue
            try:
                s = compute_agnostic_score(self._fb_selected + [t], self._project_root)
            except Exception:
                continue
            delta = s - current_score
            cand_scores[t] = s
            cand_deltas[t] = delta
            if delta > pos_max:
                pos_max = delta
            if delta < neg_min:
                neg_min = delta
            if (best_score is None) or (s > best_score):
                best_score = s
                best_tag = t
        self._fb_recommended_tag = best_tag
        self._fb_candidate_scores = cand_scores
        self._fb_candidate_deltas = cand_deltas
        self._fb_pos_max_delta = pos_max
        self._fb_neg_min_delta = neg_min

    def _fb_color_for_delta(self, delta: float):
        # Positive improvements: green shades (adaptive)
        pos_max = self._fb_pos_max_delta
        if delta > 0:
            if pos_max > 0 and delta >= 0.66 * pos_max:
                return QColor("#34c759")  # light green (very good)
            return QColor("#147d3f")  # dark green (good)
        # Negative or neutral: treat down to -0.9 as yellow
        if delta >= -0.9:
            return QColor("#f5c518")  # yellow
        return QColor("#d0021b")  # red

    # --- Persistence of manual unlocked ---
    @staticmethod
    def _load_tag_meta(project_root: Path) -> dict[str, tuple[float, float]]:
        """Return mapping tag_id -> (artValue, commercialValue). Missing values default to 0.0"""
        path = project_root / "Data" / "Configs" / "TagData.json"
        try:
            raw = path.read_text(encoding="utf-8")
            import json as _json
            data = _json.loads(raw)
        except Exception:
            return {}
        out: dict[str, tuple[float, float]] = {}
        if isinstance(data, dict):
            for tag_id, meta in data.items():
                if not isinstance(meta, dict):
                    continue
                try:
                    a = float(meta.get("artValue", 0) or 0)
                except Exception:
                    a = 0.0
                try:
                    c = float(meta.get("commercialValue", 0) or 0)
                except Exception:
                    c = 0.0
                out[str(tag_id)] = (a, c)
        return out

    @staticmethod
    def _load_audience_groups(project_root: Path) -> dict[str, dict[str, float]]:
        """Load audience weights from AudienceGroups.json. Returns mapping id -> weights dict."""
        path = project_root / "Data" / "Configs" / "AudienceGroups.json"
        try:
            raw = path.read_text(encoding="utf-8")
            import json as _json
            data = _json.loads(raw)
        except Exception:
            return {}
        out: dict[str, dict[str, float]] = {}
        if isinstance(data, dict):
            for gid, meta in data.items():
                if not isinstance(meta, dict):
                    continue
                def _f(k: str) -> float:
                    try:
                        return float(meta.get(k, 0) or 0)
                    except Exception:
                        return 0.0
                out[str(gid)] = {
                    "baseWeight": _f("baseWeight"),
                    "artWeight": _f("artWeight"),
                    "commercialWeight": _f("commercialWeight"),
                    "baseDefaultAudience": _f("baseDefaultAudience"),
                    "artDefaultAudience": _f("artDefaultAudience"),
                    "comDefaultAudience": _f("comDefaultAudience"),
                }
        return out

    def _fb_compute_audience(self) -> list[tuple[str, float]]:
        """Compute normalized audience distribution based on selected tags.

        Heuristic: Sum art/commercial over selected tags, clamp negatives to 0 for appeal,
        then for each audience group compute:
            raw = baseWeight + artWeight*art_pos + commercialWeight*com_pos
            + baseDefaultAudience + artDefaultAudience*art_pos + comDefaultAudience*com_pos
        Normalize raw to percentages.
        """
        if not self._audience_groups:
            return []
        art_total = 0.0
        com_total = 0.0
        for t in self._fb_selected:
            a, c = self._tag_meta.get(t, (0.0, 0.0))
            art_total += a
            com_total += c
        art_pos = max(0.0, art_total)
        com_pos = max(0.0, com_total)
        raws: dict[str, float] = {}
        for gid, w in self._audience_groups.items():
            raw = (
                w.get("baseWeight", 0.0)
                + w.get("artWeight", 0.0) * art_pos
                + w.get("commercialWeight", 0.0) * com_pos
                + w.get("baseDefaultAudience", 0.0)
                + w.get("artDefaultAudience", 0.0) * art_pos
                + w.get("comDefaultAudience", 0.0) * com_pos
            )
            raws[gid] = max(0.0, raw)
        s = sum(raws.values())
        if s <= 0:
            return [(gid, 0.0) for gid in sorted(raws.keys())]
        return [(gid, 100.0 * v / s) for gid, v in sorted(raws.items())]

    def _fb_update_audience(self) -> None:
        dist = self._fb_compute_audience()
        # Map codes to friendly labels and enforce order
        label_map = {
            "AF": "Adult Female",
            "AM": "Adult Male",
            "TF": "Teen Female",
            "TM": "Teen Male",
            "YF": "Young Female",
            "YM": "Young Male",
        }
        order = ["AF", "AM", "TF", "TM", "YF", "YM"]
        dist_dict = {k: v for k, v in dist}
        rows = [(gid, dist_dict.get(gid, 0.0)) for gid in order if gid in dist_dict] + [
            (gid, pct) for gid, pct in dist if gid not in order
        ]
        self.fb_audience_table.setRowCount(len(rows))
        for r, (gid, pct) in enumerate(rows):
            name = label_map.get(gid, gid)
            self.fb_audience_table.setItem(r, 0, QTableWidgetItem(name))
            it = QTableWidgetItem(f"{pct:.1f}")
            it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.fb_audience_table.setItem(r, 1, it)
        self.fb_audience_table.resizeRowsToContents()

    # --- Presentation helpers ---
    @staticmethod
    def _pretty_tag_name(tag_id: str) -> str:
        """Return a display-friendly tag name: strip known category prefixes and underscores.

        Keeps the raw ID semantics elsewhere via Qt.UserRole.
        """
        prefixes = [
            "PROTAGONIST_",
            "ANTAGONIST_",
            "SUPPORTINGCHARACTER_",
            "THEME_",
            "EVENTS_",
            "FINALE_",
        ]
        s = tag_id
        for p in prefixes:
            if s.startswith(p):
                s = s[len(p):]
                break
        return s.replace("_", " ")
    @staticmethod
    def _manual_unlocked_path(project_root: Path) -> Path:
        # Store alongside the project, not inside game data
        return project_root / "ManualUnlocked.json"

    @classmethod
    def _load_manual_unlocked(cls, project_root: Path) -> set[str]:
        path = cls._manual_unlocked_path(project_root)
        try:
            raw = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return set()
        except Exception:
            return set()
        try:
            import json as _json
            data = _json.loads(raw)
            if isinstance(data, list):
                return {str(x) for x in data}
            return set()
        except Exception:
            return set()

    @classmethod
    def _save_manual_unlocked(cls, project_root: Path, items: set[str]) -> None:
        path = cls._manual_unlocked_path(project_root)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            import json as _json
            path.write_text(_json.dumps(sorted(items), ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            # Non-fatal
            pass

    # Ensure we persist on close as well
    def closeEvent(self, event) -> None:  # type: ignore[override]
        try:
            self._save_manual_unlocked(self._project_root, self._manual_unlocked)
        finally:
            return super().closeEvent(event)

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
