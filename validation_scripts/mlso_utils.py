
'''
To use this lyot filter code locally, you will need to download the tuning_calibration ini  files from
https://github.com/NCAR/ucomp-configuration/tree/main/config

And edit the gitPath to match the path on your local system.  For me I cloned the git repository into 
c:\\git\\ucomp-configuration but the values should be changd to match your system.

'''
gitDirectory = Path(".")
from pathlib import Path
import numpy as np


def gaussian(x, amplitude=1.0, center=1074.7, sigma=1.0, expon=2.0):
    ...
    return (amplitude/(np.sqrt(2*np.pi)*sigma))* np.exp(-abs(x-center)**expon / (2*sigma**expon))


def createStages(cont="both",cam="onband",wavelength=None,width=1, filterConfig={},stages=5,lcvrTemp=[],offsets=[],step=None):
    '''Create a simulation of a multi stage lyot/bi-refigent filter similar to what is used in UCoMP
    
    Parameters:
    waveLength (float):  Tuning wavelength (should be in the same units of the FSR for UCoMP [nm])
    
    width (float): Parameter to define how many FSR cosine packets to disaply typicall this is set to just 1 tuning packet. 
    
    cont (enum "both","red",blue"): Defines the tuning offset for the stage0 crystal.  When cont is blank or set to both
                                    the continum is selected 50/50 from either side of the central wavelength.  When "red"
                                    or "blue" is selected a pi/8 phase shift is applied to the tuning.
                                    
    cam (enum "onband", "offband"): Defines if a pi/2 offset should be applied to stage 1.  When the pi/2 offset is applied
                                    stage1 (the last stage in the filter) acts like a sine funcion selecting the light at the
                                    first cosine null.  Operationally we use this feature to select a continum signal near 
                                    near the emission line.
                                    
    stages (int): Number of stages in the fitler, the more stages use the more the narrower the final emisison line, and the 
                  more supression of the wings.
                  

    offsets (list of floats equal to the number of stages):  Phase offset to apply to the tuning, this is use to simulate
                                                             tempature corrections applied in the filter.
                                                             
    filterConfig (dict):  Dictionay definining prameters related for tuning.
    
    filterConfig["FSR"]:  Free spectral range of the filter width of the COSINE funciton. 
                          Same physical units of wavelength and region. 
                          
    filterConfig["region"]: Central wavelength of the filter.  Same physical units of wavelength and FSR.
    filterConfig["refTemp"]: List of reference tempatures for tempature tuning corrections.  
                             Measured in the lab, before deployment.
    filterConfig["refCoff"]: List of tempature coefficents for tempature tuning corrections.
                             Measured in the lab, before deployment.
                             
    tempMeasurements (list):  List of acutal tempature measruements at time of data.  Phase correction for each 
                               stage is applied as: applied as phase - tempCoff*(tempMeasurement - refTemp)

    
    '''
    FSR = 1
    region = 0
    refTemp = 0 
    refCoff = 0 
    if "FSR" in filterConfig.keys():
        FSR = filterConfig["FSR"]
    if "region" in filterConfig.keys():
        region = filterConfig["region"]
    if "tempRef" in filterConfig.keys():
        refTemp = filterConfig["tempRef"]
    if "tempCof" in filterConfig.keys():
        refCoff = filterConfig["tempCof"]
    if wavelength == None:
        wavelength = region
    phase = np.zeros(stages)
    try:  #deal with times stages = 1 
        if cam != "onband":
            phase[1] = np.pi/2
        if cont =="red":
            phase[0] = -np.pi/8
        if cont =="blue":
            phase[0] = +np.pi/8
    except:
        pass
    if step == None:
        step = FSR/5000
    x = np.arange(region-FSR/2*width,region+FSR/2*width,step)
    result = np.ones(x.shape[0])
    if len(offsets) != stages:
        offsets = [0] * stages
        if len(lcvrTemp) == stages:
            offsets = (lcvrTemp-refTemp)*tempCoff
    for s in range(stages):
        result = result*np.cos(2**s*np.pi*(x-wavelength)/FSR + phase[s]-offsets[s])**2
    return x, result

'''
Pulls the relevant lyot filter config data out of a tuning_calibration ini file and puts it in a dictoary for 
use by createStages function.

period in the ini files is the FSR in nm. Thicker crystals have shorter periods

region (float): is the central wavelength of the emission line we plan to study in that region 
tempCof (list of floats) is the tempature correction coefficent for a filter.
tempRef (list of floats) is the refernce tempature for the tuning phases listed in the ini file
        The tempature correction code applies the following alorigthm:  
corrected phase[stageNum] = uncorrected phase[stageNum] - tempCof[stageNum]*(measured Temp[stageNum]- tempRef[stageNum])

'''
def getFilterConfig(filename):
    print
    filename = gitDirectory / filename
    dataF = open(filename,"r")
    data = dataF.readlines()
    ref = []
    cof = []
    tempRef = []
    tempCof = []
    period = []
    i = -1
    for line in data:
        if "reference_wavelength " in line:
            region = float(line.split("=")[-1])
        if "temp_coefficient =" in line:
            cof.append(float(line.split("=")[-1]))
        if "reference_temp =" in line:
            ref.append(float(line.split("=")[-1]))
        if "period =" in line:
            period.append(float(line.split("=")[-1]))
    dataF.close()
    FSR = period[np.argsort(period)[::-1][0]]
    
    #Stages in UCoMP are named 0-4 from going from the Sun to the cameras
    #But for this anayslis they are ordered from lowest frequency (highest FSR) to highest frequency.
    #So we need to reorder the tempature correction list by peroid so it can be applied.
    for i in np.argsort(period)[::-1]:
        tempRef.append(ref[i])
        tempCof.append(cof[i])
    return {"FSR":FSR,"region":region,"tempCof":tempCof,"tempRef":tempRef}
 
 

def find_nearest(array,value):
    return (np.abs(array-value)).argmin()


def UCoMPGetDailyFlatList(obsDate,waveRegion):
    flatLocation = f"{getRoute(obsDate, 'ucomp-process')}/{obsDate}/*flat.files.txt"
   # print(glob.glob(flatLocation))
    if len(glob.glob(flatLocation)) > 0:
        with open(glob.glob(flatLocation)[0]) as flatFile:
            flatList = flatFile.read()
        locationList = []
        for flatF in flatList.split("\n"):
            if f"ucomp.{waveRegion}.l0" in flatF:
                locationList.append(f"{getRoute(obsDate, 'ucomp-raw')}/{obsDate}/{flatF.split()[0]}")
        return locationList
#obsDate = "20220104"
#waveRegion = "1074"
#UCoMPGetDailyFlatList(obsDate,waveRegion)


import glob
def getRoute(obsDate, inst):
    with  open("/hao/dawn/Data/routing.cfg", "r") as route:
        line = route.readline()
        while inst not in line:  # The EOF char is an empty string
            if line == '':
                break
            line = route.readline()
        routing =""

        while obsDate[:4] not in line:
            line = route.readline()
            if "[" in line:
                break
            if "*" in line:
                routing = line.split(":")[-1]
    return routing.strip()
