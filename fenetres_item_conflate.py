# -*- coding: utf-8 -*-
"""
Fenêtres liées : Objets (ywp_mst_item) et Fusions (ywp_mst_conflate).

Module AUTONOME : il ne fait aucun `import mainFR13`. Le fichier principal lui passe
un petit "contexte" (dossier des mst, index serveur des PNG, thème, ...) :

    import fenetres_item_conflate as fic
    fic.ouvrir_menu(fenetre, contexte)     # contexte = fonction qui renvoie un dict

Le dict renvoyé par `contexte()` contient :
    dossier_mst   : dossier où se trouvent ywp_mst_item / ywp_mst_conflate (ou "")
    fichier_yokai : chemin de ywp_mst_youkai (pour résoudre les noms de Yo-kai)
    index_serveur : dict {nom_fichier_minuscule: chemin} pour retrouver les PNG
    dossier_ressources : dossier de secours où chercher les PNG
    theme         : dict de couleurs du thème actif
    lire          : lire_donnees_fichier(chemin) -> (texte_brut, donnees, est_compact)
    ecrire        : maj_fichier_original(chemin, lignes, id, ...)  (facultatif)

Règle du saut de ligne : en mémoire, un saut de ligne est TOUJOURS le vrai "\n".
Le texte lu depuis le fichier arrive déjà normalisé par `lire`.
Ordre de recherche des fichiers : .txt d'abord, puis .json.
"""
import io
import json
import os
import re
import tkinter as tk
from tkinter import messagebox, ttk, filedialog

try:
    from PIL import Image, ImageTk
except Exception:                      # Pillow absent : les fenêtres marchent sans aperçu PNG
    Image = ImageTk = None

# ------------------------------------------------------------------
# Constantes
# ------------------------------------------------------------------
NOM_ITEM = "ywp_mst_item"
NOM_CONFLATE = "ywp_mst_conflate"

# ywp_mst_item : 9 colonnes
CHAMPS_ITEM = [
    "ItemId", "Categorie", "Nom", "Valeur", "Sous-valeur",
    "Description", "IconePNG", "FichierEffet", "Drapeau",
]
# ywp_mst_conflate : 8 colonnes
CHAMPS_CONFLATE = [
    "ConflateId", "PrixYen",
    "TypeA", "IdA", "TypeB", "IdB", "TypeResultat", "IdResultat",
]

CATEGORIES_ITEM = {
    "1": "Exporb (XP)", "2": "Nourriture", "3": "Secrets d'Âmultime",
    "4": "Pièce Crank-a-kai", "5": "Objet d'évolution", "7": "Objet clé / accessoire",
    "8": "Charme (mini-jeu)", "9": "Pass / événement", "10": "Livre de compétence",
}
TYPES_ELEMENT = {"1": "Objet", "2": "Yo-kai"}          # type dans mst_conflate

# ------------------------------------------------------------------
# Utilitaires purs (testables sans interface)
# ------------------------------------------------------------------
_RE_NL = re.compile(r"\\+n")


def _nl(txt):
    """Vrai \\n interne (idempotent). Copie volontairement locale pour rester autonome."""
    if txt is None:
        return ""
    t = str(txt).replace("\r\n", "\n").replace("\r", "\n")
    return _RE_NL.sub("\n", t)


def _nettoyer_champ(txt):
    """Un champ ne doit contenir ni '|' ni '*' (séparateurs du format du jeu)."""
    return _nl(txt).replace("|", "").replace("*", "")


def parser_table(texte_brut, nb_colonnes):
    """texte_brut -> liste de listes de str, complétées/tronquées à nb_colonnes."""
    lignes = []
    for brut in (texte_brut or "").split("*"):
        if not brut.strip():
            continue
        cols = brut.split("|")
        cols = (cols + [""] * nb_colonnes)[:nb_colonnes]
        lignes.append(cols)
    return lignes


def doublons_id(lignes, index=0):
    """Renvoie {id: [positions]} pour les ID présents plusieurs fois."""
    vu = {}
    for pos, cols in enumerate(lignes):
        vu.setdefault(cols[index], []).append(pos)
    return {k: v for k, v in vu.items() if len(v) > 1}


def ligne_vers_texte(cols):
    return "|".join(_nl(c).replace("*", "") for c in cols)


def prochain_id(lignes, plancher=1, index=0):
    ids = []
    for cols in lignes:
        try:
            ids.append(int(cols[index]))
        except (ValueError, IndexError):
            pass
    return str(max(ids) + 1) if ids else str(plancher)


def valider_item(cols):
    """Renvoie la liste des problèmes (chaîne vide = OK)."""
    p = []
    if not cols[0].strip().isdigit():
        p.append("ItemId doit être un entier.")
    if not cols[1].strip().lstrip("-").isdigit():
        p.append("Catégorie doit être un entier.")
    if not cols[2].strip():
        p.append("Le nom est vide.")
    if not cols[6].strip():
        p.append("Aucun PNG d'icône référencé.")
    elif not cols[6].lower().endswith(".png"):
        p.append("L'icône doit être un fichier .png.")
    return p


