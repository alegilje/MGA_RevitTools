# -*- coding: utf-8 -*-
# Author: Alexander Gilje (refaktor)
# Date: 30.09.2025

#  _  _      ____  ____  ____  _____ 
# / \/ \__/|/  __\/  _ \/  __\/__ __\
# | || |\/|||  \/|| / \||  \/|  / \  
# | || |  |||  __/| \_/||    /  | |  
# \_/\_/  \|\_/   \____/\_/\_\  \_/ IMPORTS
#---------------------------------- STANDARD LIBRARY ----------------------------------#
import unicodedata, re
from System.Collections.Generic import IList
#----------------------- AUTODESK REVIT / PYREVIT IMPORTS -----------------------------#
from Autodesk.Revit.DB import \
    BoundingBoxXYZ, \
    BuiltInCategory, \
    BuiltInParameter, \
    Curve, \
    CurveLoop, \
    ElementCategoryFilter, \
    ElementId, \
    ElementTransformUtils, \
    FilledRegion, \
    FilledRegionType, \
    FilteredElementCollector, \
    Line, \
    LogicalAndFilter, \
    LogicalOrFilter, \
    ParameterFilterElement, \
    Plane, \
    SketchPlane, \
    TextNote, \
    TextNoteOptions, \
    TextNoteType, \
    Transaction, \
    VerticalTextAlignment, \
    View, \
    ViewDuplicateOption, \
    ViewType, \
    XYZ
from Autodesk.Revit.UI import \
    TaskDialog, \
    TaskDialogCommonButtons, \
    TaskDialogCommandLinkId, \
    TaskDialogResult
from pyrevit import revit, forms, DB
from pyrevit.framework import List

from Snippets._convert import convert_m_to_internal
from tools._transactions import revit_transaction, revit_groupTransaction

#  _     ____  ____  _  ____  ____  _     _____ ____ 
# / \ |\/  _ \/  __\/ \/  _ \/  __\/ \   /  __// ___\
# | | //| / \||  \/|| || / \|| | //| |   |  \  |    \
# | \// | |-|||    /| || |-||| |_\\| |_/\|  /_ \___ |
# \__/  \_/ \|\_/\_\\_/\_/ \|\____/\____/\____\\____/ VARIABLES
#----------------------------- GLOBALS / CONTEXT --------------------------------------#
uidoc = __revit__.ActiveUIDocument
doc   = revit.doc
view  = revit.active_view

try:
    from Autodesk.Revit.DB import FilterHasValueRule
    _HAS_HASVALUE = True
except:
    FilterHasValueRule = None
    _HAS_HASVALUE = False


MAX_ROWS     = 30 

#  _____ _     _      ____  _____  _  ____  _      ____ 
# /    // \ /\/ \  /|/   _\/__ __\/ \/  _ \/ \  /|/ ___\
# |  __\| | ||| |\ |||  /    / \  | || / \|| |\ |||    \
# | |   | \_/|| | \|||  \__  | |  | || \_/|| | \||\___ |
# \_/   \____/\_/  \|\____/  \_/  \_/\____/\_/  \|\____/ FUNCTIONS
BASE_W_M   = 3.0     # swatch-bredde
BASE_H_M   = 0.9     # swatch-høyde
BASE_GAP_M = 0.2     # vertikal radavstand
BASE_TX_M  = 0.9     # horisontal avstand fra swatch til tekst (f.eks. 0.9 m)

def scaled_sizes_for_view(v):
    """Skaler basis-mål (definert for 1:200) til gjeldende view.Scale."""
    f = float(v.Scale) / 200.0
    return (
        convert_m_to_internal(BASE_W_M * f),
        convert_m_to_internal(BASE_H_M * f),
        convert_m_to_internal(BASE_GAP_M * f),
        convert_m_to_internal(BASE_TX_M * f),
        convert_m_to_internal(0.22 * f)  # kolonneavstand – juster etter smak
    )
#----------------------------------------Utils------------------------------------------------#

