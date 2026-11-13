# -*- coding: utf-8 -*-
"""
Module de gestion des fichiers MST, sauvegardes automatiques et assainissement de texte.
"""

import os
import re
import json
import shutil
import zipfile
import tempfile
import subprocess
from datetime import datetime

CLES_JSON_TABLE = ("tableData", "masterData", "data", "rows", "table")


# =====================================================================
# SAUVEGARDE AUTOMATIQUE (BACKUPS)
# =====================================================================

def creer_backup(chemin_fichier, dossier_backup="backups", max_backups=25):
    """
    Crée une copie horodatée du fichier dans un dossier de sauvegarde (par défaut 'backups/').
    Nettoie les anciennes sauvegardes pour ne conserver que les `max_backups` plus récentes.
    """
    if not chemin_fichier or not os.path.exists(chemin_fichier):
        return None

    try:
        dossier_backups = os.path.abspath(dossier_backup)
        os.makedirs(dossier_backups, exist_ok=True)

        nom_fichier = os.path.basename(chemin_fichier)
        nom_sans_ext, ext = os.path.splitext(nom_fichier)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nom_backup = f"{nom_sans_ext}_{timestamp}{ext}.bak"
        chemin_backup = os.path.join(dossier_backups, nom_backup)

        shutil.copy2(chemin_fichier, chemin_backup)

        # Nettoyage des anciennes sauvegardes pour ce fichier spécifique
        prefixe = f"{nom_sans_ext}_"
        backups_existants = [
            f for f in os.listdir(dossier_backups)
            if f.startswith(prefixe) and f.endswith(".bak")
        ]
        backups_existants.sort(
            key=lambda f: os.path.getmtime(os.path.join(dossier_backups, f)),
            reverse=True
        )

        for vieux in backups_existants[max_backups:]:
            try:
                os.remove(os.path.join(dossier_backups, vieux))
            except OSError:
                pass

        return chemin_backup
    except Exception as e:
        print(f"[Backup] Erreur lors de la création du backup pour {chemin_fichier} : {e}")
        return None


# =====================================================================
# ASSAINISSEMENT & GESTION DES SAUTS DE LIGNE
# =====================================================================

def normaliser_sauts_ligne(val):
    """Transforme les faux sauts de ligne littéraux en vrais sauts de ligne."""
    if not isinstance(val, str):
        return val
    return val.replace(r"\n", "\n")


def assainir_texte_export(val):
    """Garantit qu'aucun saut physique de ligne n'est écrit dans le fichier brut."""
    if not isinstance(val, str):
        return val
    v = val.replace("\r\n", r"\n").replace("\r", r"\n").replace("\n", r"\n")
    return re.sub(r"(\\n){2,}", r"\\n", v)


def litteraliser_pour_txt(val):
    """Garantit qu'aucun saut de ligne physique n'atterrit dans un fichier .txt brut."""
    if not isinstance(val, str):
        return val
    return val.replace("\r\n", r"\n").replace("\r", r"\n").replace("\n", r"\n")


def preparer_texte_interface(val):
    """Prépare le texte pour l'affichage dans un Text widget multi-lignes."""
    if not isinstance(val, str):
        return ""
    v = val.replace(r"\n", "\n")
    return re.sub(r"\n{2,}", "\n", v)


def formater_texte_4_mots(texte, max_mots_secours=5, max_sauts_de_ligne=None):
    """Formate un texte en insérant un saut de ligne environ tous les 4 mots."""
    mots = texte.strip().split()
    if not mots:
        return ""
    lignes = []
    i = 0
    while i < len(mots):
        if max_sauts_de_ligne is not None and len(lignes) >= max_sauts_de_ligne:
            lignes.append(" ".join(mots[i:]))
            break
        mots_restants = len(mots) - i
        if mots_restants <= max_mots_secours:
            lignes.append(" ".join(mots[i:]))
            break
        paquet = 4
        lignes.append(" ".join(mots[i:i + paquet]))
        i += paquet
    return r"\n".join(lignes)


def _element_vers_ligne(element):
    if isinstance(element, dict):
        return "|".join(str(v) if v is not None else "" for v in element.values())
    if isinstance(element, (list, tuple)):
        return "|".join(str(v) if v is not None else "" for v in element)
    return str(element) if element is not None else ""


def _normaliser_texte(texte):
    if not isinstance(texte, str):
        return ""
    return texte.replace("\r\n", "\n").replace("\r", "\n")


