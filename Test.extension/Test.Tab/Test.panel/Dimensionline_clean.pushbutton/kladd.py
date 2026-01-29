
# encoding: utf-8
""" 
Author Alexander Gilje
title: Clean dimmension lines
Date: 27.01.2026
"""
#  _  _      ____  ____  ____  _____ 
# / \/ \__/|/  __\/  _ \/  __\/__ __\
# | || |\/|||  \/|| / \||  \/|  / \  
# | || |  |||  __/| \_/||    /  | |  
# \_/\_/  \|\_/   \____/\_/\_\  \_/ IMPORTS
#----------------------------------STANDARD LIBRARY IMPORTS----------------------------------#
import math

import clr
clr.AddReference("System.Globalization")
from System.Globalization import CultureInfo


#---------------------------- AUTODESK REVIT AND PYREVIT IMPORTS ----------------------------#

from pyrevit import revit
from Autodesk.Revit.DB import \
    BuiltInCategory, \
    BuiltInParameter, \
    Dimension, \
    DimensionStyleType, \
    FilteredElementCollector,\
    LabelUtils, \
    SpotDimension, \
    Transaction, \
    UnitTypeId, \
    UnitUtils

#  _     ____  ____  _  ____  ____  _     _____ ____ 
# / \ |\/  _ \/  __\/ \/  _ \/  __\/ \   /  __// ___\
# | | //| / \||  \/|| || / \|| | //| |   |  \  |    \
# | \// | |-|||    /| || |-||| |_\\| |_/\|  /_ \___ |
# \__/  \_/ \|\_/\_\\_/\_/ \|\____/\____/\____\\____/ VARIABLES
#------------------------------------ DOCUMENT VARIABLES ------------------------------------#

uidoc = __revit__.ActiveUIDocument
doc = uidoc.Document
view = uidoc.ActiveView
view_scale = view.Scale   

CI = CultureInfo.CurrentCulture

#--------------------------------- USER SETTINGS VARIABLES ---------------------------------#

PADDING_MM = 2.0                # ekstra luft når vi sjekkar "passar i segment"
CHAR_FACTOR = 0.68              # ca snitt bokstavbreidde = CHAR_FACTOR * teksthøgde
ROW_TOL_MM_MIN = 1.0            # toleranse for å gruppere tekstar på same "rad"
MOVED_THR_MIN_MM = 1.0          # minste terskel for å rekne tekst som "flytta"
MOVED_THR_TEXT_FRAC = 0.15      # terskel som del av text_height_mm
OVERLAP_STEP_TEXT_FRAC = 1.20   # ekstra "ut" ved overlap, som del av text_height_mm
MAX_OVERLAP_ITERS = 10


#  _____ _     _      ____  _____  _  ____  _      ____ 
# /    // \ /\/ \  /|/   _\/__ __\/ \/  _ \/ \  /|/ ___\
# |  __\| | ||| |\ |||  /    / \  | || / \|| |\ |||    \
# | |   | \_/|| | \|||  \__  | |  | || \_/|| | \||\___ |
# \_/   \____/\_/  \|\____/  \_/  \_/\____/\_/  \|\____/ FUNCTIONS

