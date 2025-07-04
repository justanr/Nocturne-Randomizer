# code modified from https://github.com/samfin/mmbn3-random/tree/cleanup
import copy
from pickletools import uint1
import struct
import re
import random
import os
from tokenize import Special

import randomizer
import races
from base_classes import Demon, Skill, Magatama, Battle
from paths import DATA_PATH, PATCHES_PATH

N_DEMONS = 383
N_MAGATAMAS = 25
N_BATTLES = 1270

all_demons = {}
all_magatamas = {}
all_battles = {}
all_skills = {}
gathering_demons = {}
special_gathering_map = {}

# demons/bosses that absorb/repel/null phys
PHYS_INVALID_DEMONS = [
    2,
    14,
    87,
    93,
    98,
    104,
    105,
    144,
    155,
    172,
    202,
    206,
    269,
    274,
    276,
    277,
    333,
    334,
    352,
]

# demons/bosses that are normally in the hospital/shibuya
BASE_DEMONS = [61, 137, 92, 97, 131, 91, 126, 103, 135, 136]

DRAGON_EYE_DEMONS = {  # [73, 56, 100, 113, 116, 110, 89, 144, 71]
    73: 0x69,  # Eligor
    56: 0x6C,  # Setanta
    100: 0x6D,  # Yaksini
    113: 0x6E,  # Loki
    116: 0x42,  # Queen Mab
    110: 0x6F,  # Aciel
    89: 0x6C,  # Sarutahiko
    144: 0x6A,  # Arahabaki
    71: 0x6C,  # Ose
}

SHADY_BROKER = {
    167: 208,  # Pisaca
    124: 209,  # Nue
    144: 210,  # Arahabaki
    131: 211,  # Preta
    122: 212,  # Mothman
    105: 213,  # Girimehkala
}


def load_demons(rom):
    demon_offset = 0x0024A7F0

    demon_names_path = os.path.join(DATA_PATH, "demon_names.txt")
    demon_names = open(demon_names_path, "r").read().strip()
    demon_names = demon_names.split("\n")

    rom.seek(demon_offset)
    for i in range(N_DEMONS):
        demon_name = demon_names[i]

        demon_offset = rom.r_offset
        (
            _,
            flag,
            _,
            race_id,
            level,
            hp,
            _,
            mp,
            _,
            demon_id,
            strength,
            _,
            magic,
            vitality,
            agility,
            luck,
            battle_skills,
            _,
            macca_drop,
            exp_drop,
            _,
        ) = struct.unpack("<12sH2sBBHHHHHBBBBBB12s8sHHH", rom.read(0x3C))

        # skip entry if it's a garbage/unknown demon
        if race_id == 0 or demon_name == "?":
            continue

        # Beelzebub (Human) and Beelzebub (Fly) share the same demon_id for some reason, so separate them
        if demon_name == "Beelzebub":
            demon_id = 207

        demon = Demon(demon_id, demon_name)
        demon.offset = demon_offset
        demon.skill_offset = 0x00234CF4 + (demon_id * 0x66)
        # demon.ai_offset = 0x002999E4 + (demon_id * 0xA4)
        demon.ai_offset = 0x002999E0 + (demon_id * 0xA4)

        demon.race = race_id
        demon.level = level
        demon.hp = hp
        demon.mp = mp
        demon.stats = [strength, magic, vitality, agility, luck]
        demon.macca_drop = macca_drop
        demon.exp_drop = exp_drop

        s = []
        for j in range(0, len(battle_skills), 2):
            skill = struct.unpack("<H", battle_skills[j : j + 2])[0]
            if skill > 0:
                s.append(skill)

        # battle skills are the skills that show up when you analyze enemy demons (used for demon ai later)
        demon.battle_skills = s
        demon.skills = load_demon_skills(rom, demon.skill_offset, level)

        demon.is_boss = bool(i >= 255)
        # remove jive talk flag
        demon.flag = flag & (~0x0080)
        if not demon.is_boss:
            # remove evolution fusion flag from non-boss demons
            demon.flag = demon.flag & (~0x0002)

        # keep track of phys invalid demons and demons in the hospital for "Easy Hospital" and early buff/debuff distribution
        demon.phys_inv = demon_id in PHYS_INVALID_DEMONS
        demon.base_demon = demon_id in BASE_DEMONS

        if demon_id in SHADY_BROKER.keys():
            demon.shady_broker = SHADY_BROKER[demon_id]

        for i in range(
            3
        ):  # Find demons that naturally use gathering and store the skill data
            for j in range(5):
                offset = (demon.ai_offset + 0x28) + (i * 0x28) + j * 0x8
                skill_odds = rom.read_halfword(offset)
                skill_id = rom.read_halfword(offset + 0x2)
                if (
                    skill_id >= 0x9000
                    and skill_id <= 0xBFFF
                    and (
                        demon_id not in gathering_demons
                        or gathering_demons[demon_id]["odds"] >= skill_odds
                    )
                ):
                    summoned_demon = skill_id % 0x1000
                    if summoned_demon != demon_id:
                        special_gathering_map[summoned_demon] = 0x01
                    skill_prefix = 0x9000
                    if skill_id >= 0xA000:
                        skill_prefix = 0xA000
                    if skill_id >= 0xB000:
                        skill_prefix = 0xB000
                    gathering_data = {
                        "ai_group": i,
                        "odds": skill_odds,
                        "summon_id": summoned_demon,
                        "skill_prefix": skill_prefix,
                    }
                    gathering_demons[demon_id] = gathering_data
                    break

        all_demons[demon_id] = demon


