#!/usr/bin/env python3
"""
UCoMP Recipe/Cookbook Validator

This module validates observing scripts for the Upgraded Coronal 
Multi-channel Polarimeter (UCoMP) instrument.

The validation system ensures:
1. Cookbook files reference existing recipes
2. Recipe files contain valid commands  
3. Coronal measurements have matching flats and darks
4. All command parameters are within valid ranges

Classes:
    ConfigManager: Loads and manages validation configuration
    CommandValidator: Validates individual commands
    InstrumentState: Tracks instrument state during validation
    ScriptValidator: Main validation orchestrator
    ValidationReporter: Generates validation reports

Usage:
    python validator.py                     # Validate all files
    python validator.py daily.menu          # Validate specific file
    python validator.py --format json       # Output as JSON
    python validator.py --verbose          # Show detailed output
"""

import os
import sys
import glob
import argparse
import json
import yaml
import logging
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set, Union, TextIO
from dataclasses import dataclass, field
from enum import Enum

# Try to import mlso_utils, provide fallback if not available
try:
    from mlso_utils import getFilterConfig, createStages, find_nearest
except ImportError:
    logging.warning("mlso_utils not found, some features may be limited")
    # Provide stub implementations
    def getFilterConfig(path): return {}
    def createStages(**kwargs): return [], []
    def find_nearest(array, value): return 0



# ============================================================================
# Constants and Configuration
# ============================================================================

class TimingConstants:
    """Hardware timing constants in seconds"""
    COVER_TIME = 60
    OCC_TIME = 20
    PREFILTER_TIME = 25
    ROTATE_TIME = 5
    CALIB_TIME = 20
    DIFFUSER_TIME = 20
    RELAXATION_TIME = 300
    
class CameraConstants:
    """Camera readout times in milliseconds"""
    READOUT_TIMES = {
        "high": 13.7,
        "low": 7.6
    }

class Icons:
    """Unicode icons for markdown output"""
    DATA = "&#x1F4D7;"
    FLAT = "&#x1F4D8;"
    DARK = "&#x1F4D9;"
    CALIB = "&#x1F4D5;"

class ValidationLevel(Enum):
    """Validation issue severity levels"""
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class ValidationIssue:
    """Container for validation issues"""
    level: ValidationLevel
    file: str
    message: str
    line: Optional[int] = None
    context: Optional[str] = None
    
    def __str__(self) -> str:
        location = f"{self.file}:{self.line}" if self.line else self.file
        msg = f"[{self.level.value}] {location}: {self.message}"
        if self.context:
            msg += f" (context: {self.context})"
        return msg


@dataclass
class ScriptTiming:
    """Timing information for a script"""
    integration_time: float = 0.0  # milliseconds
    hardware_time: float = 0.0     # seconds
    
    @property
    def total_minutes(self) -> float:
        """Total time in minutes"""
        return self.integration_time / 1000 / 60 + self.hardware_time / 60


# ============================================================================
# Configuration Management
# ============================================================================

