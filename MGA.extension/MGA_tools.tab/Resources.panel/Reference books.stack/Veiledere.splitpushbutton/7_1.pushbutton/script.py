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

#  _____ _     _      ____  _____  _  ____  _      ____ 
# /    // \ /\/ \  /|/   _\/__ __\/ \/  _ \/ \  /|/ ___\
# |  __\| | ||| |\ |||  /    / \  | || / \|| |\ |||    \
# | |   | \_/|| | \|||  \__  | |  | || \_/|| | \||\___ |
# \_/   \____/\_/  \|\____/  \_/  \_/\____/\_/  \|\____/ FUNCTIONS

#----------------------------------------MAIN------------------------------------------------#
def main():
    # Known first six characters of the filename
    search_prefix = '7_1'
    # Directory containing the files
    try:
        directory = "~\\DC\\ACCDocs\\MGA\\Revit Bibliotek\\Project Files\\Veiledere\\"
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