def valider_conflate(cols, ids_items=None, ids_yokai=None):
    p = []
    for i in (0, 1, 3, 5, 7):
        if not cols[i].strip().lstrip("-").isdigit():
            p.append(f"{CHAMPS_CONFLATE[i]} doit être un entier.")
    for i in (2, 4, 6):
        if cols[i].strip() not in TYPES_ELEMENT:
            p.append(f"{CHAMPS_CONFLATE[i]} doit valoir 1 (objet) ou 2 (Yo-kai).")
    for t_i, id_i in ((2, 3), (4, 5), (6, 7)):
        t, ident = cols[t_i].strip(), cols[id_i].strip()
        if t == "1" and ids_items is not None and ident not in ids_items:
            p.append(f"{CHAMPS_CONFLATE[id_i]} : l'objet {ident} n'existe pas dans mst_item.")
        if t == "2" and ids_yokai is not None and ident not in ids_yokai:
            p.append(f"{CHAMPS_CONFLATE[id_i]} : le Yo-kai {ident} n'existe pas dans mst_youkai.")
    return p


def ecrire_table(chemin, lignes, lire):
    """Réécrit `chemin` en conservant son format (JSON compact/indenté, ou .txt brut).
    Autonome : n'appelle pas maj_fichier_original pour pouvoir REMPLACER toute la table."""
    _, donnees, est_compact = lire(chemin)
    texte = "*".join(ligne_vers_texte(c) for c in lignes)
    if donnees is None:                                   # .txt brut : \n littéral voulu
        with open(chemin, "w", encoding="utf-8") as f:
            f.write(texte.replace("\n", "\\" + "n"))
        return
    kw = {"ensure_ascii": False}
    if est_compact:
        kw["separators"] = (",", ":")
    else:
        kw["indent"] = 4
    if isinstance(donnees, dict):
        cle = next((c for c in ("tableData", "masterData", "data", "rows", "table") if c in donnees), None)
        if cle is None:
            raise ValueError("Structure JSON inconnue : aucune clé de table trouvée.")
        donnees[cle] = texte                              # json.dump échappe \n une seule fois
    else:
        donnees = texte
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(donnees, f, **kw)


def sauvegarde_bak(chemin):
    """Copie de sécurité unique (.bak) avant la 1re écriture de la session."""
    bak = chemin + ".bak"
    if not os.path.exists(bak):
        try:
            with open(chemin, "rb") as s, open(bak, "wb") as d:
                d.write(s.read())
        except OSError:
            pass


# ------------------------------------------------------------------
# Accès contexte
# ------------------------------------------------------------------
def _dossiers(ctx):
    """Liste des dossiers candidats (nouveau format `dossiers_mst`, ancien `dossier_mst`)."""
    ds = list(ctx.get("dossiers_mst") or [])
    if ctx.get("dossier_mst"):
        ds.append(ctx["dossier_mst"])
    return [d for d in ds if d]


def _trouver(nom, dossiers):
    """Cherche nom.txt PUIS nom.json dans chaque dossier, dans l'ordre. `dossiers` = str ou liste.
    Le .txt est prioritaire : c'est le fichier de travail de ces deux tables."""
    if not dossiers:
        return None
    if isinstance(dossiers, str):
        dossiers = [dossiers]
    for dossier in dossiers:
        for ext in (".txt", ".json"):
            c = os.path.join(dossier, nom + ext)
            if os.path.exists(c):
                return c
    return None


def _fichiers_en_double(nom, dossiers):
    """Liste de tous les fichiers nom.txt / nom.json existants (pour avertir si les deux sont là)."""
    if isinstance(dossiers, str):
        dossiers = [dossiers]
    return [os.path.join(d, nom + e) for d in (dossiers or []) for e in (".txt", ".json")
            if os.path.exists(os.path.join(d, nom + e))]


def _avertir_double(fenetre, nom, dossiers, choisi):
    """Si plusieurs fichiers existent pour la même table, dit lequel est utilisé."""
    autres = [f for f in _fichiers_en_double(nom, dossiers) if os.path.normpath(f) != os.path.normpath(choisi)]
    if autres:
        messagebox.showinfo(
            "Plusieurs fichiers trouvés",
            f"Fichier utilisé :\n{choisi}\n\nIgnoré(s) :\n- " + "\n- ".join(autres),
            parent=fenetre)


def _charger_yokai_noms(ctx):
    """{yokai_id: nom} depuis ywp_mst_youkai (colonnes 0 et 1)."""
    chemin = ctx.get("fichier_yokai") or ""
    if not chemin or not os.path.exists(chemin):
        return {}
    try:
        brut, _, _ = ctx["lire"](chemin)
    except Exception:
        return {}
    noms = {}
    for ligne in (brut or "").split("*"):
        cols = ligne.split("|")
        if len(cols) > 1 and cols[0].strip():
            noms[cols[0].strip()] = cols[1]
    return noms


def _chemin_png(nom_png, ctx):
    if not nom_png:
        return None
    idx = ctx.get("index_serveur") or {}
    c = idx.get(nom_png.lower())
    if c and os.path.exists(c):
        return c
    d = ctx.get("dossier_ressources") or ""
    if d:
        c = os.path.join(d, nom_png)
        if os.path.exists(c):
            return c
    return None