class ConfigManager:
    """Loads and manages validation configuration"""
    
    DEFAULT_CONFIG = {
        'valid_commands': [
            "data", "cal", "dark", "fw", "occ", "diffuser", "calib",
            "occyrel", "saveall", "occxrel", "o1", "calret", "calpol",
            "cover", "shut", "exposure", "nd", "gain", "distortiongrid",
            "modwait", "prefilterrange"
        ],
        'ignore_commands': ["date", "author", "description"],
        'prefilters': ["530", "637", "656", "670", "691", "706", "761", 
                      "789", "802", "991", "1074", "1079", "1083"],
        'position_commands': ["cover", "occ", "shut", "calib", "diffuser", 
                             "distortiongrid", "nd"],
        'position_values': ["in", "out"],
        'gain_values': ["high", "low"],
        'camera_values': ["rcam", "tcam"],
        'continuum_values': ["both", "red", "blue"],
        'wavelength_range': {"min": 530, "max": 1083},
        'exposure_range': {"min": 1, "max": 84},
        'numsum_range': {"min": 1, "max": 16}
    }
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration manager
        
        Args:
            config_path: Path to YAML config file, or None to use defaults
        """
        if config_path and config_path.exists():
            self.load_from_file(config_path)
        else:
            self.config = self.DEFAULT_CONFIG.copy()
            
    def load_from_file(self, config_path: Path) -> None:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                loaded = yaml.safe_load(f)
                # Merge with defaults
                self.config = {**self.DEFAULT_CONFIG, **loaded}
        except Exception as e:
            logging.warning(f"Failed to load config from {config_path}: {e}")
            self.config = self.DEFAULT_CONFIG.copy()
    
    @property
    def valid_commands(self) -> List[str]:
        return self.config['valid_commands']
    
    @property
    def ignore_commands(self) -> List[str]:
        return self.config['ignore_commands']
    
    @property
    def prefilters(self) -> List[str]:
        return self.config['prefilters']
    
    @property
    def position_commands(self) -> List[str]:
        return self.config['position_commands']
    
    @property
    def position_values(self) -> List[str]:
        return self.config['position_values']


# ============================================================================
# Instrument State Tracking
# ============================================================================

class InstrumentState:
    """Tracks instrument state during validation"""
    
    def __init__(self):
        self.reset()
    
    def reset(self) -> None:
        """Reset to default state"""
        self.exposure = "80"
        self.shut = ""
        self.calib = ""
        self.occ = ""
        self.diffuser = ""
        self.gain = "high"
        self.filter = None
        self.calret = None
        self.calpol = None
        self.cover = ""
        
    def update(self, command: str, value: str) -> None:
        """Update state based on command"""
        if hasattr(self, command):
            setattr(self, command, value)
    
    def is_dark(self) -> bool:
        """Check if configuration is for dark frames"""
        return self.shut == "in"
    
    def is_flat(self) -> bool:
        """Check if configuration is for flat fields"""
        return (self.shut == "out" and 
                self.calib == "out" and 
                self.diffuser == "in")
    
    def is_coronal(self) -> bool:
        """Check if configuration is for coronal observation"""
        return (self.shut == "out" and 
                self.calib == "out" and 
                self.diffuser == "out")
    
    def is_calibration(self) -> bool:
        """Check if configuration is for calibration"""
        return (self.shut == "out" and 
                self.calib == "in" and 
                self.diffuser == "in")
    
    def get_signature(self, cam: str = "", cont: str = "", 
                     wave: str = "", sums: str = "") -> str:
        """Get configuration signature for matching darks/flats"""
        parts = []
        if self.exposure:
            parts.append(self.exposure)
        if self.gain:
            parts.append(self.gain)
        if sums:
            parts.append(sums)
        if cam:
            parts.append(cam)
        if cont:
            parts.append(cont)
        if wave:
            parts.append(wave)
        return "".join(parts)


# ============================================================================
# Command Validation
# ============================================================================

class CommandValidator:
    """Validates individual commands and their parameters"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        
    def validate_command(self, command: str, args: List[str], 
                        parent: str) -> Optional[ValidationIssue]:
        """Validate a single command with its arguments
        
        Args:
            command: Command name
            args: Command arguments
            parent: Parent context for error reporting
            
        Returns:
            ValidationIssue if validation fails, None if valid
        """
        # Check if command is valid
        if command not in self.config.valid_commands:
            if command not in self.config.ignore_commands:
                return ValidationIssue(
                    level=ValidationLevel.ERROR,
                    file=parent,
                    message=f"Unknown command: {command}",
                    context=" ".join([command] + args)
                )
            return None
        
        # Validate specific commands
        if command == "data":
            return self._validate_data_command(args, parent)
        elif command == "exposure":
            return self._validate_exposure(args, parent)
        elif command == "gain":
            return self._validate_gain(args, parent)
        elif command in self.config.position_commands:
            return self._validate_position(command, args, parent)
        elif command == "prefilterrange":
            return self._validate_prefilter(args, parent)
        elif command in ["calret", "calpol"]:
            return self._validate_angle(command, args, parent)
            
        return None
    
    def _validate_data_command(self, args: List[str], 
                               parent: str) -> Optional[ValidationIssue]:
        """Validate DATA command parameters"""
        if len(args) != 4:
            return ValidationIssue(
                level=ValidationLevel.ERROR,
                file=parent,
                message=f"DATA command requires 4 arguments, got {len(args)}",
                context=f"data {' '.join(args)}"
            )
        
        cam, cont, wave, sums = args
        
        # Validate camera
        if cam not in self.config.config['camera_values']:
            return ValidationIssue(
                level=ValidationLevel.ERROR,
                file=parent,
                message=f"Invalid camera: {cam}",
                context=f"Valid cameras: {self.config.config['camera_values']}"
            )
        
        # Validate continuum
        if cont not in self.config.config['continuum_values']:
            return ValidationIssue(
                level=ValidationLevel.ERROR,
                file=parent,
                message=f"Invalid continuum: {cont}",
                context=f"Valid values: {self.config.config['continuum_values']}"
            )
        
        # Validate wavelength
        try:
            wave_val = float(wave)
            wave_min = self.config.config['wavelength_range']['min']
            wave_max = self.config.config['wavelength_range']['max']
            if not (wave_min <= wave_val <= wave_max):
                return ValidationIssue(
                    level=ValidationLevel.ERROR,
                    file=parent,
                    message=f"Wavelength {wave} out of range ({wave_min}-{wave_max})",
                )
        except ValueError:
            return ValidationIssue(
                level=ValidationLevel.ERROR,
                file=parent,
                message=f"Wavelength must be a number: {wave}",
            )
        
        # Validate numsum as integer
        try:
            sums_val = int(sums)
            sums_min = self.config.config['numsum_range']['min']
            sums_max = self.config.config['numsum_range']['max']
            if not (sums_min <= sums_val <= sums_max):
                return ValidationIssue(
                    level=ValidationLevel.ERROR,
                    file=parent,
                    message=f"Numsum {sums} out of range ({sums_min}-{sums_max})",
                )
        except ValueError:
            return ValidationIssue(
                level=ValidationLevel.ERROR,
                file=parent,
                message=f"Numsum must be an integer: {sums}",
            )
        
        return None
    
    def _validate_exposure(self, args: List[str], 
                          parent: str) -> Optional[ValidationIssue]:
        """Validate exposure time"""
        if len(args) != 1:
            return ValidationIssue(
                level=ValidationLevel.ERROR,
                file=parent,
                message="EXPOSURE command requires 1 argument"
            )
        
        try:
            exp = float(args[0])
            exp_min = self.config.config['exposure_range']['min']
            exp_max = self.config.config['exposure_range']['max']
            if not (exp_min <= exp <= exp_max):
                return ValidationIssue(
                    level=ValidationLevel.ERROR,
                    file=parent,
                    message=f"Exposure {exp}ms out of range ({exp_min}-{exp_max}ms)"
                )
        except ValueError:
            return ValidationIssue(
                level=ValidationLevel.ERROR,
                file=parent,
                message=f"Exposure must be a number: {args[0]}"
            )
        
        return None
    
    def _validate_gain(self, args: List[str], 
                      parent: str) -> Optional[ValidationIssue]:
        """Validate gain setting"""
        if len(args) != 1:
            return ValidationIssue(
                level=ValidationLevel.ERROR,
                file=parent,
                message="GAIN command requires 1 argument"
            )
        
        if args[0] not in self.config.config['gain_values']:
            return ValidationIssue(
                level=ValidationLevel.ERROR,
                file=parent,
                message=f"Invalid gain: {args[0]}",
                context=f"Valid values: {self.config.config['gain_values']}"
            )
        
        return None
    
    def _validate_position(self, command: str, args: List[str], 
                          parent: str) -> Optional[ValidationIssue]:
        """Validate position commands (in/out)"""
        if len(args) != 1:
            return ValidationIssue(
                level=ValidationLevel.ERROR,
                file=parent,
                message=f"{command.upper()} command requires 1 argument"
            )
        
        if args[0] not in self.config.position_values:
            return ValidationIssue(
                level=ValidationLevel.ERROR,
                file=parent,
                message=f"Invalid position for {command}: {args[0]}",
                context=f"Valid values: {self.config.position_values}"
            )
        
        return None
    
    def _validate_prefilter(self, args: List[str], 
                           parent: str) -> Optional[ValidationIssue]:
        """Validate prefilter selection"""
        if len(args) != 1:
            return ValidationIssue(
                level=ValidationLevel.ERROR,
                file=parent,
                message="PREFILTERRANGE command requires 1 argument"
            )
        
        if args[0] not in self.config.prefilters:
            return ValidationIssue(
                level=ValidationLevel.ERROR,
                file=parent,
                message=f"Invalid prefilter: {args[0]}",
                context=f"Valid filters: {', '.join(self.config.prefilters)}"
            )
        
        return None
    
    def _validate_angle(self, command: str, args: List[str], 
                       parent: str) -> Optional[ValidationIssue]:
        """Validate angle commands (calret, calpol)"""
        if len(args) != 1:
            return ValidationIssue(
                level=ValidationLevel.ERROR,
                file=parent,
                message=f"{command.upper()} command requires 1 argument"
            )
        
        try:
            angle = float(args[0])
            if not (0 <= angle <= 360):
                return ValidationIssue(
                    level=ValidationLevel.WARNING,
                    file=parent,
                    message=f"Angle {angle} outside normal range (0-360)"
                )
        except ValueError:
            return ValidationIssue(
                level=ValidationLevel.ERROR,
                file=parent,
                message=f"Angle must be a number: {args[0]}"
            )
        
        return None


