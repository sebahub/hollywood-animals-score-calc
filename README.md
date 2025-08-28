# Hollywood Animal – Tag Compatibility Browser

This repository contains a desktop GUI app to explore and prototype tag compatibilities and audience fit based on the game data under `Data/Configs/`.

Key features:
- Tag Compatibility Browser with per-category filtering and related-tag table.
- Film Builder prototype with selectable tags, live score, and next-tag recommendations.
- Toggle to show per-tag delta vs. next score for recommendations.
- Audience distribution table computed from selected tags and `AudienceGroups.json`.
- Separate displays for Art and Commercial aggregates from `TagData.json`.
- Genre pair interaction support using `GenrePairs.json`.

## 1. Prerequisites
- Python 3.10+ (3.11 recommended)
- Windows, macOS, or Linux
- Git (optional)

## 2. Setup
It is recommended to use a virtual environment.

### Windows (PowerShell)
```powershell
# From the project root
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### macOS / Linux (bash/zsh)
```bash
python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

If you do not have a `requirements.txt`, install the essentials:
```bash
pip install PySide6
```

## 3. Launching the App
From the project root:
```bash
python ./src/gui_app.py
```
The app window should open with two main tabs: the tag browser and the film builder.

## 4. Project Structure
- `src/gui_app.py`: Main GUI application (Qt). Implements the UI and all film builder logic.
- `src/compatibility_loader.py`: Loads and indexes `TagCompatibilityData.json` and maps tags to categories.
- `src/score_calculator.py`: Computes an agnostic score from selected tags; integrates `GenrePairs.json`.
- `src/inspect_compat.py`: Helpers and utilities for inspecting compatibility data.
- `Data/Configs/`: Game configuration JSON files, e.g.:
  - `TagCompatibilityData.json`: Pairwise compatibility values.
  - `TagData.json`: Tag metadata (category mapping, artValue, commercialValue, etc.).
  - `AudienceGroups.json`: Audience group weights and defaults.
  - `GenrePairs.json`: Additional genre-genre pair interactions.

## 5. How Scores and Audience Are Calculated
- Overall Score: `src/score_calculator.py` → `compute_agnostic_score()` uses pairwise values from `TagCompatibilityData.json`. For pairs that are both genres, it also considers `GenrePairs.json` and averages available sources.
- Delta vs. Score Display: In the Film Builder tag lists you can toggle between showing the delta (improvement vs. current selection) and the next score if this tag were added.
- Art/Commercial Aggregates: Film Builder shows the sum of `artValue` and `commercialValue` across selected tags (from `TagData.json`).
- Audience Distribution: Based on `AudienceGroups.json` and the positive parts of the aggregated Art/Commercial values; the result is normalized to 100% and displayed per audience group.

## 6. Troubleshooting
- Qt platform plugin errors (e.g., "could not load platform plugin"):
  - Ensure PySide6 is installed in your active virtual environment.
  - On Linux, ensure you have the necessary X11/Wayland runtime libraries.
- Import errors:
  - Activate your virtual environment before running the app.
  - Reinstall dependencies with `pip install -r requirements.txt`.
- No data / missing files:
  - Verify that `Data/Configs/` exists with the expected JSON files.

## 7. Development Notes
- Run directly with `python src/gui_app.py` during development.
- Code style: standard Python type hints are used; no strict linter enforced.
- If you add new data files under `Data/Configs/`, please keep their structure consistent and update loaders as needed.

## 8. License
This project is intended for internal prototyping. If you plan to publish or distribute, add a proper license here.
