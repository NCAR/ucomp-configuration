# UCoMP Observing Scripts description and format 


## Current observing programs and program locations: 

During the commission phase of the UCoMP program, we adopted two daily programs to demonstrate the instrument's capabilities.  These include the so-called **synoptic** program, which cycles thru taking data from all or most available prefilters.  And the so-called **waves** program sits on the 1074 line and produces an L0 data product every 30 seconds.   Both programs included sets of flats and darks relevant to the data taken. In 2021 and 2022, both programs saw changes in repose to things the commissioning team saw in the data; or changes to the instrument. One should not expect identical observing programs looking back in time thru commissioning.   Changes to these programs can be tracked on GitHub after July 15, 2021\.  Before moving to GitHub, changes were tracked in the HAO subversion; if programs are needed before this point, please email the UCoMP team for a copy.

During the commissioning phase, the team also ran other engineering programs.  The most common of these tests was a polarimetric calibration in each of the prefilters; this data set was used to create a demodulation matrix to convert our 4 L0 modulation states into IQUV stokes vectors.  Other engineering tests were run at ad hoc timing to measure various subsystems' optical distortion and stability of sub-systems.   It is not expected that most UCoMP data users will need or want to dig into the engineering data.

GitHub location to find all of the files  
[https://github.com/NCAR/ucomp-configuration/tree/main/Recipes](https://github.com/NCAR/ucomp-configuration/tree/main/Recipes)

The UCoMP real-time code executes its observing program by looking for files with .menu extensions in the git recipe folder.   These .menu files list one or more programs .cbk files to run in a top-to-bottom sequence.  And each of these programs comprises a series of small steps defined in .rcp files.  (Menus are full of cookbooks that contain recipes).    The default menu is called **daily.menu,** and outside of any special engineering goals, the program sequencer runs every day.  

Note that two files are produced for every .menu file in the repository after every GitHub commit. These are .md and .summary files, which provide an ordered breakdown of all the individual UCoMP commands to be run in that .menu file.  We encourage all readers of this document to review either of these daily.md or daily.summary files to understand the flow of these commands.  (Note the .md files are a collapsed list that expands/collapses when you push the triangles).  
[https://github.com/NCAR/ucomp-configuration/blob/main/Recipes/daily.md](https://github.com/NCAR/ucomp-configuration/blob/main/Recipes/daily.md)  
https://github.com/NCAR/ucomp-configuration/blob/main/Recipes/daily.summary

### Synoptic Program 

The current synoptic program is accomplished by two program files all\_wavelength\_coronal\_flat.cbk and all\_wavelength\_coronal.cbk.  This first program acquires a set of flats in each filter, and the second acquires the solar data.  These were broken out into two sub-programs to allow the team to vary the cadence flats relative to the solar data easily. Currently, we do two solar runs for each flat run.

[https://github.com/NCAR/ucomp-configuration/blob/main/Recipes/all\_wavelength\_coronal.cbk](https://github.com/NCAR/ucomp-configuration/blob/main/Recipes/all\_wavelength\_coronal.cbk)  
[https://github.com/NCAR/ucomp-configuration/blob/main/Recipes/all\_wavelength\_coronal\_flat.cbk](https://github.com/NCAR/ucomp-configuration/blob/main/Recipes/all\_wavelength\_coronal.cbk)

The current synoptic program cycles thought all 9 prefilters (5 of the original 2021 filters and 4 that were replaced in Nov 2022).  Within each filter, the program performs 2 measurements in which we average polarization data from 3 wavelength tunings over about 2.5 minutes.  Once both sets of averages are done, we proceed to the net prefilter.   It is likely that when UCoMP comes back line after the eruption, we will only take one measurement per pass thru the prefilters.   This will reduce the revisit time between prefilters from \~45 minutes to \~22, and should help better track dynamic events.  

### Waves Program 

[https://github.com/NCAR/ucomp-configuration/blob/main/Recipes/waves\_1074\_1hour.cbk](https://github.com/NCAR/ucomp-configuration/blob/main/Recipes/waves\_1074\_1hour.cbk)

The waves program is a continuation of the Alfen wave search that was performed with CoMP. We trade wavelength diversity and SNR for higher cadence observations in this program.  The waves program spends \~1 hour taking only 1074 data with \~4.5 few integrations in each of the wavelength/modulation modes, with each fits image taking \~30 seconds to collect.  

###  Instrument calibration programs

The UCoMP real-time controller software is a sequencer that reads its instructions step by step from a control script and executes that script from top to bottom unless and until the instrument operator intervenes due to weather or other issues. The software can restart where it was stopped or quit and run a new script.

The UCoMP scripting language was derived from the CoMP scripting language, and while the scripts are incompatible, they share common ideas.  The language is divided into three levels MENU files, where area list programs to run for the whole day; COOKBOOK files which define scientific programs and RECIPES, which execute a small set of instrument configurations or data collection.  Copies of the scripts can be found on GitHub at: [https://github.com/NCAR/ucomp-configuration/tree/main/Recipes](https://github.com/NCAR/ucomp-configuration/tree/main/Recipes)

## Automatically generated summary files

When GitHub detects a commit to the ucomp-configuration repository, it automatically runs some code to regenerate summary files for the daily menu scripts. This code uses the same rules as the real-time code to unravel the menu->cookbook->recipe scripts into a single human-readable format.  This has proven very helpful for understanding the execution and context of an observing program. This context is presented in two formats: the .summary file, which is a flat text file with an output similar to the unix tree command, and the .md file, which creates an interactive markdown file to allow the user to drill down on relevant sections of the program.

### .summary files
A summary file is generated for each .menu file in the GitHub repo, and it uses columns and arrows to show the hierarchy of scripts called during the observing program.   In the example code below the first observation of the day is a DARK a cookbook written  to take flats.  The first action the instrument will do is set up for flats, then set up for darks, and then run a dark recipe, which begins taking data.
```   > daily.menu
 ------ > all_wavelength_coronal_flat.cbk
 ------------ > setupFlat.rcp
------------------> diffuser  in
------------------> cover out
------------------> occ		out
------------------> shut	out
------------------> calib	out
 ------------ > dark_01wave_1beam_16sums_10rep_BOTH.rcp
------------------> shut	in
------------------> data	rcam	both	656.28	16
....
```

### .md
The markdown summary files show the same information as above but in an interactive way.  Click the ▶ &#9654;  button below to explore.

&#x1F4D9; =dark  
&#x1F4D5; =calib  
&#x1F4D8; =flat  
&#x1F4D7; =data 
<details><summary>daily.menu</summary><blockquote><pre><details><summary>all_wavelength_coronal_flat.cbk</summary><blockquote><pre><details><summary>setupFlat.rcp</summary><blockquote><pre> diffuser  in 
 cover out 
 occ		out 
 shut	out 
 calib	out 
 Integration:0.00 minutes.  Hardware:1.00 minutes. total:1.00 minutes  </pre></blockquote></details><details><summary>setupDark.rcp</summary><blockquote><pre> shut	in 
 Integration:0.00 minutes.  Hardware:0.00 minutes. total:0.00 minutes  </pre></blockquote></details><details><summary>&#x1F4D9; dark_01wave_1beam_16sums_10rep_BOTH.rcp</summary><blockquote><pre> shut	in 
&#x1F4D9;  data	rcam	both	656.28	16 
&#x1F4D9;  data	rcam	both	656.28	16 
&#x1F4D9;  data	rcam	both	656.28	16 
&#x1F4D9;  data	rcam	both	656.28	16 
&#x1F4D9;  data	rcam	both	656.28	16 
&#x1F4D9;  data	rcam	both	656.28	16 
&#x1F4D9;  data	rcam	both	656.28	16 
&#x1F4D9;  data	rcam	both	656.28	16 
&#x1F4D9;  data	rcam	both	656.28	16 
&#x1F4D9;  data	rcam	both	656.28	16 
 Integration:0.90 minutes.  Hardware:0.00 minutes. total:0.90 minutes  </pre></blockquote></details></details></details>

## Script files Descriptions

#### Menu files 

The MENU files are the simplest of these files and were born out of a desire in CoMP to specify multiple observing programs (i.e., Waves and Synoptic) that could be mixed and matched over the day.  Initially, in CoMP, we had one cookbook file that combined everything for a day, but we needed help tracking when the various scientific programs stopped and started.  And it took an effort to tell at a glance what programs were affected by any individual edit to the script file.  Unless particular engineering tests are needed, the observers daily.menu takes a combination of Synoptic, Waves, and calibrations cookbooks.  A snippet of a daily.menu can be found below:

all\_wavelength\_coronal\_flat.cbk  
all\_wavelength\_coronal.cbk  
all\_wavelength\_coronal.cbk  
waves\_1074\_1hour.cbk  
dark\_80ms\_2beam\_16sums\_BOTH.cbk  
637\_Pol\_Calibrate.cbk  
670\_Pol\_Calibrate.cbk

Here, we see a list of programs running for about 3 hours, taking synoptic data in all the pre-filters, waves data, and polarization calibration in 2 prefilters.  In normal operations, the observer would start the script just after sunrise. Then UCoMP would take a set of flats, followed by coronal data in all the prefilters, followed by 1 hour of staring at 1074 and some polarization calibrations.  Typically we have the daily.menu setup with 12+ hours of observing steps so that there are always more script steps available, even if the observer can run for a very long day. 

####  Cookbook files 

The COOKBOOK files represent observing programs with a particular purpose or goal. These could be scientific goals such as monitoring Alfven waves in our waves program or calibration goals where we take the data needed to produce the Mulermatrix for the 670 prefilters.  
COOKBOOKS are composed of lists of RECIPE files, or they can loop over a set of recipe lines multiple times with a FOR N, ENDFOR block.  An example of this is a section of the all\_wavelength\_coronal.cbk

setupDark.rcp  
dark\_01wave\_1beam\_16sums\_10rep\_BOTH.rcp  
setupObserving.rcp

637\_FW.rcp  
FOR 2  
637\_03wave\_2beam\_16sums\_4rep\_BOTH.rcp  
ENDFOR

This program sets the instrument to take darks, takes darks, sets up the instrument for coronal observing, changes the prefilter to the 637 wave band, and then takes two sets of 637 data.

#### Recipe Files

RECIPE files represent a discrete step in an observation.  Each line in the file can command a change in the instrument configuration,  take some image data, or call another RECIPE file to do more fine-grain work.   

## UCoMP Recipe commands: 

### Science data collection commands 

#### DATA 

DATA commands the instrument to take one  4x2x1280x1024 image array and store it as a FITS extension in the current working FITS file.   This array comprises images taken across 4 polarization modulation states on the two cameras with 1280x1024 pixel focal planes.   If no FITS files are currently open, a new one will be created with the relevant instrument.  UCoMP will create 1 FITS file for each top-level recipe that contains DATA commands.  (If a recipe calls multiple child recipes that also have DATA commands, these will all be collected to the same FITS file associated with the top-level recipe).

DATA takes 4 arguments:  
Primary Camera:  The camera receives the specified camera, with the other receiving the continuum.  \[rcam | tcam\]  
Continuum type:  The location of the continuum w.r.t. to the central wavelength \[red | blue| both\]  
Wavelength:  The wavelength tuning location for the lyot filter  \[530-1083\]nm  
Repeats:  The amount of summing the instrument should do in the instrument buffers Between 1 and 16\.  Note with Repeats=2  Cam0 will read out the repeated modulations interleaved with the other three modulations, Ie ModA1, ModB1, ModC1, ModD1, ModA2, ModB2, ModC2, ModD2.  With the recorded values for ModA \= ModA1+ModA2   \[1-16\]

#### PREFILTERRANGE 

Prefilter range commands the instrument to set up for a new prefilter; this moves the O1 and the filter well to a saved known good position to accommodate that prefilter.

PREFILTERRANGE takes 1 argument  
Prefilter name:  This is the integer part of the central wavelength of the prefilter defined as floor(wavelength)  \[637 | 670 | 706 | 761 |789 | 802 | 991 | 1074 | 1079\]

#### DIFFUSER 

Commands the instrument to move the calibration diffuser in or out of the beam.

Diffuser takes 1 argument  
Beam position:  The final position of the diffuser \[in | out\]

#### OCC 

Commands the instrument to move the occulter stage in or out of the beam.

OCC takes 1 argument  
Beam position:  The final position of the occulter stage \[in | out\]

#### SHUT

Commands the instrument to move the dark shutter in or out of the beam.

SHUT takes 1 argument  
Beam position:  The final position of the dark shutter\[in | out\]

#### CALRET  

Commands the instrument to move the calibration retarder to an angular position.

CALRET 1 argument:  
Retarder angle:  This is the final position of the retarder angle in degrees  \[degs\]

#### CALPOL 

 Commands the instrument to move the calibration polarizer to an angular position.

CALPOL 1 argument:  
Polarizer angle:  This is the final position of the polarizer angle in degrees  \[degs\]

#### CALIB 

Commands the instrument to move the calibration polarizer and retarder in or out of the beam.

CALIB takes 1 argument  
Beam position:  The final position of the calibration optics\[in | out\]

### Instrument engineering-specific commands 

These commands are not run during normal operation but are provided for instrument engineering tasks. 

#### Cover 

Commands the instrument to move the lens cover in or out of the beam.

Cover takes 1 argument  
Beam position:  The final position of the lens cover \[in | out\]


#### ND 

Commands the instrument/observer to manually put an ND filter in front of the lens cover in or out of the beam.  

ND takes 1 argument  
Beam position:  The final position of the manual ND filter \[in | out\]

#### DISTORTIONGRID

Commands the instrument/observer to manually put a distortion grid in place of the occulter in or out of the beam.

DISTORTIONGRID takes 1 argument  
Beam position:  The final position of the distortion grid \[in | out\]

#### SAVEALL

Changes the mode between summing like modulations when DATA Repeats \>1 into a single fits extension vs. saving every set of modulation reds a new FITS extension.  

SAVEALL takes 1 argument  
Beam position:  Mode to save all images \[in | out\].  In commands the instrument to save individual frames, while out commands the instrument to sum like frames.

#### EXPOSURE 

Commands the instrument to change the exposure time on the cameras.  UCoMP allows only one exposure time per fits file.  If EXPOSURE and DATA appear in the same recipe file, EXPOSURE must come first.  It is best practice for EXPOSURE (and other camera-related configurations) to be written into their own stand-alone recipe files.

Further, early UCoMP engineering found we are always photon limited in coronal observations, so we expect to run at 80ms (max camera exposure) all the time.

EXPOSURE takes 1 argument  
Exposure time:  Camera exposure time in \[1-80\] ms

#### GAIN 

Commands the instrument to change the GAIN mode on the cameras.  UCoMP requires one gain setting per fits file.  If GAIN and DATA appear in the same recipe file, GAIN must come first.  It is best practice for GAIN (and other camera-related configurations) to be written into their own stand-alone recipe files.

Further, early UCoMP engineering found that we don't have the sensitivity to collect coronal data in low gain.

GAIN takes 1 argument  
Camera gain:  Camera gain mode \[high | low\]

#### O1 

 Commands the instrument to move the O1 to an absolute position in mm within its range.  
O1 takes  1 argument:  
O1 pos:  Final position of the O1 \[0-62\]nm

#### FW  

Commands the instrument to move the prefilter wheel to a discrete position.  
FW takes 1 argument  
FW pos: Final index for the pre-filter wheel  \[0-8\]  
