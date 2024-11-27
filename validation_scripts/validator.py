#Validates all the .menu files in the recipe folder for to meet UCoMP rules.
#
# Rule 1) Cookbook files can have 
# Rule 2) Sub-scripts should exist
# Rule 3) coronal measurement should have flats and darks with the same camera modes and tunings
# Rule 4) Only valid_commands (See list) should be in the recipe files
# Rule 5) prefilterrange should be in prefilter list (see below)
# Rule 6) Exposure should be between 0 and 86ms
# Rule 7) Data Commands should be formatted DATA [TCAM|RCAM], [BLUE|RED|BOTH], WAVELENGTH, NUMSUM[1-16] 
# Rule 8) cover, occ, shut,calib,distortiongrid,nd should have values [IN|OUT]
# Rule 9) gain should have values [HIGH|LOW]
#
# DARKS are any beam confugraiton with dark shutter the beam
# FLATS are beam configuration with only the Diffuser in the beam (script currently only tracks, cover,diffuser,occ,calib,shut not the other optics)
# Violations of the rules will be recorded in recipes\warnings.txt
#

import os
os.chdir("Recipes")
import glob

valid_commands = ["data", "cal", "dark", "fw", "occ", 
                  "diffuser","calib", "occyrel", 
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
    results = [r.split("#")[0].lower().split() for r in results]  #Remove comments
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
    if  ".cbk" in script_name:  #Remove this test when Labview can handle for loops in rcp files.
        results2 = unroll_forloop(results)
    else:
        results2 = results
    summary.write(f" {tab*6*'-'} > {script_name.split('#')[0]}\n")
    runTime = 0
    hardwareTime = 0
            
 
    emoji = None
    if "_FW" not in script_name and "setup" not in script_name and "cbk" not in script_name and "menu" not in script_name and "_in" not in script_name and "_out" not in script_name:
        if state['shut'] == "in":
            emoji = icons["dark"]
        if state['shut'] == "out" and state['calib'] =='out' and state['diffuser'] == "in":
            emoji = icons["flat"]
        if state['shut'] == "out" and state['calib'] =='out' and state['diffuser'] == "out":
            
            emoji = icons["data"]
        if state['shut'] == "out" and state['calib'] =='in' and state['diffuser'] == "in":
            emoji = icons["calib"]
    else:
        emoji = None

    md.write(f"<details><summary>")
    if emoji is not None: 
        md.write(emoji)
    md.write(f"{script_name}</summary><blockquote><pre>")
    tab = tab +1
    for child in results2:
        filename =child.split('#')[0].strip()
        commands = child.split('#')[0].strip().lower().split()
        child=child.strip().lower()
        emoji = None
        if len(commands) > 0 and commands[0] not in ignore_commands:
            if child_extension in commands[0]:
                try:
                    (tTime,hTime) = read_script(filename,   parent+","+commands[0],tab,state,darks,flats,coronal,coronalExp,summary,md,warning)
                    runTime += tTime
                    hardwareTime += hTime
                    
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
                    data,cam,cont,wave,sums = commands
                    
                    if cam not in ["rcam","tcam"]:
                            warning.write(f"{parent} {{ {tab_space.join(commands)} }} has invalid camera\n")
                            continue
                    if cont not in ["both", "red,", "blue"]:
                            warning.write(f"{parent} {{ {tab_space.join(commands)} }} has invalid continuum\n")
                            continue
                    try:
                            float(wave)   # Type-casting the string to `float`.
                    except ValueError:
                            warning.write(f"{parent} {{ {tab_space.join(commands)} }} wavelength is not a number\n")
                            continue
                    
                    if state['shut'] == "in":
                        emoji = icons["dark"]
                        if state['exposure']+state['gain']+sums not in darks:
                            darks.append(state['exposure']+state['gain']+sums)
                    if state['shut'] == "out" and state['calib'] =='out' and state['diffuser'] == "in":
                        emoji = icons["flat"]
                        if state['gain']+sums+cam+cont+wave not in flats:
                            flats.append(state['gain']+sums+cam+cont+wave)
                    if state['shut'] == "out" and state['calib'] =='out' and state['diffuser'] == "out":
                        emoji = icons["data"]
                        coronal.append(state['gain']+sums+cam+cont+wave)
                        coronalExp.append(state['exposure']+state['gain']+sums)
                    
                    if state['shut'] == "out" and state['calib'] =='in' and state['diffuser'] == "in":
                        emoji = icons["calib"]
                    runTime += relaxation_time +(int(state['exposure'])+camera_readout[state["gain"]])*4*int(sums)
                summary.write(f"{tab*6*'-'}> {tab_space.join(commands)}\n")
                if "_FW" not in commands[0] and "setup" not in commands[0] and "cbk" not in commands[0] and "menu" not in commands[0]:
                    if emoji is not None: 
                        md.write(emoji) 
                
                md.write(tab_space.join(commands)) 
                md.write("\n")

                pass
    script.close()
    if "rcp" in child_extension: 
        md.write(f"\nIntegration:{runTime/1000/60:.2f} minutes.  Hardware:{hardwareTime/60:.2f} minutes. total:{runTime/1000/60 + hardwareTime/60:.2f} minutes  ")
    else:
        for corona in coronalExp:
            if corona not in darks:
                warning.write(f"{parent} missing dark for {{ {corona} }}\n")
        for corona in coronal:
            if corona not in flats:
                warning.write(f"{parent} missing flat for {{ {corona} }}\n")
        
    md.write("</pre></blockquote></details>")
    return runTime,hardwareTime
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
