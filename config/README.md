# UCoMP instrument configuration scripts.

## Instrument configuration
``` instrument_config.ini ``` Contains all the settings we give the instrument hardware.  Including named positions, camera settings, and logical routing information like COM ports and IP addresses. 

## FITS header configuration
``` header_config.ini ``` Provides a mapping between labview data types/names and fits header types, names, and comments.  Editing this file will change the formats written into the FITS files.

``` header_static_data.ini ``` A collection of facts is used to create the fits headers that shouldn't change (much) over the course.  This includes ``` STATICINFO ```, which we expect to remain constant.  And ``` HWIDS ``` contains hardware identification that cannot be read from the equipment. This includes the ``` OCCLTRID ``` which defines the occulter in the instrument, which changes 4 times a year. Hardware upgrades may change other ID's


## Lyot filter tuning files.
### ``` Lyot Calibration.ini ``` defines the mapping from prefilter to calibration file.
### ``` tuning_calibration_[filter].ini ``` Tuning calibration for the filter band.        
This file contains a lookup table for each of the 5 lyot filter states between a requested tuning phase and the output voltage sent to the LCVR.  If the code reproduces the values of the lab-derived tuning, the code will look at the phase value that is closest to 0 for each stage and the voltage value that maps to this phase.   For a writeup on how the tuning works please review [Lyot-phase-to-voltage.md](Lyot-phase-to-voltage.md) in this directory.


# Previous folder
Local to track pervious versions of the config files. When a new version of the file is read in a copy will be placed in this folder with an md5 hash appended to file name.  This should allow tracking vs time.  We also plan to include a copy of the md5 hashes in the fits headers so we can see the state of the instrument when data were taken.