# ============================================================================
# Main Validation Logic
# ============================================================================

class ScriptValidator:
    """Main validation orchestrator for menu, cookbook, and recipe files"""
    
    def __init__(self, recipes_dir: Path, config: ConfigManager):
        """Initialize validator
        
        Args:
            recipes_dir: Directory containing recipe files
            config: Configuration manager instance
        """
        self.recipes_dir = Path(recipes_dir).resolve()
        self.config = config
        self.command_validator = CommandValidator(config)
        self.issues: List[ValidationIssue] = []
        self.state = InstrumentState()
        
        # Data collection tracking
        self.darks: List[str] = []
        self.flats: List[str] = []
        self.coronal: List[str] = []
        self.coronal_exp: List[str] = []
        
        # Timing tracking
        self.timing = ScriptTiming()
        
        # Tuning configurations (if available)
        self.tuning_configs: Dict = {}
        self.seen_tunings: Dict = {}
        self._load_tuning_configs()
        
    def _load_tuning_configs(self) -> None:
        """Load tuning configurations if available"""
        try:
            atlas = self._get_kitt_peak_atlas()
            for tuning_config in glob.glob("../resource/*ini"):
                key = Path(tuning_config).name.split("_")[-1].split(".")[0]
                self.tuning_configs[key] = getFilterConfig(tuning_config)
                
                csv_files = glob.glob(f"../resource/{key}*.csv")
                if csv_files:
                    prefilter = np.loadtxt(csv_files[0], delimiter=",", skiprows=10)
                    self.tuning_configs[key]["prefilter"] = prefilter
        except Exception as e:
            logging.debug(f"Could not load tuning configs: {e}")
    
    def _get_kitt_peak_atlas(self) -> np.ndarray:
        """Load Kitt Peak atlas data"""
        atlas = np.zeros([0, 3])
        for atlas_name in glob.glob("../resource/lm*"):
            try:
                atlas1 = np.loadtxt(atlas_name)
                atlas = np.concatenate((atlas, atlas1), axis=0)
            except Exception:
                pass
        return atlas
    
    def validate_menu(self, menu_file: Path) -> List[ValidationIssue]:
        """Validate a menu file and all referenced cookbooks
        
        Args:
            menu_file: Path to menu file
            
        Returns:
            List of validation issues found
        """
        self.issues = []
        self.state.reset()
        self.darks = []
        self.flats = []
        self.coronal = []
        self.coronal_exp = []
        
        # Check for NOWARNING flag
        with open(menu_file, 'r') as f:
            content = f.read()
            if "NOWARNING" in content:
                logging.info(f"Skipping {menu_file} due to NOWARNING flag")
                return []
        
        # Process menu file
        self._process_script(menu_file, str(menu_file), 0, ".cbk")
        
        # Cross-validation for darks and flats
        self._validate_darks_and_flats(str(menu_file))
        
        return self.issues
    
    def validate_cookbook(self, cookbook_file: Path) -> List[ValidationIssue]:
        """Validate a cookbook file
        
        Args:
            cookbook_file: Path to cookbook file
            
        Returns:
            List of validation issues found
        """
        self.issues = []
        self.state.reset()
        self._process_script(cookbook_file, str(cookbook_file), 0, ".rcp")
        return self.issues
    
    def validate_recipe(self, recipe_file: Path) -> List[ValidationIssue]:
        """Validate a recipe file
        
        Args:
            recipe_file: Path to recipe file
            
        Returns:
            List of validation issues found
        """
        self.issues = []
        self.state.reset()
        self._process_recipe_contents(recipe_file, str(recipe_file))
        return self.issues
    
    def _process_script(self, script_path: Path, parent: str, 
                       depth: int, child_extension: str) -> Tuple[float, float]:
        """Process a script file (menu, cookbook, or recipe)
        
        Args:
            script_path: Path to script file
            parent: Parent context for error reporting
            depth: Nesting depth for tracking
            child_extension: Expected extension for child files
            
        Returns:
            Tuple of (integration_time_ms, hardware_time_s)
        """
        # Reset collection tracking for top-level cookbooks
        if child_extension != ".rcp":
            self.coronal = []
            self.coronal_exp = []
        
        # Find file (case-insensitive)
        script_name = self._find_file(script_path)
        if not script_name:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                file=parent,
                message=f"File not found: {script_path}"
            ))
            return 0, 0
        
        # Read and process file
        with open(script_name, 'r') as f:
            lines = f.readlines()
        
        # Unroll FOR loops if cookbook
        if ".cbk" in str(script_name):
            lines = self._unroll_forloop(lines)
        
        run_time = 0.0
        hardware_time = 0.0
        
        # Process each line
        for line in lines:
            # Remove comments and clean
            line = line.split('#')[0].strip()
            if not line:
                continue
            
            commands = line.lower().split()
            if not commands:
                continue
            
            # Check for child script reference
            if child_extension in commands[0]:
                child_path = self.recipes_dir / commands[0]
                t_time, h_time = self._process_script(
                    child_path, f"{parent},{commands[0]}", 
                    depth + 1, ".rcp"
                )
                run_time += t_time
                hardware_time += h_time
            else:
                # Process command
                timing = self._process_command(commands, parent)
                if timing:
                    run_time += timing[0]
                    hardware_time += timing[1]
        
        # Validate darks/flats for cookbooks
        if child_extension != ".rcp":
            self._validate_cookbook_completeness(parent)
        
        return run_time, hardware_time
    
    def _process_recipe_contents(self, recipe_path: Path, parent: str) -> None:
        """Process the contents of a recipe file"""
        with open(recipe_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                # Remove comments and clean
                line_clean = line.split('#')[0].strip().lower()
                if not line_clean:
                    continue
                
                commands = line_clean.split()
                if not commands:
                    continue
                
                # Validate command
                issue = self.command_validator.validate_command(
                    commands[0], commands[1:], parent
                )
                if issue:
                    issue.line = line_num
                    self.issues.append(issue)
                
                # Process command for state tracking
                self._process_command(commands, parent)
    
    def _process_command(self, commands: List[str], 
                        parent: str) -> Optional[Tuple[float, float]]:
        """Process a single command
        
        Args:
            commands: Command and arguments
            parent: Parent context
            
        Returns:
            Tuple of (integration_time_ms, hardware_time_s) if applicable
        """
        if not commands:
            return None
        
        command = commands[0]
        args = commands[1:] if len(commands) > 1 else []
        
        # Skip ignored commands
        if command in self.config.ignore_commands:
            return None
        
        # Validate command
        issue = self.command_validator.validate_command(command, args, parent)
        if issue:
            self.issues.append(issue)
            return None
        
        run_time = 0.0
        hardware_time = 0.0
        
        # Update state and calculate timing
        if command == "gain" and args:
            self.state.update("gain", args[0])
            
        elif command == "shut" and args:
            self.state.update("shut", args[0])
            
        elif command == "exposure" and args:
            self.state.update("exposure", args[0])
            
        elif command == "cover" and args:
            if self.state.cover != args[0]:
                hardware_time += TimingConstants.COVER_TIME
            self.state.update("cover", args[0])
            
        elif command == "occ" and args:
            if self.state.occ != args[0]:
                hardware_time += TimingConstants.OCC_TIME
            self.state.update("occ", args[0])
            
        elif command == "prefilterrange" and args:
            if self.state.filter != args[0]:
                hardware_time += TimingConstants.PREFILTER_TIME
            self.state.update("filter", args[0])
            
        elif command == "calret" and args:
            if self.state.calret != args[0]:
                hardware_time += TimingConstants.ROTATE_TIME
            self.state.update("calret", args[0])
            
        elif command == "calpol" and args:
            if self.state.calpol != args[0]:
                hardware_time += TimingConstants.ROTATE_TIME
            self.state.update("calpol", args[0])
            
        elif command == "calib" and args:
            if self.state.calib != args[0]:
                hardware_time += TimingConstants.CALIB_TIME
            self.state.update("calib", args[0])
            
        elif command == "diffuser" and args:
            if self.state.diffuser != args[0]:
                hardware_time += TimingConstants.DIFFUSER_TIME
            self.state.update("diffuser", args[0])
            
        elif command == "data" and len(args) == 4:
            # Track data collection
            cam, cont, wave, sums = args
            
            if self.state.is_dark():
                sig = self.state.get_signature(sums=sums)
                if sig not in self.darks:
                    self.darks.append(sig)
                    
            elif self.state.is_flat():
                sig = self.state.get_signature(cam, cont, wave, sums)
                if sig not in self.flats:
                    self.flats.append(sig)
                    
            elif self.state.is_coronal():
                self.coronal.append(self.state.get_signature(cam, cont, wave, sums))
                self.coronal_exp.append(self.state.get_signature(sums=sums))
            
            # Calculate timing
            try:
                exp_time = float(self.state.exposure)
                num_sums = int(sums)
                readout = CameraConstants.READOUT_TIMES.get(self.state.gain, 10)
                run_time = (TimingConstants.RELAXATION_TIME + 
                           (exp_time + readout) * 4 * num_sums)
            except (ValueError, KeyError):
                pass
        
        return run_time, hardware_time
    
    def _unroll_forloop(self, lines: List[str]) -> List[str]:
        """Unroll FOR loops in cookbook files
        
        Args:
            lines: Lines from cookbook file
            
        Returns:
            Lines with FOR loops expanded
        """
        result = []
        i = 0
        while i < len(lines):
            line = lines[i].split('#')[0].strip().lower()
            
            if line.startswith('for '):
                try:
                    count = int(line.split()[1])
                    i += 1
                    loop_body = []
                    
                    # Collect loop body
                    while i < len(lines):
                        inner_line = lines[i].split('#')[0].strip().lower()
                        if inner_line == 'endfor':
                            break
                        loop_body.append(lines[i])
                        i += 1
                    
                    # Expand loop
                    for _ in range(count):
                        result.extend(loop_body)
                        
                except (IndexError, ValueError) as e:
                    self.issues.append(ValidationIssue(
                        level=ValidationLevel.ERROR,
                        file="cookbook",
                        message=f"Invalid FOR loop: {line}"
                    ))
            else:
                result.append(lines[i])
            
            i += 1
        
        return result
    
    def _validate_darks_and_flats(self, parent: str) -> None:
        """Validate that coronal observations have matching darks and flats"""
        for corona in self.coronal_exp:
            if corona not in self.darks:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    file=parent,
                    message=f"Missing dark for configuration: {corona}"
                ))
        
        for corona in self.coronal:
            if corona not in self.flats:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    file=parent,
                    message=f"Missing flat for configuration: {corona}"
                ))
    
    def _validate_cookbook_completeness(self, parent: str) -> None:
        """Validate completeness of cookbook (darks/flats for coronals)"""
        self._validate_darks_and_flats(parent)
    
    def _find_file(self, file_path: Union[Path, str]) -> Optional[Path]:
        """Find file with case-insensitive matching
        
        Args:
            file_path: Path or name of file to find
            
        Returns:
            Path to file if found, None otherwise
        """
        file_name = Path(file_path).name
        
        # Try exact match first
        if Path(file_path).exists():
            return Path(file_path)
        
        # Try in recipes directory
        full_path = self.recipes_dir / file_name
        if full_path.exists():
            return full_path
        
        # Try case-insensitive match
        for file in self.recipes_dir.iterdir():
            if file.name.lower() == file_name.lower():
                return file
        
        return None


