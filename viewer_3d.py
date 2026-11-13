# -*- coding: utf-8 -*-
"""
Module de visualisation 3D avancée avec animations (SGF YMD / WebGL / fbxtoymdUltra).
Permet la lecture complète de toutes les animations squelettiques (Idle, Attaque, Dégâts, Âmultime),
le contrôle temporel (Play, Pause, Scrubber, Vitesse), l'affichage du squelette, fil de fer et textures.
"""

import os
import io
import re
import json
import zipfile
import threading
import webbrowser
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import ymd

# État global du serveur de visualisation
SERVEUR_ACTIF = None
PORT_SERVEUR = 8790
THREAD_SERVEUR = None
CONTEXTE_VISUALISEUR = {
    "dossier_ressources": "",
    "dossier_serveur": "",
    "index_serveur": {},
    "chemin_yokai_exe": "",
    "f_traiter_ez": None,
    "nom_yokai_getter": None,
}

CACHE_SCENES = {}
CACHE_TEXTURES = {}


def localiser_fichiers_3d(yokai_id, dossier_ressources, dossier_serveur, index_serveur):
    """Localise le fichier 3D (.ayd, .ez ou .ymd) pour le Yo-kai."""
    fichier_ayd = os.path.abspath(os.path.join(dossier_ressources, f"{yokai_id}.ayd"))
    fichier_ez = os.path.abspath(os.path.join(dossier_ressources, f"{yokai_id}.ez"))
    fichier_ymd = os.path.abspath(os.path.join(dossier_ressources, f"{yokai_id}.ymd"))

    if dossier_serveur:
        fichier_ayd = index_serveur.get(f"{yokai_id}.ayd".lower(), fichier_ayd)
        fichier_ez = index_serveur.get(f"{yokai_id}.ez".lower(), fichier_ez)
        fichier_ymd = index_serveur.get(f"{yokai_id}.ymd".lower(), fichier_ymd)

    return fichier_ayd, fichier_ez, fichier_ymd


def extraire_donnees_yokai(yokai_id, dossier_ressources, dossier_serveur, index_serveur,
                           chemin_yokai_exe, f_traiter_ez):
    """
    Extrait les octets du fichier YMD ainsi que l'ensemble des textures PNG associées.
    Supporte les formats .ayd (archive zip directe), .ez (archive compressée Level-5 via yokai.exe)
    et les fichiers .ymd bruts.
    """
    if yokai_id in CACHE_SCENES and yokai_id in CACHE_TEXTURES:
        return CACHE_SCENES[yokai_id], CACHE_TEXTURES[yokai_id]

    fichier_ayd, fichier_ez, fichier_ymd = localiser_fichiers_3d(
        yokai_id, dossier_ressources, dossier_serveur, index_serveur
    )

    ymd_bytes = None
    png_files = {}

    if os.path.exists(fichier_ayd):
        with zipfile.ZipFile(fichier_ayd, 'r') as zf:
            fichiers = zf.namelist()
            ymd_cands = [f for f in fichiers if f.lower().endswith('.ymd')]
            for f in fichiers:
                if f.lower().endswith('.png'):
                    png_files[os.path.basename(f)] = zf.read(f)
            if ymd_cands:
                ymd_bytes = zf.read(max(ymd_cands, key=lambda f: zf.getinfo(f).file_size))
            else:
                # Contient peut-être un .ez interne
                ez_nom = next((f for f in fichiers if f.lower().endswith('.ez')), None)
                if ez_nom and f_traiter_ez:
                    dir_tmp = os.path.dirname(os.path.abspath(chemin_yokai_exe)) if chemin_yokai_exe else dossier_ressources
                    temp_ez = os.path.join(dir_tmp, f"temp_{yokai_id}.ez")
                    with open(temp_ez, "wb") as f_out:
                        f_out.write(zf.read(ez_nom))
                    zip_gen = f_traiter_ez(chemin_yokai_exe, temp_ez)
                    if zip_gen and os.path.exists(zip_gen):
                        with zipfile.ZipFile(zip_gen, 'r') as zf_d:
                            for f in zf_d.namelist():
                                if f.lower().endswith('.ymd'):
                                    ymd_bytes = zf_d.read(f)
                                elif f.lower().endswith('.png'):
                                    png_files[os.path.basename(f)] = zf_d.read(f)
                    if os.path.exists(temp_ez):
                        try: os.remove(temp_ez)
                        except OSError: pass

    elif os.path.exists(fichier_ez):
        if not f_traiter_ez or not chemin_yokai_exe or not os.path.exists(chemin_yokai_exe):
            raise ValueError("yokai.exe est nécessaire pour décompresser les fichiers .ez mais n'est pas configuré.")
        zip_gen = f_traiter_ez(chemin_yokai_exe, fichier_ez)
        if zip_gen and os.path.exists(zip_gen):
            with zipfile.ZipFile(zip_gen, 'r') as zf:
                for f in zf.namelist():
                    if f.lower().endswith('.ymd'):
                        ymd_bytes = zf.read(f)
                    elif f.lower().endswith('.png'):
                        png_files[os.path.basename(f)] = zf.read(f)

    elif os.path.exists(fichier_ymd):
        with open(fichier_ymd, 'rb') as f:
            ymd_bytes = f.read()
        # Rechercher d'éventuelles textures PNG dans le même répertoire
        rep_ymd = os.path.dirname(fichier_ymd)
        for nom in os.listdir(rep_ymd):
            if nom.lower().startswith(str(yokai_id)) and nom.lower().endswith('.png'):
                with open(os.path.join(rep_ymd, nom), 'rb') as pf:
                    png_files[nom] = pf.read()

    if not ymd_bytes:
        raise ValueError(f"Fichier 3D (.ayd, .ez ou .ymd) introuvable pour le Yo-kai {yokai_id}.")

    scene = ymd.loads(ymd_bytes)
    CACHE_SCENES[yokai_id] = scene
    CACHE_TEXTURES[yokai_id] = png_files
    return scene, png_files