def _colonnes_natives(ligne):
    return [normaliser_sauts_ligne(c) for c in ligne.split("|")]


# =====================================================================
# LECTURE & ÉCRITURE DES FICHIERS MST (.txt / .json)
# =====================================================================

def lire_donnees_fichier(chemin):
    """
    Lit un fichier MST (texte brut séparé par * ou JSON structuré).
    Retourne (texte_normalise, donnees_json_orig, est_compact).
    """
    if not chemin or not os.path.exists(chemin):
        return "", None, None

    try:
        with open(chemin, "r", encoding="utf-8") as f:
            contenu = f.read().strip()
    except Exception as e:
        print(f"Erreur de lecture de {chemin} : {e}")
        return "", None, None

    try:
        donnees = json.loads(contenu)
    except ValueError:
        return _normaliser_texte(contenu), None, None

    est_compact = "\n" not in contenu

    if isinstance(donnees, dict):
        for cle in CLES_JSON_TABLE:
            if cle in donnees:
                valeur = donnees[cle]
                if isinstance(valeur, str):
                    return _normaliser_texte(valeur), donnees, est_compact
                iterable = valeur.values() if isinstance(valeur, dict) else valeur
                return _normaliser_texte("*".join(_element_vers_ligne(e) for e in iterable)), donnees, est_compact
        return _normaliser_texte("*".join(_element_vers_ligne(v) for v in donnees.values())), donnees, est_compact

    if isinstance(donnees, list):
        return _normaliser_texte("*".join(_element_vers_ligne(e) for e in donnees)), donnees, est_compact

    return "", None, None


def maj_fichier_original(chemin_fichier, nouvelles_lignes, yokai_id,
                         insertion_par_dictionary_id=False, avec_backup=True):
    """
    Met à jour un fichier MST d'origine en remplaçant ou insérant les lignes du Yo-kai.
    Effectue une sauvegarde préalable dans 'backups/' si avec_backup=True.
    """
    if not chemin_fichier or not os.path.exists(chemin_fichier):
        raise FileNotFoundError(f"Fichier introuvable : {chemin_fichier}")

    if avec_backup:
        creer_backup(chemin_fichier)

    texte_brut, donnees_json_orig, est_compact = lire_donnees_fichier(chemin_fichier)
    lignes_existantes = texte_brut.split('*') if texte_brut else []
    lignes_filtrees = [l.strip() for l in lignes_existantes if l.strip() and not l.startswith(str(yokai_id) + "|")]
    liste_nouvelles = nouvelles_lignes if isinstance(nouvelles_lignes, list) else [nouvelles_lignes]
    liste_nouvelles = [l.strip() for l in liste_nouvelles if l.strip()]

    if insertion_par_dictionary_id:
        def dictionary_id_de(ligne):
            colonnes = ligne.split('|')
            try:
                return int(colonnes[14])
            except (IndexError, ValueError):
                return None

        for nouvelle_ligne in liste_nouvelles:
            did_nouveau = dictionary_id_de(nouvelle_ligne)
            if did_nouveau is None:
                lignes_filtrees.append(nouvelle_ligne)
                continue

            position_insertion = len(lignes_filtrees)
            for i, ligne_existante in enumerate(lignes_filtrees):
                did_existant = dictionary_id_de(ligne_existante)
                if did_existant is not None and did_existant > did_nouveau:
                    position_insertion = i
                    break
            lignes_filtrees.insert(position_insertion, nouvelle_ligne)
        lignes_finales = lignes_filtrees
    else:
        lignes_finales = liste_nouvelles + lignes_filtrees

    lignes_finales_json = [normaliser_sauts_ligne(l) for l in lignes_finales]
    nouveau_texte_json = "*".join(lignes_finales_json)
    nouveau_texte = "*".join(litteraliser_pour_txt(l) for l in lignes_finales)

    def _reconstruire(valeur_orig):
        if isinstance(valeur_orig, str):
            return nouveau_texte_json
        if isinstance(valeur_orig, list):
            if valeur_orig and isinstance(valeur_orig[0], str):
                return lignes_finales_json
            return [_colonnes_natives(l) for l in lignes_finales_json]
        if isinstance(valeur_orig, dict):
            return {l.split("|")[0]: _colonnes_natives(l) for l in lignes_finales_json}
        return nouveau_texte_json

    kwargs_json = {"ensure_ascii": False}
    if est_compact:
        kwargs_json["separators"] = (",", ":")
    else:
        kwargs_json["indent"] = 4

    with open(chemin_fichier, "w", encoding="utf-8") as f:
        if donnees_json_orig is None:
            f.write(nouveau_texte)
        elif isinstance(donnees_json_orig, dict) and any(c in donnees_json_orig for c in CLES_JSON_TABLE):
            cle = next(c for c in CLES_JSON_TABLE if c in donnees_json_orig)
            donnees_json_orig[cle] = _reconstruire(donnees_json_orig[cle])
            json.dump(donnees_json_orig, f, **kwargs_json)
        else:
            json.dump(_reconstruire(donnees_json_orig), f, **kwargs_json)


