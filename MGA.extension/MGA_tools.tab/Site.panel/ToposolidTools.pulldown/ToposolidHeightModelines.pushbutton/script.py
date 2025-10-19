# encoding: utf-8
# -*- coding: utf-8 -*-

import clr
clr.AddReference("RevitAPI")
clr.AddReference("RevitServices")
# Vi trenger List for DirectShape
from System.Collections.Generic import List

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI.Selection import ObjectType, ISelectionFilter
from pyrevit import revit, forms

# --- Globale variabler ---
uidoc = __revit__.ActiveUIDocument
doc = uidoc.Document

def get_3d_view():
    """Finner en egnet 3D-visning for projeksjon."""
    view = doc.ActiveView
    if view and view.ViewType == ViewType.ThreeD and not view.IsTemplate:
        return view
    collector = FilteredElementCollector(doc).OfClass(View3D)
    for v in collector:
        if not v.IsTemplate:
            return v
    return None

class ToposolidSelectionFilter(ISelectionFilter):
    """Lar brukeren kun velge Toposolid-elementer."""
    def AllowElement(self, elem): return isinstance(elem, Toposolid)
    def AllowReference(self, reference, position): return False

class ModelCurveSelectionFilter(ISelectionFilter):
    """Lar brukeren kun velge ModelCurve-elementer."""
    def AllowElement(self, elem): return isinstance(elem, ModelCurve)
    def AllowReference(self, reference, position): return True

def sample_curve_points(curve, spacing_m=1.0):
    """Deler opp en kurve i en serie med punkter."""
    spacing_ft = spacing_m / 0.3048
    length = curve.Length
    points = []
    if length == 0: return []
    num_segments = int(length / spacing_ft)
    if num_segments < 1: num_segments = 1
    for i in range(num_segments + 1):
        parameter = float(i) / float(num_segments)
        points.append(curve.Evaluate(parameter, True))
    return points

def main():
    three_d_view = get_3d_view()
    if not three_d_view:
        forms.alert("Vennligst åpne en 3D-visning før du kjører skriptet.", exitscript=True)
        return

    # === STEG 1: Få input fra bruker ===
    spacing_str = forms.ask_for_string(
        prompt="Oppgi nøyaktighet/punktavstand (meter).\nLavere tall = jevnere linje.",
        title="Draper linjer på Toposolid",
        default="0.5"
    )
    if not spacing_str: return
    try:
        spacing = float(spacing_str)
        if spacing <= 0: raise ValueError
    except ValueError:
        forms.alert("Ugyldig tallformat.", exitscript=True)
        return

    # === STEG 2: Velg elementer ===
    try:
        toposolid_ref = uidoc.Selection.PickObject(ObjectType.Element, ToposolidSelectionFilter(), "Velg en Toposolid")
        selected_toposolid = doc.GetElement(toposolid_ref.ElementId)
        line_refs = uidoc.Selection.PickObjects(ObjectType.Element, ModelCurveSelectionFilter(), "Velg modellinjer som skal draperes")
        model_curve_elements = [doc.GetElement(r.ElementId) for r in line_refs]
    except Exception:
        return # Bruker avbrøt
    if not model_curve_elements: return

    # === STEG 3: Utfør operasjonen ===
    with revit.Transaction("Lag draperte linjer med DirectShape"):
        
        intersector = ReferenceIntersector(selected_toposolid.Id, FindReferenceTarget.Face, three_d_view)
        
        # Opprett en liste for å holde all 3D-geometri
        geometry_list = List[GeometryObject]()
        
        for el in model_curve_elements:
            if not isinstance(el, ModelCurve): continue

            model_line_points = sample_curve_points(el.GeometryCurve, spacing_m=spacing)
            
            projected_points = []
            for point in model_line_points:
                context = intersector.FindNearest(point, XYZ.BasisZ.Negate())
                if context:
                    projected_points.append(context.GetReference().GlobalPoint)
            
            # Lag linjesegmenter og legg dem til i geometri-listen
            for i in range(len(projected_points) - 1):
                p1 = projected_points[i]
                p2 = projected_points[i+1]
                
                if p1.IsAlmostEqualTo(p2): continue
                
                line_geom = Line.CreateBound(p1, p2)
                geometry_list.Add(line_geom)
        
        if geometry_list.Count > 0:
            # Opprett ett enkelt DirectShape-element for å holde alle linjene
            # Vi bruker "Generic Models" kategorien, da den er mest fleksibel
            ds = DirectShape.CreateElement(doc, ElementId(BuiltInCategory.OST_GenericModel))
            ds.Name = "Draperte linjer"
            ds.SetShape(geometry_list)

            forms.alert("Laget {} draperte linjesegmenter i ett nytt 'Generic Model' objekt.".format(geometry_list.Count), title="Suksess")
        else:
            forms.alert("Fant ingen punkter å projisere. Sjekk at linjene er over din Toposolid.", title="Ingen handling utført")

if __name__ == "__main__":
    main()