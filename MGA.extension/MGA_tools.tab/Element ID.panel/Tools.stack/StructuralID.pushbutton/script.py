# -*- coding: utf-8 -*-
"""
Author = Andreas Lorentzen Mathisen, Alexander Gilje
Title  = Renumber Framing Elements ID
doc    = Version = 1.0
"""
#  _  _      ____  ____  ____  _____ 
# / \/ \__/|/  __\/  _ \/  __\/__ __\
# | || |\/|||  \/|| / \||  \/|  / \  
# | || |  |||  __/| \_/||    /  | |  
# \_/\_/  \|\_/   \____/\_/\_\  \_/ IMPORTS
#----------------------------------STANDARD LIBRARY IMPORTS----------------------------------#
#.NET Imports
import clr
clr.AddReference('System')
from System.Collections.Generic import List
from collections import defaultdict

#---------------------------- AUTODESK REVIT AND PYREVIT IMPORTS ----------------------------#
from Autodesk.Revit.UI import TaskDialog, TaskDialogCommonButtons, TaskDialogResult, TaskDialogCommandLinkId
from Autodesk.Revit.UI.Selection import ObjectType
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory

#---------------------------------------CUSTOM IMPORTS---------------------------------------#
from tools._logger import ScriptLogger
from tools._transactions import revit_transaction

#  _     ____  ____  _  ____  ____  _     _____ ____ 
# / \ |\/  _ \/  __\/ \/  _ \/  __\/ \   /  __// ___\
# | | //| / \||  \/|| || / \|| | //| |   |  \  |    \
# | \// | |-|||    /| || |-||| |_\\| |_/\|  /_ \___ |
# \__/  \_/ \|\_/\_\\_/\_/ \|\____/\____/\____\\____/ VARIABLES

app    = __revit__.Application
uidoc  = __revit__.ActiveUIDocument
doc    = __revit__.ActiveUIDocument.Document

#  _     ____  _____ _____ _  _      _____
# / \   /  _ \/  __//  __// \/ \  /|/  __/
# | |   | / \|| |  _| |  _| || |\ ||| |  _
# | |_/\| \_/|| |_//| |_//| || | \||| |_//
# \____/\____/\____\\____\\_/\_/  \|\____\ LOGGING

logger = ScriptLogger(name='Renumber Framing Elements ID', log_to_file=True)


#  _____ _     _      ____  _____  _  ____  _      ____ 
# /    // \ /\/ \  /|/   _\/__ __\/ \/  _ \/ \  /|/ ___\
# |  __\| | ||| |\ |||  /    / \  | || / \|| |\ |||    \
# | |   | \_/|| | \|||  \__  | |  | || \_/|| | \||\___ |
# \_/   \____/\_/  \|\____/  \_/  \_/\____/\_/  \|\____/ FUNCTIONS

#----------------------------------------MAIN------------------------------------------------#
def _feet_to_m(feet_value):
    return feet_value * 0.3048


def _round_len_m(val_m, precision):
    # python 2.7 round returns float; ensure stable string sorting later
    return round(val_m, precision)


def _get_elem_length_m(elem):
    # Try localized "Pre-cut Lengde" first, then "Cut Length"
    p = elem.LookupParameter("Pre-cut Lengde")
    if p is None:
        p = elem.LookupParameter("Cut Length")
    if p and p.HasValue:
        try:
            return _feet_to_m(p.AsDouble())
        except:
            return None
    return None


def _collect_selected_or_all_framing():
    sel_ids = uidoc.Selection.GetElementIds()
    elements = []
    if sel_ids is not None and sel_ids.Count > 0:
        # Use only Structural Framing from current selection
        for eid in sel_ids:
            e = doc.GetElement(eid)
            if e and e.Category and e.Category.Id.IntegerValue == int(BuiltInCategory.OST_StructuralFraming):
                elements.append(e)
    else:
        # Nothing selected: get all Structural Framing instances in model
        elements = list(FilteredElementCollector(doc)
                        .OfCategory(BuiltInCategory.OST_StructuralFraming)
                        .WhereElementIsNotElementType()
                        .ToElements())
    return elements


def _group_by_type_and_length(elements, precision):
    # { type_name: { rounded_length_m: [elements...] } }
    grouped = {}
    for e in elements:
        # Skip invalids
        if e is None:
            continue
        length_m = _get_elem_length_m(e)
        if length_m is None:
            continue
        # Type name: use element type name (FamilySymbol.Name)
        try:
            t = e.Symbol
            if t:
                type_name = t.Name
            else:
                type_name = e.Name
        except:
            type_name = e.Name
        rlen = _round_len_m(length_m, precision)
        if type_name not in grouped:
            grouped[type_name] = {}
        if rlen not in grouped[type_name]:
            grouped[type_name][rlen] = []
        grouped[type_name][rlen].append(e)
    return grouped


def _assign_mark_values(grouped):
    # Sequential Mark per (type, rounded length) group
    mark_val = 1
    # Sort type names alphabetically; lengths numerically
    for type_name in sorted(grouped.keys()):
        length_map = grouped[type_name]
        # sorted keys of lengths; ensure numeric sort
        for rlen in sorted(length_map.keys()):
            elems = length_map[rlen]
            for e in elems:
                p = e.LookupParameter("Mark")
                if p and not p.IsReadOnly:
                    p.Set(str(mark_val))
            mark_val += 1


def main():
    elements = _collect_selected_or_all_framing()
    if not elements:
        TaskDialog.Show("Renumber Framing Elements ID", "Ingen bjelker funnet (Structural Framing).")
        return
    with revit_transaction(doc,"Renumber Framing Elements ID"):
        grouped = _group_by_type_and_length(elements, precision=2)
        if not grouped:
            TaskDialog.Show("Renumber Framing Elements ID", "Fant ingen elementer med gyldig lengde.")
            return
        _assign_mark_values(grouped)
    TaskDialog.Show("Renumber Framing Elements ID", "Nummerering fullført.")

#  _      ____  _  _     
# / \__/|/  _ \/ \/ \  /|
# | |\/||| / \|| || |\ ||
# | |  ||| |-||| || | \||
# \_/  \|\_/ \|\_/\_/  \| MAIN SCRIPT

# Run the script
if __name__ == "__main__":
    main()

