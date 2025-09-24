# -*- coding: utf-8 -*-
""" 
Author Alexander Gilje
title: Door Type Mark
Date: 06.08.2025
"""



#  _  _      ____  ____  ____  _____ 
# / \/ \__/|/  __\/  _ \/  __\/__ __\
# | || |\/|||  \/|| / \||  \/|  / \  
# | || |  |||  __/| \_/||    /  | |  
# \_/\_/  \|\_/   \____/\_/\_\  \_/ IMPORTS

#----------------------------------STANDARD LIBRARY IMPORTS----------------------------------#

import os

#---------------------------- AUTODESK REVIT AND PYREVIT IMPORTS ----------------------------#
from Autodesk.Revit.DB import Transaction, BuiltInCategory, FilteredElementCollector

from Autodesk.Revit.UI import TaskDialog, TaskDialogCommonButtons, TaskDialogResult
from Autodesk.Revit.UI.Selection import ObjectType

#---------------------------------------CUSTOM IMPORTS---------------------------------------#
from tools._logger import ScriptLogger

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

logger = ScriptLogger(name='DoorTypeMark', log_to_file=True)


#  _____ _     _      ____  _____  _  ____  _      ____ 
# /    // \ /\/ \  /|/   _\/__ __\/ \/  _ \/ \  /|/ ___\
# |  __\| | ||| |\ |||  /    / \  | || / \|| |\ |||    \
# | |   | \_/|| | \|||  \__  | |  | || \_/|| | \||\___ |
# \_/   \____/\_/  \|\____/  \_/  \_/\____/\_/  \|\____/ FUNCTIONS

#----------------------------------------MAIN------------------------------------------------#

def main():
    # Get the active selection

    unique_types_doors = None


    doors_collector = DoorCollector(doc, logger)
    unique_types_doors = doors_collector.get_unique_doortypes()

    if not unique_types_doors:
        TaskDialog.Show("❌Error", "No doors found in the active document.")
    else:    
        grouper = TypeGrouper(unique_types_doors, logger)
        grouped_types = grouper.group_by_family_prefix()

        assigner = TypeMarkAssigner(doc, logger)
        try:
            assigner.assign_type_marks(grouped_types)
            TaskDialog.Show("✅Success", "Door type marks have been assigned successfully.")
        except Exception as e:
            logger.error("Error during transaction: {}".format(e))


#  ____  _     ____  ____  ____  _____ ____ 
# /   _\/ \   /  _ \/ ___\/ ___\/  __// ___\
# |  /  | |   | / \||    \|    \|  \  |    \
# |  \__| |_/\| |-||\___ |\___ ||  /_ \___ |
# \____/\____/\_/ \|\____/\____/\____\\____/ CLASSES

class DoorCollector(object):
    def __init__(self,doc, logger):
        self.doc = doc
        self.logger = logger
    
    def get_unique_doortypes(self):
        """
        Collects all unique door types in the active document.

        Returns:
            list: A list of unique door types (FamilySymbol elements)
        """
        doors = FilteredElementCollector(self.doc).OfCategory(BuiltInCategory.OST_Doors).WhereElementIsNotElementType().ToElements()
        unique_doortypes = {}

        logg_list = []
        logg_list_error = []

        for door in doors:
            try:
                symbol = door.Symbol
                if symbol and symbol.Id not in unique_doortypes:
                    unique_doortypes[symbol.Id] = symbol
                    logg_list.append("Successfully collected unique door type: {}" .format(symbol.FamilyName))
            except AttributeError as e:
                logg_list_error.append("Skipped element due to AttributeError: {}".format(e))
                continue
        if logg_list:
            loggs = "\n".join(logg_list)
            self.logger.info(loggs)

        
        if logg_list_error:
            error_logs = "\n".join(logg_list_error)
            self.logger.error(error_logs)
 
        
        
        
        return list(unique_doortypes.values())

class TypeGrouper(object):
    def __init__(self, types,logger):
        self.types = types
        self.logger = logger
    
    def group_by_family_prefix(self):
        grouped = {}
        for symbol in self.types:
            prefix = symbol.FamilyName[:2].upper() if symbol.FamilyName else "UN"
            grouped.setdefault(prefix, []).append(symbol)
        
        for prefix in grouped:
            grouped[prefix].sort(key=lambda x: x.Id)
        
        return grouped

class TypeMarkAssigner(object):
    def __init__(self, doc, logger):
        self.doc = doc
        self.logger = logger

    def assign_type_marks(self, grouped_types):
        logg_list = []
        logg_list_error = []
        t = Transaction(self.doc, "Assign Type Mark to Doors")
        t.Start()
        try:
            for prefix, types in grouped_types.items():
                for i, symbol in enumerate(types, start=1):
                    type_mark = "{}-{:02d}".format(prefix, i)
                    param = symbol.LookupParameter("Type Mark")
                    if param and not param.IsReadOnly:
                        param.Set(type_mark)
                        logg_list.append("Assigned {} to {}".format(type_mark, symbol.FamilyName))
                    else:
                        logg_list_error.append("Could not assign Type Mark to {}".format(symbol.FamilyName))
            t.Commit()
        except Exception as e:
            self.logger.error("Error during transaction: {}".format(e))
            t.RollBack()



#  _      ____  _  _     
# / \__/|/  _ \/ \/ \  /|
# | |\/||| / \|| || |\ ||
# | |  ||| |-||| || | \||
# \_/  \|\_/ \|\_/\_/  \| MAIN SCRIPT

# Run the script
if __name__ == "__main__":
    main()
