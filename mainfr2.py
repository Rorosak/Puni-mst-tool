import json
import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import ttk
import os
import sys
import io
import struct
import subprocess
import zipfile
import numpy as np
import open3d as o3d
from PIL import Image, ImageTk

# ==========================================
# PARAMÈTRES ET VARIABLES GLOBALES
# ==========================================
# Dossier de base : celui de l'exe (PyInstaller --onedir) ou celui du script en mode .py
if getattr(sys, "frozen", False):
    DOSSIER_BASE = os.path.dirname(sys.executable)
else:
    DOSSIER_BASE = os.path.dirname(os.path.abspath(__file__))

FICHIER_CONFIG = os.path.join(DOSSIER_BASE, "config.json")

def log(message):
    """print() sécurisé : en mode --windowed (pas de console), sys.stdout peut être None
    et un print() classique ferait planter l'appli silencieusement. On avale l'erreur ici."""
    try:
        print(message)
    except Exception:
        pass

FICHIER_DB = ""
FICHIER_SKILL_DB = ""
FICHIER_SKILL_LEVEL_DB = ""
FICHIER_BONUS_EFFECT_DB = ""
FICHIER_BONUS_EFFECT_LEVEL_DB = ""
DOSSIER_RESSOURCES = ""

CHEMIN_YOKAI_EXE = ""
CHEMIN_SPRITESHEET = ""
CHEMIN_KIND_SPRITESHEET = ""

DOSSIER_SERVEUR = ""
INDEX_SERVEUR = {}

