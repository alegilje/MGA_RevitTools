# encoding: utf-8
""" 
Author Alexander Gilje
Title: Window Type Mark
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

from Autodesk.Revit.DB import Transaction, BuiltInCategory, BuiltInParameter, FilteredElementCollector
from Autodesk.Revit.UI import TaskDialog
from tools._logger import ScriptLogger



#---------------------------------------CUSTOM IMPORTS---------------------------------------#

from tools._transactions import revit_transaction

#  _     ____  _____ _____ _  _      _____
# / \   /  _ \/  __//  __// \/ \  /|/  __/
# | |   | / \|| |  _| |  _| || |\ ||| |  _
# | |_/\| \_/|| |_//| |_//| || | \||| |_//
# \____/\____/\____\\____\\_/\_/  \|\____\ LOGGING
                                  


logger = ScriptLogger(name='WindowTypeMark', log_to_file=True)


#  _     ____  ____  _  ____  ____  _     _____ ____ 
# / \ |\/  _ \/  __\/ \/  _ \/  __\/ \   /  __// ___\
# | | //| / \||  \/|| || / \|| | //| |   |  \  |    \
# | \// | |-|||    /| || |-||| |_\\| |_/\|  /_ \___ |
# \__/  \_/ \|\_/\_\\_/\_/ \|\____/\____/\____\\____/ VARIABLES

#----------------------------------Project Parameters----------------------------------------#

app    = __revit__.Application
uidoc  = __revit__.ActiveUIDocument
doc    = __revit__.ActiveUIDocument.Document 



#  _____ _     _      ____  _____  _  ____  _      ____ 
# /    // \ /\/ \  /|/   _\/__ __\/ \/  _ \/ \  /|/ ___\
# |  __\| | ||| |\ |||  /    / \  | || / \|| |\ |||    \
# | |   | \_/|| | \|||  \__  | |  | || \_/|| | \||\___ |
# \_/   \____/\_/  \|\____/  \_/  \_/\____/\_/  \|\____/ FUNCTIONS

#----------------------------------------MAIN------------------------------------------------#

def main():

    collector = WindowCollector(doc, logger)
    window_types = collector.get_unique_window_types()


    if not window_types:
        TaskDialog.Show("❌ Error", "No windows found.")
        return

    # Sort alphabetically by type name for consistency
    sorted_types = sorted(
        window_types,
        key=lambda x: x.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString()
    )

    assigner = WindowTypeMarkAssigner(doc, logger)
    try:
        assigner.assign_type_marks(sorted_types)
        logger.info("Window type marks were assigned successfully.")
        TaskDialog.Show("✅ Success", "Window type marks were assigned successfully.")
    except Exception as e:
        logger.error("Error: {}".format(e))
        TaskDialog.Show("❌ Error", "An error occurred while assigning type marks.")








class WindowCollector(object):
    def __init__(self, doc, logger):
        self.doc = doc
        self.logger = logger
    
    def get_unique_window_types(self):
        """Collects all unique window types in the document."""
        windows = FilteredElementCollector(self.doc)\
            .OfCategory(BuiltInCategory.OST_Windows)\
            .WhereElementIsNotElementType()\
            .ToElements()

        unique_types = {}
        for win in windows:
            try:
                symbol = win.Symbol
                if symbol and symbol.Id not in unique_types:
                    unique_types[symbol.Id] = symbol
            except AttributeError as e:
                self.logger.error("Skipped element due to AttributeError: {}".format(e))
        return list(unique_types.values())

class WindowTypeMarkAssigner(object):
    def __init__(self, doc, logger):
        self.doc = doc
        self.logger = logger

    def assign_type_marks(self, symbols):
        """Assigns sequential type marks with prefix V-01, V-02, ..."""
        prefix = "V-"
        t = Transaction(self.doc, "Assign Type Mark to Windows")
        t.Start()
        try:
            for i, symbol in enumerate(symbols, start=1):
                type_mark = "{}{:02d}".format(prefix, i)
                param = symbol.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_MARK)
                if param and not param.IsReadOnly:
                    param.Set(type_mark)
                    self.logger.info("Assigned {} to {}".format(type_mark, symbol.FamilyName))
                else:
                    self.logger.error("Could not assign Type Mark to {}".format(symbol.FamilyName))
            t.Commit()
        except Exception as e:
            self.logger.error("Error during transaction: {}".format(e))
            t.RollBack()
# / \__/|/  _ \/ \/ \  /|
# | |\/||| / \|| || |\ ||
# | |  ||| |-||| || | \||
# \_/  \|\_/ \|\_/\_/  \| MAIN SCRIPT

if __name__ == "__main__":
    
    main() 