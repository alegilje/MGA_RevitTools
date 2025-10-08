# -*- coding: utf-8 -*-
# Author: Alexander Gilje (refaktor)
# Date: 30.09.2025

#  _  _      ____  ____  ____  _____ 
# / \/ \__/|/  __\/  _ \/  __\/__ __\
# | || |\/|||  \/|| / \||  \/|  / \  
# | || |  |||  __/| \_/||    /  | |  
# \_/\_/  \|\_/   \____/\_/\_\  \_/ IMPORTS
#---------------------------------- STANDARD LIBRARY ----------------------------------#

import os ,re ,clr

from System.Collections.Generic import List as ClrList
from System import Enum
clr.AddReference("PresentationFramework")
clr.AddReference("PresentationCore")
clr.AddReference("WindowsBase")
# (valgfritt for XamlReader, men ofte nyttig)
clr.AddReference("System.Xaml")
from System.Windows import Thickness
from System.Windows.Controls import ListBoxItem, CheckBox
from System.Windows.Markup import XamlReader

# WinForms mappevelger
clr.AddReference("System.Windows.Forms")

from System.Windows.Forms import FolderBrowserDialog, DialogResult
#----------------------- AUTODESK REVIT / PYREVIT IMPORTS -----------------------------#
from pyrevit import revit, DB, forms
from Autodesk.Revit.DB import *



#  _     ____  ____  _  ____  ____  _     _____ ____ 
# / \ |\/  _ \/  __\/ \/  _ \/  __\/ \   /  __// ___\
# | | //| / \||  \/|| || / \|| | //| |   |  \  |    \
# | \// | |-|||    /| || |-||| |_\\| |_/\|  /_ \___ |
# \__/  \_/ \|\_/\_\\_/\_/ \|\____/\____/\____\\____/ VARIABLES
#----------------------------- GLOBALS / CONTEXT --------------------------------------#
uidoc = __revit__.ActiveUIDocument
doc   = uidoc.Document
view  = revit.active_view


#  _____ _     _      ____  _____  _  ____  _      ____ 
# /    // \ /\/ \  /|/   _\/__ __\/ \/  _ \/ \  /|/ ___\
# |  __\| | ||| |\ |||  /    / \  | || / \|| |\ |||    \
# | |   | \_/|| | \|||  \__  | |  | || \_/|| | \||\___ |
# \_/   \____/\_/  \|\____/  \_/  \_/\____/\_/  \|\____/ FUNCTIONS

def _lb_item(text, tag):
    it = ListBoxItem()
    it.Content = text
    it.Tag = tag
    return it

def main():
    
    xaml_path = os.path.join(os.path.dirname(__file__), "FormUI.xaml")
    DwgExportWindow(xaml_path).ShowDialog()

def _lookup_param(element, param_name):
    try:
        return element.LookupParameter(param_name).AsString()
    except:
        return None
    

#  ____  _     ____  ____  ____  _____ ____ 
# /   _\/ \   /  _ \/ ___\/ ___\/  __// ___\
# |  /  | |   | / \||    \|    \|  \  |    \
# |  \__| |_/\| |-||\___ |\___ ||  /_ \___ |
# \____/\____/\_/ \|\____/\____/\____\\____/ CLASSES

