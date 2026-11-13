# -*- coding: utf-8 -*-
import os
import sys
import json
import re
import io
import shutil
import zipfile
import tkinter as tk
from tkinter import messagebox, filedialog, scrolledtext, ttk
from PIL import Image, ImageTk

# Permet d'importer les modules voisins (constants, mst_io, stat_presets, viewer_3d)
if getattr(sys, "frozen", False):
    DOSSIER_BASE = os.path.dirname(sys.executable)
else:
    DOSSIER_BASE = os.path.dirname(os.path.abspath(__file__))

if DOSSIER_BASE not in sys.path:
    sys.path.insert(0, DOSSIER_BASE)

from constants import (
    COORDONNEES_KINDS, COORDONNEES_RANGS, KIND_NAMES, RANK_NAMES,
    SOULT_TYPES, FOOD_TYPES, YW_BONUS_EFFECTS, CHAMPS_YOKAI,
    COLONNES_STRONG_SKILL, INDEX_RECHERCHE, THEMES,
    get_kind_label, get_rank_label, matches_kind, matches_rank
)
from mst_io import (
    normaliser_sauts_ligne, assainir_texte_export, litteraliser_pour_txt,
    preparer_texte_interface, formater_texte_4_mots, lire_donnees_fichier,
    maj_fichier_original, verifier_conflits_yokai, traiter_ez_avec_yokai,
    creer_backup, extraire_icone_depuis_ayd, DOSSIER_TEMP_ICONES
)
from stat_presets import STAT_PRESETS, get_stat_preset, verifier_coherence_stats
from viewer_3d import ouvrir_viewer_3d

# ==========================================
# PARAMÈTRES ET VARIABLES GLOBALES
# ==========================================
FICHIER_CONFIG = os.path.join(DOSSIER_BASE, "config.json")

FICHIER_DB = ""
FICHIER_SKILL_DB = ""
FICHIER_SKILL_LEVEL_DB = ""
FICHIER_BONUS_EFFECT_DB = ""
FICHIER_BONUS_EFFECT_LEVEL_DB = ""
FICHIER_STRONG_SKILL_DB = ""
FICHIER_STRONG_SKILL_LEVEL_DB = ""
DOSSIER_RESSOURCES = ""

CHEMIN_YOKAI_EXE = ""
CHEMIN_SPRITESHEET = ""
CHEMIN_KIND_SPRITESHEET = ""

DOSSIER_SERVEUR = ""
INDEX_SERVEUR = {}

THEME_ACTIF = "Mode Sakura"

MODE_JEU = "WibWob"
MODES_JEU = ("WibWob", "PuniPuni")

image_rang_reference = None
image_kind_reference = None
dictionnaire_skill_levels = {}
dictionnaire_strong_skills = {}
dictionnaire_strong_skill_levels = {}
cases_strong_skills = {}
cases_strong_skill_levels = {}
niveau_strong_actuel_var = None
niveau_strong_precedent = "1"
strong_id_actuel_var = None
cases_skill_levels = {}
niveau_actuel_var = None
niveau_precedent = "1"
lignes_yokai = []
dictionnaire_skills = {}
index_trouve = -1
cases_entrees = []
cases_skills = {}
dictionnaire_bonus_effect = {}
dictionnaire_bonus_effect_level = {}
cases_bonus = {}
cases_bonus_niveau = {}
niveau_bonus_actuel_var = None
niveau_bonus_precedent = "1"
subid_bonus_var = None
activer_bonus_effect_var = None
fenetre_res = None
mode_avance_actif = False

HISTORIQUE_RECENTS = []  # Historique des Yo-kai récents consultés


# ==========================================
# ÉDITEUR DE TEXTE AVEC SAUTS DE LIGNE
# ==========================================
def ouvrir_editeur_saut_ligne(entree, titre="Édition du texte", max_sauts_de_ligne=None, max_mots_secours=5):
    p = THEMES.get(THEME_ACTIF, THEMES["Mode Sakura"])
    fenetre_edition = tk.Toplevel(fenetre)
    fenetre_edition.title(titre)
    fenetre_edition.geometry("450x240")
    fenetre_edition.configure(bg=p["bg_main"])
    fenetre_edition.transient(fenetre)
    fenetre_edition.grab_set()

    tk.Label(fenetre_edition, text=titre, font=("Segoe UI", 10, "bold"),
             bg=p["bg_main"], fg=p["accent"]).pack(pady=(12, 6))

    sous_titre = ("Entrée libre : les sauts de ligne physiques seront convertis en '\\n'.\n"
                  "Le bouton 'Formater' découpe le texte par paquets de 4 mots.")
    tk.Label(fenetre_edition, text=sous_titre, font=("Segoe UI", 8),
             bg=p["bg_main"], fg=p["text_muted"], justify=tk.CENTER).pack(pady=(0, 8))

    zone_texte = scrolledtext.ScrolledText(
        fenetre_edition, wrap=tk.WORD, height=4, font=("Segoe UI", 10),
        bg=p["entry_bg"], fg=p["entry_fg"], insertbackground=p["accent"],
        relief=tk.SOLID, bd=1
    )
    zone_texte.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 10))
    zone_texte.insert("1.0", preparer_texte_interface(entree.get()))

    frame_boutons = tk.Frame(fenetre_edition, bg=p["bg_main"])
    frame_boutons.pack(fill=tk.X, padx=12, pady=(0, 12))

    def appliquer_format_4_mots():
        texte_actuel = zone_texte.get("1.0", "end-1c")
        formate = formater_texte_4_mots(texte_actuel, max_mots_secours=max_mots_secours,
                                        max_sauts_de_ligne=max_sauts_de_ligne)
        zone_texte.delete("1.0", tk.END)
        zone_texte.insert("1.0", preparer_texte_interface(formate))

    tk.Button(frame_boutons, text="Formater (4 mots/ligne)", command=appliquer_format_4_mots,
              font=("Segoe UI", 9), bg=p["btn_bg"], fg=p["btn_fg"], relief="flat", bd=1).pack(side=tk.LEFT)

    def valider():
        texte_final = assainir_texte_export(zone_texte.get("1.0", "end-1c"))
        entree.delete(0, tk.END)
        entree.insert(0, texte_final)
        fenetre_edition.destroy()

    tk.Button(frame_boutons, text="Annuler", command=fenetre_edition.destroy, font=("Segoe UI", 9),
              bg=p["btn_bg"], fg=p["btn_fg"], relief="flat", bd=1).pack(side=tk.RIGHT, padx=(6, 0))
    tk.Button(frame_boutons, text="Valider", font=("Segoe UI", 9, "bold"),
              bg=p["btn_special_bg"], fg=p["btn_special_fg"], relief="flat", bd=1, command=valider).pack(side=tk.RIGHT)


# ==========================================
# CONFIGURATION & INITIALISATION DES OUTILS
# ==========================================
def resoudre_chemin(chemin):
    if not chemin:
        return ""
    if not os.path.isabs(chemin):
        chemin = os.path.join(DOSSIER_BASE, chemin)
    return os.path.abspath(chemin).replace("\\", "/")

def charger_config():
    global MODE_JEU, FICHIER_STRONG_SKILL_DB, FICHIER_STRONG_SKILL_LEVEL_DB, CHEMIN_YOKAI_EXE, CHEMIN_SPRITESHEET, CHEMIN_KIND_SPRITESHEET, FICHIER_DB, FICHIER_SKILL_DB, FICHIER_SKILL_LEVEL_DB, FICHIER_BONUS_EFFECT_DB, FICHIER_BONUS_EFFECT_LEVEL_DB, DOSSIER_RESSOURCES, DOSSIER_SERVEUR, THEME_ACTIF
    if os.path.exists(FICHIER_CONFIG):
        try:
            with open(FICHIER_CONFIG, "r", encoding="utf-8") as f:
                config = json.load(f)

            y_exe = resoudre_chemin(config.get("CHEMIN_YOKAI_EXE", ""))
            s_sheet = resoudre_chemin(config.get("CHEMIN_SPRITESHEET", ""))
            k_sheet = resoudre_chemin(config.get("CHEMIN_KIND_SPRITESHEET", ""))
            f_db = resoudre_chemin(config.get("FICHIER_DB", ""))
            s_db = resoudre_chemin(config.get("FICHIER_SKILL_DB", ""))
            l_db = resoudre_chemin(config.get("FICHIER_SKILL_LEVEL_DB", ""))
            be_db = resoudre_chemin(config.get("FICHIER_BONUS_EFFECT_DB", ""))
            bel_db = resoudre_chemin(config.get("FICHIER_BONUS_EFFECT_LEVEL_DB", ""))
            d_res = resoudre_chemin(config.get("DOSSIER_RESSOURCES", ""))
            d_serv = config.get("DOSSIER_SERVEUR", "").replace("\\", "/")
            if d_serv and not os.path.isabs(d_serv):
                d_serv = resoudre_chemin(d_serv)
            THEME_ACTIF = config.get("THEME_ACTIF", "Mode Sakura")
            mode_lu = config.get("MODE_JEU", "PuniPuni")
            MODE_JEU = mode_lu if mode_lu in MODES_JEU else "PuniPuni"
            ss_db = resoudre_chemin(config.get("FICHIER_STRONG_SKILL_DB", ""))
            ssl_db = resoudre_chemin(config.get("FICHIER_STRONG_SKILL_LEVEL_DB", ""))

            mode_serveur = bool(d_serv) and os.path.exists(d_serv)
            chemins_a_verifier = {
                "CHEMIN_YOKAI_EXE": y_exe, "CHEMIN_SPRITESHEET": s_sheet, "CHEMIN_KIND_SPRITESHEET": k_sheet,
                "FICHIER_DB": f_db, "FICHIER_SKILL_DB": s_db, "FICHIER_SKILL_LEVEL_DB": l_db,
            }
            if not mode_serveur:
                chemins_a_verifier["DOSSIER_RESSOURCES"] = d_res
            manquants = [nom for nom, chemin in zip(chemins_a_verifier.keys(), chemins_a_verifier.values()) if not os.path.exists(chemin)]
            if not manquants:
                CHEMIN_YOKAI_EXE, CHEMIN_SPRITESHEET, CHEMIN_KIND_SPRITESHEET = y_exe, s_sheet, k_sheet
                FICHIER_DB, FICHIER_SKILL_DB, FICHIER_SKILL_LEVEL_DB = f_db, s_db, l_db
                FICHIER_BONUS_EFFECT_DB = be_db if os.path.exists(be_db) else ""
                FICHIER_BONUS_EFFECT_LEVEL_DB = bel_db if os.path.exists(bel_db) else ""
                FICHIER_STRONG_SKILL_DB = ss_db if os.path.exists(ss_db) else ""
                FICHIER_STRONG_SKILL_LEVEL_DB = ssl_db if os.path.exists(ssl_db) else ""
                DOSSIER_RESSOURCES = d_res
                if mode_serveur:
                    DOSSIER_SERVEUR = d_serv
                    indexer_serveur(silencieux=True)
                return True
        except Exception as e:
            print(f"Erreur chargement config: {e}")
    return False