def resoudre_texture(req_name, png_dict):
    """Associe intelligemment le nom de texture demandé dans le YMD aux fichiers PNG extraits."""
    req_clean = os.path.basename(req_name).lower()
    req_stem = os.path.splitext(req_clean)[0]

    # 1. Correspondance exacte
    for name, data in png_dict.items():
        if name.lower() == req_clean or os.path.splitext(name.lower())[0] == req_stem:
            return data

    # 2. Correspondance par suffixe (_01a, _01, _02a, etc.)
    m_suf = re.search(r'(_\d+[a-z]?)$', req_stem)
    if m_suf:
        suf = m_suf.group(1)
        for name, data in png_dict.items():
            if name.lower().endswith(suf + '.png'):
                return data

    # 3. Correspondance sans le préfixe 'x' ou 'y'
    sans_prefixe = re.sub(r'^[xy]', '', req_stem)
    for name, data in png_dict.items():
        if sans_prefixe in name.lower():
            return data

    # 4. Repli sur la première texture disponible
    if png_dict:
        return next(iter(png_dict.values()))

    return None


class HandlerVisualiseur3D(BaseHTTPRequestHandler):
    """Serveur HTTP léger pour servir le visualiseur WebGL 3D et les animations."""

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        chemin = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        dossier_assets = os.path.join(os.path.dirname(os.path.abspath(__file__)), "viewer_assets")

        if chemin in ('/', '/index.html'):
            self.servir_fichier(os.path.join(dossier_assets, "index.html"), "text/html; charset=utf-8")
        elif chemin == '/style.css':
            self.servir_fichier(os.path.join(dossier_assets, "style.css"), "text/css; charset=utf-8")
        elif chemin == '/viewer.js':
            self.servir_fichier(os.path.join(dossier_assets, "viewer.js"), "application/javascript; charset=utf-8")
        elif chemin == '/api/scene':
            yokai_id = query.get('yokai', ['1181000'])[0].strip()
            try:
                scene, _ = extraire_donnees_yokai(
                    yokai_id,
                    CONTEXTE_VISUALISEUR["dossier_ressources"],
                    CONTEXTE_VISUALISEUR["dossier_serveur"],
                    CONTEXTE_VISUALISEUR["index_serveur"],
                    CONTEXTE_VISUALISEUR["chemin_yokai_exe"],
                    CONTEXTE_VISUALISEUR["f_traiter_ez"]
                )
                nom_yokai = ""
                if CONTEXTE_VISUALISEUR["nom_yokai_getter"]:
                    nom_yokai = CONTEXTE_VISUALISEUR["nom_yokai_getter"](yokai_id)

                reponse = {
                    "scene": scene,
                    "metadata": {
                        "id": yokai_id,
                        "name": nom_yokai,
                        "clips": len(scene.get("clips", []))
                    }
                }
                corps = json.dumps(reponse).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(corps)))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(corps)
            except Exception as e:
                erreur = json.dumps({"error": str(e)}).encode('utf-8')
                self.send_response(404)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(erreur)))
                self.end_headers()
                self.wfile.write(erreur)

        elif chemin.startswith('/api/texture/'):
            # Chemin attendu : /api/texture/<yokai_id>/<nom_texture>
            parties = chemin.strip('/').split('/')
            if len(parties) >= 4:
                yokai_id = parties[2]
                nom_texture = parties[3]
                try:
                    _, textures = extraire_donnees_yokai(
                        yokai_id,
                        CONTEXTE_VISUALISEUR["dossier_ressources"],
                        CONTEXTE_VISUALISEUR["dossier_serveur"],
                        CONTEXTE_VISUALISEUR["index_serveur"],
                        CONTEXTE_VISUALISEUR["chemin_yokai_exe"],
                        CONTEXTE_VISUALISEUR["f_traiter_ez"]
                    )
                    octets_png = resoudre_texture(nom_texture, textures)
                    if octets_png:
                        self.send_response(200)
                        self.send_header('Content-Type', 'image/png')
                        self.send_header('Content-Length', str(len(octets_png)))
                        self.send_header('Cache-Control', 'public, max-age=86400')
                        self.end_headers()
                        self.wfile.write(octets_png)
                        return
                except Exception:
                    pass
            self.send_response(404)
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def servir_fichier(self, chemin_fichier, type_mime):
        if os.path.exists(chemin_fichier):
            with open(chemin_fichier, 'rb') as f:
                contenu = f.read()
            self.send_response(200)
            self.send_header('Content-Type', type_mime)
            self.send_header('Content-Length', str(len(contenu)))
            self.end_headers()
            self.wfile.write(contenu)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Désactiver les logs d'accès réseau pour garder la console propre
        pass