def norm_txt(s):
    if s is None:
        return u""
    s = unicode(s)
    s = s.replace(u"\u00A0", u" ")     # NBSP -> space
    s = s.replace(u"–", u"-")          # en dash -> hyphen
    s = unicodedata.normalize('NFC', s).strip()
    s = re.sub(ur"\s*-\s*", u" - ", s) # standardiser mellomrom rundt '-'
    s = re.sub(ur"\s{2,}", u" ", s)    # klem dobbel-space
    return s

def key(s):
    """Robust nøkkel for likhetssjekk: små bokstaver, uten spaces."""
    return re.sub(ur"\s+", u"", norm_txt(s)).lower()

def _fr_type_name(fr_type):
    if not fr_type:
        return u"<missing type>"
    try:
        p = fr_type.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
        if p:
            s = p.AsString()
            if s:
                return s
    except:
        pass
    n = getattr(fr_type, 'Name', None)
    return n or u"<unnamed>"

def _description_type_param(fr_type):
    if not fr_type:
        return u"<missing type>"
    try:
        p = fr_type.get_Parameter(BuiltInParameter.ALL_MODEL_DESCRIPTION)
        if p:
            s = p.AsString()
            if s:
                return s
    except:
        pass
    n = getattr(fr_type, 'Name', None)
    return n or u"<unnamed>"

#----------------------------------------Crop 2D------------------------------------------------#

def view_in_crop_2d(el, crop_on, crop_bb):
    return (not crop_on) or _view_overlaps_crop_2d(el, crop_bb)

def _view_overlaps_crop_2d(elem, crop_bbox):
    """True hvis elementets bbox (i view/dok) overlapper crop 2D."""
    bb = _elem_bbox(elem, view)
    if not bb:
        return False
    el_min2, el_max2 = _bbox_to_crop2d(bb, crop_bbox)
    cr_min2 = (crop_bbox.Min.X, crop_bbox.Min.Y)
    cr_max2 = (crop_bbox.Max.X, crop_bbox.Max.Y)
    return _aabb2d_overlaps(el_min2, el_max2, cr_min2, cr_max2)

def _elem_bbox(elem, view_for_bbox):
    bb = None
    try:
        bb = elem.get_BoundingBox(view_for_bbox)
    except:
        bb = None
    if not isinstance(bb, BoundingBoxXYZ) or bb is None:
        try:
            bb = elem.get_BoundingBox(None)
        except:
            bb = None
    return bb if isinstance(bb, BoundingBoxXYZ) else None

def _bbox_corners(bbox):
    mn, mx = bbox.Min, bbox.Max
    return [XYZ(mn.X, mn.Y, mn.Z), XYZ(mx.X, mn.Y, mn.Z),
            XYZ(mn.X, mx.Y, mn.Z), XYZ(mx.X, mx.Y, mn.Z),
            XYZ(mn.X, mn.Y, mx.Z), XYZ(mx.X, mn.Y, mx.Z),
            XYZ(mn.X, mx.Y, mx.Z), XYZ(mx.X, mx.Y, mx.Z)]

def _bbox_to_crop2d(src_bbox, crop_bbox):
    inv = crop_bbox.Transform.Inverse
    pts_local = [inv.OfPoint(p) for p in _bbox_corners(src_bbox)]
    xs = [p.X for p in pts_local]; ys = [p.Y for p in pts_local]
    return (min(xs), min(ys)), (max(xs), max(ys))

def _aabb2d_overlaps(minA, maxA, minB, maxB):
    return not (maxA[0] < minB[0] or minA[0] > maxB[0] or
                maxA[1] < minB[1] or minA[1] > maxB[1])

#----------------------------------------View Filters------------------------------------------------#

def _is_filter_enabled(v, fid):
    try:
        return bool(v.GetIsFilterEnabled(fid))
    except:
        return True