def sauvegarder_config():
    config = {
        "CHEMIN_YOKAI_EXE": CHEMIN_YOKAI_EXE, "CHEMIN_SPRITESHEET": CHEMIN_SPRITESHEET,
        "CHEMIN_KIND_SPRITESHEET": CHEMIN_KIND_SPRITESHEET,
        "FICHIER_DB": FICHIER_DB, "FICHIER_SKILL_DB": FICHIER_SKILL_DB,
        "FICHIER_SKILL_LEVEL_DB": FICHIER_SKILL_LEVEL_DB,
        "FICHIER_BONUS_EFFECT_DB": FICHIER_BONUS_EFFECT_DB,
        "FICHIER_BONUS_EFFECT_LEVEL_DB": FICHIER_BONUS_EFFECT_LEVEL_DB,
        "FICHIER_STRONG_SKILL_DB": FICHIER_STRONG_SKILL_DB,
        "FICHIER_STRONG_SKILL_LEVEL_DB": FICHIER_STRONG_SKILL_LEVEL_DB,
        "DOSSIER_RESSOURCES": DOSSIER_RESSOURCES,
        "DOSSIER_SERVEUR": DOSSIER_SERVEUR,
        "THEME_ACTIF": THEME_ACTIF,
        "MODE_JEU": MODE_JEU
    }
    with open(FICHIER_CONFIG, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

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
        charger_strong_skills()
        charger_strong_skill_levels()
        messagebox.showinfo("Dossiers mis à jour", "Les chemins ont été mis à jour avec succès !")

def indexer_serveur(silencieux=False):
    global DOSSIER_SERVEUR, INDEX_SERVEUR
    if not silencieux:
        choix = filedialog.askdirectory(title="Sélectionner le dossier du SERVEUR (fichiers originaux)")
        if not choix: return
        DOSSIER_SERVEUR = choix.replace("\\", "/")
        sauvegarder_config()

    if not DOSSIER_SERVEUR or not os.path.exists(DOSSIER_SERVEUR): return
    INDEX_SERVEUR = {}
    for racine, _, fichiers in os.walk(DOSSIER_SERVEUR):
        for f in fichiers:
            cle = f.lower()
            if cle not in INDEX_SERVEUR:
                INDEX_SERVEUR[cle] = os.path.join(racine, f).replace("\\", "/")

    if not silencieux:
        messagebox.showinfo("Serveur indexé", f"{len(INDEX_SERVEUR)} fichiers indexés depuis le serveur !")

def trouver_fichier(nom_base, dossier):
    nom_base_sans_ext = os.path.splitext(nom_base)[0]
    for racine, _, fichiers in os.walk(dossier):
        for f in fichiers:
            if os.path.splitext(f)[0] == nom_base_sans_ext and f.lower().endswith(('.txt', '.json')):
                return os.path.join(racine, f).replace("\\", "/")
    return None

def initialiser_outils(au_demarrage=True):
    global CHEMIN_YOKAI_EXE, CHEMIN_SPRITESHEET, CHEMIN_KIND_SPRITESHEET
    dossier_outils = filedialog.askdirectory(title="1/2 : Sélectionner le dossier des OUTILS (Resources)")
    if not dossier_outils:
        if au_demarrage: sys.exit()
        return False
    dossier_outils = dossier_outils.replace("\\", "/")
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
        if au_demarrage: sys.exit()
        return False
    return True

def initialiser_dossier_version(au_demarrage=True):
    global FICHIER_DB, FICHIER_SKILL_DB, FICHIER_SKILL_LEVEL_DB, FICHIER_BONUS_EFFECT_DB, FICHIER_BONUS_EFFECT_LEVEL_DB, FICHIER_STRONG_SKILL_DB, FICHIER_STRONG_SKILL_LEVEL_DB, DOSSIER_RESSOURCES
    dossier_version = filedialog.askdirectory(title="2/2 : Sélectionner le dossier des FICHIERS DE JEU (MST)")
    if not dossier_version:
        if au_demarrage: sys.exit()
        return False
    dossier_version = dossier_version.replace("\\", "/")
    FICHIER_DB = trouver_fichier("ywp_mst_youkai", dossier_version)
    FICHIER_SKILL_DB = trouver_fichier("ywp_mst_youkai_skill", dossier_version)
    FICHIER_SKILL_LEVEL_DB = trouver_fichier("ywp_mst_youkai_skill_level", dossier_version)
    FICHIER_BONUS_EFFECT_DB = trouver_fichier("ywp_mst_youkai_bonus_effect", dossier_version) or ""
    FICHIER_BONUS_EFFECT_LEVEL_DB = trouver_fichier("ywp_mst_youkai_bonus_effect_level", dossier_version) or ""
    FICHIER_STRONG_SKILL_DB = trouver_fichier("ywp_mst_youkai_strong_skill", dossier_version) or ""
    FICHIER_STRONG_SKILL_LEVEL_DB = trouver_fichier("ywp_mst_youkai_strong_skill_level", dossier_version) or ""
    DOSSIER_RESSOURCES = dossier_version

    fichiers_manquants = [nom for nom, chemin in zip(
        ["ywp_mst_youkai", "ywp_mst_youkai_skill", "ywp_mst_youkai_skill_level"],
        [FICHIER_DB, FICHIER_SKILL_DB, FICHIER_SKILL_LEVEL_DB]
    ) if not chemin]

    if fichiers_manquants:
        messagebox.showerror("Fichiers Introuvables", "Fichiers manquants :\n- " + "\n- ".join(fichiers_manquants))
        if au_demarrage: sys.exit()
        return False
    return True

def vider_interface():
    global index_trouve
    index_trouve = -1
    for cases in [cases_entrees, cases_skills.values(), cases_skill_levels.values(), cases_bonus.values(), cases_bonus_niveau.values(), cases_strong_skills.values(), cases_strong_skill_levels.values()]:
        for case in cases:
            if isinstance(case, tk.Entry):
                case.delete(0, tk.END)
    label_image_ayd.config(image='', text="Aucune icône", width=12, height=6)
    label_rang.config(image='', text="")
    label_kind.config(image='', text="")
    if 'label_nom_food' in globals(): label_nom_food.config(text="(Inconnu)")
    if 'label_nom_rank' in globals(): label_nom_rank.config(text="")
    if 'label_nom_kind' in globals(): label_nom_kind.config(text="")
    if 'label_stat_status' in globals(): label_stat_status.config(text="")

def toggle_avance():
    global mode_avance_actif
    mode_avance_actif = not mode_avance_actif
    if mode_avance_actif:
        frame_avance.pack(fill=tk.X, padx=8, pady=8)
        btn_toggle_avance.config(text="🔼 Masquer Paramètres Avancés (Champs 15 à 38)")
    else:
        frame_avance.pack_forget()
        btn_toggle_avance.config(text="🔽 Afficher Paramètres Avancés (Champs 15 à 38)")

def comparer_versions():
    dossier_a_comparer = filedialog.askdirectory(title="Sélectionner le dossier d'une AUTRE version à comparer")
    if not dossier_a_comparer: return
    autre_db = trouver_fichier("ywp_mst_youkai", dossier_a_comparer)
    if not autre_db:
        return messagebox.showerror("Erreur", "ywp_mst_youkai (.txt ou .json) introuvable dans ce dossier.")
    
    texte_actuel, _, _ = lire_donnees_fichier(FICHIER_DB)
    texte_autre, _, _ = lire_donnees_fichier(autre_db)
    ids_actuels = {l.split('|')[0]: l.split('|')[1] for l in texte_actuel.split('*') if len(l.split('|')) > 1}
    ids_autres = {l.split('|')[0]: l.split('|')[1] for l in texte_autre.split('*') if len(l.split('|')) > 1}
    
    ajouts = [f"ID: {k} - {v}" for k, v in ids_actuels.items() if k not in ids_autres]
    retraits = [f"ID: {k} - {v}" for k, v in ids_autres.items() if k not in ids_actuels]
    
    p = THEMES.get(THEME_ACTIF, THEMES["Mode Sakura"])
    fen_comp = tk.Toplevel(fenetre)
    fen_comp.title("Comparaison de versions")
    fen_comp.geometry("600x420")
    fen_comp.configure(bg=p["bg_main"])
    
    tk.Label(fen_comp, text=f"Ajoutés dans votre version (+{len(ajouts)}) :", font=("Segoe UI", 10, "bold"), bg=p["bg_main"], fg="#2ecc71").pack(pady=(10, 2))
    lb_ajouts = tk.Listbox(fen_comp, height=7, bg=p["entry_bg"], fg=p["entry_fg"], relief=tk.SOLID, bd=1)
    lb_ajouts.pack(fill=tk.BOTH, expand=True, padx=12, pady=4)
    for a in ajouts: lb_ajouts.insert(tk.END, a)
    
    tk.Label(fen_comp, text=f"Absents dans votre version (-{len(retraits)}) :", font=("Segoe UI", 10, "bold"), bg=p["bg_main"], fg="#e74c3c").pack(pady=(10, 2))
    lb_retraits = tk.Listbox(fen_comp, height=7, bg=p["entry_bg"], fg=p["entry_fg"], relief=tk.SOLID, bd=1)
    lb_retraits.pack(fill=tk.BOTH, expand=True, padx=12, pady=4)
    for r in retraits: lb_retraits.insert(tk.END, r)


# ==========================================
# GESTION DES ICÔNES ET MODÈLES 3D
# ==========================================
def charger_icone_ayd(depuis_bouton=False):
    global image_icone_reference, CHEMIN_YOKAI_EXE
    yokai_id = ""
    if cases_entrees and len(cases_entrees) > 0:
        yokai_id = cases_entrees[0].get().strip()
    if not yokai_id and 'entree_recherche_id' in globals():
        yokai_id = entree_recherche_id.get().strip()
    if not yokai_id:
        image_icone_reference = None
        label_image_ayd.config(image='', text="Aucune icône", width=12, height=6)
        return

    # S'assurer que yokai.exe est localisé avec un chemin absolu
    if not CHEMIN_YOKAI_EXE or not os.path.exists(CHEMIN_YOKAI_EXE):
        for cand_exe in [
            os.path.join(DOSSIER_BASE, "Resources", "yokai.exe"),
            os.path.join(DOSSIER_RESSOURCES, "yokai.exe") if DOSSIER_RESSOURCES else "",
            os.path.abspath("Resources/yokai.exe")
        ]:
            if cand_exe and os.path.exists(cand_exe):
                CHEMIN_YOKAI_EXE = os.path.abspath(cand_exe).replace("\\", "/")
                break

    noms_png = [f"bl_{yokai_id}.png", f"{yokai_id}.png"]
    noms_ayd_bl = [f"bl_{yokai_id}.ayd", f"bl_{yokai_id}.ez"]
    noms_ayd_simple = [f"{yokai_id}.ayd", f"{yokai_id}.ez"]

    image_bytes = None

    # Dossiers cibles connus pour la recherche
    dossiers_cibles = [DOSSIER_TEMP_ICONES]
    for cand_gf in [
        os.path.join(DOSSIER_BASE, "gamefiles"),
        os.path.join(os.path.dirname(DOSSIER_BASE), "gamefiles"),
        DOSSIER_SERVEUR,
        DOSSIER_RESSOURCES,
        os.path.join(DOSSIER_BASE, "Resources"),
    ]:
        if cand_gf and os.path.exists(cand_gf):
            p_norm = os.path.abspath(cand_gf).replace("\\", "/")
            if p_norm not in dossiers_cibles:
                dossiers_cibles.append(p_norm)
    d_base_res = os.path.abspath(os.path.join(DOSSIER_BASE, "Resources")).replace("\\", "/")
    if FICHIER_DB and os.path.exists(FICHIER_DB):
        d_db = os.path.dirname(os.path.abspath(FICHIER_DB)).replace("\\", "/")
        if d_db not in dossiers_cibles:
            dossiers_cibles.append(d_db)

    # 1. Recherche d'une image PNG directe (fichier temporaire déjà extrait ou ressources existantes)
    candidats_png = [os.path.join(DOSSIER_TEMP_ICONES, f"bl_{yokai_id}.png")]
    if DOSSIER_SERVEUR and INDEX_SERVEUR:
        for n in noms_png:
            if n.lower() in INDEX_SERVEUR:
                candidats_png.append(INDEX_SERVEUR[n.lower()])
    for d in dossiers_cibles:
        for n in noms_png:
            candidats_png.append(os.path.join(d, n))

    for p in candidats_png:
        if p and os.path.exists(p) and os.path.isfile(p):
            try:
                with open(p, "rb") as f:
                    image_bytes = f.read()
                if image_bytes:
                    break
            except Exception:
                pass

    # 2. Si aucune image PNG trouvée, chercher bl_yokaiID.ayd / bl_yokaiID.ez pour double décompression temporaire
    if not image_bytes:
        candidats_ayd_prioritaires = []
        candidats_ayd_secondaires = []

        if DOSSIER_SERVEUR and INDEX_SERVEUR:
            for n in noms_ayd_bl:
                if n.lower() in INDEX_SERVEUR:
                    candidats_ayd_prioritaires.append(INDEX_SERVEUR[n.lower()])
            for n in noms_ayd_simple:
                if n.lower() in INDEX_SERVEUR:
                    candidats_ayd_secondaires.append(INDEX_SERVEUR[n.lower()])

        for d in dossiers_cibles:
            for n in noms_ayd_bl:
                candidats_ayd_prioritaires.append(os.path.join(d, n))
            for n in noms_ayd_simple:
                candidats_ayd_secondaires.append(os.path.join(d, n))

        # Vérifier d'abord les fichiers bl_yokaiID.ayd / .ez existants directement
        fichiers_ayd = [p for p in candidats_ayd_prioritaires if p and os.path.exists(p) and os.path.isfile(p)]

        # Recherche récursive de bl_yokaiID.* dans les dossiers si non trouvé dans les chemins directs
        if not fichiers_ayd:
            for d in [dc for dc in dossiers_cibles if dc != DOSSIER_TEMP_ICONES]:
                if d and os.path.isdir(d):
                    for racine, _, f_list in os.walk(d):
                        for f in f_list:
                            if f.lower() in [n.lower() for n in noms_ayd_bl]:
                                fichiers_ayd.append(os.path.join(racine, f))
                        if fichiers_ayd:
                            break
                if fichiers_ayd:
                    break

        # Si aucun bl_yokaiID trouvé, tester les candidats secondaires (yokaiID.ayd / .ez)
        if not fichiers_ayd:
            fichiers_ayd = [p for p in candidats_ayd_secondaires if p and os.path.exists(p) and os.path.isfile(p)]

        for p_ayd in fichiers_ayd:
            # Extraction dans le dossier temporaire du système exclusivement
            image_bytes = extraire_icone_depuis_ayd(p_ayd, yokai_id, CHEMIN_YOKAI_EXE, DOSSIER_TEMP_ICONES)
            if image_bytes:
                break

    # 3. Si toujours aucune image et déclenché manuellement depuis le bouton "Charger Icône"
    if not image_bytes and depuis_bouton:
        fichier_choisi = filedialog.askopenfilename(
            title=f"Sélectionner l'icône ou le fichier AYD pour {yokai_id}",
            filetypes=[("Fichiers compatibles", "*.png;*.ayd;*.ez"), ("Images PNG", "*.png"), ("Archives AYD", "*.ayd"), ("Archives EZ", "*.ez"), ("Tous les fichiers", "*.*")]
        )
        if fichier_choisi and os.path.exists(fichier_choisi):
            if fichier_choisi.lower().endswith(".png"):
                try:
                    with open(fichier_choisi, "rb") as f:
                        image_bytes = f.read()
                except Exception:
                    pass
            elif fichier_choisi.lower().endswith((".ayd", ".ez")):
                image_bytes = extraire_icone_depuis_ayd(fichier_choisi, yokai_id, CHEMIN_YOKAI_EXE, DOSSIER_TEMP_ICONES)

    try:
        if image_bytes:
            image_pil = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
            image_icone_reference = ImageTk.PhotoImage(image_pil)
            label_image_ayd.config(image=image_icone_reference, text="", width=image_pil.width, height=image_pil.height)
        else:
            image_icone_reference = None
            label_image_ayd.config(image='', text="Aucune icône", width=12, height=6)
    except Exception as e:
        image_icone_reference = None
        label_image_ayd.config(image='', text="Erreur", width=12, height=6)

def decouper_icone(img_complete, col, lig, nb_colonnes, nb_lignes, hauteur_cible=48):
    largeur, hauteur = img_complete.size
    x0 = round(col * largeur / nb_colonnes)
    y0 = round(lig * hauteur / nb_lignes)
    x1 = round((col + 1) * largeur / nb_colonnes)
    y1 = round((lig + 1) * hauteur / nb_lignes)

    icone = img_complete.convert("RGBA").crop((x0, y0, x1, y1))
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

def visualiser_modele_3d():
    if index_trouve == -1: return
    yokai_id = cases_entrees[0].get().strip()
    nom_actuel = cases_entrees[1].get().strip() if cases_entrees and len(cases_entrees) > 1 else ""
    succes, msg = ouvrir_viewer_3d(
        yokai_id, DOSSIER_RESSOURCES, DOSSIER_SERVEUR, INDEX_SERVEUR,
        CHEMIN_YOKAI_EXE, traiter_ez_avec_yokai,
        nom_yokai_getter=lambda yid: nom_actuel
    )
    if not succes and msg:
        messagebox.showwarning("Modèle 3D", msg)


# ==========================================
# CHARGEMENT DES BASES DE DONNÉES
# ==========================================
def charger_fichier():
    global lignes_yokai
    texte_brut, _, _ = lire_donnees_fichier(FICHIER_DB)
    if texte_brut:
        lignes_yokai = [l for l in texte_brut.split('*') if l.strip()]

def charger_skills():
    global dictionnaire_skills
    texte_brut, _, _ = lire_donnees_fichier(FICHIER_SKILL_DB)
    if texte_brut:
        for ligne in texte_brut.split('*'):
            colonnes = ligne.split('|')
            if len(colonnes) >= 4:
                dictionnaire_skills[colonnes[0]] = {
                    "Nom": colonnes[1],
                    "TypeID": colonnes[2],
                    "Description": colonnes[3],
                    "Propriete1": colonnes[4] if len(colonnes) > 4 else "0",
                    "Propriete2": colonnes[5] if len(colonnes) > 5 else "0",
                    "Anim3D": colonnes[6] if len(colonnes) > 6 else "",
                    "Anim2D": colonnes[7] if len(colonnes) > 7 else "",
                    "Anim2D_2": colonnes[8] if len(colonnes) > 8 else "",
                    "SkillUnk0": colonnes[9] if len(colonnes) > 9 else "0",
                    "SkillUnk1": colonnes[10] if len(colonnes) > 10 else "0",
                    "SkillUnk2": colonnes[11] if len(colonnes) > 11 else "0",
                    "SkillUnk3": colonnes[12] if len(colonnes) > 12 else "0",
                    "SkillUnk4": colonnes[13] if len(colonnes) > 13 else "",
                }

def charger_skill_levels():
    global dictionnaire_skill_levels
    texte_brut, _, _ = lire_donnees_fichier(FICHIER_SKILL_LEVEL_DB)
    if texte_brut:
        for ligne in texte_brut.split('*'):
            colonnes = ligne.split('|')
            if len(colonnes) >= 13:
                yokai_id, niveau = colonnes[0], colonnes[1]
                if yokai_id not in dictionnaire_skill_levels: dictionnaire_skill_levels[yokai_id] = {}
                dictionnaire_skill_levels[yokai_id][niveau] = colonnes

def _strong_skill_ligne_vers_dict(colonnes):
    return {cle: (colonnes[i + 1] if i + 1 < len(colonnes) else "") for i, cle in enumerate(COLONNES_STRONG_SKILL)}

def charger_strong_skills():
    global dictionnaire_strong_skills
    dictionnaire_strong_skills = {}
    if not FICHIER_STRONG_SKILL_DB or not os.path.exists(FICHIER_STRONG_SKILL_DB): return
    texte_brut, _, _ = lire_donnees_fichier(FICHIER_STRONG_SKILL_DB)
    if texte_brut:
        for ligne in texte_brut.split('*'):
            colonnes = ligne.split('|')
            if len(colonnes) >= 4:
                dictionnaire_strong_skills[colonnes[0]] = _strong_skill_ligne_vers_dict(colonnes)

def charger_strong_skill_levels():
    global dictionnaire_strong_skill_levels
    dictionnaire_strong_skill_levels = {}
    if not FICHIER_STRONG_SKILL_LEVEL_DB or not os.path.exists(FICHIER_STRONG_SKILL_LEVEL_DB): return
    texte_brut, _, _ = lire_donnees_fichier(FICHIER_STRONG_SKILL_LEVEL_DB)
    if texte_brut:
        for ligne in texte_brut.split('*'):
            colonnes = ligne.split('|')
            if len(colonnes) >= 13:
                dictionnaire_strong_skill_levels.setdefault(colonnes[0], {})[colonnes[1]] = colonnes

def _normaliser_ligne_bonus_effect(colonnes, yokai_id=None, sid=None):
    """Garantit qu'une ligne ywp_mst_youkai_bonus_effect possède bien ses 10 colonnes (0..9)."""
    res = list(colonnes) if colonnes else []
    while len(res) < 10:
        res.append("0")
    if yokai_id is not None:
        res[0] = str(yokai_id)
    if sid is not None:
        res[1] = str(sid)
    for idx in range(2, 10):
        if res[idx] == "" or res[idx] is None:
            res[idx] = "1" if idx == 3 else "0"
    return res[:10]

def _normaliser_ligne_bonus_level(colonnes, yokai_id=None, sid=None, niveau=None):
    """Garantit qu'une ligne ywp_mst_youkai_bonus_effect_level possède bien ses 9 colonnes (0..8)."""
    res = list(colonnes) if colonnes else []
    while len(res) < 9:
        # Colonnes 3..6 par défaut à "0", colonnes 7..8 par défaut à ""
        res.append("0" if len(res) < 7 else "")
    if yokai_id is not None:
        res[0] = str(yokai_id)
    if sid is not None:
        res[1] = str(sid)
    if niveau is not None:
        res[2] = str(niveau)
    for idx in (3, 4, 5, 6):
        if res[idx] == "" or res[idx] is None:
            res[idx] = "0"
    for idx in (7, 8):
        if res[idx] is None:
            res[idx] = ""
    return res[:9]

def charger_bonus_effects():
    global dictionnaire_bonus_effect
    dictionnaire_bonus_effect = {}
    if not FICHIER_BONUS_EFFECT_DB or not os.path.exists(FICHIER_BONUS_EFFECT_DB): return
    texte_brut, _, _ = lire_donnees_fichier(FICHIER_BONUS_EFFECT_DB)
    if texte_brut:
        for ligne in texte_brut.split('*'):
            if not ligne.strip(): continue
            colonnes = ligne.split('|')
            if len(colonnes) >= 2:
                dictionnaire_bonus_effect[(colonnes[0], colonnes[1])] = _normaliser_ligne_bonus_effect(colonnes)

def charger_bonus_effect_levels():
    global dictionnaire_bonus_effect_level
    dictionnaire_bonus_effect_level = {}
    if not FICHIER_BONUS_EFFECT_LEVEL_DB or not os.path.exists(FICHIER_BONUS_EFFECT_LEVEL_DB): return
    texte_brut, _, _ = lire_donnees_fichier(FICHIER_BONUS_EFFECT_LEVEL_DB)
    if texte_brut:
        for ligne in texte_brut.split('*'):
            if not ligne.strip(): continue
            colonnes = ligne.split('|')
            if len(colonnes) >= 3:
                cle = (colonnes[0], colonnes[1])
                if cle not in dictionnaire_bonus_effect_level: dictionnaire_bonus_effect_level[cle] = {}
                dictionnaire_bonus_effect_level[cle][colonnes[2]] = _normaliser_ligne_bonus_level(colonnes)

def classifier_yokai(youkai_id):
    try:
        yid = int(youkai_id)
        if 9000000 <= yid <= 9999999: return "CUSTOM"
        if 1000000 <= yid <= 1999999: return "OFFICIEL"
        if 2000000 <= yid <= 2999999: return "OFFICIEL"
        if 3000000 <= yid <= 3999999: return "PUNIPUNI"
        if 4000000 <= yid <= 4999999: return "EVENT"
        return "AUTRE"
    except ValueError:
        return "INCONNU"


# ==========================================
# HISTORIQUE RÉCENT ET NAVIGATION
# ==========================================
def ajouter_historique_recent(yokai_id, nom):
    global HISTORIQUE_RECENTS
    cle = f"{yokai_id} - {nom}" if nom else str(yokai_id)
    HISTORIQUE_RECENTS = [item for item in HISTORIQUE_RECENTS if not item.startswith(f"{yokai_id} ") and item != str(yokai_id)]
    HISTORIQUE_RECENTS.insert(0, cle)
    HISTORIQUE_RECENTS = HISTORIQUE_RECENTS[:12]
    if 'combo_recents' in globals():
        combo_recents['values'] = HISTORIQUE_RECENTS

def charger_depuis_recents(event=None):
    selection = combo_recents.get()
    if selection:
        yid = selection.split(" - ")[0].strip()
        entree_recherche_id.delete(0, tk.END)
        entree_recherche_id.insert(0, yid)
        charger_yokai_par_id()

def charger_yokai_par_index(idx):
    global index_trouve, niveau_precedent
    if 0 <= idx < len(lignes_yokai):
        colonnes = lignes_yokai[idx].split('|')
        index_trouve = idx
        entree_recherche_id.delete(0, tk.END)
        entree_recherche_id.insert(0, colonnes[0])
        remplir_cases(colonnes)
        niveau_actuel_var.set("1")
        niveau_precedent = "1"
        afficher_donnees_niveau(depuis_code=True)
        charger_icone_ayd()
        charger_bonus_effet_pour_yokai(colonnes[0])
        synchroniser_strong_avec_yokai()
        ajouter_historique_recent(colonnes[0], colonnes[1] if len(colonnes) > 1 else "")

def naviguer_yokai_precedent(event=None):
    if not lignes_yokai: return
    if index_trouve <= 0:
        charger_yokai_par_index(len(lignes_yokai) - 1)
    else:
        charger_yokai_par_index(index_trouve - 1)

def naviguer_yokai_suivant(event=None):
    if not lignes_yokai: return
    if index_trouve == -1 or index_trouve >= len(lignes_yokai) - 1:
        charger_yokai_par_index(0)
    else:
        charger_yokai_par_index(index_trouve + 1)

def recharger_yokai_actuel(event=None):
    if index_trouve == -1:
        messagebox.showinfo("Annuler", "Aucun Yo-kai n'est actuellement chargé.")
        return
    if messagebox.askyesno("Recharger le Yo-kai", "Annuler toutes les modifications non sauvegardées et recharger ce Yo-kai ?"):
        charger_yokai_par_index(index_trouve)


# ==========================================
# GESTION DES CHAMPS VISUELS ET COHÉRENCE
# ==========================================
def maj_nom_nourriture(event=None):
    p = THEMES.get(THEME_ACTIF, THEMES["Mode Sakura"])
    if len(cases_entrees) > 6:
        valeur = cases_entrees[6].get().strip()
        nom = FOOD_TYPES.get(valeur, "Inconnu")
        if 'label_nom_food' in globals():
            label_nom_food.config(text=f"({nom})", fg=p["accent"] if nom != "Inconnu" else p["text_muted"])
        if 'combo_food' in globals() and valeur in FOOD_TYPES:
            texte_cible = f"{valeur} - {nom}"
            if combo_food.get() != texte_cible:
                combo_food.set(texte_cible)

def synchroniser_combo_food(event=None):
    if 'combo_food' in globals() and len(cases_entrees) > 6:
        sel = combo_food.get()
        if " - " in sel:
            fid = sel.split(" - ")[0]
            cases_entrees[6].delete(0, tk.END)
            cases_entrees[6].insert(0, fid)
            maj_nom_nourriture()

def maj_icone_rang(event=None):
    global image_rang_reference
    p = THEMES.get(THEME_ACTIF, THEMES["Mode Sakura"])
    if len(cases_entrees) > 3:
        valeur_rarite = cases_entrees[3].get().strip()
        nom_rang = get_rank_label(valeur_rarite)
        if 'label_nom_rank' in globals():
            label_nom_rank.config(text=f"({nom_rang})" if nom_rang != "Inconnu" else "")
        if 'combo_rank' in globals() and valeur_rarite in RANK_NAMES:
            texte_cible = f"{valeur_rarite} - {RANK_NAMES[valeur_rarite]['nom']}"
            if combo_rank.get() != texte_cible:
                combo_rank.set(texte_cible)

        if valeur_rarite in COORDONNEES_RANGS and CHEMIN_SPRITESHEET:
            try:
                img_complete = Image.open(CHEMIN_SPRITESHEET)
                col, lig = COORDONNEES_RANGS[valeur_rarite]
                icone = decouper_icone(img_complete, col, lig, 8, 3)
                image_rang_reference = ImageTk.PhotoImage(icone)
                label_rang.config(image=image_rang_reference, text="")
            except Exception:
                label_rang.config(image='', text=f"R:{valeur_rarite}")
        else:
            label_rang.config(image='', text="")

def synchroniser_combo_rank(event=None):
    if 'combo_rank' in globals() and len(cases_entrees) > 3:
        sel = combo_rank.get()
        if " - " in sel:
            rid = sel.split(" - ")[0]
            cases_entrees[3].delete(0, tk.END)
            cases_entrees[3].insert(0, rid)
            maj_icone_rang()

def maj_icone_kind(event=None):
    global image_kind_reference
    p = THEMES.get(THEME_ACTIF, THEMES["Mode Sakura"])
    if len(cases_entrees) > 4:
        valeur_kind = cases_entrees[4].get().strip()
        nom_kind = get_kind_label(valeur_kind)
        if 'label_nom_kind' in globals():
            label_nom_kind.config(text=f"({nom_kind})" if nom_kind != "Inconnu" else "")
        if 'combo_kind' in globals() and valeur_kind in KIND_NAMES:
            texte_cible = f"{valeur_kind} - {KIND_NAMES[valeur_kind]['nom']}"
            if combo_kind.get() != texte_cible:
                combo_kind.set(texte_cible)

        if valeur_kind in COORDONNEES_KINDS and CHEMIN_KIND_SPRITESHEET:
            try:
                img_complete = Image.open(CHEMIN_KIND_SPRITESHEET)
                col, lig = COORDONNEES_KINDS[valeur_kind]
                icone = decouper_icone(img_complete, col, lig, 3, 4)
                image_kind_reference = ImageTk.PhotoImage(icone)
                label_kind.config(image=image_kind_reference, text="")
            except Exception:
                label_kind.config(image='', text=f"T:{valeur_kind}")
        else:
            label_kind.config(image='', text="")

def synchroniser_combo_kind(event=None):
    if 'combo_kind' in globals() and len(cases_entrees) > 4:
        sel = combo_kind.get()
        if " - " in sel:
            kid = sel.split(" - ")[0]
            cases_entrees[4].delete(0, tk.END)
            cases_entrees[4].insert(0, kid)
            maj_icone_kind()

def verifier_stats_interface(event=None):
    if len(cases_entrees) <= 11 or 'label_stat_status' not in globals(): return
    bhp = cases_entrees[8].get()
    mhp = cases_entrees[9].get()
    batk = cases_entrees[10].get()
    matk = cases_entrees[11].get()
    valide, erreurs, avertissements = verifier_coherence_stats(bhp, mhp, batk, matk)
    if not valide:
        label_stat_status.config(text=f"⚠️ {erreurs[0]}", fg="#e74c3c")
    elif avertissements:
        label_stat_status.config(text=f"ℹ️ {avertissements[0]}", fg="#f39c12")
    else:
        label_stat_status.config(text="✓ Statistiques cohérentes", fg="#2ecc71")

def ouvrir_dialogue_stat_presets():
    p = THEMES.get(THEME_ACTIF, THEMES["Mode Sakura"])
    fen_p = tk.Toplevel(fenetre)
    fen_p.title("⚡ Modèles de statistiques (Stat Presets)")
    fen_p.geometry("450x370")
    fen_p.configure(bg=p["bg_main"])
    fen_p.transient(fenetre)

    tk.Label(fen_p, text="Choisir un modèle statistique par Rang :",
             font=("Segoe UI", 11, "bold"), bg=p["bg_main"], fg=p["accent"]).pack(pady=12)

    rang_actuel = cases_entrees[3].get().strip() if len(cases_entrees) > 3 else "6"
    if rang_actuel not in STAT_PRESETS: rang_actuel = "6"

    lbl_info = tk.Label(fen_p, text="", font=("Segoe UI", 9), bg=p["bg_main"], fg=p["text_main"], justify=tk.LEFT)

    def actualiser_apercu(event=None):
        r_id = combo_p_rang.get().split(" - ")[0]
        pr = get_stat_preset(r_id)
        if pr:
            txt = (f"Modèle : {pr['nom']}\n"
                   f"• Niveau Max : {pr['max_level']}\n"
                   f"• PV Base    : {pr['base_hp']}  →  PV Max : {pr['max_hp']}\n"
                   f"• ATK Base   : {pr['base_atk']}  →  ATK Max : {pr['max_atk']}")
            lbl_info.config(text=txt)

    combo_p_rang = ttk.Combobox(fen_p, values=[f"{k} - {v['nom']}" for k, v in STAT_PRESETS.items()],
                                width=26, state="readonly")
    for idx, item in enumerate(combo_p_rang["values"]):
        if item.startswith(f"{rang_actuel} -"):
            combo_p_rang.current(idx)
            break
    if not combo_p_rang.get(): combo_p_rang.current(5)
    combo_p_rang.pack(pady=6)
    combo_p_rang.bind("<<ComboboxSelected>>", actualiser_apercu)

    lbl_info.pack(pady=12, padx=20)
    actualiser_apercu()

    def appliquer():
        r_id = combo_p_rang.get().split(" - ")[0]
        pr = get_stat_preset(r_id)
        if pr and len(cases_entrees) > 11:
            cases_entrees[7].delete(0, tk.END); cases_entrees[7].insert(0, str(pr['max_level']))
            cases_entrees[8].delete(0, tk.END); cases_entrees[8].insert(0, str(pr['base_hp']))
            cases_entrees[9].delete(0, tk.END); cases_entrees[9].insert(0, str(pr['max_hp']))
            cases_entrees[10].delete(0, tk.END); cases_entrees[10].insert(0, str(pr['base_atk']))
            cases_entrees[11].delete(0, tk.END); cases_entrees[11].insert(0, str(pr['max_atk']))
            verifier_stats_interface()
            fen_p.destroy()
            messagebox.showinfo("Stats appliquées", f"Les statistiques du {pr['nom']} ont été appliquées !")

    btn_f = tk.Frame(fen_p, bg=p["bg_main"])
    btn_f.pack(fill=tk.X, padx=20, pady=(10, 16))
    tk.Button(btn_f, text="Annuler", command=fen_p.destroy, font=("Segoe UI", 9),
              bg=p["btn_bg"], fg=p["btn_fg"], relief="flat", bd=1).pack(side=tk.RIGHT, padx=(6, 0))
    tk.Button(btn_f, text="Appliquer les stats", font=("Segoe UI", 9, "bold"),
              bg=p["btn_special_bg"], fg=p["btn_special_fg"], relief="flat", bd=1,
              command=appliquer).pack(side=tk.RIGHT)


# ==========================================
# GESTION DES RECHERCHES ET FILTRES
# ==========================================
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
            if yokai_id in dictionnaire_skills:
                typ = dictionnaire_skills[yokai_id].get("TypeID", "").lower()
                nom_typ = SOULT_TYPES.get(dictionnaire_skills[yokai_id].get("TypeID", ""), "").lower()
                if valeur == typ or valeur in nom_typ:
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

        if index_col == 3:  # Rang
            if matches_rank(valeur, colonnes[3]):
                resultats.append(f"[{classifier_yokai(yokai_id)}] ID: {yokai_id} - Nom: {colonnes[1]} (Rang: {get_rank_label(colonnes[3])})")
            continue

        if index_col == 4:  # Tribu / Kind
            if matches_kind(valeur, colonnes[4]):
                resultats.append(f"[{classifier_yokai(yokai_id)}] ID: {yokai_id} - Nom: {colonnes[1]} (Tribu: {get_kind_label(colonnes[4])})")
            continue
        
        if index_col == 6:  # Nourriture
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

    p = THEMES.get(THEME_ACTIF, THEMES["Mode Sakura"])
    fenetre_res = tk.Toplevel(fenetre)
    fenetre_res.title(f"Résultats ({len(resultats)})")
    fenetre_res.geometry("450x360")
    fenetre_res.configure(bg=p["bg_main"])
    tk.Label(fenetre_res, text="Double-cliquez pour charger ce Yo-kai", font=("Segoe UI", 9, "italic"), bg=p["bg_main"], fg=p["accent"]).pack(pady=6)
    
    listbox = tk.Listbox(fenetre_res, font=("Segoe UI", 10), relief=tk.SOLID, bd=1,
                         bg=p["entry_bg"], fg=p["entry_fg"],
                         selectbackground=p["accent_glow"], selectforeground="#ffffff")
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
    if not id_recherche: return
    
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
            synchroniser_strong_avec_yokai()
            ajouter_historique_recent(colonnes[0], colonnes[1] if len(colonnes) > 1 else "")
            return

    vider_interface()
    messagebox.showwarning("Introuvable", "Aucun Yo-kai ne possède ce YoukaiId.")

def obtenir_dernier_id():
    prochain_id = max([int(l.split('|')[0]) for l in lignes_yokai if l.split('|')[0].isdigit()], default=0) + 1
    messagebox.showinfo("ID dispo", f"💡 Prochain ID libre : {prochain_id}")

def nouveau_yokai():
    ids_existants = [int(l.split('|')[0]) for l in lignes_yokai if l.split('|')[0].isdigit()]
    prochain_id = max(ids_existants, default=0) + 1
    dids_existants = [int(l.split('|')[14]) for l in lignes_yokai if len(l.split('|')) > 14 and l.split('|')[14].isdigit()]
    prochain_did = max(dids_existants, default=0) + 1

    vider_interface()
    cases_entrees[0].insert(0, str(prochain_id))
    cases_entrees[1].insert(0, "Nouveau Yo-kai")
    cases_entrees[3].insert(0, "6")   # Rang S par défaut
    cases_entrees[4].insert(0, "1")   # Brave par défaut
    cases_entrees[5].insert(0, "1")
    cases_entrees[6].insert(0, "1")
    cases_entrees[7].insert(0, "50")
    cases_entrees[8].insert(0, "360")
    cases_entrees[9].insert(0, "760")
    cases_entrees[10].insert(0, "280")
    cases_entrees[11].insert(0, "640")
    cases_entrees[14].insert(0, str(prochain_did))

    maj_icone_rang()
    maj_icone_kind()
    maj_nom_nourriture()
    verifier_stats_interface()
    messagebox.showinfo("Nouveau Yo-kai", f"Nouvelle fiche initialisée avec le YoukaiId {prochain_id}.")


# ==========================================
# PRIORITÉ ABSOLUE : DUPLIQUER / CLONER YO-KAI
# ==========================================
def dupliquer_yokai_courant():
    global lignes_yokai, dictionnaire_skills, dictionnaire_skill_levels
    global dictionnaire_strong_skills, dictionnaire_strong_skill_levels
    global dictionnaire_bonus_effect, dictionnaire_bonus_effect_level

    source_id = cases_entrees[0].get().strip() if cases_entrees else ""
    if not source_id or index_trouve == -1:
        messagebox.showwarning("Duplication", "Veuillez d'abord charger un Yo-kai à dupliquer.")
        return

    # Sauvegarder d'abord les saisies de l'interface dans la mémoire pour ne rien perdre
    afficher_donnees_niveau(depuis_code=False)
    if MODE_JEU == "PuniPuni":
        _lire_niveau_strong_courant()
    if activer_bonus_effect_var and activer_bonus_effect_var.get():
        afficher_donnees_bonus_niveau(depuis_code=False)

    source_nom = cases_entrees[1].get().strip() if len(cases_entrees) > 1 else ""

    # Calcul du prochain ID de Yo-kai libre
    ids_existants = [int(l.split('|')[0]) for l in lignes_yokai if l.split('|')[0].isdigit()]
    prochain_id = max(ids_existants, default=0) + 1

    # Calcul du prochain Dictionary ID libre
    dids_existants = [int(l.split('|')[14]) for l in lignes_yokai if len(l.split('|')) > 14 and l.split('|')[14].isdigit()]
    prochain_did = max(dids_existants, default=0) + 1

    p = THEMES.get(THEME_ACTIF, THEMES["Mode Sakura"])
    fen_clone = tk.Toplevel(fenetre)
    fen_clone.title("✨ Dupliquer / Cloner le Yo-kai")
    fen_clone.geometry("490x380")
    fen_clone.configure(bg=p["bg_main"])
    fen_clone.transient(fenetre)
    fen_clone.grab_set()

    tk.Label(fen_clone, text=f"Cloner le Yo-kai : [{source_id}] {source_nom}",
             font=("Segoe UI", 11, "bold"), bg=p["bg_main"], fg=p["accent"]).pack(pady=(16, 6))

    nb_lvl_source = len(dictionnaire_skill_levels.get(source_id, {}))
    txt_info = f"ℹ️ Tous les niveaux d'Âmultime ({max(7, nb_lvl_source)} niveaux) seront dupliqués fidèlement."
    tk.Label(fen_clone, text=txt_info, font=("Segoe UI", 9, "italic"),
             bg=p["bg_main"], fg=p["text_muted"]).pack(pady=(0, 10))

    frame_champs = tk.Frame(fen_clone, bg=p["bg_main"])
    frame_champs.pack(fill=tk.X, padx=20)

    # Nouveau YoukaiId
    tk.Label(frame_champs, text="Nouveau YoukaiId (0) :", font=("Segoe UI", 9, "bold"),
             bg=p["bg_main"], fg=p["text_main"]).grid(row=0, column=0, sticky="e", padx=6, pady=6)
    entree_nid = tk.Entry(frame_champs, width=22, font=("Segoe UI", 9), relief=tk.SOLID, bd=1,
                          bg=p["entry_bg"], fg=p["entry_fg"], insertbackground=p["accent"])
    entree_nid.insert(0, str(prochain_id))
    entree_nid.grid(row=0, column=1, sticky="w", padx=6, pady=6)

    # Nouveau Nom
    tk.Label(frame_champs, text="Nouveau Nom (1) :", font=("Segoe UI", 9, "bold"),
             bg=p["bg_main"], fg=p["text_main"]).grid(row=1, column=0, sticky="e", padx=6, pady=6)
    entree_nnom = tk.Entry(frame_champs, width=22, font=("Segoe UI", 9), relief=tk.SOLID, bd=1,
                           bg=p["entry_bg"], fg=p["entry_fg"], insertbackground=p["accent"])
    entree_nnom.insert(0, f"{source_nom} (Copie)")
    entree_nnom.grid(row=1, column=1, sticky="w", padx=6, pady=6)

    # Nouveau DictionaryId
    tk.Label(frame_champs, text="Dictionary ID (14) :", font=("Segoe UI", 9, "bold"),
             bg=p["bg_main"], fg=p["text_main"]).grid(row=2, column=0, sticky="e", padx=6, pady=6)
    entree_ndid = tk.Entry(frame_champs, width=22, font=("Segoe UI", 9), relief=tk.SOLID, bd=1,
                           bg=p["entry_bg"], fg=p["entry_fg"], insertbackground=p["accent"])
    entree_ndid.insert(0, str(prochain_did))
    entree_ndid.grid(row=2, column=1, sticky="w", padx=6, pady=6)

    # Checkbox pour sauvegarde directe dans les fichiers
    var_sauvegarde_directe = tk.BooleanVar(value=True)
    cb_save = tk.Checkbutton(fen_clone, text="Sauvegarder immédiatement dans les fichiers d'origine (avec backup)",
                             variable=var_sauvegarde_directe, font=("Segoe UI", 9),
                             bg=p["bg_main"], fg=p["text_main"], selectcolor=p["entry_bg"],
                             activebackground=p["bg_main"], activeforeground=p["text_main"])
    cb_save.pack(pady=10)

    def valider_duplication():
        nouveau_id = entree_nid.get().strip()
        nouveau_nom = entree_nnom.get().strip()
        nouveau_did = entree_ndid.get().strip()

        if not nouveau_id:
            messagebox.showerror("Erreur", "Le YoukaiId ne peut pas être vide.")
            return

        conflits = verifier_conflits_yokai(lignes_yokai, nouveau_id, nouveau_did)
        if conflits:
            msg = "\n".join(conflits) + "\n\nVoulez-vous continuer malgré ces conflits ?"
            if not messagebox.askyesno("Conflit détecté", msg, icon="warning"):
                return

        # 1. Duplication des 39 colonnes de base du Yo-kai
        valeurs_copie = [assainir_texte_export(case.get()) for case in cases_entrees]
        while len(valeurs_copie) < len(CHAMPS_YOKAI): valeurs_copie.append("")
        while len(valeurs_copie) > len(CHAMPS_YOKAI): valeurs_copie.pop()

        valeurs_copie[0] = nouveau_id
        if nouveau_nom: valeurs_copie[1] = nouveau_nom
        if nouveau_did and len(valeurs_copie) > 14: valeurs_copie[14] = nouveau_did

        ligne_nouveau_yokai = "|".join(valeurs_copie)

        # 2. Duplication du skill (Mst Skill)
        type_id = combo_soult_type.get().split(" - ")[0] if " - " in combo_soult_type.get() else "-1"
        champs_skill_liste = [
            nouveau_id,
            assainir_texte_export(cases_skills["Nom"].get()),
            type_id,
            assainir_texte_export(cases_skills["Description"].get()),
            cases_skills["Propriete1"].get() or "0",
            cases_skills["Propriete2"].get() or "0",
            cases_skills["Anim3D"].get(),
            cases_skills["Anim2D"].get(),
            cases_skills["Anim2D_2"].get(),
            cases_skills["SkillUnk0"].get() or "0",
            cases_skills["SkillUnk1"].get() or "0",
            cases_skills["SkillUnk2"].get() or "0",
            cases_skills["SkillUnk3"].get() or "0",
            cases_skills["SkillUnk4"].get(),
        ]
        ligne_nouveau_skill = "|".join(champs_skill_liste)
        dictionnaire_skills[nouveau_id] = {
            "Nom": champs_skill_liste[1],
            "TypeID": champs_skill_liste[2],
            "Description": champs_skill_liste[3],
            "Propriete1": champs_skill_liste[4],
            "Propriete2": champs_skill_liste[5],
            "Anim3D": champs_skill_liste[6],
            "Anim2D": champs_skill_liste[7],
            "Anim2D_2": champs_skill_liste[8],
            "SkillUnk0": champs_skill_liste[9],
            "SkillUnk1": champs_skill_liste[10],
            "SkillUnk2": champs_skill_liste[11],
            "SkillUnk3": champs_skill_liste[12],
            "SkillUnk4": champs_skill_liste[13],
        }

        # 3. Duplication INTÉGRALE de tous les niveaux d'Âmultime (Mst Skill Level 1 à 7)
        source_levels = dictionnaire_skill_levels.get(source_id, {})
        base_lvl_data = source_levels.get(niveau_actuel_var.get(), [""] * 13)

        dictionnaire_skill_levels[nouveau_id] = {}
        lignes_levels_dupliques = []
        for lvl in range(1, 8):
            src_cols = source_levels.get(str(lvl), list(base_lvl_data))
            new_cols = list(src_cols)
            while len(new_cols) < 13: new_cols.append("")
            new_cols[0] = nouveau_id
            new_cols[1] = str(lvl)
            dictionnaire_skill_levels[nouveau_id][str(lvl)] = new_cols
            lignes_levels_dupliques.append("|".join(assainir_texte_export(c) for c in new_cols))

        # 4. Duplication du strong skill si présent
        lignes_strong_dupliques = []
        if source_id in dictionnaire_strong_skills:
            dictionnaire_strong_skills[nouveau_id] = dict(dictionnaire_strong_skills[source_id])
            if source_id in dictionnaire_strong_skill_levels:
                dictionnaire_strong_skill_levels[nouveau_id] = {}
                for lvl_s, cols_s in dictionnaire_strong_skill_levels[source_id].items():
                    n_cols_s = list(cols_s)
                    while len(n_cols_s) < 13: n_cols_s.append("")
                    n_cols_s[0] = nouveau_id
                    n_cols_s[1] = str(lvl_s)
                    dictionnaire_strong_skill_levels[nouveau_id][str(lvl_s)] = n_cols_s
                    lignes_strong_dupliques.append("|".join(assainir_texte_export(c) for c in n_cols_s))

        # 5. Duplication des bonus effects si présents
        bonus_actif = activer_bonus_effect_var.get() if activer_bonus_effect_var is not None else False
        lignes_bonus_effect_dupliques = []
        lignes_bonus_effect_level_dupliques = []
        if bonus_actif:
            for (yid, sid), v in list(dictionnaire_bonus_effect.items()):
                if yid == source_id:
                    v_clone = _normaliser_ligne_bonus_effect(v, nouveau_id, sid)
                    dictionnaire_bonus_effect[(nouveau_id, sid)] = v_clone
                    lignes_bonus_effect_dupliques.append("|".join(assainir_texte_export(c) for c in v_clone))
            for (yid, sid), n_dict in list(dictionnaire_bonus_effect_level.items()):
                if yid == source_id:
                    dictionnaire_bonus_effect_level[(nouveau_id, sid)] = {}
                    for lvl_b, data_b in n_dict.items():
                        d_clone = _normaliser_ligne_bonus_level(data_b, nouveau_id, sid, lvl_b)
                        dictionnaire_bonus_effect_level[(nouveau_id, sid)][lvl_b] = d_clone
                        lignes_bonus_effect_level_dupliques.append("|".join(assainir_texte_export(c) for c in d_clone))

        # 6. Sauvegarde directe dans les fichiers d'origine si cochée
        if var_sauvegarde_directe.get():
            try:
                maj_fichier_original(FICHIER_DB, ligne_nouveau_yokai, nouveau_id, insertion_par_dictionary_id=True, avec_backup=True)
                maj_fichier_original(FICHIER_SKILL_DB, ligne_nouveau_skill, nouveau_id, avec_backup=True)
                maj_fichier_original(FICHIER_SKILL_LEVEL_DB, lignes_levels_dupliques, nouveau_id, avec_backup=True)

                if FICHIER_STRONG_SKILL_DB and lignes_strong_dupliques:
                    row_strong = [nouveau_id] + [dictionnaire_strong_skills[nouveau_id].get(c, "") for c in COLONNES_STRONG_SKILL]
                    maj_fichier_original(FICHIER_STRONG_SKILL_DB, "|".join(row_strong), nouveau_id, avec_backup=True)
                if FICHIER_STRONG_SKILL_LEVEL_DB and lignes_strong_dupliques:
                    maj_fichier_original(FICHIER_STRONG_SKILL_LEVEL_DB, lignes_strong_dupliques, nouveau_id, avec_backup=True)

                if FICHIER_BONUS_EFFECT_DB and lignes_bonus_effect_dupliques:
                    maj_fichier_original(FICHIER_BONUS_EFFECT_DB, lignes_bonus_effect_dupliques, nouveau_id, avec_backup=True)
                if FICHIER_BONUS_EFFECT_LEVEL_DB and lignes_bonus_effect_level_dupliques:
                    maj_fichier_original(FICHIER_BONUS_EFFECT_LEVEL_DB, lignes_bonus_effect_level_dupliques, nouveau_id, avec_backup=True)

                charger_fichier()
                charger_skills()
                charger_skill_levels()
                charger_strong_skills()
                charger_strong_skill_levels()
                charger_bonus_effects()
                charger_bonus_effect_levels()
            except Exception as e:
                messagebox.showerror("Erreur sauvegarde clone", f"Erreur lors de l'enregistrement du clone :\n{e}")
                return
        else:
            lignes_yokai.append(ligne_nouveau_yokai)

        fen_clone.destroy()

        # Charger immédiatement le nouveau Yo-kai dans l'interface
        entree_recherche_id.delete(0, tk.END)
        entree_recherche_id.insert(0, nouveau_id)
        charger_yokai_par_id()

        messagebox.showinfo(
            "Duplication réussie !",
            f"✨ Le Yo-kai '{source_nom}' a été cloné avec succès !\n\n"
            f"• Nouvel ID : {nouveau_id}\n"
            f"• Nom : {valeurs_copie[1]}\n"
            f"• Niveaux d'Âmultime copiés : {len(lignes_levels_dupliques)}/7 conservés à 100%."
        )

    btn_frame = tk.Frame(fen_clone, bg=p["bg_main"])
    btn_frame.pack(fill=tk.X, padx=20, pady=(10, 16))

    tk.Button(btn_frame, text="Annuler", command=fen_clone.destroy, font=("Segoe UI", 9),
              bg=p["btn_bg"], fg=p["btn_fg"], relief="flat", bd=1).pack(side=tk.RIGHT, padx=(6, 0))
    tk.Button(btn_frame, text="✨ Cloner le Yo-kai", font=("Segoe UI", 9, "bold"),
              bg=p["btn_special_bg"], fg=p["btn_special_fg"], relief="flat", bd=1,
              command=valider_duplication).pack(side=tk.RIGHT)


# ==========================================
# GESTION DES CASES ET NIVEAUX
# ==========================================
def remplir_cases(colonnes):
    yokai_id = colonnes[0]

    for i, case in enumerate(cases_entrees):
        case.delete(0, tk.END)
        if i < len(colonnes):
            case.insert(0, colonnes[i])
            
    maj_nom_nourriture()
    maj_icone_rang()
    maj_icone_kind()
    charger_icone_ayd()
    verifier_stats_interface()

    for case in cases_skills.values():
        if isinstance(case, tk.Entry):
            case.delete(0, tk.END)

    for unk_col in ["SkillUnk0", "SkillUnk1", "SkillUnk2", "SkillUnk3", "SkillUnk4"]:
        if unk_col in cases_skills:
            cases_skills[unk_col].insert(0, "0" if unk_col != "SkillUnk4" else "")

    if yokai_id in dictionnaire_skills:
        skill = dictionnaire_skills[yokai_id]
        for k in ["Nom", "Description", "Propriete1", "Propriete2", "Anim3D", "Anim2D", "Anim2D_2", "SkillUnk0", "SkillUnk1", "SkillUnk2", "SkillUnk3", "SkillUnk4"]:
            if k in cases_skills:
                cases_skills[k].delete(0, tk.END)
                cases_skills[k].insert(0, skill.get(k, "0" if ("SkillUnk" in k and k != "SkillUnk4") else ""))
        
        type_id = skill["TypeID"]
        combo_soult_type.set(f"{type_id} - {SOULT_TYPES.get(type_id, 'Inconnu')}")

def afficher_donnees_niveau(event=None, depuis_code=False):
    global niveau_precedent
    yokai_id = cases_entrees[0].get().strip() if cases_entrees else ""
    if not yokai_id: return
    
    if not depuis_code:
        if yokai_id not in dictionnaire_skill_levels: dictionnaire_skill_levels[yokai_id] = {}
        cols_lvl = [""] * 13
        cols_lvl[0], cols_lvl[1] = yokai_id, niveau_precedent
        for idx, case in cases_skill_levels.items(): cols_lvl[idx] = assainir_texte_export(case.get())
        dictionnaire_skill_levels[yokai_id][niveau_precedent] = cols_lvl
    
    niveau_choisi = niveau_actuel_var.get()
    for case in cases_skill_levels.values(): case.delete(0, tk.END)
        
    if yokai_id in dictionnaire_skill_levels and niveau_choisi in dictionnaire_skill_levels[yokai_id]:
        donnees_niveau = dictionnaire_skill_levels[yokai_id][niveau_choisi]
        for idx, case in cases_skill_levels.items():
            if idx < len(donnees_niveau): case.insert(0, donnees_niveau[idx])
                
    niveau_precedent = niveau_choisi


# ==========================================
# STRONG SKILL (exclusif Puni Puni)
# ==========================================
def _lire_niveau_strong_courant():
    sid = strong_id_actuel_var.get().strip() if strong_id_actuel_var else ""
    if not sid: return
    cols_lvl = [""] * 13
    cols_lvl[0], cols_lvl[1] = sid, niveau_strong_precedent
    for idx, case in cases_strong_skill_levels.items():
        cols_lvl[idx] = assainir_texte_export(case.get())
    dictionnaire_strong_skill_levels.setdefault(sid, {})[niveau_strong_precedent] = cols_lvl

def afficher_niveau_strong(event=None, depuis_code=False):
    global niveau_strong_precedent
    sid = strong_id_actuel_var.get().strip() if strong_id_actuel_var else ""
    if not sid: return
    if not depuis_code:
        _lire_niveau_strong_courant()
    nv = niveau_strong_actuel_var.get()
    for c in cases_strong_skill_levels.values(): c.delete(0, tk.END)
    if sid in dictionnaire_strong_skill_levels and nv in dictionnaire_strong_skill_levels[sid]:
        cols = dictionnaire_strong_skill_levels[sid][nv]
        for idx, c in cases_strong_skill_levels.items():
            if idx < len(cols): c.insert(0, cols[idx])
    niveau_strong_precedent = nv

def charger_strong_skill_par_id(event=None, sid=None):
    if sid is None:
        sid = strong_id_actuel_var.get().strip() if strong_id_actuel_var else ""
    if not sid: return
    if sid not in dictionnaire_strong_skills:
        for c in cases_strong_skills.values():
            if isinstance(c, tk.Entry): c.delete(0, tk.END)
            elif isinstance(c, ttk.Combobox): c.set("")
        for c in cases_strong_skill_levels.values(): c.delete(0, tk.END)
        return
    donnees = dictionnaire_strong_skills[sid]
    for cle, case in cases_strong_skills.items():
        if cle == "TypeID":
            type_id = donnees.get("TypeID", "")
            case.set(f"{type_id} - {SOULT_TYPES.get(type_id, 'Inconnu')}" if type_id else "")
        elif isinstance(case, tk.Entry):
            case.delete(0, tk.END)
            case.insert(0, donnees.get(cle, ""))
    niveau_strong_actuel_var.set("1")
    afficher_niveau_strong(depuis_code=True)

def synchroniser_strong_avec_yokai():
    if MODE_JEU != "PuniPuni" or not cases_entrees: return
    yid = cases_entrees[0].get().strip()
    if yid:
        strong_id_actuel_var.set(yid)
        charger_strong_skill_par_id(sid=yid)

def _ligne_strong_skill(sid):
    type_id = cases_strong_skills["TypeID"].get().split(" - ")[0] if " - " in cases_strong_skills["TypeID"].get() else (cases_strong_skills["TypeID"].get().strip() or "-1")
    def v(cle, defaut=""):
        return cases_strong_skills[cle].get()
    return "|".join([
        sid,
        assainir_texte_export(v("Nom")),
        type_id,
        assainir_texte_export(v("Description")),
        v("Propriete1") or "0",
        v("Propriete2") or "0",
        v("Anim3D"),
        v("Anim2D"),
        v("Anim2D_2"),
        v("SkillUnk0") or "0",
        v("SkillUnk1") or "0",
        v("SkillUnk2") or "0",
        v("SkillUnk3") or "0",
        v("Reserve"),
        v("CutinA"),
        v("CutinB"),
        v("LienExterne")
    ])

def sauvegarder_strong_skill():
    sid = strong_id_actuel_var.get().strip() if strong_id_actuel_var else ""
    if not sid:
        return messagebox.showerror("Erreur", "Veuillez renseigner un ID de Strong Skill.")
    if not FICHIER_STRONG_SKILL_DB or not FICHIER_STRONG_SKILL_LEVEL_DB:
        return messagebox.showerror(
            "Fichiers manquants",
            "Les chemins des fichiers Strong Skill (_strong_skill et _strong_skill_level) "
            "ne sont pas configurés ou n'existent pas dans votre dossier de jeu.")
    _lire_niveau_strong_courant()
    ligne_skill = _ligne_strong_skill(sid)
    base_lvl = dictionnaire_strong_skill_levels.get(sid, {}).get(niveau_strong_actuel_var.get(), [""] * 13)
    lignes_levels = []
    for lvl in range(1, 8):
        data = list(dictionnaire_strong_skill_levels.get(sid, {}).get(str(lvl), list(base_lvl)))
        while len(data) < 13: data.append("")
        data[0] = sid
        data[1] = str(lvl)
        lignes_levels.append("|".join(assainir_texte_export(d) for d in data))
    try:
        maj_fichier_original(FICHIER_STRONG_SKILL_DB, ligne_skill, sid, avec_backup=True)
        maj_fichier_original(FICHIER_STRONG_SKILL_LEVEL_DB, lignes_levels, sid, avec_backup=True)
        charger_strong_skills()
        charger_strong_skill_levels()
        messagebox.showinfo("Succès", f"Strong Skill enregistré pour l'ID {sid} !")
    except Exception as e:
        messagebox.showerror("Erreur Strong Skill", str(e))

def basculer_mode_jeu():
    global MODE_JEU
    MODE_JEU = "PuniPuni" if MODE_JEU == "WibWob" else "WibWob"
    sauvegarder_config()
    appliquer_mode_jeu()
    messagebox.showinfo("Mode de jeu", f"Mode actif : {MODE_JEU}")

def appliquer_mode_jeu():
    btn_mode_jeu.config(text=f"🎮 Mode : {MODE_JEU}")
    if MODE_JEU == "PuniPuni":
        frame_strong.pack(fill=tk.X, padx=8, pady=8)
        synchroniser_strong_avec_yokai()
    else:
        frame_strong.pack_forget()


# ==========================================
# BONUS EFFECT (SUPPORT MULTI-SKILLS : 1, 2, 3)
# ==========================================
cartes_bonus_ui = {}

def toggle_champs_bonus_effect():
    if activer_bonus_effect_var.get():
        sub_cadre_bonus.pack(fill=tk.X, expand=True)
        yokai_id = cases_entrees[0].get().strip() if cases_entrees else ""
        if yokai_id:
            cles = sorted([sid for (yid, sid) in dictionnaire_bonus_effect.keys() if yid == yokai_id],
                          key=lambda s: int(s) if s.isdigit() else s)
            if not cles and not cartes_bonus_ui:
                ajouter_nouveau_skill("1")
            else:
                charger_bonus_effet_pour_yokai(yokai_id)
    else:
        sub_cadre_bonus.pack_forget()

def charger_bonus_effet_pour_yokai(yokai_id):
    for sid in list(cartes_bonus_ui.keys()):
        if cartes_bonus_ui[sid]["cadre"]:
            cartes_bonus_ui[sid]["cadre"].destroy()
    cartes_bonus_ui.clear()

    sids = sorted([sid for (yid, sid) in dictionnaire_bonus_effect.keys() if yid == yokai_id],
                  key=lambda s: int(s) if s.isdigit() else s)
    if sids:
        activer_bonus_effect_var.set(True)
        sub_cadre_bonus.pack(fill=tk.X, expand=True)
        for sid in sids:
            creer_carte_skill(sid, yokai_id)
        maj_boutons_ajout_skill()
        actualiser_affichage_mst_bonus()
        appliquer_theme_global(THEME_ACTIF)
    else:
        activer_bonus_effect_var.set(False)
        sub_cadre_bonus.pack_forget()
        actualiser_affichage_mst_bonus()

def creer_carte_skill(sid, yokai_id):
    if sid in cartes_bonus_ui:
        recharger_donnees_carte_skill(sid, yokai_id)
        return

    cle = (yokai_id, sid)
    donnees = _normaliser_ligne_bonus_effect(
        dictionnaire_bonus_effect.get(cle, [yokai_id, sid, "Description du Skill", "1", "0", "0", "0", "0", "0", "0"]),
        yokai_id, sid
    )

    if sid == "1":
        titre = "  🌟 Skill 1 (Permanent / SubID 1)  "
    elif sid == "2":
        titre = "  ✨ Skill 2 (Déblocable S no Sho / SubID 2)  "
    elif sid == "3":
        titre = "  ⚡ Skill 3 (Déblocable S no Sho / SubID 3)  "
    else:
        titre = f"  🎁 Skill {sid} (SubID {sid})  "

    p = THEMES.get(THEME_ACTIF, THEMES["Mode Sakura"])
    card = tk.LabelFrame(frame_skills_container, text=titre, font=("Segoe UI", 9, "bold"),
                         padx=10, pady=8, relief=tk.SOLID, bd=1, highlightthickness=1)
    card.est_carte = True
    card.pack(fill=tk.X, padx=8, pady=6)

    # Barre supérieure avec bouton de suppression pour les skills secondaires
    if sid != "1":
        frame_top_c = tk.Frame(card)
        frame_top_c.est_carte = True
        frame_top_c.pack(fill=tk.X, pady=(0, 4))
        btn_del = tk.Button(frame_top_c, text=f"🗑️ Retirer le Skill {sid}", font=("Segoe UI", 8, "bold"),
                            relief="flat", bd=1, command=lambda s=sid: supprimer_skill(s))
        btn_del.couleur_texte_speciale = "#e74c3c"
        btn_del.pack(side=tk.RIGHT, padx=2)

    # Grille des champs principaux (ywp_mst_youkai_bonus_effect : 10 colonnes 0..9)
    frame_grid = tk.Frame(card)
    frame_grid.est_carte = True
    frame_grid.pack(fill=tk.X, pady=(0, 4))

    # Ligne 0 : Type (Col 3), Ressource / Effet (Col 4), Livre ID (Col 8), Slot (Col 9)
    tk.Label(frame_grid, text="Type (Col 3) :", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="e", padx=(8, 4), pady=4)
    combo_type = ttk.Combobox(frame_grid, values=[f"{k} - {v}" for k, v in YW_BONUS_EFFECTS.items()], width=46, state="readonly")
    type_id = donnees[3] if len(donnees) > 3 and donnees[3] else "1"
    combo_type.set(f"{type_id} - {YW_BONUS_EFFECTS.get(type_id, 'Inconnu')}")
    combo_type.grid(row=0, column=1, sticky="w", padx=4, pady=4)
    combo_type.bind("<<ComboboxSelected>>", lambda e, s=sid: on_skill_field_change(s))

    tk.Label(frame_grid, text="Ressource (Col 4) :", font=("Segoe UI", 9)).grid(row=0, column=2, sticky="e", padx=(8, 4), pady=4)
    entree_res = tk.Entry(frame_grid, width=22, font=("Segoe UI", 9), relief=tk.SOLID, bd=1)
    entree_res.insert(0, donnees[4] if len(donnees) > 4 else "0")
    entree_res.grid(row=0, column=3, sticky="w", padx=4, pady=4)
    entree_res.bind("<KeyRelease>", lambda e, s=sid: on_skill_field_change(s))

    tk.Label(frame_grid, text="Livre ID (Col 8) :", font=("Segoe UI", 9)).grid(row=0, column=4, sticky="e", padx=(8, 4), pady=4)
    entree_book_id = tk.Entry(frame_grid, width=10, font=("Segoe UI", 9), relief=tk.SOLID, bd=1)
    entree_book_id.insert(0, donnees[8] if len(donnees) > 8 else "0")
    entree_book_id.grid(row=0, column=5, sticky="w", padx=4, pady=4)
    entree_book_id.bind("<KeyRelease>", lambda e, s=sid: on_skill_field_change(s))

    tk.Label(frame_grid, text="Slot (Col 9) :", font=("Segoe UI", 9)).grid(row=0, column=6, sticky="e", padx=(8, 4), pady=4)
    entree_slot = tk.Entry(frame_grid, width=6, font=("Segoe UI", 9), relief=tk.SOLID, bd=1)
    entree_slot.insert(0, donnees[9] if len(donnees) > 9 else "0")
    entree_slot.grid(row=0, column=7, sticky="w", padx=4, pady=4)
    entree_slot.bind("<KeyRelease>", lambda e, s=sid: on_skill_field_change(s))

    # Ligne 1 : Param / ID lié (Col 5), Fichier Skill 1 (Col 6), Fichier Skill 2 (Col 7)
    tk.Label(frame_grid, text="Param / ID lié (Col 5) :", font=("Segoe UI", 9)).grid(row=1, column=0, sticky="e", padx=(8, 4), pady=4)
    entree_col5 = tk.Entry(frame_grid, width=20, font=("Segoe UI", 9), relief=tk.SOLID, bd=1)
    entree_col5.insert(0, donnees[5] if len(donnees) > 5 else "0")
    entree_col5.grid(row=1, column=1, sticky="w", padx=4, pady=4)
    entree_col5.bind("<KeyRelease>", lambda e, s=sid: on_skill_field_change(s))

    tk.Label(frame_grid, text="Fichier 1 (Col 6) :", font=("Segoe UI", 9)).grid(row=1, column=2, sticky="e", padx=(8, 4), pady=4)
    entree_col6 = tk.Entry(frame_grid, width=22, font=("Segoe UI", 9), relief=tk.SOLID, bd=1)
    entree_col6.insert(0, donnees[6] if len(donnees) > 6 else "0")
    entree_col6.grid(row=1, column=3, sticky="w", padx=4, pady=4)
    entree_col6.bind("<KeyRelease>", lambda e, s=sid: on_skill_field_change(s))

    tk.Label(frame_grid, text="Fichier 2 (Col 7) :", font=("Segoe UI", 9)).grid(row=1, column=4, sticky="e", padx=(8, 4), pady=4)
    entree_col7 = tk.Entry(frame_grid, width=22, font=("Segoe UI", 9), relief=tk.SOLID, bd=1)
    entree_col7.insert(0, donnees[7] if len(donnees) > 7 else "0")
    entree_col7.grid(row=1, column=5, columnspan=3, sticky="w", padx=4, pady=4)
    entree_col7.bind("<KeyRelease>", lambda e, s=sid: on_skill_field_change(s))

    # Ligne 2 : Description (Col 2) + Bouton saut de ligne
    tk.Label(frame_grid, text="Description (Col 2) :", font=("Segoe UI", 9)).grid(row=2, column=0, sticky="e", padx=(8, 4), pady=4)
    sous_c_desc = tk.Frame(frame_grid)
    sous_c_desc.est_carte = True
    sous_c_desc.grid(row=2, column=1, columnspan=7, sticky="w", padx=4, pady=4)
    entree_desc = tk.Entry(sous_c_desc, width=68, font=("Segoe UI", 9), relief=tk.SOLID, bd=1)
    entree_desc.insert(0, assainir_texte_export(donnees[2]) if len(donnees) > 2 else "0")
    entree_desc.pack(side=tk.LEFT)
    entree_desc.bind("<KeyRelease>", lambda e, s=sid: on_skill_field_change(s))
    btn_ed = creer_bouton_saut_ligne(
        sous_c_desc,
        lambda e=entree_desc, s=sid: (ouvrir_editeur_saut_ligne(e, titre=f"Édition — Description Skill {s}", max_sauts_de_ligne=None, max_mots_secours=5), on_skill_field_change(s))
    )
    btn_ed.pack(side=tk.LEFT, padx=(4, 0))

    # Section Niveaux (1 à 5) — ywp_mst_youkai_bonus_effect_level (9 colonnes 0..8)
    frame_niv = tk.LabelFrame(card, text=f"  Niveaux du Skill {sid} (1 à 5)  ", font=("Segoe UI", 9, "bold"),
                              padx=8, pady=6, relief=tk.SOLID, bd=1, highlightthickness=1)
    frame_niv.est_carte = True
    frame_niv.pack(fill=tk.X, padx=4, pady=(4, 2))

    top_niv = tk.Frame(frame_niv)
    top_niv.est_carte = True
    top_niv.pack(fill=tk.X, pady=(0, 4))

    tk.Label(top_niv, text="Niveau affiché :", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(4, 6))
    var_nv = tk.StringVar(value="1")
    combo_nv = ttk.Combobox(top_niv, textvariable=var_nv, values=[str(i) for i in range(1, 6)], width=4, state="readonly")
    combo_nv.pack(side=tk.LEFT, padx=4)
    combo_nv.bind("<<ComboboxSelected>>", lambda e, s=sid: changer_niveau_skill(s))

    btn_dup_niv1 = tk.Button(top_niv, text="📋 Dupliquer Niv 1 sur 2 à 5", font=("Segoe UI", 8),
                             relief="flat", bd=1, command=lambda s=sid: dupliquer_niveau_1_vers_tous(s))
    btn_dup_niv1.pack(side=tk.RIGHT, padx=4)

    btn_grille_niv = tk.Button(top_niv, text="📝 Éditeur Groupé (Grille 1 à 5)", font=("Segoe UI", 8, "bold"),
                               relief="flat", bd=1, command=lambda s=sid: ouvrir_editeur_niveaux_bonus_groupe(s))
    btn_grille_niv.est_bouton_special = True
    btn_grille_niv.pack(side=tk.RIGHT, padx=4)

    grid_niv = tk.Frame(frame_niv)
    grid_niv.est_carte = True
    grid_niv.pack(fill=tk.X)

    cases_nv = {}

    # Ligne 0 de grid_niv : Description Niveau (Col 3) sur toute la largeur + bouton saut de ligne
    tk.Label(grid_niv, text="Description Niveau (Col 3) :", font=("Segoe UI", 9)).grid(row=0, column=0, sticky="e", padx=(8, 4), pady=3)
    sous_c_desc_nv = tk.Frame(grid_niv)
    sous_c_desc_nv.est_carte = True
    sous_c_desc_nv.grid(row=0, column=1, columnspan=3, sticky="w", padx=4, pady=3)
    e_desc_nv = tk.Entry(sous_c_desc_nv, width=64, font=("Segoe UI", 9), relief=tk.SOLID, bd=1)
    e_desc_nv.pack(side=tk.LEFT)
    e_desc_nv.bind("<KeyRelease>", lambda evt, s=sid: on_skill_level_change(s))
    btn_ed_nv = creer_bouton_saut_ligne(
        sous_c_desc_nv,
        lambda e=e_desc_nv, s=sid: (ouvrir_editeur_saut_ligne(e, titre=f"Édition — Description Niveau (Skill {s})", max_sauts_de_ligne=None, max_mots_secours=5), on_skill_level_change(s))
    )
    btn_ed_nv.pack(side=tk.LEFT, padx=(4, 0))
    cases_nv[3] = e_desc_nv

    # Lignes 1 et 2 : Valeur 1 (Col 4), Valeur 2 (Col 5), Valeur 3 (Col 6), Extra / Unk (Col 8)
    champs_niveaux_num = [
        ("Valeur 1 / Effet (Col 4)", 4),
        ("Valeur 2 (Col 5)", 5),
        ("Valeur 3 (Col 6)", 6),
        ("Extra / Unk (Col 8)", 8),
    ]
    for i, (libelle, idx) in enumerate(champs_niveaux_num):
        r, c = 1 + (i // 2), (i % 2) * 2
        tk.Label(grid_niv, text=libelle + " :", font=("Segoe UI", 9)).grid(row=r, column=c, sticky="e", padx=(8, 4), pady=3)
        e = tk.Entry(grid_niv, width=28, font=("Segoe UI", 9), relief=tk.SOLID, bd=1)
        e.grid(row=r, column=c+1, padx=4, pady=3, sticky="w")
        e.bind("<KeyRelease>", lambda evt, s=sid: on_skill_level_change(s))
        cases_nv[idx] = e

    # Ligne 3 de grid_niv : Paramètres / Config Clé:Valeur (Col 7) sur toute la largeur (ex: radius:25, prob1:7500,size1:1...)
    tk.Label(grid_niv, text="Paramètres / Config (Col 7) :", font=("Segoe UI", 9, "bold")).grid(row=3, column=0, sticky="e", padx=(8, 4), pady=3)
    e_cfg_nv = tk.Entry(grid_niv, width=68, font=("Segoe UI", 9), relief=tk.SOLID, bd=1)
    e_cfg_nv.grid(row=3, column=1, columnspan=3, padx=4, pady=3, sticky="w")
    e_cfg_nv.bind("<KeyRelease>", lambda evt, s=sid: on_skill_level_change(s))
    cases_nv[7] = e_cfg_nv

    cartes_bonus_ui[sid] = {
        "cadre": card,
        "combo_type": combo_type,
        "entree_desc": entree_desc,
        "entree_res": entree_res,
        "entree_col5": entree_col5,
        "entree_col6": entree_col6,
        "entree_col7": entree_col7,
        "entree_book_id": entree_book_id,
        "entree_slot": entree_slot,
        "var_niveau": var_nv,
        "niveau_precedent": "1",
        "combo_niveau": combo_nv,
        "cases_niveau": cases_nv
    }

    if sid == "1":
        cases_bonus["Description"] = entree_desc
        cases_bonus["Ressource"] = entree_res
        cases_bonus["Col5"] = entree_col5
        cases_bonus["Col6"] = entree_col6
        cases_bonus["Col7"] = entree_col7
        cases_bonus["LivreID"] = entree_book_id
        cases_bonus["Slot"] = entree_slot
        for idx, e_box in cases_nv.items():
            cases_bonus_niveau[idx] = e_box
        subid_bonus_var.set("1")
        combo_bonus_type.set(combo_type.get())
        niveau_bonus_actuel_var.set("1")

    charger_donnees_niveau_dans_ui(sid, yokai_id, "1")

def recharger_donnees_carte_skill(sid, yokai_id):
    if sid not in cartes_bonus_ui: return
    ui = cartes_bonus_ui[sid]
    cle = (yokai_id, sid)
    donnees = _normaliser_ligne_bonus_effect(
        dictionnaire_bonus_effect.get(cle, [yokai_id, sid, "0", "1", "0", "0", "0", "0", "0", "0"]),
        yokai_id, sid
    )

    type_id = donnees[3] if len(donnees) > 3 and donnees[3] else "1"
    ui["combo_type"].set(f"{type_id} - {YW_BONUS_EFFECTS.get(type_id, 'Inconnu')}")
    ui["entree_res"].delete(0, tk.END)
    ui["entree_res"].insert(0, donnees[4] if len(donnees) > 4 else "0")
    ui["entree_desc"].delete(0, tk.END)
    ui["entree_desc"].insert(0, assainir_texte_export(donnees[2]) if len(donnees) > 2 else "0")

    for k_ui, col_i in (("entree_col5", 5), ("entree_col6", 6), ("entree_col7", 7), ("entree_book_id", 8), ("entree_slot", 9)):
        if ui.get(k_ui):
            ui[k_ui].delete(0, tk.END)
            ui[k_ui].insert(0, donnees[col_i] if len(donnees) > col_i else "0")

    ui["var_niveau"].set("1")
    ui["niveau_precedent"] = "1"
    charger_donnees_niveau_dans_ui(sid, yokai_id, "1")

def charger_donnees_niveau_dans_ui(sid, yokai_id, niveau):
    if sid not in cartes_bonus_ui: return
    ui = cartes_bonus_ui[sid]
    cle = (yokai_id, sid)
    donnees_brutes = dictionnaire_bonus_effect_level.get(cle, {}).get(str(niveau), [yokai_id, sid, str(niveau), "0", "0", "0", "0", "", ""])
    donnees_niveau = _normaliser_ligne_bonus_level(donnees_brutes, yokai_id, sid, niveau)
    for idx, case in ui["cases_niveau"].items():
        case.delete(0, tk.END)
        if idx < len(donnees_niveau):
            val = assainir_texte_export(donnees_niveau[idx]) if idx == 3 else donnees_niveau[idx]
            case.insert(0, val)

def _extraire_ligne_niveau_depuis_ui(ui, yokai_id, sid, niveau):
    cle = (yokai_id, sid)
    existante = dictionnaire_bonus_effect_level.get(cle, {}).get(str(niveau), [yokai_id, sid, str(niveau), "0", "0", "0", "0", "", ""])
    lvl_line = _normaliser_ligne_bonus_level(existante, yokai_id, sid, niveau)
    for idx, case in ui["cases_niveau"].items():
        val = assainir_texte_export(case.get().strip())
        if idx < len(lvl_line):
            if idx in (3, 4, 5, 6):
                lvl_line[idx] = val if val != "" else "0"
            else:
                lvl_line[idx] = val
    return lvl_line

def changer_niveau_skill(sid):
    if sid not in cartes_bonus_ui: return
    ui = cartes_bonus_ui[sid]
    yokai_id = cases_entrees[0].get().strip() if cases_entrees else ""
    if not yokai_id: return
    cle = (yokai_id, sid)
    if cle not in dictionnaire_bonus_effect_level: dictionnaire_bonus_effect_level[cle] = {}

    nv_prec = ui["niveau_precedent"]
    dictionnaire_bonus_effect_level[cle][nv_prec] = _extraire_ligne_niveau_depuis_ui(ui, yokai_id, sid, nv_prec)

    nv_choisi = ui["var_niveau"].get()
    charger_donnees_niveau_dans_ui(sid, yokai_id, nv_choisi)
    ui["niveau_precedent"] = nv_choisi
    actualiser_affichage_mst_bonus()

def dupliquer_niveau_1_vers_tous(sid):
    if sid not in cartes_bonus_ui: return
    ui = cartes_bonus_ui[sid]
    yokai_id = cases_entrees[0].get().strip() if cases_entrees else ""
    if not yokai_id: return
    cle = (yokai_id, sid)

    nv_actuel = ui["var_niveau"].get()
    lvl_line = _extraire_ligne_niveau_depuis_ui(ui, yokai_id, sid, nv_actuel)
    dictionnaire_bonus_effect_level.setdefault(cle, {})[nv_actuel] = lvl_line

    base_line = _normaliser_ligne_bonus_level(dictionnaire_bonus_effect_level[cle].get("1", lvl_line), yokai_id, sid, "1")
    for lvl in range(2, 6):
        dictionnaire_bonus_effect_level[cle][str(lvl)] = _normaliser_ligne_bonus_level(base_line, yokai_id, sid, str(lvl))
    messagebox.showinfo("Duplication Niveaux", f"Les valeurs du Niveau 1 du Skill {sid} ont été appliquées aux niveaux 2 à 5 !")
    actualiser_affichage_mst_bonus()

def ouvrir_editeur_niveaux_bonus_groupe(sid):
    """Éditeur en grille pour modifier simultanément les 5 niveaux (colonnes 3 à 8) d'un Skill Bonus Effect."""
    if sid not in cartes_bonus_ui: return
    yokai_id = cases_entrees[0].get().strip() if cases_entrees else ""
    if not yokai_id:
        messagebox.showwarning("Niveau Skill", "Veuillez d'abord charger ou définir un Yo-kai.")
        return

    enregistrer_skill_ui_en_memoire(sid, yokai_id)
    cle = (yokai_id, sid)
    p = THEMES.get(THEME_ACTIF, THEMES["Mode Sakura"])

    fen_b = tk.Toplevel(fenetre)
    fen_b.title(f"Éditeur groupé des niveaux — Skill {sid} (Yo-kai {yokai_id})")
    fen_b.geometry("1120x360")
    fen_b.configure(bg=p["bg_main"])
    fen_b.transient(fenetre)

    colonnes_grille = [
        ("Description (Col 3)", 3, 28),
        ("Valeur 1 (Col 4)", 4, 12),
        ("Valeur 2 (Col 5)", 5, 12),
        ("Valeur 3 (Col 6)", 6, 10),
        ("Paramètres / Config (Col 7)", 7, 36),
        ("Extra / Unk (Col 8)", 8, 10),
    ]

    table = tk.Frame(fen_b, bg=p["bg_main"])
    table.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    tk.Label(table, text="Niveau", font=("Segoe UI", 9, "bold"), bg=p["bg_main"], fg=p["accent"]).grid(row=0, column=0, padx=4, pady=4)
    for col_i, (nom_col, _, _) in enumerate(colonnes_grille, 1):
        tk.Label(table, text=nom_col, font=("Segoe UI", 9, "bold"), bg=p["bg_main"], fg=p["text_main"]).grid(row=0, column=col_i, padx=4, pady=4)

    cellules = {}
    for niveau in range(1, 6):
        tk.Label(table, text=str(niveau), font=("Segoe UI", 9, "bold"), bg=p["bg_main"], fg=p["accent"]).grid(row=niveau, column=0, padx=4, pady=4)
        donnees = _normaliser_ligne_bonus_level(
            dictionnaire_bonus_effect_level.get(cle, {}).get(str(niveau), [yokai_id, sid, str(niveau), "0", "0", "0", "0", "", ""]),
            yokai_id, sid, niveau
        )
        for col_i, (_, idx_col, larg) in enumerate(colonnes_grille, 1):
            e = tk.Entry(table, width=larg, font=("Segoe UI", 9), relief=tk.SOLID, bd=1,
                         bg=p["entry_bg"], fg=p["entry_fg"], insertbackground=p["accent"])
            val = assainir_texte_export(donnees[idx_col]) if idx_col == 3 else donnees[idx_col]
            e.insert(0, val)
            e.grid(row=niveau, column=col_i, padx=3, pady=4)
            cellules[(niveau, idx_col)] = e

    def enregistrer_grille():
        dictionnaire_bonus_effect_level.setdefault(cle, {})
        for niveau in range(1, 6):
            ligne = _normaliser_ligne_bonus_level(
                dictionnaire_bonus_effect_level[cle].get(str(niveau), [yokai_id, sid, str(niveau), "0", "0", "0", "0", "", ""]),
                yokai_id, sid, niveau
            )
            for _, idx_col, _ in colonnes_grille:
                v = assainir_texte_export(cellules[(niveau, idx_col)].get().strip())
                if idx_col in (3, 4, 5, 6):
                    ligne[idx_col] = v if v != "" else "0"
                else:
                    ligne[idx_col] = v
            dictionnaire_bonus_effect_level[cle][str(niveau)] = ligne

        nv_act = cartes_bonus_ui[sid]["var_niveau"].get()
        charger_donnees_niveau_dans_ui(sid, yokai_id, nv_act)
        actualiser_affichage_mst_bonus()
        fen_b.destroy()

    bas = tk.Frame(fen_b, bg=p["bg_main"])
    bas.pack(fill=tk.X, padx=10, pady=8)
    tk.Button(bas, text="Enregistrer", font=("Segoe UI", 9, "bold"),
              bg=p["btn_special_bg"], fg=p["btn_special_fg"], relief="flat", bd=1, command=enregistrer_grille).pack(side=tk.RIGHT, padx=6)
    tk.Button(bas, text="Fermer", font=("Segoe UI", 9),
              bg=p["btn_bg"], fg=p["btn_fg"], relief="flat", bd=1, command=fen_b.destroy).pack(side=tk.RIGHT, padx=6)

def enregistrer_skill_ui_en_memoire(sid, yokai_id=None):
    if sid not in cartes_bonus_ui: return
    if not yokai_id:
        yokai_id = cases_entrees[0].get().strip() if cases_entrees else ""
    if not yokai_id: return

    ui = cartes_bonus_ui[sid]
    cle = (yokai_id, sid)
    type_id = ui["combo_type"].get().split(" - ")[0] if " - " in ui["combo_type"].get() else (ui["combo_type"].get().strip() or "1")
    desc = assainir_texte_export(ui["entree_desc"].get().strip()) or "0"
    res = assainir_texte_export(ui["entree_res"].get().strip()) or "0"
    col5 = assainir_texte_export(ui["entree_col5"].get().strip()) if ui.get("entree_col5") else "0"
    col6 = assainir_texte_export(ui["entree_col6"].get().strip()) if ui.get("entree_col6") else "0"
    col7 = assainir_texte_export(ui["entree_col7"].get().strip()) if ui.get("entree_col7") else "0"
    book_id = assainir_texte_export(ui["entree_book_id"].get().strip()) if ui.get("entree_book_id") else "0"
    slot = assainir_texte_export(ui["entree_slot"].get().strip()) if ui.get("entree_slot") else "0"

    base_line = _normaliser_ligne_bonus_effect(
        dictionnaire_bonus_effect.get(cle, [yokai_id, sid, desc, type_id, res, "0", "0", "0", "0", "0"]),
        yokai_id, sid
    )
    base_line[0] = yokai_id
    base_line[1] = sid
    base_line[2] = desc
    base_line[3] = type_id
    base_line[4] = res or "0"
    base_line[5] = col5 or "0"
    base_line[6] = col6 or "0"
    base_line[7] = col7 or "0"
    base_line[8] = book_id or "0"
    base_line[9] = slot or "0"
    dictionnaire_bonus_effect[cle] = base_line

    nv_actuel = ui["var_niveau"].get()
    if cle not in dictionnaire_bonus_effect_level: dictionnaire_bonus_effect_level[cle] = {}
    dictionnaire_bonus_effect_level[cle][nv_actuel] = _extraire_ligne_niveau_depuis_ui(ui, yokai_id, sid, nv_actuel)

def enregistrer_tous_les_skills_ui(yokai_id=None):
    if not yokai_id:
        yokai_id = cases_entrees[0].get().strip() if cases_entrees else ""
    if not yokai_id: return
    for sid in list(cartes_bonus_ui.keys()):
        enregistrer_skill_ui_en_memoire(sid, yokai_id)
        cle = (yokai_id, sid)
        if cle in dictionnaire_bonus_effect_level:
            base_lvl = _normaliser_ligne_bonus_level(
                dictionnaire_bonus_effect_level[cle].get("1", [yokai_id, sid, "1", "0", "0", "0", "0", "", ""]),
                yokai_id, sid, "1"
            )
            for lvl in range(1, 6):
                lvl_str = str(lvl)
                if lvl_str not in dictionnaire_bonus_effect_level[cle]:
                    dictionnaire_bonus_effect_level[cle][lvl_str] = _normaliser_ligne_bonus_level(base_lvl, yokai_id, sid, lvl_str)
                else:
                    dictionnaire_bonus_effect_level[cle][lvl_str] = _normaliser_ligne_bonus_level(
                        dictionnaire_bonus_effect_level[cle][lvl_str], yokai_id, sid, lvl_str
                    )

def on_skill_field_change(sid):
    yokai_id = cases_entrees[0].get().strip() if cases_entrees else ""
    if yokai_id:
        enregistrer_skill_ui_en_memoire(sid, yokai_id)
        actualiser_affichage_mst_bonus()

def on_skill_level_change(sid):
    yokai_id = cases_entrees[0].get().strip() if cases_entrees else ""
    if yokai_id:
        enregistrer_skill_ui_en_memoire(sid, yokai_id)
        actualiser_affichage_mst_bonus()

def ajouter_nouveau_skill(target_sid=None):
    yokai_id = cases_entrees[0].get().strip() if cases_entrees else ""
    if not yokai_id: return messagebox.showerror("Erreur", "Veuillez d'abord définir un YoukaiId.")
    activer_bonus_effect_var.set(True)
    sub_cadre_bonus.pack(fill=tk.X, expand=True)

    sids_actifs = [int(s) for s in cartes_bonus_ui.keys() if s.isdigit()]
    if target_sid:
        sid_str = str(target_sid)
    else:
        sid_str = str(max(sids_actifs, default=0) + 1)

    cle = (yokai_id, sid_str)
    if cle not in dictionnaire_bonus_effect:
        def_type = "13" if sid_str in ("2", "3") else "1"
        dictionnaire_bonus_effect[cle] = [yokai_id, sid_str, f"Description du Skill {sid_str}", def_type, "0", "0", "0", "0", "0", "0"]

    if cle not in dictionnaire_bonus_effect_level:
        dictionnaire_bonus_effect_level[cle] = {}
        for lvl in range(1, 6):
            dictionnaire_bonus_effect_level[cle][str(lvl)] = [yokai_id, sid_str, str(lvl), f"Niveau {lvl}", "0", "0", "0", "", ""]

    creer_carte_skill(sid_str, yokai_id)
    maj_boutons_ajout_skill()
    actualiser_affichage_mst_bonus()
    appliquer_theme_global(THEME_ACTIF)

def supprimer_skill(sid):
    yokai_id = cases_entrees[0].get().strip() if cases_entrees else ""
    if not yokai_id: return
    if not messagebox.askyesno("Confirmation", f"Supprimer le Skill (SubID {sid}) pour ce Yo-kai ?"):
        return
    cle = (yokai_id, sid)
    dictionnaire_bonus_effect.pop(cle, None)
    dictionnaire_bonus_effect_level.pop(cle, None)
    if sid in cartes_bonus_ui:
        cartes_bonus_ui[sid]["cadre"].destroy()
        del cartes_bonus_ui[sid]
    maj_boutons_ajout_skill()
    actualiser_affichage_mst_bonus()

def maj_boutons_ajout_skill():
    sids = set(cartes_bonus_ui.keys())
    if "1" not in sids:
        btn_ajouter_skill2.pack_forget()
        btn_ajouter_skill3.pack_forget()
        btn_ajouter_skill_autre.pack(side=tk.LEFT, padx=6)
        btn_ajouter_skill_autre.config(text="➕ Ajouter Skill 1")
    elif "2" not in sids:
        btn_ajouter_skill2.pack(side=tk.LEFT, padx=(0, 6))
        btn_ajouter_skill3.pack_forget()
        btn_ajouter_skill_autre.pack_forget()
    elif "3" not in sids:
        btn_ajouter_skill2.pack_forget()
        btn_ajouter_skill3.pack(side=tk.LEFT, padx=(0, 6))
        btn_ajouter_skill_autre.pack_forget()
    else:
        btn_ajouter_skill2.pack_forget()
        btn_ajouter_skill3.pack_forget()
        btn_ajouter_skill_autre.pack(side=tk.LEFT, padx=6)
        btn_ajouter_skill_autre.config(text="➕ Ajouter un autre Skill (SubID suivant)")

def actualiser_affichage_mst_bonus():
    if 'txt_mst_preview' not in globals(): return
    yokai_id = cases_entrees[0].get().strip() if cases_entrees else ""
    if not yokai_id or not (activer_bonus_effect_var and activer_bonus_effect_var.get()):
        txt_mst_preview.config(state="normal")
        txt_mst_preview.delete("1.0", tk.END)
        txt_mst_preview.insert(tk.END, "(Aucun effet bonus actif pour ce Yo-kai)")
        txt_mst_preview.config(state="disabled")
        if 'lbl_mst_info' in globals(): lbl_mst_info.config(text="0 Skill actif")
        return

    enregistrer_tous_les_skills_ui(yokai_id)

    lignes_be = [
        _normaliser_ligne_bonus_effect(dictionnaire_bonus_effect[(yid, sid)], yokai_id, sid)
        for (yid, sid) in sorted(dictionnaire_bonus_effect.keys(), key=lambda x: (x[0], int(x[1]) if x[1].isdigit() else x[1]))
        if yid == yokai_id and sid in cartes_bonus_ui
    ]
    lignes_lvl = []
    for (yid, sid) in sorted(dictionnaire_bonus_effect_level.keys(), key=lambda x: (x[0], int(x[1]) if x[1].isdigit() else x[1])):
        if yid == yokai_id and sid in cartes_bonus_ui:
            niveaux = dictionnaire_bonus_effect_level[(yid, sid)]
            for lvl in sorted(niveaux.keys(), key=lambda n: int(n) if n.isdigit() else n):
                data = _normaliser_ligne_bonus_level(niveaux[lvl], yokai_id, sid, str(lvl))
                lignes_lvl.append(data)

    txt_mst_preview.config(state="normal")
    txt_mst_preview.delete("1.0", tk.END)

    output = []
    output.append(f"=== ywp_mst_youkai_bonus_effect ({len(lignes_be)} ligne(s)) ===")
    for row in lignes_be:
        output.append("|".join(str(c) for c in row))
    output.append("")
    output.append(f"=== ywp_mst_youkai_bonus_effect_level ({len(lignes_lvl)} ligne(s)) ===")
    for row in lignes_lvl:
        output.append("|".join(str(c) for c in row))

    txt_mst_preview.insert(tk.END, "\n".join(output))
    txt_mst_preview.config(state="disabled")
    if 'lbl_mst_info' in globals():
        lbl_mst_info.config(text=f"✨ {len(lignes_be)} Skill(s) actif(s)  •  {len(lignes_be)} ligne(s) Bonus Effect  •  {len(lignes_lvl)} ligne(s) Niveaux")

def copier_lignes_mst_presse_papier():
    txt = txt_mst_preview.get("1.0", tk.END).strip()
    fenetre.clipboard_clear()
    fenetre.clipboard_append(txt)
    messagebox.showinfo("Copié", "Lignes MST copiées dans le presse-papier !")

# Fonctions de compatibilité pour les appels existants
def afficher_donnees_bonus_effect(event=None, depuis_code=False):
    yokai_id = cases_entrees[0].get().strip() if cases_entrees else ""
    if yokai_id: charger_bonus_effet_pour_yokai(yokai_id)

def afficher_donnees_bonus_niveau(event=None, depuis_code=False):
    enregistrer_tous_les_skills_ui()


# ==========================================
# SAUVEGARDE ET CHARGEMENT MODS
# ==========================================
def ouvrir_menu_sauvegarde():
    p = THEMES.get(THEME_ACTIF, THEMES["Mode Sakura"])
    yokai_id = cases_entrees[0].get().strip() if cases_entrees else ""
    if not yokai_id:
        messagebox.showerror("Erreur", "Veuillez d'abord définir un YoukaiId (champ 0).")
        return

    if yokai_id not in dictionnaire_skill_levels: dictionnaire_skill_levels[yokai_id] = {}
    cols_lvl = [""] * 13
    cols_lvl[0], cols_lvl[1] = yokai_id, niveau_actuel_var.get()
    for idx, case in cases_skill_levels.items(): cols_lvl[idx] = assainir_texte_export(case.get())
    dictionnaire_skill_levels[yokai_id][niveau_actuel_var.get()] = cols_lvl

    fen_menu = tk.Toplevel(fenetre)
    fen_menu.title("Options de sauvegarde")
    fen_menu.geometry("420x250")
    fen_menu.configure(bg=p["bg_main"])
    tk.Label(fen_menu, text=f"Sauvegarder les données du Yo-kai {yokai_id}", font=("Segoe UI", 11, "bold"), bg=p["bg_main"], fg=p["accent"]).pack(pady=12)
    tk.Button(fen_menu, text="💾 Écraser dans les index originaux (avec backup auto)", font=("Segoe UI", 9, "bold"),
              bg=p["btn_special_bg"], fg=p["btn_special_fg"], relief="flat", bd=1,
              command=lambda: executer_sauvegarde(yokai_id, "original", fen_menu)).pack(fill=tk.X, padx=24, pady=4)
    tk.Button(fen_menu, text="📁 Exporter en Mod isolé", font=("Segoe UI", 9, "bold"),
              bg=p["btn_bg"], fg=p["accent"], relief="flat", bd=1,
              command=lambda: executer_sauvegarde(yokai_id, "isole", fen_menu)).pack(fill=tk.X, padx=24, pady=4)
    tk.Button(fen_menu, text="📦 Dump Yo-kai (tous les fichiers gamefiles)", font=("Segoe UI", 9, "bold"),
              bg=p["btn_bg"], fg=p["accent"], relief="flat", bd=1,
              command=lambda: dump_yokai(fen_menu)).pack(fill=tk.X, padx=24, pady=4)
    tk.Button(fen_menu, text="🗑️ Supprimer ce Yo-kai (index originaux)", font=("Segoe UI", 9, "bold"),
              bg=p["btn_bg"], fg="#c0392b", relief="flat", bd=1,
              command=lambda: supprimer_yokai_entier(yokai_id, fen_menu)).pack(fill=tk.X, padx=24, pady=(12, 4))

def supprimer_yokai_entier(yokai_id, fen_menu):
    if not messagebox.askyesno(
        "Confirmation de suppression",
        f"Supprimer DÉFINITIVEMENT le Yo-kai {yokai_id} des index originaux ?\n\n"
        "Seront retirés : données de base, skills et niveaux, strong skill et bonus effects.\n\n"
        "Une sauvegarde automatique (.bak) sera créée avant suppression.",
        icon="warning"
    ):
        return

    fen_menu.destroy()

    try:
        maj_fichier_original(FICHIER_DB, [], yokai_id, insertion_par_dictionary_id=True, avec_backup=True)
        maj_fichier_original(FICHIER_SKILL_DB, [], yokai_id, avec_backup=True)
        maj_fichier_original(FICHIER_SKILL_LEVEL_DB, [], yokai_id, avec_backup=True)

        if FICHIER_STRONG_SKILL_DB:
            maj_fichier_original(FICHIER_STRONG_SKILL_DB, [], yokai_id, avec_backup=True)
        if FICHIER_STRONG_SKILL_LEVEL_DB:
            maj_fichier_original(FICHIER_STRONG_SKILL_LEVEL_DB, [], yokai_id, avec_backup=True)
        if FICHIER_BONUS_EFFECT_DB:
            maj_fichier_original(FICHIER_BONUS_EFFECT_DB, [], yokai_id, avec_backup=True)
        if FICHIER_BONUS_EFFECT_LEVEL_DB:
            maj_fichier_original(FICHIER_BONUS_EFFECT_LEVEL_DB, [], yokai_id, avec_backup=True)

        dictionnaire_skill_levels.pop(yokai_id, None)
        dictionnaire_skills.pop(yokai_id, None)
        dictionnaire_strong_skills.pop(yokai_id, None)
        dictionnaire_strong_skill_levels.pop(yokai_id, None)
        for cle in [k for k in dictionnaire_bonus_effect if k[0] == yokai_id]:
            dictionnaire_bonus_effect.pop(cle, None)
        for cle in [k for k in dictionnaire_bonus_effect_level if k[0] == yokai_id]:
            dictionnaire_bonus_effect_level.pop(cle, None)

        charger_fichier()
        charger_skills()
        charger_skill_levels()
        charger_strong_skills()
        charger_strong_skill_levels()
        charger_bonus_effects()
        charger_bonus_effect_levels()

        vider_interface()
        messagebox.showinfo("Suppression réussie", f"Le Yo-kai {yokai_id} a été supprimé des index originaux.")
    except Exception as e:
        messagebox.showerror("Erreur de suppression", str(e))

def executer_sauvegarde(yokai_id, mode, fen_menu):
    fen_menu.destroy()
    
    valeurs_yokai = [assainir_texte_export(case.get()) for case in cases_entrees]
    while len(valeurs_yokai) < len(CHAMPS_YOKAI): valeurs_yokai.append("")
    while len(valeurs_yokai) > len(CHAMPS_YOKAI): valeurs_yokai.pop()
    
    ligne_yokai = "|".join(valeurs_yokai)
    type_id = combo_soult_type.get().split(" - ")[0] if " - " in combo_soult_type.get() else "-1"
    
    champs_skill_liste = [
        yokai_id,
        assainir_texte_export(cases_skills["Nom"].get()),
        type_id,
        assainir_texte_export(cases_skills["Description"].get()),
        cases_skills["Propriete1"].get() or "0",
        cases_skills["Propriete2"].get() or "0",
        cases_skills["Anim3D"].get(),
        cases_skills["Anim2D"].get(),
        cases_skills["Anim2D_2"].get(),
        cases_skills["SkillUnk0"].get() or "0",
        cases_skills["SkillUnk1"].get() or "0",
        cases_skills["SkillUnk2"].get() or "0",
        cases_skills["SkillUnk3"].get() or "0",
        cases_skills["SkillUnk4"].get(),
    ]
    ligne_skill = "|".join(champs_skill_liste)
    
    lignes_levels = []
    base_lvl_data = dictionnaire_skill_levels.get(yokai_id, {}).get(niveau_actuel_var.get(), [""]*13)

    niveaux_manquants = [
        str(lvl) for lvl in range(1, 8)
        if str(lvl) not in dictionnaire_skill_levels.get(yokai_id, {})
    ]
    if niveaux_manquants:
        if not messagebox.askyesno(
            "Confirmation",
            f"Les niveaux {', '.join(niveaux_manquants)} de l'Âmultime n'ont pas encore "
            f"leurs propres données.\nVoulez-vous les baser sur le niveau "
            f"{niveau_actuel_var.get()} actuellement affiché ?"
        ):
            return

    for lvl in range(1, 8):
        data = dictionnaire_skill_levels.get(yokai_id, {}).get(str(lvl), list(base_lvl_data))
        data[1] = str(lvl)
        while len(data) < 13: data.append("")
        data[0] = yokai_id
        lignes_levels.append("|".join(assainir_texte_export(d) for d in data))

    bonus_actif = activer_bonus_effect_var.get() if activer_bonus_effect_var is not None else False
    lignes_bonus_effect = []
    lignes_bonus_effect_level = []

    if bonus_actif:
        enregistrer_tous_les_skills_ui(yokai_id)
        lignes_bonus_effect = ["|".join(assainir_texte_export(c) for c in _normaliser_ligne_bonus_effect(v, yokai_id, sid))
                               for (yid, sid), v in sorted(dictionnaire_bonus_effect.items(), key=lambda x: (x[0][0], int(x[0][1]) if x[0][1].isdigit() else x[0][1]))
                               if yid == yokai_id and sid in cartes_bonus_ui]
        for (yid, sid), niveaux in sorted(dictionnaire_bonus_effect_level.items(), key=lambda x: (x[0][0], int(x[0][1]) if x[0][1].isdigit() else x[0][1])):
            if yid != yokai_id or sid not in cartes_bonus_ui: continue
            for niveau in sorted(niveaux.keys(), key=lambda n: int(n) if n.isdigit() else n):
                data = _normaliser_ligne_bonus_level(niveaux[niveau], yokai_id, sid, str(niveau))
                lignes_bonus_effect_level.append("|".join(assainir_texte_export(d) for d in data))

    if mode == "isole":
        dossier_parent = filedialog.askdirectory(title="Choisir le dossier de destination")
        if not dossier_parent: return
        chemin_mod = os.path.join(dossier_parent, f"Yokai_{yokai_id}")
        os.makedirs(chemin_mod, exist_ok=True)
        try:
            fichiers_a_ecrire = [
                ("ywp_mst_youkai.json", ligne_yokai),
                ("ywp_mst_youkai_skill.json", ligne_skill),
                ("ywp_mst_youkai_skill_level.json", "*".join(lignes_levels))
            ]
            if bonus_actif and lignes_bonus_effect:
                fichiers_a_ecrire.append(("ywp_mst_youkai_bonus_effect.json", "*".join(lignes_bonus_effect)))
            if bonus_actif and lignes_bonus_effect_level:
                fichiers_a_ecrire.append(("ywp_mst_youkai_bonus_effect_level.json", "*".join(lignes_bonus_effect_level)))
                
            for nom, data in fichiers_a_ecrire:
                data = normaliser_sauts_ligne(data)
                with open(os.path.join(chemin_mod, nom), "w", encoding="utf-8") as f:
                    json.dump({"tableData": data, "version": "1"}, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("Succès", f"Dossier Mod créé dans :\n{chemin_mod}")
        except Exception as e:
            messagebox.showerror("Erreur Mod", str(e))
            
    elif mode == "original":
        try:
            maj_fichier_original(FICHIER_DB, ligne_yokai, yokai_id, insertion_par_dictionary_id=True, avec_backup=True)
            maj_fichier_original(FICHIER_SKILL_DB, ligne_skill, yokai_id, avec_backup=True)
            maj_fichier_original(FICHIER_SKILL_LEVEL_DB, lignes_levels, yokai_id, avec_backup=True)
            
            if FICHIER_BONUS_EFFECT_DB:
                maj_fichier_original(FICHIER_BONUS_EFFECT_DB, lignes_bonus_effect if bonus_actif else [], yokai_id, avec_backup=True)
            if FICHIER_BONUS_EFFECT_LEVEL_DB:
                maj_fichier_original(FICHIER_BONUS_EFFECT_LEVEL_DB, lignes_bonus_effect_level if bonus_actif else [], yokai_id, avec_backup=True)
            
            charger_fichier()
            charger_skills()
            charger_skill_levels()
            charger_bonus_effects()
            charger_bonus_effect_levels()
            messagebox.showinfo("Succès", f"Index d'origine mis à jour pour l'ID {yokai_id} !\n(Sauvegarde .bak créée dans 'backups/')")
        except Exception as e:
            messagebox.showerror("Erreur DB Originale", str(e))
          
def sauvegarder_skill_sous():
    if index_trouve == -1: return messagebox.showerror("Erreur", "Aucun Yo-kai chargé !")
    soult_id = cases_entrees[0].get()
    type_id = combo_soult_type.get().split(" - ")[0] if " - " in combo_soult_type.get() else "-1"
    
    nouvelle_ligne = "|".join([
        soult_id,
        assainir_texte_export(cases_skills["Nom"].get()),
        type_id,
        assainir_texte_export(cases_skills["Description"].get()),
        cases_skills["Propriete1"].get() or "0",
        cases_skills["Propriete2"].get() or "0",
        cases_skills["Anim3D"].get(),
        cases_skills["Anim2D"].get(),
        cases_skills["Anim2D_2"].get(),
        cases_skills["SkillUnk0"].get() or "0",
        cases_skills["SkillUnk1"].get() or "0",
        cases_skills["SkillUnk2"].get() or "0",
        cases_skills["SkillUnk3"].get() or "0",
        cases_skills["SkillUnk4"].get(),
    ])
    
    chemin_sauvegarde = filedialog.asksaveasfilename(
        title="Enregistrer l'Âmultime sous...",
        defaultextension=".json",
        filetypes=[("Fichier JSON", "*.json"), ("Fichier Texte", "*.txt")]
    )
    if not chemin_sauvegarde: return
    try:
        maj_fichier_original(chemin_sauvegarde if os.path.exists(chemin_sauvegarde) else FICHIER_SKILL_DB, nouvelle_ligne, soult_id, avec_backup=True)
        messagebox.showinfo("Succès", "Âmultime enregistrée avec succès !")
    except Exception as e:
        messagebox.showerror("Erreur de sauvegarde", str(e))

def charger_dossier_mod():
    global index_trouve, niveau_precedent
    dossier_mod = filedialog.askdirectory(title="Sélectionner le dossier du Mod")
    if not dossier_mod: return
    
    f_youkai = trouver_fichier("ywp_mst_youkai", dossier_mod)
    f_skill = trouver_fichier("ywp_mst_youkai_skill", dossier_mod)
    f_level = trouver_fichier("ywp_mst_youkai_skill_level", dossier_mod)
    f_be = trouver_fichier("ywp_mst_youkai_bonus_effect", dossier_mod)
    f_bel = trouver_fichier("ywp_mst_youkai_bonus_effect_level", dossier_mod)
    
    if not f_youkai:
        return messagebox.showerror("Erreur Mod", "Fichier ywp_mst_youkai introuvable dans ce dossier.")
        
    texte_yokai, _, _ = lire_donnees_fichier(f_youkai)
    if not texte_yokai: return messagebox.showerror("Erreur Mod", "Fichier Yo-kai vide ou illisible.")
    
    colonnes = texte_yokai.split('*')[0].split('|')
    yokai_id = colonnes[0]
    
    if f_skill:
        t_sk, _, _ = lire_donnees_fichier(f_skill)
        if t_sk:
            cols_sk = t_sk.split('*')[0].split('|')
            if len(cols_sk) >= 4:
                dictionnaire_skills[yokai_id] = {
                    "Nom": cols_sk[1], "TypeID": cols_sk[2], "Description": cols_sk[3],
                    "Propriete1": cols_sk[4] if len(cols_sk) > 4 else "0",
                    "Propriete2": cols_sk[5] if len(cols_sk) > 5 else "0",
                    "Anim3D": cols_sk[6] if len(cols_sk) > 6 else "",
                    "Anim2D": cols_sk[7] if len(cols_sk) > 7 else "",
                    "Anim2D_2": cols_sk[8] if len(cols_sk) > 8 else "",
                    "SkillUnk0": cols_sk[9] if len(cols_sk) > 9 else "0",
                    "SkillUnk1": cols_sk[10] if len(cols_sk) > 10 else "0",
                    "SkillUnk2": cols_sk[11] if len(cols_sk) > 11 else "0",
                    "SkillUnk3": cols_sk[12] if len(cols_sk) > 12 else "0",
                    "SkillUnk4": cols_sk[13] if len(cols_sk) > 13 else "",
                }
                
    if f_level:
        t_lvl, _, _ = lire_donnees_fichier(f_level)
        if t_lvl:
            if yokai_id not in dictionnaire_skill_levels: dictionnaire_skill_levels[yokai_id] = {}
            for l in t_lvl.split('*'):
                c_lvl = l.split('|')
                if len(c_lvl) >= 13: dictionnaire_skill_levels[yokai_id][c_lvl[1]] = c_lvl

    if f_be:
        t_be, _, _ = lire_donnees_fichier(f_be)
        if t_be:
            for k in [cle for cle in list(dictionnaire_bonus_effect.keys()) if cle[0] == yokai_id]:
                dictionnaire_bonus_effect.pop(k, None)
            for l in t_be.split('*'):
                if not l.strip(): continue
                c_be = l.split('|')
                if len(c_be) >= 2:
                    dictionnaire_bonus_effect[(c_be[0], c_be[1])] = _normaliser_ligne_bonus_effect(c_be)

    if f_bel:
        t_bel, _, _ = lire_donnees_fichier(f_bel)
        if t_bel:
            for k in [cle for cle in list(dictionnaire_bonus_effect_level.keys()) if cle[0] == yokai_id]:
                dictionnaire_bonus_effect_level.pop(k, None)
            for l in t_bel.split('*'):
                if not l.strip(): continue
                c_bel = l.split('|')
                if len(c_bel) >= 3:
                    cle_b = (c_bel[0], c_bel[1])
                    dictionnaire_bonus_effect_level.setdefault(cle_b, {})[c_bel[2]] = _normaliser_ligne_bonus_level(c_bel)
                
    index_trouve = next((i for i, l in enumerate(lignes_yokai) if l.startswith(yokai_id + "|")), -1)
    remplir_cases(colonnes)
    niveau_actuel_var.set("1"); niveau_precedent = "1"
    afficher_donnees_niveau(depuis_code=True)
    charger_icone_ayd()
    charger_bonus_effet_pour_yokai(yokai_id)
    synchroniser_strong_avec_yokai()
    messagebox.showinfo("Mod Chargé", f"Données du Mod chargées pour l'ID {yokai_id} !")

def trouver_fichiers_gamefiles_yokai(yokai_id):
    """
    Recherche tous les fichiers dont le nom contient yokai_id dans gamefiles / serveur / ressources.
    """
    yid_lower = str(yokai_id).strip().lower()
    if not yid_lower:
        return []

    fichiers_trouves = []
    chemins_vus = set()
    noms_vus = set()

    def ajouter_si_valide(chemin_complet):
        if not chemin_complet or not os.path.isfile(chemin_complet):
            return
        nom_f = os.path.basename(chemin_complet)
        if nom_f.lower().endswith(".bak"):
            return
        if yid_lower not in nom_f.lower():
            return
        chemin_abs = os.path.abspath(chemin_complet).replace("\\", "/")
        # Éviter de prendre les fichiers temporaires d'icônes générés par l'outil
        if DOSSIER_TEMP_ICONES and os.path.abspath(DOSSIER_TEMP_ICONES).replace("\\", "/") in chemin_abs:
            return
        if chemin_abs not in chemins_vus and nom_f.lower() not in noms_vus:
            chemins_vus.add(chemin_abs)
            noms_vus.add(nom_f.lower())
            fichiers_trouves.append(chemin_abs)

    # 1. Recherche rapide via INDEX_SERVEUR si déjà indexé
    if DOSSIER_SERVEUR and INDEX_SERVEUR:
        for cle, chemin in INDEX_SERVEUR.items():
            if yid_lower in cle:
                ajouter_si_valide(chemin)

    # 2. Recherche dans les dossiers gamefiles / serveur / ressources
    dossiers_recherche = []
    for cand in [
        os.path.join(DOSSIER_BASE, "gamefiles"),
        os.path.join(os.path.dirname(DOSSIER_BASE), "gamefiles"),
        DOSSIER_SERVEUR,
        DOSSIER_RESSOURCES,
        os.path.join(DOSSIER_BASE, "Resources"),
    ]:
        if cand and os.path.isdir(cand):
            c_norm = os.path.abspath(cand).replace("\\", "/")
            if c_norm not in dossiers_recherche:
                dossiers_recherche.append(c_norm)

    for dossier in dossiers_recherche:
        for racine, _, fichiers in os.walk(dossier):
            for f in fichiers:
                if yid_lower in f.lower():
                    ajouter_si_valide(os.path.join(racine, f))

    return fichiers_trouves

def dump_yokai(fen_menu=None):
    global DOSSIER_SERVEUR
    if fen_menu is not None:
        try:
            fen_menu.destroy()
        except Exception:
            pass

    yokai_id = ""
    if cases_entrees and len(cases_entrees) > 0:
        yokai_id = cases_entrees[0].get().strip()
    if not yokai_id and 'entree_recherche_id' in globals():
        yokai_id = entree_recherche_id.get().strip()

    if not yokai_id:
        messagebox.showwarning("Dump Yo-kai", "Veuillez d'abord charger ou saisir un YoukaiId.")
        return

    fichiers = trouver_fichiers_gamefiles_yokai(yokai_id)

    # Si aucun fichier trouvé, proposer de sélectionner le dossier gamefiles
    if not fichiers:
        if messagebox.askyesno(
            "Dossier gamefiles",
            f"Aucun fichier contenant l'ID '{yokai_id}' n'a été trouvé dans les dossiers configurés.\n\n"
            "Voulez-vous sélectionner le dossier 'gamefiles' contenant les fichiers du jeu ?"
        ):
            choix_gf = filedialog.askdirectory(title="Sélectionner le dossier 'gamefiles'")
            if choix_gf and os.path.isdir(choix_gf):
                DOSSIER_SERVEUR = choix_gf.replace("\\", "/")
                sauvegarder_config()
                indexer_serveur(silencieux=True)
                fichiers = trouver_fichiers_gamefiles_yokai(yokai_id)

    if not fichiers:
        messagebox.showinfo("Dump Yo-kai", f"Aucun fichier contenant '{yokai_id}' n'a été trouvé dans gamefiles.")
        return

    dossier_dest = filedialog.askdirectory(
        title=f"Choisir le dossier où dump les {len(fichiers)} fichier(s) du Yo-kai {yokai_id}"
    )
    if not dossier_dest:
        return

    os.makedirs(dossier_dest, exist_ok=True)
    fichiers_copies = []
    erreurs = []

    for src in fichiers:
        nom_f = os.path.basename(src)
        dst = os.path.join(dossier_dest, nom_f)
        try:
            if os.path.abspath(src) != os.path.abspath(dst):
                shutil.copy2(src, dst)
            fichiers_copies.append(nom_f)
        except Exception as e:
            erreurs.append(f"{nom_f} : {e}")

    apercu = "\n".join(f"• {n}" for n in fichiers_copies[:15])
    if len(fichiers_copies) > 15:
        apercu += f"\n... et {len(fichiers_copies) - 15} autre(s) fichier(s)."

    msg = (
        f"✅ {len(fichiers_copies)} fichier(s) du Yo-kai {yokai_id} dumpé(s) dans :\n"
        f"{dossier_dest}\n\n"
        f"Fichiers copiés :\n{apercu}"
    )
    if erreurs:
        msg += "\n\n⚠️ Erreurs :\n" + "\n".join(erreurs[:5])
    messagebox.showinfo("Dump Yo-kai terminé", msg)

def recherche_multi_criteres():
    p = THEMES.get(THEME_ACTIF, THEMES["Mode Sakura"])
    fen_rech = tk.Toplevel(fenetre)
    fen_rech.title("Recherche multi-critères")
    fen_rech.geometry("820x620")
    fen_rech.configure(bg=p["bg_main"])
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
    cadre = tk.Frame(fen_rech, bg=p["bg_main"])
    cadre.pack(fill=tk.X, padx=12, pady=10)
    for i, (label, cle) in enumerate(champs):
        r, c = divmod(i, 4)
        tk.Label(cadre, text=label + " :", font=("Segoe UI", 9), bg=p["bg_main"], fg=p["text_muted"]).grid(row=r * 2, column=c, sticky="w", padx=5)
        e = tk.Entry(cadre, width=17, font=("Segoe UI", 9), relief=tk.SOLID, bd=1,
                     bg=p["entry_bg"], fg=p["entry_fg"], insertbackground=p["accent"])
        e.grid(row=r * 2 + 1, column=c, sticky="ew", padx=5, pady=(0, 6))
        entrees[cle] = e
    for c in range(4): cadre.grid_columnconfigure(c, weight=1)

    zone = tk.Frame(fen_rech, bg=p["bg_main"])
    zone.pack(fill=tk.BOTH, expand=True, padx=12, pady=5)
    liste = tk.Listbox(zone, font=("Segoe UI", 10), relief=tk.SOLID, bd=1, exportselection=False,
                       bg=p["entry_bg"], fg=p["entry_fg"],
                       selectbackground=p["accent_glow"], selectforeground="#ffffff")
    barre = ttk.Scrollbar(zone, orient="vertical", command=liste.yview)
    liste.configure(yscrollcommand=barre.set)
    liste.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    barre.pack(side=tk.RIGHT, fill=tk.Y)
    correspondances = []

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
            
            # Rang avec support texte / alias
            r_val = entrees["rank"].get().strip()
            if r_val and not matches_rank(r_val, colonnes[3]): continue
            
            # Tribu avec support texte / alias
            k_val = entrees["kind"].get().strip()
            if k_val and not matches_kind(k_val, colonnes[4]): continue
            
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

    tk.Button(fen_rech, text="Rechercher", font=("Segoe UI", 9, "bold"),
              bg=p["btn_special_bg"], fg=p["btn_special_fg"], relief="flat", bd=1, command=rechercher).pack(side=tk.LEFT, padx=12, pady=10)
    tk.Button(fen_rech, text="Fermer", font=("Segoe UI", 9),
              bg=p["btn_bg"], fg=p["btn_fg"], relief="flat", bd=1, command=fen_rech.destroy).pack(side=tk.RIGHT, padx=12, pady=10)
    liste.bind("<Double-Button-1>", charger_selection)
    liste.bind("<Return>", charger_selection)

def ouvrir_editeur_niveaux_groupe():
    p = THEMES.get(THEME_ACTIF, THEMES["Mode Sakura"])
    yokai_id = cases_entrees[0].get().strip() if cases_entrees else ""
    if not yokai_id:
        messagebox.showwarning("Niveau", "Veuillez d'abord charger ou définir un Yo-kai.")
        return
    fen_niv = tk.Toplevel(fenetre)
    fen_niv.title(f"Éditeur groupé des niveaux - {yokai_id}")
    fen_niv.geometry("1100x480")
    fen_niv.configure(bg=p["bg_main"])
    noms = globals().get("champs_niveaux", [])
    colonnes_editables = [idx for _, idx in noms]
    table = tk.Frame(fen_niv, bg=p["bg_main"]); table.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    tk.Label(table, text="Niveau", font=("Segoe UI", 9, "bold"), bg=p["bg_main"], fg=p["accent"]).grid(row=0, column=0, padx=4, pady=4)
    for col, (nom, _) in enumerate(noms, 1):
        tk.Label(table, text=nom, font=("Segoe UI", 9, "bold"), wraplength=110, bg=p["bg_main"], fg=p["text_main"]).grid(row=0, column=col, padx=4, pady=4)
    cellules = {}
    for niveau in range(1, 8):
        tk.Label(table, text=str(niveau), font=("Segoe UI", 9, "bold"), bg=p["bg_main"], fg=p["accent"]).grid(row=niveau, column=0, padx=4, pady=4)
        donnees = dictionnaire_skill_levels.get(yokai_id, {}).get(str(niveau), [""] * 13)
        for col, idx in enumerate(colonnes_editables, 1):
            e = tk.Entry(table, width=16, font=("Segoe UI", 9), relief=tk.SOLID, bd=1,
                         bg=p["entry_bg"], fg=p["entry_fg"], insertbackground=p["accent"])
            if idx < len(donnees): e.insert(0, donnees[idx])
            e.grid(row=niveau, column=col, padx=3, pady=3)
            cellules[(niveau, idx)] = e
    def appliquer_ligne():
        try: source = int(var_source.get())
        except ValueError: return
        if not messagebox.askyesno("Confirmation", f"Appliquer la ligne du niveau {source} à tous les autres niveaux (2 à 7) ?"): return
        valeurs_src = {idx: cellules[(source, idx)].get() for idx in colonnes_editables}
        for niveau in range(1, 8):
            if niveau == source: continue
            for idx in colonnes_editables:
                if idx == 1: continue
                cellules[(niveau, idx)].delete(0, tk.END)
                cellules[(niveau, idx)].insert(0, valeurs_src[idx])
    def enregistrer():
        dictionnaire_skill_levels.setdefault(yokai_id, {})
        for niveau in range(1, 8):
            data = list(dictionnaire_skill_levels[yokai_id].get(str(niveau), [""] * 13))
            while len(data) < 13: data.append("")
            data[0] = yokai_id
            for idx in colonnes_editables:
                if idx == 1: continue
                data[idx] = assainir_texte_export(cellules[(niveau, idx)].get())
            data[1] = str(niveau)
            dictionnaire_skill_levels[yokai_id][str(niveau)] = data
        if niveau_actuel_var.get() in dictionnaire_skill_levels[yokai_id]:
            afficher_donnees_niveau(depuis_code=True)
        fen_niv.destroy()
    bas = tk.Frame(fen_niv, bg=p["bg_main"]); bas.pack(fill=tk.X, padx=10, pady=8)
    tk.Label(bas, text="Ligne source :", font=("Segoe UI", 9), bg=p["bg_main"], fg=p["text_muted"]).pack(side=tk.LEFT)
    var_source = tk.StringVar(value="1")
    ttk.Combobox(bas, textvariable=var_source, values=[str(i) for i in range(1, 8)], width=4, state="readonly").pack(side=tk.LEFT, padx=6)
    tk.Button(bas, text="Appliquer à tous", font=("Segoe UI", 9), bg=p["btn_bg"], fg=p["btn_fg"], relief="flat", bd=1, command=appliquer_ligne).pack(side=tk.LEFT, padx=6)
    tk.Button(bas, text="Enregistrer", font=("Segoe UI", 9, "bold"), bg=p["btn_special_bg"], fg=p["btn_special_fg"], relief="flat", bd=1, command=enregistrer).pack(side=tk.RIGHT, padx=6)
    tk.Button(bas, text="Fermer", font=("Segoe UI", 9), bg=p["btn_bg"], fg=p["btn_fg"], relief="flat", bd=1, command=fen_niv.destroy).pack(side=tk.RIGHT, padx=6)


# ==========================================
# THÈMES ET STYLES TTK
# ==========================================
def configurer_styles_ttk(p):
    style = ttk.Style()
    try: style.theme_use("clam")
    except tk.TclError: pass
    style.configure("TCombobox",
                    fieldbackground=p["entry_bg"],
                    background=p["btn_bg"],
                    foreground=p["entry_fg"],
                    darkcolor=p["card_border"],
                    lightcolor=p["card_border"],
                    arrowcolor=p["accent"])
    style.map("TCombobox",
              fieldbackground=[("readonly", p["entry_bg"])],
              selectbackground=[("readonly", p["accent_glow"])],
              selectforeground=[("readonly", "#ffffff")])
    style.configure("Vertical.TScrollbar",
                    background=p["btn_bg"],
                    troughcolor=p["bg_main"],
                    bordercolor=p["card_border"],
                    arrowcolor=p["text_muted"])
    style.configure("Horizontal.TScrollbar",
                    background=p["btn_bg"],
                    troughcolor=p["bg_main"],
                    bordercolor=p["card_border"],
                    arrowcolor=p["text_muted"])
    try:
        fenetre.option_add("*TCombobox*Listbox.background", p["entry_bg"])
        fenetre.option_add("*TCombobox*Listbox.foreground", p["entry_fg"])
        fenetre.option_add("*TCombobox*Listbox.selectBackground", p["accent_glow"])
        fenetre.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")
    except Exception:
        pass

def appliquer_theme_global(nom_theme):
    global THEME_ACTIF
    THEME_ACTIF = nom_theme
    p = THEMES.get(nom_theme, THEMES["Mode Sakura"])
    configurer_styles_ttk(p)
    fenetre.configure(bg=p["bg_main"])

    def actualiser_widget(w):
        try:
            classe = w.winfo_class()
            if getattr(w, "est_bouton_special", False) or getattr(w, "est_bouton_saut", False):
                w.configure(
                    bg=p["btn_special_bg"],
                    fg=p["btn_special_fg"],
                    activebackground=p["accent_glow"],
                    activeforeground="#ffffff"
                )
            elif classe == "Button":
                w.configure(
                    bg=p["btn_bg"],
                    fg=p["btn_fg"],
                    activebackground=p["card_border"],
                    activeforeground=p["accent"]
                )
            elif classe == "Checkbutton":
                parent_bg = w.master.cget("bg") if hasattr(w.master, "cget") else p["card_bg"]
                w.configure(
                    bg=parent_bg,
                    fg=p["accent"],
                    selectcolor=p["entry_bg"],
                    activebackground=parent_bg,
                    activeforeground=p["accent"]
                )
            elif classe in ("Labelframe", "LabelFrame"):
                w.configure(
                    bg=p["card_bg"],
                    fg=p["accent"]
                )
                try:
                    w.configure(highlightbackground=p["card_border"], highlightcolor=p["accent"])
                except tk.TclError:
                    pass
            elif classe in ("Frame", "Toplevel"):
                parent_bg = w.master.cget("bg") if hasattr(w.master, "cget") else p["bg_main"]
                if getattr(w, "est_carte", False):
                    w.configure(bg=p["card_bg"])
                elif parent_bg in (p["card_bg"], p["bg_main"]):
                    w.configure(bg=parent_bg)
                else:
                    w.configure(bg=p["bg_main"])
            elif classe == "Canvas":
                w.configure(bg=p["bg_main"], highlightthickness=0)
            elif classe == "Label":
                parent_bg = w.master.cget("bg") if hasattr(w.master, "cget") else p["bg_main"]
                fg_spec = getattr(w, "couleur_texte_speciale", None)
                w.configure(bg=parent_bg, fg=fg_spec if fg_spec else p["text_main"])
            elif classe == "Entry":
                w.configure(
                    bg=p["entry_bg"],
                    fg=p["entry_fg"],
                    insertbackground=p["accent"]
                )
                try:
                    w.configure(highlightbackground=p["card_border"], highlightcolor=p["accent"])
                except tk.TclError:
                    pass
            elif classe == "Text":
                w.configure(
                    bg=p["entry_bg"],
                    fg=p["entry_fg"],
                    insertbackground=p["accent"]
                )
            elif classe == "Listbox":
                w.configure(
                    bg=p["entry_bg"],
                    fg=p["entry_fg"],
                    selectbackground=p["accent_glow"],
                    selectforeground="#ffffff"
                )
        except (tk.TclError, AttributeError):
            pass

        for enfant in w.winfo_children():
            actualiser_widget(enfant)

    actualiser_widget(fenetre)
    canvas.configure(bg=p["bg_main"])
    scrollable_frame.configure(bg=p["bg_main"])
    maj_nom_nourriture()
    maj_icone_rang()
    maj_icone_kind()
    charger_icone_ayd()
    verifier_stats_interface()

def changer_theme_selectionne(event=None):
    nouveau = combo_theme_choisi.get()
    if nouveau in THEMES:
        appliquer_theme_global(nouveau)
        sauvegarder_config()

def _dossiers_mst_candidats():
    """Dossiers où chercher les mst, par ordre de priorité :
    1) <serveur>/Resources (même règle que indexer_serveur / initialiser_dossier_version),
    2) le dossier de ywp_mst_youkai déjà chargé,
    3) le dossier des autres mst chargés (skill, bonus...)."""
    candidats = []
    if DOSSIER_SERVEUR:
        candidats.append(os.path.join(DOSSIER_SERVEUR, "Resources"))
    for f in (FICHIER_DB, FICHIER_SKILL_DB, FICHIER_SKILL_LEVEL_DB, FICHIER_BONUS_EFFECT_DB,
              FICHIER_STRONG_SKILL_DB):
        if f:
            candidats.append(os.path.dirname(f))
    vus, out = set(), []
    for c in candidats:
        c = c.replace("\\", "/")
        if c and c not in vus and os.path.isdir(c):
            vus.add(c)
            out.append(c)
    return out

def _contexte_fenetres_liees():
    """Dictionnaire passé au module séparé. Relu à chaque ouverture (suit dossiers/thème)."""
    return {
        "dossiers_mst": _dossiers_mst_candidats(),
        "fichier_yokai": FICHIER_DB,
        "index_serveur": INDEX_SERVEUR,
        "dossier_ressources": DOSSIER_RESSOURCES,
        "theme": THEMES.get(THEME_ACTIF, THEMES["Mode Sakura"]),
        "lire": lire_donnees_fichier,
    }

def ouvrir_fenetres_liees():
    try:
        import fenetres_item_conflate as fic
    except ImportError:
        return messagebox.showerror(
            "Module introuvable",
            "Le fichier fenetres_item_conflate.py doit être placé dans le même dossier que ce script.")
    fic.ouvrir_menu(fenetre, _contexte_fenetres_liees)


# ==========================================
# INTERFACE PRINCIPALE (TKINTER)
# ==========================================
fenetre = tk.Tk()
fenetre.title("PuniEmu Custom Unit Maker - Modding Suite V8")
fenetre.geometry("1140x880")
fenetre.withdraw()

pal_init = THEMES.get(THEME_ACTIF, THEMES["Mode Sakura"])
fenetre.configure(bg=pal_init["bg_main"])
configurer_styles_ttk(pal_init)

# --- BANDEAU SUPÉRIEUR ---
frame_top = tk.Frame(fenetre, padx=14, pady=10)
frame_top.pack(fill=tk.X)

frame_gauche = tk.Frame(frame_top)
frame_gauche.pack(side=tk.LEFT, fill=tk.Y)

# Ligne 0 : Filtre de recherche standard
lbl_filtre = tk.Label(frame_gauche, text="🔍 Filtre :", font=("Segoe UI", 9, "bold"))
lbl_filtre.couleur_texte_speciale = pal_init["accent"]
lbl_filtre.grid(row=0, column=0, sticky="e", pady=2)

combo_recherche = ttk.Combobox(frame_gauche, values=list(INDEX_RECHERCHE.keys()), width=18, state="readonly")
combo_recherche.current(0)
combo_recherche.grid(row=0, column=1, padx=4, pady=2)

entree_recherche_av = tk.Entry(frame_gauche, width=15, font=("Segoe UI", 9), relief=tk.SOLID, bd=1)
entree_recherche_av.grid(row=0, column=2, padx=4, pady=2)
entree_recherche_av.bind("<Return>", lambda e: recherche_avancee())

tk.Button(frame_gauche, text="Go", font=("Segoe UI", 9, "bold"), relief="flat", bd=1, command=recherche_avancee).grid(row=0, column=3, padx=2, pady=2)
tk.Button(frame_gauche, text="Recherche avancée", font=("Segoe UI", 9), relief="flat", bd=1, command=recherche_multi_criteres).grid(row=0, column=4, padx=4, pady=2)

# Ligne 1 : Chargement direct et Navigation Précédent / Suivant
tk.Label(frame_gauche, text="⚙️ Charger ID :", font=("Segoe UI", 9, "bold")).grid(row=1, column=0, sticky="e", pady=4)

frame_id_nav = tk.Frame(frame_gauche)
frame_id_nav.grid(row=1, column=1, columnspan=4, sticky="w", pady=4)

entree_recherche_id = tk.Entry(frame_id_nav, width=12, font=("Segoe UI", 9), relief=tk.SOLID, bd=1)
entree_recherche_id.pack(side=tk.LEFT, padx=(0, 4))
entree_recherche_id.bind("<Return>", lambda e: charger_yokai_par_id())

btn_charger_fiche = tk.Button(frame_id_nav, text="Charger Fiche", font=("Segoe UI", 9, "bold"), relief="flat", bd=1, command=charger_yokai_par_id)
btn_charger_fiche.est_bouton_special = True
btn_charger_fiche.pack(side=tk.LEFT, padx=2)

btn_prec = tk.Button(frame_id_nav, text="◀ Préc.", font=("Segoe UI", 9, "bold"), relief="flat", bd=1, command=naviguer_yokai_precedent)
btn_prec.pack(side=tk.LEFT, padx=2)

btn_suiv = tk.Button(frame_id_nav, text="Suiv. ▶", font=("Segoe UI", 9, "bold"), relief="flat", bd=1, command=naviguer_yokai_suivant)
btn_suiv.pack(side=tk.LEFT, padx=2)

# Bouton prioritaire : Dupliquer / Cloner
btn_clone = tk.Button(frame_id_nav, text="✨ Dupliquer ce Yo-kai", font=("Segoe UI", 9, "bold"),
                      relief="flat", bd=1, command=dupliquer_yokai_courant)
btn_clone.est_bouton_special = True
btn_clone.pack(side=tk.LEFT, padx=(6, 2))

# Bouton Annuler / Recharger
btn_annuler = tk.Button(frame_id_nav, text="🔄 Recharger", font=("Segoe UI", 9),
                        relief="flat", bd=1, command=recharger_yokai_actuel)
btn_annuler.pack(side=tk.LEFT, padx=2)

# Ligne 2 : Yo-kai récents et Nouveau
tk.Label(frame_gauche, text="🕒 Récents :", font=("Segoe UI", 8, "bold")).grid(row=2, column=0, sticky="e", pady=2)
frame_recents = tk.Frame(frame_gauche)
frame_recents.grid(row=2, column=1, columnspan=4, sticky="w", pady=2)

combo_recents = ttk.Combobox(frame_recents, values=HISTORIQUE_RECENTS, width=24, state="readonly")
combo_recents.pack(side=tk.LEFT, padx=(0, 6))
combo_recents.bind("<<ComboboxSelected>>", charger_depuis_recents)

btn_nouveau = tk.Button(frame_recents, text="➕ Nouveau Yo-kai", font=("Segoe UI", 9), relief="flat", bd=1, command=nouveau_yokai)
btn_nouveau.pack(side=tk.LEFT, padx=2)

btn_stat_preset = tk.Button(frame_recents, text="⚡ Modèles de stats", font=("Segoe UI", 9), relief="flat", bd=1, command=ouvrir_dialogue_stat_presets)
btn_stat_preset.pack(side=tk.LEFT, padx=4)

# Cadre droite (Icône du Yo-kai, Rang, Tribu, Boutons globaux)
frame_droite = tk.Frame(frame_top, bd=1, relief=tk.SOLID, padx=12, pady=8, highlightthickness=1)
frame_droite.est_carte = True
frame_droite.pack(side=tk.RIGHT, fill=tk.Y)

frame_icone = tk.Frame(frame_droite)
frame_icone.est_carte = True
frame_icone.pack(side=tk.LEFT, padx=(0, 12))

frame_image_et_rang = tk.Frame(frame_icone)
frame_image_et_rang.est_carte = True
frame_image_et_rang.pack()

label_image_ayd = tk.Label(frame_image_et_rang, text="Aucune icône", relief=tk.FLAT, width=12, height=6, font=("Segoe UI", 8))
label_image_ayd.pack(side=tk.LEFT, padx=4)

label_rang = tk.Label(frame_image_et_rang, text="", font=("Segoe UI", 16, "bold"))
label_rang.couleur_texte_speciale = "#ffb86c"
label_rang.pack(side=tk.LEFT, padx=4)

label_kind = tk.Label(frame_image_et_rang, text="", font=("Segoe UI", 16, "bold"))
label_kind.pack(side=tk.LEFT, padx=4)

btn_charger_icone = tk.Button(frame_icone, text="Charger Icône", font=("Segoe UI", 8, "bold"), relief="flat", bd=1, command=lambda: charger_icone_ayd(depuis_bouton=True))
btn_charger_icone.pack(pady=4)

frame_boutons_droite = tk.Frame(frame_droite)
frame_boutons_droite.est_carte = True
frame_boutons_droite.pack(side=tk.RIGHT)

def creer_bouton_action(parent, texte, commande, spec=False):
    btn = tk.Button(parent, text=texte, font=("Segoe UI", 9, "bold" if spec else "normal"),
                    relief="flat", bd=1, command=commande)
    if spec: btn.est_bouton_special = True
    btn.pack(pady=2, fill=tk.X)
    return btn

creer_bouton_action(frame_boutons_droite, "👁️ Modèle 3D", visualiser_modele_3d, spec=True)
creer_bouton_action(frame_boutons_droite, "💡 Nouvel ID", obtenir_dernier_id)
creer_bouton_action(frame_boutons_droite, "💾 Sauvegarde Globale", ouvrir_menu_sauvegarde, spec=True)
creer_bouton_action(frame_boutons_droite, "📦 Dump Yo-kai", dump_yokai, spec=True)
creer_bouton_action(frame_boutons_droite, "📂 Charger Mod", charger_dossier_mod)
creer_bouton_action(frame_boutons_droite, "⚖️ Comparer Versions", comparer_versions)
creer_bouton_action(frame_boutons_droite, "⚙️ Dossiers", changer_dossiers)
creer_bouton_action(frame_boutons_droite, "🌐 Lier Serveur", indexer_serveur)
creer_bouton_action(frame_boutons_droite, "🎒 Objets & Fusions", ouvrir_fenetres_liees, spec=True)
btn_mode_jeu = creer_bouton_action(frame_boutons_droite, "🎮 Mode : WibWob", basculer_mode_jeu, spec=True)

# Menu choix de thème
tk.Label(frame_boutons_droite, text="🎨 Thème :", font=("Segoe UI", 8, "bold")).pack(pady=(4, 0))
combo_theme_choisi = ttk.Combobox(frame_boutons_droite, values=list(THEMES.keys()), width=14, state="readonly")
combo_theme_choisi.set(THEME_ACTIF)
combo_theme_choisi.pack(pady=(0, 2), fill=tk.X)
combo_theme_choisi.bind("<<ComboboxSelected>>", changer_theme_selectionne)

# --- ZONE CENTRALE DÉROULANTE ---
frame_milieu = tk.Frame(fenetre)
frame_milieu.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 10))

canvas = tk.Canvas(frame_milieu, highlightthickness=0)
scrollbar = ttk.Scrollbar(frame_milieu, orient="vertical", command=canvas.yview)
scrollable_frame = tk.Frame(canvas)

scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)
canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

