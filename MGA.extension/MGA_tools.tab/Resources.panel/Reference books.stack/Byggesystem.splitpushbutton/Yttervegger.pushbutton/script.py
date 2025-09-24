# -*- coding: utf-8 -*-

#  _  _      ____  ____  ____  _____ 
# / \/ \__/|/  __\/  _ \/  __\/__ __\
# | || |\/|||  \/|| / \||  \/|  / \  
# | || |  |||  __/| \_/||    /  | |  
# \_/\_/  \|\_/   \____/\_/\_\  \_/ IMPORTS
#----------------------------------STANDARD LIBRARY IMPORTS----------------------------------#

import os
import clr
clr.AddReference('System')
from System.Collections.Generic import List

#---------------------------- AUTODESK REVIT AND PYREVIT IMPORTS ----------------------------#

from Autodesk.Revit.UI import TaskDialog

#-------------------------------------- CUSTOM IMPORTS --------------------------------------#

from tools._file_magement import open_first_file_with_prefix

#  _     ____  ____  _  ____  ____  _     _____ ____ 
# / \ |\/  _ \/  __\/ \/  _ \/  __\/ \   /  __// ___\
# | | //| / \||  \/|| || / \|| | //| |   |  \  |    \
# | \// | |-|||    /| || |-||| |_\\| |_/\|  /_ \___ |
# \__/  \_/ \|\_/\_\\_/\_/ \|\____/\____/\____\\____/ VARIABLES

app    = __revit__.Application
uidoc  = __revit__.ActiveUIDocument
doc    = __revit__.ActiveUIDocument.Document #type:Document


#  _____ _     _      ____  _____  _  ____  _      ____ 
# /    // \ /\/ \  /|/   _\/__ __\/ \/  _ \/ \  /|/ ___\
# |  __\| | ||| |\ |||  /    / \  | || / \|| |\ |||    \
# | |   | \_/|| | \|||  \__  | |  | || \_/|| | \||\___ |
# \_/   \____/\_/  \|\____/  \_/  \_/\____/\_/  \|\____/ FUNCTIONS

#----------------------------------------MAIN------------------------------------------------#
def main():
    # Known first six characters of the filename
    search_prefix = '23'
    # Directory containing the files
    try:
        directory = "~\\DC\\ACCDocs\\MGA\\Boligbank\\Project Files\\Byggdetaljer\\00 Samlefiler og Informasjon\\01 Dokumenter\\"
        open_first_file_with_prefix(directory, search_prefix)
        TaskDialog.Show("✅Success", "File opened successfully.")

    except:
        TaskDialog.Show("Error", "Could not find path to building system. Set the 'Boligbank' project as the Selected Project in ACC - Desktop Connector.")
#  _      ____  _  _     
# / \__/|/  _ \/ \/ \  /|
# | |\/||| / \|| || |\ ||
# | |  ||| |-||| || | \||
# \_/  \|\_/ \|\_/\_/  \| MAIN SCRIPT    
if __name__ == '__main__':
    main()   