# =====================================================================
# DÉTECTION DES CONFLITS
# =====================================================================

def verifier_conflits_yokai(lignes_yokai, nouveau_yokai_id, nouveau_dict_id=None, ignorer_yokai_id=None):
    """
    Vérifie si un YoukaiId ou un DictionaryId est déjà utilisé dans la base.
    Retourne une liste de messages d'avertissement (vide si aucun conflit).
    """
    conflits = []
    nouveau_yokai_id_str = str(nouveau_yokai_id).strip()
    nouveau_dict_id_str = str(nouveau_dict_id).strip() if nouveau_dict_id is not None else ""
    ignorer_str = str(ignorer_yokai_id).strip() if ignorer_yokai_id is not None else ""

    for ligne in lignes_yokai:
        colonnes = ligne.split('|')
        if len(colonnes) < 2:
            continue
        yid = colonnes[0].strip()
        nom = colonnes[1].strip()

        if yid == ignorer_str:
            continue

        if yid == nouveau_yokai_id_str:
            conflits.append(f"Le YoukaiId '{yid}' est déjà utilisé par '{nom}'.")

        if nouveau_dict_id_str and len(colonnes) > 14:
            did = colonnes[14].strip()
            if did == nouveau_dict_id_str:
                conflits.append(f"Le Dictionary ID '{did}' est déjà utilisé par '{nom}' (ID: {yid}).")

    return conflits


# =====================================================================
# OUTILS EXTERNES (yokai.exe pour fichiers .ez)
# =====================================================================

def traiter_ez_avec_yokai(chemin_exe, chemin_ez):
    """Décompresse un fichier .ez via yokai.exe."""
    if not chemin_exe or not os.path.exists(chemin_exe):
        return None
    dossier_parent = os.path.dirname(os.path.abspath(chemin_ez))
    try:
        subprocess.run(
            [os.path.abspath(chemin_exe), os.path.abspath(chemin_ez)],
            cwd=dossier_parent, check=True, creationflags=0x08000000 if os.name == 'nt' else 0
        )
        chemin_zip = os.path.splitext(chemin_ez)[0] + ".zip"
        return chemin_zip if os.path.exists(chemin_zip) else None
    except Exception as e:
        print(f"Erreur extraction EZ: {e}")
        return None


DOSSIER_TEMP_ICONES = os.path.join(tempfile.gettempdir(), "mst_tool_temp_icons")
os.makedirs(DOSSIER_TEMP_ICONES, exist_ok=True)

def nettoyer_fichiers_temporaires():
    try:
        if os.path.exists(DOSSIER_TEMP_ICONES):
            shutil.rmtree(DOSSIER_TEMP_ICONES, ignore_errors=True)
    except Exception:
        pass

import atexit
atexit.register(nettoyer_fichiers_temporaires)


