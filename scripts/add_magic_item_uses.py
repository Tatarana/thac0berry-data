"""Funções que um item mágico ativa (`power.uses`), lidas do texto do livro.

Pedido do usuário (2026-10-24): a spell sheet da web puxa sozinha os itens da
ficha que lançam magias. Só 23 itens tinham `power.spell` e o texto não dá para
casar automaticamente, então as funções são escritas à mão, item por item.

Cada função: nome, magia equivalente (SpellRef, ou None quando não é magia),
cargas por uso, limite por dia e o efeito do item quando difere da magia.
Ficam de fora os efeitos de arma (golpe com carga) e os itens sem função
ativável (Rod of Flailing, Staff of Striking, Magical Quarterstaff...).

Lote 1: os 43 Rods/Staves/Wands do DMG.

Idempotente; `--dry-run` só mostra o que mudaria. Confere cada magia contra a
base de magias (nome exato, na classe indicada) e para se alguma não existir.
"""
import glob
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILE = ROOT / "data" / "magic_rods_staves_wands.json"

P, W = "Priest", "Wizard"


def use(name, spell=None, cls=None, charges=None, per_day=None, effect=None):
    return {"name": name, "spell": (spell, cls) if spell else None, "chargeCost": charges, "perDay": per_day, "effect": effect}


