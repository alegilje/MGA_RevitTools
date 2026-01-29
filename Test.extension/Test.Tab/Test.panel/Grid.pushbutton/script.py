# -*- coding: utf-8 -*-
# pyRevit | Revit 2023–2026
# Clip all straight Grids to the active view Crop Region
# DEBUG PRINTS — avoid .IntegerValue (print ElementId directly); correct VS arg order

from pyrevit import revit
from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, Grid, XYZ, Line,
    DatumExtentType, DatumEnds
)
import traceback

uidoc = __revit__.ActiveUIDocument
doc   = uidoc.Document
view  = uidoc.ActiveView

EPS = 1e-9

def _make_unbounded_dir(p0, p1):
    d = p1 - p0
    try:
        d = d.Normalize()
    except:
        return None, None
    mid = p0 + d * (p0.DistanceTo(p1) * 0.5)
    return mid, d

def _solve_intersections_in_crop_space(O, D, bb):
    xmin, ymin, zmin = bb.Min.X, bb.Min.Y, bb.Min.Z
    xmax, ymax, zmax = bb.Max.X, bb.Max.Y, bb.Max.Z
    pts = []
    if abs(D.X) > EPS:
        for x in (xmin, xmax):
            t = (x - O.X) / D.X
            y = O.Y + t * D.Y
            if (ymin - EPS) <= y <= (ymax + EPS):
                z = O.Z + t * D.Z
                pts.append(XYZ(x, y, z))
    if abs(D.Y) > EPS:
        for y in (ymin, ymax):
            t = (y - O.Y) / D.Y
            x = O.X + t * D.X
            if (xmin - EPS) <= x <= (xmax + EPS):
                z = O.Z + t * D.Z
                pts.append(XYZ(x, y, z))
    uniq = []
    for p in pts:
        if all(p.DistanceTo(q) >= 1e-6 for q in uniq):
            uniq.append(p)
    return uniq

def _clip_line_to_crop(line, bb):
    T   = bb.Transform
    Tin = T.Inverse
    a = Tin.OfPoint(line.GetEndPoint(0))
    b = Tin.OfPoint(line.GetEndPoint(1))
    O, D = _make_unbounded_dir(a, b)
    if O is None:
        return None, a, b, [], None, None
    pts_cs = _solve_intersections_in_crop_space(O, D, bb)
    if len(pts_cs) < 2:
        return None, a, b, pts_cs, O, D
    def _param(p):
        v = p - O
        return v.X*D.X + v.Y*D.Y + v.Z*D.Z
    pts_cs.sort(key=_param)
    pA = T.OfPoint(pts_cs[0])
    pB = T.OfPoint(pts_cs[-1])
    if pA.IsAlmostEqualTo(pB):
        return None, a, b, pts_cs, O, D
    return Line.CreateBound(pA, pB), a, b, pts_cs, O, D

def _get_grids_in_view(v):
    return FilteredElementCollector(doc, v.Id)\
        .OfCategory(BuiltInCategory.OST_Grids)\
        .WhereElementIsNotElementType()\
        .ToElements()

def _force_vs_per_end(g, v):
    """Correct signature: SetDatumExtentType(DatumEnds end, View view, DatumExtentType type)"""
    ok = True
    try:
        g.SetDatumExtentType(DatumEnds.End0, v, DatumExtentType.ViewSpecific)
    except Exception as ex0:
        print("   End0 VS FAIL: {}".format(ex0)); ok = False
    try:
        g.SetDatumExtentType(DatumEnds.End1, v, DatumExtentType.ViewSpecific)
    except Exception as ex1:
        print("   End1 VS FAIL: {}".format(ex1)); ok = False
    try:
        e0 = g.GetDatumExtentType(DatumEnds.End0, v)
        e1 = g.GetDatumExtentType(DatumEnds.End1, v)
        print("   Extents now: End0={}, End1={}".format(e0, e1))
        ok = ok and (e0 == DatumExtentType.ViewSpecific and e1 == DatumExtentType.ViewSpecific)
    except Exception as exq:
        print("   Query VS FAIL: {}".format(exq)); ok = False
    return ok

