# encoding: utf-8
""" 
Author Alexander Gilje
title: Set height lines
Date: 26.03.2025
"""
#  _  _      ____  ____  ____  _____ 
# / \/ \__/|/  __\/  _ \/  __\/__ __\
# | || |\/|||  \/|| / \||  \/|  / \  
# | || |  |||  __/| \_/||    /  | |  
# \_/\_/  \|\_/   \____/\_/\_\  \_/ IMPORTS
#----------------------------------STANDARD LIBRARY IMPORTS----------------------------------#
import os, clr
clr.AddReference("PresentationFramework")
clr.AddReference("PresentationCore")
clr.AddReference("WindowsBase")

from System.Windows import Window

#---------------------------- AUTODESK REVIT AND PYREVIT IMPORTS ----------------------------#
from Autodesk.Revit.DB import Plane, SketchPlane, ModelCurve, Line, Arc, XYZ
from Autodesk.Revit.UI.Selection import ObjectType
from pyrevit import revit, forms

#---------------------------------------CUSTOM IMPORTS---------------------------------------#
from tools._logger import ScriptLogger
from tools._transactions import revit_transaction

#  _     ____  ____  _  ____  ____  _     _____ ____ 
# / \ |\/  _ \/  __\/ \/  _ \/  __\/ \   /  __// ___\
# | | //| / \||  \/|| || / \|| | //| |   |  \  |    \
# | \// | |-|||    /| || |-||| |_\\| |_/\|  /_ \___ |
# \__/  \_/ \|\_/\_\\_/\_/ \|\____/\____/\____\\____/ VARIABLES

uidoc  = __revit__.ActiveUIDocument
doc    = __revit__.ActiveUIDocument.Document

#  _     ____  _____ _____ _  _      _____
# / \   /  _ \/  __//  __// \/ \  /|/  __/
# | |   | / \|| |  _| |  _| || |\ ||| |  _
# | |_/\| \_/|| |_//| |_//| || | \||| |_//
# \____/\____/\____\\____\\_/\_/  \|\____\ LOGGING

logger = ScriptLogger(name='SetHeightModelLine', log_to_file=True)

#  _____ _     _      ____  _____  _  ____  _      ____ 
# /    // \ /\/ \  /|/   _\/__ __\/ \/  _ \/ \  /|/ ___\
# |  __\| | ||| |\ |||  /    / \  | || / \|| |\ |||    \
# | |   | \_/|| | \|||  \__  | |  | || \_/|| | \||\___ |
# \_/   \____/\_/  \|\____/  \_/  \_/\____/\_/  \|\____/ FUNCTIONS

#----------------------------------------MAIN------------------------------------------------#

def main():
    form = HeightForm()
    form.ShowDialog()
    if form.result:
        z_mm = form.result
        try:
            new_z = float(z_mm) / 304.8  # konverter mm til fot
        except:
            forms.alert("Ugyldig tall.", exitscript=True)

        # La bruker velge ModelCurves
        refs = uidoc.Selection.PickObjects(ObjectType.Element, "Velg model lines/arcs")
        elements = [doc.GetElement(r.ElementId) for r in refs]

        with revit.Transaction("Flytt ModelCurves til ny Z"):
            # Lag nytt plan i riktig høyde
            plane = Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ(0,0,new_z))
            sketchplane = SketchPlane.Create(doc, plane)

            for el in elements:
                if isinstance(el, ModelCurve):
                    curve = el.GeometryCurve

                    if isinstance(curve, Line):
                        # Rett linje
                        start = curve.GetEndPoint(0)
                        end = curve.GetEndPoint(1)
                        new_curve = Line.CreateBound(
                            XYZ(start.X, start.Y, new_z),
                            XYZ(end.X, end.Y, new_z)
                        )

                    elif isinstance(curve, Arc):
                        # Bue
                        start = curve.GetEndPoint(0)
                        end = curve.GetEndPoint(1)
                        mid = curve.Evaluate(0.5, True)
                        new_curve = Arc.Create(
                            XYZ(start.X, start.Y, new_z),
                            XYZ(end.X, end.Y, new_z),
                            XYZ(mid.X, mid.Y, new_z)
                        )
                    else:
                        continue

                    # Lag ny ModelCurve på ønsket plan
                    doc.Create.NewModelCurve(new_curve, sketchplane)
                    # Slett gammel
                    doc.Delete(el.Id)

#  ____  _     ____  ____  ____  _____ ____ 
# /   _\/ \   /  _ \/ ___\/ ___\/  __// ___\
# |  /  | |   | / \||    \|    \|  \  |    \
# |  \__| |_/\| |-||\___ |\___ ||  /_ \___ |
# \____/\____/\_/ \|\____/\____/\____\\____/ CLASSES
import wpf
class HeightForm(Window):
    def __init__(self):
        path_xaml_file = os.path.join(os.path.dirname(__file__), "FormUI.xaml")
        if not os.path.exists(path_xaml_file):
            raise FileNotFoundError("XAML file not found at {}".format(path_xaml_file))

        # Last inn XAML
        wpf.LoadComponent(self, path_xaml_file)

        # Event handlers
        self.OkButton.Click += self.on_ok
        self.CancelButton.Click += self.on_cancel
        self.result = None

    def on_ok(self, sender, args):
        try:
            self.result = float(self.ZBox.Text)
            self.Close()
        except:
            from pyrevit import forms
            forms.alert("Ugyldig tall!")

    def on_cancel(self, sender, args):
        self.Close()

#  _      ____  _  _     
# / \__/|/  _ \/ \/ \  /|
# | |\/||| / \|| || |\ ||
# | |  ||| |-||| || | \||
# \_/  \|\_/ \|\_/\_/  \| MAIN SCRIPT

if __name__ == "__main__":
    
    main()