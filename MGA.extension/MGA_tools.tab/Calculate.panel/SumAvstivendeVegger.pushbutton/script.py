# -*- coding: utf-8 -*-
from Autodesk.Revit.DB import FilteredElementCollector, Dimension, DimensionType, BuiltInParameter
from pyrevit import forms
from Autodesk.Revit.UI import TaskDialog

doc = __revit__.ActiveUIDocument.Document

# Hent alle dimension types og sikre korrekt navn
dimension_types = FilteredElementCollector(doc).OfClass(DimensionType).ToElements()
dimension_type_names = sorted(list(set([
    dt.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString() for dt in dimension_types
])))

# La bruker velge dimension type
selected_type = forms.SelectFromList.show(
    dimension_type_names,
    title="Velg Dimension Type",
    button_name="Summer dimensjoner"
)

# Hvis bruker avbryter
if not selected_type:
    TaskDialog.Show("Avbrutt", "Ingen dimension type ble valgt.")
    script.exit()

# Hent alle dimensjoner og filtrer
all_dimensions = FilteredElementCollector(doc).OfClass(Dimension)
target_dimensions = [
    dim for dim in all_dimensions
    if dim.DimensionType.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString() == selected_type
]

# Summer lengdene
total_length = 0.0
for dim in target_dimensions:
    if dim.Value:
        total_length += dim.Value

# Konverter til meter
total_length_meters = total_length * 0.3048

# Vis resultat
TaskDialog.Show(
    "Resultat",
    "Totallengde for dimensjoner av type '{}':\n{} meter".format(
        selected_type, round(total_length_meters, 2))
)
