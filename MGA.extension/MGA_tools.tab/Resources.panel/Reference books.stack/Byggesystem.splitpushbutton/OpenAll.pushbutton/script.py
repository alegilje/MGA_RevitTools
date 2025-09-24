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
from pyrevit import forms

#  _____ _     _      ____  _____  _  ____  _      ____ 
# /    // \ /\/ \  /|/   _\/__ __\/ \/  _ \/ \  /|/ ___\
# |  __\| | ||| |\ |||  /    / \  | || / \|| |\ |||    \
# | |   | \_/|| | \|||  \__  | |  | || \_/|| | \||\___ |
# \_/   \____/\_/  \|\____/  \_/  \_/\____/\_/  \|\____/ FUNCTIONS

#----------------------------------------MAIN------------------------------------------------#
def main():
    # Juster prefiks etter behov, t.d. '21'
    search_prefix = '2'

    try:
        directory = os.path.expanduser(
            "~\\DC\\ACCDocs\\MGA\\Boligbank\\Project Files\\Byggdetaljer\\00 Samlefiler og Informasjon\\01 Dokumenter\\"
        )

        # Collect only files that match the prefix
        all_names = os.listdir(directory)
        files = [f for f in all_names if f.startswith(search_prefix)]
        total = len(files)

        if total == 0:
            TaskDialog.Show("Info",
                            "No files found with prefix '{0}' in:\n{1}".format(search_prefix, directory))
            return

        opened_count = 0
        cancelled = False

        # Real filling progress bar at the top of the Revit window
        # Tip: increase 'step' (e.g., 10 or 25) to reduce GUI updates for many items
        with forms.ProgressBar(title='{value} of {max_value}', cancellable=True, step=1) as pb:
            for i, filename in enumerate(files, start=1):
                if pb.cancelled:
                    cancelled = True
                    break

                file_path = os.path.join(directory, filename)
                try:
                    os.startfile(file_path)
                    opened_count += 1
                except Exception:
                    # Optionally log the error here if you want
                    pass

                pb.update_progress(i, total)

        if cancelled:
            TaskDialog.Show("Cancelled",
                            "Stopped after opening {0} of {1} files.".format(opened_count, total))
        else:
            TaskDialog.Show("✅ Success",
                            "Opens {0} of {1} files.".format(opened_count, total))

    except Exception as e:
        TaskDialog.Show("Error",
                        "Could not find path to the building system.\n"
                        "Set the 'Boligbank' project as the Selected Project in ACC - Desktop Connector.\n\n"
                        "Details: {0}".format(e))
        
#  _      ____  _  _     
# / \__/|/  _ \/ \/ \  /|
# | |\/||| / \|| || |\ ||
# | |  ||| |-||| || | \||
# \_/  \|\_/ \|\_/\_/  \| MAIN SCRIPT    
if __name__ == '__main__':
    main()
