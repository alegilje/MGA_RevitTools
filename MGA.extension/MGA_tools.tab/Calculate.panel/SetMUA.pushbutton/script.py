# encoding: utf-8
""" 
Author Alexander Gilje
title: Get Area Filled Regions
Date: 05.06.2025
"""
#  _  _      ____  ____  ____  _____ 
# / \/ \__/|/  __\/  _ \/  __\/__ __\
# | || |\/|||  \/|| / \||  \/|  / \  
# | || |  |||  __/| \_/||    /  | |  
# \_/\_/  \|\_/   \____/\_/\_\  \_/ IMPORTS
#----------------------------------STANDARD LIBRARY IMPORTS----------------------------------#

#---------------------------- AUTODESK REVIT AND PYREVIT IMPORTS ----------------------------#
from pyrevit import revit, DB

from Autodesk.Revit.DB import BuiltInCategory, BuiltInParameter, FilteredElementCollector, StorageType, UnitUtils, UnitTypeId
from Autodesk.Revit.UI import TaskDialog
#---------------------------------------CUSTOM IMPORTS---------------------------------------#
from formsWindow._forms import dialogwindow_TextInput
from tools._transactions import revit_transaction

#  _     ____  ____  _  ____  ____  _     _____ ____ 
# / \ |\/  _ \/  __\/ \/  _ \/  __\/ \   /  __// ___\
# | | //| / \||  \/|| || / \|| | //| |   |  \  |    \
# | \// | |-|||    /| || |-||| |_\\| |_/\|  /_ \___ |
# \__/  \_/ \|\_/\_\\_/\_/ \|\____/\____/\____\\____/ VARIABLES

doc = revit.doc
uidoc = revit.uidoc
view = doc.ActiveView

#  _____ _     _      ____  _____  _  ____  _      ____ 
# /    // \ /\/ \  /|/   _\/__ __\/ \/  _ \/ \  /|/ ___\
# |  __\| | ||| |\ |||  /    / \  | || / \|| |\ |||    \
# | |   | \_/|| | \|||  \__  | |  | || \_/|| | \||\___ |
# \_/   \____/\_/  \|\____/  \_/  \_/\____/\_/  \|\____/ FUNCTIONS

#----------------------------------------MAIN------------------------------------------------#
def main():
    filled_regions_in_view = FilteredElementCollector(doc, view.Id).OfCategory(BuiltInCategory.OST_DetailComponents).WhereElementIsNotElementType()
    
    if filled_regions_in_view:
        filled_regions_in_view_length = len(list(filled_regions_in_view))
        if filled_regions_in_view_length > 1:
            search_word = dialogwindow_TextInput("MUA", "Skriv inn hele eller deler av ordet fra kommentarfeltet (Comments).\n For eksempel: Skriv 'MUA' for å hente alle med 'MUA' i kommentaren (som 'MUA 1', 'MUA 2'),\n eller skriv 'MUA 1' for å hente kun de med nøyaktig 'MUA 1'. Ved tomt felt blir alle hentet:", "Hva skal du ha arealet av")
            if not search_word or search_word.lower() == "alle":
                search_word = "Alle"

            filled_regions = [el for el in filled_regions_in_view if isinstance(el, DB.FilledRegion)]

            length_count = 0
            area_count = 0

            if search_word == "Alle":
                for fr in filled_regions:
                    comments = check_comments(fr)
                    if not "demo" in comments.lower():

                        areal_param = fr.LookupParameter("Areal")
                        length_param = fr.LookupParameter("Omkrets")

                        if areal_param and length_param:

                            with revit_transaction(doc,"Sett areal og omkrets"):
                                areal_param.Set(get_total_area(fr))
                                length_param.Set(get_total_length(fr))
                                length_count += 1
                                area_count += 1

                        elif length_param:    
                            with revit_transaction(doc,"Sett omkrets"):
                                length_param.Set(get_total_length(fr))
                                length_count += 1

                        elif areal_param:
                            with revit_transaction(doc,"Sett areal"):
                                areal_param.Set(get_total_area(fr))
                                area_count += 1

            else:
                for fr in filled_regions:
                    comments = check_comments(fr)
                    if not "demo" in comments.lower() and str(search_word).lower() in comments.lower():
                        areal_param = fr.LookupParameter("Areal")
                        length_param = fr.LookupParameter("Omkrets")

                        if areal_param and length_param:

                            with revit_transaction(doc,"Sett areal og omkrets"):
                                areal_param.Set(get_total_area(fr))
                                length_param.Set(get_total_length(fr))
                                length_count += 1
                                area_count += 1

                        elif length_param:    
                            with revit_transaction(doc,"Sett omkrets"):
                                length_param.Set(get_total_length(fr))
                                length_count += 1

                        elif areal_param:
                            with revit_transaction(doc,"Sett areal"):
                                areal_param.Set(get_total_area(fr))
                                area_count += 1

            TaskDialog.Show("Success","Satt areal på {}, og omkrets på {} filled regions.".format(area_count, length_count))
        else:
            TaskDialog.Show("Feil","Ingen filled regions i viewet.") 
    else:
        TaskDialog.Show("Feil","Ingen filled regions i viewet.")
   


def get_total_length(filled_region):
    total_length = 0.0
    for loop in filled_region.GetBoundaries():
        total_length += loop.GetExactLength()
    return total_length

def get_total_area(filled_region):
    area_param = filled_region.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED)
    if area_param and area_param.StorageType == StorageType.Double:
        return UnitUtils.ConvertFromInternalUnits(area_param.AsDouble(), UnitTypeId.SquareMeters)

def check_comments(filled_region):
    comment = filled_region.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
    return comment.AsString() if comment else None
#  _      ____  _  _     
# / \__/|/  _ \/ \/ \  /|
# | |\/||| / \|| || |\ ||
# | |  ||| |-||| || | \||
# \_/  \|\_/ \|\_/\_/  \| MAIN SCRIPT

if __name__ == "__main__":
    
    main()