def _photo(chemin, taille=64):
    if Image is None or not chemin:
        return None
    try:
        img = Image.open(chemin).convert("RGBA")
        img.thumbnail((taille, taille))
        return ImageTk.PhotoImage(img)
    except Exception:
        return None


# ------------------------------------------------------------------
# Style commun
# ------------------------------------------------------------------
def _p(ctx):
    return ctx.get("theme") or {}


def _c(p, cle, defaut):
    return p.get(cle, defaut)


def _bouton(parent, ctx, texte, cmd, spec=False):
    p = _p(ctx)
    b = tk.Button(parent, text=texte, command=cmd, relief="flat", bd=1,
                  font=("Segoe UI", 9, "bold" if spec else "normal"),
                  bg=_c(p, "btn_special_bg" if spec else "btn_bg", "#eeeeee"),
                  fg=_c(p, "btn_special_fg" if spec else "btn_fg", "#000000"))
    return b


def _style_arbre(ctx):
    p = _p(ctx)
    s = ttk.Style()
    s.configure("FIC.Treeview", background=_c(p, "entry_bg", "#ffffff"),
                fieldbackground=_c(p, "entry_bg", "#ffffff"),
                foreground=_c(p, "entry_fg", "#000000"), rowheight=24)
    s.configure("FIC.Treeview.Heading", font=("Segoe UI", 9, "bold"))
    s.map("FIC.Treeview", background=[("selected", _c(p, "accent_glow", "#d36c99"))],
          foreground=[("selected", "#ffffff")])


def _fenetre(parent, ctx, titre, geo):
    p = _p(ctx)
    f = tk.Toplevel(parent)
    f.title(titre)
    f.geometry(geo)
    f.configure(bg=_c(p, "bg_main", "#f0f0f0"))
    _style_arbre(ctx)
    return f


def _label(parent, ctx, texte, gras=False, muted=False):
    p = _p(ctx)
    fg = _c(p, "text_muted" if muted else "text_main", "#000000")
    return tk.Label(parent, text=texte, bg=parent.cget("bg"), fg=fg,
                    font=("Segoe UI", 9, "bold" if gras else "normal"))