def lookup_demon(ind):
    return all_demons.get(ind)


race_names = []


def load_races():
    names_path = os.path.join(DATA_PATH, "race_names.txt")
    names = open(names_path, "r").read().strip()
    names = names.split("\n")
    race_names.extend(names)


def load_demon_skills(rom, skill_offset, level):
    demon_skills = []

    rom.save_offsets()
    rom.seek(skill_offset + 0x0A)

    count = 0
    while True:
        # level at which they learn the skill
        learn_level = rom.read_byte()
        # event indicates what event happens at learn_level
        # 0x01 = skill learned normally
        # 0x05 = demon evolves
        # 0x06 = skill learned through evolution only
        # 0x07 = "demon body is changing" text thing
        event = rom.read_byte()
        skill_id = rom.read_halfword()

        if event == 0 or count >= 23:
            break

        # skip the evolution events
        if event == 0x05 or event == 0x07:
            continue

        s = {
            "level": max(0, learn_level - level),
            # disregard events currently since we are removing evolution demons
            "event": 1,
            "skill_id": skill_id,
        }

        for skill in demon_skills:
            if skill["skill_id"] == s["skill_id"]:
                continue

        demon_skills.append(s)
        count += 1

    rom.load_offsets()
    return demon_skills


def load_skills(rom):
    skill_data_path = os.path.join(DATA_PATH, "skill_data.txt")
    skill_data = open(skill_data_path, "r").read().strip()
    pattern = re.compile(r"([\dABCDEF]{3}) ([\w\'\&\- ]+) (\d+) (\d+) (\d+)")

    skill_data = list(map(lambda s: re.search(pattern, s), skill_data.split("\n")))

    # for i in range(len(skill_data)):
    for i, data in enumerate(skill_data):
        skill_id = int(data[1], 16)
        name = data[2]
        rank = int(data[3])
        skill_type = int(data[4])
        skill_level = int(data[5])

        skill = Skill(skill_id, name, rank)
        skill.skill_type = skill_type
        skill.level = skill_level

        all_skills[skill_id] = skill


def load_skill_changes(rom):
    skill_change_offset = 0x0023AC20
    rom.seek(skill_change_offset)
    with open("./logs/skill_changes.txt", "w") as debug_file:
        for i in range(0, 55):
            debug_file.write(
                all_skills[rom.read_halfword()].name
                + " to "
                + all_skills[rom.read_halfword()].name
                + "\n"
            )


def lookup_skill(ind):
    return all_skills.get(ind)


def lookup_skill_by_name(skill_name):
    for key, skill in all_skills.items():
        if skill.name == skill_name:
            return skill
    print("ERROR: Skill name was misspelled: " + skill_name)
    return None


