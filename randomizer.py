# a lot of code modified from https://github.com/samfin/mmbn3-random/tree/cleanup
import random
import copy
import logging
import hashlib
import string
import sys
import os
import tkinter as tk
from collections import defaultdict
from io import BytesIO
from configparser import ConfigParser, NoOptionError

import nocturne
import logic
import races
import gui
from paths import RANDO_ROOT_PATH, PATCHES_PATH
from modified_scripts import Script_Modifier
from base_classes import *
from rom import Rom
from fs.Iso_FS import IsoFS
from fs.DDS3_FS import DDS3FS
from fs.LB_FS import LB_FS

with open(os.path.join(RANDO_ROOT_PATH, "version.txt"), "r") as f:
    VERSION = f.read().strip()
BETA = True
TEST = False

MD5_NTSC = "92e00a8a00c72d25e23d01694ac89193"

DEV_CHEATS = False


class Randomizer:
    def __init__(self, input_iso_path, seed, flags):
        self.input_iso_path = input_iso_path
        self.text_seed = seed
        self.flags = flags
        self.output_iso_path = ""

        # Config
        self.config_settings = Settings()
        self.config_make_logs = True  # Write various data to the logs/ folder
        self.config_export_to_hostfs = (
            False  # Build to folder with HostFS patch instead of an .iso
        )

    def init_iso_data(self):
        print("parsing iso")
        self.input_iso_file = IsoFS(self.input_iso_path)
        self.input_iso_file.read_iso()

        print("getting rom")
        rom_file = self.input_iso_file.get_file_from_path("SLUS_209.11;1")
        self.rom = Rom(rom_file)

        if not os.path.exists("out"):
            os.mkdir("out")

        if not os.path.exists("out/old_DDS3.DDT"):
            print("getting ddt")
            ddt_file = self.input_iso_file.get_file_from_path("DDS3.DDT;1")
            with open("out/old_DDS3.DDT", "wb") as file:
                file.write(ddt_file.read())

        if not os.path.exists("out/old_DDS3.IMG"):
            print("getting file system img")
            with open("out/old_DDS3.IMG", "wb") as file:
                for chunk in self.input_iso_file.read_file_in_chunks("DDS3.IMG;1"):
                    file.write(chunk)

        print("parsing dds3 fs")
        self.dds3 = DDS3FS("out/old_DDS3.DDT", "out/old_DDS3.IMG")
        self.dds3.read_dds3()

    def generate_demon_permutation(self, demon_gen):
        def swap_demon(d1, d2):
            for key, value in demon_map.items():
                if value == d1.ind:
                    demon_map[d2.ind], demon_map[key] = (
                        demon_map[key],
                        demon_map[d2.ind],
                    )
                    return

        all_demons = [d for d in nocturne.all_demons.values() if not d.is_boss]
        all_base = [d for d in all_demons if d.base_demon]
        all_elements = [d for d in all_demons if d.race == 7]
        all_mitamas = [d for d in all_demons if d.race == 8]
        all_fiends = [d for d in all_demons if d.race == 38]
        all_pixies = [d for d in all_demons if d.name == "Pixie"]
        the_pixie = all_pixies[0]

        demon_map = {}
        demon_pool = all_demons
        shuffled_pool = copy.copy(demon_pool)
        random.shuffle(shuffled_pool)

        for old_demon, new_demon in zip(demon_pool, shuffled_pool):
            demon_map[old_demon.ind] = new_demon.ind

        # iterate through each hospital demon looking for conflicts
        for demon in all_base:
            new_demon = nocturne.lookup_demon(demon_map.get(demon.ind))
            if new_demon.phys_inv:
                # choose a new demon from all non-hospital, non-phys invalid demons
                new_choice = random.choice(
                    [d for d in demon_pool if not d.phys_inv and not d.base_demon]
                )
                swap_demon(new_choice, demon)
                demon_pool.remove(new_choice)

        for element in all_elements:
            # find the element in generated demons
            chosen_demon = None
            d = next((d for d in demon_gen.demons if d.name == element.name), None)
            # choose a demon in demon pool that is the same level as the generated demon
            candidates = [c for c in demon_pool if c.level == d.level]
            try:
                chosen_demon = random.choice(candidates)
            except IndexError:
                print("error: No demon candidate for an element")
                candidates = [c for c in demon_pool if abs(c.level - d.level) < 6]
                chosen_demon = random.choice(candidates)
            # find the elemental in the map and swap
            if chosen_demon:
                demon_pool.remove(chosen_demon)
                swap_demon(element, chosen_demon)
            else:
                print("Error finding mutation for " + element.name)

        for mitama in all_mitamas:
            # find the mitama in generated demons
            chosen_demon = None
            d = next((d for d in demon_gen.demons if d.name == mitama.name), None)
            # choose a demon in demon pool that is the same level as the generated demon
            candidates = [c for c in demon_pool if c.level == d.level]
            try:
                chosen_demon = random.choice(candidates)
            except IndexError:
                print("error: No demon candidate for a mitama")
                candidates = [c for c in demon_pool if abs(c.level - d.level) < 6]
                chosen_demon = random.choice(candidates)
            # find the mitama in the map and swap
            if chosen_demon:
                demon_pool.remove(chosen_demon)
                swap_demon(mitama, chosen_demon)
            else:
                print("Error finding mutation for " + mitama.name)

        if self.config_settings.balance_pixie or self.config_settings.low_level_pixie:
            # find pixie in generated demons
            chosen_demon = None
            d = next((d for d in demon_gen.demons if d.name == the_pixie.name), None)
            # choose a demon in demon pool that is the same level as the generated demon
            candidates = [c for c in demon_pool if c.level == d.level]
            if not candidates:
                print("ERROR: No demon candidate for pixie")
                candidates = [c for c in demon_pool if abs(c.level - d.level) < 6]
            chosen_demon = random.choice(candidates)
            # find pixie in the map and swap
            if chosen_demon:
                demon_pool.remove(chosen_demon)
                swap_demon(the_pixie, chosen_demon)
            else:
                print("Error finding mutation for pixie")

        # get the fiends beforehand and shuffle since there isn't a direct connection beyond demon race
        generated_fiends = [
            d for d in demon_gen.demons if races.raceref[d.race] == "Fiend"
        ]
        random.shuffle(generated_fiends)
        for fiend in all_fiends:
            # use one of the randomly selected fiends
            chosen_demon = None
            gen_fiend = generated_fiends.pop()
            # choose a demon in demon pool that is the same level as the generated demon
            candidates = [c for c in demon_pool if c.level == gen_fiend.level]
            try:
                chosen_demon = random.choice(candidates)
            except IndexError:
                print("error: No demon candidate for a fiend")
                candidates = [
                    c for c in demon_pool if abs(c.level - gen_fiend.level) < 6
                ]
                chosen_demon = random.choice(candidates)
            # find the fiend in the map and swap
            if chosen_demon:
                demon_pool.remove(chosen_demon)
                swap_demon(fiend, chosen_demon)
            else:
                print("Error finding mutation for " + fiend.name)

        if self.config_make_logs:
            with open("logs/demon_spoiler_{}.txt".format(self.text_seed), "w") as f:
                for key, value in demon_map.items():
                    f.write(
                        "Vanilla {} became Randomized {}\n".format(
                            nocturne.lookup_demon(key).name,
                            nocturne.lookup_demon(value).name,
                        )
                    )

        return demon_map

    def generate_skill_permutation(
        self, balance_by_rank=True, ignored_skills=[]
    ):  # keep_pierce = False):
        skill_sets = defaultdict(list)
        # separare skills by rank
        for skill in nocturne.all_skills.values():
            skill_id = skill.rank
            if not balance_by_rank:
                # still keep special skills (boss/demon specific) separate
                if skill_id < 100:
                    skill_id = 1
                # treak attack/passive/recruitment skills differently
                skill_id += skill.skill_type * 1000
            # keep ignored skills separate
            if skill.ind in ignored_skills:
                skill_id = skill.ind
            skill_sets[skill_id].append(skill.ind)

        # shuffle inside each set
        skill_map = {}
        for key, vals in skill_sets.items():
            keys = copy.copy(vals)
            random.shuffle(vals)
            for old_skill, new_skill in zip(keys, vals):
                skill_map[old_skill] = new_skill

        return skill_map

    # Number of possible mutations = 55
    def randomize_skill_mutations(self):
        truth_map = {"True": True, "False": False}
        mutations = []
        with open("./data/better_mutations.txt", "r") as mutation_file:
            for line in mutation_file:
                mutations.append(line.strip().split(","))
        if self.config_settings.random_mutations:
            random.shuffle(mutations)
        slots_left = 55
        new_mutations = {}
        while (
            slots_left > 0 and mutations
        ):  # number of mutations should never reach 0, hopefully we always run out of slots
            mutation = mutations.pop(0)
            if (not self.config_settings.unique_mutations) and truth_map[mutation[0]]:
                continue
            if len(mutation) - 2 > slots_left:
                continue  # Too many skills in the upgrade sequence
            for i in range(1, len(mutation) - 1):
                base_skill = mutation[i]
                enhanced_skill = mutation[i + 1]
                if base_skill in new_mutations.keys():
                    continue  # Only one mutation per skill
                new_mutations[base_skill] = enhanced_skill
                slots_left -= 1
                pass
        with open("logs/skill_mutations_{}.txt".format(self.text_seed), "w") as file:
            for key, value in new_mutations.items():
                file.write(key + " to " + value + "\n")
        return new_mutations

    def randomize_stats(self, total_stats, req_min=True):
        # get total number of stat points
        if req_min:
            # remove 5 for the min 1 point per stat
            total_stats -= 5
            new_stats = [1, 1, 1, 1, 1]
        else:
            new_stats = [0, 0, 0, 0, 0]
        # keep track of non-maxed stats
        valid_stats = [0, 1, 2, 3, 4]
        # distribute stats randomly one at a time
        while total_stats > 0:
            # sanity check incase there are no more valid stats
            if not valid_stats:
                break
            choice = random.choice(valid_stats)
            # make sure stats don't go past max
            if (new_stats[choice] + 1) > 40:
                valid_stats.remove(choice)
                continue
            new_stats[choice] += 1
            total_stats -= 1

        return new_stats

    # ban victory cry and son's oath from showing up
    BANNED_SKILLS = [0x15C, 0x169, 0x165]

    def randomize_skills(self, new_demon, force_skills=None, skill_scaling=False):
        new_skills = []
        new_battle_skills = []
        is_pixie = bool(new_demon.name == "Pixie")

        starting_skills = random.randint(2, 4)
        total_skills = starting_skills + random.randint(4, 6)
        level = 0

        skill_pool = [
            s
            for s in list(nocturne.all_skills.values())
            if s.ind not in self.BANNED_SKILLS
        ]
        # re-add son's oath to skill pool for dante only
        if new_demon.name == "Dante":
            skill_pool.append(nocturne.lookup_skill(0x169))
        unique_pool = [s for s in skill_pool if s.rank >= 100]
        # remove unique skills from skill pool
        skill_pool = [s for s in skill_pool if s not in unique_pool]
        skill_pool.append(nocturne.lookup_skill(0x165))  # pierce becomes a normal skill
        random.shuffle(skill_pool)
        random.shuffle(unique_pool)

        # get the total number of unique skills for the demon
        num_of_unique = 0
        for s in new_demon.skills:
            s = nocturne.lookup_skill(s["skill_id"])
            if not s:
                continue
            if s.rank >= 100:
                num_of_unique += 1
        if (
            num_of_unique == 0 and random.randrange(100) < 7
        ):  # Demons have a small chance to gain a unique skill
            num_of_unique += 1
        # add any forced skills first
        if force_skills:
            for s in force_skills:
                skill = {
                    "level": level,
                    "skill_id": s,
                    "event": 1,
                }
                new_skills.append(skill)
                for p in skill_pool:
                    if p.ind == s:
                        skill_pool.remove(p)
                        break
                total_skills -= 1
        # this is mainly for Dante who has like 10 unique skills
        if num_of_unique >= total_skills:
            total_skills = num_of_unique + 1
        # make sure demons can't learn more than 8 skills
        if (total_skills - starting_skills) > 8:
            starting_skills = min(total_skills - 8, 8)
        # randomly select nonunique skills
        chosen_skills = random.sample(skill_pool, total_skills - num_of_unique)
        # randomly select unique skills and add it to the list + shuffle
        chosen_skills += random.sample(unique_pool, num_of_unique)
        random.shuffle(chosen_skills)
        rejected_skills = (
            []
        )  # skills that are initially passed over for being too high level
        weak_skills = (
            []
        )  # Skills that are initially passed over for being much lower level

        for i in range(total_skills):
            chosen_skill = chosen_skills.pop()

            # add skills that can be used in battle to battle_skills, if they are of the appropriate level
            if (
                chosen_skill.skill_type == 1
                and len(new_battle_skills) < 8
                and chosen_skill.name
                not in [
                    "Analyze",
                    "Trafuri",
                    "Beckon Call",
                    "Riberama",
                    "Lightoma",
                    "Liftoma",
                    "Estoma",
                ]
            ):
                if (
                    chosen_skill.level <= new_demon.level
                    and chosen_skill.level
                    >= min(new_demon.level - 20, new_demon.level / 2)
                ) or not skill_scaling:
                    if skill_scaling or (
                        chosen_skill.ind not in [0x104, 0x11F]
                    ):  # remove gods bow and death flies if skill scaling is disabled
                        new_battle_skills.append(chosen_skill.ind)
                elif chosen_skill.level > new_demon.level:
                    rejected_skills.append(chosen_skill)
                else:
                    weak_skills.append(chosen_skill)

            if len(new_skills) >= starting_skills:
                if is_pixie or level == 0:
                    level = new_demon.level + 1
                else:
                    level += 1

            skill = {
                "level": level,
                "skill_id": chosen_skill.ind,
                "event": 1,
            }
            new_skills.append(skill)

        if (
            len(rejected_skills) > 0
        ):  # Attempt to give at least 3 skills to demons, provided they have skills that aren't too much above their level
            rejected_skills.sort(key=lambda x: x.level)
            while len(new_battle_skills) < 3 and len(rejected_skills) > 0:
                skill_count = len(new_battle_skills)
                next_skill = rejected_skills.pop(0)
                if skill_count == 0 or next_skill.level <= new_demon.level + (
                    30 - skill_count * 10
                ):
                    new_battle_skills.append(next_skill.ind)
                else:
                    break

        if (
            len(weak_skills) > 0
        ):  # Demon AI can only know 5 skills, so prioritize strong skills for high level demons
            weak_skills.sort(key=lambda x: x.level, reverse=True)
            while len(new_battle_skills) < 5 and len(weak_skills) > 0:
                skill_count = len(new_battle_skills)
                next_skill = weak_skills.pop(0)
                new_battle_skills.append(next_skill.ind)

        if DEV_CHEATS:
            new_battle_skills = [
                0x33,
                0x2D,
                0x2B,
                0x30,
                0xD4,
            ]  # Recarmdra, Eternal Rest, and 3 status cures

        return [new_skills, new_battle_skills]

    def rebalance_demon(
        self,
        old_demon,
        new_level,
        stats=None,
        new_hp=-1,
        new_mp=-1,
        new_exp=-1,
        new_macca=-1,
        exp_mod=1,
        stat_mod=1,
        macca_mod=1,
    ):
        new_demon = copy.copy(old_demon)
        level_mod = new_level / old_demon.level
        new_demon.level = int(new_level)
        if stats:
            total_stats = sum(stats) * stat_mod
        else:
            # generate stats based on level if they aren't supplied
            total_stats = (20 + new_level) * stat_mod
        new_demon.stats = self.randomize_stats(int(total_stats))
        if new_hp > 0:
            new_demon.hp = new_hp
        else:
            # generate hp based on level and vitality stat if they aren't supplied
            new_demon.hp = (6 * new_demon.level) + (6 * new_demon.stats[2])
            if DEV_CHEATS:
                new_demon.hp = 10
        new_demon.hp = min(int(new_demon.hp), 0xFFFF)
        if new_mp > 0:
            new_demon.mp = new_mp
        else:
            # generate mp based on level and magic stat if they aren't supplied
            new_demon.mp = (3 * new_demon.level) + (3 * new_demon.stats[1])
        new_demon.mp = min(int(new_demon.mp), 0xFFFF)
        if new_exp > 0:
            exp = new_exp * exp_mod
        else:
            # this gives horrible values if the level difference is extreme
            exp = round(old_demon.exp_drop * exp_mod * stat_mod * level_mod)
        new_demon.exp_drop = int(min(exp, 0xFFFF))
        if new_macca > 0:
            macca = new_macca * macca_mod
        else:
            # this gives horrible values if the level difference is extreme
            macca = round(old_demon.macca_drop * macca_mod * stat_mod * level_mod)
        new_demon.macca_drop = int(min(macca, 0xFFFF))

        return new_demon

    # Make the new boss have the exact stats of the old boss
    def rebalance_demon_stat_copy(
        self,
        old_demon,
        new_level,
        new_hp=-1,
        new_mp=-1,
        new_exp=-1,
        new_macca=-1,
        exp_mod=1,
        stats=[1, 1, 1, 1, 1],
        macca_mod=1,
    ):
        new_demon = copy.copy(old_demon)
        level_mod = new_level / old_demon.level
        new_demon.level = int(new_level)
        new_demon.stats = stats
        if new_hp > 0:
            new_demon.hp = new_hp
        else:
            # generate hp based on level and vitality stat if they aren't supplied
            new_demon.hp = (6 * new_demon.level) + (6 * new_demon.stats[2])
        new_demon.hp = min(int(new_demon.hp), 0xFFFF)
        if new_mp > 0:
            new_demon.mp = new_mp
        else:
            # generate mp based on level and magic stat if they aren't supplied
            new_demon.mp = (3 * new_demon.level) + (3 * new_demon.stats[1])
        new_demon.mp = min(int(new_demon.mp), 0xFFFF)
        if new_exp > 0:
            exp = new_exp * exp_mod
        else:
            # this gives horrible values if the level difference is extreme
            exp = round(old_demon.exp_drop * exp_mod * level_mod)
        new_demon.exp_drop = int(min(exp, 0xFFFF))
        if new_macca > 0:
            macca = new_macca * macca_mod
        else:
            # this gives horrible values if the level difference is extreme
            macca = round(old_demon.macca_drop * macca_mod * level_mod)
        new_demon.macca_drop = int(min(macca, 0xFFFF))

        return new_demon

    def randomize_demons(
        self,
        demon_map,
        generated_demons,
        exp_mod=1,
        enemy_skill_scaling=False,
        macca_mod=1,
    ):
        new_demons = []
        if self.config_settings.low_level:
            exp_mod = 0
        # buffs/debuffs to give to base demons + tetraja
        skills_to_distribute = [52, 53, 54, 57, 64, 65, 66, 67, 77, 68]
        random.shuffle(skills_to_distribute)
        # take the stats from old_demon and use them to rebalance the new_demon permutation
        demon_pool = [d for d in nocturne.all_demons.values() if not d.is_boss]
        for old_demon in demon_pool:
            new_demon = demon_map[old_demon.ind]
            new_demon = nocturne.lookup_demon(new_demon)
            new_demon = self.rebalance_demon(
                new_demon,
                old_demon.level,
                stats=old_demon.stats,
                new_exp=old_demon.exp_drop,
                new_macca=old_demon.macca_drop,
                exp_mod=exp_mod,
                macca_mod=macca_mod,
            )
            assigned_new_race = False
            # don't change elemental race
            if new_demon.race == 7:
                d = next(
                    (
                        d
                        for d in generated_demons
                        if races.raceref[d.race] == new_demon.name
                    ),
                    None,
                )
                if d:
                    generated_demons.remove(d)
                    assigned_new_race = True
            # don't change mitama race
            elif new_demon.race == 8:
                d = next(
                    (d for d in generated_demons if d.name == new_demon.name), None
                )
                if d:
                    generated_demons.remove(d)
                    assigned_new_race = True
            # don't change fiend race
            elif new_demon.race == 38:
                d = next(
                    (
                        d
                        for d in generated_demons
                        if races.raceref[d.race] == "Fiend"
                        and d.level == old_demon.level
                    ),
                    None,
                )
                if d:
                    generated_demons.remove(d)
                    assigned_new_race = True
            # change the race based on the generated demons
            else:
                for d in generated_demons:
                    race = races.raceref[d.race]
                    if (
                        race in ["Erthys", "Aeros", "Aquans", "Flaemis"]
                        or race == "Mitama"
                        or race == "Fiend"
                    ):
                        continue
                    elif old_demon.level == d.level:
                        generated_demons.remove(d)
                        race_ind = nocturne.race_names.index(race) + 1
                        new_demon.race = race_ind
                        assigned_new_race = True
                        break
            if not assigned_new_race:
                print("Error: Could not rebalance " + new_demon.name)
                return
            new_demon.base_demon = bool(old_demon.base_demon)
            if old_demon.base_demon:
                old_demon.base_demon = False
            # distribute basic buffs to the base demons
            if new_demon.name == "Pixie":
                if DEV_CHEATS:
                    new_demon.skills, new_demon.battle_skills = self.randomize_skills(
                        new_demon, [73, 269]
                    )  # Estoma and showtime
                else:
                    # Always give Pixie Estoma and Riberama
                    new_demon.skills, new_demon.battle_skills = self.randomize_skills(
                        new_demon, [73, 74]
                    )
            elif new_demon.base_demon and len(skills_to_distribute) > 0:
                skill = [skills_to_distribute.pop()]
                new_demon.skills, new_demon.battle_skills = self.randomize_skills(
                    new_demon, skill, enemy_skill_scaling
                )
            else:
                new_demon.skills, new_demon.battle_skills = self.randomize_skills(
                    new_demon, None, enemy_skill_scaling
                )
            new_demon.old_id = old_demon.ind  # keep track of who is replaced
            new_demons.append(new_demon)

        return new_demons

    def randomize_magatamas(self):
        new_magatamas = []
        # remove Watchful, Beckon Call, Estoma, Riberama, Lightoma, Liftoma, Sacrifice, Kamikaze, Last Resort, Victory Cry, Son's Oath, Pierce, Recarmdra
        ignored_skills = [354, 223, 73, 74, 75, 76, 115, 116, 152, 348, 361, 357, 51]
        # make one skill_map for all magatamas to prevent duplicate skills
        skill_map = self.generate_skill_permutation(False, ignored_skills)
        for old_magatama in nocturne.all_magatamas.values():
            new_magatama = copy.copy(old_magatama)
            if (
                new_magatama.name != "Marogareh"
            ):  # Ensure tutorial is beatable on hard mode
                new_magatama.stats = self.randomize_stats(
                    sum(new_magatama.stats), False
                )
            new_skills = []
            for skill in new_magatama.skills:
                ind = skill["skill_id"]
                new_skill = skill_map.get(ind)
                if new_skill:
                    skill["skill_id"] = new_skill
                skill["level"] = skill["level"] + new_magatama.level
                new_skills.append(skill)
            new_magatama.skills = new_skills
            new_magatamas.append(new_magatama)

        return new_magatamas

    def randomize_battles(self, demon_map):
        new_battles = []
        for b in nocturne.all_battles.values():
            new_battle = copy.deepcopy(b)
            # check if it the battle is a scripted fight or not
            if b.is_boss:
                for i, d in enumerate(b.enemies):
                    if d > 0:
                        demon = nocturne.lookup_demon(d)
                        if not demon:
                            continue
                        # don't change any of the early scripted fights
                        if not demon.is_boss or demon.name not in [
                            "Will o' Wisp",
                            "Kodama",
                            "Preta",
                        ]:
                            new_demon = demon_map.get(d)
                            if new_demon:
                                new_battle.enemies[i] = new_demon
                        else:
                            continue
            else:
                for i, d in enumerate(b.enemies):
                    if d > 0:
                        new_demon = demon_map.get(d)
                        if new_demon:
                            new_battle.enemies[i] = new_demon
            new_battles.append(new_battle)
        return new_battles

    # Additional demons in certain boss fights
    boss_extras = {
        "Albion (Boss)": [279, 280, 281, 282],  # Urizen, Luvah, Tharmas, Urthona
        "White Rider (Boss)": [359],  # Virtue
        "Red Rider (Boss)": [360],  # Power
        "Black Rider (Boss)": [361],  # Legion
        "Pale Rider (Boss)": [358],  # Loa
        "Atropos 2 (Boss)": [326, 327],  # Clotho, Lachesis
        "Berith (Boss)": [313],  # Succubus
        "Noah 1st Form (Boss)": [259],  # Noah 2nd Form
        "Kagutsuchi 1st Form (Boss)": [264],  # Kagutsuchi 2nd Form
        "Baal Avatar (Boss)": [289, 290],  # Hallel Flauros, Hallel Ose
        "Specter 1 (Boss)": [294, 295, 296],  # All fused specters
        "Ahriman 1st Form (Boss)": [258],  # Ahriman 2nd Form
        "Raphael (Boss)": [284, 286],  # Gabriel, Uriel
    }

    # bosses that should always go first regardless of settings, removing Matador and Mizuchi for now
    always_goes_first = [
        "Specter 1 (Boss)",
        "Specter 2 (Boss)",
        "Specter 3 (Boss)",
        "Ongyo-Ki (Boss)",
        "White Rider (Boss)",
        "Red Rider (Boss)",
        "Black Rider (Boss)",
        "Pale Rider (Boss)",
        "Albion (Boss)",
        "Trumpeter (Boss)",
        "Ahriman 1st Form (Boss)",
    ]
    never_goes_first = [
        "Baal Avatar (Boss)",
        "Lucifer (Boss)",
        "Samael (Boss)",
        "Bishamon 2 (Boss)",
        "Koumoku (Boss)",
    ]
    go_first_checks = [
        "Matador (Boss)",
        "Daisoujou (Boss)",
        "Hell Biker (Boss)",
        "Mizuchi (Boss)",
        "Black Frost (Boss)",
        "The Harlot (Boss)",
        "Mara (Boss)",
        "Futomimi (Boss)",
        "Trumpeter (Boss)",
        "Bishamon 1 (Boss)",
        "Surt (Boss)",
        "Mada (Boss)",
        "Dante 2 (Boss)",
        "Beezlebub Fly (Boss)",
        "Metatron (Boss)",
    ]

    def randomize_boss_battles(self, world):
        boss_demons = []
        boss_battles = []

        for check in world.get_checks():
            old_boss = world.get_boss(check.name)
            new_boss = check.boss

            boss_battle = copy.deepcopy(new_boss.battle)
            boss_battle.offset = check.offset

            old_boss_demon = next(
                (nocturne.lookup_demon(d) for d in old_boss.battle.enemies if d > 0),
                None,
            )
            new_boss_demon = copy.copy(
                next(
                    (
                        nocturne.lookup_demon(d)
                        for d in new_boss.battle.enemies
                        if d > 0
                    ),
                    None,
                )
            )

            if old_boss.name == "Berith":
                old_boss_demon = nocturne.lookup_demon(312)
            if new_boss.name == "Berith":
                new_boss_demon = nocturne.lookup_demon(312)

            new_level = old_boss_demon.level

            new_hp = old_boss_demon.hp
            new_mp = old_boss_demon.mp

            if DEV_CHEATS:
                new_hp = 10

            new_exp = old_boss_demon.exp_drop
            new_macca = old_boss_demon.macca_drop

            if old_boss is not new_boss:
                if new_level < new_boss_demon.level:
                    new_level /= 2
                # if the new boss is replacing the Sisters or Kaiwans triple hp and mp. Also Ahriman, Noah, Kagutsuchi, Albion, and Archangels
                if old_boss_demon.name in [
                    "Atropos 2 (Boss)",
                    "Kaiwan (Boss)",
                    "Ahriman 1st Form (Boss)",
                    "Noah 1st Form (Boss)",
                    "Raphael (Boss)",
                    "Kagutsuchi 1st Form (Boss)",
                    "Albion (Boss)",
                ]:
                    new_hp *= 3
                    if old_boss_demon.name in [
                        "Atropos 2 (Boss)",
                        "Kaiwan (Boss)",
                        "Raphael (Boss)",
                        "Albion (Boss)",
                    ]:
                        new_exp *= 3
                        new_macca *= 3
                    if old_boss_demon.name == "Kaiwan (Boss)":
                        new_mp *= 3
                # if the new boss is replacing a Specter, do 6 times hp and mp
                if old_boss_demon.name in [
                    "Specter 1 (Boss)",
                    "Specter 2 (Boss)",
                    "Specter 3 (Boss)",
                ]:
                    new_hp *= 6
                    new_exp *= 6
                    new_macca *= 6
                    new_mp *= 6
                    # if old_boss_demon.name == "Specter 2 (Boss)":
                    #    new_mp *= 10
                # if the new boss is replacing gary, compensate for Sakahagi's exp and macca
                if old_boss_demon.name == "Girimehkala (Boss)":
                    new_exp *= 7
                    new_macca *= 10
                # if the new boss is the Sisters or Kaiwans divide the hp pool evenly between the 3
                if new_boss_demon.name in [
                    "Atropos 2 (Boss)",
                    "Kaiwan (Boss)",
                    "Raphael (Boss)",
                ]:
                    new_hp = round(new_hp / 3)
                    new_exp = round(new_exp / 3)
                    new_macca = round(new_macca / 3)
                    if new_boss_demon.name == "Kaiwan (Boss)":
                        new_mp = round(new_mp / 3)
                # if the new boss is a Specter, divide hp and mp by 6
                if new_boss_demon.name in [
                    "Specter 1 (Boss)",
                    "Specter 2 (Boss)",
                    "Specter 3 (Boss)",
                ]:
                    new_hp = round(new_hp / 6)
                    new_exp = round(new_exp / 6)
                    new_macca = round(new_macca / 6)
                    new_mp = round(new_mp / 6)
                    # if new_boss_demon.name == "Specter 2 (Boss)":
                    #    new_mp = 40
                # if the new boss is Noah, Lucifer, or Kagutsuchi, divide hp by 3, add Ahriman later?
                if new_boss_demon.name in [
                    "Noah 1st Form (Boss)",
                    "Kagutsuchi 1st Form (Boss)",
                    "Lucifer (Boss)",
                    "Ahriman 1st Form (Boss)",
                ]:
                    new_hp = round(new_hp / 3)
                # if the new boss is mara half it's HP with a cap of 4000
                if new_boss_demon.name == "Mara (Boss)":
                    new_hp = round(new_hp / 2)
                    new_hp = min(new_hp, 4000)
                if new_boss_demon.name == "Ongyo-Ki (Boss)":
                    new_hp = round(new_hp / 4)
                    new_exp = round(new_exp / 8)
                    new_macca = round(new_macca / 8)
                if new_boss_demon.name not in self.always_goes_first:
                    if (
                        new_boss_demon.name in self.never_goes_first
                        or not self.config_settings.bosses_go_first_more_often
                        or old_boss_demon.name not in self.go_first_checks
                    ):
                        boss_battle.goes_first = 0x0D
                    elif old_boss_demon.name in self.go_first_checks:
                        boss_battle.goes_first = old_boss.battle.goes_first
                # balanced_demon = self.rebalance_demon(new_boss_demon, new_level, new_hp=new_hp, new_mp=new_mp, new_exp=new_exp, new_macca=new_macca, exp_mod=self.config_settings.exp_modifier, stat_mod=1)
                balanced_demon = self.rebalance_demon_stat_copy(
                    new_boss_demon,
                    new_level,
                    new_hp=new_hp,
                    new_mp=new_mp,
                    new_exp=new_exp,
                    new_macca=new_macca,
                    exp_mod=self.config_settings.exp_modifier,
                    stats=old_boss_demon.stats,
                    macca_mod=self.config_settings.macca_modifier,
                )
            else:
                balanced_demon = old_boss_demon
                if DEV_CHEATS:
                    balanced_demon.hp = 10
                new_exp *= self.config_settings.exp_modifier
                new_macca *= self.config_settings.macca_modifier
                balanced_demon.exp_drop = int(min(new_exp, 0xFFFF))
            boss_demons.append(balanced_demon)
            # balance any extra demons that show up in the fight
            extras = self.boss_extras.get(new_boss_demon.name)
            if extras and (old_boss is not new_boss or DEV_CHEATS):
                new_hp = -1
                new_mp = -1
                new_level = balanced_demon.level
                stat_mod = 1
                exp_mod = self.config_settings.exp_modifier
                if new_boss_demon.name in [
                    "White Rider (Boss)",
                    "Red Rider (Boss)",
                    "Black Rider (Boss)",
                    "Pale Rider (Boss)",
                ]:
                    # stat_mod = 0.75
                    new_level = round(new_level * 0.85)
                elif new_boss_demon.name == "Albion (Boss)":
                    new_level = round(new_level * 0.75)
                    exp_mod = 1
                elif new_boss_demon.name in ["Atropos 2 (Boss)", "Raphael (Boss)"]:
                    new_hp = balanced_demon.hp
                    new_mp = balanced_demon.mp
                elif new_boss_demon.name == "Berith (Boss)":
                    new_hp = round(balanced_demon.hp * 0.3)
                    new_mp = round(balanced_demon.mp * 0.3)
                elif new_boss_demon.name in [
                    "Noah 1st Form (Boss)",
                    "Kagutsuchi 1st Form (Boss)",
                    "Ahriman 1st Form (Boss)",
                    "Specter 1 (Boss)",
                ]:  # Could deal with the different forms later
                    new_hp = balanced_demon.hp * 2
                    new_mp = balanced_demon.mp * 2
                elif new_boss_demon.name == "Baal Avatar (Boss)":
                    new_hp = round(balanced_demon.hp / 2)
                    new_mp = round(balanced_demon.mp / 2)
                for d in extras:
                    # phase change bosses keep the stat mirroring, minions have random stats.
                    if new_boss_demon.name in [
                        "Noah 1st Form (Boss)",
                        "Kagutsuchi 1st Form (Boss)",
                        "Ahriman 1st Form (Boss)",
                        "Specter 1 (Boss)",
                    ]:
                        d = self.rebalance_demon_stat_copy(
                            nocturne.lookup_demon(d),
                            new_level,
                            new_hp=new_hp,
                            new_mp=new_mp,
                            exp_mod=exp_mod,
                            stats=old_boss_demon.stats,
                            macca_mod=self.config_settings.macca_modifier,
                        )
                    else:
                        d = self.rebalance_demon(
                            nocturne.lookup_demon(d),
                            new_level,
                            new_hp=new_hp,
                            new_mp=new_mp,
                            exp_mod=exp_mod,
                            stat_mod=stat_mod,
                            macca_mod=self.config_settings.macca_modifier,
                        )
                    boss_demons.append(d)

            # get rid of any vanilla magatama drops
            if 345 >= boss_battle.reward >= 320:
                boss_battle.reward = 0
            # add our generated magatama drop
            if new_boss.reward is not None:
                magatama = nocturne.all_magatamas[new_boss.reward.name]
                boss_battle.reward = magatama.ind + 320
                magatama.level = min(magatama.level, round(old_boss_demon.level / 2))

            if self.config_settings.check_based_music:
                boss_battle.music = old_boss.battle.music
                if (
                    old_boss_demon.name == "kagutsuchi 1st Form (Boss)"
                    and old_boss is not new_boss
                ):
                    boss_battle.music = 8
            elif self.config_settings.random_music:
                # music randomizer, 8 is maybe kagutsuchi phase 2?
                boss_battle.music = random.choice([5, 6, 7, 8, 9, 10, 11, 12, 13, 14])

            # Sakahagi returns?
            # if old_boss_demon.name == 'Girimehkala (Boss)':
            #    boss_battle.phase_value = 2
            #    #print(old_boss.battle.reinforcement_value)

            boss_battles.append(boss_battle)

        return boss_demons, boss_battles

    def write_demon_log(self, output_path, demons):
        with open(output_path, "w") as file:
            for demon in demons:
                file.write(str(vars(demon)) + "\n\n")

    def get_md5(self, file_path):
        # from https://stackoverflow.com/questions/1131220/get-md5-hash-of-big-files-in-python
        with open(file_path, "rb") as f:
            input_md5 = hashlib.md5()
            while True:
                chunk = f.read(2**20)
                if not chunk:
                    break
                input_md5.update(chunk)

        input_md5 = input_md5.hexdigest()
        with open(file_path + ".md5", "w") as f:
            f.write(input_md5)

        return input_md5

    def export_to_iso(self):
        print("exporting modified dds3 fs")
        self.dds3.export_dds3("out/DDS3.DDT", "out/DDS3.IMG")

        if TEST:
            self.output_iso_path = "out/output.iso"
        else:
            self.output_iso_path = "out/nocturne_rando_{}.iso".format(self.text_seed)
        print("exporting randomized iso to {}".format(self.output_iso_path))
        self.input_iso_file.add_new_file("SLUS_209.11;1", BytesIO(self.rom.buffer))
        self.input_iso_file.rm_file("DUMMY.DAT;1")

        with open("out/DDS3.DDT", "rb") as ddt, open("out/DDS3.IMG", "rb") as img:
            self.input_iso_file.export_iso(
                self.output_iso_path, {"DDS3.DDT;1": ddt, "DDS3.IMG;1": img}
            )
        """
        if not TEST:
            print('cleaning up files')
            os.remove('out/DDS3.DDT')
            os.remove('out/DDS3.IMG')
            os.remove('out/old_DDS3.DDT')
            os.remove('out/old_DDS3.IMG')
        """

    def export_to_hostfs(self):
        print("exporting modified dds3 fs")
        self.dds3.export_dds3_to_folder("out/dds3data")

        print("exporting MOVIE folder")
        if not os.path.exists("out/dds3data/MOVIE"):
            os.mkdir("out/dds3data/MOVIE")

        for child in self.input_iso_file.find_by_path("MOVIE").children.values():
            if child.name in [".", ".."]:
                continue
            with open("out/dds3data/MOVIE/" + child.name[:-2], "wb") as f:
                f.write(self.input_iso_file.get_file_from_path(child.file_path).read())

        print("exporting binary")
        with open("out/SLUS_209.11.ELF", "wb") as f:
            f.write(self.rom.buffer)

        if not TEST:
            print("cleaning up files")
            os.remove("out/old_DDS3.DDT")
            os.remove("out/old_DDS3.IMG")

        print(
            'be sure to change "HostFs=disabled" to "HostFs=enabled" in your emulator\'s "inis/PCSX2_vm.ini" file'
        )

    def run(self):
        print("SMT3 Nocturne Randomizer version {}\n".format(VERSION))
        if BETA:
            print(
                "WARNING: This is a beta build and things may not work as intended.\nContact TristanS if you encounter any bugs\n"
            )

        try:
            (
                self.config_settings,
                self.input_iso_path,
                self.text_seed,
                self.settings_seed,
                self.config_export_to_host_fs,
            ) = gui.create_gui(self.config_settings)
        except OSError:
            return

        print("Settings seed is: " + self.settings_seed)

        # if self.text_seed is None:
        #    self.text_seed = input("Please input your desired seed value (blank for random seed):\n> ").strip()
        #    print()
        if self.text_seed == "":
            self.text_seed = "".join(
                random.choices(string.ascii_uppercase + string.digits, k=10)
            )
            print("Your generated seed is: {}\n".format(self.text_seed))
        self.full_seed = "{}-{}-{}".format(VERSION, self.text_seed, self.settings_seed)
        seed = int(hashlib.sha256(self.full_seed.encode("utf-8")).hexdigest(), 16)
        random.seed(seed)

        if not TEST:
            if os.path.exists(self.input_iso_path + ".md5"):
                with open(self.input_iso_path + ".md5", "r") as f:
                    input_md5 = f.read().strip()
            else:
                print("Testing MD5 hash of input file. (This can take a while)")
                input_md5 = self.get_md5(self.input_iso_path)

            if input_md5 != MD5_NTSC:
                print(
                    "WARNING: The MD5 of the provided ISO file does not match the MD5 of an unmodified Nocturne ISO"
                )
                response = input("Continue? y/n\n> ")
                print()
                if not response[:1].lower() == "y":
                    return

        print("opening iso")
        self.init_iso_data()

        if not os.path.exists("logs"):
            os.mkdir("logs")

        logger = logging.getLogger("")
        if self.config_make_logs:
            logging.basicConfig(
                filename="logs/spoiler_{}.log".format(self.text_seed),
                level=logging.INFO,
            )
            with open("logs/spoiler_{}.log".format(self.text_seed), "w") as f:
                f.write("")

        print("initializing data")
        nocturne.load_all(self.rom)
        # if self.config_make_logs:
        #     self.write_demon_log('logs/demons.txt', nocturne.all_demons.values())

        print("creating logical progression")
        # generate a world and come up with a logical boss and boss magatama drop progression
        # logic can sometimes get stuck shuffling bosses so keep generating until you get a valid world
        world = None
        while world is None:
            world = logic.create_world(self.config_settings)
            world = logic.randomize_world(world, logger, self.config_settings)
        world.seed = self.text_seed

        # adjust the level of the bonus magatama
        nocturne.all_magatamas[world.bonus_magatama.name].level = 4

        print("randomizing demons")
        # generate demon levels and races making sure all demons are fuseable
        demon_generator = races.all_demons(races.demon_levels, races.demon_names)
        demon_generator.generate(config_settings=self.config_settings)
        # generate_demon_permutation disregards demon names for most races for better randomization (non-element/mitama)
        demon_map = self.generate_demon_permutation(demon_generator)
        # randomize and rebalance all demon stats
        new_demons = self.randomize_demons(
            demon_map,
            demon_generator.demons,
            exp_mod=self.config_settings.exp_modifier,
            enemy_skill_scaling=self.config_settings.enemy_skill_scaling,
            macca_mod=self.config_settings.macca_modifier,
        )

        print("randomizing battles")
        # mutate all the non-boss demons using demon_map
        new_battles = self.randomize_battles(demon_map)
        # rebalance boss battles based on their check in the world
        new_bosses, new_boss_battles = self.randomize_boss_battles(world)
        new_demons.extend(new_bosses)
        new_battles.extend(new_boss_battles)
        if self.config_make_logs:
            self.write_demon_log(
                "logs/random_demons_{}.txt".format(self.text_seed), new_demons
            )

        # magatamas have to be randomized AFTER boss battles to correctly rebalance their levels
        print("randomizing magatamas")
        new_magatamas = self.randomize_magatamas()

        # randomize/fix skill mutations if settings flags are set
        if self.config_settings.better_mutations:
            world.skill_mutations = self.randomize_skill_mutations()

        # Add all the new demons, magatamas, and bosses to the world
        world.add_demons(new_demons)
        world.add_battles(new_battles)
        world.add_magatamas(new_magatamas)
        world.demon_generator = demon_generator
        world.demon_map = demon_map

        # write all changes to the binary buffer
        print("writing changes to binary")
        nocturne.write_all(self, world)

        print("patching scripts")
        script_modifier = Script_Modifier(self.dds3)
        script_modifier.run(world, self.config_settings)

        # just overwrite the old title screen tmx
        # I'm too lazy to rewrite the lb fs just for this
        title_screen_lb_data = self.dds3.get_file_from_path("/title/titletex.LB")
        with open(os.path.join(PATCHES_PATH, "t_logo.tmx"), "rb") as f:
            title_screen_lb_data.seek(0x20440)
            title_screen_lb_data.write(f.read())
        self.dds3.add_new_file("/title/titletex.LB", title_screen_lb_data)

        if self.config_export_to_hostfs:
            self.export_to_hostfs()
        else:
            self.export_to_iso()


if __name__ == "__main__":
    input_path = None
    seed = None
    flags = None
    if TEST:
        input_path = "out/input.iso"
        seed = ""
        flags = string.ascii_lowercase
    if len(sys.argv) > 1:
        input_path = sys.argv[1].strip()
    if len(sys.argv) > 2:
        seed = sys.argv[2].upper().strip()
    if len(sys.argv) > 3:
        flags = sys.argv[3].strip()
    rando = Randomizer(input_path, seed, flags)
    rando.run()
    input("Press [Enter] to exit")