USES = {
    "rod_of_alertness": [
        use("Detect alignment", "Know Alignment", P, 0),
        use("Detect evil/good", "Detect Evil", P, 0),
        use("Detect illusions", None, None, 0),
        use("Detect invisibility", "Detect Invisibility", W, 0),
        use("Detect lie", "Detect Lie", P, 0),
        use("Detect magic", "Detect Magic", P, 0),
        use("Alertness (light + prayer)", "Prayer", P, 1),
        use("Animate object", "Animate Object", P, 1, effect="up to 16 objects; +1 charge"),
    ],
    "rod_of_beguiling": [use("Beguile (20-ft radius)", None, None, 1, effect="1 turn per charge")],
    "rod_of_lordly_might": [
        use("Paralyzation (touch)", None, None, 1),
        use("Fear", "Fear", W, 1),
        use("Drain hit points (touch)", None, None, 1, effect="2d4 hp to the wielder"),
    ],
    "rod_of_passage": [
        use("Activation (all five, 1 day)", None, None, 1),
        use("Astral travel", "Astral Spell", W, 0, effect="up to 5 creatures"),
        use("Dimension door", "Dimension Door", W, 0),
        use("Passwall", "Passwall", W, 0),
        use("Phase door", "Phase Door", W, 0),
        use("Teleport without error", "Teleport Without Error", W, 0),
    ],
    "rod_of_resurrection": [use("Resurrection", "Resurrection", P, None, 1, "1–4 charges by class + 1–4 by race")],
    "rod_of_rulership": [use("Rulership (120 ft)", None, None, 1, effect="1 turn per charge")],
    "rod_of_security": [use("Pocket paradise", None, None, 1)],
    "rod_of_splendor": [
        use("Noble garb", None, None, 1),
        use("Palatial tent", None, None, 1, effect="1 day; +1 charge per extra day"),
    ],
    "rod_of_terror": [use("Terror aura (30 ft)", None, None, 1, effect="20% chance: −1 Charisma")],
    "staff_of_command": [
        use("Human influence", None, None, 1),
        use("Mammal/animal control", None, None, 1, effect="per turn"),
        use("Plant control", None, None, 1, effect="per 10 sq ft per turn; priest only"),
    ],
    "staff_of_curing": [
        use("Cure disease", "Cure Disease", P, 1, 2),
        use("Cure blindness", "Cure Blindness or Deafness", P, 1, 2),
        use("Cure wounds", None, None, 1, 2, "3d6+3 hp"),
        use("Cure insanity", None, None, 1, 2),
    ],
    "staff_of_swarming_insects": [use("Insect swarm", None, None, 1, effect="60 + 10/level insects; 1 hp per 10")],
    "staff_of_the_magi": [
        use("Detect magic", "Detect Magic", W, 0),
        use("Enlarge", "Enlarge", W, 0),
        use("Hold portal", "Hold Portal", W, 0),
        use("Light", "Light", W, 0),
        use("Protection from evil/good", "Protection From Evil", W, 0),
        use("Invisibility", "Invisibility", W, 1),
        use("Fireball", "Fireball", W, 1),
        use("Knock", "Knock", W, 1),
        use("Lightning bolt", "Lightning Bolt", W, 1),
        use("Pyrotechnics", "Pyrotechnics", W, 1),
        use("Ice storm", "Ice Storm", W, 1),
        use("Web", "Web", W, 1),
        use("Wall of fire", "Wall of Fire", W, 1),
        use("Dispel magic", "Dispel Magic", W, 1),
        use("Passwall", "Passwall", W, 1),
        use("Whirlwind", None, None, 2, effect="as a djinni"),
        use("Conjure elemental", "Conjure Elemental", W, 2, effect="8 HD; one of each type per day"),
        use("Planar travel", None, None, 2),
        use("Telekinesis", "Telekinesis", W, 2, effect="8th level (200 lb)"),
    ],
    "staff_of_the_woodlands": [
        use("Wall of thorns", "Wall of Thorns", P, 1),
        use("Animal friendship + speak with animals", "Animal Friendship", P, 1),
        use("Animate tree", None, None, 1, effect="8 rounds"),
        use("Pass without trace", "Pass Without Trace", P, 0, 1, "+3 or lower staff"),
        use("Barkskin", "Barkskin", P, 0, 1, "+2 or +1 staff"),
        use("Tree", "Tree", P, 0, 1, "+1 staff"),
    ],
    "staff_of_thunder_lightning": [
        use("Thunderclap", None, None, 2, effect="stun 1d2 rounds"),
        use("Lightning stroke", None, None, 2, effect="8d6 (1s count as 2)"),
        use("Thunder & lightning", None, None, 4, effect="8d6 (1s and 2s count as 3)"),
    ],
    "wand_of_conjuration": [
        use("Unseen servant", "Unseen Servant", W, 1),
        use("Monster summoning", "Monster Summoning I", W, 1, effect="1 charge per level (I–VI), max 6"),
        use("Curtain of blackness", None, None, 2),
        use("Prismatic sphere/wall", "Prismatic Sphere", W, 1, effect="1 charge per color"),
    ],
    "wand_of_earth_and_stone": [
        use("Dig", "Dig", W, None, effect="½ charge per use"),
        use("Passwall", "Passwall", W, 1),
        use("Move earth", "Move Earth", W, 2),
        use("Transmute mud to rock", "Transmute Rock to Mud", W, 1, effect="50% of wands"),
        use("Transmute rock to mud", "Transmute Rock to Mud", W, 1, effect="50% of wands"),
    ],
    "wand_of_enemy_detection": [use("Enemy detection (60 ft)", None, None, 1, effect="1 turn per charge")],
    "wand_of_fear": [use("Fear ray (cone)", "Remove Fear", P, 1, effect="as cause fear (reverse)")],
    "wand_of_fire": [
        use("Burning hands", "Burning Hands", W, 1, effect="6 hp"),
        use("Pyrotechnics", "Pyrotechnics", W, 1),
        use("Fireball", "Fireball", W, 2, effect="6d6 (1s count as 2)"),
        use("Wall of fire", "Wall of Fire", W, 2, effect="2d6+6 if touched"),
    ],
    "wand_of_flame_extinguishing": [
        use("Extinguish normal fire", None, None, 0),
        use("Extinguish large fire", None, None, 1),
        use("Extinguish magical fire", None, None, 2),
    ],
    "wand_of_frost": [
        use("Ice storm", "Ice Storm", W, 1),
        use("Wall of ice", "Wall of Ice", W, 1),
        use("Cone of cold", "Cone of Cold", W, 2, effect="6d6 (1s count as 2)"),
    ],
    "wand_of_illumination": [
        use("Dancing lights", "Dancing Lights", W, 1),
        use("Light", "Light", W, 1),
        use("Continual light", "Continual Light", W, 2),
        use("Sunburst", None, None, 3, effect="6d6 to undead; blinds 1 round"),
    ],
    "wand_of_illusion": [
        use("Audible glamer", "Audible Glamer", W, 1, effect="+1 charge per round"),
        use("Phantasmal force", "Phantasmal Force", W, 1, effect="+1 charge per round"),
    ],
    "wand_of_lightning": [
        use("Shock (melee)", None, None, 1, effect="1d10"),
        use("Lightning bolt", "Lightning Bolt", W, 2, effect="6d6 (1s count as 2)"),
    ],
    "wand_of_magic_detection": [use("Magic detection (30 ft)", "Detect Magic", W, 1, effect="1 turn per charge")],
    "wand_of_magic_missiles": [use("Magic missile", "Magic Missile", W, 1, effect="1d4+1; max 2 per round")],
    "wand_of_metal_and_mineral_detection": [use("Metal & mineral detection (30 ft)", None, None, 1, effect="2 turns per charge")],
    "wand_of_negation": [use("Negation", None, None, 1)],
    "wand_of_paralyzation": [use("Paralyzation ray", None, None, 1, effect="5d4 rounds")],
    "wand_of_polymorphing": [
        use("Polymorph others (ray)", "Polymorph Other", W, 1),
        use("Polymorph self (touch)", "Polymorph Self", W, 1),
    ],
    "wand_of_secret_door_and_trap_location": [
        use("Secret door location (15 ft)", None, None, 1),
        use("Trap location (30 ft)", None, None, 1),
    ],
    "wand_of_size_alteration": [use("Enlarge/reduce", "Enlarge", W, 1)],
    "wand_of_wonder": [use("Random effect", None, None, 1)],
}