def load_magatamas(rom):
    magatama_offset = 0x0023AE3A

    magatama_names_path = os.path.join(DATA_PATH, "magatama_names.txt")
    magatama_names = open(magatama_names_path, "r").read().strip()
    magatama_names = magatama_names.split("\n")

    rom.seek(magatama_offset)
    for i in range(N_MAGATAMAS):
        m_name = magatama_names[i]

        m_offset = rom.r_offset
        _, strength, _, magic, vitality, agility, luck, _, skills = struct.unpack(
            "<14sBBBBBB14s32s", rom.read(0x42)
        )

        m = Magatama(m_name)
        m.ind = i
        m.stats = [strength, magic, vitality, agility, luck]

        m.level = None

        s = []
        for j in range(0, len(skills), 4):
            level, skill_id = struct.unpack("<HH", skills[j : j + 4])

            if m.level is None:
                m.level = level

            if skill_id > 0:
                skill = {
                    "level": level - m.level,
                    "skill_id": skill_id,
                }
                s.append(skill)
        m.skills = s
        m.offset = m_offset
        all_magatamas[m.name] = m


def load_battles(rom):
    offset = 0x002AFFE0

    for i in range(N_BATTLES):
        enemies = []

        for j in range(0, 18, 2):
            enemy_id = rom.read_halfword(offset + 6 + j)
            enemies.append(enemy_id)
            # if enemy_id == 0x12b or enemy_id == 0x163:
            #    print("Sakahagi, allegedly")
            #    print(offset)

        battle = Battle(offset)
        battle.enemies = enemies
        battle.is_boss = rom.read_halfword(offset) == 0x01FF
        battle.reward = rom.read_halfword(offset + 0x02)
        battle.phase_value = rom.read_halfword(offset + 0x04)
        battle.arena = rom.read_word(offset + 0x1C)
        battle.goes_first = rom.read_halfword(offset + 0x20)
        battle.reinforcement_value = rom.read_halfword(offset + 0x22)
        battle.music = rom.read_halfword(offset + 0x24)
        all_battles[offset] = battle
        offset += 0x26


def write_demon(rom, demon, offset):
    rom.seek(offset)

    rom.write_halfword(demon.flag, offset + 0x0C)
    rom.write_byte(demon.race, offset + 0x10)
    rom.write_byte(demon.level, offset + 0x11)
    rom.write_halfword(demon.hp, offset + 0x12)
    rom.write_halfword(demon.hp, offset + 0x14)
    # Specter 2 starting mp fix
    if demon.name == "Specter 2 (Boss)":
        rom.write_halfword(29, offset + 0x16)
    else:
        rom.write_halfword(demon.mp, offset + 0x16)
    rom.write_halfword(demon.mp, offset + 0x18)

    stats = struct.pack(
        "<BBBBBB",
        demon.stats[0],
        0x00,
        demon.stats[1],
        demon.stats[2],
        demon.stats[3],
        demon.stats[4],
    )
    rom.write(stats, offset + 0x1C)

    rom.write_halfword(demon.macca_drop, offset + 0x36)
    rom.write_halfword(demon.exp_drop, offset + 0x38)

    # don't change boss ai or skills
    if not demon.is_boss:
        # if rom.read_halfword(demon.ai_offset) != 0x46:
        #    print(demon.name)
        #    print(rom.read_halfword(demon.ai_offset))

        # zero out old battle skills
        rom.write(struct.pack("<16x"), offset + 0x22)

        rom.seek(offset + 0x22)
        for skill in demon.battle_skills:
            rom.write_halfword(skill)

        write_skills(rom, demon)
        write_ai(rom, demon)


def write_demons(rom, new_demons):
    find_special_gatherings(new_demons)
    for demon in new_demons:
        write_demon(rom, demon, demon.offset)

        if demon.shady_broker is not None:
            shady_broker_offset = 0x0024A7B4 + (demon.shady_broker) * 0x3C
            write_demon(rom, demon, shady_broker_offset)
            # set the race_id back to 0 on the shady_broker demons to disable them from fusions and stuff
            rom.write_byte(0, shady_broker_offset + 0x10)


def find_special_gatherings(new_demons):
    for demon in new_demons:
        if demon.old_id in special_gathering_map:
            special_gathering_map[demon.old_id] = demon.ind


