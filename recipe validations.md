# UCoMP Recipe/Cookbook Validation System

## Overview

The UCoMP (Upgraded Coronal Multi-channel Polarimeter) configuration repository contains the observing scripts and validation tools for the UCoMP instrument. The validation system ensures that all recipe, cookbook, and menu files follow the correct syntax and contain valid instrument commands before deployment to the telescope.

## Repository Structure

```
ucomp-configuration/
├── Recipes/                    # All observing scripts
│   ├── *.menu                  # Daily observing menus
│   ├── *.cbk                   # Cookbook programs
│   ├── *.rcp                   # Individual recipes
│   ├── *.md                    # Auto-generated markdown summaries
│   └── *.summary               # Auto-generated text summaries
└── validation_scripts/
    └── validator.py             # Recipe validation script
```

## Script Hierarchy

The UCoMP observing system uses a four-tier hierarchy:

```
Menu (.menu) - Daily observing schedule
├── Cookbook (.cbk) - Scientific/engineering programs
│   ├── Recipe (.rcp) - Individual instrument commands
│   │   ├── Hardware configuration commands
│   │   │   ├── Data collection commands
```

### File Types

- **Menu Files (`.menu`)**: Schedule for the days observing/engineering programs. 
- **Cookbook Files (`.cbk`)**: List of steps to execute an program. 
- **Recipe Files (`.rcp`)**: Step in the obseving program; either taking a data scan across the emission line or for setting up the instrument to be ready for the next scan.
- 
## Validator.py Script

Located at `validation_scripts/validator.py`, this script validates all menu files the `Recipes/` directory.  This command also creates a `Recipes/warnings.txt` file which lists all the rule infringements found. 

### Purpose

The validator ensures:
1. **Syntax correctness** - All commands follow proper format, such that that LabView code will execute it.
2. **Parameter validation** - Values are within acceptable ranges (for execution they may not make sense scientifically)
3. **Verify that proper darks and flats where taken** - Ensures that each coronal tuning command will is backed up by flats and data commands with the appropriate instrument/camera settings (note conditions at the observatory may prevent taking all the required data this check only verifies the scripts.).


### Validation Rules

#### Menu Rules:
- **File References**: All .cbk files must exist in the Recipe folder.

#### Cookbook rules
- **File References**: All .rcp files must exist in Recipes/ directory
- **Accecptable entire**:  Valid .rcp file, FOR/ENDFOR loop structure, or script metadata lines to be added to the fits header ["Author":"AUTHORNAME", "Date":"Date of edits/creation", "Description":"Short description of the program "]
- **Loop Structure**: Loop starts with a FOR LOOPNUM on one line followed by 1 or lines of commands followed ENDFOR.  LOOPNUM must be a positive integer

#### Recipe options:
- **Comment** `#` will cause the Labview code to ignore the rest of the Recipe line.
- **Child recipe** Valid .rcp file in Recipes/ directory
- **Data Command** Data collection command. 
- **Hardware Command** Valid hardware command 
- **Script Metadata**  One of ["Author":"AUTHORNAME", "Date":"Date of edits/creation", "Description":"Short description of the program "] to be store in the fits header.

## Suggested Data Recipe Naming Conventions

Recipe files should follow a standardized naming pattern:
```
<filter>_<waves>wave_<beams>beam_<sums>sums_<reps>rep_<continuum>.rcp
```
For example:
```
1074_03waves_2beam_14sums_1rep_both.rcp
DATA tcam both 1074.50 14     
DATA tcam both 1074.70 14
DATA tcam both 1074.90 14
DATA rcam both 1074.50 14
DATA rcam both 1074.70 14
DATA rcam both 1074.90 14
```
`03waves` Tells us there will be 3 tunings `1074.50`, `1074.7`,`1074.90` across the emission line.
`2beam` Tells us we should expect to see `wave` pairs of `tcam` and `rcam` tunings
`14sums` Tells us that `NUMSUM` should be 14
`1rep` Tells us that we will see 1 repetition of the block `waves`*`beams` lines 
`BOTH` Tells us the conitnum will be both.


####  Commands

##### Data Collection
```
DATA <camera> <continuum> <wavelength> <repeats>
```
- `camera`: Must be 'tcam' or 'rcam'
- `continuum`: Must be 'red', 'blue', or 'both'
- `wavelength`: Must be a float
- `repeats`: Must be an integer between 1-16

##### Prefilter Selection
```
PREFILTERRANGE <filter>
```
- Valid filters: 530, 637, 656, 670, 691, 706, 761, 789, 802, 991, 1074, 1079, 1083

##### Hardware Commands
- `EXPOSURE <ms>`: Range 1-80 ms
- `GAIN <setting>`: Must be 'high' or 'low'
- `O1 <position>`: Range 0-62 mm
- `FW <position>`: Range 0-8
- `SHUT <position>`: Must be 'in' or 'out'
- `OCC <position>`: Must be 'in' or 'out'
- `DIFFUSER <position>`: Must be 'in' or 'out'
- `COVER <position>`: Must be 'open' or 'closed'
- `CALIB <position>`: Must be 'in' or 'out'
- `CALRET <angle>`: Range 0-360 degrees
- `CALPOL <angle>`: Range 0-360 degrees
- `DISTORTIONGRID <position>`: Must be 'in' or 'out'
- `ND <position>`: Must be 'in' or 'out'


