# Puni MST Tool

**Puni MST Tool** is a comprehensive GUI tool built with Python and Tkinter designed to edit, view, and create custom Yo-kai/units, items, and fusions for Yo-kai Watch Puni Puni and Wibble Wobble (WibWob) game files and emulation environments.

---

## 🌟 Key Features

- **Yo-kai Database Management (`ywp_mst_youkai`)**:
  - Full editing of core attributes (Name, Tribe/Kind, Rank/Rarity, Food Type, Base & Max HP/ATK, Evolution parameters, Descriptions, and Dictionary IDs).
  - Quick searching and multi-criteria filtering by Name, Rank, Tribe, Food Type, Dictionary ID, Soultimate Type, or Bonus Effect.
  - Yo-kai duplication/cloning, recently viewed history, version comparison, and automatic Next-Available-ID & conflict detection.
  - Built-in stat presets by rank (E through UZ) and HP/ATK consistency validation (`stat_presets.py`).

- **Soultimate, Strong Skill & Multi-Skill Editing**:
  - **Soultimates (`ywp_mst_youkai_skill` & `ywp_mst_youkai_skill_level`)**: Supports Soultimate Types (`-1` to `119`), properties, animations, and a bulk 1–7 level grid editor.
  - **Strong Skills (`ywp_mst_youkai_strong_skill` & `_level`)**: Dedicated support for Puni Puni Strong Skills (`PuniPuni` game mode).
  - **Multi-Skill Bonus Effects (`ywp_mst_youkai_bonus_effect` & `_level`)**: Supports Skills 1, 2, and 3 (`YW_BONUS_EFFECTS` 1–59) with live MST preview and bulk level editing.

- **Items & Fusions Editor (`fenetres_item_conflate.py`)**:
  - Dedicated secondary windows to browse, create, duplicate, validate, and edit `ywp_mst_item` and `ywp_mst_conflate`.

- **3D & 2D Asset Viewer**:
  - **WebGL 3D Animation Viewer (`viewer_3d.py`, `ymd.py`, `viewer_assets/`)**: Local HTTP + WebGL viewer capable of parsing `.ayd`, `.ez` (via `yokai.exe`), and `.ymd` assets with full skeletal animation playback, speed/scrubber controls, wireframe, bone skeleton overlay, textures, camera presets, and PNG capture.
  - **Rank, Tribe & Icon Preview**: Extracts unit icons (`bl_*.png` / `.ayd` / `.ez`) and crops rank & tribe sprites from `rankicons.png` and `kindicons.png`.

- **Modding, Safety & Themes**:
  - **Isolated Mod Export & Import**: Dump single Yo-kai packages or load mod folders (`ywp_mst_youkai`, skills, bonus effects).
  - **Direct Save & Automatic Backups**: Inject or update units directly in active `.txt`/`.json` MST databases with automatic timestamped backups (`backups/`).
  - **UI Themes & Config Persistence**: Switch between 4 themes (`Mode Sakura`, `Mode Sombre`, `Mode Clair`, `Mode Printemps`) and persist paths in `config.json`.

---

## 📋 Prerequisites & Requirements

This tool requires **Python 3.8+** (tested with Python 3.11; `mainFr17.py` no longer depends on `open3d` or `numpy`).

### Python Packages (`requirements.txt`)
```text
Pillow>=9.0.0
```

*Note: `tkinter`, `json`, `os`, `io`, `struct`, `subprocess`, `http.server`, and `zipfile` are part of the Python standard library. Legacy scripts (`mainFR.py`, `mainEN.py`, `mainfr2.py`) used `numpy` and `open3d` (which do not support Python 3.14).*

### External Tools & Assets
To use all features (such as `.ez` extraction, 3D viewing, and rank/tribe previews), keep the `Resources/` folder or locate the following components:
1. `yokai.exe`: CLI tool for unpacking/converting `.ez` assets (included in `Resources/`).
2. `rankicons.png` & `kindicons.png`: Spritesheets containing rank and tribe icon graphics (included in `Resources/`).
3. Game Database Files (`.json` or `.txt`): **THESE ARE NOT PROVIDED — SUPPLY YOUR OWN**
   - Required: `ywp_mst_youkai`, `ywp_mst_youkai_skill`, `ywp_mst_youkai_skill_level`
   - Optional: `ywp_mst_youkai_bonus_effect`, `ywp_mst_youkai_bonus_effect_level`, `ywp_mst_youkai_strong_skill`, `ywp_mst_youkai_strong_skill_level`, `ywp_mst_item`, `ywp_mst_conflate`
   - `youkai/` resource folder containing `.ayd`, `.png`, `.ymd`, and `.ez` unit files. *(Note: `yokai.exe` does not support the newest Puni `.ayd` encryption.)*

---

## 🚀 Quick Start

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Rorosak/Puni-mst-tool.git
   cd Puni-mst-tool
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application**:
   ```bash
   python mainFr17.py
   ```
   *(On Windows, you can also double-click `Lancer_Mst_Tool.bat` or `run.bat`.)*

4. **Initial Setup**:
   On first launch, the tool will prompt you to select:
   - **Directory 1**: Folder containing `yokai.exe`, `rankicons.png`, and `kindicons.png` (e.g., `Resources/`).
   - **Directory 2**: Game version folder containing the target JSON/TXT master tables and asset files.

---

## 📁 Repository Structure

```text
├── Resources/                 # External tools & spritesheets (yokai.exe, rankicons.png, kindicons.png)
├── viewer_assets/             # WebGL 3D animation viewer frontend (index.html, style.css, viewer.js)
├── mainFr17.py                # Latest GUI application (V17)
├── constants.py               # Rank, tribe, food, soultimate, bonus effect & theme definitions
├── mst_io.py                  # MST (.txt/.json) read/write, backups, conflict checks & .ayd/.ez extraction
├── stat_presets.py            # Rank stat presets and HP/ATK validation
├── viewer_3d.py               # Local HTTP server & asset extraction for the WebGL 3D viewer
├── ymd.py                     # SGF YMD binary model/animation parser
├── fenetres_item_conflate.py  # Item (ywp_mst_item) and fusion (ywp_mst_conflate) editor windows
├── Lancer_Mst_Tool.bat        # Windows launcher for mainFr17.py
├── run.bat                    # Windows wrapper launcher
├── mainfr2.py / mainFR.py / mainEN.py  # Legacy standalone versions
├── requirements.txt           # Python dependency list
├── README.md                  # Documentation
└── config.json                # Automatically generated on initial configuration
```

---

## 🤝 Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request for new Soultimate types, bug fixes, or UI enhancements.

## 🙏 Acknowledgements & Credits

- A big thanks to **SuperTavor** and the **PuniEmu** project ([puniemu](https://github.com/SuperTavor/puniemu)) for all the value definitions (`YoukaiId`, `SoultType`, etc.).
- Special thanks as well to **Eclip5eLP**, creator of `yokai.exe` ([ykwp-decrypt](https://github.com/Eclip5eLP/ykwp-decrypt)), for the file decryption tools.

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