def write_skills(rom, demon):
    # zero out old demon skills
    offset = demon.skill_offset + 0x0A
    rom.write(struct.pack("<92x"), offset)

    rom.seek(offset)
    for skill in demon.skills:
        rom.write_byte(skill["level"])
        rom.write_byte(skill["event"])
        rom.write_halfword(skill["skill_id"])


def write_ai(rom, demon):
    # get rid of special demon ai scripts, except for dragon eye scripts
    # if rom.read_halfword(demon.ai_offset) not in [0x46, 0x69, 0x6a, 0x6b, 0x6c, 0x6d, 0x6e, 0x6f, 0x79]:
    if demon.old_id not in DRAGON_EYE_DEMONS.keys():
        # 0x46 is the default I think?
        rom.write_halfword(0x46, demon.ai_offset)
    else:
        rom.write_halfword(DRAGON_EYE_DEMONS[demon.old_id], demon.ai_offset)

    gathering_data = None
    if demon.old_id in gathering_demons:
        gathering_data = gathering_demons[demon.old_id]

    # todo: make generating odds more random
    total_odds = [
        [
            100,
        ],
        [50, 50],
        [34, 33, 33],
        [25, 25, 25, 25],
        [20, 20, 20, 20, 20],
    ]

    # 3 sets of ai skills
    for i in range(3):
        skill_pool = copy.copy(demon.battle_skills)

        if gathering_data:  # Add gathering to the skill pool if appropriate
            summoned_demon = demon.old_id
            if summoned_demon != gathering_data["summon_id"]:
                summoned_demon = special_gathering_map[gathering_data["summon_id"]]
            else:
                summoned_demon = demon.ind
            gathering_skill_id = gathering_data["skill_prefix"] + summoned_demon
            skill_pool.append(gathering_skill_id)

        # add basic attack to skill pool and shuffle
        skill_pool.append(0x8000)
        random.shuffle(skill_pool)

        # can only write a max of 5 skills per set
        num_of_skills = min(len(skill_pool), 5)

        odds = assign_odds(num_of_skills, 100)

        # zero out old demon ai
        offset = (demon.ai_offset + 0x28) + (i * 0x28)
        rom.write(struct.pack("<40x"), offset)

        rom.seek(offset)
        # write the new demon ai
        for o, s in zip(odds, skill_pool):
            rom.write(struct.pack("<HHI", o, s, 0))


def assign_odds(num_skills, total_odds):
    odds = []
    remaining_odds = total_odds
    remaining_skills = num_skills
    for i in range(num_skills - 1):
        average = round(remaining_odds / remaining_skills)
        minimum = 5
        maximum = remaining_odds - 5 * (remaining_skills - 1)
        random_direction = random.choice(["average", "higher", "lower"])
        chosen_odds = 0
        if random_direction == "average":
            chosen_odds = average
        elif random_direction == "lower":
            chosen_odds = max(
                random.randint(minimum, average), random.randint(minimum, average)
            )
        else:
            chosen_odds = min(
                random.randint(average, maximum), random.randint(average, maximum)
            )
        odds.append(chosen_odds)
        remaining_odds -= chosen_odds
        remaining_skills -= 1
        if remaining_odds <= 0:
            print("ERROR: ran out of odds in ai selection")
    odds.append(remaining_odds)
    return odds


def write_skill_changes(rom, new_mutations):
    skill_change_offset = 0x0023AC20
    rom.seek(skill_change_offset)
    for base_skill, enhanced_skill in new_mutations.items():
        rom.write_halfword(lookup_skill_by_name(base_skill).ind)
        rom.write_halfword(lookup_skill_by_name(enhanced_skill).ind)


def write_magatamas(rom, new_magatams):
    for magatama in new_magatams:
        stats = struct.pack(
            "<BBBBBB",
            magatama.stats[0],
            0xFF,
            magatama.stats[1],
            magatama.stats[2],
            magatama.stats[3],
            magatama.stats[4],
        )
        rom.seek(magatama.offset + 0x0E)
        for i in range(2):
            rom.write(stats)
        rom.seek(magatama.offset + 0x22)
        for skill in magatama.skills:
            rom.write_halfword(skill["level"])
            rom.write_halfword(skill["skill_id"])


# reward_tbl_offset = 0x001FEE00
# reward_tbl = []