def _build_pf_filter(pf):
    """Kombiner kategori-filter og regel-filter frå ParameterFilterElement."""
    try:
        cats = pf.GetCategories() or []
    except:
        cats = []
    cat_filters = []
    for cid in cats:
        try:
            cat_filters.append(ElementCategoryFilter(cid))
        except:
            pass
    try:
        rules_filter = pf.GetElementFilter()
    except:
        rules_filter = None

    if cat_filters and rules_filter:
        return LogicalAndFilter([LogicalOrFilter(cat_filters), rules_filter])
    elif cat_filters:
        return LogicalOrFilter(cat_filters)
    else:
        return rules_filter  # kan vere None

def get_effective_filters(doc_, enabled_filter_ids, view_):
    """Returner liste med N A V N på aktiverte filter som faktisk treffer i viewet."""
    names = []
    for fid in enabled_filter_ids:
        pf = doc_.GetElement(fid)
        if not isinstance(pf, ParameterFilterElement):
            continue
        combo_filter = _build_pf_filter(pf)
        if combo_filter is None:
            continue
        coll = (FilteredElementCollector(doc_, view_.Id)
                .WhereElementIsNotElementType()
                .WherePasses(combo_filter))
        # rask telling m/fallback
        try:
            count = coll.GetElementCount()
        except:
            try:
                count = sum(1 for _ in coll)
            except:
                count = 0
        if count > 0:
            names.append(unicode(pf.Name))
    return names

#----------------------------------------FILTER MAP------------------------------------------------#

def build_vf_to_frt_map(doc_):
    """Map: normalisert 'View Filter'-tekst -> [FilledRegionType,...]"""
    vf_to_frt = {}
    for frt in FilteredElementCollector(doc_).OfClass(FilledRegionType):
        p = frt.LookupParameter("View Filter")
        val = p.AsString() if (p and p.HasValue) else None
        k = key(val)
        if not k:
            continue
        vf_to_frt.setdefault(k, []).append(frt)
    return vf_to_frt

def is_valid_eid(eid):
    return bool(eid) and eid != ElementId.InvalidElementId

def collect_fr_type_ids_in_view(view_, crop_on, crop_bb):
    """Returner sett med TypeId (ElementId) for synlige FilledRegion i viewet."""
    tids = set()
    doc_ = view_.Document
    for fr in FilteredElementCollector(doc_, view_.Id).OfClass(FilledRegion):
        if not view_in_crop_2d(fr, crop_on, crop_bb):
            continue
        tid = fr.GetTypeId()
        if is_valid_eid(tid):
            tids.add(tid)   # legg inn ElementId direkte; ingen behov for IntegerValue
    return tids

def collect_topo_vf_keys(view_, crop_on, crop_bb):
    """Returner sett med normaliserte 'View Filter'-nøkler fra toposolids + subdivisions."""
    doc_ = view_.Document
    keys = set()
    for topo in (FilteredElementCollector(doc_, view_.Id)
                 .OfCategory(BuiltInCategory.OST_Toposolid)
                 .WhereElementIsNotElementType()):
        
        if not view_in_crop_2d(topo, crop_on, crop_bb):
            continue
        topo_element = doc.GetElement(topo.GetTypeId())
        p = topo_element.LookupParameter("View Filter")
        
        if p and p.HasValue:
            keys.add(key(p.AsString()))
        # subdivisions
        for sid in topo.GetSubDivisionIds() or []:
            sub = doc_.GetElement(sid)
            sub_element = doc_.GetElement(sub.GetTypeId())
            if not sub:
                continue
            if not view_in_crop_2d(sub, crop_on, crop_bb):
                continue
            sp = sub_element.LookupParameter("View Filter")
            
            if sp and sp.HasValue:
                keys.add(key(sp.AsString()))
    return keys

#----------------------------------------Create Legend------------------------------------------------#

def _rect_loop(origin, w, h):
    x, y = origin
    p1 = XYZ(x, y, 0.0)
    p2 = XYZ(x + w, y, 0.0)
    p3 = XYZ(x + w, y + h, 0.0)
    p4 = XYZ(x, y + h, 0.0)
    return [Line.CreateBound(p1, p2), Line.CreateBound(p2, p3), Line.CreateBound(p3, p4), Line.CreateBound(p4, p1)]

