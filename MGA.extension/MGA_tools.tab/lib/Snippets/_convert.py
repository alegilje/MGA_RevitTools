# Encoding: utf-8

# IMPORTS
from Autodesk.Revit.DB import *

# VARIABLES
app = __revit__.Application

# FUNCTIONS

def convert_internal_to_mm(length):
    return UnitUtils.ConvertFromInternalUnits( length,
                                              UnitTypeId.Millimeters)

def convert_mm_to_internal(length):
    return UnitUtils.ConvertToInternalUnits(length, UnitTypeId.Millimeters)