COORDONNEES_KINDS = {str(i): ((i - 1) % 3, (i - 1) // 3) for i in range(1, 13)}

COORDONNEES_RANGS = {
    "1": (2, 0), "2": (3, 0), "3": (4, 0), "4": (5, 0),
    "5": (6, 0), "6": (7, 0), "7": (0, 1), "8": (2, 1),
    "9": (4, 1), "10": (6, 1), "11": (0, 2), "12": (2, 2)
}

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

YW_BONUS_EFFECTS = {
    "1": "BonusScore",               # Get a bonus in Score Attack against X
    "3": "RaiseTribeEffect",         # Raises X Tribe effects
    "4": "ChipDropsMore",            # Merican/American Chip drops more
    "5": "MisteryChallengesSimpler", # Make mistery challenges simpler
    "6": "LowersDamage",             # Lowers damage from X
    "8": "WibWobAppearsMore",        # His/Her Wib Wob appears more
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
    "Nom du Yo-kai (1)": 1, "Rang / Rarity (3)": 3, "Tribu / Kind (4)": 4,
    "Nourriture / FoodType (6)": 6, "Dictionary ID (14)": 14, "Type Âmultime (-1 à 44)": "SOULT",
    "Effet Bonus (texte)": "BONUS", "Effet Bonus (ID Type)": "BONUS_TYPE"
}

image_rang_reference = None 
image_kind_reference = None 
dictionnaire_skill_levels = {} 
cases_skill_levels = {}
niveau_actuel_var = None 
niveau_precedent = "1"
lignes_yokai = []
dictionnaire_skills = {}
index_trouve = -1
cases_entrees = []
cases_skills = {}
# --- Effets Bonus (liés au YoukaiId courant, via un SubId choisi) ---
dictionnaire_bonus_effect = {}        # (yokai_id, subid) -> [id, subid, description, type, ressource, 0,0,0]
dictionnaire_bonus_effect_level = {}  # (yokai_id, subid) -> {niveau_str: [id, subid, niveau, texte, valA, valB, 0]}
cases_bonus = {}
subid_bonus_var = None
niveau_bonus_actuel_var = None
niveau_bonus_precedent = "1"
cases_bonus_niveau = {}
image_tk_reference = None 
fenetre_res = None 
mode_avance_actif = False

# ==========================================
# FONCTIONS DE CONFIGURATION & SERVEUR
# ==========================================
def charger_config():
    global CHEMIN_YOKAI_EXE, CHEMIN_SPRITESHEET, CHEMIN_KIND_SPRITESHEET, FICHIER_DB, FICHIER_SKILL_DB, FICHIER_SKILL_LEVEL_DB, FICHIER_BONUS_EFFECT_DB, FICHIER_BONUS_EFFECT_LEVEL_DB, DOSSIER_RESSOURCES, DOSSIER_SERVEUR
    if os.path.exists(FICHIER_CONFIG):
        try:
            with open(FICHIER_CONFIG, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            y_exe = config.get("CHEMIN_YOKAI_EXE", "").replace("\\", "/")
            s_sheet = config.get("CHEMIN_SPRITESHEET", "").replace("\\", "/")
            k_sheet = config.get("CHEMIN_KIND_SPRITESHEET", "").replace("\\", "/")
            f_db = config.get("FICHIER_DB", "").replace("\\", "/")
            s_db = config.get("FICHIER_SKILL_DB", "").replace("\\", "/")
            l_db = config.get("FICHIER_SKILL_LEVEL_DB", "").replace("\\", "/")
            be_db = config.get("FICHIER_BONUS_EFFECT_DB", "").replace("\\", "/")
            bel_db = config.get("FICHIER_BONUS_EFFECT_LEVEL_DB", "").replace("\\", "/")
            d_res = config.get("DOSSIER_RESSOURCES", "").replace("\\", "/")
            d_serv = config.get("DOSSIER_SERVEUR", "").replace("\\", "/")

            mode_serveur = bool(d_serv) and os.path.exists(d_serv)

            chemins_a_verifier = {
                "CHEMIN_YOKAI_EXE": y_exe, "CHEMIN_SPRITESHEET": s_sheet, "CHEMIN_KIND_SPRITESHEET": k_sheet,
                "FICHIER_DB": f_db, "FICHIER_SKILL_DB": s_db, "FICHIER_SKILL_LEVEL_DB": l_db,
            }
            if not mode_serveur:
                chemins_a_verifier["DOSSIER_RESSOURCES"] = d_res
            manquants = [nom for nom, chemin in chemins_a_verifier.items() if not os.path.exists(chemin)]
            if manquants:
                log("Config invalide, chemins introuvables :")
                for nom in manquants:
                    log(f"  - {nom} = {chemins_a_verifier[nom]!r}")

            if not manquants:
                CHEMIN_YOKAI_EXE, CHEMIN_SPRITESHEET, CHEMIN_KIND_SPRITESHEET = y_exe, s_sheet, k_sheet
                FICHIER_DB, FICHIER_SKILL_DB, FICHIER_SKILL_LEVEL_DB = f_db, s_db, l_db
                FICHIER_BONUS_EFFECT_DB = be_db if os.path.exists(be_db) else ""
                FICHIER_BONUS_EFFECT_LEVEL_DB = bel_db if os.path.exists(bel_db) else ""
                DOSSIER_RESSOURCES = d_res
                
                if mode_serveur:
                    DOSSIER_SERVEUR = d_serv
                    indexer_serveur(silencieux=True)
                return True
        except Exception as e:
            log(f"Erreur charger_config : {e}")


def sauvegarder_config():
    config = {
        "CHEMIN_YOKAI_EXE": CHEMIN_YOKAI_EXE, "CHEMIN_SPRITESHEET": CHEMIN_SPRITESHEET,
        "CHEMIN_KIND_SPRITESHEET": CHEMIN_KIND_SPRITESHEET,
        "FICHIER_DB": FICHIER_DB, "FICHIER_SKILL_DB": FICHIER_SKILL_DB,
        "FICHIER_SKILL_LEVEL_DB": FICHIER_SKILL_LEVEL_DB,
        "FICHIER_BONUS_EFFECT_DB": FICHIER_BONUS_EFFECT_DB, "FICHIER_BONUS_EFFECT_LEVEL_DB": FICHIER_BONUS_EFFECT_LEVEL_DB,
        "DOSSIER_RESSOURCES": DOSSIER_RESSOURCES,
        "DOSSIER_SERVEUR": DOSSIER_SERVEUR
    }
    try:
        with open(FICHIER_CONFIG, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    except Exception as e:
        log(f"Erreur config : {e}")

def changer_dossiers():
    global CHEMIN_YOKAI_EXE, CHEMIN_SPRITESHEET, CHEMIN_KIND_SPRITESHEET
    CHEMIN_YOKAI_EXE = CHEMIN_SPRITESHEET = CHEMIN_KIND_SPRITESHEET = ""
    if initialiser_outils(au_demarrage=False) and initialiser_dossier_version(au_demarrage=False):
        sauvegarder_config()
        charger_fichier()
        charger_skills()
        charger_skill_levels()
        charger_bonus_effects()
        charger_bonus_effect_levels()
        vider_interface()
        messagebox.showinfo("Succès", "Dossiers mis à jour !")

def indexer_serveur(silencieux=False):
    global DOSSIER_SERVEUR, INDEX_SERVEUR, FICHIER_DB, FICHIER_SKILL_DB, FICHIER_SKILL_LEVEL_DB, FICHIER_BONUS_EFFECT_DB, FICHIER_BONUS_EFFECT_LEVEL_DB
    
    if not silencieux:
        dossier = filedialog.askdirectory(title="Sélectionner la RACINE du serveur (contenant dataDownload et Resources)")
        if not dossier: return
        DOSSIER_SERVEUR = dossier.replace("\\", "/")
        
    if not DOSSIER_SERVEUR or not os.path.exists(DOSSIER_SERVEUR): return
        
    dossier_assets = os.path.join(DOSSIER_SERVEUR, "dataDownload")
    INDEX_SERVEUR.clear()
    if os.path.exists(dossier_assets):
        for racine, _, fichiers in os.walk(dossier_assets):
            for f in fichiers:
                INDEX_SERVEUR[f.lower()] = os.path.join(racine, f).replace("\\", "/")
                
    dossier_mst = os.path.join(DOSSIER_SERVEUR, "Resources")
    fichiers_manquants = ["ywp_mst_youkai", "ywp_mst_youkai_skill", "ywp_mst_youkai_skill_level"]
    if os.path.exists(dossier_mst):
        f_db = trouver_fichier("ywp_mst_youkai", dossier_mst)
        s_db = trouver_fichier("ywp_mst_youkai_skill", dossier_mst)
        l_db = trouver_fichier("ywp_mst_youkai_skill_level", dossier_mst)
        be_db = trouver_fichier("ywp_mst_youkai_bonus_effect", dossier_mst)
        bel_db = trouver_fichier("ywp_mst_youkai_bonus_effect_level", dossier_mst)
        
        fichiers_manquants = [nom for nom, chemin in zip(["ywp_mst_youkai", "ywp_mst_youkai_skill", "ywp_mst_youkai_skill_level"], [f_db, s_db, l_db]) if not chemin]
        
        if not fichiers_manquants:
            FICHIER_DB, FICHIER_SKILL_DB, FICHIER_SKILL_LEVEL_DB = f_db.replace("\\", "/"), s_db.replace("\\", "/"), l_db.replace("\\", "/")
        FICHIER_BONUS_EFFECT_DB = be_db.replace("\\", "/") if be_db else ""
        FICHIER_BONUS_EFFECT_LEVEL_DB = bel_db.replace("\\", "/") if bel_db else ""
            
    if not silencieux:
        sauvegarder_config()
        if not fichiers_manquants:
            charger_fichier()
            charger_skills()
            charger_skill_levels()
            charger_bonus_effects()
            charger_bonus_effect_levels()
            vider_interface()
            messagebox.showinfo("Serveur lié", f"Succès !\n- {len(INDEX_SERVEUR)} assets trouvés\n- Bases de données chargées")
        else:
            messagebox.showwarning("Liaison partielle", f"Assets indexés ({len(INDEX_SERVEUR)}).\nFichiers manquants dans Resources :\n- " + "\n- ".join(fichiers_manquants))

# ==========================================
# FONCTIONS UTILITAIRES & FICHIERS
# ==========================================
def trouver_fichier(nom_base, dossier):
    for ext in [".json", ".txt"]:
        chemin = os.path.join(dossier, nom_base + ext)
        if os.path.exists(chemin): return chemin
    return None
# ==========================================
# LECTURE UNIVERSELLE TXT / JSON
# ==========================================
CLES_JSON_TABLE = ("tableData", "masterData", "data", "rows", "table")

def _element_vers_ligne(element):
    """Convertit un élément JSON (str, liste ou dict) en ligne 'col1|col2|...'."""
    if isinstance(element, str):
        return element
    if isinstance(element, (list, tuple)):
        return "|".join("" if c is None else str(c) for c in element)
    if isinstance(element, dict):
        return "|".join("" if v is None else str(v) for v in element.values())
    return str(element)

def _normaliser_texte(texte):
    """Uniformise les séparateurs : enlève les \r, convertit les \n en * si besoin."""
    texte = str(texte).replace("\r", "")
    if "*" not in texte and "\n" in texte:
        texte = texte.replace("\n", "*")
    else:
        texte = texte.replace("\n", "")
    return texte.strip("*")

def _colonnes_natives(ligne):
    """Reconvertit les colonnes en int/float quand possible (pour réécriture JSON propre)."""
    colonnes = []
    for c in ligne.split("|"):
        if c.lstrip("-").isdigit():
            colonnes.append(int(c))
        else:
            try:
                colonnes.append(float(c))
            except ValueError:
                colonnes.append(c)
    return colonnes

def lire_donnees_fichier(chemin):
    """
    Lit un ywp_mst (TXT brut ou JSON) et retourne (texte "l1*l2*...", json_original ou None).
    Formats JSON acceptés :
      - {"tableData": "l1*l2*..."}   (ou masterData / data / rows / table)
      - {"tableData": [["c1","c2"], ...]} ou {"id": [etc.]}
      - ["l1|l2|...", ...]  ou  [["c1","c2"], ...]  ou  [{...}, ...]
    """
    try:
        with open(chemin, "r", encoding="utf-8") as f:
            contenu = f.read().strip()
    except Exception as e:
        messagebox.showerror("Erreur Lecture", f"Impossible de lire {chemin}:\n{e}")
        return "", None

    try:
        donnees = json.loads(contenu)
    except ValueError:
        return _normaliser_texte(contenu), None  # TXT brut classique

    # --- JSON avec clé connue (tableData / masterData / ...) ---
    if isinstance(donnees, dict):
        for cle in CLES_JSON_TABLE:
            if cle in donnees:
                valeur = donnees[cle]
                if isinstance(valeur, str):
                    return _normaliser_texte(valeur), donnees
                iterable = valeur.values() if isinstance(valeur, dict) else valeur
                return _normaliser_texte("*".join(_element_vers_ligne(e) for e in iterable)), donnees
        # --- JSON dict de lignes : {"id": "l|..."} ou {"id": [etc.]} ---
        return _normaliser_texte("*".join(_element_vers_ligne(v) for v in donnees.values())), donnees

    # --- JSON liste : ["l|...", ...] ou [["c","c"], ...] ---
    if isinstance(donnees, list):
        return _normaliser_texte("*".join(_element_vers_ligne(e) for e in donnees)), donnees

    return "", None

def maj_fichier_original(chemin_fichier, nouvelles_lignes, yokai_id):
    texte_brut, donnees_json_orig = lire_donnees_fichier(chemin_fichier)
    lignes_existantes = texte_brut.split('*') if texte_brut else []

    lignes_filtrees = [l.strip() for l in lignes_existantes if l.strip() and not l.startswith(yokai_id + "|")]
    if isinstance(nouvelles_lignes, list):
        lignes_filtrees.extend(nouvelles_lignes)
    else:
        lignes_filtrees.append(nouvelles_lignes)

    def tri_par_id(ligne):
        try:
            return int(ligne.split('|')[0])
        except ValueError:
            return float('inf')

    lignes_filtrees.sort(key=tri_par_id)
    nouveau_texte = "*".join(lignes_filtrees)

    def _reconstruire(valeur_orig):
        """Reconstruit la table dans le même format que le fichier d'origine."""
        if isinstance(valeur_orig, str):
            return nouveau_texte
        if isinstance(valeur_orig, list):
            if valeur_orig and isinstance(valeur_orig[0], str):
                return lignes_filtrees
            return [_colonnes_natives(l) for l in lignes_filtrees]
        if isinstance(valeur_orig, dict):
            return {l.split("|")[0]: _colonnes_natives(l) for l in lignes_filtrees}
        return nouveau_texte

    with open(chemin_fichier, "w", encoding="utf-8") as f:
        if donnees_json_orig is None:
            f.write(nouveau_texte)  # TXT brut
        elif isinstance(donnees_json_orig, dict) and any(c in donnees_json_orig for c in CLES_JSON_TABLE):
            cle = next(c for c in CLES_JSON_TABLE if c in donnees_json_orig)
            donnees_json_orig[cle] = _reconstruire(donnees_json_orig[cle])
            json.dump(donnees_json_orig, f, ensure_ascii=False, indent=4)
        else:
            json.dump(_reconstruire(donnees_json_orig), f, ensure_ascii=False, indent=4)

def initialiser_outils(au_demarrage=True):
    global CHEMIN_YOKAI_EXE, CHEMIN_SPRITESHEET, CHEMIN_KIND_SPRITESHEET
    dossier_outils = filedialog.askdirectory(title="1/2 : Sélectionner le dossier des OUTILS du script (yokai.exe, rankicons.png et kindicons.png)")
    
    if not dossier_outils:
        if au_demarrage: fenetre.destroy()
        return False
        
    for racine, _, fichiers in os.walk(dossier_outils):
        if "yokai.exe" in fichiers and not CHEMIN_YOKAI_EXE:
            CHEMIN_YOKAI_EXE = os.path.join(racine, "yokai.exe").replace("\\", "/")
        if "rankicons.png" in fichiers and not CHEMIN_SPRITESHEET:
            CHEMIN_SPRITESHEET = os.path.join(racine, "rankicons.png").replace("\\", "/")
        if "kindicons.png" in fichiers and not CHEMIN_KIND_SPRITESHEET:
            CHEMIN_KIND_SPRITESHEET = os.path.join(racine, "kindicons.png").replace("\\", "/")
        if CHEMIN_YOKAI_EXE and CHEMIN_SPRITESHEET and CHEMIN_KIND_SPRITESHEET: break
            
    fichiers_manquants = [nom for nom, chemin in zip(["yokai.exe", "rankicons.png", "kindicons.png"], [CHEMIN_YOKAI_EXE, CHEMIN_SPRITESHEET, CHEMIN_KIND_SPRITESHEET]) if not chemin]
    if fichiers_manquants:
        messagebox.showerror("Outils Introuvables", "Outils manquants :\n- " + "\n- ".join(fichiers_manquants))
        if au_demarrage: fenetre.destroy()
        return False
    return True

def initialiser_dossier_version(au_demarrage=True):
    global FICHIER_DB, FICHIER_SKILL_DB, FICHIER_SKILL_LEVEL_DB, FICHIER_BONUS_EFFECT_DB, FICHIER_BONUS_EFFECT_LEVEL_DB, DOSSIER_RESSOURCES, DOSSIER_SERVEUR
    dossier = filedialog.askdirectory(title="2/2 : Sélectionner le dossier de version (ou la RACINE du Serveur)")
    
    if not dossier:
        if au_demarrage: fenetre.destroy()
        return False
        
    dossier_mst = os.path.join(dossier, "Resources")
    if os.path.exists(dossier_mst) and trouver_fichier("ywp_mst_youkai", dossier_mst):
        dossier_recherche = dossier_mst
        DOSSIER_SERVEUR = dossier.replace("\\", "/")
        indexer_serveur(silencieux=True)
    else:
        dossier_recherche = dossier

    FICHIER_DB = trouver_fichier("ywp_mst_youkai", dossier_recherche)
    FICHIER_SKILL_DB = trouver_fichier("ywp_mst_youkai_skill", dossier_recherche)
    FICHIER_SKILL_LEVEL_DB = trouver_fichier("ywp_mst_youkai_skill_level", dossier_recherche)
    be_db = trouver_fichier("ywp_mst_youkai_bonus_effect", dossier_recherche)
    bel_db = trouver_fichier("ywp_mst_youkai_bonus_effect_level", dossier_recherche)
    FICHIER_BONUS_EFFECT_DB = be_db.replace("\\", "/") if be_db else ""
    FICHIER_BONUS_EFFECT_LEVEL_DB = bel_db.replace("\\", "/") if bel_db else ""
    DOSSIER_RESSOURCES = os.path.join(dossier, "youkai")
    
    fichiers_manquants = [nom for nom, chemin in zip(["ywp_mst_youkai", "ywp_mst_youkai_skill", "ywp_mst_youkai_skill_level"], [FICHIER_DB, FICHIER_SKILL_DB, FICHIER_SKILL_LEVEL_DB]) if not chemin]
    
    if fichiers_manquants:
        messagebox.showerror("Dossier Invalide", "Éléments introuvables :\n- " + "\n- ".join(fichiers_manquants))
        if au_demarrage: fenetre.destroy()
        return False
        
    return True

def vider_interface():
    global index_trouve
    index_trouve = -1
    for cases in [cases_entrees, cases_skills.values(), cases_skill_levels.values(), cases_bonus.values(), cases_bonus_niveau.values()]:
        for case in cases: case.delete(0, tk.END)
    combo_bonus_type.set("")
    subid_bonus_var.set("1")
    niveau_bonus_actuel_var.set("1")
    label_image_ayd.config(image='', text="Aucune icône") 
    label_rang.config(image='', text="Aucun")
    maj_nom_nourriture()

def traiter_ez_avec_yokai(chemin_ez):
    dossier_exe = os.path.dirname(os.path.abspath(CHEMIN_YOKAI_EXE)) or "."
    chemin_zip = chemin_ez.rsplit('.', 1)[0] + '.zip'
    if os.path.exists(chemin_zip):
        try: os.remove(chemin_zip)
        except: pass
    try: subprocess.run([os.path.abspath(CHEMIN_YOKAI_EXE), chemin_ez], shell=False, check=True, cwd=dossier_exe)
    except Exception as e: log(f"Erreur yokai.exe : {e}")
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

def comparer_versions():
    dossier_ancien = filedialog.askdirectory(title="1/2 : Sélectionner l'ANCIENNE version du jeu")
    if not dossier_ancien: return
    dossier_nouveau = filedialog.askdirectory(title="2/2 : Sélectionner la NOUVELLE version du jeu")
    if not dossier_nouveau: return
    if dossier_ancien == dossier_nouveau:
        messagebox.showwarning("Attention", "Même dossier sélectionné deux fois.")
        return

    def scanner_dossier(d_racine):
        return {os.path.relpath(os.path.join(r, f), d_racine): os.path.getsize(os.path.join(r, f)) for r, d, files in os.walk(d_racine) for f in files}

    fichiers_anciens, fichiers_nouveaux = scanner_dossier(dossier_ancien), scanner_dossier(dossier_nouveau)
    fichiers_ajoutes = [f for f in fichiers_nouveaux if f not in fichiers_anciens]
    fichiers_modifies = [f for f, t in fichiers_nouveaux.items() if f in fichiers_anciens and fichiers_anciens[f] != t]

    fen_diff = tk.Toplevel(fenetre)
    fen_diff.title("Comparaison de versions")
    fen_diff.geometry("700x500")

    tk.Label(fen_diff, text="Comparaison terminée !", font=("Arial", 12, "bold")).pack(pady=10)
    tk.Label(fen_diff, text=f"Ancien : {dossier_ancien}\nNouveau : {dossier_nouveau}", font=("Arial", 9, "italic"), fg="gray").pack(pady=5)

    zone_texte = tk.Text(fen_diff, wrap=tk.WORD, font=("Consolas", 10))
    scrollbar_txt = ttk.Scrollbar(fen_diff, command=zone_texte.yview)
    zone_texte.configure(yscrollcommand=scrollbar_txt.set)
    scrollbar_txt.pack(side=tk.RIGHT, fill=tk.Y)
    zone_texte.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

    zone_texte.insert(tk.END, f"=== FICHIERS AJOUTÉS ({len(fichiers_ajoutes)}) ===\n")
    for f in sorted(fichiers_ajoutes): zone_texte.insert(tk.END, f"[NOUVEAU] {f}\n")

    zone_texte.insert(tk.END, f"\n=== FICHIERS MODIFIÉS ({len(fichiers_modifies)}) ===\n")
    for f in sorted(fichiers_modifies): zone_texte.insert(tk.END, f"[MODIFIÉ] {f}\n")

    if not fichiers_ajoutes and not fichiers_modifies: zone_texte.insert(tk.END, "\nLes deux dossiers sont identiques.")
    zone_texte.config(state=tk.DISABLED)

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
    
    if DOSSIER_SERVEUR:
        fichier_png_racine = INDEX_SERVEUR.get(f"bl_{yokai_id}.png".lower(), fichier_png_racine)
        fichier_ayd = INDEX_SERVEUR.get(f"{yokai_id}.ayd".lower(), fichier_ayd)

    png_data = None
    try:
        if os.path.exists(fichier_png_racine):
            with open(fichier_png_racine, "rb") as f: png_data = f.read()
        elif os.path.exists(fichier_ayd):
            with zipfile.ZipFile(fichier_ayd, 'r') as zf:
                png_filename = next((name for name in zf.namelist() if name.lower().endswith('.png')), None)
                if png_filename: png_data = zf.read(png_filename)

        if png_data:
            img = Image.open(io.BytesIO(png_data))
            image_tk_reference = ImageTk.PhotoImage(img)
            label_image_ayd.config(image=image_tk_reference, text="", width=img.width, height=img.height)
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
                    uvs.append(list(struct.unpack("<2f", data.read(8))))
                skinning_count = struct.unpack('<i', data.read(4))[0]
                if skinning_count > 0:
                    for i in range(0, skinning_count, 3):
                        if i + 2 < num_vertices: faces.append([i + vertex_offset, i + 1 + vertex_offset, i + 2 + vertex_offset])
                    data.seek(data.tell() + skinning_count * 4)
                vertex_offset += num_vertices
    except struct.error: pass
    except Exception as e: log(f"Avertissement géométrie: {e}")
    return positions, faces, uvs

def visualiser_modele_3d():
    if index_trouve == -1: return
    yokai_id = cases_entrees[0].get()
    fichier_ayd = os.path.abspath(os.path.join(DOSSIER_RESSOURCES, f"{yokai_id}.ayd"))
    fichier_ez = os.path.abspath(os.path.join(DOSSIER_RESSOURCES, f"{yokai_id}.ez"))
    
    if DOSSIER_SERVEUR:
        fichier_ayd = INDEX_SERVEUR.get(f"{yokai_id}.ayd".lower(), fichier_ayd)
        fichier_ez = INDEX_SERVEUR.get(f"{yokai_id}.ez".lower(), fichier_ez)
    
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
            for i, face in enumerate(faces): triangle_uvs[i*3:i*3+3] = [uvs[face[0]], uvs[face[1]], uvs[face[2]]]
            mesh.triangle_uvs = o3d.utility.Vector2dVector(triangle_uvs)
            mesh.triangle_material_ids = o3d.utility.IntVector([0] * len(faces))
        else:
            mesh.paint_uniform_color([0.8, 0.8, 0.8])
            
        mesh.compute_vertex_normals()
        o3d.visualization.draw_geometries([mesh], window_name=f"Viewer 3D - Yo-kai ID: {yokai_id}", width=800, height=600)
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
        log(f"Base Yo-kai chargée ({len(lignes_yokai)} entrées).")

def charger_skills():
    global dictionnaire_skills
    texte_brut, _ = lire_donnees_fichier(FICHIER_SKILL_DB)
    if texte_brut:
        for ligne in texte_brut.split('*'):
            colonnes = ligne.split('|')
            if len(colonnes) >= 4:
                dictionnaire_skills[colonnes[0]] = {
                    "Nom": colonnes[1], "TypeID": colonnes[2], "Description": colonnes[3],
                    "Propriete1": colonnes[4] if len(colonnes) > 4 else "0",
                    "Propriete2": colonnes[5] if len(colonnes) > 5 else "0",
                    "Anim3D": colonnes[6] if len(colonnes) > 6 else "",
                    "Anim2D": colonnes[7] if len(colonnes) > 7 else ""
                }
        log(f"Base Âmultimes chargée ({len(dictionnaire_skills)} compétences).")

def charger_skill_levels():
    global dictionnaire_skill_levels
    texte_brut, _ = lire_donnees_fichier(FICHIER_SKILL_LEVEL_DB)
    if texte_brut:
        for ligne in texte_brut.split('*'):
            colonnes = ligne.split('|')
            if len(colonnes) >= 13:
                yokai_id, niveau = colonnes[0], colonnes[1]
                if yokai_id not in dictionnaire_skill_levels: dictionnaire_skill_levels[yokai_id] = {}
                dictionnaire_skill_levels[yokai_id][niveau] = colonnes
        log(f"Base Skill Levels chargée ({len(dictionnaire_skill_levels)} Yo-kai configurés).")

def charger_bonus_effects():
    """ywp_mst_youkai_bonus_effect : id|subid|description|type|ressource|0|0|0"""
    global dictionnaire_bonus_effect
    dictionnaire_bonus_effect = {}
    if not FICHIER_BONUS_EFFECT_DB or not os.path.exists(FICHIER_BONUS_EFFECT_DB): return
    texte_brut, _ = lire_donnees_fichier(FICHIER_BONUS_EFFECT_DB)
    if texte_brut:
        for ligne in texte_brut.split('*'):
            colonnes = ligne.split('|')
            if len(colonnes) >= 2:
                dictionnaire_bonus_effect[(colonnes[0], colonnes[1])] = colonnes
        log(f"Base Effets Bonus chargée ({len(dictionnaire_bonus_effect)} entrées).")

def charger_bonus_effect_levels():
    """ywp_mst_youkai_bonus_effect_level : id|subid|niveau|texte|valA|valB|0"""
    global dictionnaire_bonus_effect_level
    dictionnaire_bonus_effect_level = {}
    if not FICHIER_BONUS_EFFECT_LEVEL_DB or not os.path.exists(FICHIER_BONUS_EFFECT_LEVEL_DB): return
    texte_brut, _ = lire_donnees_fichier(FICHIER_BONUS_EFFECT_LEVEL_DB)
    if texte_brut:
        for ligne in texte_brut.split('*'):
            colonnes = ligne.split('|')
            if len(colonnes) >= 3:
                cle = (colonnes[0], colonnes[1])
                if cle not in dictionnaire_bonus_effect_level: dictionnaire_bonus_effect_level[cle] = {}
                dictionnaire_bonus_effect_level[cle][colonnes[2]] = colonnes
        log(f"Base Niveaux Effets Bonus chargée ({len(dictionnaire_bonus_effect_level)} effets configurés).")

def classifier_yokai(youkai_id):
    try:
        id_val = int(youkai_id)
        return "Jouable" if 8000 <= id_val < 9000 else "Boss" if 9000 <= id_val < 10000 else "Autre"
    except: return "Inconnu"

def recherche_avancee():
    global fenetre_res 
    critere, valeur = combo_recherche.get(), entree_recherche_av.get().strip().lower()
    
    if fenetre_res and fenetre_res.winfo_exists(): fenetre_res.destroy()
    if not valeur or critere not in INDEX_RECHERCHE: return
        
    index_col = INDEX_RECHERCHE[critere]
    resultats = []
    
    for ligne in lignes_yokai:
        colonnes = ligne.split('|')
        yokai_id = colonnes[0] 
        
        if index_col == "SOULT":
            if yokai_id in dictionnaire_skills and dictionnaire_skills[yokai_id]["TypeID"] == valeur:
                resultats.append(f"[{classifier_yokai(yokai_id)}] ID: {yokai_id} - Nom: {colonnes[1]}")
            continue 

        if index_col == "BONUS":
            for (yid, sid), donnees in dictionnaire_bonus_effect.items():
                if yid == yokai_id and len(donnees) > 2 and valeur in donnees[2].lower():
                    resultats.append(f"[{classifier_yokai(yokai_id)}] ID: {yokai_id} - Nom: {colonnes[1]}")
                    break
            continue

        if index_col == "BONUS_TYPE":
            for (yid, sid), donnees in dictionnaire_bonus_effect.items():
                if yid == yokai_id and len(donnees) > 3 and donnees[3].strip() == valeur:
                    resultats.append(f"[{classifier_yokai(yokai_id)}] ID: {yokai_id} - Nom: {colonnes[1]}")
                    break
            continue
            
        if len(colonnes) <= index_col: continue
        
        if index_col == 6:
            val_food = colonnes[6].strip()
            if val_food == valeur or valeur in FOOD_TYPES.get(val_food, "").lower():
                resultats.append(f"[{classifier_yokai(yokai_id)}] ID: {yokai_id} - Nom: {colonnes[1]}")
            continue

        if index_col == 1:
            nom_jap = colonnes[1].lower()
            nom_lecture = colonnes[31].lower() if len(colonnes) > 31 else ""
            if valeur in nom_jap or valeur in nom_lecture:
                resultats.append(f"[{classifier_yokai(yokai_id)}] ID: {yokai_id} - Nom: {colonnes[1]}")
        elif colonnes[index_col].strip().lower() == valeur:
            resultats.append(f"[{classifier_yokai(yokai_id)}] ID: {yokai_id} - Nom: {colonnes[1]}")
                
    if not resultats:
        messagebox.showwarning("Introuvable", "Aucun résultat trouvé.")
        return

    fenetre_res = tk.Toplevel(fenetre)
    fenetre_res.title(f"Résultats ({len(resultats)})")
    fenetre_res.geometry("400x300")
    tk.Label(fenetre_res, text="Double-cliquez pour charger ce Yo-kai", font=("Arial", 9, "italic")).pack(pady=5)
    
    listbox = tk.Listbox(fenetre_res, font=("Arial", 10))
    listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    for res in resultats: listbox.insert(tk.END, res)
        
    def charger_id_selectionne(event):
        if listbox.curselection():
            try:
                entree_recherche_id.delete(0, tk.END)
                entree_recherche_id.insert(0, listbox.get(listbox.curselection()[0]).split("ID: ")[1].split(" - ")[0])
                charger_yokai_par_id()
                fenetre_res.destroy()
            except IndexError: pass
            
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
            charger_bonus_effet_pour_yokai(id_recherche)
            return 

    vider_interface()
    messagebox.showwarning("Introuvable", "Aucun Yo-kai ne possède ce YoukaiId.")

def obtenir_dernier_id():
    messagebox.showinfo("ID dispo", f"💡 Prochain ID libre : {max([int(l.split('|')[0]) for l in lignes_yokai if l.split('|')[0].isdigit()], default=0) + 1}")
    
def maj_nom_nourriture(event=None):
    if 'label_nom_food' in globals():
        valeur = cases_entrees[6].get().strip() if len(cases_entrees) > 6 else ""
        nom = FOOD_TYPES.get(valeur, "Inconnu")
        label_nom_food.config(text=f"({nom})", fg="#0066cc" if nom != "Inconnu" else "gray")

def decouper_icone(img_complete, col, lig, nb_colonnes, nb_lignes, hauteur_cible=48):
    """Découpe une cellule sans laisser de colonne voisine, puis la recadre."""
    largeur, hauteur = img_complete.size
    x0 = round(col * largeur / nb_colonnes)
    y0 = round(lig * hauteur / nb_lignes)
    x1 = round((col + 1) * largeur / nb_colonnes)
    y1 = round((lig + 1) * hauteur / nb_lignes)

    icone = img_complete.convert("RGBA").crop((x0, y0, x1, y1))
    # Les feuilles anciennes utilisent parfois un fond uniforme non transparent.
    # On le rend transparent afin que getbbox recadre aussi ces marges.
    pixels = icone.load()
    fond = pixels[0, 0][:3]
    for y in range(icone.height):
        for x in range(icone.width):
            r, g, b, a = pixels[x, y]
            if (r, g, b) == fond:
                pixels[x, y] = (r, g, b, 0)

    boite = icone.getchannel("A").getbbox()
    if boite:
        icone = icone.crop(boite)
    if icone.height and hauteur_cible and icone.height != hauteur_cible:
        largeur_cible = max(1, round(icone.width * hauteur_cible / icone.height))
        icone = icone.resize((largeur_cible, hauteur_cible), Image.Resampling.LANCZOS)
    return icone

def remplir_cases(colonnes):
    global image_rang_reference, image_kind_reference
    yokai_id = colonnes[0]

    for i, case in enumerate(cases_entrees):
        case.delete(0, tk.END)
        if i < len(colonnes): case.insert(0, colonnes[i])
            
    maj_nom_nourriture()

    for case in cases_skills.values(): case.delete(0, tk.END)

    if yokai_id in dictionnaire_skills:
        skill = dictionnaire_skills[yokai_id]
        for k in ["Nom", "Description", "Propriete1", "Propriete2", "Anim3D", "Anim2D"]:
            cases_skills[k].insert(0, skill[k])
        
        type_id = skill["TypeID"]
        combo_soult_type.set(f"{type_id} - {SOULT_TYPES.get(type_id, 'Inconnu')}")

    if len(colonnes) > 3:
        valeur_rarite = colonnes[3]
        if valeur_rarite in COORDONNEES_RANGS:
            try:
                img_complete = Image.open(CHEMIN_SPRITESHEET)
                col, lig = COORDONNEES_RANGS[valeur_rarite]
                icone = decouper_icone(img_complete, col, lig, 8, 3)
                image_rang_reference = ImageTk.PhotoImage(icone)
                label_rang.config(image=image_rang_reference, text="")
            except Exception as e:
                label_rang.config(image='', text=f"ID Rareté : {valeur_rarite}")
        else:
            label_rang.config(image='', text="Aucun")

    if len(colonnes) > 4 and colonnes[4] in COORDONNEES_KINDS and CHEMIN_KIND_SPRITESHEET and 'label_kind' in globals():
        try:
            img_complete = Image.open(CHEMIN_KIND_SPRITESHEET)
            col, lig = COORDONNEES_KINDS[colonnes[4]]
            icone = decouper_icone(img_complete, col, lig, 3, 4)
            image_kind_reference = ImageTk.PhotoImage(icone)
            label_kind.config(image=image_kind_reference, text="")
        except Exception:
            label_kind.config(image='', text=f"ID Tribu : {colonnes[4]}")
    elif 'label_kind' in globals():
        label_kind.config(image='', text="Aucune")

def afficher_donnees_niveau(event=None, depuis_code=False):
    global niveau_precedent
    yokai_id = cases_entrees[0].get()
    if not yokai_id: return
    
    if not depuis_code:
        if yokai_id not in dictionnaire_skill_levels: dictionnaire_skill_levels[yokai_id] = {}
        cols_lvl = [""] * 13
        cols_lvl[0], cols_lvl[1] = yokai_id, niveau_precedent
        for idx, case in cases_skill_levels.items(): cols_lvl[idx] = case.get()
        dictionnaire_skill_levels[yokai_id][niveau_precedent] = cols_lvl
    
    niveau_choisi = niveau_actuel_var.get()
    for case in cases_skill_levels.values(): case.delete(0, tk.END)
        
    if yokai_id in dictionnaire_skill_levels and niveau_choisi in dictionnaire_skill_levels[yokai_id]:
        donnees_niveau = dictionnaire_skill_levels[yokai_id][niveau_choisi]
        for idx, case in cases_skill_levels.items():
            if idx < len(donnees_niveau): case.insert(0, donnees_niveau[idx])
                
    niveau_precedent = niveau_choisi

# ==========================================
# EFFETS BONUS (liés au YoukaiId courant)
# ==========================================
def charger_bonus_effet_pour_yokai(yokai_id):
    """Appelée quand un Yo-kai est chargé : peuple le bloc Effets Bonus avec le SubId 1."""
    global niveau_bonus_precedent
    subid_bonus_var.set("1")
    niveau_bonus_actuel_var.set("1")
    niveau_bonus_precedent = "1"
    afficher_donnees_bonus_effect(depuis_code=True)

def afficher_donnees_bonus_effect(event=None, depuis_code=False):
    """Affiche description/type/ressource pour (yokai_id, subid) actuellement sélectionnés."""
    yokai_id = cases_entrees[0].get()
    subid = subid_bonus_var.get().strip()
    if not yokai_id or not subid: return
    cle = (yokai_id, subid)
    donnees = dictionnaire_bonus_effect.get(cle)
    for champ in ("Description", "Ressource"):
        cases_bonus[champ].delete(0, tk.END)
    if donnees and len(donnees) >= 5:
        cases_bonus["Description"].insert(0, donnees[2])
        cases_bonus["Ressource"].insert(0, donnees[4])
        type_id = donnees[3] if len(donnees) > 3 else "1"
        combo_bonus_type.set(f"{type_id} - {YW_BONUS_EFFECTS.get(type_id, 'Inconnu')}")
    else:
        combo_bonus_type.set("")
    afficher_donnees_bonus_niveau(depuis_code=True)

def afficher_donnees_bonus_niveau(event=None, depuis_code=False):
    """Affiche/sauvegarde les champs de niveau pour (yokai_id, subid, niveau) — même logique que afficher_donnees_niveau."""
    global niveau_bonus_precedent
    yokai_id = cases_entrees[0].get()
    subid = subid_bonus_var.get().strip()
    if not yokai_id or not subid: return
    cle = (yokai_id, subid)

    if not depuis_code:
        dictionnaire_bonus_effect_level.setdefault(cle, {})
        cols_niv = ["", "", "", "", "", "", "0"]
        cols_niv[0], cols_niv[1], cols_niv[2] = yokai_id, subid, niveau_bonus_precedent
        for idx, case in cases_bonus_niveau.items(): cols_niv[idx] = case.get()
        dictionnaire_bonus_effect_level[cle][niveau_bonus_precedent] = cols_niv

    niveau_choisi = niveau_bonus_actuel_var.get()
    for case in cases_bonus_niveau.values(): case.delete(0, tk.END)

    if cle in dictionnaire_bonus_effect_level and niveau_choisi in dictionnaire_bonus_effect_level[cle]:
        donnees_niveau = dictionnaire_bonus_effect_level[cle][niveau_choisi]
        for idx, case in cases_bonus_niveau.items():
            if idx < len(donnees_niveau): case.insert(0, donnees_niveau[idx])

    niveau_bonus_precedent = niveau_choisi

# ==========================================
# FONCTIONS DE SAUVEGARDE ET CHARGEMENT MODS
# ==========================================
def ouvrir_menu_sauvegarde():
    yokai_id = cases_entrees[0].get().strip()
    if not yokai_id:
        messagebox.showerror("Erreur", "Veuillez d'abord définir un YoukaiId (champ 0).")
        return

    if yokai_id not in dictionnaire_skill_levels: dictionnaire_skill_levels[yokai_id] = {}
    cols_lvl = [""] * 13
    cols_lvl[0], cols_lvl[1] = yokai_id, niveau_actuel_var.get()
    for idx, case in cases_skill_levels.items(): cols_lvl[idx] = case.get()
    dictionnaire_skill_levels[yokai_id][niveau_actuel_var.get()] = cols_lvl

    fen_menu = tk.Toplevel(fenetre)
    fen_menu.title("Options de sauvegarde globale")
    fen_menu.geometry("400x180")
    tk.Label(fen_menu, text=f"Sauvegarder les données du Yo-kai {yokai_id}", font=("Arial", 11, "bold")).pack(pady=10)
    tk.Button(fen_menu, text="💾 Enregistrer dans les index originaux (Écraser)", bg="#f8d7da", command=lambda: executer_sauvegarde(yokai_id, "original", fen_menu)).pack(fill=tk.X, padx=20, pady=5)
    tk.Button(fen_menu, text="📁 Exporter dans un dossier Mod (Isolé)", bg="#d4edda", command=lambda: executer_sauvegarde(yokai_id, "isole", fen_menu)).pack(fill=tk.X, padx=20, pady=5)

def executer_sauvegarde(yokai_id, mode, fen_menu):
    fen_menu.destroy()
    
    valeurs_yokai = [case.get() for case in cases_entrees]
    while len(valeurs_yokai) > 35 and not valeurs_yokai[-1]: valeurs_yokai.pop()
    ligne_yokai = "|".join(valeurs_yokai)
    
    type_id = combo_soult_type.get().split(" - ")[0] if " - " in combo_soult_type.get() else "-1"
    ligne_skill = "|".join([
        yokai_id, cases_skills["Nom"].get(), type_id, cases_skills["Description"].get(),
        cases_skills["Propriete1"].get(), cases_skills["Propriete2"].get(),
        cases_skills["Anim3D"].get(), cases_skills["Anim2D"].get()
    ])
    
    lignes_levels = []
    base_lvl_data = dictionnaire_skill_levels.get(yokai_id, {}).get(niveau_actuel_var.get(), [""]*13)
    
    for lvl in range(1, 8):
        data = dictionnaire_skill_levels.get(yokai_id, {}).get(str(lvl), list(base_lvl_data))
        data[1] = str(lvl)
        while len(data) < 13: data.append("") 
        data[0] = yokai_id
        lignes_levels.append("|".join(data))

    # --- Effets Bonus : on force la sauvegarde de l'écran courant dans les dictionnaires,
    # puis on reconstruit toutes les lignes (tous SubId confondus) pour ce yokai_id ---
    afficher_donnees_bonus_niveau(depuis_code=False)
    subid_courant = subid_bonus_var.get().strip()
    if subid_courant:
        cle_courante = (yokai_id, subid_courant)
        type_bonus_id = combo_bonus_type.get().split(" - ")[0] if " - " in combo_bonus_type.get() else "1"
        dictionnaire_bonus_effect[cle_courante] = [
            yokai_id, subid_courant, cases_bonus["Description"].get(), type_bonus_id,
            cases_bonus["Ressource"].get(), "0", "0", "0"
        ]

    lignes_bonus_effect = ["|".join(v) for k, v in dictionnaire_bonus_effect.items() if k[0] == yokai_id]
    lignes_bonus_effect_level = []
    for (yid, sid), niveaux in dictionnaire_bonus_effect_level.items():
        if yid != yokai_id: continue
        for niveau, data in niveaux.items():
            data = list(data)
            while len(data) < 7: data.append("0")
            data[0], data[1], data[2] = yokai_id, sid, niveau
            lignes_bonus_effect_level.append("|".join(data))
    
    if mode == "isole":
        dossier_parent = filedialog.askdirectory(title="Choisir le dossier de destination pour le Mod")
        if not dossier_parent: return
        chemin_mod = os.path.join(dossier_parent, f"Yokai_{yokai_id}")
        os.makedirs(chemin_mod, exist_ok=True)
        try:
            fichiers_a_ecrire = [("ywp_mst_youkai.json", ligne_yokai), ("ywp_mst_youkai_skill.json", ligne_skill), ("ywp_mst_youkai_skill_level.json", "*".join(lignes_levels))]
            if lignes_bonus_effect:
                fichiers_a_ecrire.append(("ywp_mst_youkai_bonus_effect.json", "*".join(lignes_bonus_effect)))
            if lignes_bonus_effect_level:
                fichiers_a_ecrire.append(("ywp_mst_youkai_bonus_effect_level.json", "*".join(lignes_bonus_effect_level)))
            for nom, data in fichiers_a_ecrire:
                with open(os.path.join(chemin_mod, nom), "w", encoding="utf-8") as f:
                    json.dump({"tableData": data, "version": "1"}, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("Succès", f"Dossier Mod créé avec succès dans :\n{chemin_mod}")
        except Exception as e:
            messagebox.showerror("Erreur Mod", str(e))
            
    elif mode == "original":
        try:
            maj_fichier_original(FICHIER_DB, ligne_yokai, yokai_id)
            maj_fichier_original(FICHIER_SKILL_DB, ligne_skill, yokai_id)
            maj_fichier_original(FICHIER_SKILL_LEVEL_DB, lignes_levels, yokai_id)
            if FICHIER_BONUS_EFFECT_DB and lignes_bonus_effect:
                maj_fichier_original(FICHIER_BONUS_EFFECT_DB, lignes_bonus_effect, yokai_id)
            if FICHIER_BONUS_EFFECT_LEVEL_DB and lignes_bonus_effect_level:
                maj_fichier_original(FICHIER_BONUS_EFFECT_LEVEL_DB, lignes_bonus_effect_level, yokai_id)
            
            charger_fichier()
            charger_skills()
            charger_skill_levels()
            charger_bonus_effects()
            charger_bonus_effect_levels()
            messagebox.showinfo("Succès", f"Les index d'origine ont été mis à jour et triés pour l'ID {yokai_id} !")
        except Exception as e:
            messagebox.showerror("Erreur DB Originale", str(e))
          
def sauvegarder_skill_sous():
    if index_trouve == -1: return messagebox.showerror("Erreur", "Aucun Yo-kai chargé !")
        
    soult_id = cases_entrees[0].get()
    type_id = combo_soult_type.get().split(" - ")[0] if " - " in combo_soult_type.get() else "-1"
    
    nouvelle_ligne = "|".join([
        soult_id, cases_skills["Nom"].get(), type_id, cases_skills["Description"].get(),
        cases_skills["Propriete1"].get(), cases_skills["Propriete2"].get(),
        cases_skills["Anim3D"].get(), cases_skills["Anim2D"].get()
    ])
    
    chemin_sauvegarde = filedialog.asksaveasfilename(defaultextension=".json", initialfile="ywp_mst_skill_mod.json", title="Enregistrer sous...", filetypes=[("JSON", "*.json"), ("TXT", "*.txt"), ("Tous", "*.*")])
    if not chemin_sauvegarde: return
    
    try:
        maj_fichier_original(chemin_sauvegarde if os.path.exists(chemin_sauvegarde) else FICHIER_SKILL_DB, nouvelle_ligne, soult_id)
        messagebox.showinfo("Succès", f"Fichier sauvegardé avec succès et trié sous :\n{chemin_sauvegarde}")
    except Exception as e:
        messagebox.showerror("Erreur de sauvegarde", str(e))

def charger_dossier_mod():
    global index_trouve, niveau_precedent
    dossier_mod = filedialog.askdirectory(title="Sélectionner le dossier du Mod à charger")
    if not dossier_mod: return

    fichier_yokai = trouver_fichier("ywp_mst_youkai", dossier_mod)
    if not fichier_yokai: return messagebox.showerror("Erreur", "Fichier ywp_mst_youkai introuvable.")

    try:
        texte_yokai, _ = lire_donnees_fichier(fichier_yokai)
        if texte_yokai:
            colonnes = texte_yokai.split('|')
            yokai_id = colonnes[0]

        fichier_skill = trouver_fichier("ywp_mst_youkai_skill", dossier_mod)
        if fichier_skill and lire_donnees_fichier(fichier_skill)[0]:
            cols_skill = lire_donnees_fichier(fichier_skill)[0].split('|')
            if len(cols_skill) >= 4:
                dictionnaire_skills[yokai_id] = {
                    "Nom": cols_skill[1], "TypeID": cols_skill[2], "Description": cols_skill[3],
                    "Propriete1": cols_skill[4] if len(cols_skill) > 4 else "0", "Propriete2": cols_skill[5] if len(cols_skill) > 5 else "0",
                    "Anim3D": cols_skill[6] if len(cols_skill) > 6 else "", "Anim2D": cols_skill[7] if len(cols_skill) > 7 else ""
                }

        fichier_lvl = trouver_fichier("ywp_mst_youkai_skill_level", dossier_mod)
        if fichier_lvl and lire_donnees_fichier(fichier_lvl)[0]:
            dictionnaire_skill_levels[yokai_id] = {}
            for l in lire_donnees_fichier(fichier_lvl)[0].split('*'):
                cols = l.split('|')
                if len(cols) >= 13: dictionnaire_skill_levels[yokai_id][cols[1]] = cols

        fichier_be = trouver_fichier("ywp_mst_youkai_bonus_effect", dossier_mod)
        if fichier_be and lire_donnees_fichier(fichier_be)[0]:
            for l in lire_donnees_fichier(fichier_be)[0].split('*'):
                cols = l.split('|')
                if len(cols) >= 2 and cols[0] == yokai_id:
                    dictionnaire_bonus_effect[(cols[0], cols[1])] = cols

        fichier_bel = trouver_fichier("ywp_mst_youkai_bonus_effect_level", dossier_mod)
        if fichier_bel and lire_donnees_fichier(fichier_bel)[0]:
            for l in lire_donnees_fichier(fichier_bel)[0].split('*'):
                cols = l.split('|')
                if len(cols) >= 3 and cols[0] == yokai_id:
                    cle = (cols[0], cols[1])
                    dictionnaire_bonus_effect_level.setdefault(cle, {})[cols[2]] = cols

        entree_recherche_id.delete(0, tk.END); entree_recherche_id.insert(0, yokai_id)
        
        index_trouve = next((i for i, l in enumerate(lignes_yokai) if l.startswith(yokai_id + "|")), -1)
        remplir_cases(colonnes)
        niveau_actuel_var.set("1"); niveau_precedent = "1"
        afficher_donnees_niveau(depuis_code=True)
        charger_icone_ayd()
        charger_bonus_effet_pour_yokai(yokai_id)
        messagebox.showinfo("Succès", f"Mod du Yo-kai {yokai_id} chargé avec succès !")
    except Exception as e:
        messagebox.showerror("Erreur", f"Erreur lors du chargement du Mod :\n{e}")

def recherche_multi_criteres():
    """Recherche AND multi-critères, sans modifier la recherche simple existante."""
    fen_rech = tk.Toplevel(fenetre)
    fen_rech.title("Recherche avancée multi-critères")
    fen_rech.geometry("760x560")
    fen_rech.transient(fenetre)

    champs = [
        ("Nom du Yo-kai", "name"), ("Rang / Rarity", "rank"),
        ("Tribu / Kind", "kind"), ("Nourriture / FoodType", "food"),
        ("Dictionary ID", "dictionary"), ("Type Âmultime / SoultType", "soult"),
        ("Effet Bonus (texte)", "bonus"), ("Effet Bonus (ID Type)", "bonus_type"),
        ("MaxLevel", "maxlevel"), ("BaseHp min", "min_basehp"),
        ("BaseHp max", "max_basehp"), ("MaxHp min", "min_maxhp"),
        ("MaxHp max", "max_maxhp"), ("BaseAtk min", "min_baseatk"),
        ("BaseAtk max", "max_baseatk"), ("MaxAtk min", "min_maxatk"),
        ("MaxAtk max", "max_maxatk")
    ]
    entrees = {}
    cadre = tk.Frame(fen_rech)
    cadre.pack(fill=tk.X, padx=10, pady=8)
    for i, (label, cle) in enumerate(champs):
        r, c = divmod(i, 4)
        tk.Label(cadre, text=label + " :").grid(row=r * 2, column=c, sticky="w", padx=4)
        e = tk.Entry(cadre, width=17)
        e.grid(row=r * 2 + 1, column=c, sticky="ew", padx=4, pady=(0, 5))
        entrees[cle] = e
    for c in range(4): cadre.grid_columnconfigure(c, weight=1)

    zone = tk.Frame(fen_rech)
    zone.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    liste = tk.Listbox(zone, font=("Arial", 10), exportselection=False)
    barre = ttk.Scrollbar(zone, orient="vertical", command=liste.yview)
    liste.configure(yscrollcommand=barre.set)
    liste.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    barre.pack(side=tk.RIGHT, fill=tk.Y)
    correspondances = []

    def nombre(cle, colonne):
        valeur = entrees[cle].get().strip()
        if not valeur: return True
        try: cible = float(valeur)
        except ValueError: return False
        try: return float(colonne) >= cible
        except (TypeError, ValueError): return False

    def rechercher():
        correspondances.clear(); liste.delete(0, tk.END)
        for ligne in lignes_yokai:
            colonnes = ligne.split('|')
            if len(colonnes) <= 14: continue
            def contient(cle, index, traductions=None):
                valeur = entrees[cle].get().strip().lower()
                if not valeur: return True
                contenu = colonnes[index].strip().lower() if index < len(colonnes) else ""
                noms = (traductions or {}).get(contenu, "").lower()
                return valeur in contenu or (noms and valeur in noms)
            if not contient("name", 1): continue
            if not contient("rank", 3): continue
            if not contient("kind", 4): continue
            if not contient("food", 6, FOOD_TYPES): continue
            if not contient("dictionary", 14): continue
            soult = entrees["soult"].get().strip().lower()
            if soult:
                skill = dictionnaire_skills.get(colonnes[0], {})
                typ = skill.get("TypeID", "").lower()
                nom_typ = SOULT_TYPES.get(skill.get("TypeID", ""), "").lower()
                if soult not in typ and soult not in nom_typ: continue
            bonus = entrees["bonus"].get().strip().lower()
            if bonus:
                trouve = any(yid == colonnes[0] and len(d) > 2 and bonus in d[2].lower()
                             for (yid, sid), d in dictionnaire_bonus_effect.items())
                if not trouve: continue
            bonus_type = entrees["bonus_type"].get().strip()
            if bonus_type:
                trouve = any(yid == colonnes[0] and len(d) > 3 and d[3].strip() == bonus_type
                             for (yid, sid), d in dictionnaire_bonus_effect.items())
                if not trouve: continue
            if not contient("maxlevel", 7): continue
            filtres = (("min_basehp", 8, True), ("max_basehp", 8, False),
                       ("min_maxhp", 9, True), ("max_maxhp", 9, False),
                       ("min_baseatk", 10, True), ("max_baseatk", 10, False),
                       ("min_maxatk", 11, True), ("max_maxatk", 11, False))
            valide = True
            for cle, idx, minimum in filtres:
                v = entrees[cle].get().strip()
                if not v: continue
                try: cible, actuel = float(v), float(colonnes[idx])
                except ValueError: valide = False; break
                if (minimum and actuel < cible) or (not minimum and actuel > cible): valide = False; break
            if not valide: continue
            correspondances.append(colonnes[0])
            liste.insert(tk.END, f"[{classifier_yokai(colonnes[0])}] ID: {colonnes[0]} - Nom: {colonnes[1]}")
        if not correspondances: liste.insert(tk.END, "Aucun résultat.")

    def charger_selection(event=None):
        selection = liste.curselection()
        if not selection or selection[0] >= len(correspondances): return
        entree_recherche_id.delete(0, tk.END)
        entree_recherche_id.insert(0, correspondances[selection[0]])
        charger_yokai_par_id()
        fen_rech.destroy()

    tk.Button(fen_rech, text="Rechercher (ET)", command=rechercher).pack(side=tk.LEFT, padx=10, pady=8)
    tk.Button(fen_rech, text="Fermer", command=fen_rech.destroy).pack(side=tk.RIGHT, padx=10, pady=8)
    liste.bind("<Double-Button-1>", charger_selection)
    liste.bind("<Return>", charger_selection)
    if mode_sombre_actif: appliquer_theme(fen_rech)

def ouvrir_editeur_niveaux_groupe():
    """Édite les sept niveaux dans la même table et réutilise le dictionnaire existant."""
    yokai_id = cases_entrees[0].get().strip()
    if not yokai_id:
        messagebox.showwarning("Niveau", "Veuillez d'abord charger ou définir un Yo-kai.")
        return
    fen_niv = tk.Toplevel(fenetre)
    fen_niv.title(f"Éditeur groupé des niveaux - {yokai_id}")
    fen_niv.geometry("1100x470")
    noms = globals().get("champs_niveaux", [])
    colonnes_editables = [idx for _, idx in noms]
    table = tk.Frame(fen_niv); table.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
    tk.Label(table, text="Niveau", font=("Arial", 9, "bold")).grid(row=0, column=0, padx=3, pady=3)
    for col, (nom, _) in enumerate(noms, 1):
        tk.Label(table, text=nom, font=("Arial", 9, "bold"), wraplength=110).grid(row=0, column=col, padx=3, pady=3)
    cellules = {}
    for niveau in range(1, 8):
        tk.Label(table, text=str(niveau)).grid(row=niveau, column=0, padx=3, pady=3)
        donnees = dictionnaire_skill_levels.get(yokai_id, {}).get(str(niveau), [""] * 13)
        for col, idx in enumerate(colonnes_editables, 1):
            e = tk.Entry(table, width=16)
            if idx < len(donnees): e.insert(0, donnees[idx])
            e.grid(row=niveau, column=col, padx=2, pady=2)
            cellules[(niveau, idx)] = e
    def appliquer_ligne():
        try:
            source = int(var_source.get())
        except ValueError:
            return
        valeurs_src = {idx: cellules[(source, idx)].get() for idx in colonnes_editables}
        for niveau in range(1, 8):
            if niveau == source:
                continue
            for idx in colonnes_editables:
                if idx == 1:          # ne jamais toucher au numéro de niveau
                    continue
                cellules[(niveau, idx)].delete(0, tk.END)
                cellules[(niveau, idx)].insert(0, valeurs_src[idx])
    def enregistrer():
        dictionnaire_skill_levels.setdefault(yokai_id, {})
        for niveau in range(1, 8):
            data = list(dictionnaire_skill_levels[yokai_id].get(str(niveau), [""] * 13))
            while len(data) < 13:
                data.append("")
            data[0] = yokai_id
            for idx in colonnes_editables:
                if idx == 1:
                    continue
                data[idx] = cellules[(niveau, idx)].get()
            data[1] = str(niveau)     # toujours forcé en dernier, jamais écrasable
            dictionnaire_skill_levels[yokai_id][str(niveau)] = data
        if niveau_actuel_var.get() in dictionnaire_skill_levels[yokai_id]:
            afficher_donnees_niveau(depuis_code=True)
        fen_niv.destroy()
    bas = tk.Frame(fen_niv); bas.pack(fill=tk.X, padx=8, pady=5)
    tk.Label(bas, text="Ligne source à appliquer à toutes :").pack(side=tk.LEFT)
    var_source = tk.StringVar(value="1")
    ttk.Combobox(bas, textvariable=var_source, values=[str(i) for i in range(1, 8)], width=4, state="readonly").pack(side=tk.LEFT, padx=5)
    tk.Button(bas, text="Appliquer à tous", command=appliquer_ligne).pack(side=tk.LEFT, padx=5)
    tk.Button(bas, text="Enregistrer", command=enregistrer).pack(side=tk.RIGHT, padx=5)
    tk.Button(bas, text="Fermer", command=fen_niv.destroy).pack(side=tk.RIGHT, padx=5)
    if mode_sombre_actif: appliquer_theme(fen_niv)

# ==========================================
# THÈME CLAIR / SOMBRE
# ==========================================
THEME_CLAIR = {
    "bg": "#f0f0f0", "bg_alt": "#ffffff", "fg": "#000000",
    "entry_bg": "#ffffff", "entry_fg": "#000000",
    "btn_bg": "#e2e3e5", "btn_fg": "#000000",
    "label_bg": "#f0f0f0",
}
THEME_SOMBRE = {
    "bg": "#2b2b2b", "bg_alt": "#3c3c3c", "fg": "#e6e6e6",
    "entry_bg": "#3c3c3c", "entry_fg": "#e6e6e6",
    "btn_bg": "#454545", "btn_fg": "#e6e6e6",
    "label_bg": "#2b2b2b",
}

COULEURS_BOUTONS_SOMBRE = {
    "#d4edda": "#2f5233",  # vert (Modèle 3D)
    "#fff3cd": "#5c4a1a",  # jaune (Nouvel ID)
    "#add8e6": "#1f3f52",  # bleu (Yo-kai Global)
    "#f8d7da": "#5a2a2e",  # rouge (Changer dossiers)
    "#cce5ff": "#1f3f52",  # bleu clair (Charger)
    "#e2e3e5": "#454545",  # gris neutre
}
COULEURS_BOUTONS_CLAIR = {v: k for k, v in COULEURS_BOUTONS_SOMBRE.items()}

# Cadres/zones colorées (Âmultime, Niveaux d'Âmultime, etc.)
COULEURS_CADRES_SOMBRE = {
    "#fffbea": "#3f3a28",  # crème (cadre Âmultime)
    "#fffde7": "#3f3a28",
    "#fff9e6": "#3f3a28",  # crème (cadre Âmultime, couleur réellement utilisée en UI)
    "#e6f2ff": "#25313d",  # bleu pâle (cadre Niveaux)
    "#e8f5e9": "#243d26",  # vert pâle (cadre Effets Bonus)
    "#f3e8ff": "#332947",  # lavande (cadre Niveaux d'Effet Bonus)
    "#f0f0f0": "#2b2b2b",
    "#ffffff": "#3c3c3c",
}
COULEURS_CADRES_CLAIR = {
    "#3f3a28": "#fff9e6",
    "#25313d": "#e6f2ff",
    "#243d26": "#e8f5e9",
    "#332947": "#f3e8ff",
    "#2b2b2b": "#f0f0f0",
    "#3c3c3c": "#ffffff",
}

mode_sombre_actif = False


def _bg_cible(bg_actuel, theme):
    """Retourne la couleur de fond adaptée au thème pour un conteneur/label."""
    bg_actuel = str(bg_actuel).lower()
    table = COULEURS_CADRES_SOMBRE if mode_sombre_actif else COULEURS_CADRES_CLAIR
    if bg_actuel in table:
        return table[bg_actuel]
    # couleur inconnue : on ne la casse pas si elle est déjà cohérente
    if mode_sombre_actif and bg_actuel in COULEURS_CADRES_CLAIR:
        return bg_actuel
    if not mode_sombre_actif and bg_actuel in COULEURS_CADRES_SOMBRE:
        return bg_actuel
    return theme["bg"]


def appliquer_style_ttk(theme):
    """Applique le thème aux widgets ttk (Combobox, Scrollbar, Separator)."""
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure("TCombobox",
                    fieldbackground=theme["entry_bg"],
                    background=theme["btn_bg"],
                    foreground=theme["entry_fg"],
                    arrowcolor=theme["fg"],
                    bordercolor=theme["btn_bg"],
                    lightcolor=theme["btn_bg"],
                    darkcolor=theme["btn_bg"])
    style.map("TCombobox",
              fieldbackground=[("readonly", theme["entry_bg"])],
              foreground=[("readonly", theme["entry_fg"])],
              background=[("readonly", theme["btn_bg"])])

    style.configure("Vertical.TScrollbar",
                    background=theme["btn_bg"],
                    troughcolor=theme["bg"],
                    bordercolor=theme["bg"],
                    arrowcolor=theme["fg"])
    style.configure("Horizontal.TScrollbar",
                    background=theme["btn_bg"],
                    troughcolor=theme["bg"],
                    bordercolor=theme["bg"],
                    arrowcolor=theme["fg"])

    style.configure("TFrame", background=theme["bg"])
    style.configure("TLabel", background=theme["bg"], foreground=theme["fg"])
    style.configure("TSeparator", background=theme["bg"])


def appliquer_theme(widget=None, theme=None):
    """Parcourt récursivement tous les widgets et applique le thème donné."""
    global mode_sombre_actif
    if theme is None:
        theme = THEME_SOMBRE if mode_sombre_actif else THEME_CLAIR
    if widget is None:
        widget = fenetre
        appliquer_style_ttk(theme)

    try:
        classe = widget.winfo_class()

        # --- Boutons : on conserve l'identité colorée ---
        if classe == "Button":
            bg_actuel = str(widget.cget("bg")).lower()
            table = COULEURS_BOUTONS_SOMBRE if mode_sombre_actif else COULEURS_BOUTONS_CLAIR
            autre = COULEURS_BOUTONS_CLAIR if mode_sombre_actif else COULEURS_BOUTONS_SOMBRE
            if bg_actuel in table:
                nouvelle_bg = table[bg_actuel]
            elif bg_actuel in autre:
                nouvelle_bg = bg_actuel  # déjà dans le bon thème
            else:
                nouvelle_bg = theme["btn_bg"]
            widget.configure(bg=nouvelle_bg, fg=theme["btn_fg"],
                             activebackground=nouvelle_bg,
                             activeforeground=theme["btn_fg"],
                             highlightbackground=theme["bg"])

        # --- Conteneurs (attention : Labelframe avec f minuscule !) ---
        elif classe in ("Frame", "Toplevel", "Labelframe", "LabelFrame", "Tk"):
            nouvelle_bg = _bg_cible(widget.cget("bg"), theme)
            widget.configure(bg=nouvelle_bg)
            if classe in ("Labelframe", "LabelFrame"):
                widget.configure(fg=theme["fg"])

        elif classe == "Canvas":
            widget.configure(bg=_bg_cible(widget.cget("bg"), theme),
                             highlightbackground=theme["bg"],
                             highlightthickness=0)

        elif classe == "Label":
            widget.configure(bg=_bg_cible(widget.cget("bg"), theme),
                             fg=theme["fg"])

        elif classe == "Entry":
            widget.configure(bg=theme["entry_bg"], fg=theme["entry_fg"],
                             insertbackground=theme["entry_fg"],
                             disabledbackground=theme["bg"],
                             disabledforeground="#8a8a8a",
                             highlightbackground=theme["bg"])

        elif classe == "Text":
            widget.configure(bg=theme["entry_bg"], fg=theme["entry_fg"],
                             insertbackground=theme["entry_fg"])

        elif classe == "Listbox":
            widget.configure(bg=theme["entry_bg"], fg=theme["entry_fg"],
                             selectbackground="#1f3f52",
                             selectforeground=theme["fg"])

        elif classe in ("Checkbutton", "Radiobutton"):
            widget.configure(bg=_bg_cible(widget.cget("bg"), theme),
                             fg=theme["fg"],
                             activebackground=theme["bg"],
                             activeforeground=theme["fg"],
                             selectcolor=theme["entry_bg"])

    except (tk.TclError, AttributeError):
        pass

    for enfant in widget.winfo_children():
        appliquer_theme(enfant, theme)


def basculer_theme():
    global mode_sombre_actif
    mode_sombre_actif = not mode_sombre_actif
    theme = THEME_SOMBRE if mode_sombre_actif else THEME_CLAIR
    fenetre.configure(bg=theme["bg"])
    appliquer_theme(fenetre, theme)
    btn_theme.config(text="☀️ Mode Clair" if mode_sombre_actif else "🌙 Mode Sombre")


# ==========================================
# INTERFACE GRAPHIQUE
# ==========================================
fenetre = tk.Tk()
fenetre.title("PuniEmu Custom Unit Maker - Édition Complète V7")
fenetre.geometry("1050x800")
fenetre.withdraw() 

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
tk.Button(frame_gauche, text="🔍+ Recherche avancée", command=recherche_multi_criteres).grid(row=0, column=4, sticky="w", padx=(5, 0))

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

label_kind = tk.Label(frame_image_et_rang, text="", font=("Arial", 16, "bold"), fg="#0066cc", bg="#f0f0f0")
label_kind.pack(side=tk.LEFT, padx=5)

tk.Button(frame_icone, text="🖼️ Charger Icône", font=("Arial", 8), command=charger_icone_ayd).pack(pady=2)

frame_boutons_droite = tk.Frame(frame_droite, bg="#f0f0f0")
frame_boutons_droite.pack(side=tk.RIGHT)
tk.Label(frame_boutons_droite, text="📦 Ressources", font=("Arial", 10, "bold"), bg="#f0f0f0").pack()
tk.Button(frame_boutons_droite, text="👁️ Modèle 3D", bg="#d4edda", font=("Arial", 9, "bold"), command=visualiser_modele_3d).pack(pady=5, fill=tk.X)
tk.Button(frame_boutons_droite, text="💡 Nouvel ID", command=obtenir_dernier_id, bg="#fff3cd").pack(fill=tk.X)
tk.Button(frame_boutons_droite, text="💾  Yo-kai (Global)", bg="#add8e6", font=("Arial", 9, "bold"), command=ouvrir_menu_sauvegarde).pack(pady=5, fill=tk.X)
tk.Button(frame_boutons_droite, text="📂 Charger Dossier Mod", command=charger_dossier_mod, bg="#e2e3e5", font=("Arial", 9, "bold")).pack(pady=5, fill=tk.X)
tk.Button(frame_boutons_droite, text="⚖️ Comparer 2 Versions", command=comparer_versions, bg="#e2e3e5", font=("Arial", 9, "bold")).pack(pady=5, fill=tk.X)
tk.Button(frame_boutons_droite, text="⚙️ Changer les dossiers", command=changer_dossiers, bg="#f8d7da", font=("Arial", 9, "bold")).pack(pady=5, fill=tk.X)
tk.Button(frame_boutons_droite, text="🌐 Lier Serveur Assets", command=indexer_serveur, bg="#e2e3e5", font=("Arial", 9, "bold")).pack(pady=5, fill=tk.X)
btn_theme = tk.Button(frame_boutons_droite, text="🌙 Mode Sombre", command=basculer_theme, bg="#e2e3e5", font=("Arial", 9, "bold"))
btn_theme.pack(pady=5, fill=tk.X)

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
    ligne, colonne = i // 2, (i % 2) * 2 
    tk.Label(frame_basique, text=CHAMPS_YOKAI[i], font=("Arial", 9)).grid(row=ligne, column=colonne, sticky="e", padx=(10, 5), pady=5)
    
    if i == 6:
        sub_frame_food = tk.Frame(frame_basique)
        sub_frame_food.grid(row=ligne, column=colonne+1, sticky="w", padx=5, pady=5)
        entree = tk.Entry(sub_frame_food, width=12)
        entree.pack(side=tk.LEFT)
        cases_entrees.append(entree)
        label_nom_food = tk.Label(sub_frame_food, text="(Inconnu)", font=("Arial", 9, "bold"), fg="gray")
        label_nom_food.pack(side=tk.LEFT, padx=5)
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
    ligne, colonne = (i + 2) // 2, ((i + 2) % 2) * 2
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
    ("DisplayName (Nom affiché)", 2), ("Unk0 (Vitesse jauge?)", 3), ("SoultPt (Puissance/Points)", 4),
    ("MaxUseCount", 5), ("SoultStatsDict (Dico Stats)", 11), ("Unk1", 6), ("Unk2", 7), 
    ("Unk3", 8), ("Unk4", 9), ("Unk5", 10), ("Unk7 (Double)", 12)
]

for i, (nom_champ, index_col) in enumerate(champs_niveaux):
    ligne, colonne = (i // 2) + 1, (i % 2) * 2
    tk.Label(frame_skill_levels, text=f"{nom_champ} :", font=("Arial", 9), bg="#e6f2ff").grid(row=ligne, column=colonne, sticky="e", padx=(10, 5), pady=2)
    entree = tk.Entry(frame_skill_levels, width=35)
    entree.grid(row=ligne, column=colonne+1, padx=5, pady=2)
    cases_skill_levels[index_col] = entree

tk.Button(frame_skill_levels, text="🧰 Éditeur groupé (7 niveaux)", command=ouvrir_editeur_niveaux_groupe).grid(row=7, column=0, columnspan=4, pady=8)

# --- UI : EFFETS BONUS (liés au YoukaiId courant) ---
frame_bonus = tk.LabelFrame(scrollable_frame, text="🎖️ Effets Bonus", font=("Arial", 10, "bold"), bg="#e8f5e9", padx=10, pady=10)
frame_bonus.pack(fill=tk.X, padx=10, pady=10)

# --- UI : EFFETS BONUS (liés au YoukaiId courant) ---
frame_bonus = tk.LabelFrame(scrollable_frame, text="🎖️ Effets Bonus", font=("Arial", 10, "bold"), bg="#e8f5e9", padx=10, pady=10)
frame_bonus.pack(fill=tk.X, padx=10, pady=10)

subid_bonus_var = tk.StringVar(value="1")

tk.Label(frame_bonus, text="Type (BonusEffect) :", font=("Arial", 9), bg="#e8f5e9").grid(row=0, column=0, sticky="e", padx=(10, 5), pady=5)
combo_bonus_type = ttk.Combobox(frame_bonus, values=[f"{k} - {v}" for k, v in YW_BONUS_EFFECTS.items()], width=28, state="readonly")
combo_bonus_type.grid(row=0, column=1, padx=5, pady=5)

tk.Label(frame_bonus, text="Description :", font=("Arial", 9), bg="#e8f5e9").grid(row=1, column=0, sticky="e", padx=(10, 5), pady=5)
entree_bonus_description = tk.Entry(frame_bonus, width=35)
entree_bonus_description.grid(row=1, column=1, padx=5, pady=5)
cases_bonus["Description"] = entree_bonus_description

tk.Label(frame_bonus, text="Ressource (effet:...,balloon:...) :", font=("Arial", 9), bg="#e8f5e9").grid(row=2, column=0, sticky="e", padx=(10, 5), pady=5)
entree_bonus_ressource = tk.Entry(frame_bonus, width=35)
entree_bonus_ressource.grid(row=2, column=1, padx=5, pady=5)
cases_bonus["Ressource"] = entree_bonus_ressource

# --- UI : NIVEAUX D'EFFET BONUS ---
frame_bonus_niveaux = tk.LabelFrame(scrollable_frame, text="📊 Niveaux d'Effet Bonus", font=("Arial", 10, "bold"), bg="#f3e8ff", padx=10, pady=10)
frame_bonus_niveaux.pack(fill=tk.X, padx=10, pady=10)

niveau_bonus_actuel_var = tk.StringVar(value="1")
tk.Label(frame_bonus_niveaux, text="Sélectionner le Niveau :", font=("Arial", 9, "bold"), bg="#f3e8ff").grid(row=0, column=0, sticky="e", padx=5, pady=5)
combo_niveau_bonus = ttk.Combobox(frame_bonus_niveaux, textvariable=niveau_bonus_actuel_var, values=[str(i) for i in range(1, 6)], width=10, state="readonly")
combo_niveau_bonus.grid(row=0, column=1, sticky="w", padx=5, pady=5)
combo_niveau_bonus.bind("<<ComboboxSelected>>", afficher_donnees_bonus_niveau)

champs_bonus_niveaux = [
    ("Texte affiché", 3), ("ValeurA (réf. externe)", 4), ("ValeurB (montant x1000)", 5),
]
for i, (nom_champ, index_col) in enumerate(champs_bonus_niveaux):
    ligne, colonne = (i // 2) + 1, (i % 2) * 2
    tk.Label(frame_bonus_niveaux, text=f"{nom_champ} :", font=("Arial", 9), bg="#f3e8ff").grid(row=ligne, column=colonne, sticky="e", padx=(10, 5), pady=2)
    entree = tk.Entry(frame_bonus_niveaux, width=35)
    entree.grid(row=ligne, column=colonne+1, padx=5, pady=2)
    cases_bonus_niveau[index_col] = entree

# --- UI : BOUTON ET ÉLÉMENTS AVANCÉS (15 à 38) ---
btn_toggle_avance = tk.Button(scrollable_frame, text="▼ Afficher les paramètres avancés (15-38) ▼", command=toggle_avance, bg="#e2e3e5", font=("Arial", 9, "bold"))
btn_toggle_avance.pack(pady=10)
frame_avance = tk.Frame(scrollable_frame)

for i in range(15, len(CHAMPS_YOKAI)):
    ligne, colonne = (i - 15) // 2, ((i - 15) % 2) * 2 
    tk.Label(frame_avance, text=CHAMPS_YOKAI[i], font=("Arial", 9)).grid(row=ligne, column=colonne, sticky="e", padx=(10, 5), pady=5)
    entree = tk.Entry(frame_avance, width=35)
    entree.grid(row=ligne, column=colonne+1, padx=5, pady=5)
    cases_entrees.append(entree)

# --- INITIALISATION ET LANCEMENT ---
def demarrer_outil():
    if charger_config(): return True
    if initialiser_outils(au_demarrage=True) and initialiser_dossier_version(au_demarrage=True):
        sauvegarder_config()
        return True
    return False

if demarrer_outil():
    charger_fichier()
    charger_skills()
    charger_skill_levels()
    charger_bonus_effects()
    charger_bonus_effect_levels()
    fenetre.deiconify() 
    fenetre.mainloop()