def _clean_text(text):
    return text.replace(" ", "").replace("\r", "\n").replace("\n\n", "\n").lower()

def _default_text_type_id(doc, prefer_name=u"Tegnforklaring"):
    """Finn gyldig TextNoteType.Id. Prøv navn, ellers første type."""
    types = list(FilteredElementCollector(doc).OfClass(TextNoteType).WhereElementIsElementType())
    if not types:
        return ElementId.InvalidElementId

    def _name(t):
        n = getattr(t, "Name", None)
        if not n:
            p = t.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME)
            n = p.AsString() if (p and p.HasValue) else u""
        return unicode(n)

    if prefer_name:
        want = _clean_text(prefer_name)
        # eksakt (case-insens)
        for t in types:
            if _clean_text(_name(t)) == want:
                return t.Id
        # inneholder (case-insens)
        for t in types:
            if want in _clean_text(_name(t)):
                return t.Id

    # fallback
    return types[0].Id

def _text_height_internal(doc, text_type_id):
    """Hent teksthøyde (internal units/feet) fra typen."""
    tnt = doc.GetElement(text_type_id)
    p = tnt.get_Parameter(BuiltInParameter.TEXT_SIZE) if tnt else None
    return p.AsDouble() if (p and p.HasValue) else convert_m_to_internal(0.003)  # fallback ~3 mm

def _add_text_centered_y(doc, view, text, left_x, center_y, text_type_id):
    """
    Lag en venstrejustert TextNote med vertikal midt-justering (hvis støttet).
    Fallback: mål bounding box og flytt til eksakt center_y (m/ liten optisk justering).
    """
    opts = TextNoteOptions(text_type_id)
    # Horisontal venstre
    try:
        from Autodesk.Revit.DB import HorizontalTextAlignment
        opts.HorizontalAlignment = HorizontalTextAlignment.Left
    except:
        pass

    used_native_middle = False
    # Vertikal midt (Revit 2022+)
    try:
        opts.VerticalAlignment = VerticalTextAlignment.Middle
        used_native_middle = True
    except:
        pass

    # Lag noten med innsettingspunkt på ønsket senter-Y
    note = TextNote.Create(doc, view.Id, XYZ(left_x, center_y, 0.0), text, opts)

    # Fallback/finjustering når VerticalAlignment ikke finnes
    if not used_native_middle:
        bb = note.get_BoundingBox(view)
        if bb:
            cur_center_y = 0.5 * (bb.Min.Y + bb.Max.Y)
            dy = center_y - cur_center_y
            # liten optisk korreksjon (tekst ser ofte litt “tung” ut mot toppen)
            text_h = (bb.Max.Y - bb.Min.Y)
            dy += -0.10 * text_h   # justér +/- 0.05–0.15 etter smak
            if abs(dy) > 1e-9:
                ElementTransformUtils.MoveElement(doc, note.Id, XYZ(0, dy, 0))
    return note

def _ensure_sketchplane_for_view(doc, view):
    # Bruk eksisterende SketchPlane hvis den finnes
    sp = getattr(view, "SketchPlane", None)
    if sp: 
        return sp
    # Ellers lag en XY-plane (Z-opp) ved origo
    plane = Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ.Zero)
    return SketchPlane.Create(doc, plane)

def _create_detail_curve(doc, view, curve):
    # Prøv overloaden som tar View først (nyere Revit)
    try:
        dc = doc.Create.NewDetailCurve(view, curve)
    except:
        # Eldre overload: krever SketchPlane
        sp = _ensure_sketchplane_for_view(doc, view)
        dc = doc.Create.NewDetailCurve(sp, curve)
    return dc

