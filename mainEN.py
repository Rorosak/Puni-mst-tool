import json
import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import ttk
import os
import io
import struct
import subprocess
import zipfile
import numpy as np
import open3d as o3d
from PIL import Image, ImageTk

# --- PARAMETERS AND GLOBAL VARIABLES ---
CONFIG_FILE = "config.json" 

# These variables will be filled dynamically at startup
DB_FILE = ""
SKILL_DB_FILE = ""
SKILL_LEVEL_DB_FILE = ""
RESOURCES_FOLDER = ""

# These tools remain linked to your software installation folder
YOKAI_EXE_PATH = ""
SPRITESHEET_PATH = ""

RANK_COORDINATES = {
    "1": (2, 0), "2": (3, 0), "3": (4, 0), "4": (5, 0),
    "5": (6, 0), "6": (7, 0), "7": (0, 1), "8": (2, 1),
    "9": (4, 1), "10": (6, 1), "11": (0, 2), "12": (2, 2)
}

rank_image_ref = None 
skill_levels_dict = {} 
skill_levels_entries = {}
current_level_var = None 
previous_level = "1"
json_data = {}
yokai_lines = []
skills_dict = {}
found_index = -1
input_entries = []
skill_entries = {}
tk_image_ref = None 
res_window = None 
advanced_mode_active = False

SOULT_TYPES = {
    "-1": "None", "1": "RangePopper", "2": "SummonOtherPuni", "3": "RandomPopper",
    "4": "Inflator", "5": "Hider", "7": "PuniRearranger", "8": "BallMaker",
    "9": "Healer", "11": "Befriender", "12": "ExpBooster", "13": "MoneyBooster",
    "14": "ItemDropBooster", "15": "AttackBooster", "16": "ScoreBooster",
    "17": "DefenseBooster", "18": "Stunner", "20": "DirectAttacker",
    "22": "MultipleAreaPopper", "23": "BonusBallsMaker", "24": "AttackBoosterAndHeal",
    "25": "AllAttackerAndStunner", "26": "InflatorBetter", "27": "CrossAreaPopper",
    "28": "AllAttackerAndHealer", "30": "Tracer", "31": "SingleAttackerAndHPScaling",
    "32": "PopperDissapear", "33": "SingleAttackerAndBefriender", "34": "SingleAttackerLuckScaling",
    "35": "SingleAttackerScalingOnPuni", "36": "AllPopperHealerScalingOnPuni",
    "41": "NoFillerTracer", "44": "Slasher"
}

YOKAI_FIELDS = [
    "0: YoukaiId", "1: YoukaiName", "2: YoukaiType", "3: YoukaiRarity", "4: YoukaiKind",
    "5: LevelType", "6: FoodType", "7: MaxLevel", "8: BaseHp", "9: MaxHp",
    "10: BaseAtk", "11: MaxAtk", "12: EvolutionYoukaiId", "13: EvolutionLevel", "14: DictionaryId",
    "15: YoukaiDescription", "16: TextPuzzle", "17: TextGasha", "18: TextMission", "19: TextGift",
    "20: UnusedName", "21: SkillEffectColorR", "22: SkillEffectColorG", "23: SkillEffectColorB", "24: ScaleBattleFriend",
    "25: ScaleBattleEnemy", "26: YoukaiSize", "27: Width", "28: Height", "29: X",
    "30: Y", "31: ReadingName", "32: FriendOffsetX", "33: FriendOffsetY", "34: EffectType",
    "35: OpenDt", "36: YoukaiEffectBack", "37: YoukaiEffectFront", "38: ScaleOffsetDeck"
]

SEARCH_INDEX = {
    "Yo-kai Name (1)": 1, "Rank / Rarity (3)": 3, "Tribe / Kind (4)": 4,
    "Dictionary ID (14)": 14, "Soultimate Type (-1 to 44)": "SOULT"
}

# ==========================================
# UNIVERSAL FILE READING FUNCTIONS (JSON/TXT)
# ==========================================
def find_file(base_name, folder):
    """Searches for a file first in .json, then in .txt"""
    for ext in [".json", ".txt"]:
        path = os.path.join(folder, base_name + ext)
        if os.path.exists(path):
            return path
    return None

