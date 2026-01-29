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
from Autodesk.Revit.DB import Plane, SketchPlane, ModelCurve, Line, Arc, XYZ, UnitUtils, UnitTypeId
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
    mc = None
    p1z_mm = 0.0
    p2z_mm = 0.0
    try:
        sel_ids = list(uidoc.Selection.GetElementIds())
        if len(sel_ids) == 1:
            el = doc.GetElement(sel_ids[0])
            if isinstance(el, ModelCurve):
                mc = el
                crv = mc.GeometryCurve
                p1 = crv.GetEndPoint(0)
                p2 = crv.GetEndPoint(1)
                p1z_mm = UnitUtils.ConvertFromInternalUnits(p1.Z, UnitTypeId.Millimeters)
                p2z_mm = UnitUtils.ConvertFromInternalUnits(p2.Z, UnitTypeId.Millimeters)
    except:
        pass
    # Require that the user has selected a ModelCurve (linje) first
    if mc is None:
        forms.alert(u"Vennligst velg én modellinje (ModelCurve) før du kjører verktøyet.", exitscript=True)
        return

    dlg = ZDialog(p1z_mm, p2z_mm)
    if dlg.show():
        new_p1_mm = dlg.p1_mm
        new_p2_mm = dlg.p2_mm

        # --- Bruk verdiene (mm -> internal feet) ---
        new_p1_ft = UnitUtils.ConvertToInternalUnits(new_p1_mm, UnitTypeId.Millimeters)
        new_p2_ft = UnitUtils.ConvertToInternalUnits(new_p2_mm, UnitTypeId.Millimeters)

        if mc:
            # Flytt endepunkter på valgt ModelCurve til angitt Z
            crv = mc.GeometryCurve
            p1 = crv.GetEndPoint(0)
            p2 = crv.GetEndPoint(1)
            p1n = XYZ(p1.X, p1.Y, new_p1_ft)
            p2n = XYZ(p2.X, p2.Y, new_p2_ft)

            with revit.Transaction('Sett Z på modellinje'):
                try:
                    # Skap ny kurve med samme type
                    new_crv = Line.CreateBound(p1n, p2n)
                    mc.SetGeometryCurve(new_crv, True)
                except:
                    # fallback for ikke-lineære kurver: flytt ved hjelp av Translate
                    dz1 = new_p1_ft - p1.Z
                    dz2 = new_p2_ft - p2.Z
                    # Hvis ulik Z, gjør en enkel rekonstruksjon:
                    new_crv = Line.CreateBound(XYZ(p1.X, p1.Y, p1.Z + dz1),
                                                XYZ(p2.X, p2.Y, p2.Z + dz2))
                    mc.SetGeometryCurve(new_crv, True)

#  ____  _     ____  ____  ____  _____ ____ 
# /   _\/ \   /  _ \/ ___\/ ___\/  __// ___\
# |  /  | |   | / \||    \|    \|  \  |    \
# |  \__| |_/\| |-||\___ |\___ ||  /_ \___ |
# \____/\____/\_/ \|\____/\____/\____\\____/ CLASSES
import wpf
class ZDialog(forms.WPFWindow):
    def __init__(self, p1_init, p2_init):
        path_xaml_file = os.path.join(os.path.dirname(__file__), "FormUI.xaml")
        if not os.path.exists(path_xaml_file):
            raise FileNotFoundError("XAML file not found at {}".format(path_xaml_file))
        wpf.LoadComponent(self, path_xaml_file)
        # init verdier
        self.P1Box.Text = ('{0:.3f}'.format(p1_init)).rstrip('0').rstrip('.')
        self.P2Box.Text = ('{0:.3f}'.format(p2_init)).rstrip('0').rstrip('.')
        # hvis P1==P2 => default "samme"
        if abs(p1_init - p2_init) < 1e-6:
            self.SameAsP1.IsChecked = True
            self.P2Box.IsEnabled = False
            self.P2Box.Text = self.P1Box.Text
        # events
        self.SameAsP1.Checked += self._sync_on
        self.SameAsP1.Unchecked += self._sync_off
        self.P1Box.TextChanged += self._p1_changed
        self.OkButton.Click += self._ok
        self.CancelButton.Click += self._cancel

    def _sync_on(self, sender, args):
        self.P2Box.IsEnabled = False
        self.P2Box.Text = self.P1Box.Text

    def _sync_off(self, sender, args):
        self.P2Box.IsEnabled = True

    def _p1_changed(self, sender, args):
        if self.SameAsP1.IsChecked:
            self.P2Box.Text = self.P1Box.Text

    def _ok(self, sender, args):
        try:
            self.p1_mm = float(self.P1Box.Text.replace(',', '.'))
            self.p2_mm = float(self.P2Box.Text.replace(',', '.')) if not self.SameAsP1.IsChecked else self.p1_mm
            self.DialogResult = True
        except:
            forms.alert('Ugyldig tall. Bruk punktum eller komma.', exitscript=False)

    def _cancel(self, sender, args):
        self.DialogResult = False

#  _      ____  _  _     
# / \__/|/  _ \/ \/ \  /|
# | |\/||| / \|| || |\ ||
# | |  ||| |-||| || | \||
# \_/  \|\_/ \|\_/\_/  \| MAIN SCRIPT

if __name__ == "__main__":
    
    main()