def _create_filled_region(doc, view, fr_type_id, rect_curves):
    # Variant 1: IList<IList<Curve>>
    try:
        curve_list = List[Curve](rect_curves)                 # IList<Curve>
        boundaries = List[IList[Curve]]()                     # IList<IList<Curve>>
        boundaries.Add(curve_list)
        return FilledRegion.Create(doc, fr_type_id, view.Id, boundaries)
    except:
        # Variant 2: CurveLoop-overload (andre Revit-versjoner)
        loop = CurveLoop()
        for c in rect_curves:
            loop.Append(c)
        loops = List[CurveLoop]([loop])                       # IList<CurveLoop>
        return FilledRegion.Create(doc, fr_type_id, view.Id, loops)

def _layout_points(nitems, max_rows):
    pts = []
    col = 0; row = 0
    for i in range(nitems):
        pts.append((col, row))
        row += 1
        if row >= max_rows:
            row = 0
            col += 1
    return pts

def draw_tegnforklaring(view, fr_types, start_world_pt=None, border_mode="keep"):
    doc = view.Document
    if not fr_types: return
    if start_world_pt is None:
        start_world_pt = XYZ(0, 0, 0)

    w, h, row_gap, text_dx, col_dx = scaled_sizes_for_view(view)

    tnt_id = _default_text_type_id(doc, prefer_name=u"Tegnforklaring")
    if tnt_id == ElementId.InvalidElementId:
        forms.alert(u"Fant ingen TextNoteType.", exitscript=False); return

    text_h   = _text_height_internal(doc, tnt_id)
    row_pitch= max(h, text_h) * 1.20

    fr_types_sorted = sorted(fr_types, key=lambda t: _description_type_param(t))
    temp_line_ids = []  # <- samle IDer hvis border_mode=="temp"

    with Transaction(doc, "Tegnforklaring") as t:
        t.Start()
        for (col, row), frt in zip(_layout_points(len(fr_types_sorted), MAX_ROWS), fr_types_sorted):
            base_x = start_world_pt.X + col * col_dx
            base_y = start_world_pt.Y - row * row_pitch

            rect_curves = _rect_loop((base_x, base_y), w, h)
            _create_filled_region(doc, view, frt.Id, rect_curves)

            # kantlinjer
            if border_mode in ("keep", "temp"):
                for seg in rect_curves:
                    dc = _create_detail_curve(doc, view, seg)
                    if border_mode == "temp" and dc:
                        temp_line_ids.append(dc.Id)

            # tekst, vertikalt midtstilt
            mid_y  = base_y + 0.5*h
            left_x = base_x + w + text_dx
            _add_text_centered_y(doc, view, _description_type_param(frt), left_x, mid_y, tnt_id)

        # slett midlertidige linjer (hvis valgt)
        if temp_line_ids:
            ids = List[ElementId](temp_line_ids)
            doc.Delete(ids)

        t.Commit()

def ask_overwrite_or_duplicate(desired_name):
    """Vis valg-dialog. Returnerer 'overwrite', 'duplicate' eller None (avbryt)."""
    td = TaskDialog("Tegnforklaring")
    td.MainInstruction = u"Legend '{}' finnes allerede.".format(desired_name)
    td.MainContent = u"Vil du overskrive innholdet i den eksisterende legenden,\neller duplisere den og tegne i en ny kopi?"
    td.AddCommandLink(TaskDialogCommandLinkId.CommandLink1, u"Overskriv eksisterende")
    td.AddCommandLink(TaskDialogCommandLinkId.CommandLink2, u"Dupliser og tegn i kopi")
    td.CommonButtons = TaskDialogCommonButtons.Cancel
    td.DefaultButton = TaskDialogResult.CommandLink1
    r = td.Show()
    if r == TaskDialogResult.CommandLink1:
        return "overwrite"
    if r == TaskDialogResult.CommandLink2:
        return "duplicate"
    return None