def spell_names():
    names = {P: {}, W: {}}
    for f in glob.glob(str(ROOT / "data" / "*.json")):
        stem = Path(f).stem
        cls = P if stem.startswith("priest_") else W if stem.startswith("wizard_") else None
        if not cls:
            continue
        data = json.load(open(f, encoding="utf-8"))
        items = data if isinstance(data, list) else next((v for v in data.values() if isinstance(v, list)), [])
        for s in items:
            if isinstance(s, dict) and s.get("name"):
                names[cls].setdefault(s["name"].lower(), s["name"])
    return names


def snake(name):
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def main():
    dry = "--dry-run" in sys.argv
    names = spell_names()
    missing = []
    for item, uses in USES.items():
        for u in uses:
            if u["spell"]:
                spell, cls = u["spell"]
                found = names[cls].get(spell.lower())
                if not found:
                    missing.append(f"{item}: {spell} ({cls})")
                    continue
                u["spell"] = {"id": snake(found), "name": found, "class": cls}
    if missing:
        print("Magias que não existem na base:\n  " + "\n  ".join(missing))
        sys.exit(1)

    items = json.load(open(FILE, encoding="utf-8"))
    by_id = {it["id"]: it for it in items}
    changed = 0
    for item_id, uses in USES.items():
        it = by_id.get(item_id)
        if it is None:
            print(f"{item_id}: não encontrado")
            sys.exit(1)
        power = it.get("power") or {"name": None, "chargeBased": True, "maxCharges": None, "spell": None}
        if power.get("uses") == uses:
            print(f"{item_id}: já tem as funções")
            continue
        power["uses"] = uses
        it["power"] = power
        changed += 1
        print(f"{item_id}: {len(uses)} funções")
    if dry:
        print("(dry-run: nada gravado)")
        return
    if changed:
        # Mesmo formato compacto do arquivo (como fix_magic_item_values.py).
        with open(FILE, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(items, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
