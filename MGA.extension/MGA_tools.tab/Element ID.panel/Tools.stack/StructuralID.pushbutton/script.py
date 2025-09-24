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
def main():
    selected_elements = ask_user_for_scope(uidoc)

    if not selected_elements:
        TaskDialog.Show("Error", "No elements selected.")
        logger.info("No elements selected.")
        return
    
    else:
        elements = [doc.GetElement(eid) for eid in selected_elements if doc.GetElement(eid)]
        with revit_transaction(doc, "Renumber Framing Elements ID"):
            grouped = group_elements_by_type_and_length(elements, precision=2)
            assign_mark_values(doc, grouped)
            TaskDialog.Show("Success","Renumbering complete.")
        
        logger.info("Renumbering complete.")

def ask_user_for_scope(uidoc):
    """Ask the user if all windows should be processed or only the selected ones."""
    dialog = TaskDialog("Renumber Framing Elements ID")
    dialog.MainInstruction = "Select the beams/joists you wish to number?"
    dialog.AddCommandLink(TaskDialogCommandLinkId.CommandLink1, "Select manually")
    dialog.CommonButtons = TaskDialogCommonButtons.Cancel

    result = dialog.Show()

    if result == TaskDialogResult.CommandLink1:
        return pick_elements(uidoc)
    else:
        return None 


def pick_elements(uidoc):
    """Let the user pick windows manually in Revit."""
    picked_elements = uidoc.Selection.PickObjects(ObjectType.Element, "Select windows")
    return picked_elements

def round_length(length_value, precision=2):
    # Rounding the length to the specified precision (e.g., 2 decimal places)
    return round(length_value, precision)


def get_length_in_meters(element):
    """Return element length in meters (using Pre-cut Length or Cut Length)."""
    length_param = element.LookupParameter("Pre-cut Lengde") or element.LookupParameter("Cut Length")
    if length_param and length_param.HasValue:
        length_value = length_param.AsDouble()  # stored in feet
        return length_value * 0.3048  # convert to meters
    return None

def group_elements_by_type_and_length(elements, precision=2):
    """Group elements by type name and rounded length."""
    type_dict = defaultdict(lambda: defaultdict(list))
    for element in elements:
        type_name = element.Name
        length_value = get_length_in_meters(element)
        if length_value is not None:
            rounded_length = round_length(length_value, precision)
            type_dict[type_name][rounded_length].append(element)
    return type_dict


def assign_mark_values(doc, grouped_elements):
    """Assign sequential Mark values to grouped elements."""
    mark_value = 1
    for type_name, length_groups in sorted(grouped_elements.items()):
        for length_value, elements_in_group in sorted(length_groups.items()):
            for element in elements_in_group:
                mark_param = element.LookupParameter("Mark")
                if mark_param:
                    mark_param.Set(str(mark_value))
                else:
                    TaskDialog.Show(
                        "Element {} does not have a 'Mark' parameter.".format(element.Id),
                        title="Warning"
                    )
            mark_value += 1

#  _      ____  _  _     
# / \__/|/  _ \/ \/ \  /|
# | |\/||| / \|| || |\ ||
# | |  ||| |-||| || | \||
# \_/  \|\_/ \|\_/\_/  \| MAIN SCRIPT

# Run the script
if __name__ == "__main__":
    main()

