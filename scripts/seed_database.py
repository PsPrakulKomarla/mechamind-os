#!/usr/bin/env python3
"""
Database seeding script for Mechamind OS.
Pre-populates the equipment catalog with common industrial equipment,
their known problems, and standard solutions.
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.db.models import (
    Equipment, EquipmentIssue, ProblemSolution,
    EquipmentCategory, EquipmentCriticality, EquipmentStatus,
    ProblemSource, SolutionSource
)
from app.config import settings


# Equipment catalog data
EQUIPMENT_DATA = [
    {
        "name": "Centrifugal Pump P-101",
        "tag_number": "P-101",
        "category": EquipmentCategory.PUMP,
        "criticality": EquipmentCriticality.CRITICAL,
        "location": "Boiler Feedwater Area",
        "area": "Unit 1 - Power Block",
        "building": "Turbine Building",
        "floor": "Ground Floor",
        "manufacturer": "KSB",
        "model": "WKLN 150/5",
        "serial_number": "KSB-2023-04567",
        "specifications": {
            "flow_rate_m3h": 450,
            "head_m": 180,
            "power_kw": 315,
            "speed_rpm": 2980,
            "suction_size_mm": 200,
            "discharge_size_mm": 150,
            "material": "Cast Iron / SS316",
        },
        "operating_parameters": {
            "normal_flow_m3h": 420,
            "normal_discharge_pressure_barg": 16.5,
            "normal_suction_pressure_barg": 2.5,
            "normal_vibration_mm_s": 2.5,
            "normal_bearing_temp_c": 65,
            "normal_motor_current_a": 480,
        },
        "description": "Boiler feedwater pump supplying high-pressure water to steam generator",
        "p_and_id_reference": "PID-101-PFW-001",
        "installation_date": datetime(2023, 3, 15),
        "last_maintenance_date": datetime(2024, 11, 10),
        "next_maintenance_date": datetime(2025, 2, 10),
    },
    {
        "name": "Centrifugal Pump P-102",
        "tag_number": "P-102",
        "category": EquipmentCategory.PUMP,
        "criticality": EquipmentCriticality.CRITICAL,
        "location": "Boiler Feedwater Area",
        "area": "Unit 1 - Power Block",
        "building": "Turbine Building",
        "floor": "Ground Floor",
        "manufacturer": "KSB",
        "model": "WKLN 150/5",
        "serial_number": "KSB-2023-04568",
        "specifications": {
            "flow_rate_m3h": 450,
            "head_m": 180,
            "power_kw": 315,
            "speed_rpm": 2980,
            "suction_size_mm": 200,
            "discharge_size_mm": 150,
            "material": "Cast Iron / SS316",
        },
        "operating_parameters": {
            "normal_flow_m3h": 420,
            "normal_discharge_pressure_barg": 16.5,
            "normal_suction_pressure_barg": 2.5,
            "normal_vibration_mm_s": 2.5,
            "normal_bearing_temp_c": 65,
            "normal_motor_current_a": 480,
        },
        "description": "Standby boiler feedwater pump",
        "p_and_id_reference": "PID-101-PFW-001",
        "installation_date": datetime(2023, 3, 15),
        "last_maintenance_date": datetime(2024, 10, 20),
        "next_maintenance_date": datetime(2025, 1, 20),
    },
    {
        "name": "Induced Draft Fan IDF-201",
        "tag_number": "IDF-201",
        "category": EquipmentCategory.OTHER,  # Fan/Blower
        "criticality": EquipmentCriticality.CRITICAL,
        "location": "Boiler Area",
        "area": "Unit 1 - Power Block",
        "building": "Boiler Building",
        "floor": "3rd Floor",
        "manufacturer": "Howden",
        "model": "BVF 45/28",
        "serial_number": "HWD-2022-11234",
        "specifications": {
            "flow_rate_m3s": 45,
            "static_pressure_pa": 1200,
            "power_kw": 800,
            "speed_rpm": 1485,
            "blade_material": "SA240 Type 316",
            "casing_material": "Carbon Steel",
        },
        "operating_parameters": {
            "normal_flow_m3s": 42,
            "normal_vibration_mm_s": 3.0,
            "normal_bearing_temp_c": 70,
            "normal_motor_current_a": 1250,
            "normal_outlet_temp_c": 140,
        },
        "description": "Induced draft fan for boiler flue gas extraction",
        "p_and_id_reference": "PID-201-FGD-001",
        "installation_date": datetime(2022, 8, 10),
        "last_maintenance_date": datetime(2024, 11, 5),
        "next_maintenance_date": datetime(2025, 2, 5),
    },
    {
        "name": "Steam Turbine TG-301",
        "tag_number": "TG-301",
        "category": EquipmentCategory.TURBINE,
        "criticality": EquipmentCriticality.CRITICAL,
        "location": "Turbine Hall",
        "area": "Unit 1 - Power Block",
        "building": "Turbine Building",
        "floor": "Ground Floor",
        "manufacturer": "Siemens",
        "model": "SST-6000",
        "serial_number": "SIE-2022-09876",
        "specifications": {
            "rated_power_mw": 300,
            "throttle_pressure_barg": 165,
            "throttle_temp_c": 540,
            "reheat_pressure_barg": 38,
            "reheat_temp_c": 540,
            "condenser_pressure_bara": 0.05,
            "speed_rpm": 3000,
        },
        "operating_parameters": {
            "normal_load_mw": 285,
            "normal_vibration_um": 50,
            "normal_bearing_temp_c": 85,
            "normal_lube_oil_temp_c": 45,
            "normal_lube_oil_pressure_barg": 1.5,
        },
        "description": "300MW condensing steam turbine generator",
        "p_and_id_reference": "PID-301-STM-001",
        "installation_date": datetime(2022, 12, 1),
        "last_maintenance_date": datetime(2024, 6, 15),
        "next_maintenance_date": datetime(2025, 6, 15),
    },
    {
        "name": "Air Compressor C-401",
        "tag_number": "C-401",
        "category": EquipmentCategory.COMPRESSOR,
        "criticality": EquipmentCriticality.MAJOR,
        "location": "Instrument Air Station",
        "area": "Utilities",
        "building": "Compressor House",
        "floor": "Ground Floor",
        "manufacturer": "Atlas Copco",
        "model": "GA 160 VSD",
        "serial_number": "ACP-2023-03456",
        "specifications": {
            "free_air_delivery_m3min": 28,
            "working_pressure_barg": 7.5,
            "power_kw": 160,
            "speed_rpm": 2960,
            "cooling": "Air cooled",
            "drive_type": "VSD",
        },
        "operating_parameters": {
            "normal_pressure_barg": 7.0,
            "normal_outlet_temp_c": 45,
            "normal_oil_level": "Mid sight glass",
            "normal_vibration_mm_s": 2.0,
        },
        "description": "Variable speed drive rotary screw compressor for instrument air",
        "p_and_id_reference": "PID-401-IAS-001",
        "installation_date": datetime(2023, 1, 20),
        "last_maintenance_date": datetime(2024, 11, 1),
        "next_maintenance_date": datetime(2025, 2, 1),
    },
    {
        "name": "Shell & Tube Heat Exchanger HE-501",
        "tag_number": "HE-501",
        "category": EquipmentCategory.HEAT_EXCHANGER,
        "criticality": EquipmentCriticality.MAJOR,
        "location": "Condensate Polishing Area",
        "area": "Unit 1 - Power Block",
        "building": "Turbine Building",
        "floor": "Mezzanine",
        "manufacturer": "Alfa Laval",
        "model": "T100-BFG",
        "serial_number": "ALV-2022-07890",
        "specifications": {
            "type": "Shell and Tube",
            "tube_material": "Titanium Gr2",
            "shell_material": "Carbon Steel",
            "heat_transfer_area_m2": 850,
            "design_pressure_tube_barg": 10,
            "design_pressure_shell_barg": 16,
            "design_temp_c": 200,
        },
        "operating_parameters": {
            "tube_side_flow_kg_s": 120,
            "shell_side_flow_kg_s": 150,
            "tube_inlet_temp_c": 40,
            "tube_outlet_temp_c": 110,
            "shell_inlet_temp_c": 130,
            "shell_outlet_temp_c": 85,
            "normal_pressure_drop_tube_barg": 0.5,
        },
        "description": "Condensate preheater using LP steam",
        "p_and_id_reference": "PID-501-CDP-001",
        "installation_date": datetime(2022, 9, 5),
        "last_maintenance_date": datetime(2024, 8, 20),
        "next_maintenance_date": datetime(2025, 8, 20),
    },
    {
        "name": "Water Tube Boiler B-601",
        "tag_number": "B-601",
        "category": EquipmentCategory.BOILER,
        "criticality": EquipmentCriticality.CRITICAL,
        "location": "Boiler Area",
        "area": "Unit 1 - Power Block",
        "building": "Boiler Building",
        "floor": "Multiple",
        "manufacturer": "BHEL",
        "model": "500 MW Subcritical",
        "serial_number": "BHL-2021-00123",
        "specifications": {
            "steam_capacity_tph": 1500,
            "design_pressure_barg": 170,
            "design_temp_c": 540,
            "fuel_type": "Pulverized Coal",
            "furnace_type": "Tangential Firing",
            "burner_count": 24,
        },
        "operating_parameters": {
            "normal_steam_flow_tph": 1450,
            "normal_drum_pressure_barg": 165,
            "normal_drum_level_mm": 0,
            "normal_furnace_pressure_mmwc": -5,
            "normal_o2_percent": 3.5,
            "normal_co_ppm": 50,
        },
        "description": "500MW coal-fired utility boiler with tangential firing",
        "p_and_id_reference": "PID-601-BLR-001",
        "installation_date": datetime(2021, 6, 1),
        "last_maintenance_date": datetime(2024, 4, 1),
        "next_maintenance_date": datetime(2025, 4, 1),
    },
    {
        "name": "Belt Conveyor CV-701",
        "tag_number": "CV-701",
        "category": EquipmentCategory.CONVEYOR,
        "criticality": EquipmentCriticality.MAJOR,
        "location": "Coal Handling Plant",
        "area": "Fuel Handling",
        "building": "Conveyor Gallery A",
        "floor": "Ground to 2nd Floor",
        "manufacturer": "TRF Limited",
        "model": "TC-1400-250",
        "serial_number": "TRF-2022-05678",
        "specifications": {
            "belt_width_mm": 1400,
            "capacity_tph": 1200,
            "speed_m_s": 2.5,
            "length_m": 850,
            "lift_m": 45,
            "motor_power_kw": 250,
            "belt_type": "Steel Cord ST2500",
        },
        "operating_parameters": {
            "normal_load_tph": 1000,
            "normal_belt_tension_kn": 180,
            "normal_motor_current_a": 380,
            "normal_gearbox_oil_temp_c": 70,
        },
        "description": "Main coal conveyor from crusher house to boiler bunkers",
        "p_and_id_reference": "PID-701-CHP-001",
        "installation_date": datetime(2022, 4, 15),
        "last_maintenance_date": datetime(2024, 11, 15),
        "next_maintenance_date": datetime(2025, 2, 15),
    },
    {
        "name": "Motor Operated Valve MOV-801",
        "tag_number": "MOV-801",
        "category": EquipmentCategory.VALVE,
        "criticality": EquipmentCriticality.CRITICAL,
        "location": "Main Steam Line",
        "area": "Unit 1 - Power Block",
        "building": "Turbine Building",
        "floor": "2nd Floor",
        "manufacturer": "Flowserve",
        "model": "Mark One 8\" 900#",
        "serial_number": "FLS-2022-04321",
        "specifications": {
            "size_inch": 8,
            "rating_class": 900,
            "body_material": "A216 WCC",
            "trim_material": "Stellite 6 / 410 SS",
            "actuator_type": "Electric Modulating",
            "actuator_model": "Limitorque SMB-00",
            "fail_position": "As-is",
        },
        "operating_parameters": {
            "normal_position_percent": 100,
            "stroke_time_sec": 45,
            "normal_thrust_kn": 45,
        },
        "description": "Main steam isolation valve - turbine trip valve",
        "p_and_id_reference": "PID-801-MST-001",
        "installation_date": datetime(2022, 11, 10),
        "last_maintenance_date": datetime(2024, 10, 1),
        "next_maintenance_date": datetime(2025, 4, 1),
    },
    {
        "name": "Generator GEN-301",
        "tag_number": "GEN-301",
        "category": EquipmentCategory.GENERATOR,
        "criticality": EquipmentCriticality.CRITICAL,
        "location": "Turbine Hall",
        "area": "Unit 1 - Power Block",
        "building": "Turbine Building",
        "floor": "Ground Floor",
        "manufacturer": "Siemens",
        "model": "Topaz 300MW",
        "serial_number": "SIE-2022-09877",
        "specifications": {
            "rated_mva": 360,
            "rated_voltage_kv": 21,
            "power_factor": 0.85,
            "frequency_hz": 50,
            "speed_rpm": 3000,
            "cooling": "Hydrogen inner, Water stator",
            "excitation": "Brushless",
        },
        "operating_parameters": {
            "normal_mw": 285,
            "normal_mvar": 80,
            "normal_h2_pressure_barg": 4.5,
            "normal_stator_winding_temp_c": 95,
            "normal_rotor_winding_temp_c": 85,
            "normal_bearing_temp_c": 70,
        },
        "description": "300MW hydrogen-cooled synchronous generator",
        "p_and_id_reference": "PID-301-GEN-001",
        "installation_date": datetime(2022, 12, 1),
        "last_maintenance_date": datetime(2024, 6, 15),
        "next_maintenance_date": datetime(2025, 12, 15),
    },
    {
        "name": "Transformer TRF-901",
        "tag_number": "TRF-901",
        "category": EquipmentCategory.TRANSFORMER,
        "criticality": EquipmentCriticality.CRITICAL,
        "location": "Switchyard",
        "area": "Electrical",
        "building": "Outdoor",
        "floor": "Ground",
        "manufacturer": "CGL",
        "model": "315 MVA 400/21 kV",
        "serial_number": "CGL-2022-01234",
        "specifications": {
            "rating_mva": 315,
            "hv_voltage_kv": 400,
            "lv_voltage_kv": 21,
            "vector_group": "YNd11",
            "impedance_percent": 14.5,
            "cooling": "ONAN/ONAF",
            "tap_changer": "OLTC ±10%",
        },
        "operating_parameters": {
            "normal_load_mva": 280,
            "normal_oil_temp_c": 55,
            "normal_winding_temp_c": 65,
            "normal_oil_level": "Mid gauge",
        },
        "description": "Generator step-up transformer 400/21 kV",
        "p_and_id_reference": "SLD-901-SWT-001",
        "installation_date": datetime(2022, 5, 1),
        "last_maintenance_date": datetime(2024, 3, 1),
        "next_maintenance_date": datetime(2025, 3, 1),
    },
]

# Known issues per equipment category
ISSUES_BY_CATEGORY = {
    EquipmentCategory.PUMP: [
        {
            "issue_name": "High Vibration at 1X RPM",
            "description": "Vibration amplitude exceeds 4.5 mm/s at running speed",
            "symptoms": ["Increasing vibration trend", "Bearing temperature rise", "Noise increase"],
            "root_causes": ["Rotor unbalance", "Coupling misalignment", "Bent shaft", "Foundation looseness"],
            "severity": 8,
            "frequency": "occasional",
            "detection_method": "Vibration monitoring (weekly)",
            "prevention": "Precision alignment, dynamic balancing, foundation grout inspection",
            "typical_solution": "In-place balancing or coupling realignment",
            "estimated_downtime_hours": 8,
            "estimated_cost": 15000,
            "regulatory_impact": False,
            "safety_impact": False,
        },
        {
            "issue_name": "Mechanical Seal Leakage",
            "description": "Visible leakage from mechanical seal assembly",
            "symptoms": ["Water dripping", "Seal chamber pressure drop", "Glycol contamination"],
            "root_causes": ["Seal face wear", "Dry running", "Chemical attack", "Improper installation"],
            "severity": 7,
            "frequency": "frequent",
            "detection_method": "Visual inspection, seal leak detector",
            "prevention": "Seal flush plan maintenance, proper startup procedure",
            "typical_solution": "Replace mechanical seal, inspect seal faces",
            "estimated_downtime_hours": 6,
            "estimated_cost": 25000,
            "regulatory_impact": False,
            "safety_impact": True,
        },
        {
            "issue_name": "Cavitation",
            "description": "Vapor bubble formation and collapse causing impeller damage",
            "symptoms": ["Cracking noise", "Vibration increase", "Performance drop", "Impeller pitting"],
            "root_causes": ["Low NPSHa", "High suction temperature", "Clogged strainer", "Vortex formation"],
            "severity": 9,
            "frequency": "occasional",
            "detection_method": "Sound, vibration, performance curves",
            "prevention": "Maintain NPSH margin, clean strainers, proper tank levels",
            "typical_solution": "Increase suction pressure, reduce temperature, replace impeller",
            "estimated_downtime_hours": 24,
            "estimated_cost": 80000,
            "regulatory_impact": False,
            "safety_impact": False,
        },
        {
            "issue_name": "Bearing Failure",
            "description": "Anti-friction bearing degradation leading to failure",
            "symptoms": ["Temperature rise", "Vibration at bearing frequencies", "Oil contamination"],
            "root_causes": ["Lubrication failure", "Contamination", "Misalignment", "Overload", "Fatigue"],
            "severity": 9,
            "frequency": "rare",
            "detection_method": "Vibration analysis, oil analysis, temperature monitoring",
            "prevention": "Oil analysis program, proper lubrication, alignment checks",
            "typical_solution": "Replace bearings, inspect shaft, check alignment",
            "estimated_downtime_hours": 16,
            "estimated_cost": 45000,
            "regulatory_impact": False,
            "safety_impact": True,
        },
    ],
    EquipmentCategory.FAN: [
        {
            "issue_name": "Blade Fatigue Cracking",
            "description": "Cracks on fan blades due to cyclic loading",
            "symptoms": ["Vibration increase", "Visible cracks", "Noise change"],
            "root_causes": ["Resonance", "Erosion", "Material defect", "Over-speed events"],
            "severity": 9,
            "frequency": "occasional",
            "detection_method": "Visual inspection, vibration analysis, NDT",
            "prevention": "Avoid resonance, erosion protection, regular NDT",
            "typical_solution": "Blade replacement or repair welding",
            "estimated_downtime_hours": 48,
            "estimated_cost": 120000,
            "regulatory_impact": False,
            "safety_impact": True,
        },
        {
            "issue_name": "Bearing Oil Contamination",
            "description": "Lubricating oil contaminated with process gas/particles",
            "symptoms": ["Oil discoloration", "Bearing temperature rise", "Vibration change"],
            "root_causes": ["Seal failure", "Breather clogging", "Improper oil grade"],
            "severity": 6,
            "frequency": "frequent",
            "detection_method": "Oil analysis (monthly), visual inspection",
            "prevention": "Seal maintenance, breather cleaning, correct oil specification",
            "typical_solution": "Oil flush and replacement, seal replacement",
            "estimated_downtime_hours": 4,
            "estimated_cost": 8000,
            "regulatory_impact": False,
            "safety_impact": False,
        },
    ],
    EquipmentCategory.TURBINE: [
        {
            "issue_name": "Rotor Unbalance",
            "description": "Mass distribution asymmetry causing synchronous vibration",
            "symptoms": ["High 1X vibration", "Bearing temperature rise", "Steady increase over time"],
            "root_causes": ["Blade deposition", "Blade loss", "Thermal bow", "Seal rub"],
            "severity": 8,
            "frequency": "occasional",
            "detection_method": "Continuous vibration monitoring, startup/shutdown analysis",
            "prevention": "Online water washing, proper warm-up/cool-down",
            "typical_solution": "Low-speed balancing or high-speed balancing",
            "estimated_downtime_hours": 24,
            "estimated_cost": 200000,
            "regulatory_impact": False,
            "safety_impact": True,
        },
        {
            "issue_name": "Thrust Bearing Wear",
            "description": "Excessive axial clearance in thrust bearing",
            "symptoms": ["High axial vibration", "Rotor position shift", "Oil temperature rise"],
            "root_causes": ["Oil contamination", "Overload", "Misalignment", "Design margin exceeded"],
            "severity": 9,
            "frequency": "rare",
            "detection_method": "Axial position monitoring, oil analysis, vibration",
            "prevention": "Oil cleanliness, load management, alignment",
            "typical_solution": "Replace thrust bearing pads, check alignment",
            "estimated_downtime_hours": 72,
            "estimated_cost": 500000,
            "regulatory_impact": False,
            "safety_impact": True,
        },
    ],
    EquipmentCategory.COMPRESSOR: [
        {
            "issue_name": "Surge Condition",
            "description": "Flow reversal causing severe vibration and damage",
            "symptoms": ["Loud bang noise", "Pressure fluctuation", "Temperature spike", "High vibration"],
            "root_causes": ["Low flow operation", "Anti-surge valve failure", "Control system issue"],
            "severity": 10,
            "frequency": "occasional",
            "detection_method": "Surge detector, pressure/flow monitoring",
            "prevention": "Anti-surge control, minimum flow recycle, operator training",
            "typical_solution": "Emergency shutdown, inspect impeller and bearings",
            "estimated_downtime_hours": 48,
            "estimated_cost": 150000,
            "regulatory_impact": True,
            "safety_impact": True,
        },
        {
            "issue_name": "Oil Carryover",
            "description": "Compressed air contaminated with lubricating oil",
            "symptoms": ["Downstream filter loading", "Instrument malfunction", "Oil in receivers"],
            "root_causes": ["Separator element failure", "High oil level", "Wrong oil viscosity"],
            "severity": 6,
            "frequency": "frequent",
            "detection_method": "Oil carryover test, differential pressure monitoring",
            "prevention": "Regular separator change, oil level monitoring, correct oil",
            "typical_solution": "Replace separator element, clean downstream filters",
            "estimated_downtime_hours": 2,
            "estimated_cost": 5000,
            "regulatory_impact": False,
            "safety_impact": False,
        },
    ],
    EquipmentCategory.HEAT_EXCHANGER: [
        {
            "issue_name": "Tube Fouling/Scaling",
            "description": "Deposit buildup reducing heat transfer efficiency",
            "symptoms": ["Reduced outlet temperature", "Increased pressure drop", "Higher energy consumption"],
            "root_causes": ["Water quality issues", "Temperature excursion", "Chemical treatment failure"],
            "severity": 6,
            "frequency": "frequent",
            "detection_method": "Performance monitoring, pressure drop tracking",
            "prevention": "Water treatment, regular cleaning schedule",
            "typical_solution": "Chemical cleaning or mechanical cleaning",
            "estimated_downtime_hours": 12,
            "estimated_cost": 30000,
            "regulatory_impact": False,
            "safety_impact": False,
        },
        {
            "issue_name": "Tube Leak",
            "description": "Tube-to-tubesheet joint or tube body leak",
            "symptoms": ["Cross-contamination", "Level changes", "Conductivity changes"],
            "root_causes": ["Thermal cycling", "Vibration", "Corrosion", "Erosion", "Manufacturing defect"],
            "severity": 8,
            "frequency": "occasional",
            "detection_method": "Helium leak test, pressure test, conductivity monitoring",
            "prevention": "Proper thermal cycling, vibration dampening, material selection",
            "typical_solution": "Plug leaking tubes or retube",
            "estimated_downtime_hours": 24,
            "estimated_cost": 75000,
            "regulatory_impact": True,
            "safety_impact": False,
        },
    ],
    EquipmentCategory.BOILER: [
        {
            "issue_name": "Water Wall Tube Leak",
            "description": "Leak in furnace water wall tubes",
            "symptoms": ["Drum level drop", "Furnace pressure loss", "Steam flow/feedwater flow mismatch", "Visible steam"],
            "root_causes": ["Overheating (departure from nucleate boiling)", "Corrosion fatigue", "Erosion", "Weld defect"],
            "severity": 10,
            "frequency": "occasional",
            "detection_method": "Flame scanner, acoustic leak detection, drum level monitoring",
            "prevention": "Water treatment, sootblowing management, combustion optimization",
            "typical_solution": "Emergency shutdown, tube replacement or pad welding",
            "estimated_downtime_hours": 12,
            "estimated_cost": 100000,
            "regulatory_impact": True,
            "safety_impact": True,
        },
        {
            "issue_name": "Superheater Tube Overheating",
            "description": "Tube metal temperature exceeding design limits",
            "symptoms": ["Steam temperature deviation", "Metal temperature thermocouple alarms", "Creep damage"],
            "root_causes": ["Flame impingement", "Soot buildup", "Improper burner tilt", "Coal quality variation"],
            "severity": 9,
            "frequency": "occasional",
            "detection_method": "Metal temperature monitoring, steam temperature monitoring",
            "prevention": "Sootblowing optimization, burner management, coal quality monitoring",
            "typical_solution": "Adjust combustion, increase sootblowing, tube replacement if crept",
            "estimated_downtime_hours": 48,
            "estimated_cost": 200000,
            "regulatory_impact": True,
            "safety_impact": True,
        },
    ],
    EquipmentCategory.CONVEYOR: [
        {
            "issue_name": "Belt Misalignment",
            "description": "Belt running off center causing edge damage and spillage",
            "symptoms": ["Belt edge wear", "Material spillage", "Belt tracking switch activation"],
            "root_causes": ["Idler misalignment", "Uneven loading", "Belt splice error", "Structural settlement"],
            "severity": 5,
            "frequency": "frequent",
            "detection_method": "Belt tracking sensors, visual inspection, spillage observation",
            "prevention": "Idler alignment program, loading chute design, training idlers",
            "typical_solution": "Realign idlers, adjust training idlers, check loading",
            "estimated_downtime_hours": 2,
            "estimated_cost": 3000,
            "regulatory_impact": False,
            "safety_impact": False,
        },
        {
            "issue_name": "Carrying Roller Bearing Failure",
            "description": "Idler roller bearing seizure causing belt damage",
            "symptoms": ["Roller not rotating", "Belt bottom cover wear", "Noise", "Vibration"],
            "root_causes": ["Contamination", "Lubrication failure", "Overload", "Seal failure"],
            "severity": 6,
            "frequency": "frequent",
            "detection_method": "Walk-down inspection, thermal imaging, acoustic monitoring",
            "prevention": "Sealed for life rollers, regular inspection, proper specification",
            "typical_solution": "Replace failed rollers",
            "estimated_downtime_hours": 1,
            "estimated_cost": 2000,
            "regulatory_impact": False,
            "safety_impact": False,
        },
    ],
    EquipmentCategory.VALVE: [
        {
            "issue_name": "Seat Leakage (Class IV/V)",
            "description": "Valve fails to achieve required shutoff class",
            "symptoms": ["Downstream pressure rise", "Process fluid loss", "Safety system activation"],
            "root_causes": ["Seat erosion", "Particle entrapment", "Thermal deformation", "Actuator thrust loss"],
            "severity": 7,
            "frequency": "occasional",
            "detection_method": "Leak testing, ultrasonic testing, downstream monitoring",
            "prevention": "Regular stroke testing, filtration, proper sizing",
            "typical_solution": "Lap seats, replace trim, increase actuator thrust",
            "estimated_downtime_hours": 8,
            "estimated_cost": 15000,
            "regulatory_impact": True,
            "safety_impact": True,
        },
        {
            "issue_name": "Actuator Failure",
            "description": "Electric/hydraulic/pneumatic actuator fails to operate",
            "symptoms": ["Valve not responding", "Position feedback error", "Torque/force limit trip"],
            "root_causes": ["Motor burnout", "Gear wear", "Limit switch failure", "Control card failure", "Air supply loss"],
            "severity": 8,
            "frequency": "occasional",
            "detection_method": "Partial stroke testing, position monitoring, torque monitoring",
            "prevention": "PST program, preventive maintenance, spare parts",
            "typical_solution": "Replace actuator or components",
            "estimated_downtime_hours": 4,
            "estimated_cost": 25000,
            "regulatory_impact": True,
            "safety_impact": True,
        },
    ],
    EquipmentCategory.GENERATOR: [
        {
            "issue_name": "Stator Winding Insulation Degradation",
            "description": "Insulation resistance decline due to thermal/aging effects",
            "symptoms": ["Low IR/Pi values", "Partial discharge increase", "Tan delta increase"],
            "root_causes": ["Thermal aging", "Moisture ingress", "Contamination", "Mechanical stress"],
            "severity": 9,
            "frequency": "rare",
            "detection_method": "IR/PI testing, partial discharge monitoring, tan delta, online monitoring",
            "prevention": "Temperature control, moisture prevention, regular testing",
            "typical_solution": "Rewedge, VPI treatment, or rewind",
            "estimated_downtime_hours": 720,
            "estimated_cost": 2000000,
            "regulatory_impact": True,
            "safety_impact": True,
        },
    ],
    EquipmentCategory.TRANSFORMER: [
        {
            "issue_name": "OLTC Contact Wear",
            "description": "On-load tap changer contacts worn causing high resistance",
            "symptoms": ["High contact resistance", "DGA showing arcing gases", "Tap position discrepancy"],
            "root_causes": ["Normal wear", "Frequent tap changes", "Contact pressure loss", "Contamination"],
            "severity": 7,
            "frequency": "occasional",
            "detection_method": "DGA, dynamic resistance measurement (DRM), tap position monitoring",
            "prevention": "Regular DRM, minimize unnecessary tap changes, maintenance schedule",
            "typical_solution": "OLTC overhaul, contact replacement",
            "estimated_downtime_hours": 48,
            "estimated_cost": 100000,
            "regulatory_impact": True,
            "safety_impact": True,
        },
    ],
}

# Standard solutions for common problems
STANDARD_SOLUTIONS = {
    "pump_vibration": {
        "problem": "High vibration on centrifugal pump",
        "solution": "1. Verify vibration spectrum - identify 1X, 2X, subsynchronous\n2. Check alignment (dial indicator or laser)\n3. Check foundation bolts and grout condition\n4. Perform in-place balancing if 1X dominant\n5. Inspect coupling for wear\n6. Verify bearing condition via vibration and temperature\n7. Document baseline after correction",
        "tools": ["Laser alignment tool", "Vibration analyzer", "Dial indicators", "Feeler gauges"],
        "parts": ["Shims", "Coupling elements (if needed)"],
        "time_hours": 8,
        "cost": 15000,
        "safety": "LOTO pump and motor. Verify zero energy. Use proper PPE.",
    },
    "pump_seal_leak": {
        "problem": "Mechanical seal leakage on pump",
        "solution": "1. Identify leak source (atmospheric vs. process side)\n2. Check seal flush/quench flow and pressure\n3. Verify seal chamber pressure and temperature\n4. Remove seal assembly\n5. Inspect seal faces for wear, cracks, heat checks\n6. Check sleeve/shaft for grooves or corrosion\n7. Replace seal with correct materials for service\n8. Reassemble with proper face load and spring compression\n9. Pressure test before startup\n10. Monitor for 2 hours after restart",
        "tools": ["Seal installation tool", "Torque wrench", "Clean room supplies"],
        "parts": ["Mechanical seal kit", "O-rings", "Gaskets", "Flush piping components if needed"],
        "time_hours": 6,
        "cost": 25000,
        "safety": "LOTO. Drain and vent. Chemical PPE if hazardous fluid. Confined space permit if seal inside vessel.",
    },
    "fan_blade_crack": {
        "problem": "Fatigue cracking on fan/blower blades",
        "solution": "1. Perform NDT (MT/PT) on all blades\n2. Map crack locations and lengths\n3. Determine if repair or replacement needed\n4. For repair: grind out crack, weld with qualified procedure, PWHT, NDT\n5. For replacement: source OEM blades, verify weight match\n6. Balance rotor after repair/replacement\n7. Verify natural frequencies haven't shifted\n8. Run-in with vibration monitoring",
        "tools": ["NDT equipment", "Welding equipment", "Balancing machine"],
        "parts": ["Replacement blades", "Welding consumables", "Balancing weights"],
        "time_hours": 48,
        "cost": 120000,
        "safety": "LOTO. Working at heights permit. Hot work permit for welding. Rotor lifting plan.",
    },
    "compressor_surge": {
        "problem": "Compressor surge event",
        "solution": "1. EMERGENCY: Trip compressor immediately if not auto-tripped\n2. Verify anti-surge valve opened\n3. Inspect impeller for damage (boroscope)\n4. Check thrust bearing for axial shift\n5. Verify surge control system logic and tuning\n6. Check recycle valve stroke time and capacity\n7. Verify instrumentation (pressure, flow, temperature)\n8. Test anti-surge loop before restart\n9. Restart with extended recycle period",
        "tools": ["Boroscope", "Vibration analyzer", "Control system access"],
        "parts": ["Anti-surge valve seat/seal kit (if damaged)"],
        "time_hours": 48,
        "cost": 150000,
        "safety": "LOTO. High pressure gas hazard. Hearing protection. Gas detection.",
    },
    "boiler_tube_leak": {
        "problem": "Water wall or superheater tube leak",
        "solution": "1. EMERGENCY: Initiate controlled shutdown per procedure\n2. Isolate boiler (main steam, feedwater, fuel)\n3. Depressurize and cool per cool-down curve\n4. Locate leak (visual, acoustic, thermal)\n5. Assess extent - single tube vs. multiple\n6. For single tube: pad weld or tube replacement\n7. For multiple: evaluate retube vs. panel replacement\n8. Hydrotest at 1.5x design pressure\n9. Refire per startup curve with NDT hold points",
        "tools": ["Acoustic leak detector", "Thermal camera", "Tube expander", "Welding equipment"],
        "parts": ["Replacement tubes", "Welding consumables", "Pad material", "Hydrotest equipment"],
        "time_hours": 12,
        "cost": 100000,
        "safety": "Confined space permit. Working at heights. Hot work permit. Hydrotest safety plan. PPE for insulation removal.",
    },
}


async def seed_database():
    """Seed the database with equipment catalog and known issues."""
    
    # Create engine
    engine = create_async_engine(
        settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
        echo=True,
    )
    
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print("🌱 Starting database seeding...")
        
        # Check if already seeded
        result = await session.execute(select(Equipment).limit(1))
        if result.scalar_one_or_none():
            print("⚠️  Database already seeded. Skipping.")
            return
        
        equipment_map = {}
        
        # Insert equipment
        print("📦 Inserting equipment catalog...")
        for eq_data in EQUIPMENT_DATA:
            equipment = Equipment(**eq_data)
            session.add(equipment)
            await session.flush()
            equipment_map[eq_data["tag_number"]] = equipment.id
            print(f"  ✅ {eq_data['tag_number']}: {eq_data['name']}")
        
        # Insert known issues and solutions
        print("🔧 Inserting known issues and solutions...")
        
        for tag, equip_id in equipment_map.items():
            # Get equipment category from the data
            eq_data = next(e for e in EQUIPMENT_DATA if e["tag_number"] == tag)
            category = eq_data["category"]
            
            if category in ISSUES_BY_CATEGORY:
                for issue_data in ISSUES_BY_CATEGORY[category]:
                    issue = EquipmentIssue(
                        equipment_id=equip_id,
                        **issue_data
                    )
                    session.add(issue)
                    await session.flush()
                    
                    # Add standard solution
                    solution_key = f"{category.value}_{issue_data['issue_name'].lower().replace(' ', '_')}"
                    if solution_key in STANDARD_SOLUTIONS:
                        sol_data = STANDARD_SOLUTIONS[solution_key]
                    else:
                        sol_data = {
                            "problem": issue_data["issue_name"],
                            "solution": issue_data["typical_solution"],
                            "solution_steps": [
                                "Diagnose using vibration/thermal/oil analysis",
                                "Plan shutdown per maintenance schedule",
                                "Execute repair per OEM manual",
                                "Verify repair with baseline measurements",
                                "Document in CMMS"
                            ],
                            "tools_required": ["Standard toolkit", "Vibration analyzer", "Thermal camera"],
                            "parts_required": ["OEM spare parts kit"],
                            "estimated_time_hours": issue_data["estimated_downtime_hours"],
                            "estimated_cost": issue_data["estimated_cost"],
                            "safety_precautions": "Follow LOTO procedure. Use appropriate PPE. Obtain required permits.",
                        }
                    
                    solution = ProblemSolution(
                        equipment_id=equip_id,
                        source=SolutionSource.PRE_SEEDED,
                        **sol_data
                    )
                    session.add(solution)
                    
                    print(f"  🔧 {tag}: {issue_data['issue_name']} (Severity: {issue_data['severity']}/10)")
        
        # Add a few cross-equipment problems (common patterns)
        print("🔗 Adding cross-equipment common problems...")
        
        # Vibration issues common to all rotating equipment
        rotating_equip = [eid for tag, eid in equipment_map.items() 
                         if any(cat in tag for cat in ['P-', 'IDF-', 'TG-', 'C-', 'GEN-'])]
        
        for equip_id in rotating_equip:
            generic_issue = EquipmentIssue(
                equipment_id=equip_id,
                issue_name="General Rotating Equipment Vibration",
                description="Elevated vibration on rotating machinery - generic monitoring issue",
                symptoms=["Vibration trend increasing", "Alarm on monitoring system"],
                root_causes=["Imbalance", "Misalignment", "Looseness", "Bearing wear", "Resonance"],
                severity=5,
                frequency="frequent",
                detection_method="Online vibration monitoring system",
                prevention="Monthly vibration trending, precision maintenance",
                typical_solution="Precision alignment, balancing, bearing replacement as needed",
                estimated_downtime_hours=8,
                estimated_cost=20000,
                regulatory_impact=False,
                safety_impact=False,
                source=ProblemSource.PRE_SEEDED,
            )
            session.add(generic_issue)
            await session.flush()
            
            generic_solution = ProblemSolution(
                equipment_id=equip_id,
                problem="Elevated vibration on rotating equipment",
                solution="Follow ISO 10816 vibration severity criteria. Diagnose using spectrum analysis. Correct root cause (alignment, balance, bearings).",
                solution_steps=[
                    "Collect vibration data (velocity, acceleration, displacement)",
                    "Analyze spectrum for dominant frequencies",
                    "Identify root cause: 1X=imbalance, 2X=misalignment, harmonics=looseness",
                    "Plan correction during next available outage",
                    "Execute precision alignment/balancing",
                    "Verify vibration within acceptable limits",
                    "Update baseline in monitoring system"
                ],
                tools_required=["Vibration analyzer (CSI/SPM/ Pruftechnik)", "Laser alignment tool", "Balancing equipment"],
                parts_required=["Shims", "Coupling elements", "Bearings (if needed)"],
                estimated_time_hours=8,
                estimated_cost=20000,
                safety_precautions="LOTO equipment. Follow vibration safety procedures.",
                source=SolutionSource.PRE_SEEDED,
            )
            session.add(generic_solution)
        
        await session.commit()
        print("✅ Database seeding completed successfully!")
        
        # Print summary
        total_equip = len(EQUIPMENT_DATA)
        total_issues = sum(len(issues) for issues in ISSUES_BY_CATEGORY.values()) + len(rotating_equip)
        print(f"\n📊 Summary:")
        print(f"   Equipment: {total_equip}")
        print(f"   Known Issues: {total_issues}")
        print(f"   Solutions: {total_issues}")


if __name__ == "__main__":
    asyncio.run(seed_database())