# ------------------------------------------------------------------
# Fenêtre OBJETS (ywp_mst_item)
# ------------------------------------------------------------------
class FenetreItems:
    def __init__(self, parent, ctx):
        self.ctx = ctx
        self.p = _p(ctx)
        self.chemin = _trouver(NOM_ITEM, _dossiers(ctx))
        if not self.chemin:
            messagebox.showerror("Introuvable",
                                 f"{NOM_ITEM} est introuvable dans le dossier des tables.\n"
                                 "Dossiers cherchés :\n- " + "\n- ".join(_dossiers(ctx) or ["(aucun)"]))
            return
        brut, _, _ = ctx["lire"](self.chemin)
        self.lignes = parser_table(brut, len(CHAMPS_ITEM))
        self.sel = None            # position (dans self.lignes) de la ligne en cours d'édition
        self.photo = None
        self.modifie = False

        self.win = _fenetre(parent, ctx, f"Objets — {self.chemin}", "1080x640")
        self.win.protocol("WM_DELETE_WINDOW", self.fermer)
        self._construire()
        self.rafraichir()
        _avertir_double(self.win, NOM_ITEM, _dossiers(ctx), self.chemin)

    def recharger(self, ctx=None):
        """Relit ywp_mst_item depuis le disque (perd les modifications non enregistrées)."""
        if ctx is not None:
            self.ctx = ctx
            nouveau = _trouver(NOM_ITEM, _dossiers(ctx))
            if nouveau:
                self.chemin = nouveau
        if self.modifie and not messagebox.askyesno(
                "Recharger", "Des modifications ne sont pas enregistrées.\nRelire le fichier et les perdre ?",
                parent=self.win):
            return
        brut, _, _ = self.ctx["lire"](self.chemin)
        self.lignes = parser_table(brut, len(CHAMPS_ITEM))
        self.sel, self.modifie = None, False
        self.win.title(f"Objets — {self.chemin}")
        self.rafraichir()

    # -- construction --
    def _construire(self):
        p, w = self.p, self.win
        haut = tk.Frame(w, bg=_c(p, "bg_main", "#f0f0f0"))
        haut.pack(fill=tk.X, padx=10, pady=(10, 4))
        _label(haut, self.ctx, "Recherche :", gras=True).pack(side=tk.LEFT)
        self.var_rech = tk.StringVar()
        self.var_rech.trace_add("write", lambda *_: self.rafraichir())
        tk.Entry(haut, textvariable=self.var_rech, width=26).pack(side=tk.LEFT, padx=6)
        _label(haut, self.ctx, "Catégorie :", gras=True).pack(side=tk.LEFT, padx=(12, 0))
        self.var_cat = tk.StringVar(value="Toutes")
        cb = ttk.Combobox(haut, textvariable=self.var_cat, state="readonly", width=24,
                          values=["Toutes"] + [f"{k} - {v}" for k, v in CATEGORIES_ITEM.items()])
        cb.pack(side=tk.LEFT, padx=6)
        cb.bind("<<ComboboxSelected>>", lambda e: self.rafraichir())
        self.lbl_stats = _label(haut, self.ctx, "", muted=True)
        self.lbl_stats.pack(side=tk.RIGHT)

        corps = tk.Frame(w, bg=_c(p, "bg_main", "#f0f0f0"))
        corps.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)

        # tableau
        gauche = tk.Frame(corps, bg=_c(p, "bg_main", "#f0f0f0"))
        gauche.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        cols = ("id", "cat", "nom", "png")
        self.arbre = ttk.Treeview(gauche, columns=cols, show="headings", style="FIC.Treeview",
                                  selectmode="browse")
        for c, t, l in (("id", "ID", 80), ("cat", "Catégorie", 150), ("nom", "Nom", 220), ("png", "PNG", 200)):
            self.arbre.heading(c, text=t)
            self.arbre.column(c, width=l, anchor="w")
        sb = ttk.Scrollbar(gauche, orient="vertical", command=self.arbre.yview)
        self.arbre.configure(yscrollcommand=sb.set)
        self.arbre.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.arbre.bind("<<TreeviewSelect>>", self._sur_selection)
        self.arbre.tag_configure("doublon", background="#ffd9d9")

        # formulaire
        droite = tk.LabelFrame(corps, text="  Édition  ", padx=10, pady=8,
                               bg=_c(p, "card_bg", "#ffffff"), fg=_c(p, "accent", "#c2185b"),
                               font=("Segoe UI", 10, "bold"))
        droite.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        self.cases = {}
        self.lbl_png = tk.Label(droite, text="Aucun aperçu", width=12, height=5,
                                bg=_c(p, "card_bg", "#ffffff"), fg=_c(p, "text_muted", "#666666"))
        self.lbl_png.grid(row=0, column=0, columnspan=2, pady=(0, 6))
        r = 1
        for i, nom in enumerate(CHAMPS_ITEM):
            tk.Label(droite, text=nom, bg=_c(p, "card_bg", "#ffffff"),
                     fg=_c(p, "text_main", "#000000"), font=("Segoe UI", 9)).grid(row=r, column=0, sticky="ne", padx=(0, 6), pady=3)
            if nom == "Description":
                e = tk.Text(droite, width=34, height=4, wrap="word", font=("Segoe UI", 9),
                            bg=_c(p, "entry_bg", "#ffffff"), fg=_c(p, "entry_fg", "#000000"), relief=tk.SOLID, bd=1)
            elif nom == "Categorie":
                e = ttk.Combobox(droite, width=32, values=[f"{k} - {v}" for k, v in CATEGORIES_ITEM.items()])
            else:
                e = tk.Entry(droite, width=36, bg=_c(p, "entry_bg", "#ffffff"), fg=_c(p, "entry_fg", "#000000"))
            e.grid(row=r, column=1, sticky="w", pady=3)
            self.cases[i] = e
            r += 1
        self.lbl_png_statut = tk.Label(droite, text="", bg=_c(p, "card_bg", "#ffffff"),
                                       fg=_c(p, "text_muted", "#666666"), font=("Segoe UI", 8))
        self.lbl_png_statut.grid(row=r, column=0, columnspan=2, sticky="w")
        self.cases[6].bind("<KeyRelease>", lambda e: self._maj_apercu())
        self.cases[6].bind("<FocusOut>", lambda e: self._maj_apercu())

        bas = tk.Frame(w, bg=_c(p, "bg_main", "#f0f0f0"))
        bas.pack(fill=tk.X, padx=10, pady=(4, 10))
        _bouton(bas, self.ctx, "➕ Nouvel objet", self.nouveau).pack(side=tk.LEFT, padx=(0, 6))
        _bouton(bas, self.ctx, "📋 Dupliquer", self.dupliquer).pack(side=tk.LEFT, padx=6)
        _bouton(bas, self.ctx, "🗑 Supprimer", self.supprimer).pack(side=tk.LEFT, padx=6)
        _bouton(bas, self.ctx, "🖼 Choisir un PNG…", self.choisir_png).pack(side=tk.LEFT, padx=6)
        _bouton(bas, self.ctx, "🔄 Recharger", lambda: self.recharger()).pack(side=tk.LEFT, padx=6)
        _bouton(bas, self.ctx, "💾 Enregistrer le fichier", self.enregistrer, spec=True).pack(side=tk.RIGHT)
        _bouton(bas, self.ctx, "✔ Appliquer à la ligne", self.appliquer).pack(side=tk.RIGHT, padx=6)

    # -- lecture/écriture des cases --
    def _lire_cases(self):
        cols = []
        for i in range(len(CHAMPS_ITEM)):
            w = self.cases[i]
            v = w.get("1.0", "end-1c") if isinstance(w, tk.Text) else w.get()
            if i == 1:
                v = v.split(" - ")[0].strip()
            cols.append(_nettoyer_champ(v).strip() if i != 5 else _nettoyer_champ(v))
        return cols

    def _remplir_cases(self, cols):
        for i, w in enumerate(self.cases.values()):
            v = cols[i] if cols else ""
            if isinstance(w, tk.Text):
                w.delete("1.0", tk.END)
                w.insert("1.0", v)
            elif i == 1 and isinstance(w, ttk.Combobox):
                w.set(f"{v} - {CATEGORIES_ITEM[v]}" if v in CATEGORIES_ITEM else v)
            else:
                w.delete(0, tk.END)
                w.insert(0, v)
        self._maj_apercu()

    def _maj_apercu(self):
        nom = self.cases[6].get().strip()
        chemin = _chemin_png(nom, self.ctx)
        self.photo = _photo(chemin)
        if self.photo:
            self.lbl_png.config(image=self.photo, text="", width=64, height=64)
            self.lbl_png_statut.config(text=f"PNG trouvé : {os.path.basename(chemin)}")
        else:
            self.lbl_png.config(image="", text="Aucun aperçu", width=12, height=5)
            self.lbl_png_statut.config(text="PNG introuvable dans le serveur/ressources." if nom else "")

    # -- tableau --
    def rafraichir(self):
        rech = self.var_rech.get().strip().lower()
        cat = self.var_cat.get().split(" - ")[0] if self.var_cat.get() != "Toutes" else None
        dbl = doublons_id(self.lignes)
        for i in self.arbre.get_children():
            self.arbre.delete(i)
        n = 0
        for pos, c in enumerate(self.lignes):
            if cat and c[1] != cat:
                continue
            if rech and rech not in c[0].lower() and rech not in c[2].lower() and rech not in c[6].lower():
                continue
            lib = CATEGORIES_ITEM.get(c[1], c[1])
            tags = ("doublon",) if c[0] in dbl else ()
            self.arbre.insert("", tk.END, iid=str(pos), values=(c[0], lib, c[2], c[6]), tags=tags)
            n += 1
        txt = f"{n}/{len(self.lignes)} objets"
        if dbl:
            txt += f"  ⚠ ID en double : {', '.join(sorted(dbl))}"
        self.lbl_stats.config(text=txt)

    def _sur_selection(self, event=None):
        s = self.arbre.selection()
        if not s:
            return
        self.sel = int(s[0])
        self._remplir_cases(self.lignes[self.sel])

    # -- actions --
    def appliquer(self):
        cols = self._lire_cases()
        pb = valider_item(cols)
        if pb:
            if not messagebox.askyesno("Vérification", "Problèmes détectés :\n- " + "\n- ".join(pb) +
                                       "\n\nAppliquer quand même ?", parent=self.win):
                return
        if self.sel is None:
            self.lignes.insert(0, cols)     # nouvelle ligne : au début (l'ordre n'importe pas hors mst_youkai)
            self.sel = 0
        else:
            self.lignes[self.sel] = cols
        self.modifie = True
        self.rafraichir()
        if str(self.sel) in self.arbre.get_children():
            self.arbre.selection_set(str(self.sel))

    def nouveau(self):
        self.sel = None
        self.arbre.selection_remove(self.arbre.selection())
        base = [prochain_id(self.lignes, 10001), "2", "", "1", "0", "", "", "", "0"]
        self._remplir_cases(base)

    def dupliquer(self):
        if self.sel is None:
            return messagebox.showinfo("Dupliquer", "Sélectionne d'abord un objet.", parent=self.win)
        c = list(self.lignes[self.sel])
        c[0] = prochain_id(self.lignes, 10001)
        self.sel = None
        self._remplir_cases(c)
        messagebox.showinfo("Dupliquer",
                            f"Copie prête avec le nouvel ID {c[0]}.\nClique « Appliquer à la ligne » pour l'ajouter.",
                            parent=self.win)

    def supprimer(self):
        if self.sel is None:
            return
        c = self.lignes[self.sel]
        if messagebox.askyesno("Supprimer", f"Supprimer l'objet {c[0]} — {c[2]} ?", parent=self.win):
            del self.lignes[self.sel]
            self.sel = None
            self.modifie = True
            self._remplir_cases(None)
            self.rafraichir()

    def choisir_png(self):
        ch = filedialog.askopenfilename(parent=self.win, title="Choisir le PNG de l'objet",
                                        filetypes=[("PNG", "*.png"), ("Tous", "*.*")])
        if ch:
            self.cases[6].delete(0, tk.END)
            self.cases[6].insert(0, os.path.basename(ch))
            # aperçu direct même si le fichier n'est pas encore dans le serveur
            self.photo = _photo(ch)
            if self.photo:
                self.lbl_png.config(image=self.photo, text="", width=64, height=64)
                self.lbl_png_statut.config(text="Aperçu du fichier choisi (pense à le copier dans dataDownload).")

    def enregistrer(self):
        dbl = doublons_id(self.lignes)
        if dbl and not messagebox.askyesno(
                "ID en double",
                f"Ces ID apparaissent plusieurs fois : {', '.join(sorted(dbl))}.\n"
                "Les deux lignes seront conservées telles quelles. Enregistrer ?", parent=self.win):
            return
        try:
            sauvegarde_bak(self.chemin)
            ecrire_table(self.chemin, self.lignes, self.ctx["lire"])
            self.modifie = False
            messagebox.showinfo("Enregistré", f"{len(self.lignes)} objets écrits dans :\n{self.chemin}", parent=self.win)
            cb = self.ctx.get("apres_ecriture")
            if cb:
                cb("item")
        except Exception as e:
            messagebox.showerror("Erreur d'écriture", str(e), parent=self.win)

    def fermer(self):
        if self.modifie and not messagebox.askyesno(
                "Modifications non enregistrées", "Fermer sans enregistrer ?", parent=self.win):
            return
        self.win.destroy()


