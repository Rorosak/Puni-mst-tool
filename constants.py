# -*- coding: utf-8 -*-
"""
Constantes et tables de correspondance pour l'outil Mst Tool (Yo-kai Watch Puni Puni & WibWob).
"""

COORDONNEES_KINDS = {str(i): ((i - 1) % 3, (i - 1) // 3) for i in range(1, 13)}
# Inversion 9 (Enma) et 10 (Kaima / Wicked)
COORDONNEES_KINDS["9"], COORDONNEES_KINDS["10"] = COORDONNEES_KINDS["10"], COORDONNEES_KINDS["9"]

COORDONNEES_RANGS = {
    "1": (2, 0), "2": (3, 0), "3": (4, 0), "4": (5, 0),
    "5": (6, 0), "6": (7, 0), "7": (0, 1), "8": (2, 1),
    "9": (4, 1), "10": (6, 1), "11": (0, 2), "12": (2, 2)
}

KIND_NAMES = {
    "1": {"nom": "Brave (Isamashi)", "en": "Brave", "alias": ["brave", "isamashi", "vaillant"]},
    "2": {"nom": "Mystérieux (Fushigi)", "en": "Mysterious", "alias": ["mysterieux", "mysterious", "fushigi"]},
    "3": {"nom": "Robuste (Goketsu)", "en": "Tough", "alias": ["robuste", "tough", "goketsu", "costaud"]},
    "4": {"nom": "Mignon (Purichi)", "en": "Charming", "alias": ["mignon", "charming", "purichi", "charmant"]},
    "5": {"nom": "Bienveillant (Pokapoka)", "en": "Heartful", "alias": ["bienveillant", "heartful", "pokapoka"]},
    "6": {"nom": "Sombre (Usurakage)", "en": "Shady", "alias": ["sombre", "shady", "usurakage"]},
    "7": {"nom": "Sinistre (Bukimi)", "en": "Eerie", "alias": ["sinistre", "eerie", "bukimi"]},
    "8": {"nom": "Insaisissable (Nyororon)", "en": "Slippery", "alias": ["insaisissable", "slippery", "nyororon"]},
    "9": {"nom": "Enma", "en": "Enma", "alias": ["enma", "lord enma"]},
    "10": {"nom": "Kaima (Wicked)", "en": "Wicked", "alias": ["kaima", "wicked", "malefique"]},
    "11": {"nom": "Hagure (Wanderer)", "en": "Hagure", "alias": ["hagure", "wanderer"]},
    "12": {"nom": "Kuroi / Boss", "en": "Kuroi", "alias": ["kuroi", "boss"]}
}

RANK_NAMES = {
    "1": {"nom": "Rang E", "court": "E", "alias": ["e", "rang e"]},
    "2": {"nom": "Rang D", "court": "D", "alias": ["d", "rang d"]},
    "3": {"nom": "Rang C", "court": "C", "alias": ["c", "rang c"]},
    "4": {"nom": "Rang B", "court": "B", "alias": ["b", "rang b"]},
    "5": {"nom": "Rang A", "court": "A", "alias": ["a", "rang a"]},
    "6": {"nom": "Rang S", "court": "S", "alias": ["s", "rang s"]},
    "7": {"nom": "Rang SS", "court": "SS", "alias": ["ss", "rang ss"]},
    "8": {"nom": "Rang SSS", "court": "SSS", "alias": ["sss", "rang sss"]},
    "9": {"nom": "Rang Z", "court": "Z", "alias": ["z", "rang z"]},
    "10": {"nom": "Rang ZZ", "court": "ZZ", "alias": ["zz", "rang zz"]},
    "11": {"nom": "Rang ZZZ", "court": "ZZZ", "alias": ["zzz", "rang zzz"]},
    "12": {"nom": "Rang UZ", "court": "UZ", "alias": ["uz", "rang uz"]}
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
    "64": "DirectAttackerFeverScaling", "65": "AllPopperAndStunner", "66": "ExtremePopper",
    "67": "WibWobEraserTimed", "68": "BeybladeV2", "69": "SequentialPuniEliminatorSword",
    "70": "DefenseBoosterAndHealer", "71": "AllPopperAndSoultGaugeFiller", "72": "VerticalLinePuniEraserTimed",
    "73": "AttackerAndWibWobTransformer", "74": "DoubleDirectionalLight", "75": "ExtremePopperVariant",
    "76": "WheelInflator", "77": "TracerInflator", "78": "TapAreaExPop", 
    "79": "TapPuniAttacker", "80": "AreaPopScaleEachTime", "81": "WheelPopAndBallOwnPuni", 
    "82": "AttackBoostAndStun", "83": "RinneZ(KindOfExPop)", "84": "TapInflatorBig", 
    "85": "AllPopFeverExtender", "86": "RangePopperBaseDamage", "87": "Sephiroth(AllPopCharge)", 
    "88": "2RowsAndBonusBalls", "89": "AllPopChargeSoult", "90": "InflateAndClear", 
    "91": "ExPopperNewer", "92": "none", "93": "DarkRinne(TraceLetter)", 
    "94": "AreaPopAndBonusBalls", "95": "AreaPopAndStun", "96": "AllPopChargeSoultNewer", 
    "97": "98ButSolo", "98": "BallMakerBetter", "99": "AllPopHeal", 
    "100": "AllPopRearranger", "101": "InflatorPop(4/5)", "102": "AllPopInflate4", 
    "103": "Arle(39Better)", "104": "100ComboPop", "105": "Megumin", 
    "106": "none", "107": "AllPopCrit", "108": "AllPopAnd46(Rimuru)", 
    "109": "Rem(AllPopAndOtherForm)", "110": "%HpDamageAllAttacker(AP)", "111": "AllPopAnd32", 
    "112": "AllPopAndOnlyLinkOwn", "113": "Atomic(AllPopAndSpam)", "114": "ExPopAndSingleAttacker", 
    "115": "Asuna(SwitchThing)", "116": "AllPopScaleHitTarget", "117": "none", 
    "118": "AllPopAnd1AttackerAnd104", "119": "AllPopMusicRhythm"
}

FOOD_TYPES = {
    "1": "RiceBalls", "2": "Sandwiches", "3": "Sweets", "4": "Chocobars",
    "5": "Milk", "6": "Juice", "7": "Burgers", "8": "Ramen",
    "9": "ChineseFood", "10": "Vegetables", "11": "Meat", "12": "Seafood",
    "13": "Sushi", "14": "Curry", "15": "Dessert", "16": "Oden",
    "17": "ZarusobaNoodles", "18": "Chips", "19": "IceCream"
}

YW_BONUS_EFFECTS = {
    "1": "BonusScore",
    "2": "LinksWithOtherWibWob",
    "3": "RaiseTribeEffect",
    "4": "ChipDropsMore",
    "5": "MisteryChallengesSimpler",
    "6": "LowersDamage",
    "7": "ReducesDamageFromBosses",
    "8": "PuniAppearsLess/More",
    "9": "LargePuniFalls",
    "10": "ReduceAllDamage(SolarEnma)",
    "11": "EzToLink",
    "12": "BonusBallsOwnPuni",
    "13": "Prefill",
    "14": "SetPositionFall",
    "15": "Revive",
    "16": "FeverFast",
    "17": "Redrop",
    "18": "BonusDamageAgainstTribe",
    "19": "SoultChargeWhenTakeDmg",
    "20": "OtherSoultChargeHis",
    "21": "CanChargeWhenBigPuniPop",
    "22": "CanHealWhenBigPuniPop",
    "23": "BigLinksWibwob",
    "24": "BonusYpoint",
    "25": "Guard",
    "26": "ChargeOtherWhenOwnBigPuniPop",
    "27": "SoultChargeWhenFever",
    "28": "Postfill",
    "29": "BonusBallsOwnPuni",
    "30": "OrganizeFirstFall",
    "31": "9ButWithRandom",
    "32": "StunStartBattle",
    "33": "HealEachXSeconds",
    "34": "CanIncreaseDamageIfXDamage",
    "35": "CanIncreaseFeverIfBigPuni",
    "36": "WhenOwnSoultBigPuniFalls",
    "37": "CanHealX%WhenOwnSoultUse",
    "38": "OwnBigPuniCanStun",
    "39": "FeverPrefill",
    "40": "SwapTribeOfCentralYokai",
    "41": "IncreaseX%DamageIfStun",
    "42": "IncreaseOhajikiDamage",
    "43": "X%DamageBoostOha/Golf",
    "44": "LargerRangeBonusBalls",
    "45": "RaiseX%DamageTeamIfBigPuniPop",
    "48": "HealInsteadDamageWhenPuniPop",
    "49": "PowerUpInFever",
    "50": "StatsBoostSpecificChar",
    "51": "ReduceStunTime",
    "52": "SurroundingPuniInflateWhenLink",
    "53": "SoultChargeWhenLink",
    "54": "SoultimateDamageScalingHP",
    "57": "SameTribeUnityBoost",
    "58": "DamageBoostPopUniEvt",
    "59": "TurnIntoKachiBlock",
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

COLONNES_STRONG_SKILL = [
    "Nom", "TypeID", "Description", "Propriete1", "Propriete2", "Anim3D", "Anim2D",
    "Anim2D_2", "SkillUnk0", "SkillUnk1", "SkillUnk2", "SkillUnk3", "Reserve",
    "CutinA", "CutinB", "LienExterne"
]

INDEX_RECHERCHE = {
    "Nom du Yo-kai (1)": 1,
    "Rang / Rarity (3)": 3,
    "Tribu / Kind (4)": 4,
    "Nourriture / FoodType (6)": 6,
    "Dictionary ID (14)": 14,
    "Type Âmultime (-1 à 119)": "SOULT",
    "Effet Bonus (texte)": "BONUS",
    "Effet Bonus (ID Type)": "BONUS_TYPE"
}

THEMES = {
    "Mode Sakura": {
        "bg_main": "#0e0c16",
        "card_bg": "#171424",
        "card_border": "#31264a",
        "accent": "#d980fa",
        "accent_glow": "#9b59b6",
        "text_main": "#f3e8ff",
        "text_muted": "#8d81a8",
        "entry_bg": "#201a33",
        "entry_fg": "#ffffff",
        "btn_bg": "#28203f",
        "btn_fg": "#e2d9f3",
        "btn_special_bg": "#3c1d56",
        "btn_special_fg": "#d980fa",
    },
    "Mode Sombre": {
        "bg_main": "#18191a",
        "card_bg": "#242526",
        "card_border": "#3a3b3c",
        "accent": "#6ea8fe",
        "accent_glow": "#0d6efd",
        "text_main": "#e4e6eb",
        "text_muted": "#b0b3b8",
        "entry_bg": "#3a3b3c",
        "entry_fg": "#ffffff",
        "btn_bg": "#3a3b3c",
        "btn_fg": "#e4e6eb",
        "btn_special_bg": "#1c3d5a",
        "btn_special_fg": "#6ea8fe",
    },
    "Mode Clair": {
        "bg_main": "#f4f6f9",
        "card_bg": "#ffffff",
        "card_border": "#dee2e6",
        "accent": "#0d6efd",
        "accent_glow": "#0b5ed7",
        "text_main": "#212529",
        "text_muted": "#6c757d",
        "entry_bg": "#ffffff",
        "entry_fg": "#212529",
        "btn_bg": "#e9ecef",
        "btn_fg": "#212529",
        "btn_special_bg": "#cfe2ff",
        "btn_special_fg": "#084298",
    },
    "Mode Printemps": {
        "bg_main": "#f2f7f2",
        "card_bg": "#ffffff",
        "card_border": "#cde3d1",
        "accent": "#2e7d32",
        "accent_glow": "#4caf50",
        "text_main": "#1b381e",
        "text_muted": "#527958",
        "entry_bg": "#f9fcf9",
        "entry_fg": "#1b381e",
        "btn_bg": "#e2efe4",
        "btn_fg": "#1b381e",
        "btn_special_bg": "#c8e6c9",
        "btn_special_fg": "#1b5e20",
    }
}

def get_kind_label(kind_id):
    """Retourne le libellé d'une tribu."""
    info = KIND_NAMES.get(str(kind_id))
    return info["nom"] if info else "Inconnu"

def get_rank_label(rank_id):
    """Retourne le libellé d'un rang."""
    info = RANK_NAMES.get(str(rank_id))
    return info["nom"] if info else "Inconnu"

def matches_kind(recherche, kind_id):
    """Vérifie si une recherche textuelle correspond à une tribu."""
    recherche = recherche.strip().lower()
    if not recherche:
        return True
    if str(kind_id).lower() == recherche:
        return True
    info = KIND_NAMES.get(str(kind_id))
    if not info:
        return False
    if recherche in info["nom"].lower() or recherche in info["en"].lower():
        return True
    return any(recherche in a for a in info.get("alias", []))

def matches_rank(recherche, rank_id):
    """Vérifie si une recherche textuelle correspond à un rang."""
    recherche = recherche.strip().lower()
    if not recherche:
        return True
    if str(rank_id).lower() == recherche:
        return True
    info = RANK_NAMES.get(str(rank_id))
    if not info:
        return False
    if recherche in info["nom"].lower() or recherche == info["court"].lower():
        return True
    return any(recherche in a for a in info.get("alias", []))
