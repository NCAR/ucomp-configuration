# UCoMP Observing Scripts Description and Format

## Table of Contents

- [Folder Structure](#folder-structure)
- [Scripting File Types](#scripting-file-types)
- [Current Observing Programs](#current-observing-programs)
- [Automatically Generated Summary Files](#automatically-generated-summary-files)
- [Script File Descriptions](#script-file-descriptions)
- [UCoMP Recipe Commands](#ucomp-recipe-commands)

---

## Folder Structure

| Folder | Description |
|--------|-------------|
| `Recipes/` | Top-level UCoMP control scripts containing daily/engineering plans (`.menu` files) |
| `scripts/` | Observing/engineering programs (`.cbk`) and individual measurement/configuration scripts (`.rcp`) |
| `previous/` | History of previously run scripts, including MD5 hashes to help understand older observations |
| `summary/` | Plan file overviews in fully expanded list format |
| `tuningplots/` | Visual representations of expected bandpass for various measurements (accounts for Lyot filter FWHM, prefilter shape, and solar atlas) |

---

## Scripting File Types

| Extension | Name | Description |
|-----------|------|-------------|
| `.menu` | Menu | Top-level file loaded into the observing code to define the day's observations. Contains comments (text after `#`) or a list of `.cbk` files. |
| `.cbk` | Cookbook | Observing plan representing a scientific or engineering program (e.g., synoptic or waves). Composed of comments or calls to `.rcp` files. |
| `.rcp` | Recipe | Data collection or instrument configuration script. If it contains a `DATA` command, it creates a new `.fts` file with a FITS extension for each `DATA` command. |
| `.md` | Markdown Summary | Human-friendly expansion of the corresponding `.menu` file, including all subscripts, observing times, and bandpass plots. Auto-generated on commit. |
| `.summary` | Summary | Compressed version of the `.md` file showing only subscripts and subcommands. Auto-generated on commit. |

---

## Current Observing Programs

### Operational Emission Lines

Currently 5 of the 9 UCoMP emission lines are considered out of commissioning. Most observations are from:

- **FeXIII** 1074/1079
- **FeX** 637
- **FeXI** 789
- **FeXV** 706 (low signal outside active regions; may only run when active regions are on the limb)

### Science Programs

| Program | Description |
|---------|-------------|
| **Synoptic** | Cycles through operational wavelengths taking coronal data, flats, and darks. Typically measures 5 wavelengths across an emission with the 3rd centered on the line. |
| **FeXIII Wide Density Scans** | Similar to synoptic but focuses only on FeXIII, taking 7 points across the line. |
| **Waves** | ~1 hour of ~30-second 3-point 1074 measurements for Alfvén wave detection. |

### Engineering Programs

- **Polarization Calibration**: Measures modulator Mueller matrix; typically done once per week.
- **Other Engineering**: Ad hoc tests as needed.

The `daily.menu` or `daily_with_polarizations.menu` handles most normal observations. Other `.menu` files represent less common measurements.

---

## Automatically Generated Summary Files

When GitHub detects a commit to the ucomp-configuration repository, it automatically regenerates summary files for the daily menu scripts using the same rules as the real-time code to unroll menu → cookbook → recipe scripts into human-readable format.

### .summary Files

A flat text file with tree-like output showing the hierarchy of scripts:

```
   > daily.menu
 ------ > all_wavelength_coronal_flat.cbk
 ------------ > setupFlat.rcp
------------------> diffuser  in
------------------> cover out
------------------> occ       out
------------------> shut      out
------------------> calib     out
 ------------ > dark_01wave_1beam_16sums_10rep_BOTH.rcp
------------------> shut      in
------------------> data      rcam    both    656.28  16
....
```

### .md Files

Interactive markdown files with collapsible sections. Click the ▶ triangles to expand/explore. Icons indicate data type:


&#x1F4D7;  = data  
&#x1F4D8;  = flat  
&#x1F4D9;  = dark  
&#x1F4D5;  = calib<details><summary>daily.menu</summary><blockquote><pre><details><summary>synoptic_bright_lines.cbk</summary><blockquote><pre><details><summary>setupDark.rcp</summary><blockquote><pre>shut	in
 &#xE0020;
Integration:0.00 minutes.  Hardware:0.00 minutes. total:0.00 minutes 

 Darks:    
Flats:   
 Data:     
Calibs:   
</pre></blockquote></details><details><summary>&#x1F4D9; [dark_01wave_1beam_16sums_10rep_BOTH.rcp](tuningplots/dark_01wave_1beam_16sums_10rep_BOTH.rcp.png)</summary><blockquote><pre>shut	in
 &#xE0020;&#x1F4D9; data	rcam	both	656.28	16
 &#xE0020;&#x1F4D9; data	rcam	both	656.28	16
 &#xE0020;&#x1F4D9; data	rcam	both	656.28	16
 &#xE0020;&#x1F4D9; data	rcam	both	656.28	16
 &#xE0020;&#x1F4D9; data	rcam	both	656.28	16
 &#xE0020;&#x1F4D9; data	rcam	both	656.28	16
 &#xE0020;&#x1F4D9; data	rcam	both	656.28	16
 &#xE0020;&#x1F4D9; data	rcam	both	656.28	16
 &#xE0020;&#x1F4D9; data	rcam	both	656.28	16
 &#xE0020;&#x1F4D9; data	rcam	both	656.28	16
 &#xE0020;
Integration:1.05 minutes.  Hardware:0.00 minutes. total:1.05 minutes 

 Darks:  dark_01wave_1beam_16sums_10rep_BOTH.rcp  
Flats:   
 Data:     
Calibs:   
</pre></blockquote></details><details><summary>setupObserving.rcp</summary><blockquote><pre>shut	in
 &#xE0020;cover	out
 &#xE0020;calib	out
 &#xE0020;occ	in
 &#xE0020;diffuser	out
 &#xE0020;shut	out
 &#xE0020;
Integration:0.00 minutes.  Hardware:1.00 minutes. total:1.00 minutes 

 Darks:    
Flats:   
 Data:     
Calibs:   
</pre></blockquote></details><details><summary>1079_FW.rcp</summary><blockquote><pre>prefilterrange	1079
 &#xE0020;
Integration:0.00 minutes.  Hardware:0.42 minutes. total:0.42 minutes 

 Darks:    
Flats:   
 Data:     
Calibs:   
</pre></blockquote></details><details><summary>&#x1F4D7; [1079_05wave_0.1step_2beam_16sums_4rep_BOTH.rcp](tuningplots/1079_05wave_0.1step_2beam_16sums_4rep_BOTH.rcp.png)</summary><blockquote><pre>&#x1F4D7; data	rcam	both	1079.64	16
 &#xE0020;&#x1F4D7; data	rcam	both	1079.69	16
 &#xE0020;&#x1F4D7; data	rcam	both	1079.80	16
 &#xE0020;&#x1F4D7; data	rcam	both	1079.91	16
 &#xE0020;&#x1F4D7; data	rcam	both	1079.96	16
 &#xE0020;&#x1F4D7; data	tcam	both	1079.64	16
 &#xE0020;&#x1F4D7; data	tcam	both	1079.69	16
 &#xE0020;&#x1F4D7; data	tcam	both	1079.80	16
 &#xE0020;&#x1F4D7; data	tcam	both	1079.91	16
 &#xE0020;&#x1F4D7; data	tcam	both	1079.96	16
 &#xE0020;&#x1F4D7; data	rcam	both	1079.64	16
 &#xE0020;&#x1F4D7; data	rcam	both	1079.69	16
 &#xE0020;&#x1F4D7; data	rcam	both	1079.80	16
 &#xE0020;&#x1F4D7; data	rcam	both	1079.91	16
 &#xE0020;&#x1F4D7; data	rcam	both	1079.96	16
 &#xE0020;&#x1F4D7; data	tcam	both	1079.64	16
 &#xE0020;&#x1F4D7; data	tcam	both	1079.69	16
 &#xE0020;&#x1F4D7; data	tcam	both	1079.80	16
 &#xE0020;&#x1F4D7; data	tcam	both	1079.91	16
 &#xE0020;&#x1F4D7; data	tcam	both	1079.96	16
 &#xE0020;&#x1F4D7; data	rcam	both	1079.64	16
 &#xE0020;&#x1F4D7; data	rcam	both	1079.69	16
 &#xE0020;&#x1F4D7; data	rcam	both	1079.80	16
 &#xE0020;&#x1F4D7; data	rcam	both	1079.91	16
 &#xE0020;&#x1F4D7; data	rcam	both	1079.96	16
 &#xE0020;&#x1F4D7; data	tcam	both	1079.64	16
 &#xE0020;&#x1F4D7; data	tcam	both	1079.69	16
 &#xE0020;&#x1F4D7; data	tcam	both	1079.80	16
 &#xE0020;&#x1F4D7; data	tcam	both	1079.91	16
 &#xE0020;&#x1F4D7; data	tcam	both	1079.96	16
 &#xE0020;&#x1F4D7; data	rcam	both	1079.64	16
 &#xE0020;&#x1F4D7; data	rcam	both	1079.69	16
 &#xE0020;&#x1F4D7; data	rcam	both	1079.80	16
 &#xE0020;&#x1F4D7; data	rcam	both	1079.91	16
 &#xE0020;&#x1F4D7; data	rcam	both	1079.96	16
 &#xE0020;&#x1F4D7; data	tcam	both	1079.64	16
 &#xE0020;&#x1F4D7; data	tcam	both	1079.69	16
 &#xE0020;&#x1F4D7; data	tcam	both	1079.80	16
 &#xE0020;&#x1F4D7; data	tcam	both	1079.91	16
 &#xE0020;&#x1F4D7; data	tcam	both	1079.96	16
 &#xE0020;
Integration:4.20 minutes.  Hardware:0.00 minutes. total:4.20 minutes 

 Darks:    
Flats:   
 Data:   1079_05wave_0.1step_2beam_16sums_4rep_BOTH.rcp  
Calibs:   
</pre></blockquote></details><details><summary>1074_FW.rcp</summary><blockquote><pre>prefilterrange	1074
 &#xE0020;
Integration:0.00 minutes.  Hardware:0.42 minutes. total:0.42 minutes 

 Darks:    
Flats:   
 Data:     
Calibs:   
</pre></blockquote></details><details><summary>&#x1F4D7; [1074_05wave_0.1step_2beam_16sums_4rep_BOTH.rcp](tuningplots/1074_05wave_0.1step_2beam_16sums_4rep_BOTH.rcp.png)</summary><blockquote><pre>&#x1F4D7; data	rcam	both	1074.54	16
 &#xE0020;&#x1F4D7; data	rcam	both	1074.59	16
 &#xE0020;&#x1F4D7; data	rcam	both	1074.70	16
 &#xE0020;&#x1F4D7; data	rcam	both	1074.81	16
 &#xE0020;&#x1F4D7; data	rcam	both	1074.86	16
 &#xE0020;&#x1F4D7; data	tcam	both	1074.54	16
 &#xE0020;&#x1F4D7; data	tcam	both	1074.59	16
 &#xE0020;&#x1F4D7; data	tcam	both	1074.70	16
 &#xE0020;&#x1F4D7; data	tcam	both	1074.81	16
 &#xE0020;&#x1F4D7; data	tcam	both	1074.86	16
 &#xE0020;&#x1F4D7; data	rcam	both	1074.54	16
 &#xE0020;&#x1F4D7; data	rcam	both	1074.59	16
 &#xE0020;&#x1F4D7; data	rcam	both	1074.70	16
 &#xE0020;&#x1F4D7; data	rcam	both	1074.81	16
 &#xE0020;&#x1F4D7; data	rcam	both	1074.86	16
 &#xE0020;&#x1F4D7; data	tcam	both	1074.54	16
 &#xE0020;&#x1F4D7; data	tcam	both	1074.59	16
 &#xE0020;&#x1F4D7; data	tcam	both	1074.70	16
 &#xE0020;&#x1F4D7; data	tcam	both	1074.81	16
 &#xE0020;&#x1F4D7; data	tcam	both	1074.86	16
 &#xE0020;&#x1F4D7; data	rcam	both	1074.54	16
 &#xE0020;&#x1F4D7; data	rcam	both	1074.59	16
 &#xE0020;&#x1F4D7; data	rcam	both	1074.70	16
 &#xE0020;&#x1F4D7; data	rcam	both	1074.81	16
 &#xE0020;&#x1F4D7; data	rcam	both	1074.86	16
 &#xE0020;&#x1F4D7; data	tcam	both	1074.54	16
 &#xE0020;&#x1F4D7; data	tcam	both	1074.59	16
 &#xE0020;&#x1F4D7; data	tcam	both	1074.70	16
 &#xE0020;&#x1F4D7; data	tcam	both	1074.81	16
 &#xE0020;&#x1F4D7; data	tcam	both	1074.86	16
 &#xE0020;&#x1F4D7; data	rcam	both	1074.54	16
 &#xE0020;&#x1F4D7; data	rcam	both	1074.59	16
 &#xE0020;&#x1F4D7; data	rcam	both	1074.70	16
 &#xE0020;&#x1F4D7; data	rcam	both	1074.81	16
 &#xE0020;&#x1F4D7; data	rcam	both	1074.86	16
 &#xE0020;&#x1F4D7; data	tcam	both	1074.54	16
 &#xE0020;&#x1F4D7; data	tcam	both	1074.59	16
 &#xE0020;&#x1F4D7; data	tcam	both	1074.70	16
 &#xE0020;&#x1F4D7; data	tcam	both	1074.81	16
 &#xE0020;&#x1F4D7; data	tcam	both	1074.86	16
 &#xE0020;
Integration:4.20 minutes.  Hardware:0.00 minutes. total:4.20 minutes 

 Darks:    
Flats:   
 Data:   1074_05wave_0.1step_2beam_16sums_4rep_BOTH.rcp  
Calibs:   
</pre></blockquote></details><details><summary>setupFlat.rcp</summary><blockquote><pre>diffuser	in
 &#xE0020;cover	out
 &#xE0020;occ	out
 &#xE0020;shut	out
 &#xE0020;calib	out
 &#xE0020;
Integration:0.00 minutes.  Hardware:0.33 minutes. total:0.33 minutes 

 Darks:    
Flats:   
 Data:     
Calibs:   
</pre></blockquote></details><details><summary>1079_FW.rcp</summary><blockquote><pre>prefilterrange	1079
 &#xE0020;
Integration:0.00 minutes.  Hardware:0.42 minutes. total:0.42 minutes 

 Darks:    
Flats:   
 Data:     
Calibs:   
</pre></blockquote></details><details><summary>&#x1F4D8; [1079_05wave_0.1step_2beam_16sums_4rep_BOTH.rcp](tuningplots/1079_05wave_0.1step_2beam_16sums_4rep_BOTH.rcp.png)</summary><blockquote><pre>&#x1F4D8; data	rcam	both	1079.64	16
 &#xE0020;&#x1F4D8; data	rcam	both	1079.69	16
 &#xE0020;&#x1F4D8; data	rcam	both	1079.80	16
 &#xE0020;&#x1F4D8; data	rcam	both	1079.91	16
 &#xE0020;&#x1F4D8; data	rcam	both	1079.96	16
 &#xE0020;&#x1F4D8; data	tcam	both	1079.64	16
 &#xE0020;&#x1F4D8; data	tcam	both	1079.69	16
 &#xE0020;&#x1F4D8; data	tcam	both	1079.80	16
 &#xE0020;&#x1F4D8; data	tcam	both	1079.91	16
 &#xE0020;&#x1F4D8; data	tcam	both	1079.96	16
 &#xE0020;&#x1F4D8; data	rcam	both	1079.64	16
 &#xE0020;&#x1F4D8; data	rcam	both	1079.69	16
 &#xE0020;&#x1F4D8; data	rcam	both	1079.80	16
 &#xE0020;&#x1F4D8; data	rcam	both	1079.91	16
 &#xE0020;&#x1F4D8; data	rcam	both	1079.96	16
 &#xE0020;&#x1F4D8; data	tcam	both	1079.64	16
 &#xE0020;&#x1F4D8; data	tcam	both	1079.69	16
 &#xE0020;&#x1F4D8; data	tcam	both	1079.80	16
 &#xE0020;&#x1F4D8; data	tcam	both	1079.91	16
 &#xE0020;&#x1F4D8; data	tcam	both	1079.96	16
 &#xE0020;&#x1F4D8; data	rcam	both	1079.64	16
 &#xE0020;&#x1F4D8; data	rcam	both	1079.69	16
 &#xE0020;&#x1F4D8; data	rcam	both	1079.80	16
 &#xE0020;&#x1F4D8; data	rcam	both	1079.91	16
 &#xE0020;&#x1F4D8; data	rcam	both	1079.96	16
 &#xE0020;&#x1F4D8; data	tcam	both	1079.64	16
 &#xE0020;&#x1F4D8; data	tcam	both	1079.69	16
 &#xE0020;&#x1F4D8; data	tcam	both	1079.80	16
 &#xE0020;&#x1F4D8; data	tcam	both	1079.91	16
 &#xE0020;&#x1F4D8; data	tcam	both	1079.96	16
 &#xE0020;&#x1F4D8; data	rcam	both	1079.64	16
 &#xE0020;&#x1F4D8; data	rcam	both	1079.69	16
 &#xE0020;&#x1F4D8; data	rcam	both	1079.80	16
 &#xE0020;&#x1F4D8; data	rcam	both	1079.91	16
 &#xE0020;&#x1F4D8; data	rcam	both	1079.96	16
 &#xE0020;&#x1F4D8; data	tcam	both	1079.64	16
 &#xE0020;&#x1F4D8; data	tcam	both	1079.69	16
 &#xE0020;&#x1F4D8; data	tcam	both	1079.80	16
 &#xE0020;&#x1F4D8; data	tcam	both	1079.91	16
 &#xE0020;&#x1F4D8; data	tcam	both	1079.96	16
 &#xE0020;
Integration:4.20 minutes.  Hardware:0.00 minutes. total:4.20 minutes 

 Darks:    
Flats:  1079_05wave_0.1step_2beam_16sums_4rep_BOTH.rcp 
 Data:     
Calibs:   
</pre></blockquote></details><details><summary>1074_FW.rcp</summary><blockquote><pre>prefilterrange	1074
 &#xE0020;
Integration:0.00 minutes.  Hardware:0.42 minutes. total:0.42 minutes 

 Darks:    
Flats:   
 Data:     
Calibs:   
</pre></blockquote></details></details></details>
---

## Script File Descriptions

### Menu Files

Menu files specify multiple observing programs that can be mixed and matched throughout the day. Unless particular engineering tests are needed, the `daily.menu` combines synoptic, waves, and calibration cookbooks.

Example `daily.menu`:
```
synoptic_bright_lines.cbk
synoptic_feXIII_density.cbk
waves_1074_1hour.cbk
synoptic_bright_lines.cbk
synoptic_bright_lines.cbk
synoptic_bright_lines.cbk
```

Typically, the daily.menu is set up with 12+ hours of observing steps so there are always more script steps available, even for very long observing days.

### Cookbook Files

Cookbooks define programs with specific scientific or calibration goals. They contain lists of recipe files and can loop over sets of recipe lines using `FOR N` / `ENDFOR` blocks.

Example from `synoptic_bright_lines.cbk`:
```
setupDark.rcp
dark_01wave_1beam_16sums_10rep_BOTH.rcp
setupObserving.rcp

637_FW.rcp
FOR 2
637_03wave_2beam_16sums_4rep_BOTH.rcp
ENDFOR
```

This program: sets up for darks → takes darks → sets up for coronal observing → changes to 637 waveband → takes two sets of 637 data.

### Recipe Files

Recipes represent discrete observation steps. Each line can command instrument configuration changes, take image data, or call another recipe file.

---

## Current Science Programs

### Synoptic Program

**Files:**
- [all_wavelength_coronal.cbk](https://github.com/NCAR/ucomp-configuration/blob/main/Recipes/all_wavelength_coronal.cbk)
- [all_wavelength_coronal_flat.cbk](https://github.com/NCAR/ucomp-configuration/blob/main/Recipes/all_wavelength_coronal_flat.cbk)

The synoptic program cycles through all 9 prefilters (5 original 2021 filters + 4 replaced in Nov 2022). Within each filter, it performs 2 measurements averaging polarization data from 3 wavelength tunings over ~2.5 minutes, then proceeds to the next prefilter.

Current revisit time between prefilters: ~45 minutes. A planned reduction to 1 measurement per pass would reduce this to ~22 minutes for better tracking of dynamic events.

### Waves Program

**File:** [waves_1074_1hour.cbk](https://github.com/NCAR/ucomp-configuration/blob/main/Recipes/waves_1074_1hour.cbk)

Continues the Alfvén wave search from CoMP. Trades wavelength diversity and SNR for higher cadence: ~1 hour of 1074-only data with ~4.5 fewer integrations per wavelength/modulation mode, producing ~30-second FITS images.

---

## UCoMP Recipe Commands

### Science Data Collection

#### DATA

Takes one `4×2×1280×1024` image array and stores it as a FITS extension. The array comprises images taken across 4 polarization modulation states on two cameras with `1280×1024` pixel focal planes. Creates a new FITS file if none is open; one FITS file per top-level recipe containing DATA commands.

| Parameter | Description | Values |
|-----------|-------------|--------|
| Primary Camera | Camera receiving specified wavelength (other receives continuum) | `rcam`, `tcam` |
| Continuum Type | Location of continuum relative to central wavelength | `red`, `blue`, `both` |
| Wavelength | Lyot filter tuning location | `530`–`1083` nm |
| Repeats | Number of sums in instrument buffers | `1`–`16` |

With Repeats > 1, modulations are read interleaved (ModA1, ModB1, ModC1, ModD1, ModA2, ...) and summed (ModA = ModA1 + ModA2).

#### PREFILTERRANGE

Sets up for a new prefilter by moving O1 and filter wheel to known good positions.

| Parameter | Description | Values |
|-----------|-------------|--------|
| Prefilter Name | Integer part of central wavelength: floor(wavelength) | `637`, `670`, `706`, `761`, `789`, `802`, `991`, `1074`, `1079` |

### Optical Element Commands

| Command | Description | Values |
|---------|-------------|--------|
| `DIFFUSER` | Move calibration diffuser in/out of beam | `in`, `out` |
| `OCC` | Move occulter stage in/out of beam | `in`, `out` |
| `SHUT` | Move dark shutter in/out of beam | `in`, `out` |
| `CALIB` | Move calibration polarizer and retarder in/out of beam | `in`, `out` |
| `COVER` | Move lens cover in/out of beam (engineering) | `in`, `out` |

### Calibration Optic Angle Commands

| Command | Description | Values |
|---------|-------------|--------|
| `CALRET` | Set calibration retarder angle | Degrees |
| `CALPOL` | Set calibration polarizer angle | Degrees |

### Engineering Commands

These are not used during normal operation.

| Command | Description | Values |
|---------|-------------|--------|
| `ND` | Manual ND filter position (requires observer action) | `in`, `out` |
| `DISTORTIONGRID` | Manual distortion grid position (requires observer action) | `in`, `out` |
| `SAVEALL` | Toggle between summing like modulations vs. saving every modulation as separate FITS extension | `in` (save all), `out` (sum) |
| `EXPOSURE` | Set camera exposure time. Must precede DATA in same recipe. | `1`–`80` ms |
| `GAIN` | Set camera gain mode. Must precede DATA in same recipe. | `high`, `low` |
| `O1` | Move O1 to absolute position | `0`–`62` mm |
| `FW` | Move prefilter wheel to discrete position | `0`–`8` |

**Notes:**
- Early engineering found UCoMP is always photon-limited in coronal observations, so it typically runs at 80 ms (max exposure).
- Early engineering found insufficient sensitivity for coronal data in low gain mode.

---

## Version History

Changes to observing programs can be tracked on GitHub after July 15, 2021. Earlier changes were tracked in HAO Subversion; contact the UCoMP team for copies of pre-GitHub scripts.