def get_or_prepare_legend_with_choice(doc, desired_name):
    """
    Finn/lag legend basert på brukerens valg.
    - Finnes ingen: dupliser første legend og gi navn.
    - Finnes: spør bruker om 'overskriv' eller 'dupliser'.
    Returnerer (legend_view, action) der action er 'overwrite' eller 'duplicate', ellers None.
    """
    legends = [v for v in FilteredElementCollector(doc).OfClass(View)
               if v.ViewType == ViewType.Legend and not v.IsTemplate]
    if not legends:
        forms.alert(u"Fant ingen Legend-views. Lag én manuelt (View > Legend) og kjør igjen.",
                    exitscript=False)
        return None, None

    # Sjekk om ønsket navn finnes
    existing = None
    for v in legends:
        if _clean_text(unicode(v.Name)) == _clean_text(unicode(desired_name)):
            existing = v
            break

    if not existing:
        # Dupliser første legend og gi ønsket navn
        src = legends[0]
        with Transaction(doc, "Duplicate Legend") as t:
            t.Start()
            dup_id = src.Duplicate(ViewDuplicateOption.Duplicate)
            legend = doc.GetElement(dup_id)
            # prøv ønsket navn (+teller ved konflikt)
            base = unicode(desired_name); i = 1
            while True:
                try:
                    legend.Name = base if i == 1 else u"{} ({})".format(base, i)
                    break
                except:
                    i += 1
            t.Commit()
        return legend, "duplicate"

    # Finnes allerede → spør
    choice = ask_overwrite_or_duplicate(desired_name)
    if choice is None:
        return None, None

    if choice == "overwrite":
        return existing, "overwrite"

    # duplicate choice
    with Transaction(doc, "Duplicate Legend") as t:
        t.Start()
        dup_id = existing.Duplicate(ViewDuplicateOption.Duplicate)
        legend = doc.GetElement(dup_id)
        # Gi nytt navn automatisk
        base = unicode(desired_name)
        i = 2
        while True:
            try:
                legend.Name = u"{} ({})".format(base, i)
                break
            except:
                i += 1
        t.Commit()
    return legend, "duplicate"

def _delete_eids(doc, eids, txname="Delete legend block"):
    if not eids:
        return 0
    from pyrevit.framework import List
    ids = List[ElementId](list(eids))
    with Transaction(doc, txname) as t:
        t.Start()
        doc.Delete(ids)
        t.Commit()
    return len(eids)

def _collect_detail_eids_in_view(doc, view, cats):
    """Hent alle element-IDs i viewet for gitte kategorier."""
    eids = set()
    for bic in cats:
        for el in (FilteredElementCollector(doc, view.Id)
                    .OfCategory(bic)
                    .WhereElementIsNotElementType()):
            eids.add(el.Id)
    return eids

def _collect_detail_eids_in_rect(doc, view, cats, rect_min, rect_max):
    """Hent element-IDs innenfor en rektangulær region (view-koordinater)."""
    eids = set()
    for bic in cats:
        for el in (FilteredElementCollector(doc, view.Id)
                    .OfCategory(bic)
                    .WhereElementIsNotElementType()):
            bb = el.get_BoundingBox(view)
            if not bb:
                bb = el.get_BoundingBox(None)
            if not bb:
                continue
            if _aabb2d_overlaps(bb.Min, bb.Max, rect_min, rect_max):
                eids.add(el.Id)
    return eids

def clear_legend_area(doc, legend_view, origin_pt, width_ft, height_ft,
                      margin_ft=0.0, cats=None):
    """
    Slett detail-elementer i en rektangel i legend-viewet.
    origin_pt: nedre-venstre hjørne (samme koordinater som du bruker ved tegn).
    width_ft/height_ft: samlet bredde/høyde på blokka du vil rydde.
    margin_ft: ekstra luft rundt (tåler at du ikke treffer nøyaktig).
    """
    if cats is None:
        cats = [BuiltInCategory.OST_DetailComponents,  # FilledRegion
                BuiltInCategory.OST_TextNotes,         # TextNote
                BuiltInCategory.OST_Lines]             # DetailCurve

    x0 = origin_pt.X - margin_ft
    y0 = origin_pt.Y - margin_ft
    x1 = origin_pt.X + width_ft + margin_ft
    y1 = origin_pt.Y + height_ft + margin_ft

    rect_min = XYZ(min(x0, x1), min(y0, y1), -1)
    rect_max = XYZ(max(x0, x1), max(y0, y1), +1)

    eids = _collect_detail_eids_in_rect(doc, legend_view, cats, rect_min, rect_max)
    return _delete_eids(doc, eids, txname="Clear legend area")