def demarrer_serveur_3d():
    """Démarre le serveur HTTP local pour le visualiseur WebGL dans un thread démon."""
    global SERVEUR_ACTIF, THREAD_SERVEUR, PORT_SERVEUR
    if SERVEUR_ACTIF is not None:
        return PORT_SERVEUR

    for port_candidat in range(8790, 8805):
        try:
            SERVEUR_ACTIF = ThreadingHTTPServer(('127.0.0.1', port_candidat), HandlerVisualiseur3D)
            PORT_SERVEUR = port_candidat
            THREAD_SERVEUR = threading.Thread(target=SERVEUR_ACTIF.serve_forever, daemon=True)
            THREAD_SERVEUR.start()
            return PORT_SERVEUR
        except OSError:
            continue

    raise RuntimeError("Impossible de démarrer le serveur 3D (aucun port libre entre 8790 et 8805).")


def ouvrir_viewer_3d(yokai_id, dossier_ressources, dossier_serveur, index_serveur,
                     chemin_yokai_exe, f_traiter_ez, nom_yokai_getter=None):
    """
    Lance le visualiseur 3D interactif avec support intégral des animations squelettiques.
    Vérifie l'existence des assets 3D pour le Yo-kai et ouvre la page WebGL dans le navigateur.
    Retourne (succes: bool, message: str).
    """
    if not yokai_id:
        return False, "Veuillez d'abord sélectionner un Yo-kai."

    # Mettre à jour le contexte global
    CONTEXTE_VISUALISEUR["dossier_ressources"] = dossier_ressources
    CONTEXTE_VISUALISEUR["dossier_serveur"] = dossier_serveur
    CONTEXTE_VISUALISEUR["index_serveur"] = index_serveur or {}
    CONTEXTE_VISUALISEUR["chemin_yokai_exe"] = chemin_yokai_exe
    CONTEXTE_VISUALISEUR["f_traiter_ez"] = f_traiter_ez
    CONTEXTE_VISUALISEUR["nom_yokai_getter"] = nom_yokai_getter

    # Vérification préalable de la présence d'un fichier 3D
    fichier_ayd, fichier_ez, fichier_ymd = localiser_fichiers_3d(
        yokai_id, dossier_ressources, dossier_serveur, index_serveur
    )
    if not any(os.path.exists(p) for p in (fichier_ayd, fichier_ez, fichier_ymd)):
        return False, (
            f"Aucun fichier 3D (.ayd, .ez ou .ymd) trouvé pour l'ID '{yokai_id}'.\n\n"
            f"Vérifiez que le fichier existe dans votre dossier Ressources :\n"
            f"{os.path.abspath(dossier_ressources)}"
        )

    # Pré-extraire et valider les données 3D
    try:
        scene, _ = extraire_donnees_yokai(
            yokai_id, dossier_ressources, dossier_serveur, index_serveur,
            chemin_yokai_exe, f_traiter_ez
        )
        nb_clips = len(scene.get("clips", []))
    except Exception as e:
        return False, f"Erreur lors du chargement 3D du Yo-kai {yokai_id} :\n{e}"

    # Démarrer le serveur et ouvrir la page
    try:
        port = demarrer_serveur_3d()
        url = f"http://127.0.0.1:{port}/?yokai={urllib.parse.quote(str(yokai_id))}"
        webbrowser.open(url)
        return True, f"Visualiseur 3D ouvert avec {nb_clips} animations disponibles !"
    except Exception as e:
        return False, f"Erreur lors du lancement du visualiseur 3D :\n{e}"
