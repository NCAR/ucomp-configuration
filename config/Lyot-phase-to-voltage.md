The results from the wavelength calibration process are a set of phase-voltage tables for each wave region.  The code computes a phase->voltage map with nonimal tuning plus the information needed to tune to nearby wavelengths or compenstate for filter tempature changes.

The tables are stored in the ```tuning_calibration_????.ini files```, with data in  3 section types.  The Main section contains information common across all of the tuning parameters; for the real-time code, the important keys are reference_wavelength and wavelength_offset.  The reference wavelength is the nominal wavelength that we assumed the instrument was configured for when building the tuning parameters.  The wavelength_offset, which represents the offset between the tuning wavelength and the actual location of the emission line, was found in the sky.  For CoMP, this was a fixed value for the mission, but due to the drift in wavelength, as seen in UCoMP, this number has been updated periodically during the mission.  The voltage section contains an array of length number_of_volrages as defined in the Main section; this acts as the Y values in the spline fit between the phase and voltage lookup tables.  Finally, the Stage section is divided into information specific to the 5 Lyot filter stages.  This stage section contains an array of phase values of equal length of the voltage array, a measurement period (in nm) for the stage, and 3 values needed to perform the temperature correction of the temperature sensor, reference temperature, and temperature coefficient.

For the nominal tuning for the center wavelength, as calculated by the spectrograph, the tuning voltages will find the voltage associated with a phase 0 for each wave region. 
As an example, in the 1074.7 region, the stage0 has a zero phase value between 
```phase09 =   -0.0963289```
```phase10 =    0.0536209```
which maps to the voltages
```voltage09 =    2.0473660```
```voltage10 =    2.1002145```
Giving a stage0 voltage of ```~2.05V```.  With the same logic applied to the other 4 stages.  The observation does a spline fit between these two arrays to produce the mapping.

As noted above, we never take data at the zero phase offset tunings, so the following applies.


When these ini files are loaded into the real-time system, they are ready for tuning.  The recipes will provide a few facts about the tuning wavelength, the continuum location (BOTH, RED, BLUE), and the ONBAND camera.  These tuning controls and LCVR temperatures (all recorded in the fits header) drive voltages for the lyot filter.
First, we find the difference between the tuning wavelength and the reference wavelength
```diff_𝛌 = recipe_𝛌 - refernece_𝛌 - offset_𝛌 ```

Then, for each of the 5 stages, we compute the stage_phase using the period read from the ini files.
```stage_phase =( diff_𝛌 / stage_period -round(  diff_𝛌 / stage_period)) * π  ``` 
Here, we subtract the full phase to keep the tuning within the phase-voltage lookup tables.  The stage_phases are then corrected for the camera beam swapping, continuum location, and changes in the Lithium Niobate with the following corrections:
If onband is rcam  ```stage4_phase = stage4_phase +π/2```
If continuum is BLUE ```stage0_phase = stage0_phase -π/8```
If continuum is RED ```stage0_phase = stage0_phase +π/8```

When temperature correction is turned on (recorded in the T_COMPS fits keyword), the phase for each stage is changed by the following equation. ```stage_phase =stage_phase -( stage_temp -stage_refTemp)*stage_tempCoefficent ```
At this point, we check if the stage_phase is within the minimum and maximum phases in the stage’s phase array.  If the ```stage_phase``` is outside, this range is π added or subtracted as needed to move the stage_phase into the range of the phase table.


For example, one of the short wavelength measurements in the FeXIII 3-point waves program during the 2024 eclipse:
```DATA RCAM BOTH 1074.59 14 ```
```recipe_𝛌 = 1074.59```
```continuum = BOTH```
```ONBAND = RCAM```
```offset_𝛌  = 2.15```  (eclipse waveoff) 
```stage0_temp = 34.3 ``` (possible temp to do find actual observed eclipse temp)
```stage0_period = 5.1271543```


```diff_𝛌 = 1074.7 - 1074.59 - 2.15  = > -2.04```
```stage_phase0 =( -2.04 / 5.1271543 -round(  -2.04 / 5.1271543)) * π ```
```stage_phase0 =( -0.39788 -round( -0.39788)) * π```
Since the continuum is both, we dont have to add or subtract π/8
```stage_phase0 = -1.24998 -(34.3 - 34.536)*-0.2825676  => -1.317``` Rad
The ```-1.317``` value is outside the range of values in the phase table.
```-1.317 + π = 1.825 rad```
```phase21 =    1.8239643```
```phase22 =    1.9807401```
```voltage21 =    2.8504315
```voltage22 =    2.9413810 ```
Giving a stage0 voltage value of ```~2.86V```