def _get_curve_vs(g, v):
    try: return g.GetCurveInView(DatumExtentType.ViewSpecific, v)
    except: return None

def _get_curve_model(g, v):
    try: return g.GetCurveInView(DatumExtentType.Model, v)
    except: return None

# --- main with prints ---
print("=== Clip Grids to Crop (fix VS arg order / debug v2) ===")
bb = view.CropBox
if not bb:
    print("Ingen CropBox i denne visninga. Avbryt.")
    raise SystemExit
print("View: {} (Id={})".format(view.Name, view.Id))  # avoid .IntegerValue
print("CropBox Min=({:.3f},{:.3f},{:.3f}) Max=({:.3f},{:.3f},{:.3f})".format(
    bb.Min.X, bb.Min.Y, bb.Min.Z, bb.Max.X, bb.Max.Y, bb.Max.Z
))

grids = _get_grids_in_view(view)
print("Fant {} grids i visninga.".format(len(grids)))

processed = 0
skipped_non_line = 0
skipped_no_clip = 0
errors = 0

with revit.Transaction('Clip Grids to Crop (VS per-end)'):
    for g in grids:
        try:
            # Avoid .IntegerValue; print ElementId directly
            print("\n-- Grid {} '{}'".format(g.Id, getattr(g, 'Name', '<ukjent>')))
            crv = g.Curve
            if not isinstance(crv, Line):
                print("   Hoppar: ikkje lineær (arc).")
                skipped_non_line += 1
                continue

            mcurve = _get_curve_model(g, view)
            vscurve = _get_curve_vs(g, view)
            print("   Has Model curve? {} | Has VS curve? {}".format(bool(mcurve), bool(vscurve)))
            if mcurve:
                p0 = mcurve.GetEndPoint(0); p1 = mcurve.GetEndPoint(1)
                print("   Model P0=({:.3f},{:.3f},{:.3f})  P1=({:.3f},{:.3f},{:.3f})".format(
                    p0.X, p0.Y, p0.Z, p1.X, p1.Y, p1.Z
                ))

            seg, a_cs, b_cs, pts_cs, O, D = _clip_line_to_crop(crv, bb)
            print("   Intersections (crop-space): {}".format(len(pts_cs)))
            for i, ip in enumerate(pts_cs):
                print("     [{}] ({:.3f},{:.3f},{:.3f})".format(i, ip.X, ip.Y, ip.Z))
            if not seg:
                print("   → hoppar (ingen gyldig klipp)")
                skipped_no_clip += 1
                continue
            pa = seg.GetEndPoint(0); pb = seg.GetEndPoint(1)
            print("   Trimma segment A=({:.3f},{:.3f},{:.3f})  B=({:.3f},{:.3f},{:.3f})".format(
                pa.X, pa.Y, pa.Z, pb.X, pb.Y, pb.Z
            ))

            made_vs = _force_vs_per_end(g, view)
            print("   Force VS per-end result: {}".format(made_vs))

            set_ok = False
            try:
                g.SetCurveInView(DatumExtentType.ViewSpecific, view, seg)
                print("   >>> SetCurveInView(ViewSpecific) OK")
                set_ok = True
            except Exception as ex_vs:
                print("   SetCurveInView(ViewSpecific) FAIL: {}".format(ex_vs))
                try:
                    g.SetCurveInView(DatumExtentType.Model, view, seg)
                    print("   >>> SetCurveInView(Model) OK (fallback)")
                    set_ok = True
                except Exception as ex_md:
                    print("   SetCurveInView(Model) FAIL: {}".format(ex_md))

            if set_ok:
                processed += 1
            else:
                print("   → hoppar (klarte ikkje SetCurveInView).")
                skipped_no_clip += 1

        except Exception as ex:
            print("   FEIL: {}".format(ex))
            try:
                print(traceback.format_exc())
            except:
                pass
            errors += 1

print("\n=== Oppsummering ===")
print(("Prosesserte grids:", processed))
print(("Hoppa (ikkje-lineære):", skipped_non_line))
print(("Hoppa (ingen klipp/VS):", skipped_no_clip))
print(("Feil:", errors))