def creer_section(parent, titre):
    carte = tk.LabelFrame(parent, text=f"  {titre}  ", font=("Segoe UI", 10, "bold"),
                          padx=14, pady=12, relief=tk.SOLID, bd=1, highlightthickness=1)
    carte.est_carte = True
    carte.pack(fill=tk.X, padx=8, pady=8)
    return carte

def creer_bouton_saut_ligne(parent, commande):
    btn = tk.Button(parent, text="↵", width=3, font=("Segoe UI", 9, "bold"),
                    relief="flat", bd=0, command=commande)
    btn.est_bouton_saut = True
    return btn

# --- UI : IDENTITÉ & STATISTIQUES DU YO-KAI (0 à 14) ---
frame_basique = creer_section(scrollable_frame, "Identité & Statistiques du Yo-kai")

for i in range(15):
    ligne, colonne = i // 2, (i % 2) * 2
    tk.Label(frame_basique, text=CHAMPS_YOKAI[i], font=("Segoe UI", 9)).grid(row=ligne, column=colonne, sticky="e", padx=(12, 6), pady=5)

    if i == 3:  # Rang / Rarity avec dropdown et label
        sub_frame_rank = tk.Frame(frame_basique)
        sub_frame_rank.est_carte = True
        sub_frame_rank.grid(row=ligne, column=colonne+1, sticky="w", padx=6, pady=5)
        entree = tk.Entry(sub_frame_rank, width=6, font=("Segoe UI", 9), relief=tk.SOLID, bd=1)
        entree.pack(side=tk.LEFT)
        cases_entrees.append(entree)
        combo_rank = ttk.Combobox(sub_frame_rank, values=[f"{k} - {v['nom']}" for k, v in RANK_NAMES.items()], width=14, state="readonly")
        combo_rank.pack(side=tk.LEFT, padx=4)
        combo_rank.bind("<<ComboboxSelected>>", synchroniser_combo_rank)
        label_nom_rank = tk.Label(sub_frame_rank, text="", font=("Segoe UI", 8, "italic"))
        label_nom_rank.pack(side=tk.LEFT, padx=2)
        entree.bind("<KeyRelease>", maj_icone_rang)

    elif i == 4:  # Tribu / Kind avec dropdown et label
        sub_frame_kind = tk.Frame(frame_basique)
        sub_frame_kind.est_carte = True
        sub_frame_kind.grid(row=ligne, column=colonne+1, sticky="w", padx=6, pady=5)
        entree = tk.Entry(sub_frame_kind, width=6, font=("Segoe UI", 9), relief=tk.SOLID, bd=1)
        entree.pack(side=tk.LEFT)
        cases_entrees.append(entree)
        combo_kind = ttk.Combobox(sub_frame_kind, values=[f"{k} - {v['nom']}" for k, v in KIND_NAMES.items()], width=22, state="readonly")
        combo_kind.pack(side=tk.LEFT, padx=4)
        combo_kind.bind("<<ComboboxSelected>>", synchroniser_combo_kind)
        label_nom_kind = tk.Label(sub_frame_kind, text="", font=("Segoe UI", 8, "italic"))
        label_nom_kind.pack(side=tk.LEFT, padx=2)
        entree.bind("<KeyRelease>", maj_icone_kind)

    elif i == 6:  # Nourriture / FoodType avec dropdown
        sub_frame_food = tk.Frame(frame_basique)
        sub_frame_food.est_carte = True
        sub_frame_food.grid(row=ligne, column=colonne+1, sticky="w", padx=6, pady=5)
        entree = tk.Entry(sub_frame_food, width=6, font=("Segoe UI", 9), relief=tk.SOLID, bd=1)
        entree.pack(side=tk.LEFT)
        cases_entrees.append(entree)
        combo_food = ttk.Combobox(sub_frame_food, values=[f"{k} - {v}" for k, v in FOOD_TYPES.items()], width=16, state="readonly")
        combo_food.pack(side=tk.LEFT, padx=4)
        combo_food.bind("<<ComboboxSelected>>", synchroniser_combo_food)
        label_nom_food = tk.Label(sub_frame_food, text="(Inconnu)", font=("Segoe UI", 9, "bold"))
        label_nom_food.pack(side=tk.LEFT, padx=4)
        entree.bind("<KeyRelease>", maj_nom_nourriture)

    else:
        entree = tk.Entry(frame_basique, width=36, font=("Segoe UI", 9), relief=tk.SOLID, bd=1)
        entree.grid(row=ligne, column=colonne+1, padx=6, pady=5, sticky="w")
        cases_entrees.append(entree)
        if i == 0:
            entree.bind("<KeyRelease>", lambda e: charger_icone_ayd())
            entree.bind("<FocusOut>", lambda e: charger_icone_ayd())
            entree.bind("<Return>", lambda e: charger_icone_ayd())
        # Vérification dynamique des stats pour les champs 8 (BaseHp), 9 (MaxHp), 10 (BaseAtk), 11 (MaxAtk)
        if i in (8, 9, 10, 11):
            entree.bind("<KeyRelease>", verifier_stats_interface)