# ============================================================================
# Plotting Functions
# ============================================================================

class TuningPlotter:
    """Generates tuning profile plots for recipes"""
    
    def __init__(self, tuning_configs: Dict, atlas: Optional[np.ndarray] = None):
        self.tuning_configs = tuning_configs
        self.atlas = atlas
        self.seen_tunings: Dict = {}
        
    def read_and_plot_rcp(self, recipe_path: Path, output_dir: Path) -> None:
        """Generate tuning plot for a recipe file
        
        Args:
            recipe_path: Path to recipe file
            output_dir: Directory for output plots
        """
        # Create output directory if needed
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / f"{recipe_path.name}.png"
        
        # Skip if already exists
        if output_file.exists():
            return
        
        # Extract wavelengths from DATA commands
        waves = []
        with open(recipe_path, 'r') as f:
            for line in f:
                line = line.split('#')[0].strip().lower()
                parts = line.split()
                if len(parts) >= 4 and parts[0] == "data":
                    waves.append(f"{parts[3]} {parts[2]}")
        
        if not waves or not self.tuning_configs:
            return
        
        try:
            # Generate plot
            fig = plt.figure(figsize=(10, 6))
            plt.title(f"{recipe_path.name}\nTuning Profiles + Pre-filter and Kitt Peak Atlas")
            
            # Determine which tuning configuration to use
            mean_wave = np.mean([float(w.split()[0]) for w in waves])
            wave_keys = np.array(list(self.tuning_configs.keys()), dtype=np.uint16)
            tuning_key = list(self.tuning_configs.keys())[
                find_nearest(wave_keys, mean_wave)
            ]
            
            if "prefilter" in self.tuning_configs[tuning_key]:
                for key in sorted(set(waves)):
                    wave_val = float(key.split()[0])
                    cont = key.split()[1].lower()
                    
                    # Calculate convolutions
                    for cam in ["onband", "offband"]:
                        cache_key = f"{key}{cam}"
                        if cache_key not in self.seen_tunings:
                            self.seen_tunings[cache_key] = self._convolve_filters(
                                wave_val, self.tuning_configs[tuning_key], cam, cont
                            )
                        
                        plt.plot(*self.seen_tunings[cache_key], 
                                label=f"{wave_val:.2f} {cont} {cam}")
                
                # Plot prefilter
                prefilter = self.tuning_configs[tuning_key]["prefilter"]
                plt.plot(prefilter[:, 0], prefilter[:, 1], 'k--', alpha=0.5)
            
            plt.ylabel("Filter throughput [%]")
            plt.xlabel("Wavelength [nm]")
            plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
            plt.tight_layout()
            
            fig.savefig(output_file, bbox_inches='tight')
            plt.close(fig)
            
        except Exception as e:
            logging.debug(f"Failed to generate plot for {recipe_path}: {e}")
            plt.close('all')
    
    def _convolve_filters(self, wave: float, config: Dict, 
                         cam: str = "onband", cont: str = "both") -> Tuple:
        """Calculate filter convolution
        
        Args:
            wave: Wavelength
            config: Tuning configuration
            cam: Camera type
            cont: Continuum type
            
        Returns:
            Tuple of (wavelengths, transmissions)
        """
        try:
            tuning_wave, tuning_trans = createStages(
                filterConfig=config, wavelength=wave, cam=cam, cont=cont
            )
            
            if "prefilter" in config:
                for i in range(len(tuning_wave)):
                    idx = find_nearest(config["prefilter"][:, 0], tuning_wave[i])
                    tuning_trans[i] *= config["prefilter"][idx, 1]
            
            return tuning_wave, tuning_trans
        except Exception:
            return [], []