# ------------------------------------------------------------------
# Fenêtre FUSIONS (ywp_mst_conflate)
# ------------------------------------------------------------------
class FenetreConflate:
    def __init__(self, parent, ctx):
        self.ctx = ctx
        self.p = _p(ctx)
        self.chemin = _trouver(NOM_CONFLATE, _dossiers(ctx))
        if not self.chemin:
            messagebox.showerror("Introuvable",
                                 f"{NOM_CONFLATE} est introuvable dans le dossier des tables.\n"
                                 "Dossiers cherchés :\n- " + "\n- ".join(_dossiers(ctx) or ["(aucun)"]))
            return
        brut, _, _ = ctx["lire"](self.chemin)
        self.lignes = parser_table(brut, len(CHAMPS_CONFLATE))

        # noms des objets (mst_item) et Yo-kai (mst_youkai)
        self.noms_items = {}
        ch_item = _trouver(NOM_ITEM, _dossiers(ctx))
        if ch_item:
            b, _, _ = ctx["lire"](ch_item)
            for c in parser_table(b, len(CHAMPS_ITEM)):
                self.noms_items.setdefault(c[0], c[2])      # 1re occurrence si ID en double
        self.noms_yokai = _charger_yokai_noms(ctx)

        self.sel = None
        self.modifie = False
        self.win = _fenetre(parent, ctx, f"Fusions — {self.chemin}", "1120x560")
        self.win.protocol("WM_DELETE_WINDOW", self.fermer)
        self._construire()
        self.rafraichir()
        _avertir_double(self.win, NOM_CONFLATE, _dossiers(ctx), self.chemin)

    def recharger(self, ctx=None):
        """Relit conflate + noms des objets/Yo-kai depuis le disque."""
        if ctx is not None:
            self.ctx = ctx
            nouveau = _trouver(NOM_CONFLATE, _dossiers(ctx))
            if nouveau:
                self.chemin = nouveau
        if self.modifie and not messagebox.askyesno(
                "Recharger", "Des modifications ne sont pas enregistrées.\nRelire le fichier et les perdre ?",
                parent=self.win):
            return
        brut, _, _ = self.ctx["lire"](self.chemin)
        self.lignes = parser_table(brut, len(CHAMPS_CONFLATE))
        self.noms_items = {}
        ch_item = _trouver(NOM_ITEM, _dossiers(self.ctx))
        if ch_item:
            b, _, _ = self.ctx["lire"](ch_item)
            for c in parser_table(b, len(CHAMPS_ITEM)):
                self.noms_items.setdefault(c[0], c[2])
        self.noms_yokai = _charger_yokai_noms(self.ctx)
        self.sel, self.modifie = None, False
        self.win.title(f"Fusions — {self.chemin}")
        self.rafraichir()

    def _nom(self, type_, ident):
        ident = ident.strip()
        if type_.strip() == "1":
            return self.noms_items.get(ident, "⚠ objet inconnu")
        if type_.strip() == "2":
            return self.noms_yokai.get(ident, "⚠ Yo-kai inconnu" if self.noms_yokai else "")
        return ""

    def _construire(self):
        p, w = self.p, self.win
        haut = tk.Frame(w, bg=_c(p, "bg_main", "#f0f0f0"))
        haut.pack(fill=tk.X, padx=10, pady=(10, 4))
        _label(haut, self.ctx, "Recherche (ID ou nom) :", gras=True).pack(side=tk.LEFT)
        self.var_rech = tk.StringVar()
        self.var_rech.trace_add("write", lambda *_: self.rafraichir())
        tk.Entry(haut, textvariable=self.var_rech, width=28).pack(side=tk.LEFT, padx=6)
        self.lbl_stats = _label(haut, self.ctx, "", muted=True)
        self.lbl_stats.pack(side=tk.RIGHT)

        corps = tk.Frame(w, bg=_c(p, "bg_main", "#f0f0f0"))
        corps.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)

        gauche = tk.Frame(corps, bg=_c(p, "bg_main", "#f0f0f0"))
        gauche.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        cols = ("id", "prix", "a", "b", "res")
        self.arbre = ttk.Treeview(gauche, columns=cols, show="headings", style="FIC.Treeview",
                                  selectmode="browse")
        for c, t, l in (("id", "ID", 60), ("prix", "Prix (¥)", 70), ("a", "Yo-kai / élément A", 190),
                        ("b", "Élément B", 190), ("res", "Résultat", 190)):
            self.arbre.heading(c, text=t)
            self.arbre.column(c, width=l, anchor="w")
        sb = ttk.Scrollbar(gauche, orient="vertical", command=self.arbre.yview)
        self.arbre.configure(yscrollcommand=sb.set)
        self.arbre.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.arbre.bind("<<TreeviewSelect>>", self._sur_selection)
        self.arbre.tag_configure("doublon", background="#ffd9d9")
        self.arbre.tag_configure("inconnu", background="#fff2cc")

        droite = tk.LabelFrame(corps, text="  Édition  ", padx=10, pady=8,
                               bg=_c(p, "card_bg", "#ffffff"), fg=_c(p, "accent", "#c2185b"),
                               font=("Segoe UI", 10, "bold"))
        droite.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        self.cases, self.noms_lbl = {}, {}
        bg = _c(p, "card_bg", "#ffffff")
        tk.Label(droite, text="ConflateId", bg=bg, fg=_c(p, "text_main", "#000")).grid(row=0, column=0, sticky="e", padx=(0, 6), pady=3)
        self.cases[0] = tk.Entry(droite, width=14); self.cases[0].grid(row=0, column=1, sticky="w")
        tk.Label(droite, text="Prix (yens)", bg=bg, fg=_c(p, "text_main", "#000")).grid(row=1, column=0, sticky="e", padx=(0, 6), pady=3)
        self.cases[1] = tk.Entry(droite, width=14); self.cases[1].grid(row=1, column=1, sticky="w")

        r = 2
        for etiquette, t_i, id_i in (("Élément A", 2, 3), ("Élément B", 4, 5), ("Résultat", 6, 7)):
            tk.Label(droite, text=etiquette, bg=bg, fg=_c(p, "accent", "#c2185b"),
                     font=("Segoe UI", 9, "bold")).grid(row=r, column=0, columnspan=2, sticky="w", pady=(10, 0))
            r += 1
            tk.Label(droite, text="Type", bg=bg, fg=_c(p, "text_main", "#000")).grid(row=r, column=0, sticky="e", padx=(0, 6))
            cb = ttk.Combobox(droite, width=14, state="readonly", values=["1 - Objet", "2 - Yo-kai"])
            cb.grid(row=r, column=1, sticky="w", pady=2)
            self.cases[t_i] = cb
            r += 1
            tk.Label(droite, text="ID", bg=bg, fg=_c(p, "text_main", "#000")).grid(row=r, column=0, sticky="e", padx=(0, 6))
            e = tk.Entry(droite, width=14)
            e.grid(row=r, column=1, sticky="w", pady=2)
            self.cases[id_i] = e
            r += 1
            lbl = tk.Label(droite, text="", bg=bg, fg=_c(p, "text_muted", "#666"), font=("Segoe UI", 8, "italic"),
                           wraplength=240, justify="left")
            lbl.grid(row=r, column=0, columnspan=2, sticky="w")
            self.noms_lbl[id_i] = (t_i, lbl)
            e.bind("<KeyRelease>", lambda ev: self._maj_noms())
            cb.bind("<<ComboboxSelected>>", lambda ev: self._maj_noms())
            r += 1

        bas = tk.Frame(w, bg=_c(p, "bg_main", "#f0f0f0"))
        bas.pack(fill=tk.X, padx=10, pady=(4, 10))
        _bouton(bas, self.ctx, "➕ Nouvelle fusion", self.nouveau).pack(side=tk.LEFT, padx=(0, 6))
        _bouton(bas, self.ctx, "📋 Dupliquer", self.dupliquer).pack(side=tk.LEFT, padx=6)
        _bouton(bas, self.ctx, "🗑 Supprimer", self.supprimer).pack(side=tk.LEFT, padx=6)
        _bouton(bas, self.ctx, "🔄 Recharger", lambda: self.recharger()).pack(side=tk.LEFT, padx=6)
        _bouton(bas, self.ctx, "💾 Enregistrer le fichier", self.enregistrer, spec=True).pack(side=tk.RIGHT)
        _bouton(bas, self.ctx, "✔ Appliquer à la ligne", self.appliquer).pack(side=tk.RIGHT, padx=6)

    def _maj_noms(self):
        for id_i, (t_i, lbl) in self.noms_lbl.items():
            t = self.cases[t_i].get().split(" - ")[0]
            ident = self.cases[id_i].get()
            lbl.config(text=self._nom(t, ident) if ident.strip() else "")

    def _lire_cases(self):
        cols = []
        for i in range(len(CHAMPS_CONFLATE)):
            v = self.cases[i].get()
            if i in (2, 4, 6):
                v = v.split(" - ")[0]
            cols.append(_nettoyer_champ(v).strip())
        return cols

    def _remplir_cases(self, cols):
        for i in range(len(CHAMPS_CONFLATE)):
            w = self.cases[i]
            v = cols[i] if cols else ""
            if isinstance(w, ttk.Combobox):
                w.set(f"{v} - {TYPES_ELEMENT[v]}" if v in TYPES_ELEMENT else "")
            else:
                w.delete(0, tk.END)
                w.insert(0, v)
        self._maj_noms()

    def rafraichir(self):
        rech = self.var_rech.get().strip().lower()
        dbl = doublons_id(self.lignes)
        for i in self.arbre.get_children():
            self.arbre.delete(i)
        n = 0
        for pos, c in enumerate(self.lignes):
            na, nb, nr = self._nom(c[2], c[3]), self._nom(c[4], c[5]), self._nom(c[6], c[7])
            texte = " ".join([c[0], c[3], c[5], c[7], na, nb, nr]).lower()
            if rech and rech not in texte:
                continue
            aff = lambda t, i, nom: f"{i}  {nom}".strip() if nom else i
            tags = []
            if c[0] in dbl:
                tags.append("doublon")
            if any("⚠" in x for x in (na, nb, nr)):
                tags.append("inconnu")
            self.arbre.insert("", tk.END, iid=str(pos), tags=tuple(tags), values=(
                c[0], c[1], aff(c[2], c[3], na), f"[{TYPES_ELEMENT.get(c[4], '?')}] " + aff(c[4], c[5], nb),
                aff(c[6], c[7], nr)))
            n += 1
        txt = f"{n}/{len(self.lignes)} fusions"
        if dbl:
            txt += f"  ⚠ ID en double : {', '.join(sorted(dbl))}"
        self.lbl_stats.config(text=txt)

    def _sur_selection(self, event=None):
        s = self.arbre.selection()
        if not s:
            return
        self.sel = int(s[0])
        self._remplir_cases(self.lignes[self.sel])

    def appliquer(self):
        cols = self._lire_cases()
        pb = valider_conflate(cols, ids_items=set(self.noms_items) if self.noms_items else None,
                              ids_yokai=set(self.noms_yokai) if self.noms_yokai else None)
        if cols[0] in {c[0] for i, c in enumerate(self.lignes) if i != self.sel}:
            pb.append(f"Le ConflateId {cols[0]} existe déjà.")
        if pb and not messagebox.askyesno("Vérification", "Problèmes détectés :\n- " + "\n- ".join(pb) +
                                          "\n\nAppliquer quand même ?", parent=self.win):
            return
        if self.sel is None:
            self.lignes.insert(0, cols)
            self.sel = 0
        else:
            self.lignes[self.sel] = cols
        self.modifie = True
        self.rafraichir()
        if str(self.sel) in self.arbre.get_children():
            self.arbre.selection_set(str(self.sel))

    def nouveau(self):
        self.sel = None
        self.arbre.selection_remove(self.arbre.selection())
        self._remplir_cases([prochain_id(self.lignes, 1001), "500", "2", "", "2", "", "2", ""])

    def dupliquer(self):
        if self.sel is None:
            return messagebox.showinfo("Dupliquer", "Sélectionne d'abord une fusion.", parent=self.win)
        c = list(self.lignes[self.sel])
        c[0] = prochain_id(self.lignes, 1001)
        self.sel = None
        self._remplir_cases(c)

    def supprimer(self):
        if self.sel is None:
            return
        c = self.lignes[self.sel]
        if messagebox.askyesno("Supprimer", f"Supprimer la fusion {c[0]} ?", parent=self.win):
            del self.lignes[self.sel]
            self.sel = None
            self.modifie = True
            self._remplir_cases(None)
            self.rafraichir()

    def enregistrer(self):
        try:
            sauvegarde_bak(self.chemin)
            ecrire_table(self.chemin, self.lignes, self.ctx["lire"])
            self.modifie = False
            messagebox.showinfo("Enregistré", f"{len(self.lignes)} fusions écrites dans :\n{self.chemin}", parent=self.win)
            cb = self.ctx.get("apres_ecriture")
            if cb:
                cb("conflate")
        except Exception as e:
            messagebox.showerror("Erreur d'écriture", str(e), parent=self.win)

    def fermer(self):
        if self.modifie and not messagebox.askyesno(
                "Modifications non enregistrées", "Fermer sans enregistrer ?", parent=self.win):
            return
        self.win.destroy()