# Indicateur de cohérence des statistiques
label_stat_status = tk.Label(frame_basique, text="", font=("Segoe UI", 9, "bold"))
label_stat_status.grid(row=8, column=0, columnspan=4, sticky="w", padx=16, pady=(4, 2))

# --- UI : ÂMULTIME (SKILLS) ---
frame_skills = creer_section(scrollable_frame, "✨ Âmultime")

champs_skills_noms = [
    ("Nom", "Nom"),
    ("Description", "Description"),
    ("Propriété 1", "Propriete1"),
    ("Propriété 2", "Propriete2"),
    ("Anim 3D", "Anim3D"),
    ("Anim 2D (1)", "Anim2D"),
    ("Anim 2D (2)", "Anim2D_2"),
    ("Unk0 (Skill)", "SkillUnk0"),
    ("Unk1 (Skill)", "SkillUnk1"),
    ("Unk2 (Skill)", "SkillUnk2"),
    ("Unk3 (Skill)", "SkillUnk3"),
    ("Unk4 (Skill)", "SkillUnk4")
]

tk.Label(frame_skills, text="Type (SoultType) :", font=("Segoe UI", 9)).grid(row=0, column=0, sticky="e", padx=(12, 6), pady=5)
combo_soult_type = ttk.Combobox(frame_skills, values=[f"{k} - {v}" for k, v in SOULT_TYPES.items()], width=34, state="readonly")
combo_soult_type.grid(row=0, column=1, padx=6, pady=5, sticky="w")
cases_skills["TypeID"] = combo_soult_type