def write_battles(rom, new_battles, preserve_boss_arenas=False):
    for b in new_battles:
        # only write magatama rewards
        """if b.reward:
            b.reward_index = len(reward_tbl)
            rom.write_halfword(b.reward_index + 1, b.offset + 0x02)
            reward_tbl.append(b.reward)
        else:
            rom.write_halfword(0x00, b.offset + 0x02)
        if 345 >= b.reward >= 320:
            rom.write_halfword(b.reward, b.offset + 0x02)"""
        if 345 >= b.reward >= 320:
            rom.write_halfword(
                0, b.offset + 0x02
            )  # Magatama rewards are given through eventing now, so this is no longer necessary
        else:
            rom.write_halfword(b.reward, b.offset + 0x02)
        rom.write_halfword(b.phase_value, b.offset + 0x04)
        rom.seek(b.offset + 0x06)
        for e in b.enemies:
            rom.write_halfword(e)
        if preserve_boss_arenas:
            rom.write_word(b.arena, b.offset + 0x1C)
        rom.write_halfword(b.goes_first, b.offset + 0x20)
        rom.write_halfword(b.reinforcement_value, b.offset + 0x22)
        rom.write_halfword(b.music, b.offset + 0x24)

    """
    for i, r in enumerate(reward_tbl):
        offset = reward_tbl_offset + (i * 0x10)
        reward_type = 0x01                      # always an item for now, 0x02 will be flags later
        rom.write_byte(reward_type, offset)
        #rom.write_byte(1, offset + 0x01)       # Amount
        rom.write_halfword(r, offset + 0x02)
    """


def patch_incubus_koppa(rom, demon_map):
    ik_offset = 0x002B1540  # Battle with koppa and incubus
    rom.write_halfword(demon_map[0x76], ik_offset + 0x8)  # incubus
    rom.write_halfword(demon_map[0x34], ik_offset + 0xA)  # koppa
    pass


def patch_fix_tutorials(rom, tutorial_ais, dds3):
    # currently demon specific sounds effects don't work for the copied demons
    # copy preta to 0x16a
    tut_preta = copy.deepcopy(all_demons[0x83])
    tut_preta.ai_offset = 0x002999E0 + (0x16A * 0xA4)
    tut_preta.offset = (0x0024A7F0 + (0x16A * 0x3C)) - 0x3C
    tut_preta.is_boss = True
    tut_preta.race = 39
    all_demons[0x16A] = tut_preta
    write_demon(rom, tut_preta, tut_preta.offset)
    rom.write(tutorial_ais[0], tut_preta.ai_offset)
    # write name offset to name table
    rom.write_word(0x00550248, 0x002E88D0)

    # copy kodama to 0x16b
    tut_kodama = copy.deepcopy(all_demons[0x5C])
    tut_kodama.ai_offset = 0x002999E0 + (0x16B * 0xA4)
    tut_kodama.offset = (0x0024A7F0 + (0x16B * 0x3C)) - 0x3C
    tut_kodama.is_boss = True
    tut_kodama.race = 35
    all_demons[0x16B] = tut_kodama
    write_demon(rom, tut_kodama, tut_kodama.offset)
    rom.write(tutorial_ais[1], tut_kodama.ai_offset)
    # write name offset to name table
    rom.write_word(0x00550328, 0x002E88D4)

    # copy will o' wisp to 0x16c
    tut_willy = copy.deepcopy(all_demons[0x89])
    tut_willy.ai_offset = 0x002999E0 + (0x16C * 0xA4)
    tut_willy.offset = (0x0024A7F0 + (0x16C * 0x3C)) - 0x3C
    tut_willy.is_boss = True
    tut_willy.race = 36
    all_demons[0x16C] = tut_willy
    write_demon(rom, tut_willy, tut_willy.offset)
    rom.write(tutorial_ais[2], tut_willy.ai_offset)
    # write name offset to name table
    rom.write_word(0x00540308, 0x002E88D8)

    tutorial_2_offset = 0x002BBBF8
    tutorial_3_offset = 0x002BBC1E
    tutorial_4_offset = 0x002BBC44

    rom.write(struct.pack("<H", 0x16A), tutorial_2_offset)
    rom.write(struct.pack("<HH", 0x16B, 0x16B), tutorial_3_offset)
    rom.write(struct.pack("<HH", 0x16B, 0x16C), tutorial_4_offset)

    dds3.add_new_file("/npackl/BU16A.LB", dds3.get_file_from_path("/npackl/BU083.LB"))
    dds3.add_new_file("/npackl/BU16B.LB", dds3.get_file_from_path("/npackl/BU05C.LB"))
    dds3.add_new_file("/npackl/BU16C.LB", dds3.get_file_from_path("/npackl/BU089.LB"))


