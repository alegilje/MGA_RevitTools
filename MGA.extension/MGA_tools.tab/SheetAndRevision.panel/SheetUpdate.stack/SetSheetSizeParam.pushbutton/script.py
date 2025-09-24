# encoding: utf-8
""" 
Author Alexander Gilje
title: Set Sheet Size
Date: 08.09.2025
"""
#  _  _      ____  ____  ____  _____ 
# / \/ \__/|/  __\/  _ \/  __\/__ __\
# | || |\/|||  \/|| / \||  \/|  / \  
# | || |  |||  __/| \_/||    /  | |  
# \_/\_/  \|\_/   \____/\_/\_\  \_/ IMPORTS
#----------------------------------STANDARD LIBRARY IMPORTS----------------------------------#

#---------------------------- AUTODESK REVIT AND PYREVIT IMPORTS ----------------------------#
from pyrevit import revit

from Autodesk.Revit.DB import \
    FilteredElementCollector, \
    BuiltInCategory, \
    BuiltInParameter,\
    BuiltInParameter, \
    StorageType, \
    UnitUtils, \
    UnitTypeId, \
    ViewSheet

#---------------------------- CUSTOM IMPORTS ----------------------------#

from tools._transactions import revit_transaction

#  _     ____  ____  _  ____  ____  _     _____ ____ 
# / \ |\/  _ \/  __\/ \/  _ \/  __\/ \   /  __// ___\
# | | //| / \||  \/|| || / \|| | //| |   |  \  |    \
# | \// | |-|||    /| || |-||| |_\\| |_/\|  /_ \___ |
# \__/  \_/ \|\_/\_\\_/\_/ \|\____/\____/\____\\____/ VARIABLES

uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document
TOL = 1.0  # mm toleranse



#  _____ _     _      ____  _____  _  ____  _      ____ 
# /    // \ /\/ \  /|/   _\/__ __\/ \/  _ \/ \  /|/ ___\
# |  __\| | ||| |\ |||  /    / \  | || / \|| |\ |||    \
# | |   | \_/|| | \|||  \__  | |  | || \_/|| | \||\___ |
# \_/   \____/\_/  \|\____/  \_/  \_/\____/\_/  \|\____/ FUNCTIONS

#----------------------------------------MAIN------------------------------------------------#
def main():
    sheets = FilteredElementCollector(doc).OfClass(ViewSheet).ToElements()

    with revit.Transaction("Set sheet format"):
        for sheet in sheets:
            p_w = sheet.get_Parameter(BuiltInParameter.SHEET_WIDTH)
            p_h = sheet.get_Parameter(BuiltInParameter.SHEET_HEIGHT)
            p_fmt = sheet.LookupParameter("Format")

            if not (p_w and p_h):
                continue

            w_int = p_w.AsDouble()
            h_int = p_h.AsDouble()
            w_mm = UnitUtils.ConvertFromInternalUnits(w_int, UnitTypeId.Millimeters)
            h_mm = UnitUtils.ConvertFromInternalUnits(h_int, UnitTypeId.Millimeters)

            fmt = classify_iso_a(w_mm, h_mm)
            if fmt and p_fmt and not p_fmt.IsReadOnly and p_fmt.StorageType == StorageType.String:
                p_fmt.Set(fmt)


def classify_iso_a(width_mm, height_mm, tol=TOL):
    w, h = sorted([width_mm, height_mm])
    pairs = {
        "A4":  (210, 297),
        "A3":  (297, 420),
        "A2":  (420, 594),
        "A1":  (594, 841),
        "A0":  (841, 1189),
    }
    for name, (aw, ah) in pairs.items():
        if abs(w - aw) <= tol and abs(h - ah) <= tol:
            return name
    # fallback med sum (uavhengig av orientering)
    sums = {"A4": 507, "A3": 717, "A2": 1014, "A1": 1435, "A0": 2030}
    s = w + h
    for name, target in sums.items():
        if abs(s - target) <= tol:
            return name
    return None

#  _      ____  _  _     
# / \__/|/  _ \/ \/ \  /|
# | |\/||| / \|| || |\ ||
# | |  ||| |-||| || | \||
# \_/  \|\_/ \|\_/\_/  \| MAIN SCRIPT

if __name__ == '__main__':
    main()