# ============================================================================
# Report Generation
# ============================================================================

class ValidationReporter:
    """Generates validation reports in various formats"""
    
    def __init__(self, format_type: str = "text"):
        """Initialize reporter
        
        Args:
            format_type: Output format (text, json, github, markdown)
        """
        self.format = format_type
        self.issues: List[ValidationIssue] = []
        
    def add_issues(self, issues: List[ValidationIssue]) -> None:
        """Add issues to report"""
        self.issues.extend(issues)
    
    def generate_report(self) -> str:
        """Generate report in specified format
        
        Returns:
            Formatted report string
        """
        if self.format == "json":
            return self._json_report()
        elif self.format == "github":
            return self._github_report()
        elif self.format == "markdown":
            return self._markdown_report()
        else:
            return self._text_report()
    
    def _text_report(self) -> str:
        """Generate human-readable text report"""
        if not self.issues:
            return "No validation issues found."
        
        lines = []
        # Group by file
        by_file: Dict[str, List[ValidationIssue]] = {}
        for issue in self.issues:
            if issue.file not in by_file:
                by_file[issue.file] = []
            by_file[issue.file].append(issue)
        
        for file, file_issues in sorted(by_file.items()):
            lines.append(f"\n{file}:")
            for issue in sorted(file_issues, key=lambda x: x.line or 0):
                location = f"  Line {issue.line}" if issue.line else "  "
                lines.append(f"{location}: [{issue.level.value}] {issue.message}")
                if issue.context:
                    lines.append(f"    Context: {issue.context}")
        
        # Summary
        error_count = sum(1 for i in self.issues if i.level == ValidationLevel.ERROR)
        warning_count = sum(1 for i in self.issues if i.level == ValidationLevel.WARNING)
        lines.append(f"\nSummary: {error_count} errors, {warning_count} warnings")
        
        return "\n".join(lines)
    
    def _json_report(self) -> str:
        """Generate JSON report"""
        data = {
            "issues": [
                {
                    "level": issue.level.value,
                    "file": issue.file,
                    "line": issue.line,
                    "message": issue.message,
                    "context": issue.context
                }
                for issue in self.issues
            ],
            "summary": {
                "total": len(self.issues),
                "errors": sum(1 for i in self.issues if i.level == ValidationLevel.ERROR),
                "warnings": sum(1 for i in self.issues if i.level == ValidationLevel.WARNING)
            }
        }
        return json.dumps(data, indent=2)
    
    def _github_report(self) -> str:
        """Generate GitHub Actions annotations"""
        lines = []
        for issue in self.issues:
            level = "error" if issue.level == ValidationLevel.ERROR else "warning"
            location = f"file={issue.file}"
            if issue.line:
                location += f",line={issue.line}"
            lines.append(f"::{level} {location}::{issue.message}")
        return "\n".join(lines)
    
    def _markdown_report(self) -> str:
        """Generate Markdown report"""
        lines = ["# Validation Report\n"]
        
        if not self.issues:
            lines.append("✅ No validation issues found.")
            return "\n".join(lines)
        
        # Summary
        error_count = sum(1 for i in self.issues if i.level == ValidationLevel.ERROR)
        warning_count = sum(1 for i in self.issues if i.level == ValidationLevel.WARNING)
        lines.append(f"## Summary")
        lines.append(f"- **Errors:** {error_count}")
        lines.append(f"- **Warnings:** {warning_count}")
        lines.append("")
        
        # Issues by file
        by_file: Dict[str, List[ValidationIssue]] = {}
        for issue in self.issues:
            if issue.file not in by_file:
                by_file[issue.file] = []
            by_file[issue.file].append(issue)
        
        lines.append("## Issues\n")
        for file, file_issues in sorted(by_file.items()):
            lines.append(f"### {file}")
            for issue in sorted(file_issues, key=lambda x: x.line or 0):
                icon = "❌" if issue.level == ValidationLevel.ERROR else "⚠️"
                location = f"Line {issue.line}" if issue.line else "File"
                lines.append(f"- {icon} **{location}**: {issue.message}")
                if issue.context:
                    lines.append(f"  - Context: `{issue.context}`")
            lines.append("")
        
        return "\n".join(lines)
    
    def save_to_file(self, path: Path) -> None:
        """Save report to file"""
        with open(path, 'w') as f:
            f.write(self.generate_report())
    
    def has_errors(self) -> bool:
        """Check if any errors were found"""
        return any(i.level == ValidationLevel.ERROR for i in self.issues)
    
    def has_warnings(self) -> bool:
        """Check if any warnings were found"""
        return any(i.level == ValidationLevel.WARNING for i in self.issues)


