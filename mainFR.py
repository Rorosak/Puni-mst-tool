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

# --- PARAMÈTRES ET VARIABLES GLOBALES ---
FICHIER_CONFIG = "config.json" 

# --- PARAMÈTRES ET VARIABLES GLOBALES ---
# Ces variables seront remplies dynamiquement au lancement
FICHIER_DB = ""
FICHIER_SKILL_DB = ""
FICHIER_SKILL_LEVEL_DB = ""
DOSSIER_RESSOURCES = ""

# Ces outils restent liés à ton dossier d'installation du logiciel
CHEMIN_YOKAI_EXE = ""
CHEMIN_SPRITESHEET = ""

COORDONNEES_RANGS = {
    "1": (2, 0), "2": (3, 0), "3": (4, 0), "4": (5, 0),
    "5": (6, 0), "6": (7, 0), "7": (0, 1), "8": (2, 1),
    "9": (4, 1), "10": (6, 1), "11": (0, 2), "12": (2, 2)
}

image_rang_reference = None 
dictionnaire_skill_levels = {} 
cases_skill_levels = {}
niveau_actuel_var = None 
niveau_precedent = "1"
donnees_json = {}
lignes_yokai = []
dictionnaire_skills = {}
index_trouve = -1
cases_entrees = []
cases_skills = {}
image_tk_reference = None 
fenetre_res = None 
mode_avance_actif = False

SOULT_TYPES = {
    "-1": "None", "1": "RangePopper", "2": "SummonOtherPuni", "3": "RandomPopper",
    "4": "Inflator", "5": "Hider", "7": "PuniRearranger", "8": "BallMaker",
    "9": "Healer", "11": "Befriender", "12": "ExpBooster", "13": "MoneyBooster",
    "14": "ItemDropBooster", "15": "AttackBooster", "16": "ScoreBooster",
    "17": "DefenseBooster", "18": "Stunner", "20": "DirectAttacker",
    "22": "MultipleAreaPopper", "23": "BonusBallsMaker", "24": "AttackBoosterAndHeal",
    "25": "AttackerAndStunner", "26": "InflatorBetter", "27": "CrossAreaPopper",
    "28": "AttackerAndHealer", "29": "BallMakerAndRecoverHp", "30": "Tracer", 
    "31": "AttackerAndHPScaling", "32": "PopperDissapear", "33": "SingleAttackerAndBefriender", 
    "34": "AttackerLuckScaling", "35": "AttackerScalingOnPuni", "36": "AllPopperHealerScalingOnPuni",
    "37": "AttackerScalingUnity", "38": "RandomPopperScaling", "39": "TimeStopperDamage", 
    "40": "AttackAndFeverBooster", "41": "NoFillerTracer", "42": "FeverAndSoultGaugeBooster", 
    "43": "HealerAndSoultBooster", "44": "Slasher", "45": "PopperAndFeverCharger", 
    "46": "BonusBallClearer", "47": "ReflectingBeam", "48": "TapSlasher", 
    "49": "OwnPuniEraserAndOrganizer", "50": "BlackholeFeverBooster", "51": "PuniTransformerAndSoultBooster", 
    "52": "RowClearerBonusBallMaker", "53": "TapClearArea", "54": "ConnectPopper", 
    "55": "AttackBoosterAndInflator", "56": "TraceEraserTime", "57": "TreasureDropper", 
    "58": "TapAreaClearer", "59": "OrganizeLinkDamageScaling", "60": "Beyblade", 
    "61": "AttackBoosterAndDamageReducer", "62": "ThreeDirectionSlasher", "63": "TapGiantPuniAndClear", 
    "64": "DirectAttackerFeverScaling", "65": "AllPopperAndStunner", "66": "ExtremePopper"
}

FOOD_TYPES = {
    "1": "RiceBalls", "2": "Sandwiches", "3": "Sweets", "4": "Chocobars",
    "5": "Milk", "6": "Juice", "7": "Burgers", "8": "Ramen",
    "9": "ChineseFood", "10": "Vegetables", "11": "Meat", "12": "Seafood",
    "13": "Sushi", "14": "Curry", "15": "Dessert", "16": "Oden",
    "17": "ZarusobaNoodles", "18": "Chips", "19": "IceCream"
}

CHAMPS_YOKAI = [
    "0: YoukaiId", "1: YoukaiName", "2: YoukaiType", "3: YoukaiRarity", "4: YoukaiKind",
    "5: LevelType", "6: FoodType", "7: MaxLevel", "8: BaseHp", "9: MaxHp",
    "10: BaseAtk", "11: MaxAtk", "12: EvolutionYoukaiId", "13: EvolutionLevel", "14: DictionaryId",
    "15: YoukaiDescription", "16: TextPuzzle", "17: TextGasha", "18: TextMission", "19: TextGift",
    "20: UnusedName", "21: SkillEffectColorR", "22: SkillEffectColorG", "23: SkillEffectColorB", "24: ScaleBattleFriend",
    "25: ScaleBattleEnemy", "26: YoukaiSize", "27: Width", "28: Height", "29: X",
    "30: Y", "31: ReadingName", "32: FriendOffsetX", "33: FriendOffsetY", "34: EffectType",
    "35: OpenDt", "36: YoukaiEffectBack", "37: YoukaiEffectFront", "38: ScaleOffsetDeck"
]

INDEX_RECHERCHE = {
    "Nom du Yo-kai (1)": 1, "Rang / Rarity (3)": 3, "Tribu / Kind (4)": 4,"Nourriture / FoodType (6)": 6,
    "Dictionary ID (14)": 14, "Type Âmultime (-1 à 44)": "SOULT"
}

# ==========================================
# FONCTIONS DE LECTURE UNIVERSELLE (JSON/TXT)
# ==========================================
def trouver_fichier(nom_base, dossier):
    """Cherche un fichier d'abord en .json, puis en .txt"""
    for ext in [".json", ".txt"]:
        chemin = os.path.join(dossier, nom_base + ext)
        if os.path.exists(chemin):
            return chemin
    return None

def lire_donnees_fichier(chemin):
    """Lit un fichier, parse le JSON ou renvoie le texte brut si c'est un TXT."""
    try:
        with open(chemin, "r", encoding="utf-8") as f:
            contenu = f.read().strip()
        try:
            donnees = json.loads(contenu)
            # On cherche dynamiquement la clé de données (tableData ou masterData)
            for cle in ["tableData", "masterData"]:
                if cle in donnees:
                    return str(donnees[cle]).replace("\n", "").replace("\r", ""), donnees
            return contenu, None
        except (json.JSONDecodeError, TypeError):
            return contenu.replace("\n", "").replace("\r", ""), None
    except Exception as e:
        messagebox.showerror("Erreur de Lecture", f"Impossible de lire le fichier {chemin}:\n{e}")
        return "", None

