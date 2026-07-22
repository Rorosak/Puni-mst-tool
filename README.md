# PuniEmu Custom Unit Maker (v5)

**PuniEmu Custom Unit Maker** is a comprehensive GUI tool built with Python and Tkinter designed to edit, view, and create custom Yo-kai/units for Yo-kai Watch Puni Puni game files and emulation environments.

---

## 🌟 Key Features

- **Yo-kai Database Management (`ywp_mst_youkai`)**:
  - Full editing of core attributes (Name, Tribe/Kind, Rank/Rarity, Base & Max HP/ATK, Evolution parameters, Descriptions, and Dictionary IDs).
  - Quick searching and filtering by Name, Rank, Tribe, Dictionary ID, or Soultimate Type.
  - Automatic Next-Available-ID locator to prevent ID collisions.

- **Soultimate & Skill Editing (`ywp_mst_youkai_skill`)**:
  - Full support for Soultimate Types (Poppers, Inflators, Attack Boosters, Tracers, Slashers, etc.).
  - Configurable skill descriptions, property flags, and 2D/3D animation triggers.
  - Granular level-by-level stats configuration (Levels 1–7) including `SoultPt`, gauge speeds, and stat dictionaries (`ywp_mst_youkai_skill_level`).

- **3D & 2D Asset Viewer**:
  - **3D Asset Rendering**: Native Open3D viewer capable of parsing `.ayd` archives and `.ez` compressed assets, extracting `.ymd` geometry, UV mappings, and texture maps.
  - **Rank & Icon Preview**: Extracts unit icons (`bl_*.png` / `.ayd`) and crops rank sprites dynamically from spritesheets.

- **Modding & Workflow Options**:
  - **Isolated Mod Export**: Save unit data as a modular package containing structured JSON/TXT data (`ywp_mst_youkai`, `ywp_mst_youkai_skill`, `ywp_mst_youkai_skill_level`).
  - **Direct Index Override**: Overwrite or inject new units directly into active game databases.
  - **Config Persistence**: Remembers paths for game version data and external tools (`yokai.exe`, `rankicons.png`).

---

## 📋 Prerequisites & Requirements

This tool requires Python 3.8+ and the following dependencies:

### Python Packages (`requirements.txt`)
```text
numpy>=1.21.0
open3d>=0.16.0
Pillow>=9.0.0
```

*Note: `tkinter`, `json`, `os`, `io`, `struct`, `subprocess`, and `zipfile` are part of the Python standard library.*

### External Tools & Assets
To use all features (such as 3D viewing and rank previews), place or locate the following external components:
1. `yokai.exe`: CLI tool for unpacking/converting `.ez` assets.
2. `rankicons.png`: Spritesheet containing rank icon graphics.
3. Game Database Files (`.json` or `.txt`):
   - `ywp_mst_youkai`
   - `ywp_mst_youkai_skill`
   - `ywp_mst_youkai_skill_level`
   - `youkai/` resource folder containing `.ayd` or `.png` unit files.

---

## 🚀 Quick Start

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-username/PuniEmu-Custom-Unit-Maker.git
   cd PuniEmu-Custom-Unit-Maker
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application**:
   ```bash
   python main.py
   ```

4. **Initial Setup**:
   On first launch, the tool will prompt you to select:
   - **Directory 1**: Path containing `yokai.exe` and `rankicons.png`.
   - **Directory 2**: Game version folder containing the target JSON/TXT master tables and the `youkai/` asset folder.

---

## 📁 Repository Structure

```text
├── main.py              # Main GUI application script
├── requirements.txt     # Python dependency list
├── README.md            # Documentation
└── config.json          # Automatically generated on initial configuration
```

---

## 🤝 Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request for new Soultimate types, bug fixes, or UI enhancements.

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
