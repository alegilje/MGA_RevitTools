# encoding: utf-8
""" 
Author Alexander Gilje
title: Set MUA Areal
Date: 26.03.2025
"""
#  _  _      ____  ____  ____  _____ 
# / \/ \__/|/  __\/  _ \/  __\/__ __\
# | || |\/|||  \/|| / \||  \/|  / \  
# | || |  |||  __/| \_/||    /  | |  
# \_/\_/  \|\_/   \____/\_/\_\  \_/ IMPORTS
#----------------------------------STANDARD LIBRARY IMPORTS----------------------------------#
import os, wpf, clr
clr.AddReference("System")
from System.Windows import Window, Visibility
from System.ComponentModel import CancelEventArgs
from System.Windows.Controls import CheckBox
from pyrevit import revit, DB

from Autodesk.Revit.DB import BuiltInCategory, BuiltInParameter, FilteredElementCollector, FillPatternElement, Color, OverrideGraphicSettings, ElementType, FilledRegion, FilledRegionType, ElementId, Element
from Autodesk.Revit.UI import\
    UIApplication

from tools._transactions import revit_transaction

#  ____  ____  ____  ____  _____ ____  _____  _  _____ ____ 
# /  __\/  __\/  _ \/  __\/  __//  __\/__ __\/ \/  __// ___\
# |  \/||  \/|| / \||  \/||  \  |  \/|  / \  | ||  \  |    \
# |  __/|    /| \_/||  __/|  /_ |    /  | |  | ||  /_ \___ |
# \_/   \_/\_\\____/\_/   \____\\_/\_\  \_/  \_/\____\\____/ POPERTIES

#---------------------------------------FORM PROPERTIES--------------------------------------#
# INPUT
@property
def UI_seksjon_list(self):
    return self.UI_seksjon_list

def UI_ok_button(self):
    return self.UI_ok_button

#  _     ____  ____  _  ____  ____  _     _____ ____ 
# / \ |\/  _ \/  __\/ \/  _ \/  __\/ \   /  __// ___\
# | | //| / \||  \/|| || / \|| | //| |   |  \  |    \
# | \// | |-|||    /| || |-||| |_\\| |_/\|  /_ \___ |
# \__/  \_/ \|\_/\_\\_/\_/ \|\____/\____/\____\\____/ VARIABLES

uidoc = __revit__.ActiveUIDocument         # noqa
doc = revit.doc
view = revit.active_view

colors = ["0,186,196,140",
    "0,249,226,127",
    "0,249,137,114",
    "0,168,206,226",
    "0,237,160,79",
    "0,200,140,100",
    "0,200,200,200"]
#  _____ _     _      ____  _____  _  ____  _      ____ 
# /    // \ /\/ \  /|/   _\/__ __\/ \/  _ \/ \  /|/ ___\
# |  __\| | ||| |\ |||  /    / \  | || / \|| |\ |||    \
# | |   | \_/|| | \|||  \__  | |  | || \_/|| | \||\___ |
# \_/   \____/\_/  \|\____/  \_/  \_/\____/\_/  \|\____/ FUNCTIONS

#----------------------------------------MAIN------------------------------------------------#
def main():

    uiapp = UIApplication(__revit__.Application)
    app = Seksjonering(doc, uiapp)
    filled_region_list = []
    filled_regions = FilteredElementCollector(doc, view.Id).OfClass(FilledRegion).WhereElementIsNotElementType().ToElements()
    seksjoner = set()
    for fr in filled_regions:
        fr_type = doc.GetElement(fr.GetTypeId())
        type_name = fr_type.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM).AsString()
        if("Seksjonering" in type_name):
            seksjoner.add(fr.LookupParameter("Seksjon").AsString())
      
    sorted_seksjoner = list(sorted(seksjoner))
    for seksjon in sorted_seksjoner:
        cb = CheckBox()
        cb.Content = seksjon
        cb.IsChecked = True  # Som standard: valgt
        app.list_seksjon.Items.Add(cb)

    app.ShowDialog()
    valgt_seksjoner = []

    for item in app.list_seksjon.Items:
        if item.IsChecked:
            valgt_seksjoner.append(str(item.Content))
    if not valgt_seksjoner:
        print("Ingen seksjoner valgt.")
        return
    color_lookup = dict(zip(sorted_seksjoner,colors))
    solid_fill_id = get_solid_fill_pattern_id(doc)
    
    seksjon = ""
    
    with revit_transaction(doc,"Set color"):

        for fr in filled_regions:
            fr_type = doc.GetElement(fr.GetTypeId())
            type_name = fr_type.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString()

            if "Seksjonering" in type_name:
                seksjon = fr.LookupParameter("Seksjon").AsString()
            if not seksjon or seksjon not in color_lookup:
                continue
            
            color_string = color_lookup[seksjon]
            current_override_param = fr.LookupParameter("Color Override")
            param_to_set = fr.LookupParameter("Color Override")
            if current_override_param and current_override_param.AsString() == color_string:
                continue  # Farge er oppdatert og korrekt            set_param = param_to_set.Set(

            
            if current_override_param and current_override_param.IsReadOnly == False:
                current_override_param.Set(color_string)
            color = parse_color(color_lookup[seksjon])
            ogs = OverrideGraphicSettings()
            ogs.SetSurfaceForegroundPatternId(solid_fill_id)
            ogs.SetSurfaceForegroundPatternColor(color)

            doc.ActiveView.SetElementOverrides(fr.Id, ogs)



    
def get_solid_fill_pattern_id(doc):
    """Returnerer ElementId for solid fill pattern."""
    collector = FilteredElementCollector(doc).OfClass(FillPatternElement)
    for fpe in collector:
        if fpe.GetFillPattern().IsSolidFill:
            return fpe.Id
    raise Exception("Fant ikkje solid fill pattern.")

def parse_color(rgb_string):
    """Tar inn '0,R,G,B' og returnerer Revit Color(R,G,B)."""
    parts = rgb_string.split(',')
    return Color(int(parts[1]), int(parts[2]), int(parts[3]))

#  ____  _     ____  ____  ____  _____ ____ 
# /   _\/ \   /  _ \/ ___\/ ___\/  __// ___\
# |  /  | |   | / \||    \|    \|  \  |    \
# |  \__| |_/\| |-||\___ |\___ ||  /_ \___ |
# \____/\____/\_/ \|\____/\____/\____\\____/ CLASSES

#-----------------------------------FORM CLASS-----------------------------------------------#

class Seksjonering(Window):
    def __init__(self,doc,uiapp):

        path_xaml_file = os.path.join(os.path.dirname(__file__), "FormUI.xaml")
        
        if not os.path.join(os.path.dirname(__file__), "FormUI.xaml"):
            raise FileNotFoundError("XAML file not found at {}".format(path_xaml_file))
        
        # Load form
        wpf.LoadComponent(self, path_xaml_file)
        self.doc = doc
        self.uiapp = uiapp

        self.list_seksjon = self.FindName("UI_seksjon_list")
        self.btn_ok = self.FindName("UI_ok_button")
        self.btn_ok.Click += self.UI_ok_button_Click

        self.list_seksjon = self.FindName("UI_seksjon_list")
        

    
    def UI_ok_button_Click(self, sender, e):
        print("Hello World")
        self.Close()


#  _      ____  _  _     
# / \__/|/  _ \/ \/ \  /|
# | |\/||| / \|| || |\ ||
# | |  ||| |-||| || | \||
# \_/  \|\_/ \|\_/\_/  \| MAIN SCRIPT

if __name__ == "__main__":
    
    main()