# ============================================================================
# Output File Generation (Summary, Markdown, Warnings)
# ============================================================================

class OutputFileGenerator:
    """Generates summary, markdown, and warnings files for menu validation"""
    
    def __init__(self, recipes_dir: Path, config: ConfigManager):
        """Initialize output file generator
        
        Args:
            recipes_dir: Directory containing recipe files
            config: Configuration manager instance
        """
        self.recipes_dir = Path(recipes_dir).resolve()
        self.config = config
        self.command_validator = CommandValidator(config)
        self.state = InstrumentState()
        self.issues: List[ValidationIssue] = []
        
        # Data collection tracking
        self.darks: List[str] = []
        self.flats: List[str] = []
        self.coronal: List[str] = []
        self.coronal_exp: List[str] = []
        
        # File handles
        self.summary_file: Optional[TextIO] = None
        self.md_file: Optional[TextIO] = None
        
        # Tab indentation
        self.tab_space = '\t'
        
        # Initialize plotter if available
        try:
            self.plotter = TuningPlotter({}, None)
            self._load_tuning_configs()
        except Exception:
            self.plotter = None
    
    def _load_tuning_configs(self) -> None:
        """Load tuning configurations for plotting"""
        try:
            atlas = self._get_kitt_peak_atlas()
            tuning_configs = {}
            
            for tuning_config in glob.glob("../resource/*ini"):
                key = Path(tuning_config).name.split("_")[-1].split(".")[0]
                tuning_configs[key] = getFilterConfig(tuning_config)
                
                csv_files = glob.glob(f"../resource/{key}*.csv")
                if csv_files:
                    prefilter = np.loadtxt(csv_files[0], delimiter=",", skiprows=10)
                    tuning_configs[key]["prefilter"] = prefilter
            
            self.plotter = TuningPlotter(tuning_configs, atlas)
        except Exception as e:
            logging.debug(f"Could not load tuning configs: {e}")
    
    def _get_kitt_peak_atlas(self) -> np.ndarray:
        """Load Kitt Peak atlas data"""
        atlas = np.zeros([0, 3])
        for atlas_name in glob.glob("../resource/lm*"):
            try:
                atlas1 = np.loadtxt(atlas_name)
                atlas = np.concatenate((atlas, atlas1), axis=0)
            except Exception:
                pass
        return atlas
    
    def process_menu(self, menu_file: Path, generate_plots: bool = True) -> None:
        """Process a menu file and generate output files
        
        Args:
            menu_file: Path to menu file
            generate_plots: Whether to generate tuning plots
        """
        # Reset state
        self.state.reset()
        self.issues = []
        self.darks = []
        self.flats = []
        self.coronal = []
        self.coronal_exp = []
        
        # Check for NOWARNING flag
        with open(menu_file, 'r') as f:
            content = f.read()
            if "NOWARNING" in content:
                logging.info(f"Skipping {menu_file} due to NOWARNING flag")
                return
        
        # Open output files
        menu_name = menu_file.stem
        self.summary_file = open(f"{menu_name}.summary", 'w')
        self.md_file = open(f"{menu_name}.md", 'w')
        
        # Write markdown header
        icons_header = "  \n".join([f'{Icons.__dict__[key]} = {key.lower()}' 
                                   for key in ['DATA', 'FLAT', 'DARK', 'CALIB']])
        self.md_file.write(icons_header + "\n\n")
        
        # Process the menu file
        self._read_script(menu_file, str(menu_file), 0, ".cbk", generate_plots)
        
        # Close files
        self.summary_file.close()
        self.md_file.close()
        
        # Validate darks and flats completeness
        for corona in self.coronal_exp:
            if corona not in self.darks:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    file=str(menu_file),
                    message=f"Missing dark for {corona}"
                ))
        
        for corona in self.coronal:
            if corona not in self.flats:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    file=str(menu_file),
                    message=f"Missing flat for {corona}"
                ))
    
    def _read_script(self, script_path: Path, parent: str, tab: int, 
                    child_extension: str, generate_plots: bool) -> Tuple[float, float]:
        """Read and process a script file, generating output
        
        Args:
            script_path: Path to script file
            parent: Parent context for error reporting
            tab: Indentation level
            child_extension: Expected extension for child files
            generate_plots: Whether to generate tuning plots
            
        Returns:
            Tuple of (integration_time_ms, hardware_time_s)
        """
        # Reset collection tracking for top-level cookbooks
        if child_extension != ".rcp":
            self.coronal = []
            self.coronal_exp = []
        
        # Find file (case-insensitive)
        script_name = self._find_file(script_path)
        if not script_name:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                file=parent,
                message=f"File not found: {script_path}"
            ))
            return 0, 0
        
        # Read file
        with open(script_name, 'r') as f:
            results = f.readlines()
        
        # Unroll FOR loops if cookbook
        if ".cbk" in str(script_name):
            results2 = self._unroll_forloop(results)
        else:
            results2 = results
        
        # Write to summary
        self.summary_file.write(f" {tab*6*'-'} > {script_name.name}\n")
        
        run_time = 0.0
        hardware_time = 0.0
        
        # Determine icon for markdown
        emoji = self._get_icon_for_state(script_name.name)
        
        # Write markdown header
        self.md_file.write("<details><summary>")
        if emoji and generate_plots and self.plotter:
            self.md_file.write(emoji)
            self.md_file.write(f"[{script_name.name}](tuningplots/{script_name.name}.png)</summary><blockquote><pre>")
            # Generate plot
            try:
                self.plotter.read_and_plot_rcp(script_name, Path("tuningplots"))
            except Exception as e:
                logging.debug(f"Failed to generate plot: {e}")
        else:
            if emoji:
                self.md_file.write(emoji)
            self.md_file.write(f"{script_name.name}</summary><blockquote><pre>")
        
        tab += 1
        
        # Process each line
        for child in results2:
            filename = child.split('#')[0].strip()
            commands = child.split('#')[0].strip().lower().split()
            
            if len(commands) > 0 and commands[0].split(":")[0] not in self.config.ignore_commands:
                if child_extension in commands[0]:
                    # Recursive call for subscript
                    try:
                        t_time, h_time = self._read_script(
                            Path(filename), 
                            f"{parent},{commands[0]}", 
                            tab, 
                            ".rcp",
                            generate_plots
                        )
                        run_time += t_time
                        hardware_time += h_time
                    except Exception as e:
                        self.issues.append(ValidationIssue(
                            level=ValidationLevel.ERROR,
                            file=parent,
                            message=f"Failed to process {filename}: {e}"
                        ))
                else:
                    # Process command
                    timing = self._process_command_with_output(commands, parent, tab)
                    if timing:
                        run_time += timing[0]
                        hardware_time += timing[1]
        
        # Write timing info to markdown
        if "rcp" in child_extension:
            self.md_file.write(f"\nIntegration:{run_time/1000/60:.2f} minutes. ")
            self.md_file.write(f"Hardware:{hardware_time/60:.2f} minutes. ")
            self.md_file.write(f"total:{run_time/1000/60 + hardware_time/60:.2f} minutes  ")
        else:
            # Validate darks/flats for cookbooks
            for corona in self.coronal_exp:
                if corona not in self.darks:
                    self.issues.append(ValidationIssue(
                        level=ValidationLevel.WARNING,
                        file=parent,
                        message=f"Missing dark for {corona}"
                    ))
            
            for corona in self.coronal:
                if corona not in self.flats:
                    self.issues.append(ValidationIssue(
                        level=ValidationLevel.WARNING,
                        file=parent,
                        message=f"Missing flat for {corona}"
                    ))
        
        self.md_file.write("</pre></blockquote></details>")
        
        return run_time, hardware_time
    
    def _process_command_with_output(self, commands: List[str], parent: str, 
                                    tab: int) -> Optional[Tuple[float, float]]:
        """Process command and write to output files
        
        Args:
            commands: Command and arguments
            parent: Parent context
            tab: Indentation level
            
        Returns:
            Tuple of (integration_time_ms, hardware_time_s) if applicable
        """
        if not commands:
            return None
        
        command = commands[0]
        args = commands[1:] if len(commands) > 1 else []
        
        # Skip ignored commands
        if command in self.config.ignore_commands:
            return None
        
        # Validate command
        issue = self.command_validator.validate_command(command, args, parent)
        if issue:
            self.issues.append(issue)
            if issue.level == ValidationLevel.ERROR:
                return None
        
        run_time = 0.0
        hardware_time = 0.0
        emoji = None
        
        # Process command based on type
        if command == "gain" and args:
            self.state.update("gain", args[0])
            
        elif command == "shut" and args:
            self.state.update("shut", args[0])
            
        elif command == "exposure" and args:
            self.state.update("exposure", args[0])
            
        elif command == "cover" and args:
            if self.state.cover != args[0]:
                hardware_time += TimingConstants.COVER_TIME
            self.state.update("cover", args[0])
            
        elif command == "occ" and args:
            if self.state.occ != args[0]:
                hardware_time += TimingConstants.OCC_TIME
            self.state.update("occ", args[0])
            
        elif command == "prefilterrange" and args:
            if self.state.filter != args[0]:
                hardware_time += TimingConstants.PREFILTER_TIME
            self.state.update("filter", args[0])
            
        elif command == "calret" and args:
            if self.state.calret != args[0]:
                hardware_time += TimingConstants.ROTATE_TIME
            self.state.update("calret", args[0])
            
        elif command == "calpol" and args:
            if self.state.calpol != args[0]:
                hardware_time += TimingConstants.ROTATE_TIME
            self.state.update("calpol", args[0])
            
        elif command == "calib" and args:
            if self.state.calib != args[0]:
                hardware_time += TimingConstants.CALIB_TIME
            self.state.update("calib", args[0])
            
        elif command == "diffuser" and args:
            if self.state.diffuser != args[0]:
                hardware_time += TimingConstants.DIFFUSER_TIME
            self.state.update("diffuser", args[0])
            
        elif command == "data" and len(args) == 4:
            cam, cont, wave, sums = args
            
            # Determine data type and track
            if self.state.is_dark():
                emoji = Icons.DARK
                sig = self.state.exposure + self.state.gain + sums
                if sig not in self.darks:
                    self.darks.append(sig)
                    
            elif self.state.is_flat():
                emoji = Icons.FLAT
                sig = self.state.gain + sums + cam + cont + wave
                if sig not in self.flats:
                    self.flats.append(sig)
                    
            elif self.state.is_coronal():
                emoji = Icons.DATA
                self.coronal.append(self.state.gain + sums + cam + cont + wave)
                self.coronal_exp.append(self.state.exposure + self.state.gain + sums)
                
            elif self.state.is_calibration():
                emoji = Icons.CALIB
            
            # Calculate timing
            try:
                exp_time = float(self.state.exposure)
                num_sums = int(sums)
                readout = CameraConstants.READOUT_TIMES.get(self.state.gain, 10)
                run_time = (TimingConstants.RELAXATION_TIME + 
                           (exp_time + readout) * 4 * num_sums)
            except (ValueError, KeyError):
                pass
        
        # Write to summary
        self.summary_file.write(f"{tab*6*'-'}> {self.tab_space.join(commands)}\n")
        
        # Write to markdown with emoji if applicable
        if emoji and "_FW" not in command and "setup" not in command:
            self.md_file.write(emoji)
        self.md_file.write(self.tab_space.join(commands))
        self.md_file.write("\n &#xE0020;")
        
        return run_time, hardware_time
    
    def _get_icon_for_state(self, script_name: str) -> Optional[str]:
        """Determine appropriate icon based on instrument state
        
        Args:
            script_name: Name of the script
            
        Returns:
            Icon string or None
        """
        # Skip setup and configuration scripts
        skip_patterns = ["_FW", "_POL", "setup", "cbk", "menu", "_in", "_out"]
        if any(pattern in script_name for pattern in skip_patterns):
            return None
        
        if self.state.is_dark():
            return Icons.DARK
        elif self.state.is_flat():
            return Icons.FLAT
        elif self.state.is_coronal():
            return Icons.DATA
        elif self.state.is_calibration():
            return Icons.CALIB
        
        return None
    
    def _unroll_forloop(self, results: List[str]) -> List[str]:
        """Unroll FOR loops in cookbook files
        
        Args:
            results: Lines from cookbook file
            
        Returns:
            Lines with FOR loops expanded
        """
        results = [r.split('#')[0].lower().split() for r in results]
        results2 = []
        endline = 0
        
        for i in range(len(results)):
            if len(results[i]) > 0:
                if "for" == results[i][0]:
                    try:
                        for_count = int(results[i][1])
                        start_line = i + 1
                        
                        # Find matching ENDFOR
                        for next_line in range(len(results) - i):
                            if len(results[start_line + next_line]) > 0:
                                if "endfor" == results[start_line + next_line][0]:
                                    endline = start_line + next_line + 1
                                    break
                                    
                        # Expand loop
                        for _ in range(for_count):
                            for line_idx in range(start_line, endline - 1):
                                if len(results[line_idx]) > 0:
                                    results2.append(self.tab_space.join(results[line_idx]))
                                    
                    except (IndexError, ValueError) as e:
                        self.issues.append(ValidationIssue(
                            level=ValidationLevel.ERROR,
                            file="cookbook",
                            message=f"Invalid FOR loop: {' '.join(results[i])}"
                        ))
                else:
                    if i < endline:
                        pass
                    else:
                        results2.append(self.tab_space.join(results[i]))
        
        return results2
    
    def _find_file(self, file_path: Union[Path, str]) -> Optional[Path]:
        """Find file with case-insensitive matching
        
        Args:
            file_path: Path or name of file to find
            
        Returns:
            Path to file if found, None otherwise
        """
        file_name = Path(file_path).name
        
        # Try exact match first
        if Path(file_path).exists():
            return Path(file_path)
        
        # Try case-insensitive match
        for file in Path('.').iterdir():
            if file.name.lower() == file_name.lower():
                return file
        
        return None
    
    def get_issues(self) -> List[ValidationIssue]:
        """Get all validation issues found
        
        Returns:
            List of validation issues
        """
        return self.issues




