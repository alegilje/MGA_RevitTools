# encoding: utf-8
""" 
Author Alexander Gilje
title: Set MUA Areal
Date: 05.06.2025
"""
#  _  _      ____  ____  ____  _____ 
# / \/ \__/|/  __\/  _ \/  __\/__ __\
# | || |\/|||  \/|| / \||  \/|  / \  
# | || |  |||  __/| \_/||    /  | |  
# \_/\_/  \|\_/   \____/\_/\_\  \_/ IMPORTS
#----------------------------------STANDARD LIBRARY IMPORTS----------------------------------#

from pyrevit import revit, DB

from Autodesk.Revit.DB import BuiltInCategory, BuiltInParameter, FilteredElementCollector, StorageType, UnitUtils, UnitTypeId

from formsWindow._forms import dialogwindow_TextInput
from tools._transactions import revit_transaction
from Autodesk.Revit.UI import TaskDialog

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

    search_word = dialogwindow_TextInput("MUA", "Skriv inn hele eller deler av ordet fra kommentarfeltet (Comments).\n For eksempel: Skriv 'MUA' for å hente alle med 'MUA' i kommentaren (som 'MUA 1', 'MUA 2'),\n eller skriv 'MUA 1' for å hente kun de med nøyaktig 'MUA 1'.:", "Hva skal du ha arealet av")
    collector = FilteredElementCollector(doc, view.Id).OfCategory(BuiltInCategory.OST_DetailComponents).WhereElementIsNotElementType()
    if not search_word:
        search_word = "Alle"
    filled_regions = [el for el in collector if isinstance(el, DB.FilledRegion)]
    if filled_regions:
        # Filterer på "search_word" i Comments
        filtered = []
        omkretser = []

        for fr in filled_regions:
            comment = fr.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
            print(comment)
            print(search_word)
            if search_word != "":
                if comment:
                    comment_str = comment.AsString()
                    if comment_str and not "demo" in comment_str.lower() and str(search_word).lower() in comment_str.lower():
                        boundaries = fr.GetBoundaries()
                        omkrets = 0.0
                        for loop in boundaries:
                            omkrets += loop.GetExactLength()
                        omkretser.append(omkrets)
                        filtered.append(fr)
                if not comment:    
                    boundaries = fr.GetBoundaries()
                    omkrets = 0.0
                    for loop in boundaries:
                        omkrets += loop.GetExactLength()
                    omkretser.append(omkrets)
                    filtered.append(fr)        
        if filtered:

            reported_lines = []
            for fr,omkrets in zip(filtered,omkretser):
                # Hent area i m²
                area_param = fr.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED)
                if area_param and area_param.StorageType == StorageType.Double:
                    area_m2 = UnitUtils.ConvertFromInternalUnits(area_param.AsDouble(), UnitTypeId.SquareMeters)

                # Finn "Areal"-parameter
                    areal_param = fr.LookupParameter("Areal")
                    length_param = fr.LookupParameter("Omkrets")
                    if areal_param and length_param:
                        
                        with revit_transaction(doc, "Set Areal og Omkrets"):
                            areal_param.Set(area_m2)
                            length_param.Set(omkrets)
                            reported_lines.append("{}: Areal og Omkrets".format(fr.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS).AsString()))

                    elif length_param:
                        with revit_transaction(doc, "Set Omkrets"):
                            length_param.Set(omkrets)
                            reported_lines.append("Omkrets for comment {} er Oppdatert".format(fr.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS).AsString()))

                    elif areal_param:
                        with revit_transaction(doc, "Set Areal"):
                            areal_param.Set(area_m2)
                            reported_lines.append("Areal for comment {} er Oppdatert".format(fr.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS).AsString()))
                    
                    else:
                        reported_lines.append("Ingen parameter funnet for: {}".format(fr.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS).AsString()))
                                
            if reported_lines:
                reported_lines.insert(0, "Dette er oppdatert(Comment verdi, Parameter):")
                report_lines = [reported_lines[0]] + ["    " + line for line in reported_lines[1:]]
                result_message = "\n".join(report_lines)
            else:
                result_message = "Ingen parameter funnet. Legg til parametere, Omkrets og/eller Areal i filled region og prøv igjen."

            TaskDialog.Show("Resultat",result_message)
        else:
            TaskDialog.Show("Feil", "Ingen Filled Region med verdien {} i Comments funnet".format(search_word))
    else:
        TaskDialog.Show("Feil", "Ingen Filled Region funnet")
#  _      ____  _  _     
# / \__/|/  _ \/ \/ \  /|
# | |\/||| / \|| || |\ ||
# | |  ||| |-||| || | \||
# \_/  \|\_/ \|\_/\_/  \| MAIN SCRIPT

if __name__ == "__main__":
    
    main()