def patch_early_spyglass(rom):
    # change the 3x preta fight's reward to spyglass
    rom.write_halfword(0x012E, 0x002B0DB0)
    """
    reward_index = len(reward_tbl)
    reward_offset = reward_tbl_offset + (reward_index * 0x10)

    rom.write_halfword(reward_index + 1, 0x002B0DB0)
    rom.write_byte(1, reward_offset)            # item type
    #rom.write_byte(1, reward_offset + 0x01)     # amount
    rom.write_halfword(0x12E, reward_offset + 0x02)
    reward_tbl.append(0x12E)
    """
    # change the selling price of the spyglass to 0 macca
    rom.write_word(0, 0x002DD614)


def remove_shop_magatamas(rom):
    # Shibuya shop
    rom.write_byte(0, 0x00230718)  # remove Iyomante
    rom.write_byte(0, 0x0023071C)  # remove Shiranui

    # Underpass shop
    rom.write_byte(0, 0x002307A2)  # remove Ankh
    rom.write_byte(0, 0x002307A6)  # remove Hifumi
    rom.write_byte(0, 0x002307AA)  # remove Kamudo

    # Asakusa shop
    rom.write_byte(0, 0x002308B6)  # remove Nirvana
    rom.write_byte(0, 0x002308BA)  # remove Gehenna

    # Asakusa Tunnel shop
    rom.write_byte(0, 0x00230920)  # remove Kamurogi
    rom.write_byte(0, 0x00230924)  # remove Vimana
    rom.write_byte(0, 0x00230928)  # remove Sophia

    # ToK shop
    rom.write_byte(0, 0x002309DE)  # remove Kailash

    # Underpass shop may be separate based on if you got Ankh from Pixie
    rom.write_byte(0, 0x00230A2C)  # remove Hifumi again(?)
    rom.write_byte(0, 0x00230A30)  # remove Kamudo again(?)


def fix_elemental_fusion_table(rom, demon_generator):
    fusion_table_offset = 0x0022E270

    # ids use for conversion to fusion table ids
    elem_table_ids = {
        races.race_flaemis: 0x24,
        races.race_aquans: 0x25,
        races.race_aeros: 0x26,
        races.race_erthys: 0x27,
    }

    # make all races not fuse into elementals
    for i in range(32):
        rom.write_byte(0, fusion_table_offset + i + (i * 32))

    # use the generated elemental results to change the fusion table
    for race, elemental in zip(races.raceref, demon_generator.elemental_results):
        if elemental > 0:
            race_id = race_names.index(race)
            race_table_offset = fusion_table_offset + (race_id * 32)
            rom.write_byte(elem_table_ids[elemental], race_table_offset + race_id)


def fix_mada_summon(rom, new_demons):
    # replace the pazuzu mada summons in it's ai with a demon that is equal or less in level than mada
    pazuzu_summon_offset = 0x002A6F86
    mada = next((d for d in new_demons if d.name == "Mada (Boss)"), None)
    candidates = [d.ind for d in new_demons if d.level <= mada.level and not d.is_boss]
    if mada and candidates:
        rom.write_byte(random.choice(candidates), pazuzu_summon_offset)


def fix_nihilo_summons(rom, demon_map):
    # replace the demons summoned by the nihilo minibosses
    def replace_summons(offsets):
        for off in offsets:
            replacement = demon_map[rom.read_byte(off)]
            rom.write_byte(replacement, off)
        return replacement

    yaka_summon_offsets = [0x0041A0FA, 0x0041A132, 0x0041A182]
    dis_summon_offsets = [0x0041A2CE, 0x0041A306, 0x0041A382, 0x0041A556]
    incubus_summon_offsets = [0x0041A4CE, 0x0041A506]

    replace_summons(yaka_summon_offsets)
    replace_summons(dis_summon_offsets)
    replace_summons(incubus_summon_offsets)


