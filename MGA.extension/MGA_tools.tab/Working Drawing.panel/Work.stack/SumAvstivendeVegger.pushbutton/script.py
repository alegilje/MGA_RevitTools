# -*- coding: utf-8 -*-

#  _  _      ____  ____  ____  _____ 
# / \/ \__/|/  __\/  _ \/  __\/__ __\
# | || |\/|||  \/|| / \||  \/|  / \  
# | || |  |||  __/| \_/||    /  | |  
# \_/\_/  \|\_/   \____/\_/\_\  \_/ IMPORTS
#----------------------------------STANDARD LIBRARY IMPORTS----------------------------------#

#---------------------------- AUTODESK REVIT AND PYREVIT IMPORTS ----------------------------#
from Autodesk.Revit.DB import FilteredElementCollector, Dimension, DimensionType, BuiltInParameter
from Autodesk.Revit.UI import TaskDialog
from pyrevit import forms
#  _     ____  ____  _  ____  ____  _     _____ ____ 
# / \ |\/  _ \/  __\/ \/  _ \/  __\/ \   /  __// ___\
# | | //| / \||  \/|| || / \|| | //| |   |  \  |    \
# | \// | |-|||    /| || |-||| |_\\| |_/\|  /_ \___ |
# \__/  \_/ \|\_/\_\\_/\_/ \|\____/\____/\____\\____/ VARIABLES
doc = __revit__.ActiveUIDocument.Document

#  _____ _     _      ____  _____  _  ____  _      ____ 
# /    // \ /\/ \  /|/   _\/__ __\/ \/  _ \/ \  /|/ ___\
# |  __\| | ||| |\ |||  /    / \  | || / \|| |\ |||    \
# | |   | \_/|| | \|||  \__  | |  | || \_/|| | \||\___ |
# \_/   \____/\_/  \|\____/  \_/  \_/\____/\_/  \|\____/ FUNCTIONS

#----------------------------------------MAIN------------------------------------------------#
def main():
    # Hent alle dimension types og sikre korrekt navn
    dimension_types = FilteredElementCollector(doc).OfClass(DimensionType).ToElements()
    dimension_type_names = sorted(list(set([
        dt.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString() for dt in dimension_types
    ])))

    # La bruker velge dimension type
    selected_type = forms.SelectFromList.show(
        dimension_type_names,
        title="Velg Dimension Type",
        button_name="Summer dimensjoner"
    )

    # Hvis bruker avbryter
    if not selected_type:
        TaskDialog.Show("Error", "Ingen dimension type ble valgt.")
        raise SystemExit()

    # Hent alle dimensjoner og filtrer
    all_dimensions = FilteredElementCollector(doc).OfClass(Dimension)
    target_dimensions = [
        dim for dim in all_dimensions
        if dim.DimensionType.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString() == selected_type
    ]

    # Summer lengdene
    total_length = 0.0
    for dim in target_dimensions:
        if dim.Value:
            total_length += dim.Value

    # Konverter til meter
    total_length_meters = total_length * 0.3048

    # Vis resultat
    TaskDialog.Show(
        "Success",
        "Totallengde for dimensjoner av type '{}':\n{} meter".format(
            selected_type, round(total_length_meters, 2))
    )

#  _      ____  _  _     
# / \__/|/  _ \/ \/ \  /|
# | |\/||| / \|| || |\ ||
# | |  ||| |-||| || | \||
# \_/  \|\_/ \|\_/\_/  \| MAIN SCRIPT

if __name__ == '__main__':
    main()