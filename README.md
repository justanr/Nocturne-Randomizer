### Nocturne-Randomizer

This is a randomizer for Shin Megami Tensei: Nocturne.

The randomization includes: boss shuffle, enemy/demon shuffle, skill randomization, Magatama and key item drops by bosses, and race randomizer for fusion logic.

We are currently in the alpha/beta stages, and the randomizer itself is not complete with Labyrinth of Amala being blocked off. Expect changes to be frequent and game balance to be shaky.

For the original randomizer website, see https://github.com/nmarkro/Nocturne-Randomizer/
See Changes.txt for all the differences from the base branch

Feel free to join the Nocturne Randomizer discord: https://discord.gg/d25ZAha

### Credits

The randomizer was created and programmed by NMarkro and PinkPajamas, with additional help from:

ChampionBeef (early testing and feedback)

TGEnigma (for the AtlusScriptToolchain tools used during development)

Krisan Thyme (file format and tools documentation)

Zombero (documentation from hardtye hack)

### Running the randomizer

Windows users can download the code as a zip from this page

Unzip and run nocturne_rando.exe

Using PCSX2 v1.5.0 or higher is recommended (download from https://pcsx2.net/download/development/dev-windows.html)

### Running the randomizer from source

Install python 3 at https://python.org

Run with: python3 randomizer.py

### Using the HostFS export format
Run nocturne_rando.exe (or from source) and follow the prompts to export to HostFS

Navigate to your PCSX2's "inis" folder and change the line "HostFs=disabled" to "HostFs=enabled" in "PCSX2_vm.ini"

Select your base, unmodified Nocturne ISO in PCSX2 and use "System -> Run ELF" and select "out/SLUS_209.11.ELF" from the randomizer's folder to boot your randomized version of Nocturne 

### Details for the randomizer's settings

If don't want to worry about choosing individual settings, you can select one of three presets on the top right based on difficulty. Click on 'use preset' to apply it.

**Better skill mutations** - Tired of dark might changing into might? These settings replace the vanilla skill mutations with ones you'd actually like to see. Because the total number of mutations has to be 55, there is a 'standard' option to use a curated list. The random options will choose 55 mutations from a larger pool. Note that allowing skills to mutate into unique skills may make fusion worse.

**Ending Selector** - Auto TDE will let you learn pierce after lowering the tower of Kagutsuchi with the Himorogi. The Labyrinth of Amala will also close when you lower ToK regardless of ending. If you choose a reason ending and complete Labyrinth of Amala, the game will treat you as on the reason ending during ToK, but you will still fight Lucifer and get TDE at the end.

**Logic Settings**
* Vanilla Menorahs - Will give you each menorah when you clear its vanilla fiend check. If this isn't set, 3 key items that unlock Kalpas 2, 3, and 4-5 will be shuffled into the pool. Matador's check will always unlock the first Kalpa.
* No Progression in Labyrinth of Amala - You will not need to go to Labyrinth of Amala to complete the seed. The bosses there may still drop rewards, but none of them will be necessary.
* Open Yurakucho Tunnel - If this is not checked, clearing Mifunashiro will open Yurakucho.

**Difficulty Settings**
* No harder bosses early - Difficult bosses may still spawn in early locations, but the logic will not expect you to clear them until later. S tier boss list: Samael, Noah, Bishamon 2, Pale Rider, Beelzebub, Metatron, Mother Harlot. A tier boss list: Trumpeter, Kagutsuchi, Ahriman, Baal Avatar, Koumouku, Red Rider, White Rider, Dante 2, Mot, Mada, Thor 2, Mara, Black Frost, Skadi, Girimehkala
* Bosses go first more often - Checks where the boss can attack you on turn 0 (Matador, Surt, etc) will let the boss go first with a few exceptions.
* No Level Safety - The logic normally doesn't expect you to do something like clear Labyrinth of Amala or fight the riders before reaching Asakusa. This removes all of those safety measures
* No Magatama Safety - Most late-game bosses will guarantee a specific magatama resistance in logic. With this setting, that no longer happens.

Check out the [Beginner Tips and FAQ](Tips and FAQ.md) if you'd like