def read_file_data(path):
    """Reads a file, parses JSON or returns raw text if TXT."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        try:
            data = json.loads(content)
            # Dynamically search for the data key (tableData or masterData)
            for key in ["tableData", "masterData"]:
                if key in data:
                    return str(data[key]).replace("\n", "").replace("\r", ""), data
            return content, None
        except (json.JSONDecodeError, TypeError):
            return content.replace("\n", "").replace("\r", ""), None
    except Exception as e:
        messagebox.showerror("Erreur de Lecture", f"Impossible de lire le fichier {path}:\n{e}")
        return "", None

def update_original_file(file_path, new_lines, yokai_id):
    """Updates the original file maintaining JSON or TXT format without unwanted line breaks."""
    raw_text, orig_json_data = read_file_data(file_path)
    existing_lines = raw_text.split('*') if raw_text else []
    
    # Filter old version and empty lines
    filtered_lines = [l.strip() for l in existing_lines if l.strip() and not l.startswith(yokai_id + "|")]
    
    if isinstance(new_lines, list):
        filtered_lines.extend(new_lines)
    else:
        filtered_lines.append(new_lines)
        
    new_text = "*".join(filtered_lines)
    
    with open(file_path, "w", encoding="utf-8") as f:
        if orig_json_data is not None:
            # Retain the original key (tableData or masterData)
            main_key = "tableData" if "tableData" in orig_json_data else "masterData"
            orig_json_data[main_key] = new_text
            json.dump(orig_json_data, f, ensure_ascii=False, indent=4)
        else:
            f.write(new_text)

# ==========================================
# CONFIGURATION FUNCTIONS
# ==========================================
def load_config():
    global YOKAI_EXE_PATH, SPRITESHEET_PATH, DB_FILE, SKILL_DB_FILE, SKILL_LEVEL_DB_FILE, RESOURCES_FOLDER
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            y_exe = config.get("YOKAI_EXE_PATH", "")
            s_sheet = config.get("SPRITESHEET_PATH", "")
            f_db = config.get("DB_FILE", "")
            s_db = config.get("SKILL_DB_FILE", "")
            l_db = config.get("SKILL_LEVEL_DB_FILE", "")
            d_res = config.get("RESOURCES_FOLDER", "")

            if os.path.exists(y_exe) and os.path.exists(s_sheet) and os.path.exists(f_db) and os.path.exists(s_db) and os.path.exists(l_db) and os.path.exists(d_res):
                YOKAI_EXE_PATH = y_exe
                SPRITESHEET_PATH = s_sheet
                DB_FILE = f_db
                SKILL_DB_FILE = s_db
                SKILL_LEVEL_DB_FILE = l_db
                RESOURCES_FOLDER = d_res
                return True
        except Exception:
            pass
    return False

def save_config():
    config = {
        "YOKAI_EXE_PATH": YOKAI_EXE_PATH,
        "SPRITESHEET_PATH": SPRITESHEET_PATH,
        "DB_FILE": DB_FILE,
        "SKILL_DB_FILE": SKILL_DB_FILE,
        "SKILL_LEVEL_DB_FILE": SKILL_LEVEL_DB_FILE,
        "RESOURCES_FOLDER": RESOURCES_FOLDER
    }
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error saving configuration: {e}")

def change_folders():
    global YOKAI_EXE_PATH, SPRITESHEET_PATH
    YOKAI_EXE_PATH = ""
    SPRITESHEET_PATH = ""
    
    if initialize_tools(at_startup=False) and initialize_version_folder(at_startup=False):
        save_config()
        load_file()
        load_skills()
        load_skill_levels()
        clear_interface()
        messagebox.showinfo("Success", "Folders updated and databases reloaded!")

# ==========================================
# STARTUP AND PATH FUNCTIONS
# ==========================================
def initialize_tools(at_startup=True):
    global YOKAI_EXE_PATH, SPRITESHEET_PATH
    
    tools_folder = filedialog.askdirectory(title="1/2: Select Resources/Tools Folder (containing yokai.exe and rankicons.png)")
    
    if not tools_folder:
        if at_startup:
            messagebox.showerror("Fatal Error", "No folder selected for tools. The tool will close.")
            window.destroy()
        return False
        
    for root, _, files in os.walk(tools_folder):
        if "yokai.exe" in files and not YOKAI_EXE_PATH:
            YOKAI_EXE_PATH = os.path.join(root, "yokai.exe")
        if "rankicons.png" in files and not SPRITESHEET_PATH:
            SPRITESHEET_PATH = os.path.join(root, "rankicons.png").replace("\\", "/")
            
        if YOKAI_EXE_PATH and SPRITESHEET_PATH:
            break
    
    missing_files = []
    if not YOKAI_EXE_PATH: missing_files.append("yokai.exe")
    if not SPRITESHEET_PATH: missing_files.append("rankicons.png")
    
    if missing_files:
        msg = "The following tools were not found in this folder:\n- " + "\n- ".join(missing_files)
        messagebox.showerror("Tools Not Found", msg)
        if at_startup: window.destroy()
        return False
        
    return True

def initialize_version_folder(at_startup=True):
    global DB_FILE, SKILL_DB_FILE, SKILL_LEVEL_DB_FILE, RESOURCES_FOLDER
    
    folder = filedialog.askdirectory(title="2/2: Select Game Version Folder (containing JSON or TXT files)")
    
    if not folder:
        if at_startup:
            messagebox.showerror("Fatal Error", "No folder selected. The tool will close.")
            window.destroy()
        return False
        
    DB_FILE = find_file("ywp_mst_youkai", folder)
    SKILL_DB_FILE = find_file("ywp_mst_youkai_skill", folder)
    SKILL_LEVEL_DB_FILE = find_file("ywp_mst_youkai_skill_level", folder)
    RESOURCES_FOLDER = os.path.join(folder, "youkai")
    
    missing_files = []
    if not DB_FILE: missing_files.append("ywp_mst_youkai (.json or .txt)")
    if not SKILL_DB_FILE: missing_files.append("ywp_mst_youkai_skill (.json or .txt)")
    if not SKILL_LEVEL_DB_FILE: missing_files.append("ywp_mst_youkai_skill_level (.json or .txt)")
    if not os.path.exists(RESOURCES_FOLDER): missing_files.append("'youkai' folder")
    
    if missing_files:
        msg = "The following elements were not found in this folder:\n- " + "\n- ".join(missing_files)

        messagebox.showerror("Invalid Folder", msg)
        if at_startup: window.destroy()
        return False
        
    return True

# ==========================================
# UTILITY FUNCTIONS (INTERFACE & TOOLS)
# ==========================================
def clear_interface():
    global found_index
    found_index = -1
    for entry in input_entries:
        entry.delete(0, tk.END)
    for entry in skill_entries.values():
        entry.delete(0, tk.END)
    for entry in skill_levels_entries.values():
        entry.delete(0, tk.END)
    ayd_image_label.config(image='', text="No icon") 
    rank_label.config(image='', text="None")

def process_ez_with_yokai(ez_path):
    abs_exe_path = os.path.abspath(YOKAI_EXE_PATH)
    exe_folder = os.path.dirname(abs_exe_path) or "."
    zip_path = ez_path.rsplit('.', 1)[0] + '.zip'
    
    if os.path.exists(zip_path):
        try: os.remove(zip_path)
        except: pass

    try:
        subprocess.run([abs_exe_path, ez_path], shell=False, check=True, cwd=exe_folder)
    except Exception as e:
        print(f"Error yokai.exe: {e}")

    return zip_path if os.path.exists(zip_path) else None

def toggle_advanced():
    global advanced_mode_active
    advanced_mode_active = not advanced_mode_active
    if advanced_mode_active:
        advanced_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        toggle_advanced_btn.config(text="▲ Hide advanced parameters (15-38) ▲")
    else:
        advanced_frame.pack_forget()
        toggle_advanced_btn.config(text="▼ Show advanced parameters (15-38) ▼")

# ==========================================
# 3D AND IMAGE MODULES
# ==========================================
def load_ayd_icon():
    global tk_image_ref
    if found_index == -1:
        messagebox.showwarning("Error", "Please load a YoukaiId first!")
        return
        
    yokai_id = input_entries[0].get()
    root_png_file = os.path.abspath(os.path.join(RESOURCES_FOLDER, f"bl_{yokai_id}.png"))
    ayd_file = os.path.abspath(os.path.join(RESOURCES_FOLDER, f"{yokai_id}.ayd"))
    png_data = None

    try:
        if os.path.exists(root_png_file):
            with open(root_png_file, "rb") as f:
                png_data = f.read()
        elif os.path.exists(ayd_file):
            with zipfile.ZipFile(ayd_file, 'r') as zf:
                png_filename = next((name for name in zf.namelist() if name.lower().endswith('.png')), None)
                if png_filename:
                    png_data = zf.read(png_filename)

        if png_data:
            tk_image_ref = tk.PhotoImage(data=png_data)
            ayd_image_label.config(image=tk_image_ref, text="", width=tk_image_ref.width(), height=tk_image_ref.height())
        else:
            messagebox.showinfo("Information", f"No icon found for ID {yokai_id}.")
            ayd_image_label.config(image='', text="No icon", width=12, height=6)
            
    except Exception as e:
        messagebox.showerror("Error", f"Unable to read icon:\{e}")

def extract_ymd_geometry_texturing(ymd_data):
    positions, faces, uvs = [], [], []
    geometry_offset = -1
    for pattern in [b"geometries", b"skin"]:
        pos = ymd_data.find(pattern)
        if pos != -1:
            geometry_offset = pos - 8
            break

    if geometry_offset == -1: return None, None, None
    data = io.BytesIO(ymd_data)
    data.seek(geometry_offset)

    try:
        meshes_count = struct.unpack("<i", data.read(4))[0]
        vertex_offset = 0
        for _ in range(meshes_count):
            mesh_length_name = struct.unpack("<i", data.read(4))[0]
            if mesh_length_name == 1:
                data.read(4); name_len = struct.unpack("<i", data.read(4))[0]
                data.read(name_len); data.read(4)
            else:
                data.read(mesh_length_name); data.read(12)
                name_len = struct.unpack("<i", data.read(4))[0]
                data.read(name_len); data.read(4)

            num_vertices = struct.unpack('<i', data.read(4))[0]
            if num_vertices > 0:
                for _ in range(num_vertices):
                    positions.append(list(struct.unpack("<3f", data.read(12))))
                    data.read(12)
                    u, v = struct.unpack("<2f", data.read(8))
                    uvs.append([u, v])

                skinning_count = struct.unpack('<i', data.read(4))[0]
                if skinning_count > 0:
                    for i in range(0, skinning_count, 3):
                        if i + 2 < num_vertices:
                            faces.append([i + vertex_offset, i + 1 + vertex_offset, i + 2 + vertex_offset])
                    data.seek(data.tell() + skinning_count * 4)
                vertex_offset += num_vertices
    except struct.error: pass
    except Exception as e: print(f"Geometry warning: {e}")

    return positions, faces, uvs

def visualize_3d_model():
    if found_index == -1: return
    yokai_id = input_entries[0].get()
    ayd_file = os.path.abspath(os.path.join(RESOURCES_FOLDER, f"{yokai_id}.ayd"))
    ez_file = os.path.abspath(os.path.join(RESOURCES_FOLDER, f"{yokai_id}.ez"))
    generated_zip_path, ymd_data, png_data = None, None, None

    try:
        if os.path.exists(ayd_file):
            with zipfile.ZipFile(ayd_file, 'r') as zf:
                files = zf.namelist()
                ymd_candidates = [f for f in files if f.lower().endswith('.ymd')]
                if not ymd_candidates:
                    ez_name = next((f for f in files if f.lower().endswith('.ez')), None)
                    if ez_name:
                        temp_ez = os.path.join(os.path.dirname(os.path.abspath(YOKAI_EXE_PATH)), f"temp_{yokai_id}.ez")
                        with open(temp_ez, "wb") as f: f.write(zf.read(ez_name))
                        generated_zip_path = process_ez_with_yokai(temp_ez)
                        if generated_zip_path:
                            with zipfile.ZipFile(generated_zip_path, 'r') as zf_d:
                                all_files = zf_d.namelist()
                                ymd_cands = [f for f in all_files if f.lower().endswith('.ymd')]
                                png_cands = [f for f in all_files if f.lower().endswith('.png')]
                                if ymd_cands: ymd_data = zf_d.read(max(ymd_cands, key=lambda f: zf_d.getinfo(f).file_size))
                                if png_cands: png_data = zf_d.read(max(png_cands, key=lambda f: zf_d.getinfo(f).file_size))
                        os.remove(temp_ez)
                else:
                    ymd_data = zf.read(max(ymd_candidates, key=lambda f: zf.getinfo(f).file_size))
                    png_candidates = [f for f in files if f.lower().endswith('.png')]
                    if png_candidates: png_data = zf.read(max(png_candidates, key=lambda f: zf.getinfo(f).file_size))

        elif os.path.exists(ez_file):
            generated_zip_path = process_ez_with_yokai(ez_file)
            if generated_zip_path:
                with zipfile.ZipFile(generated_zip_path, 'r') as zf:
                    all_files = zf.namelist()
                    ymd_cands = [f for f in all_files if f.lower().endswith('.ymd')]
                    png_cands = [f for f in all_files if f.lower().endswith('.png')]
                    if ymd_cands: ymd_data = zf_d.read(max(ymd_cands, key=lambda f: zf.getinfo(f).file_size))
                    if png_cands: png_data = zf_d.read(max(png_cands, key=lambda f: zf.getinfo(f).file_size))
        else:
            messagebox.showwarning("Not Found", f"No 3D file (AYD or EZ) found for ID {yokai_id}.")
            return

        if generated_zip_path and os.path.exists(generated_zip_path): os.remove(generated_zip_path)
        if not ymd_data:
            messagebox.showerror("Error", "No geometry found.")
            return
            
        positions, faces, uvs = extract_ymd_geometry_texturing(ymd_data)
        if not positions:
            messagebox.showerror("Error", "Geometry unreadable or corrupted.")
            return

        mesh = o3d.geometry.TriangleMesh()
        mesh.vertices = o3d.utility.Vector3dVector(np.array(positions, dtype=np.float64))
        mesh.triangles = o3d.utility.Vector3iVector(np.array(faces, dtype=np.int32))
        
        if png_data and uvs:
            img = Image.open(io.BytesIO(png_data)).convert('RGB')
            mesh.textures = [o3d.geometry.Image(np.asarray(img))]
            triangle_uvs = np.zeros((len(faces) * 3, 2))
            for i, face in enumerate(faces):
                triangle_uvs[i*3:i*3+3] = [uvs[face[0]], uvs[face[1]], uvs[face[2]]]
            mesh.triangle_uvs = o3d.utility.Vector2dVector(triangle_uvs)
            mesh.triangle_material_ids = o3d.utility.IntVector([0] * len(faces))
        else:
            mesh.paint_uniform_color([0.8, 0.8, 0.8])
            
        mesh.compute_vertex_normals()
        o3d.visualization.draw_geometries([mesh], window_name=f"3D Viewer - Yo-kai ID: {yokai_id}")

    except Exception as e:
        messagebox.showerror("Fatal Error", str(e))
        if generated_zip_path and os.path.exists(generated_zip_path):
            try: os.remove(generated_zip_path)
            except: pass

# ==========================================
# DATABASE FUNCTIONS
# ==========================================
def load_file():
    global yokai_lines
    raw_text, _ = read_file_data(DB_FILE)
    if raw_text:
        yokai_lines = raw_text.split('*')
        print(f"Yo-kai database loaded ({len(yokai_lines)} entries).")

def load_skills():
    global skills_dict
    raw_text, _ = read_file_data(SKILL_DB_FILE)
    if raw_text:
        skill_lines = raw_text.split('*')
        for line in skill_lines:
            columns = line.split('|')
            if len(columns) >= 4:
                yokai_id = columns[0]
                skills_dict[yokai_id] = {
                    "Name": columns[1], "TypeID": columns[2], "Description": columns[3],
                    "Property1": columns[4] if len(columns) > 4 else "0",
                    "Property2": columns[5] if len(columns) > 5 else "0",
                    "Anim3D": columns[6] if len(columns) > 6 else "",
                    "Anim2D": columns[7] if len(columns) > 7 else ""
                }
        print(f"Soultimates database loaded ({len(skills_dict)} skills).")

def load_skill_levels():
    global skill_levels_dict
    raw_text, _ = read_file_data(SKILL_LEVEL_DB_FILE)
    if raw_text:
        lines = raw_text.split('*')
        for line in lines:
            columns = line.split('|')
            if len(columns) >= 13:
                yokai_id = columns[0]
                level = columns[1]
                if yokai_id not in skill_levels_dict:
                    skill_levels_dict[yokai_id] = {}
                skill_levels_dict[yokai_id][level] = columns
        print(f"Skill Levels database loaded ({len(skill_levels_dict)} Yo-kai configured).")

def classify_yokai(youkai_id):
    try:
        id_val = int(youkai_id)
        if 8000 <= id_val < 9000: return "Playable"
        elif 9000 <= id_val < 10000: return "Boss"
        else: return "Other"
    except: return "Unknown"

def advanced_search():
    global res_window 
    criterion = search_combo.get()
    val = search_entry_adv.get().strip().lower()
    
    if res_window is not None and res_window.winfo_exists(): res_window.destroy()
    if not val or criterion not in SEARCH_INDEX: return
        
    col_index = SEARCH_INDEX[criterion]
    results = []
    
    for line in yokai_lines:
        columns = line.split('|')
        yokai_id = columns[0] 
        
        if col_index == "SOULT":
            if yokai_id in skills_dict:
                if skills_dict[yokai_id]["TypeID"] == val:
                    cat = classify_yokai(yokai_id)
                    results.append(f"[{cat}] ID: {yokai_id} - Name: {columns[1]}")
            continue 
        
        if len(columns) <= col_index: continue
        
        if col_index == 1:
            jap_name = columns[1].lower()
            reading_name = columns[31].lower() if len(columns) > 31 else ""
            if val in jap_name or val in reading_name:
                cat = classify_yokai(yokai_id)
                results.append(f"[{cat}] ID: {yokai_id} - Name: {columns[1]}")
        else:
            if columns[col_index].strip().lower() == val:
                cat = classify_yokai(yokai_id)
                results.append(f"[{cat}] ID: {yokai_id} - Name: {columns[1]}")
                
    if not results:
        messagebox.showwarning("Not Found", "No results found for this search.")
        return

    res_window = tk.Toplevel(window)
    res_window.title(f"Results ({len(results)})")
    res_window.geometry("400x300")
    tk.Label(res_window, text="Double-click to load this Yo-kai", font=("Arial", 9, "italic")).pack(pady=5)
    listbox = tk.Listbox(res_window, font=("Arial", 10))
    listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    
    for res in results: listbox.insert(tk.END, res)
        
    def load_selected_id(event):
        selection = listbox.curselection()
        if selection:
            try:
                isolated_id = listbox.get(selection[0]).split("ID: ")[1].split(" - ")[0]
                search_entry_id.delete(0, tk.END)
                search_entry_id.insert(0, isolated_id)
                load_yokai_by_id()
                res_window.destroy()
            except IndexError: 
                pass
                
    listbox.bind("<Double-Button-1>", load_selected_id)

def load_yokai_by_id():
    global found_index, previous_level
    search_id = search_entry_id.get().strip()
    
    for i, line in enumerate(yokai_lines):
        columns = line.split('|')
        if columns[0] == search_id:
            found_index = i
            fill_entries(columns)
            
            current_level_var.set("1") 
            previous_level = "1"
            display_level_data(from_code=True)
            
            load_ayd_icon()
            return 

    clear_interface()
    messagebox.showwarning("Not Found", "No Yo-kai has this YoukaiId.")

def get_latest_id():
    max_id = max([int(l.split('|')[0]) for l in yokai_lines if l.split('|')[0].isdigit()], default=0)
    messagebox.showinfo("Available ID", f"💡 Next available ID: {max_id + 1}")

def fill_entries(columns):
    global rank_image_ref 
    
    yokai_id = columns[0]

    for col_index, entry in enumerate(input_entries):
        entry.delete(0, tk.END)
        if col_index < len(columns):
            entry.insert(0, columns[col_index])

    for entry in skill_entries.values():
        entry.delete(0, tk.END)

    if yokai_id in skills_dict:
        skill = skills_dict[yokai_id]
        skill_entries["Name"].insert(0, skill["Name"])
        skill_entries["Description"].insert(0, skill["Description"])
        skill_entries["Property1"].insert(0, skill["Property1"])
        skill_entries["Property2"].insert(0, skill["Property2"])
        skill_entries["Anim3D"].insert(0, skill["Anim3D"])
        skill_entries["Anim2D"].insert(0, skill["Anim2D"])
        
        type_id = skill["TypeID"]
        if type_id in SOULT_TYPES:
            soult_type_combo.set(f"{type_id} - {SOULT_TYPES[type_id]}")
        else:
            soult_type_combo.set(f"{type_id} - Unknown")

    if len(columns) > 3:
        rarity_val = columns[3]
        
        if rarity_val in RANK_COORDINATES:
            try:
                full_img = Image.open(SPRITESHEET_PATH)
                total_w, total_h = full_img.size
                
                cell_w = total_w // 8
                cell_h = total_h // 3
                
                col, row = RANK_COORDINATES[rarity_val]
                
                left = col * cell_w
                top = row * cell_h
                right = left + cell_w
                bottom = top + cell_h
                
                cropped_img = full_img.crop((left, top, right, bottom))
                rank_image_ref = ImageTk.PhotoImage(cropped_img)
                
                rank_label.config(image=rank_image_ref, text="")
                
            except Exception as e:
                print(f"Error with spritesheet: {e}")
                rank_label.config(image='', text=f"Rarity ID: {rarity_val}")
        else:
            rank_label.config(image='', text="None")

def display_level_data(event=None, from_code=False):
    global previous_level
    yokai_id = input_entries[0].get()
    if not yokai_id: return
    
    if not from_code:
        if yokai_id not in skill_levels_dict:
            skill_levels_dict[yokai_id] = {}
            
        lvl_cols = ["" for _ in range(13)]
        lvl_cols[0] = yokai_id
        lvl_cols[1] = previous_level
        for col_idx, entry in skill_levels_entries.items():
            lvl_cols[col_idx] = entry.get()
        skill_levels_dict[yokai_id][previous_level] = lvl_cols
    
    chosen_level = current_level_var.get()
    for entry in skill_levels_entries.values():
        entry.delete(0, tk.END)
        
    if yokai_id in skill_levels_dict and chosen_level in skill_levels_dict[yokai_id]:
        level_data = skill_levels_dict[yokai_id][chosen_level]
        for col_idx, entry in skill_levels_entries.items():
            if col_idx < len(level_data):
                entry.insert(0, level_data[col_idx])
                
    previous_level = chosen_level

# ==========================================
# SAVE AND LOAD MODS FUNCTIONS
# ==========================================
def open_save_menu():
    yokai_id = input_entries[0].get().strip()
    if not yokai_id:
        messagebox.showerror("Error", "Please define a YoukaiId first (field 0).")
        return

    if yokai_id not in skill_levels_dict:
        skill_levels_dict[yokai_id] = {}
        
    current_lvl = current_level_var.get()
    lvl_cols = ["" for _ in range(13)]
    lvl_cols[0] = yokai_id
    lvl_cols[1] = str(current_lvl)
    for idx, entry in skill_levels_entries.items():
        lvl_cols[idx] = entry.get()
    skill_levels_dict[yokai_id][str(current_lvl)] = lvl_cols

    menu_win = tk.Toplevel(window)
    menu_win.title("Global Save Options")
    menu_win.geometry("400x180")
    
    tk.Label(menu_win, text=f"Save Yo-kai {yokai_id} Data", font=("Arial", 11, "bold")).pack(pady=10)
    
    tk.Button(menu_win, text="💾 Save to Original Master Tables (Overwrite)", bg="#f8d7da", command=lambda: execute_save(yokai_id, "original", menu_win)).pack(fill=tk.X, padx=20, pady=5)
    tk.Button(menu_win, text="📁 Export to Mod Folder (Isolated)", bg="#d4edda", command=lambda: execute_save(yokai_id, "isolated", menu_win)).pack(fill=tk.X, padx=20, pady=5)

def execute_save(yokai_id, mode, menu_win):
    menu_win.destroy()
    
    # Remove trailing empty entries
    yokai_values = [entry.get() for entry in input_entries]
    while len(yokai_values) > 35 and yokai_values[-1] == "":
        yokai_values.pop()
    yokai_line = "|".join(yokai_values)
    
    selected_type = soult_type_combo.get()
    type_id = selected_type.split(" - ")[0] if " - " in selected_type else "-1"
    skill_line = "|".join([
        yokai_id,
        skill_entries["Name"].get(),
        type_id,
        skill_entries["Description"].get(),
        skill_entries["Property1"].get(),
        skill_entries["Property2"].get(),
        skill_entries["Anim3D"].get(),
        skill_entries["Anim2D"].get()
    ])
    
    level_lines = []
    base_lvl_data = skill_levels_dict.get(yokai_id, {}).get(current_level_var.get(), [""]*13)
    
    for lvl in range(1, 8):
        lvl_str = str(lvl)
        if yokai_id in skill_levels_dict and lvl_str in skill_levels_dict[yokai_id]:
            data = skill_levels_dict[yokai_id][lvl_str]
        else:
            data = list(base_lvl_data) 
            data[1] = lvl_str
            
        while len(data) < 13: data.append("") 
        data[0] = yokai_id
        level_lines.append("|".join(data))
    
    if mode == "isolated":
        parent_folder = filedialog.askdirectory(title="Choose Destination Folder for Mod")
        if not parent_folder: return
        
        mod_path = os.path.join(parent_folder, f"Yokai_{yokai_id}")
        os.makedirs(mod_path, exist_ok=True)
        
        try:
            with open(os.path.join(mod_path, "ywp_mst_youkai.json"), "w", encoding="utf-8") as f:
                json.dump({"tableData": yokai_line, "version": "1"}, f, ensure_ascii=False, indent=4)
            with open(os.path.join(mod_path, "ywp_mst_youkai_skill.json"), "w", encoding="utf-8") as f:
                json.dump({"tableData": skill_line, "version": "1"}, f, ensure_ascii=False, indent=4)
            with open(os.path.join(mod_path, "ywp_mst_youkai_skill_level.json"), "w", encoding="utf-8") as f:
                json.dump({"tableData": "*".join(level_lines), "version": "1"}, f, ensure_ascii=False, indent=4)
                
            messagebox.showinfo("Success", f"Mod folder successfully created in:{mod_path}")
        except Exception as e:
            messagebox.showerror("Mod Error", str(e))
            
    elif mode == "original":
        try:
            def update_orig(file_path, new_lines):
                raw_text, orig_json = read_file_data(file_path)
                existing = raw_text.split('*') if raw_text else []
                filtered = [l for l in existing if not l.startswith(yokai_id + "|")]
                
                if isinstance(new_lines, list):
                    filtered.extend(new_lines)
                else:
                    filtered.append(new_lines)
                    
                new_text = "*".join(filtered)
                
                with open(file_path, "w", encoding="utf-8") as f:
                    if orig_json is not None:
                        if "tableData" in orig_json:
                            orig_json["tableData"] = new_text
                        else:
                            orig_json["masterData"] = new_text
                        json.dump(orig_json, f, ensure_ascii=False, indent=4)
                    else:
                        f.write(new_text)

            update_orig(DB_FILE, yokai_line)
            update_orig(SKILL_DB_FILE, skill_line)
            update_orig(SKILL_LEVEL_DB_FILE, level_lines)
            
            load_file()
            load_skills()
            load_skill_levels()
            messagebox.showinfo("Success", f"The 3 original master tables were updated for ID {yokai_id}!")
        except Exception as e:
            messagebox.showerror("Original DB Error", str(e))
          
def save_skill_as():
    if found_index == -1:
        messagebox.showerror("Error", "No Yo-kai loaded!")
        return
        
    yokai_id = input_entries[0].get()
    soult_id = yokai_id  
    
    selected_type = soult_type_combo.get()
    type_id = selected_type.split(" - ")[0] if " - " in selected_type else "-1"
    
    new_line = "|".join([
        soult_id,
        skill_entries["Name"].get(),
        type_id,
        skill_entries["Description"].get(),
        skill_entries["Property1"].get(),
        skill_entries["Property2"].get(),
        skill_entries["Anim3D"].get(),
        skill_entries["Anim2D"].get()
    ])
    
    save_path = filedialog.asksaveasfilename(
        defaultextension=".json",
        initialfile="ywp_mst_skill_mod.json",
        title="Save Database As...",
        filetypes=[("JSON Files", "*.json"), ("Text Files", "*.txt"), ("All Files", "*.*")]
    )
    
    if not save_path:
        return
    
    try:
        raw_text, orig_json = read_file_data(SKILL_DB_FILE)
        lines = raw_text.split('*') if raw_text else []
        modified = False
        for i, line in enumerate(lines):
            if line.startswith(soult_id + "|"):
                lines[i] = new_line
                modified = True
                break
                
        if not modified:
            lines.append(new_line)
            
        new_text = "*".join(lines)
        
        with open(save_path, "w", encoding="utf-8") as f:
            if save_path.endswith('.json') or orig_json is not None:
                final_data = orig_json if orig_json else {"tableData": new_text, "version": "1"}
                if "tableData" in final_data:
                    final_data["tableData"] = new_text
                else:
                    final_data["masterData"] = new_text
                json.dump(final_data, f, ensure_ascii=False, indent=4)
            else:
                f.write(new_text)
            
        messagebox.showinfo("Success", f"File saved successfully under:{save_path}")
    except Exception as e:
        messagebox.showerror("Save Error", str(e))

def load_mod_folder():
    global found_index, previous_level
    mod_folder = filedialog.askdirectory(title="Select Mod Folder to Load")
    if not mod_folder: return

    yokai_file = find_file("ywp_mst_youkai", mod_folder)
    skill_file = find_file("ywp_mst_youkai_skill", mod_folder)
    lvl_file = find_file("ywp_mst_youkai_skill_level", mod_folder)

    if not yokai_file:
        messagebox.showerror("Error", "The ywp_mst_youkai file (JSON or TXT) was not found in this folder.")
        return

    try:
        yokai_text, _ = read_file_data(yokai_file)
        if yokai_text:
            columns = yokai_text.split('|')
            yokai_id = columns[0]

        if skill_file:
            skill_text, _ = read_file_data(skill_file)
            if skill_text:
                skill_cols = skill_text.split('|')
                if len(skill_cols) >= 4:
                    skills_dict[yokai_id] = {
                        "Name": skill_cols[1], "TypeID": skill_cols[2],
                        "Description": skill_cols[3],
                        "Property1": skill_cols[4] if len(skill_cols) > 4 else "0",
                        "Property2": skill_cols[5] if len(skill_cols) > 5 else "0",
                        "Anim3D": skill_cols[6] if len(skill_cols) > 6 else "",
                        "Anim2D": skill_cols[7] if len(skill_cols) > 7 else ""
                    }

        if lvl_file:
            lvl_text, _ = read_file_data(lvl_file)
            if lvl_text:
                lvl_lines = lvl_text.split('*')
                skill_levels_dict[yokai_id] = {}
                for l in lvl_lines:
                    cols = l.split('|')
                    if len(cols) >= 13:
                        skill_levels_dict[yokai_id][cols[1]] = cols

        search_entry_id.delete(0, tk.END)
        search_entry_id.insert(0, yokai_id)
        
        found_index = -1
        for i, line in enumerate(yokai_lines):
            if line.startswith(yokai_id + "|"):
                found_index = i
                break
                
        fill_entries(columns)
        
        current_level_var.set("1") 
        previous_level = "1"
        display_level_data(from_code=True)
        
        load_ayd_icon()
        messagebox.showinfo("Success", f"Mod for Yo-kai {yokai_id} loaded successfully into the editor!")

    except Exception as e:
        messagebox.showerror("Error", f"Error while loading Mod:\n{e}")

# --- GRAPHICAL USER INTERFACE ---
window = tk.Tk()
window.title("Puni MST Tool")
window.geometry("1050x800")
window.withdraw() 

# --- TOP PANEL ---
top_frame = tk.Frame(window, padx=10, pady=10)
top_frame.pack(fill=tk.X)

left_frame = tk.Frame(top_frame)
left_frame.pack(side=tk.LEFT)
tk.Label(left_frame, text="🔍 Filter:").grid(row=0, column=0, sticky="e")
search_combo = ttk.Combobox(left_frame, values=list(SEARCH_INDEX.keys()), width=20, state="readonly")
search_combo.current(0)
search_combo.grid(row=0, column=1)
search_entry_adv = tk.Entry(left_frame, width=12)
search_entry_adv.grid(row=0, column=2, padx=5)
tk.Button(left_frame, text="Go", command=advanced_search).grid(row=0, column=3, sticky="w")

tk.Label(left_frame, text="⚙️ Load ID:").grid(row=1, column=0, sticky="e", pady=5)
search_entry_id = tk.Entry(left_frame, width=15)
search_entry_id.grid(row=1, column=1, pady=5)
tk.Button(left_frame, text="Load", bg="#cce5ff", command=load_yokai_by_id).grid(row=1, column=2, columnspan=2, sticky="w", padx=5)

right_frame = tk.Frame(top_frame, bd=2, relief=tk.GROOVE, padx=10, pady=5, bg="#f0f0f0")
right_frame.pack(side=tk.RIGHT, fill=tk.Y)
icon_frame = tk.Frame(right_frame, bg="#f0f0f0")
icon_frame.pack(side=tk.LEFT, padx=(0, 10))

img_and_rank_frame = tk.Frame(icon_frame, bg="#f0f0f0")
img_and_rank_frame.pack()

ayd_image_label = tk.Label(img_and_rank_frame, text="No icon", bg="#e0e0e0", relief=tk.SUNKEN, width=12, height=6)
ayd_image_label.pack(side=tk.LEFT)

rank_label = tk.Label(img_and_rank_frame, text="", font=("Arial", 16, "bold"), fg="#ff9900", bg="#f0f0f0")
rank_label.pack(side=tk.LEFT, padx=5)

tk.Button(icon_frame, text="🖼️ Load Icon", font=("Arial", 8), command=load_ayd_icon).pack(pady=2)

right_btns_frame = tk.Frame(right_frame, bg="#f0f0f0")
right_btns_frame.pack(side=tk.RIGHT)
tk.Label(right_btns_frame, text="📦 Resources", font=("Arial", 10, "bold"), bg="#f0f0f0").pack()
tk.Button(right_btns_frame, text="👁️ 3D Model", bg="#d4edda", font=("Arial", 9, "bold"), command=visualize_3d_model).pack(pady=5, fill=tk.X)
tk.Button(right_btns_frame, text="💡 Next Free ID", command=get_latest_id, bg="#fff3cd").pack(fill=tk.X)
tk.Button(right_btns_frame, text="💾 Yo-kai (Global)", bg="#add8e6", font=("Arial", 9, "bold"), command=open_save_menu).pack(pady=5, fill=tk.X)
tk.Button(right_btns_frame, text="📂 Load Mod Folder", command=load_mod_folder, bg="#e2e3e5", font=("Arial", 9, "bold")).pack(pady=5, fill=tk.X)
tk.Button(right_btns_frame, text="⚙️ Change Folders (Config)", command=change_folders, bg="#f8d7da", font=("Arial", 9, "bold")).pack(pady=5, fill=tk.X)

tk.Frame(window, height=2, bd=1, relief=tk.SUNKEN).pack(fill=tk.X, padx=10)

# --- CENTRAL SCROLLABLE AREA ---
middle_frame = tk.Frame(window)
middle_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

canvas = tk.Canvas(middle_frame)
scrollbar = ttk.Scrollbar(middle_frame, orient="vertical", command=canvas.yview)
scrollable_frame = tk.Frame(canvas)

scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)
canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# --- UI: BASIC ELEMENTS (0 to 14) ---
basic_frame = tk.Frame(scrollable_frame)
basic_frame.pack(fill=tk.X, padx=5, pady=5)

for i in range(15):
    row = i // 2 
    col = (i % 2) * 2 
    tk.Label(basic_frame, text=YOKAI_FIELDS[i], font=("Arial", 9)).grid(row=row, column=col, sticky="e", padx=(10, 5), pady=5)
    entry = tk.Entry(basic_frame, width=35)
    entry.grid(row=row, column=col+1, padx=5, pady=5)
    input_entries.append(entry)

# --- UI: SOULTIMATE (SKILLS) ---
skills_frame = tk.LabelFrame(scrollable_frame, text="✨ Soultimate (Skill)", font=("Arial", 10, "bold"), bg="#fff9e6", padx=10, pady=10)
skills_frame.pack(fill=tk.X, padx=10, pady=10)

skill_field_names = ["Name", "Description", "Property1", "Property2", "Anim3D", "Anim2D"]

tk.Label(skills_frame, text="Type (SoultType):", font=("Arial", 9), bg="#fff9e6").grid(row=0, column=0, sticky="e", padx=(10, 5), pady=5)
soult_type_combo = ttk.Combobox(skills_frame, values=[f"{k} - {v}" for k, v in SOULT_TYPES.items()], width=32, state="readonly")
soult_type_combo.grid(row=0, column=1, padx=5, pady=5)
skill_entries["TypeID"] = soult_type_combo

for i, field_name in enumerate(skill_field_names):
    row = (i + 2) // 2 
    col = ((i + 2) % 2) * 2
    tk.Label(skills_frame, text=field_name + ":", font=("Arial", 9), bg="#fff9e6").grid(row=row, column=col, sticky="e", padx=(10, 5), pady=5)
    entry = tk.Entry(skills_frame, width=35)
    entry.grid(row=row, column=col+1, padx=5, pady=5)
    skill_entries[field_name] = entry

tk.Button(skills_frame, text="💾 Save Soultimate As... (Optional)", bg="#cce5ff", font=("Arial", 9, "bold"), command=save_skill_as).grid(row=5, column=0, columnspan=4, pady=15)

# --- UI: SOULTIMATE LEVELS (SKILL LEVELS) ---
skill_levels_frame = tk.LabelFrame(scrollable_frame, text="📊 Soultimate Levels", font=("Arial", 10, "bold"), bg="#e6f2ff", padx=10, pady=10)
skill_levels_frame.pack(fill=tk.X, padx=10, pady=10)

current_level_var = tk.StringVar(value="1")

tk.Label(skill_levels_frame, text="Select Level:", font=("Arial", 9, "bold"), bg="#e6f2ff").grid(row=0, column=0, sticky="e", padx=5, pady=5)
skill_level_combo = ttk.Combobox(skill_levels_frame, textvariable=current_level_var, values=[str(i) for i in range(1, 8)], width=10, state="readonly")
skill_level_combo.grid(row=0, column=1, sticky="w", padx=5, pady=5)

skill_level_combo.bind("<<ComboboxSelected>>", display_level_data)

level_fields = [
    ("DisplayName", 2),
    ("Unk0 (Gauge Speed?)", 3),
    ("SoultPt (Power/Points)", 4),
    ("MaxUseCount", 5),
    ("SoultStatsDict (Stats Dict)", 11),
    ("Unk1", 6), ("Unk2", 7), ("Unk3", 8), 
    ("Unk4", 9), ("Unk5", 10), ("Unk7 (Double)", 12)
]

for i, (field_name, col_idx) in enumerate(level_fields):
    row = (i // 2) + 1
    col = (i % 2) * 2
    tk.Label(skill_levels_frame, text=f"{field_name}:", font=("Arial", 9), bg="#e6f2ff").grid(row=row, column=col, sticky="e", padx=(10, 5), pady=2)
    entry = tk.Entry(skill_levels_frame, width=35)
    entry.grid(row=row, column=col+1, padx=5, pady=2)
    skill_levels_entries[col_idx] = entry

# --- UI: BUTTON AND ADVANCED ELEMENTS (15 to 38) ---
toggle_advanced_btn = tk.Button(scrollable_frame, text="▼ Show advanced parameters (15-38) ▼", command=toggle_advanced, bg="#e2e3e5", font=("Arial", 9, "bold"))
toggle_advanced_btn.pack(pady=10)

advanced_frame = tk.Frame(scrollable_frame)

for i in range(15, len(YOKAI_FIELDS)):
    row = (i - 15) // 2
    col = ((i - 15) % 2) * 2 
    tk.Label(advanced_frame, text=YOKAI_FIELDS[i], font=("Arial", 9)).grid(row=row, column=col, sticky="e", padx=(10, 5), pady=5)
    entry = tk.Entry(advanced_frame, width=35)
    entry.grid(row=row, column=col+1, padx=5, pady=5)
    input_entries.append(entry)

# --- INITIALIZATION AND LAUNCH ---
def start_tool():
    if load_config():
        return True
    else:
        if initialize_tools(at_startup=True) and initialize_version_folder(at_startup=True):
            save_config()
            return True
    return False

if __name__ == "__main__":
    if start_tool():
        load_file()
        load_skills()
        load_skill_levels()
        window.deiconify() 
        window.mainloop()