#----------------------------------------MAIN------------------------------------------------#
def main():

    dimension_lines = get_element(doc, view, uidoc)
    
    move_jobs = []
    overlap_dims = []
    not_fit = []
    # PASS A: plan moves for "does not fit"
    for dim in dimension_lines:
        if not f_can_touch_dimension(dim):
            continue
        
        accuracy, unit_symbol, text_height_mm, unit_label = get_dim_units(dim)
        count_decimals = decimals_from_accuracy(accuracy) if accuracy else None

        seg_count = f_get_seg_count(dim)

        if seg_count > 0:
            # Bygg info først – ingen flytting her
            baseline = compute_baseline_nearest_line(dim, view)  # kan stå, men trengst ikkje lenger
            items = build_text_items(dim, view, text_height_mm, count_decimals, unit_label, unit_symbol)

            # Planlegg flytting basert på overlapp-klynger + "ikkje får plass"
            planned = plan_multiseg_moves(dim, view, text_height_mm, items, padding_mm=PADDING_MM)
            if planned:
                move_jobs.extend(planned)

            # valfritt: køyr resolve_overlaps etterpå som "safety"
            overlap_dims.append(dim)
        
        else:
            if is_single_dim_manually_moved(dim):
                continue

            dim_text, text_width_mm, dim_length_mm = collect_dim_seg_info(dim, text_height_mm, count_decimals, unit_label, unit_symbol)

            if text_width_mm > dim_length_mm:
                base = get_dimension_base_point(dim)
                if base is None:
                    continue
                v = offset_vector_up_side(dim, view, text_height_mm, text_width_mm, side_sign=1)
                target = base + v
                move_jobs.append((dim, target))

    # PASS B: apply moves (one transaction)
    if move_jobs:
        with revit.Transaction("Auto-fit dimension text"):
            for obj, target in move_jobs:
                try:
                    move_text(obj, target)
                    
                except Exception as e:
                    print("Move failed:", e)                

    # PASS C: resolve overlaps (text-text) (second transaction)
    # Only on multi-segment dims (and only those we may have modified)
    if overlap_dims:
        with revit.Transaction("Resvolve dimension text overlaps"):
            for dim in overlap_dims:
                try:
                    accuracy, unit_symbol, text_height_mm, unit_label = get_dim_units(dim)
                    count_decimals = decimals_from_accuracy(accuracy) if accuracy else None
                    resolve_overlaps(dim, view, text_height_mm, items, padding_mm=PADDING_MM)
                    dim.HasLeader = False
                except Exception as e:
                    print("Overlap resolve failed:",e)

# ---------------------------------------- SELECTION ---------------------------------------- #
def get_element(doc, view, uidoc):
    sel_ids = list(uidoc.Selection.GetElementIds())

    # Case 1: user has selected something -> only use selected dimensions
    if sel_ids:
        dims = []
        for eid in sel_ids:
            el = doc.GetElement(eid)
            # plukk berre dimensjonar (inkl. MultiSegment dimension)
            if isinstance(el, Dimension):
                dims.append(el)
        return dims

    # Case 2: nothing selected -> all dimensions in active view
    return (FilteredElementCollector(doc, view.Id)  # view-scoped collector :contentReference[oaicite:0]{index=0}
            .OfCategory(BuiltInCategory.OST_Dimensions)
            .WhereElementIsNotElementType()
            .ToElements())
#----------------------------------GEOMETRY HELPERS------------------------------------------#

def get_dim_frame(dim, view):
    along = dim.Curve.Direction.Normalize()
    view_dir = view.ViewDirection.Normalize()
    up = view_dir.CrossProduct(along).Normalize()
    origin = dim.Curve.Origin
    return origin, along, up

def _up_pos_mm(dim, view, p):
    origin, along, up = get_dim_frame(dim, view)
    u_ft = _dot(p-origin, up)
    return UnitUtils.ConvertFromInternalUnits(u_ft, UnitTypeId.Millimeters)

def along_pos_mm(dim, view, p):
    origin, along, up = get_dim_frame(dim, view)
    x_ft = _dot(p - origin, along)
    return UnitUtils.ConvertFromInternalUnits(x_ft, UnitTypeId.Millimeters)

def _dot(a, b):
    return a.X * b.X + a.Y * b.Y + a.Z * b.Z

def mm_to_internal(mm):
    return UnitUtils.ConvertToInternalUnits(mm, UnitTypeId.Millimeters)

#---------------------------------FILTERING / GUARDS-----------------------------------------#

def f_can_touch_dimension(dim):
    # Skip SpotDimensions (includes SpotSlope)
    if isinstance(dim, SpotDimension):
        return False
    
    # Skip Ordinate dimensions    
    try:
        dt = doc.GetElement(dim.GetTypeId())
        if dt and dt.StyleType == DimensionStyleType.Ordinate:
            return False
    except:
        pass

    # Skip Equality dimensions
    try:
        eq = getattr(dim, "EqualityFormula", None)
        if eq and str(eq).strip():
            return False
    except:
        pass

    # Must be linear dimension (needs Curve.Direction)
    try:
        _ = dim.Curve.Direction
    except:
        pass

    return True

