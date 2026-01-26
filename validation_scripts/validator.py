#Validates all the .menu files in the recipe folder to meet UCoMP rules.
#
# Rule 1) Cookbook files can have subscripts.
# Rule 2) Subscripts should exist
# Rule 3) coronal measurement should have flats and darks with the same camera modes and tunings
# Rule 4) Only valid commands (See list) should be in the recipe files
# Rule 5) prefilterrange should be in prefilter list (see below)
# Rule 6) Exposure should be between 0 and 86ms
# Rule 7) Data Commands should be formatted DATA [TCAM|RCAM], [BLUE|RED|BOTH], WAVELENGTH, NUMSUM[1-16] 
# Rule 8) cover, occ, shut,calib,distortiongrid,nd should have values [IN|OUT]
# Rule 9) Gain should have values [HIGH|LOW]
#
# DARKS are any beam configuration with a dark shutter in the beam
# FLATS are beam configurations with only the Diffuser in the beam (script currently only tracks cover,diffuser,occ,calib,shut not the other optics)
# Violations of the rules will be recorded in recipes\warnings.txt
#

import os
import numpy as np
from mlso_utils import *
from pathlib import Path
os.chdir("Recipes")
import glob

import glob
import numpy as np
import matplotlib.pylab as plt

def get_kitt_peak_atlas():
    atlas = np.zeros([0,3])
    print(glob.glob("../resource/lm*"))
    for atlas_name in glob.glob("../resource/lm*"):
        print(atlas_name)
        atlas1 = np.loadtxt(atlas_name)
        atlas = np.concatenate((atlas,atlas1),axis=0)
    return atlas

atlas = get_kitt_peak_atlas()

tuning_configs = {}
seen_tunings={}

for tuning_config in glob.glob("../resource/*ini"):
    key = Path(tuning_config).name.split("_")[-1].split(".")[0]
    tuning_configs[key] =  getFilterConfig(tuning_config)
    if len(glob.glob(f"../resource/{key}*.csv")) == 1:
        tuning_configs[key]["prefilter"] = np.loadtxt(glob.glob(f"../resource/{key}*.csv")[0],delimiter=",",skiprows =10)
        for tune_number in range(len(tuning_configs[key]["prefilter"][:,0])):
            atlas_value =    atlas[find_nearest(atlas[:,0],tuning_configs[key]["prefilter"][tune_number,0]),1]
            tuning_configs[key]["prefilter"][tune_number,1] = atlas_value*tuning_configs[key]["prefilter"][tune_number,1]
        #tuning_configs[key]["prefilter"] = np.array([tuning_configs[key]["prefilter"][:,0],tune_values])
        #print(tuning_configs[key]["prefilter"].shape)
        

def convolve_filters(wave,config,cam="onband",cont="both"):
    tuning_wave,tuning_trans = createStages(filterConfig=config,wavelength=wave,cam=cam,cont=cont)
    for i in range(len(tuning_wave)):
        tuning_trans[i] = tuning_trans[i]*config["prefilter"][find_nearest(config["prefilter"][:,0],tuning_wave[i]),1]
    return tuning_wave,tuning_trans

print(tuning_configs.keys())

def read_and_plot_rcp(recipe_path):

    with open(recipe_path,"r") as recipe:
        data = recipe.readlines()
    waves = []
    for line in data:
        line = line.split("#")[0]
        if len(line.split()) > 0 and "data" == line.split()[0].lower():
            waves.append(line.split()[3]+" "+line.split()[2])

    if len(waves) > 0 and not os.path.exists("tuningplots"+"/"+recipe_path.split("\\")[-1]+".png"):
        fig = plt.figure()
        plt.title(recipe_path.split("\\")[-1]+"\nTuning Profiles + Pre-filter and Kitt Peat Atlas")
        mvalue = np.mean(np.array([d.split()[0] for d in waves],dtype=np.float32))
        wave_keys = np.array(list(tuning_configs.keys()),dtype=np.uint16)
        tuning_key  = list(tuning_configs.keys())[find_nearest(wave_keys,mvalue)]
        if "prefilter" in tuning_configs[tuning_key]:
            for key in list(set(sorted(waves))):
                
                if key+"onband" not in  seen_tunings:
                    seen_tunings[key+"onband" ] = convolve_filters(np.float32(key.split()[0]),config=tuning_configs[tuning_key],cam="onband",cont=(key.split()[1]).lower())
                if key+"offband" not in  seen_tunings:  
                    seen_tunings[key+"offband" ] = convolve_filters(np.float32(key.split()[0]),config=tuning_configs[tuning_key],cam="offband",cont=(key.split()[1]).lower())
                
                plt.plot(*seen_tunings[key+"onband"  ],label=f"{np.float32(key.split()[0]):.2f} {key.split()[1]} onband")
                plt.plot(*seen_tunings[key+"offband" ],label=f"{np.float32(key.split()[0]):.2f} {key.split()[1]} offband")
                plt.plot(tuning_configs[tuning_key]["prefilter"][:,0],tuning_configs[tuning_key]["prefilter"][:,1])

            legend = fig.legend(loc='center left', bbox_to_anchor=(1, 0.5))
            plt.ylabel("Filter throughput [%]")
            plt.xlabel("wavelength [nm]")
            fig.savefig("tuningplots"+"/"+recipe_path.split("\\")[-1]+".png", bbox_extra_artists=(legend,), bbox_inches='tight')
        plt.close(fig)

