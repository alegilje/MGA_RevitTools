# encoding: utf-8
""" 
Author Alexander Gilje
title: Transfer Project Info
Date: 17.10.2025
"""
#  _  _      ____  ____  ____  _____ 
# / \/ \__/|/  __\/  _ \/  __\/__ __\
# | || |\/|||  \/|| / \||  \/|  / \  
# | || |  |||  __/| \_/||    /  | |  
# \_/\_/  \|\_/   \____/\_/\_\  \_/ IMPORTS
#----------------------------------STANDARD LIBRARY IMPORTS----------------------------------#

#---------------------------- AUTODESK REVIT AND PYREVIT IMPORTS ----------------------------#
from pyrevit import revit, forms

from Autodesk.Revit.DB import StorageType, ElementId

#  _     ____  ____  _  ____  ____  _     _____ ____ 
# / \ |\/  _ \/  __\/ \/  _ \/  __\/ \   /  __// ___\
# | | //| / \||  \/|| || / \|| | //| |   |  \  |    \
# | \// | |-|||    /| || |-||| |_\\| |_/\|  /_ \___ |
# \__/  \_/ \|\_/\_\\_/\_/ \|\____/\____/\____\\____/ VARIABLES

uidoc = __revit__.ActiveUIDocument
doc = uidoc.Document
app = __revit__.Application

# Parameters
PARAM_NAMES = [
    "Project Name",
    "Project Number",
    "Client Name",
    "Forhandler",
    "Byggeplass",
    "Kommune",
    "Gnr/Bnr"
]

#  _____ _     _      ____  _____  _  ____  _      ____ 
# /    // \ /\/ \  /|/   _\/__ __\/ \/  _ \/ \  /|/ ___\
# |  __\| | ||| |\ |||  /    / \  | || / \|| |\ |||    \
# | |   | \_/|| | \|||  \__  | |  | || \_/|| | \||\___ |
# \_/   \____/\_/  \|\____/  \_/  \_/\____/\_/  \|\____/ FUNCTIONS



def _get_open_docs(application):
    return [d for d in application.Documents]

def _doc_title(d):
    try:
        return d.Title
    except:
        return str(d)

def _choose_doc(prompt, docs, exclude=None):
    items, mapping = [], {}
    for d in docs:
        if exclude and d.Equals(exclude):
            continue
        title = _doc_title(d)
        mapping[title] = d
        items.append(title)
    if not items:
        return None
    picked = forms.SelectFromList.show(items, title=prompt, multiselect=False)
    if not picked:
        return None
    return mapping[picked]

def _copy_param_value(src_param, dst_param):
    if not src_param or not dst_param:
        return False, "param missing"
    if dst_param.IsReadOnly:
        return False, "read-only"
    st_src = src_param.StorageType
    st_dst = dst_param.StorageType
    if st_src != st_dst:
        return False, "storage mismatch"
    try:
        if st_src == StorageType.String:
            dst_param.Set(src_param.AsString() or "")
        elif st_src == StorageType.Integer:
            dst_param.Set(src_param.AsInteger())
        elif st_src == StorageType.Double:
            # Copy internal double value (Project Info params generally unitless/text, but safe)
            dst_param.Set(src_param.AsDouble())
        elif st_src == StorageType.ElementId:
            val = src_param.AsElementId()
            if val is None:
                val = ElementId.InvalidElementId
            dst_param.Set(val)
        else:
            return False, "unsupported storage"
        return True, "ok"
    except Exception as ex:
        return False, str(ex)

#----------------------------------------MAIN------------------------------------------------#

def main():
    docs = _get_open_docs(app)
    if len(docs) < 2:
        forms.alert("Åpne minst to prosjekter (kilde og mål).", exitscript=True)

    src_doc = _choose_doc("Velg KILDE-prosjekt (Project Information kopieres FRA)", docs)
    if not src_doc:
        forms.alert("Ingen kilde valgt.", exitscript=True)

    tgt_doc = _choose_doc("Velg MÅL-prosjekt (Project Information kopieres TIL)", docs, exclude=src_doc)
    if not tgt_doc:
        forms.alert("Ingen mål valgt.", exitscript=True)

    src_pi = src_doc.ProjectInformation
    tgt_pi = tgt_doc.ProjectInformation
    if not src_pi or not tgt_pi:
        forms.alert("Finner ikke Project Information i et av prosjektene.", exitscript=True)

    updated = 0
    tried = 0
    skipped = 0
    mismatches = 0

    with revit.Transaction('Copy Project Information Parameters', doc=tgt_doc):
        for pname in PARAM_NAMES:
            p_src = src_pi.LookupParameter(pname)
            p_tgt = tgt_pi.LookupParameter(pname)
            if not p_src or not p_src.HasValue or not p_tgt:
                skipped += 1
                continue
            ok, msg = _copy_param_value(p_src, p_tgt)
            tried += 1
            if ok:
                updated += 1
            else:
                if msg == "storage mismatch":
                    mismatches += 1
                else:
                    skipped += 1

    forms.alert(
        "Ferdig (Project Information).\nKilde: {0}\nMål: {1}\nParametre: {2}\nOppdatert: {3}\nForsøk: {4}\nSkippet: {5}\nStorage mismatch: {6}".format(
            _doc_title(src_doc),
            _doc_title(tgt_doc),
            ", ".join(PARAM_NAMES),
            updated, tried, skipped, mismatches
        ),
        exitscript=False
    )

#  _      ____  _  _     
# / \__/|/  _ \/ \/ \  /|
# | |\/||| / \|| || |\ ||
# | |  ||| |-||| || | \||
# \_/  \|\_/ \|\_/\_/  \| MAIN SCRIPT

if __name__ == "__main__":
    main()