def clear_legend_all(doc, legend_view, cats=None):
    """Slett alle detail-elementer i hele legend-viewet."""
    if cats is None:
        cats = [BuiltInCategory.OST_DetailComponents,
                BuiltInCategory.OST_TextNotes,
                BuiltInCategory.OST_Lines]
    eids = _collect_detail_eids_in_view(doc, legend_view, cats)
    return _delete_eids(doc, eids, txname="Clear legend all")

#----------------------------------------Main------------------------------------------------#

def main():
    # Is current view a floorplan?
    if view.IsTemplate or view.ViewType != ViewType.FloorPlan:
        forms.alert("Please run this tool in a Floor Plan view (not a template).", exitscript=True)

    # Crop state
    try:
        crop_on = bool(view.CropBoxActive)
        crop_bb = view.CropBox if crop_on else None
    except:
        crop_on = False
        crop_bb = None

    # 1) Active view-filters
    filter_ids = list(view.GetFilters() or [])
    if not filter_ids:
        forms.alert("No filters are applied to this view", exitscript=False)
        return

    enabled_ids = [fid for fid in filter_ids if _is_filter_enabled(view, fid)]
    if not enabled_ids:
        forms.alert("No filters are enabled in this view", exitscript=False)
        return

    filter_names_hit = get_effective_filters(doc, enabled_ids, view)

    # 2) Collect FilledRegionType -> "View Filter" map
    vf_to_frt = build_vf_to_frt_map(doc)

    # 3) Filled Regions from view-filters
    tegnforklaring_type_ids = set()
    for fname in filter_names_hit:
        k = key(fname)
        if k in vf_to_frt:
            for frt in vf_to_frt[k]:
                tegnforklaring_type_ids.add(frt.Id)

    # 4) Filled Regions in view (crop-aware)
    fr_type_ids_in_view = collect_fr_type_ids_in_view(view, crop_on, crop_bb)
    tegnforklaring_type_ids.update(fr_type_ids_in_view)
    
    # 5) Toposolids + Subdivisions: match "View Filter"-keys
    topo_keys = collect_topo_vf_keys(view, crop_on, crop_bb)
    
    for k in topo_keys:
        if k in vf_to_frt:
            for frt in vf_to_frt[k]:
                if frt.Id not in tegnforklaring_type_ids:
                    tegnforklaring_type_ids.add(frt.Id)

    # 6) Result
    matched_types = [doc.GetElement(tid) for tid in tegnforklaring_type_ids]
    legend_name = "Tegnforklaring - " + view.Name
    with revit_groupTransaction(doc, "Tegnforklaring - " + view.Name):
       
        
        legend, action = get_or_prepare_legend_with_choice(doc, legend_name)
        if not legend:
            return

        with Transaction(doc, "Sync legend scale") as tx:
            tx.Start()
            legend.Scale = view.Scale
            tx.Commit()
        
        if action == "overwrite":
            clear_legend_all(doc, legend)

        uidoc.ActiveView = legend  # så du ser resultatet
        start_pt = XYZ(convert_m_to_internal(0.2), convert_m_to_internal(0.1), 0)
        draw_tegnforklaring(legend, matched_types, start_pt, border_mode="temp")

    # TODO: her kan du tegne selve tegnforklaringen basert på matched_types

#  _      ____  _  _     
# / \__/|/  _ \/ \/ \  /|
# | |\/||| / \|| || |\ ||
# | |  ||| |-||| || | \||
# \_/  \|\_/ \|\_/\_/  \| MAIN SCRIPT

if __name__ == "__main__":
    main()
