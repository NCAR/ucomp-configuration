import glob
import configparser
import subprocess
import matplotlib.pylab as plt
from datetime import datetime



dates = []
o1 = []
for config in glob.glob("c:/ucomp-configuration/config/previous/instr*"):
    try:
        #print(config.split(".")[-1])
        inst_file = configparser.ConfigParser()
        inst_file.read(config)

        result = subprocess.run(['git', 'log', '-1', '--follow', '--format=%ci', '--', config],capture_output=True,text=True)
        date_str = result.stdout.strip().split('\n')[-1] 
        dt =datetime.strptime(date_str[:-6], '%Y-%m-%d %H:%M:%S')
        #break
        if "FILTER 1074" in inst_file:
            if "O1#1 Pos" in inst_file["FILTER 1074"]:
                #print(config.split(".")[-1],date_str,inst_file["FILTER 1074"]["O1#1 Pos" ])
                o1.append(inst_file["FILTER 1074"]["O1#1 Pos" ])
                dates.append(dt)
            if "O1 Pos" in inst_file["FILTER 1074"]:
                o1.append(inst_file["FILTER 1074"]["O1 Pos" ])
                dates.append(dt)
                #print(config.split(".")[-1],date_str,inst_file["FILTER 1074"]["O1 Pos" ])
    except:
        pass
plt.plot(dates,o1)