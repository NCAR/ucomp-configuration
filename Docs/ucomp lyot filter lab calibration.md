# UCoMP Lyot fitler calibration Labview code.

**Frame Step 1**
Init DAQ analog/digital outputs.
Init Cropico (temp probe)

**Frame Step 2**
 - Loop N repeats (default of 5)
   -  Loop over per filers 
      -  Open fits file and start populating header information for dispersion, FSR and Temp setpoint.
      -  Configure grating 
      -  Loop over IXL diff[-1C,+1C]:
         -  Inner frame step 1
            -  Initialize camera exposure time, tec, NUC, gain
         -  Inner frame step 2
            -  Wait 3 minutes
         -  Inner frame step 3
            -  Adjust ILX to 35+ ILX  diff
            -  Wait ~1 hour to stabilize temps
         - Inner frame 4 (Dark)
           - Configure spectrograph blocking filer and mirror to block light to the camera.
           - Create LCVR tuning voltages of `[1.5, 1.5, 1.5, 1.5, 1.5]`
           - Drive DAQ output to Lyot filter and cameras to take numsum=12 images and record spectra across 80 rows at the row associated with each beam (at one point in the lab this was 345 and 450, but this will be different if setup is recreated since we did save fiber fixturing.)
           - Add spectra + relevant meta data to fits file (temps, voltages, target=dark, current time)
         - Inner frame 5 (main scans)
           - Configure spectrograph blocking filer and mirror to transmit light light to the camera.
           - Calculate 25 voltage steps between 1.64 and 10V, with voltage values taken from a natural log curve: `Drive voltages =[1.640000, 1.707029, 1.777163, 1.850704, 1.928001, 2.009457, 2.095545, 2.186825, 2.283963, 2.387763, 2.499206, 2.619508, 2.750200, 2.893248, 3.051235, 3.227648, 3.427360, 3.657475, 3.928942, 4.259952, 4.684180, 5.275646, 6.259727, 7.830641, 10.000000]`  
           - Create a 5 stage x 25 voltage Tuning array. Each of the 5 stages get a randomly ordered set of the 25 voltage steps. 
           - Loop STAGE over the 5 LCVR stages
             - LOOP ROW over the 25 rows in the Tuning array.
               - Loop VOLTAGE over the 25 voltages in the Drive voltages array.
                 - Replace the STAGE voltage value in the ROW with the current VOLTAGE from the Drive voltage array.
                 - Send the 5 LCVR voltages to the Lyot filter and record the same 2 regions of data taken in the DARK step.
                 - Add the 2 spectra + the relevant metadata to the FITS file as a new extension.
          - Inner frame 6 (Dark)
            - Repeat step 4
        - Close fits file

**Frame Step 3**
  - Stop camera and DAQ tasks 
  - Clean up spectragraph 


p