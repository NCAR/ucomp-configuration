import os
os.chdir("Recipes")
import glob
def unroll_forloop(results):
    results2 = []
    endline =0
    for i in range(len(results)):
        if "FOR " in results[i]:
            forCount = int(results[i].split()[1])
            startLine = i+1
            for repeats in range(forCount):
                for nextLine in range(len(results)-i):
                    if "ENDFOR" in results[startLine+nextLine]:
                        endline = startLine+nextLine
                        break
                    else:
                        results2.append(results[startLine+nextLine])
        else:
            if i < endline:
                pass
            else:
                results2.append(results[i])
    return results2
def read_script(scriptname,parent,tab,state,darks,flat,summary,md,warning,childextension=".rcp"):
    #print(f"{scriptname},{parent},{tab},{state},{darks},{flat},{summary},{md},{warning}")
    script = open(scriptname,"r")
    results = script.readlines()
    script.close()
    results2 = unroll_forloop(results)
    #print(results2)
    summary.write(f" {tab*6*'-'} > {scriptname.split('#')[0]}\n")
    md.write(f"<details><summary>{scriptname}</summary><blockquote><pre>")
    tab = tab +1
    for child in results2:
        filename =child.split('#')[0].strip()
        child=child.strip().lower()
        if len(child.strip()) > 0 and child.strip()[0] != "#" and not child.startswith("date") and not child.startswith("author") and not child.startswith("description"):
            if childextension in child.split('#')[0]:
                try:
                    read_script(filename,parent+","+child.split('#')[0],tab,state,darks,flats,summary,md,warning)
                except FileNotFoundError:
                    warning.write(f"{parent} tried to call *{filename}* which does not exist\n")
            else:
                #print(f"{state} {darks} {flat} {parent} {child}")
                
                summary.write(f"{tab*6*'-'}> {child.split('#')[0]}\n")
                md.write(f"{child.split('#')[0]}\n")
                if "gain" in child:
                    state['gain'] = "low" if "low" in child else "high"
                if "shut" in child:
                    state['shut'] = "in" if "in" in child else "out"
                if "exposure" in child:
                    state['exposure'] = child.split(" ")[1]
                    #print(state)
                if "cover" in child:
                    state['cover'] = "in" if "in" in child else "out"
                if "occ" in child:
                    state['occ'] = "in" if "in" in child else "out"
                if "calib" in child:
                    state['calib'] = "in" if "in" in child else "out"
                if "diffuser" in child:
                    state['diffuser'] = "in" if "in" in child else "out"
                if "data" in child:
                    #print(child)
                    data,cam,cont,wave,sums = child.split()
                    if state['shut'] == "in":
                        if state['exposure']+state['gain']+sums not in darks:
                            darks.append(state['exposure']+state['gain']+sums)
                    if state['shut'] == "out" and state['calib'] =='out' and state['diffuser'] == "in":
                        if state['gain']+sums+cam+cont+wave not in flats:
                            flats.append(state['gain']+sums+cam+cont+wave)
                    if state['shut'] == "out" and state['calib'] =='out' and state['diffuser'] == "out":
                        #print(state)
                        if state['exposure']+state['gain']+sums not in darks:
                            warning.write(f"{parent} {child} missing dark for {state['exposure']+state['gain']+sums}\n")
                        if state['gain']+sums+cam+cont+wave not in flats:
                            warning.write(f"{parent} {child} missing flat for {state['gain']+sums+cam+cont+wave}\n")
                pass
    script.close()
    md.write("</pre></blockquote></details>")
menus = glob.glob("*.menu")
state = {}
darks = []
flats = []
warning = open('warnings.txt',"w")
for menu in menus:
    state = {'exposure':"80",'shut':"",'calib':"",'occ':"",'diffuser':"",'gain':"high"}
    darks = []
    flats = []
    md = open(menu.split(".menu")[0]+".md","w")
    summary = open(menu.split(".menu")[0]+".summary","w")
    quick_menu = open(menu,"r")
    qmenu = quick_menu.readlines()
    quick_menu.close()
    #print(qmenu)
    if "NOWARNING" not in "".join(qmenu):
        print(f"{menu} No warning")
        read_script(menu,menu,0,state,darks,flats,summary,md,warning,".cbk")
    md.close()
    summary.close()
warning.close()