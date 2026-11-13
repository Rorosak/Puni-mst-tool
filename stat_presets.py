# -*- coding: utf-8 -*-
"""
Module de modèles de statistiques (Stat Presets) et validation de cohérence.
"""

# Modèles de statistiques moyennes/typiques par rang pour Yo-kai Watch Puni Puni / WibWob
STAT_PRESETS = {
    "1":  {"rang": "E",   "nom": "Rang E",   "max_level": 50, "base_hp": 90,   "max_hp": 260,  "base_atk": 70,  "max_atk": 210},
    "2":  {"rang": "D",   "nom": "Rang D",   "max_level": 50, "base_hp": 130,  "max_hp": 340,  "base_atk": 100, "max_atk": 280},
    "3":  {"rang": "C",   "nom": "Rang C",   "max_level": 50, "base_hp": 170,  "max_hp": 430,  "base_atk": 130, "max_atk": 360},
    "4":  {"rang": "B",   "nom": "Rang B",   "max_level": 50, "base_hp": 220,  "max_hp": 520,  "base_atk": 170, "max_atk": 440},
    "5":  {"rang": "A",   "nom": "Rang A",   "max_level": 50, "base_hp": 280,  "max_hp": 630,  "base_atk": 220, "max_atk": 530},
    "6":  {"rang": "S",   "nom": "Rang S",   "max_level": 50, "base_hp": 360,  "max_hp": 760,  "base_atk": 280, "max_atk": 640},
    "7":  {"rang": "SS",  "nom": "Rang SS",  "max_level": 50, "base_hp": 450,  "max_hp": 920,  "base_atk": 360, "max_atk": 780},
    "8":  {"rang": "SSS", "nom": "Rang SSS", "max_level": 50, "base_hp": 560,  "max_hp": 1120, "base_atk": 450, "max_atk": 940},
    "9":  {"rang": "Z",   "nom": "Rang Z",   "max_level": 60, "base_hp": 680,  "max_hp": 1340, "base_atk": 560, "max_atk": 1140},
    "10": {"rang": "ZZ",  "nom": "Rang ZZ",  "max_level": 70, "base_hp": 820,  "max_hp": 1580, "base_atk": 680, "max_atk": 1360},
    "11": {"rang": "ZZZ", "nom": "Rang ZZZ", "max_level": 80, "base_hp": 980,  "max_hp": 1840, "base_atk": 810, "max_atk": 1600},
    "12": {"rang": "UZ",  "nom": "Rang UZ",  "max_level": 90, "base_hp": 1180, "max_hp": 2180, "base_atk": 960, "max_atk": 1880},
}


def get_stat_preset(rank_id):
    """Retourne le preset de statistiques pour un rang donné (1 à 12)."""
    return STAT_PRESETS.get(str(rank_id))


def verifier_coherence_stats(base_hp_val, max_hp_val, base_atk_val, max_atk_val):
    """
    Vérifie la cohérence des statistiques de combat.
    Retourne (est_valide, liste_erreurs, liste_avertissements).
    """
    erreurs = []
    avertissements = []

    def vers_int(val, nom):
        s = str(val).strip()
        if not s:
            return None
        try:
            return int(s)
        except ValueError:
            erreurs.append(f"Le champ {nom} ('{s}') doit être un entier valide.")
            return None

    bhp = vers_int(base_hp_val, "BaseHp (champ 8)")
    mhp = vers_int(max_hp_val, "MaxHp (champ 9)")
    batk = vers_int(base_atk_val, "BaseAtk (champ 10)")
    matk = vers_int(max_atk_val, "MaxAtk (champ 11)")

    if bhp is not None and bhp < 0:
        erreurs.append("BaseHp ne peut pas être négatif.")
    if mhp is not None and mhp < 0:
        erreurs.append("MaxHp ne peut pas être négatif.")
    if batk is not None and batk < 0:
        erreurs.append("BaseAtk ne peut pas être négatif.")
    if matk is not None and matk < 0:
        erreurs.append("MaxAtk ne peut pas être négatif.")

    if bhp is not None and mhp is not None and bhp > mhp:
        erreurs.append(f"Incohérence HP : BaseHp ({bhp}) est supérieur à MaxHp ({mhp}) !")

    if batk is not None and matk is not None and batk > matk:
        erreurs.append(f"Incohérence ATK : BaseAtk ({batk}) est supérieur à MaxAtk ({matk}) !")

    if bhp is not None and mhp is not None and bhp == mhp and bhp > 0:
        avertissements.append("BaseHp et MaxHp sont identiques (pas de progression de PV).")

    if batk is not None and matk is not None and batk == matk and batk > 0:
        avertissements.append("BaseAtk et MaxAtk sont identiques (pas de progression d'Attaque).")

    est_valide = len(erreurs) == 0
    return est_valide, erreurs, avertissements
