# Encoding: utf-8

# IMPORTS
from Autodesk.Revit.DB import *
from pyrevit import revit, DB, script, forms, HOST_APP, coreutils
# VARIABLES
app = __revit__.Application

# FUNCTIONS

def convert_internal_to_mm(length):
    return UnitUtils.ConvertFromInternalUnits( length,
                                              UnitTypeId.Millimeters)

def convert_mm_to_internal(length):
    return UnitUtils.ConvertToInternalUnits(length, UnitTypeId.Millimeters)

def convert_m_to_internal(length):
    return UnitUtils.ConvertToInternalUnits(length, UnitTypeId.Meters)

def convert_length_to_internal(value, doc=revit.doc):
    # convert length units from display units to internal
    display_units = get_length_units(doc)
    converted = DB.UnitUtils.ConvertToInternalUnits(value, display_units)
    return converted

def get_length_units(doc):
    # fetch Revit's internal units depending on the Revit version
    units = doc.GetUnits()
    if HOST_APP.is_newer_than(2021):
        int_length_units = units.GetFormatOptions(DB.SpecTypeId.Length).GetUnitTypeId()
    else:
        int_length_units = units.GetFormatOptions(DB.UnitType.UT_Length).DisplayUnits
    return int_length_units