def maj_fichier_original(chemin_fichier, nouvelles_lignes, yokai_id):
    """Met à jour le fichier d'origine en gardant le bon format JSON ou TXT, sans sauts de ligne intempestifs."""
    texte_brut, donnees_json_orig = lire_donnees_fichier(chemin_fichier)
    lignes_existantes = texte_brut.split('*') if texte_brut else []
    
    # Filtrer l'ancienne version et les lignes vides
    lignes_filtrees = [l.strip() for l in lignes_existantes if l.strip() and not l.startswith(yokai_id + "|")]
    
    if isinstance(nouvelles_lignes, list):
        lignes_filtrees.extend(nouvelles_lignes)
    else:
        lignes_filtrees.append(nouvelles_lignes)
        
    nouveau_texte = "*".join(lignes_filtrees)
    
    with open(chemin_fichier, "w", encoding="utf-8") as f:
        if donnees_json_orig is not None:
            # On conserve la clé d'origine (tableData ou masterData)
            cle_principale = "tableData" if "tableData" in donnees_json_orig else "masterData"
            donnees_json_orig[cle_principale] = nouveau_texte
            # Écriture propre du JSON sur une structure compacte ou lisible sans casser la chaîne
            json.dump(donnees_json_orig, f, ensure_ascii=False, indent=4)
        else:
            f.write(nouveau_texte)

