# UCoMP instrument configuration scripts.

## Lyot filter tuning files.
### ``` Lyot Calibration.ini ``` defines the mapping from prefilter to calibration file.
### ``` tuning_calibration_[filter].ini ``` Tuning calibraiton for the fitler band.  
This file contains a lookup table for each of the 5 lyot filter states between a requested tuning phase and the output voltage sent to the LCVR.  If the code reproduces the values of the lab-derived tuning, the code will look at the phase value that is closest to 0 for each stage and the voltage value that maps to this phase.  For example in ``` tuning_calibration_1074.7.ini ``` stage0 has a phase closest to zero at ``` phase10 =    0.0536209 ``` which maps to ``` voltage10 =    2.1002145 ```.  

To tune the filter away from the lab ``` 0 phase voltage ```, we calculate ``` (wavelength - reference_wavelength - wavelength_offset)/period * Pi ``` to get the shifted phase. If we assume we are trying to tune to 1074.7 with ``` reference_wavelength = 1074.7 ``` and ``` wavelength_offset = 2.15 ``` and a ``` stage0_period = 5.1271543 ```, we get ``` -2.15/5.1271543 * pi = -1.317  or -1.317 + pi = 1.8241 ```. Looking at the stage0 phase table, the minimum value is ```-1.127``` which is larger than the tuning phase, so instead, we find ``` phase21 = 1.8239643 ``` is a better mapping giving a tuning voltage for stage0 of ``` voltage21 = 2.8504315 ```.  When tuning, the same algorithm is applied to the other 4 stages. 

Beyond wavelength tuning, we also apply 3 other phase shifts.  To prefrom beam swapping between ``` RCAM ``` and ``` TCAM ``` the code can add a ``` PI/2 ``` phase shift to stage4.  Like tuning the continuum between both side lobes or mostly a red or blue lobe, the real-time code will add or subtract ``` PI/4 ``` to the stage.  Finally, all the stages have an individual thermal response, which is corrected by adding ```tempature_phase_correction ``` to the ``` tuning_phase ```  ``` (current_measured_tempature - reference_temp)* -0.2825676 = tempature_phase_correction ```

## FITS header configuration
``` header_config.ini ``` Provides a mapping between labview data types/names and fits header types, names, and comments.  Editing this file will change the formats written into the FITS files.

``` header_static_data.ini ``` A collection of facts is used to create the fits headers that shouldn't change (much) over the course.  This includes ``` STATICINFO ```, which we expect to remain constant.  And ``` HWIDS ``` contains hardware identification that cannot be read from the equipment. This includes the ``` OCCLTRID ``` which defines the occulter in the instrument, which changes 4 times a year. Hardware upgrades may change other ID's

``` instrument_config.ini ``` Contains all the settings we give the instrument hardware.  Including named positions, camera settings, and logical routing information like COM ports and IP addresses. 

# Previous folder
When the observing code uses a ``` header_config.ini ``` or ``` instrument_config.ini ``` file, it computes an md5 cache of its contents, and if that hash has not been seen before, a copy of that ini is put into the previous folder with the md5 hash appended to the end.   This allows us to keep old config files for comparisons of who the instrument was setup at any given time.