## Recipe Examples

### Dark Calibration Recipe
```recipe dark_2beam_14sums_1rep_BOTH.rcp
DESCRIPTION: Take 16 sum darks with 2 beams. 
AUTHOR: UCoMP Team
DATE: Jan 2, 2022
DATA tcam both 637.4 16  # T-camera, both continua, 16 sums
DATA rcam both 637.4 16  # R-camera, both continua, 16 sums

```

### Science Observation Recipe
```recipe 1074_03wave_2beam_14sums_1rep_BOTH.rcp
DESCRIPTION: Take a waves like scan across the 1074.7 FeXIII line. 
AUTHOR: UCoMP Team
DATE: Jan 2, 2022
DATA tcam both 1074.50 14
DATA tcam both 1074.70 14
DATA tcam both 1074.90 14
DATA rcam both 1074.50 14
DATA rcam both 1074.70 14
DATA rcam both 1074.90 14
```

## Cookbook Examples

### Synoptic Program
```cookbook
# all_wavelength_coronal.cbk
# Complete survey through all wavelengths

setupDark.rcp
dark_01wave_1beam_16sums_10rep_BOTH.rcp
setupObserving.rcp

# Cycle through all filters
637_FW.rcp
FOR 2
  637_03wave_2beam_16sums_4rep_BOTH.rcp
ENDFOR

670_FW.rcp
FOR 2
  670_03wave_2beam_16sums_4rep_BOTH.rcp
ENDFOR

706_FW.rcp
FOR 2
  706_03wave_2beam_16sums_4rep_BOTH.rcp
ENDFOR

# ... continues for all 9 filters
```

### Waves Program
```cookbook  waves_1074_1hour.cbk
Description: High-cadence observations for 1074.7 wave studies
Author: UCoMP Team
Date: Jan 1, 2022

1074_FW.rcp
setupDark.rcp
dark_01wave_1beam_14sums_10rep_BOTH.rcp
setupFlat.rcp 
1074_03wave_2beam_16sums_1_rep_BOTH.rcp
setupObserving.rcp
FOR 120
1074_03wave_2beam_14sums_1_rep_BOTH.rcp
ENDFOR
setupFlat.rcp 
1074_03wave_2beam_14sums_1_rep_BOTH.rcp

```

## Menu Example

```menu
# daily.menu
# Standard observing day schedule with polarization calibration

synoptic-original-lines.cbk
waves_1074_1hour.cbk
synoptic-original-lines.cbk
Pol_Cal_All_Filters.cbk
synoptic-original-lines.cbk
synoptic-new.cbk
```



Examples:
- `637_03wave_2beam_16sums_4rep_BOTH.rcp`
- `dark_80ms_2beam_16sums_BOTH.rcp`
- `1074_flat_2beam_16sums_2rep_BOTH.rcp`

## Auto-Generated Documentation

After each commit, GitHub Actions automatically generates:

1. **Markdown summaries** (`.md` files)
   - Collapsible sections showing full command hierarchy
   - Useful for reviewing observing programs

2. **Text summaries** (`.summary` files)
   - Flat list of all commands in execution order
   - Useful for quick command counting and time estimates


## Common Validation Errors

### Recipe Errors
- `Invalid camera name`: Use 'tcam' or 'rcam' only
- `Wavelength out of range`: Must be 530-1083 nm
- `Invalid repeat count`: Must be 1-16

### Cookbook Errors
- `Recipe file not found`: Verify .rcp file exists
- `Unmatched FOR/ENDFOR`: Check loop structure
- `Invalid loop count`: Must be positive integer

### Menu Errors
- `Cookbook file not found`: Verify .cbk file exists
- `Excessive observing time`: Reduce number of programs

## Best Practices

1. **Always validate before deployment**
   ```
   python validation_scripts/validator.py
   ```

2. **Test new recipes during engineering time**
   - Use engineering cookbooks for testing
   - Document any unusual configurations

3. **Version control discipline**
   - Commit changes with descriptive messages
   - Tag stable configurations for operations

4. **Documentation**
   - Comment complex command sequences
   - Update markdown files after major changes

## CI/CD Integration

The repository uses GitHub Actions to:
1. Run validator.py on all pull requests
2. Generate documentation after merges to main
3. Deploy validated configurations to operations

## Troubleshooting

### Common Issues

1. **Validator not finding files**
   - Ensure running from repository root
   - Check file extensions (.rcp, .cbk, .menu)

2. **Wavelength validation failures**
   - Verify wavelength is within filter passband
   - Check for typos in decimal points

3. **Loop count errors**
   - FOR loops require integer counts
   - Nested loops must be properly indented


## Related Repositories

- [ucomp-pipeline](https://github.com/NCAR/ucomp-pipeline): Data processing pipeline
- [comp-utilities](https://github.com/NCAR/comp-utilities): Analysis and visualization tools