valid_commands = ["data", "cal", "dark", "fw", "occ", 
                  "diffuser","calib", "occyrel","saveall",
                  "occxrel", "o1", "calret", "calpol","cover",  
                  "shut", "exposure", "nd", "gain", "distortiongrid", 
                  "modwait","shut","exposure", "cover", "occ", "prefilterrange"]

in_out_options = ["in","out"]

ignore_commands = ["date","author","description"]
prefilters = ["637","670","706","761","789","802","991","1074","1079","530","656","1083"]


icons = {"data":"&#x1F4D7; ",
         "flat":"&#x1F4D8; ",
         "dark":"&#x1F4D9; ",
         "calib":"&#x1F4D5; ",}
tab_space = '\t'

cover_time = 60
occ_time = 20
prefilter_time = 25
rotate_time = 5
calib_time = 20
diffuser_time = 20
relaxation_time =300
camera_readout = {"high":13.7,"low":7.6}


def unroll_forloop(results):
    results = [r.split("#")[0].lower().split() for r in results]  #Remove comments cookbook/recipe file
    results2 = []
    endline =0
    for i in range(len(results)):
        if len(results[i])  > 0:
            if "for" == (results[i])[0]:
                forCount = int(results[i][1])
                startLine = i+1
                for repeats in range(forCount):
                    for nextLine in range(len(results)-i):
                        if len(results[startLine+nextLine])> 0:  
                            if "endfor" == (results[startLine+nextLine])[0]:
                                endline = startLine+nextLine+1
                                break
                            else:
                                results2.append(tab_space.join(results[startLine+nextLine]))
                                
            else:
                if i < endline:
                    pass
                else:
                    results2.append(tab_space.join(results[i]))
    return results2