for i, (libelle_champ, cle_champ) in enumerate(champs_skills_noms):
    ligne, colonne = (i + 2) // 2, ((i + 2) % 2) * 2
    tk.Label(frame_skills, text=libelle_champ + " :", font=("Segoe UI", 9)).grid(row=ligne, column=colonne, sticky="e", padx=(12, 6), pady=5)
    
    if cle_champ == "Description":
        sous_conteneur = tk.Frame(frame_skills)
        sous_conteneur.est_carte = True
        sous_conteneur.grid(row=ligne, column=colonne+1, padx=6, pady=5, sticky="w")
        entree = tk.Entry(sous_conteneur, width=30, font=("Segoe UI", 9), relief=tk.SOLID, bd=1)
        entree.pack(side=tk.LEFT)
        cases_skills[cle_champ] = entree
        btn_edition_n = creer_bouton_saut_ligne(
            sous_conteneur,
            lambda e=entree: ouvrir_editeur_saut_ligne(e, titre="Édition — Description Âmultime", max_sauts_de_ligne=1, max_mots_secours=5)
        )
        btn_edition_n.pack(side=tk.LEFT, padx=(4, 0))
    else:
        entree = tk.Entry(frame_skills, width=34, font=("Segoe UI", 9), relief=tk.SOLID, bd=1)
        entree.grid(row=ligne, column=colonne+1, padx=6, pady=5, sticky="w")
        cases_skills[cle_champ] = entree