def f_can_touch_segment(seg):
    # Skip Equality on segment if present
    try:
        eq = getattr(seg, "EqualityFormula", None)
        if eq and str(eq).strip():
            return False
    except:
        pass
    return True

def f_get_seg_count(dim):
    try:
        return dim.NumberOfSegments
    except:
        try:
            return dim.Segments.Size
        except:
            return 0

#------------------------------UNIT / FORMAT HELPERS--------------------------------------#

def decimals_from_accuracy(acc, max_dec = 12):
    if acc  is None or acc <= 0:
        return None
    acc = round(float(acc), 12)
    for n in range(0, max_dec + 1):
        target = 10.0 ** (-n)
        if abs(n - round(n)) < 1e-8:
            return int(round(n))
    return None

def get_dim_units(dim):
    """
    Returns: (accuracy, unit_symbol, text_height_mm_in_model, unit_label)
    - text_height_mm_in_model already multiplied by view scale
    """

    dim_type = doc.GetElement(dim.GetTypeId())
    spec_id = dim_type.GetSpecTypeId()

    text_height_in_model = _text_type_size_mm(dim_type) * view_scale

    fo = dim_type.GetUnitsFormatOptions()
    if fo is None or fo.UseDefault:
        fo = doc.GetUnits().GetFormatOptions(spec_id)
    
    accuracy = None
    unit_symbol = None

    try:
        accuracy = fo.Accuracy
    except:
        accuracy = None
    
    try:
        sym_id = fo.GetSymbolTypeId()
        unit_symbol = LabelUtils.GetLabelForSymbol(sym_id)
    except:
        unit_symbol = None
    
    unit_id = fo.GetUnitTypeId()
    unit_label = LabelUtils.GetLabelForUnit(unit_id)

    return accuracy, unit_symbol, text_height_in_model, unit_label

def _text_type_size_mm(dim_type):
    p = dim_type.get_Parameter(BuiltInParameter.TEXT_SIZE)
    return UnitUtils.ConvertFromInternalUnits(p.AsDouble(), UnitTypeId.Millimeters)

def collect_dim_seg_info(dim_like, text_height_mm, count_decimals, unit_label, unit_symbol):
    """
    Works for DimensionSegment or Dimension (single)
    Returns: (display_text, text_width_mm, length_mm)
    """
    
    length_mm = UnitUtils.ConvertFromInternalUnits(getattr(dim_like, "Value", 0.0), UnitTypeId.Millimeters)

    v_disp = _unit_value(getattr(dim_like, "Value", 0.0), unit_label)
    if count_decimals is None:
        v_disp = int(round(float(v_disp)))
    else:
        v_disp = round(float(v_disp), int(count_decimals))
    
    txt = _format_number(v_disp, count_decimals)
    if unit_symbol:
        txt = txt + unit_symbol

    w_mm = _estimate_text_width_mm(text_height_mm, txt, count_decimals = count_decimals)
    return txt, w_mm, length_mm

def _unit_value(value_internal, unit_label):
    # Minimal mapping (extend if you use more unit labels)
    if unit_label == "Meters":
        return UnitUtils.ConvertFromInternalUnits(value_internal, UnitTypeId.Meters)
    if unit_label == "Millimeters":
        return UnitUtils.ConvertFromInternalUnits(value_internal, UnitTypeId.Millimeters)
    return UnitUtils.ConvertFromInternalUnits(value_internal, UnitTypeId.Millimeters)

def _format_number(value, decimals):
    if decimals is None:
        return str(int(round(float(value))))
    return float(value).ToString("F{}".format(int(decimals)), CI)

def _estimate_text_width_mm(text_height_mm, value_string, count_decimals = None, char_factor = CHAR_FACTOR):
    s = (value_string or "").strip()
    # add 1 char for decimal separator if we know we have decimals (conservative)
    if count_decimals and count_decimals > 0:
        return text_height_mm * char_factor * (len(s) + 1)
    return text_height_mm * char_factor * len(s)

#---------------------------BASELINE / MOVED DETECTION-----------------------------------#