def fix_specter_1_reward(rom, reward):
    # add rewards to each of the fused versions of specter 1
    fused_reward_offsets = [0x002B2842, 0x002B2868, 0x002B288E]
    for offset in fused_reward_offsets:
        rom.write_halfword(reward, offset)


def fix_girimehkala_reward(rom, reward):
    # fix magatama drop for vanilla girimehkala
    fused_reward_offsets = [0x002B30B8]
    for offset in fused_reward_offsets:
        rom.write_halfword(reward, offset)


def fix_ahriman_reward(rom, reward):
    # fix magatama drop for ahriman, 0x002B3176 is second fight
    fused_reward_offsets = [
        0x002B9322
    ]  # Notably the battle offset is +0x2 to get the reward byte
    for offset in fused_reward_offsets:
        rom.write_halfword(reward, offset)


def fix_noah_reward(rom, reward):
    # fix magatama drop for noah, 0x002B45F2 is second fight
    fused_reward_offsets = [0x002B9348]
    for offset in fused_reward_offsets:
        rom.write_halfword(reward, offset)


def fix_angel_reward(rom, reward):
    # fix the magatama drop for the optional angel fight
    offset = 0x002B63C8
    rom.write_halfword(reward + 1, offset)


"""
def patch_intro_skip(iso_file):
    # overwrite an unused event script with ours
    e506_offset = 0x3F1C7800
    with open('patches/e506.bf', 'rb') as event_file:
        iso_file.seek(e506_offset)
        iso_file.write(event_file.read())

    # hook the beginning of e601 to call our e506
    e601_hook_offset = 0x4049A254
    e601_hook = bytearray([0x1D, 0x00, 0xFA, 0x01, 0x08, 0x00, 0x66, 0x00])
    iso_file.seek(e601_hook_offset)
    iso_file.write(e601_hook)

    # write 0 to the vanilla stock increases to prevent >12 stock
    iso_file.seek(0x45D3469A)
    iso_file.write(bytes(0))
    iso_file.seek(0x49CB58B6)
    iso_file.write(bytes(0))
"""


def patch_special_fusions(rom):
    rom.write(struct.pack("<18x"), 0x0022EB78)
    rom.write(struct.pack("<192x"), 0x0022EBE0)

    # rom.seek(0x0022EB78)
    # for i in range(9):
    #     rom.write_halfword(0)
    # rom.seek(0x0022EBE0)
    # for i in range(85):
    #     rom.write_halfword(0)


def patch_fix_dummy_convo(rom):
    personality_offsets = [0x002DDF58, 0x002DF5D8, 0x002DF668, 0x002DF7B8, 0x002DFB78]
    for o in personality_offsets:
        rom.write_byte(0x0C, o)


def apply_asm_patch(rom, patch_path):
    assert os.path.exists(patch_path)
    with open(patch_path, "r") as f:
        for line in f:
            if line.startswith(";"):
                continue
            addr, value = map(int, line.split(","))
            rom.write_byte(value, addr)


def write_sp_item_strings(rom):
    names = [
        "Black Key",
        "White Key",
        "Red Key",
        "Apocalypse Stone",
        "Golden Goblet",
        "Eggplant",
        "Ongyo-Key",
    ]
    start_sp_name_table_offset = 0x002E93B4
    free_space_offset = 0x01FEE00
    description_msg_offset = 0x2F49E0

    for i, name in enumerate(names):
        off = free_space_offset + (i * 0x20)
        rom.write(name.encode(), off)
        rom.write_word(off + 0xFF000, start_sp_name_table_offset + (i * 4))

    items_path = os.path.join(PATCHES_PATH, "items.msg")
    with open(items_path, "rb") as file:
        rom.seek(description_msg_offset)
        rom.write(file.read())


def write_seed_strings(rom, seed):
    rom.write(struct.pack("<112x"), 0x43EE50)
    rom.write("Run rate is zero.".encode(), 0x43EE70)
    rom.write("Take double damage.".encode(), 0x43EE88)
    seed_msg = "Seed: {}".format(seed)
    if len(seed_msg) > 17:
        seed_msg = seed_msg[:14] + "..."
    rom.write(seed_msg.encode(), 0x43EE50)
    rom.write(seed_msg.encode(), 0x43EEA8)