btn_save_skill = tk.Button(frame_skills, text="💾 Enregistrer Âmultime sous...", font=("Segoe UI", 9, "bold"),
                          relief="flat", bd=1, command=sauvegarder_skill_sous)
btn_save_skill.est_bouton_special = True
btn_save_skill.grid(row=(len(champs_skills_noms) + 3) // 2, column=0, columnspan=4, pady=10)

# --- UI : NIVEAUX D'ÂMULTIME (1 à 7) ---
frame_niveaux = creer_section(scrollable_frame, "📊 Niveaux d'Âmultime (1 à 7)")

frame_selection_niveau = tk.Frame(frame_niveaux)
frame_selection_niveau.est_carte = True
frame_selection_niveau.pack(fill=tk.X, pady=(0, 10))

tk.Label(frame_selection_niveau, text="Édition du Niveau :", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=(12, 6))

niveau_actuel_var = tk.StringVar(value="1")
combo_niveau = ttk.Combobox(frame_selection_niveau, textvariable=niveau_actuel_var, values=[str(i) for i in range(1, 8)], width=5, state="readonly")
combo_niveau.pack(side=tk.LEFT, padx=6)
combo_niveau.bind("<<ComboboxSelected>>", afficher_donnees_niveau)

btn_groupe = tk.Button(frame_selection_niveau, text="📝 Éditeur Groupé (Grille 1 à 7)", font=("Segoe UI", 9, "bold"),
                      relief="flat", bd=1, command=ouvrir_editeur_niveaux_groupe)
btn_groupe.est_bouton_special = True
btn_groupe.pack(side=tk.RIGHT, padx=12)

frame_champs_niveaux = tk.Frame(frame_niveaux)
frame_champs_niveaux.est_carte = True
frame_champs_niveaux.pack(fill=tk.X)

champs_niveaux = [
    ("Taux Remplissage", 2),
    ("Dégâts / Taux (Float)", 3),
    ("Description (Niveau)", 4),
    ("Second Taux", 5),
    ("Troisième Taux", 6),
    ("Quatrième Taux", 7),
    ("Cinquième Taux", 8),
    ("Sixième Taux", 9),
    ("Septième Taux", 10),
    ("Unk (Level 1)", 11),
    ("Unk (Level 2)", 12)
]

for i, (libelle, index_colonne) in enumerate(champs_niveaux):
    ligne, colonne = i // 2, (i % 2) * 2
    tk.Label(frame_champs_niveaux, text=libelle + " :", font=("Segoe UI", 9)).grid(row=ligne, column=colonne, sticky="e", padx=(12, 6), pady=5)
    
    if index_colonne == 4:
        sous_conteneur_lvl = tk.Frame(frame_champs_niveaux)
        sous_conteneur_lvl.est_carte = True
        sous_conteneur_lvl.grid(row=ligne, column=colonne+1, padx=6, pady=5, sticky="w")
        entree = tk.Entry(sous_conteneur_lvl, width=30, font=("Segoe UI", 9), relief=tk.SOLID, bd=1)
        entree.pack(side=tk.LEFT)
        cases_skill_levels[index_colonne] = entree
        btn_edition_n = creer_bouton_saut_ligne(
            sous_conteneur_lvl,
            lambda e=entree: ouvrir_editeur_saut_ligne(e, titre="Édition — Description Niveau", max_sauts_de_ligne=1, max_mots_secours=5)
        )
        btn_edition_n.pack(side=tk.LEFT, padx=(4, 0))
    else:
        entree = tk.Entry(frame_champs_niveaux, width=34, font=("Segoe UI", 9), relief=tk.SOLID, bd=1)
        entree.grid(row=ligne, column=colonne+1, padx=6, pady=5, sticky="w")
        cases_skill_levels[index_colonne] = entree

# --- UI : EFFETS BONUS (SUPPORT MULTI-SKILLS : 1, 2, 3) ---
frame_bonus = creer_section(scrollable_frame, "🎁 Effets Bonus (Skills 1, 2 & 3)")

activer_bonus_effect_var = tk.BooleanVar(value=False)
chk_activer_bonus = tk.Checkbutton(frame_bonus, text="Activer les Effets Bonus (Skills) pour ce Yo-kai",
                                   variable=activer_bonus_effect_var, command=toggle_champs_bonus_effect,
                                   font=("Segoe UI", 10, "bold"), relief="flat")
chk_activer_bonus.pack(anchor="w", padx=12, pady=5)

sub_cadre_bonus = tk.Frame(frame_bonus)
sub_cadre_bonus.est_carte = True

# Conteneur des cartes de skills
frame_skills_container = tk.Frame(sub_cadre_bonus)
frame_skills_container.est_carte = True
frame_skills_container.pack(fill=tk.X, expand=True, padx=4, pady=2)

# Barre d'actions pour ajouter Skill 2 / Skill 3
frame_actions_bonus = tk.Frame(sub_cadre_bonus)
frame_actions_bonus.est_carte = True
frame_actions_bonus.pack(fill=tk.X, padx=12, pady=6)

btn_ajouter_skill2 = tk.Button(frame_actions_bonus, text="➕ Ajouter un 2ᵉ Skill (Skill 2)", font=("Segoe UI", 9, "bold"),
                               relief="flat", bd=1, command=lambda: ajouter_nouveau_skill("2"))
btn_ajouter_skill2.est_bouton_special = True
btn_ajouter_skill2.pack(side=tk.LEFT, padx=(0, 6))

btn_ajouter_skill3 = tk.Button(frame_actions_bonus, text="➕ Ajouter un 3ᵉ Skill (Skill 3)", font=("Segoe UI", 9, "bold"),
                               relief="flat", bd=1, command=lambda: ajouter_nouveau_skill("3"))
btn_ajouter_skill3.est_bouton_special = True
btn_ajouter_skill3.pack(side=tk.LEFT, padx=6)

btn_ajouter_skill_autre = tk.Button(frame_actions_bonus, text="➕ Ajouter un autre Skill", font=("Segoe UI", 9),
                                    relief="flat", bd=1, command=lambda: ajouter_nouveau_skill())
btn_ajouter_skill_autre.pack(side=tk.LEFT, padx=6)

# Aperçu de TOUTES les lignes MST générées
frame_mst_preview = tk.LabelFrame(sub_cadre_bonus, text="  📋 Lignes MST générées (ywp_mst_youkai_bonus_effect & _level)  ",
                                  font=("Segoe UI", 9, "bold"), padx=10, pady=6, relief=tk.SOLID, bd=1, highlightthickness=1)
frame_mst_preview.est_carte = True
frame_mst_preview.pack(fill=tk.X, padx=12, pady=(10, 8))

frame_mst_header = tk.Frame(frame_mst_preview)
frame_mst_header.est_carte = True
frame_mst_header.pack(fill=tk.X, pady=(0, 4))

lbl_mst_info = tk.Label(frame_mst_header, text="0 Skill actif", font=("Segoe UI", 9, "italic"))
lbl_mst_info.pack(side=tk.LEFT, padx=4)

btn_copier_mst = tk.Button(frame_mst_header, text="📋 Copier toutes les lignes MST", font=("Segoe UI", 8, "bold"),
                           relief="flat", bd=1, command=copier_lignes_mst_presse_papier)
btn_copier_mst.est_bouton_special = True
btn_copier_mst.pack(side=tk.RIGHT, padx=4)

frame_txt_scroll = tk.Frame(frame_mst_preview)
frame_txt_scroll.est_carte = True
frame_txt_scroll.pack(fill=tk.BOTH, expand=True)

txt_mst_preview = tk.Text(frame_txt_scroll, height=8, wrap="none", font=("Consolas", 9), relief=tk.SOLID, bd=1)
txt_mst_preview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

scroll_mst_y = ttk.Scrollbar(frame_txt_scroll, orient="vertical", command=txt_mst_preview.yview)
scroll_mst_y.pack(side=tk.RIGHT, fill=tk.Y)
txt_mst_preview.configure(yscrollcommand=scroll_mst_y.set)

scroll_mst_x = ttk.Scrollbar(frame_mst_preview, orient="horizontal", command=txt_mst_preview.xview)
scroll_mst_x.pack(fill=tk.X)
txt_mst_preview.configure(xscrollcommand=scroll_mst_x.set)

# Variables pour compatibilité globale
subid_bonus_var = tk.StringVar(value="1")
combo_bonus_type = ttk.Combobox(sub_cadre_bonus, values=[f"{k} - {v}" for k, v in YW_BONUS_EFFECTS.items()], width=46, state="readonly")
niveau_bonus_actuel_var = tk.StringVar(value="1")
combo_niv_b = ttk.Combobox(sub_cadre_bonus, textvariable=niveau_bonus_actuel_var, values=[str(i) for i in range(1, 6)], state="readonly")

# --- UI : STRONG SKILL (Puni Puni) ---
frame_strong = creer_section(scrollable_frame, "⚡ Strong Skill (exclusif Puni Puni)")

frame_top_strong = tk.Frame(frame_strong)
frame_top_strong.est_carte = True
frame_top_strong.pack(fill=tk.X, pady=(0, 8))

tk.Label(frame_top_strong, text="ID Strong Skill :", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(12, 6))
strong_id_actuel_var = tk.StringVar()
entree_strong_id = tk.Entry(frame_top_strong, textvariable=strong_id_actuel_var, width=12, font=("Segoe UI", 9), relief=tk.SOLID, bd=1)
entree_strong_id.pack(side=tk.LEFT, padx=6)
entree_strong_id.bind("<Return>", lambda e: charger_strong_skill_par_id())

tk.Button(frame_top_strong, text="Charger ce Strong Skill", font=("Segoe UI", 9), relief="flat", bd=1,
          command=charger_strong_skill_par_id).pack(side=tk.LEFT, padx=4)
tk.Button(frame_top_strong, text="💾 Enregistrer Strong Skill", font=("Segoe UI", 9, "bold"),
          command=sauvegarder_strong_skill, relief="flat", bd=1).pack(side=tk.RIGHT, padx=12)

frame_champs_strong = tk.Frame(frame_strong)
frame_champs_strong.est_carte = True
frame_champs_strong.pack(fill=tk.X)

tk.Label(frame_champs_strong, text="Type (SoultType) :", font=("Segoe UI", 9)).grid(row=0, column=0, sticky="e", padx=(12, 6), pady=5)
combo_strong_type = ttk.Combobox(frame_champs_strong, values=[f"{k} - {v}" for k, v in SOULT_TYPES.items()], width=34)
combo_strong_type.grid(row=0, column=1, padx=6, pady=5, sticky="w")
cases_strong_skills["TypeID"] = combo_strong_type

champs_strong_noms = [
    ("Nom", "Nom"),
    ("Description", "Description"),
    ("Propriété 1", "Propriete1"),
    ("Propriété 2", "Propriete2"),
    ("Anim 3D", "Anim3D"),
    ("Anim 2D (1)", "Anim2D"),
    ("Anim 2D (2)", "Anim2D_2"),
    ("Unk0 (Skill)", "SkillUnk0"),
    ("Unk1 (Skill)", "SkillUnk1"),
    ("Unk2 (Skill)", "SkillUnk2"),
    ("Unk3 (Skill)", "SkillUnk3"),
    ("Réserve", "Reserve"),
    ("Cutin A", "CutinA"),
    ("Cutin B", "CutinB"),
    ("Lien externe", "LienExterne"),
]

for i, (libelle, cle) in enumerate(champs_strong_noms):
    r, c = (i + 2) // 2, ((i + 2) % 2) * 2
    tk.Label(frame_champs_strong, text=libelle + " :", font=("Segoe UI", 9)).grid(row=r, column=c, sticky="e", padx=(12, 6), pady=5)
    if cle == "Description":
        sous_conteneur_s = tk.Frame(frame_champs_strong)
        sous_conteneur_s.est_carte = True
        sous_conteneur_s.grid(row=r, column=c+1, padx=6, pady=5, sticky="w")
        entree = tk.Entry(sous_conteneur_s, width=30, font=("Segoe UI", 9), relief=tk.SOLID, bd=1)
        entree.pack(side=tk.LEFT)
        cases_strong_skills[cle] = entree
        btn_edition_s = creer_bouton_saut_ligne(
            sous_conteneur_s,
            lambda e=entree: ouvrir_editeur_saut_ligne(e, titre="Édition — Description Strong Skill", max_sauts_de_ligne=1, max_mots_secours=5)
        )
        btn_edition_s.pack(side=tk.LEFT, padx=(4, 0))
    else:
        entree = tk.Entry(frame_champs_strong, width=34, font=("Segoe UI", 9), relief=tk.SOLID, bd=1)
        entree.grid(row=r, column=c+1, padx=6, pady=5, sticky="w")
        cases_strong_skills[cle] = entree

# Niveaux Strong Skill (1 à 7)
frame_niv_strong = tk.LabelFrame(frame_strong, text="  Niveaux du Strong Skill (1 à 7)  ",
                                font=("Segoe UI", 9, "bold"), padx=12, pady=8, relief=tk.SOLID, bd=1, highlightthickness=1)
frame_niv_strong.est_carte = True
frame_niv_strong.pack(fill=tk.X, padx=12, pady=(10, 5))

frame_sel_niv_s = tk.Frame(frame_niv_strong)
frame_sel_niv_s.est_carte = True
frame_sel_niv_s.pack(fill=tk.X, pady=(0, 6))

tk.Label(frame_sel_niv_s, text="Niveau sélectionné :", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(4, 6))
niveau_strong_actuel_var = tk.StringVar(value="1")
combo_niv_s = ttk.Combobox(frame_sel_niv_s, textvariable=niveau_strong_actuel_var, values=[str(i) for i in range(1, 8)], width=5, state="readonly")
combo_niv_s.pack(side=tk.LEFT, padx=4)
combo_niv_s.bind("<<ComboboxSelected>>", afficher_niveau_strong)

frame_inputs_niv_s = tk.Frame(frame_niv_strong)
frame_inputs_niv_s.est_carte = True
frame_inputs_niv_s.pack(fill=tk.X)

for i, (libelle, idx) in enumerate(champs_niveaux):
    r, c = i // 2, (i % 2) * 2
    tk.Label(frame_inputs_niv_s, text=libelle + " :", font=("Segoe UI", 9)).grid(row=r, column=c, sticky="e", padx=(12, 6), pady=5)
    if idx == 4:
        sous_conteneur_sn = tk.Frame(frame_inputs_niv_s)
        sous_conteneur_sn.est_carte = True
        sous_conteneur_sn.grid(row=r, column=c+1, padx=6, pady=5, sticky="w")
        e = tk.Entry(sous_conteneur_sn, width=30, font=("Segoe UI", 9), relief=tk.SOLID, bd=1)
        e.pack(side=tk.LEFT)
        cases_strong_skill_levels[idx] = e
        btn_edition_sn = creer_bouton_saut_ligne(
            sous_conteneur_sn,
            lambda ent=e: ouvrir_editeur_saut_ligne(ent, titre="Édition — Description Niveau Strong", max_sauts_de_ligne=1, max_mots_secours=5)
        )
        btn_edition_sn.pack(side=tk.LEFT, padx=(4, 0))
    else:
        e = tk.Entry(frame_inputs_niv_s, width=34, font=("Segoe UI", 9), relief=tk.SOLID, bd=1)
        e.grid(row=r, column=c+1, padx=6, pady=5, sticky="w")
        cases_strong_skill_levels[idx] = e

# --- UI : PARAMÈTRES AVANCÉS (Champs 15 à 38) ---
btn_toggle_avance = tk.Button(scrollable_frame, text="🔽 Afficher Paramètres Avancés (Champs 15 à 38)",
                              font=("Segoe UI", 9, "bold"), relief="flat", bd=1, command=toggle_avance)
btn_toggle_avance.pack(pady=12)

frame_avance = tk.LabelFrame(scrollable_frame, text="  Paramètres Avancés (Champs 15 à 38)  ", font=("Segoe UI", 10, "bold"),
                             padx=14, pady=12, relief=tk.SOLID, bd=1, highlightthickness=1)
frame_avance.est_carte = True

for i in range(15, len(CHAMPS_YOKAI)):
    ligne, colonne = (i - 15) // 2, ((i - 15) % 2) * 2
    tk.Label(frame_avance, text=CHAMPS_YOKAI[i], font=("Segoe UI", 9)).grid(row=ligne, column=colonne, sticky="e", padx=(12, 6), pady=5)
    
    if i in (15, 16, 17, 18, 19):
        sous_conteneur_av = tk.Frame(frame_avance)
        sous_conteneur_av.est_carte = True
        sous_conteneur_av.grid(row=ligne, column=colonne+1, padx=6, pady=5, sticky="w")
        
        entree = tk.Entry(sous_conteneur_av, width=32, font=("Segoe UI", 9), relief=tk.SOLID, bd=1)
        entree.pack(side=tk.LEFT)
        cases_entrees.append(entree)
        
        btn_edition_n = creer_bouton_saut_ligne(
            sous_conteneur_av,
            lambda e=entree, t=CHAMPS_YOKAI[i]: ouvrir_editeur_saut_ligne(e, titre=f"Édition — {t}", max_sauts_de_ligne=None, max_mots_secours=5)
        )
        btn_edition_n.pack(side=tk.LEFT, padx=(4, 0))
    else:
        entree = tk.Entry(frame_avance, width=36, font=("Segoe UI", 9), relief=tk.SOLID, bd=1)
        entree.grid(row=ligne, column=colonne+1, padx=6, pady=5, sticky="w")
        cases_entrees.append(entree)


# ==========================================
# RACCOURCIS CLAVIER GLOBAUX
# ==========================================
fenetre.bind("<Control-s>", lambda e: ouvrir_menu_sauvegarde())
fenetre.bind("<Control-S>", lambda e: ouvrir_menu_sauvegarde())
fenetre.bind("<Control-f>", lambda e: entree_recherche_id.focus_set())
fenetre.bind("<Control-F>", lambda e: entree_recherche_id.focus_set())
fenetre.bind("<Control-n>", lambda e: nouveau_yokai())
fenetre.bind("<Control-N>", lambda e: nouveau_yokai())
fenetre.bind("<Control-d>", lambda e: dupliquer_yokai_courant())
fenetre.bind("<Control-D>", lambda e: dupliquer_yokai_courant())
fenetre.bind("<Control-z>", recharger_yokai_actuel)
fenetre.bind("<Control-Z>", recharger_yokai_actuel)
fenetre.bind("<Alt-Left>", naviguer_yokai_precedent)
fenetre.bind("<Alt-Right>", naviguer_yokai_suivant)


# ==========================================
# DÉMARRAGE DE L'OUTIL
# ==========================================
def demarrer_outil():
    if charger_config(): return True
    if initialiser_outils(au_demarrage=True) and initialiser_dossier_version(au_demarrage=True):
        sauvegarder_config()
        return True
    return False

if __name__ == "__main__":
    if demarrer_outil():
        charger_fichier()
        charger_skills()
        charger_skill_levels()
        charger_bonus_effects()
        charger_bonus_effect_levels()
        charger_strong_skills()
        charger_strong_skill_levels()
        appliquer_theme_global(THEME_ACTIF)
        combo_theme_choisi.set(THEME_ACTIF)
        appliquer_mode_jeu()
        if lignes_yokai:
            charger_yokai_par_index(0)
        fenetre.deiconify()
        fenetre.mainloop()