def compute_baseline_nearest_line(dim, view):
    """
    Baseline for 'default/auto' text offset.
    Robust even if many texts are already moved: we use the half closest to the dim line (smallest |u|).
    """
    ups = []
    for seg in dim.Segments:
        try:
            tp = seg.TextPosition
        except:
            continue
        if tp is not None:
            ups.append(_up_pos_mm(dim, view, tp))
    
    if not ups:
        return 0.0
    
    ups_sorted = sorted(ups, key=lambda u:abs(u))
    take = max(1, int(len(ups_sorted) * 0.5))
    core = ups_sorted[ :take ]
    return median(core)

def seg_is_moved_relative(dim, view, seg, baseline_up_mm, text_height_mm):
    """Moved if its up-offset deviates from baseline by more than a tight threshold."""
    thr = max(MOVED_THR_MIN_MM, MOVED_THR_TEXT_FRAC * text_height_mm)

    try:
        tp = seg.TextPosition
    except:
        return True # if we can't read, don't touch it
    
    if tp is None:
        return False
    
    u = _up_pos_mm(dim, view, tp)
    return abs(u - baseline_up_mm) > thr

def median(vals):
    s = sorted(vals)
    n = len(s)

    if n == 0:
        return None
    
    # Finn midt indeksen
    mid = n // 2
    
    # Hvis n er oddetall
    if n % 2 == 1:
        return s[mid]
    
    # Hvis n er partall
    return 0.5 * (s[mid-1] + s[mid])

# ------------------------------ BASE POINTS (LEADER OFF) ------------------------------ #

def get_segment_base_point(seg, dim):
    """Safe XYZ base point to move from (TextPosition if present else dim line origin)."""
    try:
        tp = seg.TextPosition
        if tp is not None:
            return tp
    except:
        pass
    try:
        return dim.Curve.Origin
    except:
        return None

def get_dimension_base_point(dim):
    try:
        tp = dim.TextPosition
        if tp is not None:
            return tp
    except:
        pass
    try:
        return dim.Curve.Origin
    except:
        return None

def move_text(dim_like, target_xyz):
    """Set TextPosition. Leader remains off."""
    dim_like.TextPosition = target_xyz
    try:
        dim_like.HasLeader = False
    except:
        pass
    
def offset_vector_up_side(dim, view, text_height_mm, text_width_mm, side_sign):
    """Vector (internal units) to move text out from line, and a bit along the line to avoid arrowheads."""
    origin, along, up = get_dim_frame(dim, view)
    up_mm = text_height_mm * 0.35
    side_mm = max(text_height_mm * 0.8, text_width_mm * 1.2)
    return along * (mm_to_internal(side_mm) * side_sign) + up * mm_to_internal(up_mm)

# --------------------------- OVERLAP RESOLUTION (TEXT - TEXT) --------------------------- #

def is_single_dim_manually_moved(dim, tol_mm=0.5):
    """
    If ResetTextPosition would change the text position => it was manually moved.
    Probe by resetting in a transaction and rolling back.
    """
    tp_before = getattr(dim, "TextPosition", None)

    t = Transaction(doc, "Probe ResetTextPosition")
    t.Start()
    try:
        try:
            dim.ResetTextPosition()
        except:
            t.RollBack()
            return True
        tp_after = getattr(dim, "TextPosition", None)
    finally:
        t.RollBack()

    if tp_before is None or tp_after is None:
        return not (tp_before is None and tp_after is None)

    return not _points_close(tp_before, tp_after, tol_mm=tol_mm)

def _points_close(p1, p2, tol_mm=0.5):
    dist_ft = p1.DistanceTo(p2)
    dist_mm = UnitUtils.ConvertFromInternalUnits(dist_ft, UnitTypeId.Millimeters)
    return dist_mm < tol_mm

def build_text_items(dim, view, text_height_mm, count_decimals, unit_label, unit_symbol):
    items = []
    for seg in dim.Segments:
        if not f_can_touch_segment(seg):
            continue

        base = get_segment_base_point(seg, dim)
        if base is None:
            continue

        dim_text, text_width_mm, seg_len_mm = collect_dim_seg_info(
            seg, text_height_mm, count_decimals, unit_label, unit_symbol
        )

        items.append({
            "seg": seg,
            "val": getattr(seg, "Value", 1e99),
            "text": dim_text,
            "w": text_width_mm,
            "seg_len_mm": seg_len_mm,   # <-- NY
            "x": along_pos_mm(dim, view, base),
            "u": _up_pos_mm(dim, view, base)
        })
    return items