def dechiffrer_donnees_avec_yokai(donnees_cryptees, base_nom, chemin_yokai_exe, yokai_id=None):
    """
    Écrit des données cryptées dans un fichier .ez temporaire,
    utilise yokai.exe pour les déchiffrer en .zip, et extrait l'image PNG correspondante.
    """
    if not chemin_yokai_exe or not os.path.exists(chemin_yokai_exe):
        return None

    temp_dir = tempfile.mkdtemp(prefix=f"yokai_{base_nom}_")
    try:
        temp_ez = os.path.join(temp_dir, f"{base_nom}.ez")
        with open(temp_ez, "wb") as f:
            f.write(donnees_cryptees)

        flags = 0x08000000 if os.name == 'nt' else 0
        subprocess.run(
            [os.path.abspath(chemin_yokai_exe), os.path.abspath(temp_ez)],
            cwd=temp_dir, check=True, creationflags=flags, capture_output=True
        )

        temp_zip = os.path.join(temp_dir, f"{base_nom}.zip")
        if os.path.exists(temp_zip) and zipfile.is_zipfile(temp_zip):
            with zipfile.ZipFile(temp_zip, 'r') as zf_dec:
                noms = zf_dec.namelist()
                # 1. Correspondance exacte bl_{yokai_id}.png
                cibles = [f for f in noms if f.lower() == f"{base_nom}.png".lower()]
                # 2. Correspondance avec yokai_id.png
                if not cibles and yokai_id:
                    cibles = [f for f in noms if f.lower() == f"{yokai_id}.png".lower()]
                # 3. Fichiers bl_*.png SAUF les fichiers d'outline _o.png
                if not cibles:
                    cibles = [f for f in noms if f.lower().startswith("bl_") and f.lower().endswith(".png") and not f.lower().endswith("_o.png")]
                # 4. Fichiers *.png non-outline
                if not cibles:
                    cibles = [f for f in noms if f.lower().endswith(".png") and not f.lower().endswith("_o.png")]
                # 5. Dernier recours : n'importe quel PNG
                if not cibles:
                    cibles = [f for f in noms if f.lower().endswith(".png")]
                if cibles:
                    return zf_dec.read(cibles[0])
    except Exception as e:
        print(f"Erreur déchiffrement yokai.exe ({base_nom}): {e}")
    finally:
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass
    return None


def extraire_icone_depuis_ayd(chemin_ayd, yokai_id, chemin_yokai_exe, dossier_sauvegarde=None):
    """
    Extrait l'image PNG de l'icône Yo-kai (bl_yokaiID.png) depuis un fichier .ayd.
    Gère la décompression directe (si archive zip non cryptée contenant directement le png)
    et la double décompression :
      1. Premier niveau : .ayd sans encryption (archive zip) contenant un .ayd ou .ez avec encryption.
      2. Deuxième niveau : déchiffrement de l'archive interne via yokai.exe pour produire un .zip.
      3. Troisième étape : ouverture du .zip et extraction de bl_yokaiID.png.
    Met en cache l'image extraite sous forme de fichier temporaire (dans DOSSIER_TEMP_ICONES par défaut).
    """
    if not chemin_ayd or not os.path.exists(chemin_ayd):
        return None

    if dossier_sauvegarde is None:
        dossier_sauvegarde = DOSSIER_TEMP_ICONES

    base_nom = f"bl_{yokai_id}"
    image_bytes = None

    try:
        if zipfile.is_zipfile(chemin_ayd):
            with zipfile.ZipFile(chemin_ayd, 'r') as zf:
                noms = zf.namelist()
                png_cands = [f for f in noms if f.lower().endswith('.png') and not f.lower().endswith('_o.png')]
                cibles = [f for f in png_cands if f.lower() == f"{base_nom}.png".lower()]
                if not cibles:
                    cibles = [f for f in png_cands if f.lower() == f"{yokai_id}.png".lower()]
                if not cibles:
                    cibles = [f for f in png_cands if f.lower().startswith("bl_")]
                if not cibles and png_cands:
                    cibles = png_cands

                if cibles:
                    image_bytes = zf.read(cibles[0])
                else:
                    interne_nom = None
                    for f in noms:
                        if f.lower().endswith(('.ayd', '.ez')):
                            interne_nom = f
                            break
                    if not interne_nom and noms:
                        interne_nom = noms[0]

                    if interne_nom:
                        inner_bytes = zf.read(interne_nom)
                        image_bytes = dechiffrer_donnees_avec_yokai(inner_bytes, base_nom, chemin_yokai_exe, yokai_id=yokai_id)
        else:
            with open(chemin_ayd, 'rb') as f:
                raw_bytes = f.read()
            image_bytes = dechiffrer_donnees_avec_yokai(raw_bytes, base_nom, chemin_yokai_exe, yokai_id=yokai_id)

    except Exception as e:
        print(f"Erreur extraction icône AYD ({chemin_ayd}): {e}")

    if image_bytes and dossier_sauvegarde and os.path.isdir(dossier_sauvegarde):
        try:
            cache_png = os.path.join(dossier_sauvegarde, f"{base_nom}.png")
            if not os.path.exists(cache_png):
                with open(cache_png, "wb") as f_out:
                    f_out.write(image_bytes)
        except Exception:
            pass

    return image_bytes