# ------------------------------------------------------------------
# Point d'entrée : petit menu qui ouvre les fenêtres liées
# ------------------------------------------------------------------
_OUVERTES = {}


def _ouvrir_unique(cle, classe, parent, ctx):
    """Une seule instance par fenêtre : si déjà ouverte, on la ramène au premier plan."""
    inst = _OUVERTES.get(cle)
    if inst is not None:
        try:
            if inst.win.winfo_exists():
                inst.win.deiconify()
                inst.win.lift()
                inst.win.focus_force()
                inst.recharger(ctx)          # relit le fichier : voit les lignes ajoutées depuis
                return
        except Exception:
            pass
    inst = classe(parent, ctx)
    if getattr(inst, "win", None) is not None:
        _OUVERTES[cle] = inst


def ouvrir_menu(parent, contexte):
    """Ouvre le petit menu des fenêtres liées. `contexte` = fonction -> dict (relu à chaque clic,
    pour suivre un changement de dossier ou de thème)."""
    ctx = contexte()
    p = ctx.get("theme") or {}
    m = tk.Toplevel(parent)
    m.title("Fenêtres liées")
    m.geometry("340x200")
    m.configure(bg=_c(p, "bg_main", "#f0f0f0"))
    m.transient(parent)
    tk.Label(m, text="Tables liées", font=("Segoe UI", 11, "bold"),
             bg=_c(p, "bg_main", "#f0f0f0"), fg=_c(p, "accent", "#c2185b")).pack(pady=(14, 8))

    def lancer(cle, classe):
        _ouvrir_unique(cle, classe, parent, contexte())

    _bouton(m, ctx, "🎒 Objets  (ywp_mst_item)", lambda: lancer("item", FenetreItems), spec=True).pack(fill=tk.X, padx=28, pady=5)
    _bouton(m, ctx, "🔀 Fusions  (ywp_mst_conflate)", lambda: lancer("conflate", FenetreConflate), spec=True).pack(fill=tk.X, padx=28, pady=5)
    _bouton(m, ctx, "Fermer", m.destroy).pack(fill=tk.X, padx=28, pady=(10, 5))
    return m