# ============================================================================
# Command-Line Interface
# ============================================================================

def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser
    
    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        description='UCoMP Recipe/Cookbook Validator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Validate all files in Recipes/
  %(prog)s daily.menu              # Validate specific file
  %(prog)s --format json           # Output as JSON
  %(prog)s --verbose              # Show detailed logging
  %(prog)s --no-plots            # Skip plot generation
  %(prog)s --output report.txt   # Save report to file
        """
    )
    
    parser.add_argument(
        'files',
        nargs='*',
        help='Specific files to validate (default: all *.menu files)'
    )
    
    parser.add_argument(
        '--recipes-dir',
        type=Path,
        default=Path('Recipes'),
        help='Directory containing recipe files (default: Recipes/)'
    )
    
    parser.add_argument(
        '--config',
        type=Path,
        help='Path to YAML configuration file'
    )
    
    parser.add_argument(
        '--format',
        choices=['text', 'json', 'github', 'markdown'],
        default='text',
        help='Output format (default: text)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=Path,
        help='Output file (default: stdout)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress non-error output'
    )
    
    parser.add_argument(
        '--no-plots',
        action='store_true',
        help='Skip generating tuning plots'
    )
    
    parser.add_argument(
        '--no-summary',
        action='store_true',
        help='Skip generating summary files'
    )
    
    parser.add_argument(
        '--fail-on-warning',
        action='store_true',
        help='Exit with error code if warnings are found'
    )
    
    return parser


def setup_logging(verbose: bool, quiet: bool) -> None:
    """Configure logging based on verbosity settings
    
    Args:
        verbose: Enable verbose logging
        quiet: Suppress non-error output
    """
    if quiet:
        level = logging.ERROR
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s'
    )


def main() -> int:
    """Main entry point for command-line usage
    
    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    parser = create_parser()
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose, args.quiet)
    
    # Change to recipes directory if it exists
    if args.recipes_dir.exists():
        os.chdir(args.recipes_dir)
    else:
        logging.error(f"Recipes directory not found: {args.recipes_dir}")
        return 1
    
    # Load configuration
    config = ConfigManager(args.config)
    
    # Initialize validator for non-menu files
    validator = ScriptValidator(Path('.'), config)
    
    # Determine files to validate
    if args.files:
        files_to_validate = [Path(f) for f in args.files]
    else:
        # Default to all menu files
        files_to_validate = list(Path('.').glob('*.menu'))
    
    if not files_to_validate:
        logging.warning("No files to validate")
        return 0
    
    # Initialize reporter
    reporter = ValidationReporter(args.format)
    
    # Open warnings file (always created unless output is specified)
    warnings_file = None
    if not args.output:
        warnings_file = open('warnings.txt', 'w')
    
    # Validate each file
    all_issues = []
    for file_path in files_to_validate:
        if not file_path.exists():
            logging.error(f"File not found: {file_path}")
            continue
        
        logging.info(f"Validating {file_path}")
        
        # For menu files, generate summary and markdown
        if file_path.suffix == '.menu' and not args.no_summary:
            generator = OutputFileGenerator(Path('.'), config)
            generator.process_menu(file_path, generate_plots=not args.no_plots)
            issues = generator.get_issues()
        else:
            # Determine file type and validate
            if file_path.suffix == '.menu':
                # Menu without summary generation
                issues = validator.validate_menu(file_path)
            elif file_path.suffix == '.cbk':
                issues = validator.validate_cookbook(file_path)
            elif file_path.suffix == '.rcp':
                issues = validator.validate_recipe(file_path)
            else:
                logging.warning(f"Unknown file type: {file_path}")
                continue
        
        all_issues.extend(issues)
        
        # Write issues to warnings file
        if warnings_file:
            for issue in issues:
                warnings_file.write(f"{issue}\n")
    
    # Close warnings file
    if warnings_file:
        warnings_file.close()
        if not args.quiet:
            print(f"Warnings written to warnings.txt")
    
    # Add all issues to reporter
    reporter.add_issues(all_issues)
    
    # Output report
    if args.output:
        reporter.save_to_file(args.output)
        if not args.quiet:
            print(f"Report saved to {args.output}")
    else:
        # Print report to stdout if not using default warnings.txt
        if args.format != 'text' or args.verbose:
            print(reporter.generate_report())
    
    # Determine exit code
    if reporter.has_errors():
        return 1
    elif args.fail_on_warning and reporter.has_warnings():
        return 1
    else:
        return 0


if __name__ == '__main__':
    sys.exit(main())