def build_overlap_clusters(items):
    """Return list of clusters of overlapping [x0,x1] intervals (sorted along dim line)."""
    its = sorted(items, key=lambda it: it["x0"])
    clusters = []
    cur = []
    cur_max = None

    for it in its:
        if not cur:
            cur = [it]
            cur_max = it["x1"]
            continue

        # overlap test: start before current cluster end
        if it["x0"] < cur_max:
            cur.append(it)
            cur_max = max(cur_max, it["x1"])
        else:
            clusters.append(cur)
            cur = [it]
            cur_max = it["x1"]

    if cur:
        clusters.append(cur)
    return clusters


def plan_multiseg_moves(dim, view, text_height_mm, items, padding_mm=PADDING_MM):
    """
    Plan flytting for multiseg:
    - Finn overlapp-klynger
    - Første i klynge -> venstre, siste -> høgre
    - Midten -> nivå (opp/ned)
    - Klynge på 1 -> flytt berre om teksten ikkje får plass i segmentet
    Returnerer: [(seg, target_xyz), ...]
    """
    if not items:
        return []

    origin, along, up = get_dim_frame(dim, view)

    active = []
    ups = []

    # bygg x0/x1 intervall langs dimlinja (utan å flytte noko)
    for index,it in enumerate(items):
        seg = it["seg"]
        it["index"] = index
        base = get_segment_base_point(seg, dim)
        if base is None:
            continue

        try:
            pr = dim.Curve.Project(base)
            if pr is None:
                continue
            p_line = pr.XYZPoint
        except:
            continue

        it["p_line"] = p_line
        it["x"] = along_pos_mm(dim, view, p_line)
        it["u"] = _up_pos_mm(dim, view, base)

        half = 0.5 * it["w"]
        it["x0"] = it["x"] - half - padding_mm
        it["x1"] = it["x"] + half + padding_mm

        active.append(it)
        ups.append(it["u"])
    
    if len(active) < 1:
        return []

    # baseline frå dei som ligg nærast linja (minste |u|)
    ups_sorted = sorted(ups, key=lambda u: abs(u))
    take = max(1, int(len(ups_sorted) * 0.5))
    baseline_u = median(ups_sorted[:take]) if ups_sorted else 0.0

    step_mm = max(2.0, OVERLAP_STEP_TEXT_FRAC * text_height_mm)

    clusters = build_overlap_clusters(active)
    
    jobs = []

    for cl in clusters:
        # ingen overlapp -> flytt berre om "ikkje får plass"
        if len(cl) == 1:
            it = cl[0]
            seg_len_mm = it.get("seg_len_mm", None)

            if seg_len_mm and (it["w"] + padding_mm) > seg_len_mm:
                # same "ut til side + litt opp" som før
                side_mm = max(text_height_mm * 0.8, it["w"] * 1.2)
                up_mm = text_height_mm * 0.35
                p_target = it["p_line"] + along * mm_to_internal(side_mm) + up * mm_to_internal(up_mm)
                jobs.append((it["seg"], p_target))
            continue

        # overlapp-klynge (2+)
        cl_sorted = sorted(cl, key=lambda it: it["x"])  # venstre->høgre på dimlinja
        
        left = cl_sorted[0]
        right = cl_sorted[-1]
        mids = cl_sorted[1:-1]

        # Endar ut til sidene
        for it, sign in ((left, -1.0), (right, +1.0)):
            side_mm = max(text_height_mm * 0.8, it["w"] * 1.2)
            up_mm = text_height_mm * 1.20
            p_target = it["p_line"] + along * mm_to_internal(side_mm * sign) + up * mm_to_internal(up_mm)
            jobs.append((it["seg"], p_target))

        # Midten: mest berre høgde (levels)
        for i, it in enumerate(mids, start=1):
            # bevar side (over/under) relativt til baseline
            sign = 1.0 if it["u"] >= baseline_u else -1.0
            u_target_mm = baseline_u + sign * (i * step_mm)
            p_target = it["p_line"] + up * mm_to_internal(u_target_mm)
            jobs.append((it["seg"], p_target))

    return jobs