def load_all(rom):
    load_skills(rom)  # Loading this first for logging purposes
    load_demons(rom)
    load_races()
    # load_skills(rom)
    load_magatamas(rom)
    load_battles(rom)


def write_all(rando, world):
    rom = rando.rom

    # save the AI of the vanilla tutorial demons before writing the randomized demons
    tutorial_ais = [
        rom.read(0xA4, all_demons[0x83].ai_offset),
        rom.read(0xA4, all_demons[0x5C].ai_offset),
        rom.read(0xA4, all_demons[0x89].ai_offset),
    ]

    write_demons(rom, world.demons.values())
    write_magatamas(rom, world.magatamas.values())
    write_battles(rom, world.battles.values())

    if world.skill_mutations:
        write_skill_changes(rom, world.skill_mutations)

    # make the random mitamas and elementals not show up in rag's shop
    apply_asm_patch(rom, os.path.join(PATCHES_PATH, "rags.txt"))
    # fix most non-recruitable demons and demon races
    apply_asm_patch(rom, os.path.join(PATCHES_PATH, "recruit.txt"))
    # make the pierce skill work on magic
    if rando.config_settings.magic_pierce:
        apply_asm_patch(rom, os.path.join(PATCHES_PATH, "pierce.txt"))
    # make aoe healing work on the stock demons
    if rando.config_settings.stock_healing:
        apply_asm_patch(rom, os.path.join(PATCHES_PATH, "healing.txt"))
    # make learnable skills always visible
    if rando.config_settings.visible_skills:
        apply_asm_patch(rom, os.path.join(PATCHES_PATH, "skills.txt"))
    # remove hard mode price multiplier
    if rando.config_settings.remove_hardmode_prices:
        apply_asm_patch(rom, os.path.join(PATCHES_PATH, "prices.txt"))
    # remove skill rank from inheritance odds and make demons able to learn all inheritable skills
    if rando.config_settings.fix_inheritance:
        apply_asm_patch(rom, os.path.join(PATCHES_PATH, "inherit.txt"))
    # apply TGE's hostFS patch
    if rando.config_export_to_hostfs:
        apply_asm_patch(rom, os.path.join(PATCHES_PATH, "hostfs.txt"))

    # remove magatamas from shops since they are all tied to boss drops now
    remove_shop_magatamas(rom)
    # patch the fusion table using the generated elemental results
    fix_elemental_fusion_table(rom, world.demon_generator)
    # make special fusion demons fuseable normally
    patch_special_fusions(rom)
    # swap tyrant to vile for pale rider, the harlot, & trumpeter fusion
    rom.write_byte(0x12, 0x22EDE3)

    # fix tutorial fights
    patch_fix_tutorials(rom, tutorial_ais, rando.dds3)
    # add the spyglass to 3x preta fight and reduce it's selling price
    patch_early_spyglass(rom)

    # replace the pazuzu mada summons
    fix_mada_summon(rom, world.demons.values())
    # replace the demons summoned by the nihilo minibosses
    fix_nihilo_summons(rom, world.demon_map)
    # replace koppa and incubus in the nihilo fight
    patch_incubus_koppa(rom, world.demon_map)
    # fix the magatama drop on the fused versions of specter 1
    """
    for b in world.battles.values():
        if b.offset == world.get_boss("Specter 1").check.offset:
            if b.reward:
                fix_specter_1_reward(rom, b.reward)
        elif b.offset == world.get_check("Girimehkala").offset:
            if b.reward:
                fix_girimehkala_reward(rom, b.reward)
        #elif b.offset == world.get_check("Futomimi").offset:
        #    if b.reward:
        #        fix_angel_reward(rom, b.reward)
        elif b.offset == world.get_boss("Ahriman").check.offset:
            if b.reward:
                fix_ahriman_reward(rom, b.reward)
        elif b.offset == world.get_boss("Noah").check.offset:
            if b.reward:
                fix_noah_reward(rom, b.reward)
    """

    # replace the DUMMY personality on certain demons
    patch_fix_dummy_convo(rom)

    write_sp_item_strings(rom)
    write_seed_strings(rom, rando.text_seed)