#-----------------------------------FORM CLASS-----------------------------------------------#
class DwgExportWindow(forms.WPFWindow):
    def __init__(self, xaml_path):
        forms.WPFWindow.__init__(self, xaml_path)
        self.ExportBtn.IsEnabled = False

        # events
        self.SheetSetsList.SelectionChanged += self._on_set_selected
        self.SheetsList.SelectionChanged += self._on_sheets_selected
        self.CancelBtn.Click += self._on_cancel
        self.ExportBtn.Click += self._on_export

        self._populate()

    # ---------- helpers ----------
    def _safe(self, s, default="-"):
        s = (s or default).strip()
        s = re.sub(r'[\\/:*?"<>|]', "-", s)
        s = s.rstrip(". ")
        return s or default

    def _lookup_param(self, element, param_name):
        p = element.LookupParameter(param_name)
        if p:
            try:
                v = p.AsString()
                if v:
                    return v
            except:
                pass
        return None

    def _sheet_basename(self, sheet):
        proj_info = doc.ProjectInformation
        project_number = self._safe(getattr(proj_info, "Number", None))
        s_type         = "M2"
        s_organisasjon = self._safe(self._lookup_param(sheet, "Kode Organisasjon"))
        s_etasje       = self._safe(self._lookup_param(sheet, "Kode Etasje/løpenummer"))
        s_disiplin     = self._safe(self._lookup_param(sheet, "Kode Disiplin"))
        s_number       = self._safe(self._lookup_param(sheet, "Sheet Number") or getattr(sheet, "SheetNumber", None))
        return u"{}-{}-{}-{}-{}-{}".format(project_number, s_type, s_organisasjon, s_etasje, s_disiplin, s_number)

    # --- UI data ---
    def _populate(self):
        # 1) Sheet sets
        self.SheetSetsList.Items.Clear()
        for vss in FilteredElementCollector(doc).OfClass(ViewSheetSet):
            self.SheetSetsList.Items.Add(_lb_item(vss.Name, vss))

        # 2) Sheets som avkryssingsbokser
        self.SheetsList.Items.Clear()
        sheets = FilteredElementCollector(doc) \
            .OfCategory(BuiltInCategory.OST_Sheets) \
            .WhereElementIsNotElementType() \
            .ToElements()

        def _key(s):
            try:
                return (s.SheetNumber, s.Name)
            except:
                return ("", "")

        for s in sorted(list(sheets), key=_key):
            label = u"{0}  {1}".format(s.SheetNumber, s.Name)
            cb = CheckBox()
            cb.Content = label
            cb.Tag = s.Id                 # behold ElementId
            cb.Margin = Thickness(2, 1, 2, 1)
            # Oppdater Export-knappen når bruker krysser av/på
            cb.Checked += self._on_sheet_checkbox_toggled
            cb.Unchecked += self._on_sheet_checkbox_toggled
            self.SheetsList.Items.Add(cb)


    # --- Events ---
    def _on_set_selected(self, sender, args):
        if self.SheetSetsList.SelectedItem is None:
            any_checked = any(getattr(it, "IsChecked", False) for it in self.SheetsList.Items)
            self.ExportBtn.IsEnabled = any_checked
            return

        vss = self.SheetSetsList.SelectedItem.Tag  # ViewSheetSet
        ids_in_set = set(v.Id for v in vss.Views)

        # Kryss av de som finnes i settet, fjern kryss på andre
        for i in range(self.SheetsList.Items.Count):
            cb = self.SheetsList.Items[i]          # CheckBox
            cb.IsChecked = (cb.Tag in ids_in_set)

        any_checked = any(getattr(it, "IsChecked", False) for it in self.SheetsList.Items)
        self.ExportBtn.IsEnabled = any_checked or (self.SheetSetsList.SelectedItem is not None)

    def _on_sheet_checkbox_toggled(self, sender, args):
        any_checked = any(getattr(it, "IsChecked", False) for it in self.SheetsList.Items)
        has_set = self.SheetSetsList.SelectedItem is not None
        self.ExportBtn.IsEnabled = any_checked or has_set



    def _on_sheets_selected(self, sender, args):
        # Hvis bruker manuelt markerer sheets, lar vi det være gyldig valg også uten sheet set
        has_manual = self.SheetsList.SelectedItems.Count > 0
        has_set = self.SheetSetsList.SelectedItem is not None
        self.ExportBtn.IsEnabled = has_manual or has_set

    def _on_cancel(self, sender, args):
        self.Close()

    def _on_export(self, sender, args):
        # 1) Samle ElementId-er fra avkryssede checkbokser
        ids = ClrList[ElementId]()
        for i in range(self.SheetsList.Items.Count):
            cb = self.SheetsList.Items[i]          # CheckBox
            if getattr(cb, "IsChecked", False):
                ids.Add(cb.Tag)                    # Tag = ElementId

        # 2) Hvis ingen krysset av, men sheet set er valgt → bruk settet
        if ids.Count == 0 and self.SheetSetsList.SelectedItem is not None:
            vss = self.SheetSetsList.SelectedItem.Tag
            for v in vss.Views:                    # v er View/ViewSheet
                ids.Add(v.Id)

        if ids.Count == 0:
            forms.alert("Kryss av ett/flere ark, eller velg et sheet set.", warn_icon=True)
            return

        # 3) Velg eksportmappe
        dlg = FolderBrowserDialog()
        dlg.Description = "Velg mappe for DWG-eksport"
        if dlg.ShowDialog() != DialogResult.OK:
            return
        out_folder = dlg.SelectedPath

        # 4) Eksporter ett og ett sheet med egendefinert filnavn
        opts = DWGExportOptions()
        try:
            opts.MergedViews = True
            opts.FileVersion = ACADVersion.R2013
            opts.SharedCoords = True             # ingen Xref for views på ark
        except:
            pass

        exported = 0
        for eid in ids:
            el = doc.GetElement(eid)
            if not isinstance(el, ViewSheet):      # hopp over eventuelle rene views
                continue
            base_name = self._sheet_basename(el)   # uten .dwg
            one = ClrList[ElementId]()
            one.Add(eid)
            if doc.Export(out_folder, base_name, one, opts):
                exported += 1

        forms.alert(u"DWG-eksport fullført. {} filer skrevet til:\n{}".format(exported, out_folder),
                    title="Done")
        self.Close()




#  _      ____  _  _     
# / \__/|/  _ \/ \/ \  /|
# | |\/||| / \|| || |\ ||
# | |  ||| |-||| || | \||
# \_/  \|\_/ \|\_/\_/  \| MAIN SCRIPT

if __name__ == "__main__":
    main()