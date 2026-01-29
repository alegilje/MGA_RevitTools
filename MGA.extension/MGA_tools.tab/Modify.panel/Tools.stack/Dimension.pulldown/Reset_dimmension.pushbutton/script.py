
# encoding: utf-8
"""
pyRevit (Revit 2026)  Reset dimensjonstekst

Mål:
1) Flytt tekster på mållinjer tilbake til orinal posisjon

"""


from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory


from tools._transactions import revit_groupTransaction, revit_transaction


uidoc = __revit__.ActiveUIDocument
doc   = uidoc.Document
view  = uidoc.ActiveView
view_scale = view.Scale


def main():
    dims = (FilteredElementCollector(doc, view.Id)
            .OfCategory(BuiltInCategory.OST_Dimensions)
            .WhereElementIsNotElementType()
            .ToElements())


    # PASS A: plan moves for "does not fit"
    with revit_groupTransaction(doc, "Reset"):
        for dim in dims:
            if dim.Segments.Size > 1:
                with revit_transaction(doc, "Reset Dim"):
                    for i in dim.Segments:
                        try:
                            i.ResetTextPosition()
                        except Exception as e:
                            print(e)
            else:
                with revit_transaction(doc, "Reset Dim"):
                    try:
                        dim.ResetTextPosition()
                    except Exception as e:
                        print(e)

if __name__ == "__main__":
    main()