def resolve_overlaps(dim, view, text_height_mm, items, padding_mm=PADDING_MM, max_iter=MAX_OVERLAP_ITERS):
    """
    Stabil overlap-løysing for mange tette tekstar:
    - Bruk 1D-intervall langs dimlinja
    - Greedy level-assignment (0,1,2,3...)
    - SETT absolut posisjon: projiser på dimlinja + up * (baseline + level*step)
    """
    if len(items) < 2:
        return

    origin, along, up = get_dim_frame(dim, view)
    step_mm = max(2.0, OVERLAP_STEP_TEXT_FRAC * text_height_mm)

    active = []
    ups = []

    # 1) Oppdater basepunkt + x-intervall
    for it in items:
        seg = it["seg"]
        base = get_segment_base_point(seg, dim)
        if base is None:
            it["skip"] = True
            continue

        it["skip"] = False

        # PROJISER base ned på dimensjonslinja (viktig!)
        try:
            pr = dim.Curve.Project(base)
            if pr is None:
                continue
            p_line = pr.XYZPoint
        except:
            continue

        it["p_line"] = p_line  # lagre punkt på linja

        # x langs linja (mm) – berre for sortering/overlap
        it["x"] = along_pos_mm(dim, view, p_line)

        # u (mm) – kor langt frå linja
        it["u"] = _up_pos_mm(dim, view, base)

        half = 0.5 * it["w"]
        it["x0"] = it["x"] - half - padding_mm
        it["x1"] = it["x"] + half + padding_mm

        active.append(it)
        ups.append(it["u"])

    if len(active) < 2:
        return

    # 2) baseline_u: ta halvparten som ligg nærmast linja (minste |u|)
    ups_sorted = sorted(ups, key=lambda u: abs(u))
    take = max(1, int(len(ups) * 0.5))
    baseline_u = median(ups[:take])


    # 3) Level assignment (venstre -> høgre)
    active.sort(key=lambda it: (it["x0"], it["x1"]))

    levels_last_x1 = []
    level_by_key = {}

    for it in active:
        key = id(it["seg"])
        placed = False

        for lvl in range(len(levels_last_x1)):
            if it["x0"] >= levels_last_x1[lvl]:
                level_by_key[key] = lvl
                levels_last_x1[lvl] = it["x1"]
                placed = True
                break

        if not placed:
            lvl = len(levels_last_x1)
            levels_last_x1.append(it["x1"])
            level_by_key[key] = lvl

    # 4) SETT absolutt posisjon: p_line + up*(baseline + lvl*step) med same side som teksten ligg på no
    for it in active:
        seg = it["seg"]
        key = id(seg)
        lvl = level_by_key.get(key, 0)
        if lvl <= 0:
            continue

        p_line = it.get("p_line", None)
        if p_line is None:
            continue

        # bevar side (over/under) basert på noverande u
        sign = 1.0 if it["u"] >= baseline_u else -1.0

        u_target_mm = baseline_u + sign * (lvl * step_mm)
        u_ft = mm_to_internal(u_target_mm)

        p_target = p_line + up * u_ft

        try:
            seg.TextPosition = p_target
            seg.HasLeader = False
        except:
            pass

def _cluster_rows(items, row_tol_mm):
    """
    Group items by u-offset (same 'row').
    items: list of dict with key 'u'
    """
    rows = []
    for it in sorted(items, key=lambda r:r["u"]):
        placed = False
        for row in rows:
            if abs(it["u"] - row[0]["u"]) <= row_tol_mm:
                row.append(it)
                placed = True
                break
        if not placed:
            rows.append([it])
    return rows

#  _      ____  _  _     
# / \__/|/  _ \/ \/ \  /|
# | |\/||| / \|| || |\ ||
# | |  ||| |-||| || | \||
# \_/  \|\_/ \|\_/\_/  \| MAIN SCRIPT

if __name__ == '__main__':
    main()