# ==========================================
# FONCTIONS DE CONFIGURATION
# ==========================================
def charger_config():
    global CHEMIN_YOKAI_EXE, CHEMIN_SPRITESHEET, FICHIER_DB, FICHIER_SKILL_DB, FICHIER_SKILL_LEVEL_DB, DOSSIER_RESSOURCES
    if os.path.exists(FICHIER_CONFIG):
        try:
            with open(FICHIER_CONFIG, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            y_exe = config.get("CHEMIN_YOKAI_EXE", "")
            s_sheet = config.get("CHEMIN_SPRITESHEET", "")
            f_db = config.get("FICHIER_DB", "")
            s_db = config.get("FICHIER_SKILL_DB", "")
            l_db = config.get("FICHIER_SKILL_LEVEL_DB", "")
            d_res = config.get("DOSSIER_RESSOURCES", "")

            # Si les fichiers existent toujours sur le PC, on valide
            if os.path.exists(y_exe) and os.path.exists(s_sheet) and os.path.exists(f_db) and os.path.exists(s_db) and os.path.exists(l_db) and os.path.exists(d_res):
                CHEMIN_YOKAI_EXE = y_exe
                CHEMIN_SPRITESHEET = s_sheet
                FICHIER_DB = f_db
                FICHIER_SKILL_DB = s_db
                FICHIER_SKILL_LEVEL_DB = l_db
                DOSSIER_RESSOURCES = d_res
                return True
        except Exception:
            pass
    return False

def sauvegarder_config():
    config = {
        "CHEMIN_YOKAI_EXE": CHEMIN_YOKAI_EXE,
        "CHEMIN_SPRITESHEET": CHEMIN_SPRITESHEET,
        "FICHIER_DB": FICHIER_DB,
        "FICHIER_SKILL_DB": FICHIER_SKILL_DB,
        "FICHIER_SKILL_LEVEL_DB": FICHIER_SKILL_LEVEL_DB,
        "DOSSIER_RESSOURCES": DOSSIER_RESSOURCES
    }
    try:
        with open(FICHIER_CONFIG, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Erreur de sauvegarde de la configuration : {e}")

def changer_dossiers():
    global CHEMIN_YOKAI_EXE, CHEMIN_SPRITESHEET
    CHEMIN_YOKAI_EXE = ""
    CHEMIN_SPRITESHEET = ""
    
    # On force la redemande des dossiers. L'argument au_demarrage=False empêche l'outil de se fermer si on annule.
    if initialiser_outils(au_demarrage=False) and initialiser_dossier_version(au_demarrage=False):
        sauvegarder_config()
        charger_fichier()
        charger_skills()
        charger_skill_levels()
        vider_interface()
        messagebox.showinfo("Succès", "Dossiers mis à jour et bases de données rechargées !")

# ==========================================
# FONCTIONS DE DÉMARRAGE ET DE CHEMINS
# ==========================================
def initialiser_outils(au_demarrage=True):
    global CHEMIN_YOKAI_EXE, CHEMIN_SPRITESHEET
    
    dossier_outils = filedialog.askdirectory(title="1/2 : Sélectionner le dossier des Ressources/Outils (contenant yokai.exe et rankicons.png)")
    
    if not dossier_outils:
        if au_demarrage:
            messagebox.showerror("Erreur Fatale", "Aucun dossier sélectionné pour les outils. L'outil va se fermer.")
            fenetre.destroy()
        return False
        
    for racine, _, fichiers in os.walk(dossier_outils):
        if "yokai.exe" in fichiers and not CHEMIN_YOKAI_EXE:
            CHEMIN_YOKAI_EXE = os.path.join(racine, "yokai.exe")
        if "rankicons.png" in fichiers and not CHEMIN_SPRITESHEET:
            CHEMIN_SPRITESHEET = os.path.join(racine, "rankicons.png").replace("\\", "/")
            
        if CHEMIN_YOKAI_EXE and CHEMIN_SPRITESHEET:
            break
    
    fichiers_manquants = []
    if not CHEMIN_YOKAI_EXE: fichiers_manquants.append("yokai.exe")
    if not CHEMIN_SPRITESHEET: fichiers_manquants.append("rankicons.png")
    
    if fichiers_manquants:
        msg = "Les outils suivants sont introuvables dans ce dossier :\n- " + "\n- ".join(fichiers_manquants)
        messagebox.showerror("Outils Introuvables", msg)
        if au_demarrage: fenetre.destroy()
        return False
        
    return True

def initialiser_dossier_version(au_demarrage=True):
    global FICHIER_DB, FICHIER_SKILL_DB, FICHIER_SKILL_LEVEL_DB, DOSSIER_RESSOURCES
    
    dossier = filedialog.askdirectory(title="2/2 : Sélectionner le dossier de version du jeu (contenant les JSON ou TXT)")
    
    if not dossier:
        if au_demarrage:
            messagebox.showerror("Erreur Fatale", "Aucun dossier sélectionné. L'outil va se fermer.")
            fenetre.destroy()
        return False
        
    FICHIER_DB = trouver_fichier("ywp_mst_youkai", dossier)
    FICHIER_SKILL_DB = trouver_fichier("ywp_mst_youkai_skill", dossier)
    FICHIER_SKILL_LEVEL_DB = trouver_fichier("ywp_mst_youkai_skill_level", dossier)
    DOSSIER_RESSOURCES = os.path.join(dossier, "youkai")
    
    fichiers_manquants = []
    if not FICHIER_DB: fichiers_manquants.append("ywp_mst_youkai (.json ou .txt)")
    if not FICHIER_SKILL_DB: fichiers_manquants.append("ywp_mst_youkai_skill (.json ou .txt)")
    if not FICHIER_SKILL_LEVEL_DB: fichiers_manquants.append("ywp_mst_youkai_skill_level (.json ou .txt)")
    if not os.path.exists(DOSSIER_RESSOURCES): fichiers_manquants.append("Dossier 'youkai'")
    
    if fichiers_manquants:
        msg = "Les éléments suivants sont introuvables dans ce dossier :\n- " + "\n- ".join(fichiers_manquants)
        messagebox.showerror("Dossier Invalide", msg)
        if au_demarrage: fenetre.destroy()
        return False
        
    return True

# ==========================================
# FONCTIONS UTILITAIRES (INTERFACE & OUTILS)
# ==========================================
def vider_interface():
    global index_trouve
    index_trouve = -1
    for case in cases_entrees:
        case.delete(0, tk.END)
    for case in cases_skills.values():
        case.delete(0, tk.END)
    for case in cases_skill_levels.values():
        case.delete(0, tk.END)
    label_image_ayd.config(image='', text="Aucune icône") 
    label_rang.config(image='', text="Aucun")

def traiter_ez_avec_yokai(chemin_ez):
    chemin_absolu_exe = os.path.abspath(CHEMIN_YOKAI_EXE)
    dossier_exe = os.path.dirname(chemin_absolu_exe) or "."
    chemin_zip = chemin_ez.rsplit('.', 1)[0] + '.zip'
    
    if os.path.exists(chemin_zip):
        try: os.remove(chemin_zip)
        except: pass

    try:
        subprocess.run([chemin_absolu_exe, chemin_ez], shell=False, check=True, cwd=dossier_exe)
    except Exception as e:
        print(f"Erreur yokai.exe : {e}")

    return chemin_zip if os.path.exists(chemin_zip) else None

def toggle_avance():
    global mode_avance_actif
    mode_avance_actif = not mode_avance_actif
    if mode_avance_actif:
        frame_avance.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        btn_toggle_avance.config(text="▲ Masquer les paramètres avancés (15-38) ▲")
    else:
        frame_avance.pack_forget()
        btn_toggle_avance.config(text="▼ Afficher les paramètres avancés (15-38) ▼")

# ==========================================
# MODULES 3D ET IMAGE
# ==========================================
def charger_icone_ayd():
    global image_tk_reference
    if index_trouve == -1:
        messagebox.showwarning("Erreur", "Charge d'abord un YoukaiId !")
        return
        
    yokai_id = cases_entrees[0].get()
    fichier_png_racine = os.path.abspath(os.path.join(DOSSIER_RESSOURCES, f"bl_{yokai_id}.png"))
    fichier_ayd = os.path.abspath(os.path.join(DOSSIER_RESSOURCES, f"{yokai_id}.ayd"))
    png_data = None

    try:
        if os.path.exists(fichier_png_racine):
            with open(fichier_png_racine, "rb") as f:
                png_data = f.read()
        elif os.path.exists(fichier_ayd):
            with zipfile.ZipFile(fichier_ayd, 'r') as zf:
                png_filename = next((name for name in zf.namelist() if name.lower().endswith('.png')), None)
                if png_filename:
                    png_data = zf.read(png_filename)

        if png_data:
            image_tk_reference = tk.PhotoImage(data=png_data)
            label_image_ayd.config(image=image_tk_reference, text="", width=image_tk_reference.width(), height=image_tk_reference.height())
        else:
            messagebox.showinfo("Information", f"Aucune icône trouvée pour l'ID {yokai_id}.")
            label_image_ayd.config(image='', text="Aucune icône", width=12, height=6)
            
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de lire l'icône :\n{e}")

def extraire_geometrie_texturage_ymd(ymd_data):
    positions, faces, uvs = [], [], []
    geometrie_offset = -1
    for pattern in [b"geometries", b"skin"]:
        pos = ymd_data.find(pattern)
        if pos != -1:
            geometrie_offset = pos - 8
            break

    if geometrie_offset == -1: return None, None, None
    data = io.BytesIO(ymd_data)
    data.seek(geometrie_offset)

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
    except Exception as e: print(f"Avertissement géométrie: {e}")

    return positions, faces, uvs

def visualiser_modele_3d():
    if index_trouve == -1: return
    yokai_id = cases_entrees[0].get()
    fichier_ayd = os.path.abspath(os.path.join(DOSSIER_RESSOURCES, f"{yokai_id}.ayd"))
    fichier_ez = os.path.abspath(os.path.join(DOSSIER_RESSOURCES, f"{yokai_id}.ez"))
    chemin_zip_genere, ymd_data, png_data = None, None, None

    try:
        if os.path.exists(fichier_ayd):
            with zipfile.ZipFile(fichier_ayd, 'r') as zf:
                fichiers = zf.namelist()
                ymd_candidats = [f for f in fichiers if f.lower().endswith('.ymd')]
                if not ymd_candidats:
                    ez_nom = next((f for f in fichiers if f.lower().endswith('.ez')), None)
                    if ez_nom:
                        temp_ez = os.path.join(os.path.dirname(os.path.abspath(CHEMIN_YOKAI_EXE)), f"temp_{yokai_id}.ez")
                        with open(temp_ez, "wb") as f: f.write(zf.read(ez_nom))
                        chemin_zip_genere = traiter_ez_avec_yokai(temp_ez)
                        if chemin_zip_genere:
                            with zipfile.ZipFile(chemin_zip_genere, 'r') as zf_d:
                                tous = zf_d.namelist()
                                ymd_cands = [f for f in tous if f.lower().endswith('.ymd')]
                                png_cands = [f for f in tous if f.lower().endswith('.png')]
                                if ymd_cands: ymd_data = zf_d.read(max(ymd_cands, key=lambda f: zf_d.getinfo(f).file_size))
                                if png_cands: png_data = zf_d.read(max(png_cands, key=lambda f: zf_d.getinfo(f).file_size))
                        os.remove(temp_ez)
                else:
                    ymd_data = zf.read(max(ymd_candidats, key=lambda f: zf.getinfo(f).file_size))
                    png_candidats = [f for f in fichiers if f.lower().endswith('.png')]
                    if png_candidats: png_data = zf.read(max(png_candidats, key=lambda f: zf.getinfo(f).file_size))

        elif os.path.exists(fichier_ez):
            chemin_zip_genere = traiter_ez_avec_yokai(fichier_ez)
            if chemin_zip_genere:
                with zipfile.ZipFile(chemin_zip_genere, 'r') as zf:
                    tous = zf.namelist()
                    ymd_cands = [f for f in tous if f.lower().endswith('.ymd')]
                    png_cands = [f for f in tous if f.lower().endswith('.png')]
                    if ymd_cands: ymd_data = zf.read(max(ymd_cands, key=lambda f: zf.getinfo(f).file_size))
                    if png_cands: png_data = zf.read(max(png_cands, key=lambda f: zf.getinfo(f).file_size))
        else:
            messagebox.showwarning("Introuvable", f"Aucun fichier 3D (AYD ou EZ) trouvé pour l'ID {yokai_id}.")
            return

        if chemin_zip_genere and os.path.exists(chemin_zip_genere): os.remove(chemin_zip_genere)
        if not ymd_data:
            messagebox.showerror("Erreur", "Aucune géométrie trouvée.")
            return
            
        positions, faces, uvs = extraire_geometrie_texturage_ymd(ymd_data)
        if not positions:
            messagebox.showerror("Erreur", "Géométrie illisible ou corrompue.")
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
        o3d.visualization.draw_geometries([mesh], window_name=f"Viewer 3D - Yo-kai ID: {yokai_id}")

    except Exception as e:
        messagebox.showerror("Erreur Fatale", str(e))
        if chemin_zip_genere and os.path.exists(chemin_zip_genere):
            try: os.remove(chemin_zip_genere)
            except: pass

# ==========================================
# FONCTIONS DE LA BASE DE DONNÉES
# ==========================================
def charger_fichier():
    global lignes_yokai
    texte_brut, _ = lire_donnees_fichier(FICHIER_DB)
    if texte_brut:
        lignes_yokai = texte_brut.split('*')
        print(f"Base de données Yo-kai chargée ({len(lignes_yokai)} entrées).")

def charger_skills():
    global dictionnaire_skills
    texte_brut, _ = lire_donnees_fichier(FICHIER_SKILL_DB)
    if texte_brut:
        lignes_skills = texte_brut.split('*')
        for ligne in lignes_skills:
            colonnes = ligne.split('|')
            if len(colonnes) >= 4:
                yokai_id = colonnes[0]
                dictionnaire_skills[yokai_id] = {
                    "Nom": colonnes[1], "TypeID": colonnes[2], "Description": colonnes[3],
                    "Propriete1": colonnes[4] if len(colonnes) > 4 else "0",
                    "Propriete2": colonnes[5] if len(colonnes) > 5 else "0",
                    "Anim3D": colonnes[6] if len(colonnes) > 6 else "",
                    "Anim2D": colonnes[7] if len(colonnes) > 7 else ""
                }
        print(f"Base de données Âmultimes chargée ({len(dictionnaire_skills)} compétences).")

def charger_skill_levels():
    global dictionnaire_skill_levels
    texte_brut, _ = lire_donnees_fichier(FICHIER_SKILL_LEVEL_DB)
    if texte_brut:
        lignes = texte_brut.split('*')
        for ligne in lignes:
            colonnes = ligne.split('|')
            if len(colonnes) >= 13:
                yokai_id = colonnes[0]
                niveau = colonnes[1]
                if yokai_id not in dictionnaire_skill_levels:
                    dictionnaire_skill_levels[yokai_id] = {}
                dictionnaire_skill_levels[yokai_id][niveau] = colonnes
        print(f"Base de données Skill Levels chargée ({len(dictionnaire_skill_levels)} Yo-kai configurés).")

def classifier_yokai(youkai_id):
    try:
        id_val = int(youkai_id)
        if 8000 <= id_val < 9000: return "Jouable"
        elif 9000 <= id_val < 10000: return "Boss"
        else: return "Autre"
    except: return "Inconnu"

def recherche_avancee():
    global fenetre_res 
    critere = combo_recherche.get()
    valeur = entree_recherche_av.get().strip().lower()
    
    if fenetre_res is not None and fenetre_res.winfo_exists(): fenetre_res.destroy()
    if not valeur or critere not in INDEX_RECHERCHE: return
        
    index_col = INDEX_RECHERCHE[critere]
    resultats = []
    
    for ligne in lignes_yokai:
        colonnes = ligne.split('|')
        yokai_id = colonnes[0] 
        
        if index_col == "SOULT":
            if yokai_id in dictionnaire_skills:
                if dictionnaire_skills[yokai_id]["TypeID"] == valeur:
                    cat = classifier_yokai(yokai_id)
                    resultats.append(f"[{cat}] ID: {yokai_id} - Nom: {colonnes[1]}")
            continue 
        
        if len(colonnes) <= index_col: continue
            
        if index_col == 6:
            val_food = colonnes[6].strip()
            nom_food = FOOD_TYPES.get(val_food, "").lower()
            if val_food == valeur or valeur in nom_food:
                cat = classifier_yokai(yokai_id)
                resultats.append(f"[{cat}] ID: {yokai_id} - Nom: {colonnes[1]}")
            continue

        if index_col == 1:
            nom_jap = colonnes[1].lower()
            nom_lecture = colonnes[31].lower() if len(colonnes) > 31 else ""
            if valeur in nom_jap or valeur in nom_lecture:
                cat = classifier_yokai(yokai_id)
                resultats.append(f"[{cat}] ID: {yokai_id} - Nom: {colonnes[1]}")
        else:
            if colonnes[index_col].strip().lower() == valeur:
                cat = classifier_yokai(yokai_id)
                resultats.append(f"[{cat}] ID: {yokai_id} - Nom: {colonnes[1]}")
        
        if index_col == 1:
            nom_jap = colonnes[1].lower()
            nom_lecture = colonnes[31].lower() if len(colonnes) > 31 else ""
            if valeur in nom_jap or valeur in nom_lecture:
                cat = classifier_yokai(yokai_id)
                resultats.append(f"[{cat}] ID: {yokai_id} - Nom: {colonnes[1]}")
        else:
            if colonnes[index_col].strip().lower() == valeur:
                cat = classifier_yokai(yokai_id)
                resultats.append(f"[{cat}] ID: {yokai_id} - Nom: {colonnes[1]}")
                
    if not resultats:
        messagebox.showwarning("Introuvable", "Aucun résultat trouvé pour cette recherche.")
        return

    fenetre_res = tk.Toplevel(fenetre)
    fenetre_res.title(f"Résultats ({len(resultats)})")
    fenetre_res.geometry("400x300")
    tk.Label(fenetre_res, text="Double-cliquez pour charger ce Yo-kai", font=("Arial", 9, "italic")).pack(pady=5)
    listbox = tk.Listbox(fenetre_res, font=("Arial", 10))
    listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    
    for res in resultats: listbox.insert(tk.END, res)
        
    def charger_id_selectionne(event):
        selection = listbox.curselection()
        if selection:
            try:
                # 1. On extrait l'ID de la ligne cliquée
                id_isole = listbox.get(selection[0]).split("ID: ")[1].split(" - ")[0]
                
                # 2. On efface la case principale et on y insère le nouvel ID
                entree_recherche_id.delete(0, tk.END)
                entree_recherche_id.insert(0, id_isole)
                
                # 3. On lance le chargement automatiquement
                charger_yokai_par_id()
                
                # 4. On ferme la fenêtre des résultats (optionnel, mais plus propre !)
                fenetre_res.destroy()
                
            except IndexError: 
                pass
                
    listbox.bind("<Double-Button-1>", charger_id_selectionne)

def charger_yokai_par_id():
    global index_trouve, niveau_precedent
    id_recherche = entree_recherche_id.get().strip()
    
    for i, ligne in enumerate(lignes_yokai):
        colonnes = ligne.split('|')
        if colonnes[0] == id_recherche:
            index_trouve = i
            remplir_cases(colonnes)
            
            niveau_actuel_var.set("1") 
            niveau_precedent = "1"
            afficher_donnees_niveau(depuis_code=True)
            
            charger_icone_ayd()
            return 

    vider_interface()
    messagebox.showwarning("Introuvable", "Aucun Yo-kai ne possède ce YoukaiId.")

def obtenir_dernier_id():
    max_id = max([int(l.split('|')[0]) for l in lignes_yokai if l.split('|')[0].isdigit()], default=0)
    messagebox.showinfo("ID dispo", f"💡 Prochain ID libre : {max_id + 1}")

def remplir_cases(colonnes):
    global image_rang_reference 
    
    yokai_id = colonnes[0]

    for index_colonne, case in enumerate(cases_entrees):
        case.delete(0, tk.END)
        if index_colonne < len(colonnes):
            case.insert(0, colonnes[index_colonne])
    maj_nom_nourriture()

    for case in cases_skills.values():
        case.delete(0, tk.END)

    if yokai_id in dictionnaire_skills:
        skill = dictionnaire_skills[yokai_id]
        cases_skills["Nom"].insert(0, skill["Nom"])
        cases_skills["Description"].insert(0, skill["Description"])
        cases_skills["Propriete1"].insert(0, skill["Propriete1"])
        cases_skills["Propriete2"].insert(0, skill["Propriete2"])
        cases_skills["Anim3D"].insert(0, skill["Anim3D"])
        cases_skills["Anim2D"].insert(0, skill["Anim2D"])
        
        type_id = skill["TypeID"]
        if type_id in SOULT_TYPES:
            combo_soult_type.set(f"{type_id} - {SOULT_TYPES[type_id]}")
        else:
            combo_soult_type.set(f"{type_id} - Inconnu")

    if len(colonnes) > 3:
        valeur_rarite = colonnes[3]
        
        if valeur_rarite in COORDONNEES_RANGS:
            try:
                img_complete = Image.open(CHEMIN_SPRITESHEET)
                largeur_totale, hauteur_totale = img_complete.size
                
                largeur_case = largeur_totale // 8
                hauteur_case = hauteur_totale // 3
                
                col, lig = COORDONNEES_RANGS[valeur_rarite]
                
                gauche = col * largeur_case
                haut = lig * hauteur_case
                droite = gauche + largeur_case
                bas = haut + hauteur_case
                
                image_rognee = img_complete.crop((gauche, haut, droite, bas))
                image_rang_reference = ImageTk.PhotoImage(image_rognee)
                
                label_rang.config(image=image_rang_reference, text="")
                
            except Exception as e:
                print(f"Erreur avec la spritesheet : {e}")
                label_rang.config(image='', text=f"ID Rareté : {valeur_rarite}")
        else:
            label_rang.config(image='', text="Aucun")

def afficher_donnees_niveau(event=None, depuis_code=False):
    global niveau_precedent
    yokai_id = cases_entrees[0].get()
    if not yokai_id: return
    
    if not depuis_code:
        if yokai_id not in dictionnaire_skill_levels:
            dictionnaire_skill_levels[yokai_id] = {}
            
        cols_lvl = ["" for _ in range(13)]
        cols_lvl[0] = yokai_id
        cols_lvl[1] = niveau_precedent
        for index_col, case in cases_skill_levels.items():
            cols_lvl[index_col] = case.get()
        dictionnaire_skill_levels[yokai_id][niveau_precedent] = cols_lvl
    
    niveau_choisi = niveau_actuel_var.get()
    for case in cases_skill_levels.values():
        case.delete(0, tk.END)
        
    if yokai_id in dictionnaire_skill_levels and niveau_choisi in dictionnaire_skill_levels[yokai_id]:
        donnees_niveau = dictionnaire_skill_levels[yokai_id][niveau_choisi]
        for index_col, case in cases_skill_levels.items():
            if index_col < len(donnees_niveau):
                case.insert(0, donnees_niveau[index_col])
                
    niveau_precedent = niveau_choisi

# ==========================================
# FONCTIONS DE SAUVEGARDE ET CHARGEMENT MODS
# ==========================================
def ouvrir_menu_sauvegarde():
    yokai_id = cases_entrees[0].get().strip()
    if not yokai_id:
        messagebox.showerror("Erreur", "Veuillez d'abord définir un YoukaiId (champ 0).")
        return

    if yokai_id not in dictionnaire_skill_levels:
        dictionnaire_skill_levels[yokai_id] = {}
        
    lvl_actuel = niveau_actuel_var.get()
    cols_lvl = ["" for _ in range(13)]
    cols_lvl[0] = yokai_id
    cols_lvl[1] = str(lvl_actuel)
    for idx, case in cases_skill_levels.items():
        cols_lvl[idx] = case.get()
    dictionnaire_skill_levels[yokai_id][str(lvl_actuel)] = cols_lvl

    fen_menu = tk.Toplevel(fenetre)
    fen_menu.title("Options de sauvegarde globale")
    fen_menu.geometry("400x180")
    
    tk.Label(fen_menu, text=f"Sauvegarder les données du Yo-kai {yokai_id}", font=("Arial", 11, "bold")).pack(pady=10)
    
    tk.Button(fen_menu, text="💾 Enregistrer dans les index originaux (Écraser)", bg="#f8d7da", command=lambda: executer_sauvegarde(yokai_id, "original", fen_menu)).pack(fill=tk.X, padx=20, pady=5)
    tk.Button(fen_menu, text="📁 Exporter dans un dossier Mod (Isolé)", bg="#d4edda", command=lambda: executer_sauvegarde(yokai_id, "isole", fen_menu)).pack(fill=tk.X, padx=20, pady=5)

def executer_sauvegarde(yokai_id, mode, fen_menu):
    fen_menu.destroy()
    
    # Suppression des cases vides à la fin pour éviter les ||||
    valeurs_yokai = [case.get() for case in cases_entrees]
    while len(valeurs_yokai) > 35 and valeurs_yokai[-1] == "":
        valeurs_yokai.pop()
    ligne_yokai = "|".join(valeurs_yokai)
    
    type_selectionne = combo_soult_type.get()
    type_id = type_selectionne.split(" - ")[0] if " - " in type_selectionne else "-1"
    ligne_skill = "|".join([
        yokai_id,
        cases_skills["Nom"].get(),
        type_id,
        cases_skills["Description"].get(),
        cases_skills["Propriete1"].get(),
        cases_skills["Propriete2"].get(),
        cases_skills["Anim3D"].get(),
        cases_skills["Anim2D"].get()
    ])
    
    lignes_levels = []
    base_lvl_data = dictionnaire_skill_levels.get(yokai_id, {}).get(niveau_actuel_var.get(), [""]*13)
    
    for lvl in range(1, 8):
        lvl_str = str(lvl)
        if yokai_id in dictionnaire_skill_levels and lvl_str in dictionnaire_skill_levels[yokai_id]:
            data = dictionnaire_skill_levels[yokai_id][lvl_str]
        else:
            data = list(base_lvl_data) 
            data[1] = lvl_str
            
        while len(data) < 13: data.append("") 
        data[0] = yokai_id
        lignes_levels.append("|".join(data))
    
    if mode == "isole":
        dossier_parent = filedialog.askdirectory(title="Choisir le dossier de destination pour le Mod")
        if not dossier_parent: return
        
        chemin_mod = os.path.join(dossier_parent, f"Yokai_{yokai_id}")
        os.makedirs(chemin_mod, exist_ok=True)
        
        try:
            with open(os.path.join(chemin_mod, "ywp_mst_youkai.json"), "w", encoding="utf-8") as f:
                json.dump({"tableData": ligne_yokai, "version": "1"}, f, ensure_ascii=False, indent=4)
            with open(os.path.join(chemin_mod, "ywp_mst_youkai_skill.json"), "w", encoding="utf-8") as f:
                json.dump({"tableData": ligne_skill, "version": "1"}, f, ensure_ascii=False, indent=4)
            with open(os.path.join(chemin_mod, "ywp_mst_youkai_skill_level.json"), "w", encoding="utf-8") as f:
                json.dump({"tableData": "*".join(lignes_levels), "version": "1"}, f, ensure_ascii=False, indent=4)
                
            messagebox.showinfo("Succès", f"Dossier Mod créé avec succès dans :\n{chemin_mod}")
        except Exception as e:
            messagebox.showerror("Erreur Mod", str(e))
            
    elif mode == "original":
        try:
            def maj_fichier_original(chemin_fichier, nouvelles_lignes):
                texte_brut, donnees_json_orig = lire_donnees_fichier(chemin_fichier)
                lignes_existantes = texte_brut.split('*') if texte_brut else []
                lignes_filtrees = [l for l in lignes_existantes if not l.startswith(yokai_id + "|")]
                
                if isinstance(nouvelles_lignes, list):
                    lignes_filtrees.extend(nouvelles_lignes)
                else:
                    lignes_filtrees.append(nouvelles_lignes)
                    
                nouveau_texte = "*".join(lignes_filtrees)
                
                with open(chemin_fichier, "w", encoding="utf-8") as f:
                    if donnees_json_orig is not None:
                        if "tableData" in donnees_json_orig:
                            donnees_json_orig["tableData"] = nouveau_texte
                        else:
                            donnees_json_orig["masterData"] = nouveau_texte
                        json.dump(donnees_json_orig, f, ensure_ascii=False, indent=4)
                    else:
                        f.write(nouveau_texte)

            maj_fichier_original(FICHIER_DB, ligne_yokai)
            maj_fichier_original(FICHIER_SKILL_DB, ligne_skill)
            maj_fichier_original(FICHIER_SKILL_LEVEL_DB, lignes_levels)
            
            charger_fichier()
            charger_skills()
            charger_skill_levels()
            messagebox.showinfo("Succès", f"Les 3 index d'origine ont été mis à jour pour l'ID {yokai_id} !")
        except Exception as e:
            messagebox.showerror("Erreur DB Originale", str(e))
          
def sauvegarder_skill_sous():
    if index_trouve == -1:
        messagebox.showerror("Erreur", "Aucun Yo-kai chargé !")
        return
        
    yokai_id = cases_entrees[0].get()
    soult_id = yokai_id  
    
    type_selectionne = combo_soult_type.get()
    type_id = type_selectionne.split(" - ")[0] if " - " in type_selectionne else "-1"
    
    nouvelle_ligne = "|".join([
        soult_id,
        cases_skills["Nom"].get(),
        type_id,
        cases_skills["Description"].get(),
        cases_skills["Propriete1"].get(),
        cases_skills["Propriete2"].get(),
        cases_skills["Anim3D"].get(),
        cases_skills["Anim2D"].get()
    ])
    
    chemin_sauvegarde = filedialog.asksaveasfilename(
        defaultextension=".json",
        initialfile="ywp_mst_skill_mod.json",
        title="Enregistrer la base de données sous...",
        filetypes=[("Fichiers JSON", "*.json"), ("Fichiers Texte", "*.txt"), ("Tous les fichiers", "*.*")]
    )
    
    if not chemin_sauvegarde:
        return
    
    try:
        texte_brut, donnees_json_orig = lire_donnees_fichier(FICHIER_SKILL_DB)
        lignes = texte_brut.split('*') if texte_brut else []
        modifie = False
        for i, ligne in enumerate(lignes):
            if ligne.startswith(soult_id + "|"):
                lignes[i] = nouvelle_ligne
                modifie = True
                break
                
        if not modifie:
            lignes.append(nouvelle_ligne)
            
        nouveau_texte = "*".join(lignes)
        
        with open(chemin_sauvegarde, "w", encoding="utf-8") as f:
            if chemin_sauvegarde.endswith('.json') or donnees_json_orig is not None:
                donnees_finales = donnees_json_orig if donnees_json_orig else {"tableData": nouveau_texte, "version": "1"}
                if "tableData" in donnees_finales:
                    donnees_finales["tableData"] = nouveau_texte
                else:
                    donnees_finales["masterData"] = nouveau_texte
                json.dump(donnees_finales, f, ensure_ascii=False, indent=4)
            else:
                f.write(nouveau_texte)
            
        messagebox.showinfo("Succès", f"Fichier sauvegardé avec succès sous :\n{chemin_sauvegarde}")
    except Exception as e:
        messagebox.showerror("Erreur de sauvegarde", str(e))

def charger_dossier_mod():
    global index_trouve, niveau_precedent
    dossier_mod = filedialog.askdirectory(title="Sélectionner le dossier du Mod à charger")
    if not dossier_mod: return

    fichier_yokai = trouver_fichier("ywp_mst_youkai", dossier_mod)
    fichier_skill = trouver_fichier("ywp_mst_youkai_skill", dossier_mod)
    fichier_lvl = trouver_fichier("ywp_mst_youkai_skill_level", dossier_mod)

    if not fichier_yokai:
        messagebox.showerror("Erreur", "Le fichier ywp_mst_youkai (JSON ou TXT) est introuvable dans ce dossier.")
        return

    try:
        texte_yokai, _ = lire_donnees_fichier(fichier_yokai)
        if texte_yokai:
            colonnes = texte_yokai.split('|')
            yokai_id = colonnes[0]

        if fichier_skill:
            texte_skill, _ = lire_donnees_fichier(fichier_skill)
            if texte_skill:
                colonnes_skill = texte_skill.split('|')
                if len(colonnes_skill) >= 4:
                    dictionnaire_skills[yokai_id] = {
                        "Nom": colonnes_skill[1], "TypeID": colonnes_skill[2],
                        "Description": colonnes_skill[3],
                        "Propriete1": colonnes_skill[4] if len(colonnes_skill) > 4 else "0",
                        "Propriete2": colonnes_skill[5] if len(colonnes_skill) > 5 else "0",
                        "Anim3D": colonnes_skill[6] if len(colonnes_skill) > 6 else "",
                        "Anim2D": colonnes_skill[7] if len(colonnes_skill) > 7 else ""
                    }

        if fichier_lvl:
            texte_lvl, _ = lire_donnees_fichier(fichier_lvl)
            if texte_lvl:
                lignes_lvl = texte_lvl.split('*')
                dictionnaire_skill_levels[yokai_id] = {}
                for l in lignes_lvl:
                    cols = l.split('|')
                    if len(cols) >= 13:
                        dictionnaire_skill_levels[yokai_id][cols[1]] = cols

        entree_recherche_id.delete(0, tk.END)
        entree_recherche_id.insert(0, yokai_id)
        
        index_trouve = -1
        for i, ligne in enumerate(lignes_yokai):
            if ligne.startswith(yokai_id + "|"):
                index_trouve = i
                break
                
        remplir_cases(colonnes)
        
        niveau_actuel_var.set("1") 
        niveau_precedent = "1"
        afficher_donnees_niveau(depuis_code=True)
        
        charger_icone_ayd()
        messagebox.showinfo("Succès", f"Le Mod du Yo-kai {yokai_id} a été chargé avec succès dans l'éditeur !")

    except Exception as e:
        messagebox.showerror("Erreur", f"Erreur lors du chargement du Mod :\n{e}")
        
def maj_nom_nourriture(event=None):
    valeur = cases_entrees[6].get().strip() if len(cases_entrees) > 6 else ""
    nom_nourriture = FOOD_TYPES.get(valeur, "Inconnu")
    if 'label_nom_food' in globals():
        label_nom_food.config(text=f"({nom_nourriture})", fg="#0066cc" if nom_nourriture != "Inconnu" else "gray")

# --- INTERFACE GRAPHIQUE ---
fenetre = tk.Tk()
fenetre.title("Puni MST Tool")
fenetre.geometry("1050x800")
fenetre.withdraw() # On cache la fenêtre principale pour laisser la pop-up s'afficher

# --- BANDEAU SUPÉRIEUR ---
frame_top = tk.Frame(fenetre, padx=10, pady=10)
frame_top.pack(fill=tk.X)

frame_gauche = tk.Frame(frame_top)
frame_gauche.pack(side=tk.LEFT)
tk.Label(frame_gauche, text="🔍 Filtre :").grid(row=0, column=0, sticky="e")
combo_recherche = ttk.Combobox(frame_gauche, values=list(INDEX_RECHERCHE.keys()), width=18, state="readonly")
combo_recherche.current(0)
combo_recherche.grid(row=0, column=1)
entree_recherche_av = tk.Entry(frame_gauche, width=12)
entree_recherche_av.grid(row=0, column=2, padx=5)
tk.Button(frame_gauche, text="Go", command=recherche_avancee).grid(row=0, column=3, sticky="w")

tk.Label(frame_gauche, text="⚙️ Charger ID :").grid(row=1, column=0, sticky="e", pady=5)
entree_recherche_id = tk.Entry(frame_gauche, width=15)
entree_recherche_id.grid(row=1, column=1, pady=5)
tk.Button(frame_gauche, text="Charger", bg="#cce5ff", command=charger_yokai_par_id).grid(row=1, column=2, columnspan=2, sticky="w", padx=5)

frame_droite = tk.Frame(frame_top, bd=2, relief=tk.GROOVE, padx=10, pady=5, bg="#f0f0f0")
frame_droite.pack(side=tk.RIGHT, fill=tk.Y)
frame_icone = tk.Frame(frame_droite, bg="#f0f0f0")
frame_icone.pack(side=tk.LEFT, padx=(0, 10))

frame_image_et_rang = tk.Frame(frame_icone, bg="#f0f0f0")
frame_image_et_rang.pack()

label_image_ayd = tk.Label(frame_image_et_rang, text="Aucune icône", bg="#e0e0e0", relief=tk.SUNKEN, width=12, height=6)
label_image_ayd.pack(side=tk.LEFT)

label_rang = tk.Label(frame_image_et_rang, text="", font=("Arial", 16, "bold"), fg="#ff9900", bg="#f0f0f0")
label_rang.pack(side=tk.LEFT, padx=5)

tk.Button(frame_icone, text="🖼️ Charger Icône", font=("Arial", 8), command=charger_icone_ayd).pack(pady=2)

frame_boutons_droite = tk.Frame(frame_droite, bg="#f0f0f0")
frame_boutons_droite.pack(side=tk.RIGHT)
tk.Label(frame_boutons_droite, text="📦 Ressources", font=("Arial", 10, "bold"), bg="#f0f0f0").pack()
tk.Button(frame_boutons_droite, text="👁️ Modèle 3D", bg="#d4edda", font=("Arial", 9, "bold"), command=visualiser_modele_3d).pack(pady=5, fill=tk.X)
tk.Button(frame_boutons_droite, text="💡 Nouvel ID", command=obtenir_dernier_id, bg="#fff3cd").pack(fill=tk.X)
tk.Button(frame_boutons_droite, text="💾  Yo-kai (Global)", bg="#add8e6", font=("Arial", 9, "bold"), command=ouvrir_menu_sauvegarde).pack(pady=5, fill=tk.X)
tk.Button(frame_boutons_droite, text="📂 Charger Dossier Mod", command=charger_dossier_mod, bg="#e2e3e5", font=("Arial", 9, "bold")).pack(pady=5, fill=tk.X)
tk.Button(frame_boutons_droite, text="⚙️ Changer les dossiers (Config)", command=changer_dossiers, bg="#f8d7da", font=("Arial", 9, "bold")).pack(pady=5, fill=tk.X)

tk.Frame(fenetre, height=2, bd=1, relief=tk.SUNKEN).pack(fill=tk.X, padx=10)

# --- ZONE CENTRALE (Scrollbar) ---
frame_milieu = tk.Frame(fenetre)
frame_milieu.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

canvas = tk.Canvas(frame_milieu)
scrollbar = ttk.Scrollbar(frame_milieu, orient="vertical", command=canvas.yview)
scrollable_frame = tk.Frame(canvas)

scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)
canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# --- UI : ÉLÉMENTS BASIQUES (0 à 14) ---
frame_basique = tk.Frame(scrollable_frame)
frame_basique.pack(fill=tk.X, padx=5, pady=5)

for i in range(15):
    ligne = i // 2 
    colonne = (i % 2) * 2 
    tk.Label(frame_basique, text=CHAMPS_YOKAI[i], font=("Arial", 9)).grid(row=ligne, column=colonne, sticky="e", padx=(10, 5), pady=5)
    
    # Cadre spécial pour le champ FoodType (i == 6)
    if i == 6:
        sub_frame_food = tk.Frame(frame_basique)
        sub_frame_food.grid(row=ligne, column=colonne+1, sticky="w", padx=5, pady=5)
        
        entree = tk.Entry(sub_frame_food, width=12)
        entree.pack(side=tk.LEFT)
        cases_entrees.append(entree)
        
        label_nom_food = tk.Label(sub_frame_food, text="(Inconnu)", font=("Arial", 9, "bold"), fg="gray")
        label_nom_food.pack(side=tk.LEFT, padx=5)
        
        # Met à jour le nom en direct lorsqu'on tape un numéro
        entree.bind("<KeyRelease>", maj_nom_nourriture)
    else:
        entree = tk.Entry(frame_basique, width=35)
        entree.grid(row=ligne, column=colonne+1, padx=5, pady=5)
        cases_entrees.append(entree)

# --- UI : ÂMULTIME (SKILLS) ---
frame_skills = tk.LabelFrame(scrollable_frame, text="✨ Âmultime (Skill)", font=("Arial", 10, "bold"), bg="#fff9e6", padx=10, pady=10)
frame_skills.pack(fill=tk.X, padx=10, pady=10)

champs_skills_noms = ["Nom", "Description", "Propriete1", "Propriete2", "Anim3D", "Anim2D"]

tk.Label(frame_skills, text="Type (SoultType) :", font=("Arial", 9), bg="#fff9e6").grid(row=0, column=0, sticky="e", padx=(10, 5), pady=5)
combo_soult_type = ttk.Combobox(frame_skills, values=[f"{k} - {v}" for k, v in SOULT_TYPES.items()], width=32, state="readonly")
combo_soult_type.grid(row=0, column=1, padx=5, pady=5)
cases_skills["TypeID"] = combo_soult_type

for i, nom_champ in enumerate(champs_skills_noms):
    ligne = (i + 2) // 2 
    colonne = ((i + 2) % 2) * 2
    tk.Label(frame_skills, text=nom_champ + " :", font=("Arial", 9), bg="#fff9e6").grid(row=ligne, column=colonne, sticky="e", padx=(10, 5), pady=5)
    entree = tk.Entry(frame_skills, width=35)
    entree.grid(row=ligne, column=colonne+1, padx=5, pady=5)
    cases_skills[nom_champ] = entree

tk.Button(frame_skills, text="💾 Enregistrer Âmultime sous... (Optionnel)", bg="#cce5ff", font=("Arial", 9, "bold"), command=sauvegarder_skill_sous).grid(row=5, column=0, columnspan=4, pady=15)

# --- UI : NIVEAUX D'ÂMULTIME (SKILL LEVELS) ---
frame_skill_levels = tk.LabelFrame(scrollable_frame, text="📊 Niveaux d'Âmultime", font=("Arial", 10, "bold"), bg="#e6f2ff", padx=10, pady=10)
frame_skill_levels.pack(fill=tk.X, padx=10, pady=10)

niveau_actuel_var = tk.StringVar(value="1")

tk.Label(frame_skill_levels, text="Sélectionner le Niveau :", font=("Arial", 9, "bold"), bg="#e6f2ff").grid(row=0, column=0, sticky="e", padx=5, pady=5)
combo_niveau_skill = ttk.Combobox(frame_skill_levels, textvariable=niveau_actuel_var, values=[str(i) for i in range(1, 8)], width=10, state="readonly")
combo_niveau_skill.grid(row=0, column=1, sticky="w", padx=5, pady=5)

combo_niveau_skill.bind("<<ComboboxSelected>>", afficher_donnees_niveau)

champs_niveaux = [
    ("DisplayName (Nom affiché)", 2),
    ("Unk0 (Vitesse jauge?)", 3),
    ("SoultPt (Puissance/Points)", 4),
    ("MaxUseCount", 5),
    ("SoultStatsDict (Dico Stats)", 11),
    ("Unk1", 6), ("Unk2", 7), ("Unk3", 8), 
    ("Unk4", 9), ("Unk5", 10), ("Unk7 (Double)", 12)
]

for i, (nom_champ, index_col) in enumerate(champs_niveaux):
    ligne = (i // 2) + 1
    colonne = (i % 2) * 2
    tk.Label(frame_skill_levels, text=f"{nom_champ} :", font=("Arial", 9), bg="#e6f2ff").grid(row=ligne, column=colonne, sticky="e", padx=(10, 5), pady=2)
    entree = tk.Entry(frame_skill_levels, width=35)
    entree.grid(row=ligne, column=colonne+1, padx=5, pady=2)
    cases_skill_levels[index_col] = entree

# --- UI : BOUTON ET ÉLÉMENTS AVANCÉS (15 à 38) ---
btn_toggle_avance = tk.Button(scrollable_frame, text="▼ Afficher les paramètres avancés (15-38) ▼", command=toggle_avance, bg="#e2e3e5", font=("Arial", 9, "bold"))
btn_toggle_avance.pack(pady=10)

frame_avance = tk.Frame(scrollable_frame)

for i in range(15, len(CHAMPS_YOKAI)):
    ligne = (i - 15) // 2
    colonne = ((i - 15) % 2) * 2 
    tk.Label(frame_avance, text=CHAMPS_YOKAI[i], font=("Arial", 9)).grid(row=ligne, column=colonne, sticky="e", padx=(10, 5), pady=5)
    entree = tk.Entry(frame_avance, width=35)
    entree.grid(row=ligne, column=colonne+1, padx=5, pady=5)
    cases_entrees.append(entree)

# --- INITIALISATION ET LANCEMENT ---
def demarrer_outil():
    # On essaye de charger la config silencieusement
    if charger_config():
        return True
    else:
        # Sinon, on demande manuellement et on sauvegarde pour la prochaine fois
        if initialiser_outils(au_demarrage=True) and initialiser_dossier_version(au_demarrage=True):
            sauvegarder_config()
            return True
    return False

if __name__ == "__main__":
    if demarrer_outil():
        charger_fichier()
        charger_skills()
        charger_skill_levels()
        fenetre.deiconify() 
        fenetre.mainloop()
