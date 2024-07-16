from multiprocessing.pool import ApplyResult
import tkinter as tk
from tkinter import NORMAL, filedialog
from configparser import ConfigParser, NoOptionError
import os
import hashlib

MD5_NTSC = "92e00a8a00c72d25e23d01694ac89193"

BEGINNER_PRESET = "Gehenna_Entity_Hanuman_Corpus_Odin_Masakados"
NORMAL_PRESET = "Muspell_Divine_Hanuman_Devil_Vishnu_Masakados"
ADVANCED_PRESET = "Anathema_Deity_Gui Xian_Reaper_Atavaka_Kailash"

def get_md5(file_path): #Do something about this code being in 2 places eventually
        # from https://stackoverflow.com/questions/1131220/get-md5-hash-of-big-files-in-python
        with open(file_path, 'rb') as f:
            input_md5 = hashlib.md5()
            while True:
                chunk = f.read(2**20)
                if not chunk:
                    break
                input_md5.update(chunk)

        input_md5 = input_md5.hexdigest()
        with open(file_path + '.md5', 'w') as f:
            f.write(input_md5)

        return input_md5

def create_gui(config_settings):
    window = tk.Tk()
    window.geometry('1000x700+50+50')
    persistent_frame = tk.Frame(window, width=1000, height=170)
    persistent_frame.grid(row=0, column=0)
    persistent_frame.pack_propagate(False)
    page_1_frame = tk.Frame(window, width=1000, height=500, background="#cccccc")
    page_1_frame.grid(row=1, column=0)
    page_1_frame.pack_propagate(False)
    page_2_frame = tk.Frame(window, width=1000, height=500, background="#cccccc")
    page_2_frame.grid(row=1, column=0)
    page_2_frame.pack_propagate(False)
    pages = [page_1_frame, page_2_frame]
    button_controls_frame = tk.Frame(window, width=350, height=30)
    button_controls_frame.grid(row=2, column=0)
    button_controls_frame.pack_propagate(False)
    persistent_frame_top_left = tk.Frame(persistent_frame, width=500, height=100)
    persistent_frame_top_left.grid(row=0, column=0)
    persistent_frame_top_left.pack_propagate(False)
    persistent_frame_top_right = tk.Frame(persistent_frame, width=500, height=100)
    persistent_frame_top_right.grid(row=0, column=1)
    persistent_frame_top_right.pack_propagate(False)
    persistent_frame_left = tk.Frame(persistent_frame, width=500, height=20)
    persistent_frame_left.grid(row=1, column=0)
    persistent_frame_left.pack_propagate(False)
    persistent_frame_right = tk.Frame(persistent_frame, width=500, height=20)
    persistent_frame_right.grid(row=1, column=1)
    persistent_frame_right.pack_propagate(False)
    persistent_frame_bottom_left = tk.Frame(persistent_frame, width=500, height=50)
    persistent_frame_bottom_left.grid(row=2, column=0)
    persistent_frame_bottom_left.pack_propagate(False)
    persistent_frame_bottom_right = tk.Frame(persistent_frame, width=500, height=50)
    persistent_frame_bottom_right.grid(row=2, column=1)
    persistent_frame_bottom_right.pack_propagate(False)
    page_1_frame_top = tk.Frame(page_1_frame, width=1000, height=250, background="#cccccc")
    page_1_frame_top.grid(row=0, column=0, columnspan = 2, sticky = tk.W+tk.E)
    page_1_frame_top.pack_propagate(False)
    page_1_frame_left = tk.Frame(page_1_frame, width=500, height=250, background="#cccccc")
    page_1_frame_left.grid(row=1, column=0)
    page_1_frame_left.pack_propagate(False)
    page_1_frame_right = tk.Frame(page_1_frame, width=500, height=250, background="#cccccc")
    page_1_frame_right.grid(row=1, column=1)
    page_1_frame_right.pack_propagate(False)
    page_2_frame_left = tk.Frame(page_2_frame, width=500, height=500, background="#cccccc")
    page_2_frame_left.grid(row=0, column=0)
    page_2_frame_left.pack_propagate(False)
    page_2_frame_right = tk.Frame(page_2_frame, width=500, height=500, background="#cccccc")
    page_2_frame_right.grid(row=0, column=1)
    page_2_frame_right.pack_propagate(False)
        
    def randomizeClick():
        window.quit()
    #button.bind("<Button-1>", randomizeClick)
        
    def switchPage(page_index):
        if page_index < 0 or page_index >= len(pages):
            return
        page_buttons[current_page.get()].config(state=tk.NORMAL)
        page_buttons[page_index].config(state=tk.DISABLED)
        current_page.set(page_index)
        if page_index == 0:
            left_button.config(state=tk.DISABLED)
        else:
            left_button.config(state=tk.NORMAL)
        if page_index == len(pages) - 1:
            right_button.config(state=tk.DISABLED)
        else:
            right_button.config(state=tk.NORMAL)
        pages[page_index].tkraise()
    #page_1_button.bind("<Button-1>", lambda event, page_index=0: switchPage(page_index))
    #page_2_button.bind("<Button-1>", lambda event, page_index=1: switchPage(page_index))
        
    def previousPage():
        switchPage(current_page.get() - 1)
    #left_button.bind("<Button-1>", previousPage)
            
    def nextPage():
        switchPage(current_page.get() + 1)
    #right_button.bind("<Button-1>", nextPage)

    def import_iso_path():
        file_path = filedialog.askopenfilename(title="Select the path to your iso", filetypes=[("Iso files", "*.iso"), ("All files", "*.*")])
        if file_path:
            pathEntry.delete(0, tk.END)
            pathEntry.insert(0, file_path)
            
    def apply_pasted_settings():
        confirmation = tk.messagebox.askyesno(title="confirmation", message="Confirm overwriting settings?")
        if not confirmation:
            return
        apply_settings_string(settingsStringEntry.get())
        
    def display_settings_string():
        s = create_settings_string()
        settingsStringEntry.delete(0, tk.END)
        settingsStringEntry.insert(0, s)
        
    def apply_preset_settings():
        confirmation = tk.messagebox.askyesno(title="confirmation", message="Confirm overwriting settings?")
        if not confirmation:
            return
        if dropdownPresetText.get() == "Beginner":
            apply_settings_string(BEGINNER_PRESET)
        elif dropdownPresetText.get() == "Normal":
            apply_settings_string(NORMAL_PRESET)
        elif dropdownPresetText.get() == "Advanced":
            apply_settings_string(ADVANCED_PRESET)

    button = tk.Button(
        persistent_frame_top_left,
        text="Randomize!",
        width=25,
        height=5,
        bg="#598074",
        fg="black",
        command=randomizeClick,
    )
    button.pack()
        
        
    left_button = tk.Button(
        button_controls_frame,
        text="<-",
        width=10,
        height=3,
        bg="#598074",
        fg="black",
        state=tk.DISABLED,
        command=previousPage,
    )
    left_button.pack(side=tk.LEFT)
        
    right_button = tk.Button(
        button_controls_frame,
        text="->",
        width=10,
        height=3,
        bg="#598074",
        fg="black",
        command=nextPage,
    )
    right_button.pack(side=tk.RIGHT)
        
    page_1_button = tk.Button(
        button_controls_frame,
        text="Page 1",
        width=10,
        height=3,
        bg="#598074",
        fg="black",
        state=tk.DISABLED,
        command=lambda page_index=0: switchPage(page_index),
    )
    page_1_button.pack(side=tk.LEFT)
        
    page_2_button = tk.Button(
        button_controls_frame,
        text="Page 2",
        width=10,
        height=3,
        bg="#598074",
        fg="black",
        command=lambda page_index=1: switchPage(page_index),
    )
    page_2_button.pack(side=tk.RIGHT)
        
    page_buttons = [page_1_button, page_2_button]
       
    current_page = tk.IntVar(window, 0)

    pathLabel = tk.Label(persistent_frame_top_left, text="Please input the path to your SMT3 Nocturne ISO file below")
    pathLabel.pack()
    
    path_select_button = tk.Button(
        persistent_frame_left,
        text="Choose File",
        width=10,
        height=3,
        bg="#598074",
        fg="black",
        command=import_iso_path
    )
    path_select_button.pack(side=tk.RIGHT)
    
    pathEntry = tk.Entry(persistent_frame_left, fg="black", bg="#598074", width=50)
    pathEntry.pack(side=tk.RIGHT, padx = 18)

    seedLabel = tk.Label(persistent_frame_bottom_left, text="Please input your desired seed value below (blank for random seed)")
    seedLabel.pack()

    seedEntry = tk.Entry(persistent_frame_bottom_left, fg="black", bg="#598074", width=50)
    seedEntry.pack()
    
    settingsStringEntry = tk.Entry(persistent_frame_top_right, fg="black", bg="#598074", width=50)
    settingsStringEntry.pack(side=tk.BOTTOM)    

    settingsStringLabel = tk.Label(persistent_frame_top_right, text="You may paste in a settings string here")
    settingsStringLabel.pack(side=tk.BOTTOM)
    
    display_settings_button = tk.Button(
        persistent_frame_right,
        text="Show Settings String",
        width=15,
        height=3,
        bg="#598074",
        fg="black",
        command=display_settings_string
    )
    display_settings_button.pack(side=tk.RIGHT, padx = (0, 100))
    
    apply_settings_button = tk.Button(
        persistent_frame_right,
        text="Apply String",
        width=10,
        height=3,
        bg="#598074",
        fg="black",
        command=apply_pasted_settings
    )
    apply_settings_button.pack()
    
    dropdownPresetText = tk.StringVar()
    dropdownPresetText.set("Recommended Settings Presets")
    dropdownPresets = tk.OptionMenu(persistent_frame_bottom_right, dropdownPresetText,"Beginner", "Normal","Advanced")
    dropdownPresets.config(fg="black",bg="#598074",activebackground="#79a094")
    dropdownPresets.pack()
    
    apply_preset_button = tk.Button(
        persistent_frame_bottom_right,
        text="Use Preset",
        width=10,
        height=3,
        bg="#598074",
        fg="black",
        command=apply_preset_settings
    )
    apply_preset_button.pack()

    flagLabel = tk.Label(page_1_frame_top, text="General Settings")
    flagLabel.pack()

    listFlags = tk.Listbox(page_1_frame_top, selectmode = "multiple", width=100, exportselection=False, selectbackground = "#598074")
    listFlags.insert(0, "Tweak 'pierce' skill to work with magic.")
    listFlags.insert(1, "Remove hard mode shop price multiplier.")
    listFlags.insert(2, "Tweak AoE healing spells to affect demons in the stock.")
    listFlags.insert(3, "Tweak inheritance so that all skills inherit equally regaless of rank or body parts.")
    listFlags.insert(4, "Make learnable skills always visible.")
    listFlags.insert(5, "Double EXP gains.")
    listFlags.insert(6, "keep tower of Kagutsuchi bosses vanilla.")
    listFlags.insert(7, "balance skills of enemies based on level (doesn't affect your demons).")
    listFlags.insert(8, "Double Macca dropped by enemies.")
    listFlags.pack()

    musicLabel = tk.Label(page_1_frame_left, text="Music Setting")
    musicLabel.pack()

    listMusic = tk.Listbox(page_1_frame_left, selectmode = "single", exportselection=False, selectbackground = "#598074")
    listMusic.insert(0, "Vanilla")
    listMusic.insert(1, "Location-based")
    listMusic.insert(2, "Random")
    listMusic.selection_set(0)
    listMusic.pack()
        
    pixieLabel = tk.Label(page_1_frame_right, text="Starting Pixie")
    pixieLabel.pack()

    listPixie = tk.Listbox(page_1_frame_right, selectmode = "single", width = 80, exportselection=False, selectbackground = "#598074")
    listPixie.insert(0, "Fully randomize starting Pixie's level")
    listPixie.insert(1, "Normalize starting Pixie's level between 40 and 60 for a balanced early game")
    listPixie.insert(2, "Keep starting Pixie level 2 - not recommended for newer players")
    listPixie.selection_set(0)
    listPixie.pack()
        
    skillMutationLabel = tk.Label(page_2_frame_left, text="Better Skill Mutations")
    skillMutationLabel.pack()

    listSkillMutation = tk.Listbox(page_2_frame_left, selectmode = "single", width=50, exportselection=False, selectbackground = "#598074")
    listSkillMutation.insert(0, "Disabled")
    listSkillMutation.insert(1, "Standard")
    listSkillMutation.insert(2, "Random")
    listSkillMutation.insert(3, "Random - Unique Skills Allowed")
    listSkillMutation.selection_set(0)
    listSkillMutation.pack()
    
    reasonLabel = tk.Label(page_2_frame_left, text="Ending Selector")
    reasonLabel.pack()

    listReason = tk.Listbox(page_2_frame_left, selectmode = "single", width=50, exportselection=False, selectbackground = "#598074")
    listReason.insert(0, "Freedom")
    listReason.insert(1, "Yosuga")
    listReason.insert(2, "Shijima")
    listReason.insert(3, "Musubi")
    listReason.insert(4, "Auto TDE")
    listReason.selection_set(0)
    listReason.pack()
    
    logicLabel = tk.Label(page_2_frame_right, text="Logic Settings")
    logicLabel.pack()

    listLogic = tk.Listbox(page_2_frame_right, selectmode = "multiple", width=50, exportselection=False, selectbackground = "#598074")
    listLogic.insert(0, "Vanilla Menorahs")
    listLogic.insert(1, "No Progression in Labyrinth of Amala")
    listLogic.insert(2, "Vanilla Yahiro no Himorogi")
    listLogic.insert(3, "Open Yurakucho Tunnel")
    listLogic.insert(4, "Open Ikebukuro Tunnel")
    listLogic.pack()
    
    difficultyLabel = tk.Label(page_2_frame_right, text="Difficulty Settings")
    difficultyLabel.pack()

    listDifficulty = tk.Listbox(page_2_frame_right, selectmode = "multiple", width=50, exportselection=False, selectbackground = "#f7333d")
    listDifficulty.insert(0, "No S-Tier Bosses early")
    listDifficulty.insert(1, "No S or A-Tier Bosses early")
    listDifficulty.insert(2, "Bosses go first more often")
    listDifficulty.insert(3, "No level safety")
    listDifficulty.insert(4, "No Magatama safety")
    listDifficulty.insert(5, "Low Level")
    listDifficulty.pack()
    
    cutsceneLabel = tk.Label(page_2_frame_left, text="Boss Cutscene Setting")
    cutsceneLabel.pack()

    listCutscene = tk.Listbox(page_2_frame_left, selectmode = "single", width = 50, exportselection=False, selectbackground = "#598074")
    listCutscene.insert(0, "Watch - Models/Dialogue Randomized")
    listCutscene.insert(1, "Skip Longer Cutscenes")
    listCutscene.insert(2, "Skip All")
    listCutscene.selection_set(1)
    listCutscene.pack()

    outputLabel = tk.Label(page_2_frame_right, text="Export Format")
    outputLabel.pack()

    listOutput = tk.Listbox(page_2_frame_right, selectmode = "single", width=50, exportselection=False, selectbackground = "#598074")
    listOutput.insert(0, "ISO file *Recommended for most users*")
    listOutput.insert(1, "HostFS folder *EXPERIEMENTAL*")
    listOutput.selection_set(0)
    listOutput.pack()
        
    page_1_frame.tkraise()
    
    magatamaNames = open('./data/magatama_names.txt' , 'r').read().strip()
    magatamaNames = magatamaNames.split('\n')
    raceNames = open('./data/race_names.txt' , 'r').read().strip()
    raceNames = raceNames.split('\n')
    demonNames = open('./data/demon_names.txt' , 'r').read().strip()
    demonNames = demonNames.split("\n")
    demonNames = [i for i in demonNames if i != "?" and not "(" in i]

    def create_settings_string():
        generalSelection = [False for i in range(listFlags.size())]
        for i in listFlags.curselection():
            generalSelection[i] = True
        generalNumber1 = sum([b << i for i, b in enumerate(generalSelection[:4])]) #0-15
        generalNumber2 = sum([b << i for i, b in enumerate(generalSelection[4:])]) #0-31
        generalString1 = magatamaNames[generalNumber1]
        generalString2 = raceNames[generalNumber2]
        musicPixieMutateNumber = 16 * listMusic.curselection()[0] + 4 * listPixie.curselection()[0] + listSkillMutation.curselection()[0] #0-63
        musicPixieMutateString = demonNames[len(demonNames) - 1 - musicPixieMutateNumber]
        logicSelection = [False for i in range(listLogic.size())]
        for i in listLogic.curselection():
            logicSelection[i] = True
        logicNumber = sum([b << i for i, b in enumerate(logicSelection)]) #0-31
        logicString = raceNames[len(raceNames) - 1 - logicNumber]
        difficultySelection = [False for i in range(listDifficulty.size())]
        for i in listDifficulty.curselection():
            difficultySelection[i] = True
        difficultyNumber = sum([b << i for i, b in enumerate(difficultySelection)]) #0-63
        difficultyString = demonNames[difficultyNumber]
        reasonCutsceneNumber = 4 * listReason.curselection()[0] + listCutscene.curselection()[0] #0-18
        reasonCutsceneString = magatamaNames[len(magatamaNames) - 1 - reasonCutsceneNumber]
        return generalString1 + '_' + generalString2 + '_' + musicPixieMutateString + '_' + logicString + '_' + difficultyString + '_' + reasonCutsceneString

    def apply_settings_string(settings_string):
        current_settings = create_settings_string()
        try:
            split_string = settings_string.split("_")
            generalNumber1 = magatamaNames.index(split_string[0])
            generalNumber2 = raceNames.index(split_string[1])
            musicPixieMutateNumber = len(demonNames) - 1 - demonNames.index(split_string[2])
            logicNumber = len(raceNames) - 1 - raceNames.index(split_string[3])
            difficultyNumber = demonNames.index(split_string[4])
            reasonCutsceneNumber = len(magatamaNames) - 1 - magatamaNames.index(split_string[5])
            for i in range(listLogic.size()):
                if ((logicNumber & (1 << i)) > 0):
                    listLogic.selection_set(i)
                else:
                    listLogic.selection_clear(i)
            generalNumber = generalNumber1 + 16 * generalNumber2
            for i in range(listFlags.size()):
                if ((generalNumber & (1 << i)) > 0):
                    listFlags.selection_set(i)
                else:
                    listFlags.selection_clear(i)
            for i in range(listDifficulty.size()):
                if ((difficultyNumber & (1 << i)) > 0):
                    listDifficulty.selection_set(i)
                else:
                    listDifficulty.selection_clear(i)
            reasonNumber = reasonCutsceneNumber // 4
            for i in range(listReason.size()):
                if (i == reasonNumber):
                    listReason.selection_set(i)
                else:
                    listReason.selection_clear(i)
            musicNumber = musicPixieMutateNumber // 16
            for i in range(listMusic.size()):
                if (i == musicNumber):
                    listMusic.selection_set(i)
                else:
                    listMusic.selection_clear(i)
            pixieNumber = (musicPixieMutateNumber % 16) // 4
            for i in range(listPixie.size()):
                if (i == pixieNumber):
                    listPixie.selection_set(i)
                else:
                    listPixie.selection_clear(i)
            mutateNumber = musicPixieMutateNumber % 4
            for i in range(listSkillMutation.size()):
                if (i == mutateNumber):
                    listSkillMutation.selection_set(i)
                else:
                    listSkillMutation.selection_clear(i)
            cutsceneNumber = reasonCutsceneNumber % 4
            for i in range(listCutscene.size()):
                if (i == cutsceneNumber):
                    listCutscene.selection_set(i)
                else:
                    listCutscene.selection_clear(i)
            verify_string = create_settings_string()
            if (verify_string != settings_string):
                tk.messagebox.showwarning(title="warning", message="Warning: Loss of fidelity in settings string. Please double check your settings")
        except Exception:
            tk.messagebox.showerror(title="error", message="Error parsing settings string. Changes were not applied")
            apply_settings_string(current_settings)

    configur = ConfigParser()
    if os.path.exists('config.ini'):
        configur.read('config.ini')
        config_iso_path = configur.get('Files', 'Path').strip()
        config_flags = configur.get('Settings', 'Flags').strip()
        if os.path.exists(config_iso_path):
            pathEntry.insert(0, config_iso_path)
            #print('Config file found, previous ISO file path: {}'.format(config_iso_path))
            #response = input('Use previous ISO file? y/n\n> ').strip()
            #print()
            #if response[:1].lower() == 'y':
            #    self.input_iso_path = config_iso_path


        #config_flags = ''
        try:
            if configur.get('Settings', 'MagicPierce') == 'true':
                #config_flags = config_flags + 'p'
                listFlags.selection_set(0)
            if configur.get('Settings', 'RemoveHardmodePrices') == 'true':
                #config_flags = config_flags + 's'
                listFlags.selection_set(1)
            if configur.get('Settings', 'FixInheritance') == 'true':
                #config_flags = config_flags + 'i'
                listFlags.selection_set(3)
            if configur.get('Settings', 'StockHealing') == 'true':
                #config_flags = config_flags + 'h'
                listFlags.selection_set(2)
            if configur.get('Settings', 'VisibleSkills') == 'true':
                #config_flags = config_flags + 'v'
                listFlags.selection_set(4)
            if configur.get('Settings', 'ExpModifier') == 'true':
                #config_flags = config_flags + 'd'
                listFlags.selection_set(5)
            if configur.get('Settings', 'VanillaTok') == 'true':
                #config_flags = config_flags + 't'
                listFlags.selection_set(6)
            if configur.get('Settings', 'RandomMusic') == 'true':
                #config_flags = config_flags + 'm'
                listMusic.selection_clear(0)
                listMusic.selection_set(2)
            if configur.get('Settings', 'CheckBasedMusic') == 'true':
                listMusic.selection_clear(0)
                listMusic.selection_set(1)
            if configur.get('Settings', 'BalancePixie') == 'true':
                #config_flags = config_flags + 'm'
                listPixie.selection_clear(0)
                listPixie.selection_set(1)
            if configur.get('Settings', 'LowLevelPixie') == 'true':
                listPixie.selection_clear(0)
                listPixie.selection_set(2)
            if configur.get('Settings', 'EnemySkillScaling') == 'true':
                #config_flags = config_flags + 'e'
                listFlags.selection_set(7)
            if configur.get('Settings', 'BetterMutationsStandard') == 'true':
                listSkillMutation.selection_clear(0)
                listSkillMutation.selection_set(1)
            if configur.get('Settings', 'BetterMutationsRandom') == 'true':
                listSkillMutation.selection_clear(0)
                listSkillMutation.selection_set(2)
            if configur.get('Settings', 'BetterMutationsUnique') == 'true':
                listSkillMutation.selection_clear(0)
                listSkillMutation.selection_set(3)
            if configur.get('Settings', 'Yosuga') == 'true':
                listReason.selection_clear(0)
                listReason.selection_set(1)
            if configur.get('Settings', 'Shijima') == 'true':
                listReason.selection_clear(0)
                listReason.selection_set(2)
            if configur.get('Settings', 'Musubi') == 'true':
                listReason.selection_clear(0)
                listReason.selection_set(3)
            if configur.get('Settings', 'FightLucifer') == 'true':
                listReason.selection_clear(0)
                listReason.selection_set(4)
            if configur.get('Settings', 'MaccaModifier') == 'true':
                listFlags.selection_set(8)
            if configur.get('Settings', 'MenorahGroups') == 'false':
                listLogic.selection_set(0)
            if configur.get('Settings', 'NoLoaProgression') == 'true':
                listLogic.selection_set(1)
            if configur.get('Settings', 'VanillaPyramidion') == 'true':
                listLogic.selection_set(2)
            if configur.get('Settings', 'OpenYurakucho') == 'true':
                listLogic.selection_set(3)
            if configur.get('Settings', 'OpenIkebukuro') == 'true':
                listLogic.selection_set(4)
            if configur.get('Settings', 'LowBossSafety') == 'true':
                listDifficulty.selection_set(0)
            if configur.get('Settings', 'HighBossSafety') == 'true':
                listDifficulty.selection_set(1)
            if configur.get('Settings', 'BossesGoFirstMoreOften') == 'true':
                listDifficulty.selection_set(2)
            if configur.get('Settings', 'NoLevelSafety') == 'true':
                listDifficulty.selection_set(3)
            if configur.get('Settings', 'NoMagatamaSafety') == 'true':
                listDifficulty.selection_set(4)
            if configur.get('Settings', 'LowLevel') == 'true':
                listDifficulty.selection_set(5)
            if configur.get('Settings', 'LongestCutscenes') == 'true':
                listCutscene.selection_clear(1)
                listCutscene.selection_set(0)
            if configur.get('Settings', 'ShortestCutscenes') == 'true':
                listCutscene.selection_clear(1)
                listCutscene.selection_set(2)
            if configur.get('Files', 'ExportToHostfs') == 'true':
                listOutput.selection_clear(0)
                listOutput.selection_set(1)
        except NoOptionError:
            create_config_file(configur)


    else:
        create_config_file(configur)
        
    window.mainloop()

    input_iso_path = pathEntry.get()
    text_seed = seedEntry.get()

    mainFlags = [False for i in range(listFlags.size())]
    for i in listFlags.curselection():
        mainFlags[i] = True
        
    musicChoice = listMusic.curselection()
            
    pixieChoice = listPixie.curselection()
        
    skillMutationChoice = listSkillMutation.curselection()
        
    reasonChoice = listReason.curselection()
     
    logicFlags = [False for i in range(listLogic.size())]
    for i in listLogic.curselection():
        logicFlags[i] = True
        
    difficultyFlags = [False for i in range(listDifficulty.size())]
    for i in listDifficulty.curselection():
        difficultyFlags[i] = True
        
    cutsceneChoice = listCutscene.curselection()

    config_export_to_hostfs = False
    if (len(listOutput.curselection()) > 0 and listOutput.curselection()[0] == 1):
        config_export_to_hostfs = True
        
    settings_string = create_settings_string()
        
    window.destroy()

    #if self.input_iso_path == None:
    #    self.input_iso_path = input("Please input the path to your SMT3 Nocturne ISO file:\n> ").strip().replace('"', '').replace("'", "")
    #    print()

    if os.path.isdir(input_iso_path):
        print("Searching directory for ISO")
        for filename in os.listdir(input_iso_path):
            path = os.path.join(input_iso_path, filename)
            stats = os.stat(path)
            if stats.st_size == 4270227456:
                input_md5 = get_md5(path)
                if input_md5 == MD5_NTSC:
                    input_iso_path = path
                    break
        else:
            print("File not found, check input path")
            raise OSError
        print("Found valid ISO: {}\n".format(input_iso_path))
    else:
        if not input_iso_path.lower().endswith('.iso'):
            input_iso_path += '.iso'

    if not os.path.exists(input_iso_path):
        print("File not found, check input path")
        raise OSError

    configur.set('Files', 'Path', input_iso_path)

    #if self.text_seed == "":
    #    self.text_seed = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    #    print('Your generated seed is: {}\n'.format(self.text_seed))
    #self.full_seed = '{}-{}-{}'.format(VERSION, self.text_seed, self.flags)
    #seed = int(hashlib.sha256(self.full_seed.encode('utf-8')).hexdigest(), 16)
    #random.seed(seed)

    #configur.set('Settings', 'Flags', self.flags)

    if config_export_to_hostfs == False:
        configur.set('Files', 'ExportToHostfs', 'false')
    elif config_export_to_hostfs == True:
        config_export_to_hostfs = True
        configur.set('Files', 'ExportToHostfs', 'true')
    else:
        print("Invalid input, defaulting to ISO file export")
        config_export_to_hostfs = False
        configur.set('Files', 'ExportToHostfs', 'false')

    if mainFlags[0]:
        config_settings.magic_pierce = True
        configur.set('Settings', 'MagicPierce', 'true')
    else:
        configur.set('Settings', 'MagicPierce', 'false')

    if mainFlags[1]:
        config_settings.remove_hardmode_prices = True
        configur.set('Settings', 'RemoveHardmodePrices', 'true')
    else:
        configur.set('Settings', 'RemoveHardmodePrices', 'false')

    if mainFlags[2]:
        config_settings.stock_healing = True
        configur.set('Settings', 'StockHealing', 'true')
    else:
        configur.set('Settings', 'StockHealing', 'false')

    if mainFlags[3]:
        config_settings.fix_inheritance = True
        configur.set('Settings', 'FixInheritance', 'true')
    else:
        configur.set('Settings', 'FixInheritance', 'false')

    if mainFlags[4]:
        config_settings.visible_skills = True
        configur.set('Settings', 'VisibleSkills', 'true')
    else:
        configur.set('Settings', 'VisibleSkills', 'false')

    if mainFlags[5]:
        config_settings.exp_modifier = 2
        configur.set('Settings', 'ExpModifier', 'true')
    else:
        configur.set('Settings', 'ExpModifier', 'false')

    if mainFlags[6]:
        config_settings.vanilla_tok = True
        configur.set('Settings', 'VanillaTok', 'true')
    else:
        configur.set('Settings', 'VanillaTok', 'false')

    if mainFlags[7]:
        config_settings.enemy_skill_scaling = True
        configur.set('Settings', 'EnemySkillScaling', 'true')
    else:
        configur.set('Settings', 'EnemySkillScaling', 'false')
        
    if mainFlags[8]:
        config_settings.macca_modifier = 2
        configur.set('Settings', 'MaccaModifier', 'true')
    else:
        configur.set('Settings', 'MaccaModifier', 'false')
            
    if len(musicChoice) > 0 and musicChoice[0] == 2:
        config_settings.random_music = True
        configur.set('Settings', 'RandomMusic', 'true')
    else:
        configur.set('Settings', 'RandomMusic', 'false')

    if len(musicChoice) > 0 and musicChoice[0] == 1:
        config_settings.check_based_music = True
        configur.set('Settings', 'CheckBasedMusic', 'true')
    else:
        configur.set('Settings', 'CheckBasedMusic', 'false')
            
    if len(pixieChoice) > 0 and pixieChoice[0] == 1:
        config_settings.balance_pixie = True
        configur.set('Settings', 'BalancePixie', 'true')
    else:
        configur.set('Settings', 'BalancePixie', 'false')

    if len(pixieChoice) > 0 and pixieChoice[0] == 2:
        config_settings.low_level_pixie = True
        configur.set('Settings', 'LowLevelPixie', 'true')
    else:
        configur.set('Settings', 'LowLevelPixie', 'false')
            
    if len(skillMutationChoice) > 0 and skillMutationChoice[0] == 1:
        config_settings.better_mutations = True
        configur.set('Settings', 'BetterMutationsStandard', 'true')
    else:
        configur.set('Settings', 'BetterMutationsStandard', 'false')
            
    if len(skillMutationChoice) > 0 and skillMutationChoice[0] == 2:
        config_settings.better_mutations = True
        config_settings.random_mutations = True
        configur.set('Settings', 'BetterMutationsRandom', 'true')
    else:
        configur.set('Settings', 'BetterMutationsRandom', 'false')
            
    if len(skillMutationChoice) > 0 and skillMutationChoice[0] == 3:
        config_settings.better_mutations = True
        config_settings.random_mutations = True
        config_settings.unique_mutations = True
        configur.set('Settings', 'BetterMutationsUnique', 'true')
    else:
        configur.set('Settings', 'BetterMutationsUnique', 'false')
        
    if len(reasonChoice) > 0 and reasonChoice[0] == 1:
        config_settings.yosuga = True
        configur.set('Settings', 'Yosuga', 'true')
    else:
        configur.set('Settings', 'Yosuga', 'false')
        
    if len(reasonChoice) > 0 and reasonChoice[0] == 2:
        config_settings.shijima = True
        configur.set('Settings', 'Shijima', 'true')
    else:
        configur.set('Settings', 'Shijima', 'false')
        
    if len(reasonChoice) > 0 and reasonChoice[0] == 3:
        config_settings.musubi = True
        configur.set('Settings', 'Musubi', 'true')
    else:
        configur.set('Settings', 'Musubi', 'false')
        
    if len(reasonChoice) > 0 and reasonChoice[0] == 4:
        config_settings.fight_lucifer = True
        configur.set('Settings', 'FightLucifer', 'true')
    else:
        configur.set('Settings', 'FightLucifer', 'false')
        
    if logicFlags[0]:
        configur.set('Settings', 'MenorahGroups', 'false')
    else:
        config_settings.menorah_groups = True
        configur.set('Settings', 'MenorahGroups', 'true')
        
    if logicFlags[1]:
        config_settings.no_loa_progression = True
        configur.set('Settings', 'NoLoaProgression', 'true')
    else:
        configur.set('Settings', 'NoLoaProgression', 'false')
        
    if logicFlags[2]:
        config_settings.vanilla_pyramidion = True
        configur.set('Settings', 'VanillaPyramidion', 'true')
    else:
        configur.set('Settings', 'VanillaPyramidion', 'false')
        
    if logicFlags[3]:
        config_settings.open_yurakucho = True
        configur.set('Settings', 'OpenYurakucho', 'true')
    else:
        configur.set('Settings', 'OpenYurakucho', 'false')
        
    if logicFlags[4]:
        config_settings.open_ikebukuro = True
        configur.set('Settings', 'OpenIkebukuro', 'true')
    else:
        configur.set('Settings', 'OpenIkebukuro', 'false')
        
    if difficultyFlags[0]:
        config_settings.low_boss_safety = True
        configur.set('Settings', 'LowBossSafety', 'true')
    else:
        configur.set('Settings', 'LowBossSafety', 'false')
        
    if difficultyFlags[1]:
        config_settings.high_boss_safety = True
        configur.set('Settings', 'HighBossSafety', 'true')
    else:
        configur.set('Settings', 'HighBossSafety', 'false')
        
    if difficultyFlags[2]:
        config_settings.bosses_go_first_more_often = True
        configur.set('Settings', 'BossesGoFirstMoreOften', 'true')
    else:
        configur.set('Settings', 'BossesGoFirstMoreOften', 'false')
        
    if difficultyFlags[3]:
        config_settings.no_level_safety = True
        configur.set('Settings', 'NoLevelSafety', 'true')
    else:
        configur.set('Settings', 'NoLevelSafety', 'false')
        
    if difficultyFlags[4]:
        config_settings.no_magatama_safety = True
        configur.set('Settings', 'NoMagatamaSafety', 'true')
    else:
        configur.set('Settings', 'NoMagatamaSafety', 'false')
        
    if difficultyFlags[5]:
        config_settings.low_level = True
        configur.set('Settings', 'LowLevel', 'true')
    else:
        configur.set('Settings', 'LowLevel', 'false')
        
    if len(cutsceneChoice) > 0 and cutsceneChoice[0] == 2:
        config_settings.shortest_cutscenes = True
        configur.set('Settings', 'ShortestCutscenes', 'true')
    else:
        configur.set('Settings', 'ShortestCutscenes', 'false')

    if len(cutsceneChoice) > 0 and cutsceneChoice[0] == 0:
        config_settings.longest_cutscenes = True
        configur.set('Settings', 'LongestCutscenes', 'true')
    else:
        configur.set('Settings', 'LongestCutscenes', 'false')

    with open('config.ini', 'w') as configfile:
        configur.write(configfile)    

    return (config_settings, input_iso_path, text_seed, settings_string, config_export_to_hostfs)

def create_config_file(configur):
    configur.read('config.ini')
    configur['Files'] = {'path': 'Nocturne.iso', 'exporttohostfs': False}
    configur['Settings'] = {'flags': '', 'ExpModifier': False, 'MaccaModifier': False, 'VisibleSkills': False, 'MagicPierce': False,
                                'StockHealing': False, 'RemoveHardmodePrices': False, 'FixInheritance': False, 'VanillaTok': False,
                                'RandomMusic': False, 'CheckBasedMusic': False, 'BalancePixie': False, 'LowLevelPixie': False,
                                'EnemySkillScaling': False, 'FightLucifer': False, 'MenorahGroups': False, 'BetterMutationsStandard': False,
                                'BetterMutationsRandom': False, 'BetterMutationsUnique': False, 'Yosuga': False, 'Shijima': False, 'Musubi': False,
                                'NoLoaProgression': False, 'VanillaPyramidion': False, 'OpenYurakucho': False, 'OpenIkebukuro': False,
                                'LowBossSafety': False, 'HighBossSafety': False, 'BossesGoFirstMoreOften': False, 'NoLevelSafety': False, 'NoMagatamaSafety': False,
                                'ShortestCutscenes': False, 'LongestCutscenes': False, 'LowLevel': False}
    