def  read_script(script_name_in,parent,tab,state,darks,flat,coronal,coronalExp,summary,md,warning,child_extension=".rcp"):
    if child_extension != ".rcp":
        coronal = []
        coronalExp = []
    script_name = [file for file in glob.glob("*") if file.lower() ==script_name_in.lower()]
    if len(script_name) == 0:
      warning.write(f"read_script: {parent}, **{script_name_in}** command not found.\n")
      return 0,0
    script_name = script_name[0]
      
    script = open(script_name,"r")
    results = script.readlines()
    script.close()
    if  ".cbk" in script_name:  #Remove this test when LabView can handle for loops in rcp files.
        results2 = unroll_forloop(results)
    else:
        results2 = results
    summary.write(f" {tab*6*'-'} > {script_name.split('#')[0]}\n")
    runTime = 0
    hardwareTime = 0

    data_recipes = []
    flat_recipes = []
    dark_recipes = []
    calib_recipes = []
            
    ## Attempt to guess what icon to put next to a recipe name based on state coming in to that.
    ## this is kind of fragile but mostly works because most of our operational scripts dont change
    ## data types within a recipe but rely on setup?????.rcp to run before to configure things.
    ## We dont have a prefect filter for valid data script, (maybe we could key on wave and beam)
    ## so instead we try to ignore recipe that look like a setup script.
    emoji = None
    if "_FW" not in script_name and "_POL" not in script_name and "setup" not in script_name and "cbk" not in script_name and "menu" not in script_name and "_in" not in script_name and "_out" not in script_name:
        if state['shut'] == "in":
            emoji = icons["dark"]
        if state['shut'] == "out" and state['calib'] =='out' and state['diffuser'] == "in":
            emoji = icons["flat"]
        if state['shut'] == "out" and state['calib'] =='out' and state['diffuser'] == "out":
            
            emoji = icons["data"]
        if state['shut'] == "out" and state['calib'] =='in' and state['diffuser'] == "in":
            emoji = icons["calib"]


    md.write(f"<details><summary>")
    if emoji is not None: 
        md.write(emoji)
        md.write(f"[{script_name}](tuningplots/{script_name}.png)</summary><blockquote><pre>")
        #try:
        read_and_plot_rcp(script_name)
        #except:
        #    pass
        
    else:
        md.write(f"{script_name}</summary><blockquote><pre>")
    tab = tab +1
    for child in results2:
        filename =child.split('#')[0].strip()
        commands = child.split('#')[0].strip().lower().split()
        child=child.strip().lower()
        emoji = None
        if len(commands) > 0 and commands[0].split(":")[0] not in ignore_commands:
            if child_extension in commands[0]:
                try:
                    (tTime,hTime,data_recipes_rtn,flat_recipes_rtn,dark_recipes_rtn,calib_recipes_rtn) = read_script(filename,   parent+","+commands[0],tab,state,darks,flats,coronal,coronalExp,summary,md,warning)
                    runTime += tTime
                    hardwareTime += hTime
                    data_recipes.extend(data_recipes_rtn)
                    flat_recipes.extend(flat_recipes_rtn)
                    dark_recipes.extend(dark_recipes_rtn)
                    calib_recipes.extend(calib_recipes_rtn)
                    
                except FileNotFoundError:
                    warning.write(f"{parent} tried to call *{filename}* which does not exist\n")
            else:

                if commands[0] not in valid_commands:
                    warning.write(f"{parent} {{ {tab_space.join(commands)} }} command not found.\n")
                    continue
                if "gain"  == commands[0]:
                    if  commands[1] in ["low","high"]:
                        state['gain'] = "low" if "low" == commands[1] else "high"
                    else:
                        warning.write(f"{parent} {{ {tab_space.join(commands)} }} has invalid gain\n")
                        
                if "shut"  == commands[0]:
                    if  commands[1] in in_out_options:
                        state['shut'] = "in" if "in" == commands[1] else "out"
                    else:
                        warning.write(f"{parent} {{ {tab_space.join(commands)} }} has invalid position\n")
                    
                if "exposure" ==commands[0]:
                    try:
                        exp = float(commands[1])
                        if exp < 1 or exp > 84:
                            raise ValueError("Number out of range")
                        state['exposure'] = commands[1]
                    except:
                        warning.write(f"{parent} {{ {tab_space.join(commands)} }} has invalid exposure time\n")
                if "cover" == commands[0]:
                    if  commands[1] in in_out_options:
                        if 'cover' not in state or state['cover'] != commands[1]:
                            hardwareTime = hardwareTime + cover_time
                        state['cover'] = "in" if "in" == commands[1] else "out"
                    else:
                        warning.write(f"{parent} {{ {tab_space.join(commands)} }} has invalid position\n")
                if "occ" == commands[0]:
                    if  commands[1] in in_out_options:
                        if 'occ' not in state or state['occ'] == commands[1]:
                            hardwareTime = hardwareTime + occ_time 
                        state['occ'] = "in" if "in" == commands[1] else "out"
                    else:
                        warning.write(f"{parent} {{ {tab_space.join(commands)} }} has invalid position\n")
                if "prefilterrange" == commands[0]:
                    if commands[1] in prefilters:
                        if 'filter' not in state or state['filter'] != commands[1]:
                            hardwareTime = hardwareTime + prefilter_time 
                        state['filter'] = int(commands[1])
                    else:
                        warning.write(f"{parent} {{ {tab_space.join(commands)} }} invalid prefilter\n")
                if "calret" ==commands[0]:
                    try:
                        float(commands[1])
                        if 'calret' not in state or state['calret'] != commands[1]:
                            hardwareTime = hardwareTime + 5
                        state['calret'] = commands[1]
                    except:
                        warning.write(f"{parent} {{ {tab_space.join(commands)} }} should be degrees\n")
        
                if "calpol" == commands[0]:
                    try:
                        float(commands[1]) 
                        if 'calpol' not in state or state['calpol'] != commands[1]:
                            hardwareTime = hardwareTime + rotate_time
                        state['calpol'] = commands[1]    
                    except:
                        warning.write(f"{parent} {{ {tab_space.join(commands)} }} should be degrees\n")
                if "calib" == commands[0]:
                    if 'calib' not in state or state['calib'] == commands[1]:
                        hardwareTime = hardwareTime + calib_time
                    state['calib'] = "in" if "in" == commands[1] else "out"

                if "diffuser" == commands[0]:
                    if  commands[1] in ["in","out"]:
                        if 'diffuser' not in state or state['diffuser'] == commands[1]:
                            hardwareTime = hardwareTime + diffuser_time
                        state['diffuser'] = "in" if "in" == commands[1] else "out"
                    else:
                        warning.write(f"{parent} {{ {tab_space.join(commands)} }} has invalid position\n")
                if "data" == commands[0]:
                    if len(commands) ==4:
                        print(commands,child,parent)
                    data,cam,cont,wave,sums = commands
                    
                    if cam not in ["rcam","tcam"]:
                            warning.write(f"{parent} {{ {tab_space.join(commands)} }} has invalid camera\n")
                            continue
                    if cont not in ["both", "red", "blue"]:
                            warning.write(f"{parent} {{ {tab_space.join(commands)} }} has invalid continuum\n")
                            continue
                    try:
                            float(wave)   # Type-casting the string to `float`.
                    except ValueError:
                            warning.write(f"{parent} {{ {tab_space.join(commands)} }} wavelength is not a number\n")
                            continue
                    
                    if state['shut'] == "in":
                        emoji = icons["dark"]
                        dark_recipes.append(script_name)
                        if state['exposure']+state['gain']+sums not in darks:
                            darks.append(state['exposure']+state['gain']+sums)
                    if state['shut'] == "out" and state['calib'] =='out' and state['diffuser'] == "in":
                        emoji = icons["flat"]
                        flat_recipes.append(script_name)
                        if state['gain']+sums+cam+cont+wave not in flats:
                            flats.append(state['gain']+sums+cam+cont+wave)
                    if state['shut'] == "out" and state['calib'] =='out' and state['diffuser'] == "out":
                        emoji = icons["data"]
                        data_recipes.append(script_name)
                        coronal.append(state['gain']+sums+cam+cont+wave)
                        coronalExp.append(state['exposure']+state['gain']+sums)
                    
                    if state['shut'] == "out" and state['calib'] =='in' and state['diffuser'] == "in":
                        emoji = icons["calib"]
                        calib_recipes.append(script_name)
                    runTime += relaxation_time +(int(state['exposure'])+camera_readout[state["gain"]])*4*int(sums)
                summary.write(f"{tab*6*'-'}> {tab_space.join(commands)}\n")
                if "_FW" not in commands[0] and "setup" not in commands[0] and "cbk" not in commands[0] and "menu" not in commands[0]:
                    if emoji is not None: 
                        md.write(emoji) 
                
                md.write(tab_space.join(commands)) 
                md.write("\n &#xE0020;")

                pass
    script.close()
    if "rcp" in child_extension: 
        md.write(f"\nIntegration:{runTime/1000/60:.2f} minutes.  Hardware:{hardwareTime/60:.2f} minutes. total:{runTime/1000/60 + hardwareTime/60:.2f} minutes \n ")
        md.write(f"Darks: {", ".join(sorted(list(set(dark_recipes))))}  \n")
        md.write(f"Flats: {", ".join(sorted(list(set(flat_recipes))))} \n ")
        md.write(f"Data: {", ".join(sorted(list(set(data_recipes))))}  \n")
        md.write(f"Calibs: {", ".join(sorted(list(set(calib_recipes))))}  \n")
    else:
        for corona in coronalExp:
            if corona not in darks:
                warning.write(f"{parent} missing dark for {{ {corona} }}\n")
        for corona in coronal:
            if corona not in flats:
                warning.write(f"{parent} missing flat for {{ {corona} }}\n")
        
    md.write("</pre></blockquote></details>")
    return runTime,hardwareTime,data_recipes,flat_recipes,dark_recipes,calib_recipes
menus = glob.glob("*.menu")
state = {}
darks = []
coronal = []
coronalExp = []
flats = []
warning = open('warnings.txt',"w")
for menu in menus:
    with open(menu,"r") as menu_data:
        if "NOWARNING" in "".join(menu_data.readlines()):  # Comment string to force this script to ignore a menu file
            continue
    state = {'exposure':"80",'shut':"",'calib':"",'occ':"",'diffuser':"",'gain':"high"}
    darks = []
    flats = []
    coronal = []
    coronalExp = []
    menu_name = menu.split(".menu")[0]
    md = open(menu_name+".md","w")
    summary = open(menu_name+".summary","w")
    md.write("  \n".join([f'{icons[key]} = {key}' for key in icons.keys()]))
    read_script(menu,menu,0,state,darks,flats,coronal,coronalExp,summary,md,warning,".cbk")
    md.close()
    summary.close()
warning.close()
