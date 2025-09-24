# encoding: utf-8
""" 
Author Alexander Gilje
title: Move Door Tags
Date: 12.09.2025
"""
#  _  _      ____  ____  ____  _____ 
# / \/ \__/|/  __\/  _ \/  __\/__ __\
# | || |\/|||  \/|| / \||  \/|  / \  
# | || |  |||  __/| \_/||    /  | |  
# \_/\_/  \|\_/   \____/\_/\_\  \_/ IMPORTS
#----------------------------------STANDARD LIBRARY IMPORTS----------------------------------#

#---------------------------- AUTODESK REVIT AND PYREVIT IMPORTS ----------------------------#
from pyrevit import revit

from Autodesk.Revit.DB import \
    FilteredElementCollector, \
    BuiltInCategory, \
    FamilyInstance, \
    XYZ, \
    ElementTransformUtils

#---------------------------- CUSTOM IMPORTS ----------------------------#

from tools._transactions import revit_transaction, revit_groupTransaction

#  _     ____  ____  _  ____  ____  _     _____ ____ 
# / \ |\/  _ \/  __\/ \/  _ \/  __\/ \   /  __// ___\
# | | //| / \||  \/|| || / \|| | //| |   |  \  |    \
# | \// | |-|||    /| || |-||| |_\\| |_/\|  /_ \___ |
# \__/  \_/ \|\_/\_\\_/\_/ \|\____/\____/\____\\____/ VARIABLES

uidoc = __revit__.ActiveUIDocument
doc   = uidoc.Document

#  _____ _     _      ____  _____  _  ____  _      ____ 
# /    // \ /\/ \  /|/   _\/__ __\/ \/  _ \/ \  /|/ ___\
# |  __\| | ||| |\ |||  /    / \  | || / \|| |\ |||    \
# | |   | \_/|| | \|||  \__  | |  | || \_/|| | \||\___ |
# \_/   \____/\_/  \|\____/  \_/  \_/\____/\_/  \|\____/ FUNCTIONS

#----------------------------------------MAIN------------------------------------------------#

def main():
    EPS = 1e-9

    
    offsets_100 = {
        (1, True): 1.20, 
        (2, True): 1.60, 
        (3, True): 2.00, 
        (4, True): 2.40, 
        (5, True): 2.80,
        (6, True): 3.20,
        (7, True): 3.60,
        (1, False): 1.20, 
        (2, False): 1.60, 
        (3, False): 2.00, 
        (4, False): 2.40, 
        (5, False): 2.80,
        (6, False): 3.20,
        (7, False): 3.60
    }
    offsets_50 = {
        (1, True): 1.00, 
        (2, True): 1.27, 
        (3, True): 1.54, 
        (4, True): 1.81, 
        (5, True): 2.08,
        (6, True): 2.35,
        (7, True): 2.62,
        (1, False): 1.00, 
        (2, False): 1.27, 
        (3, False): 1.54, 
        (4, False): 1.81, 
        (5, False): 2.08,
        (6, False): 2.35,
        (7, False): 2.62
    }
    offsets_200 = {
        (1, True): 1.20, 
        (2, True): 1.68, 
        (3, True): 2.16, 
        (4, True): 2.64, 
        (5, True): 3.12,
        (6, True): 3.60,
        (7, True): 4.08,
        (1, False): 1.20, 
        (2, False): 1.68, 
        (3, False): 2.16, 
        (4, False): 2.64, 
        (5, False): 3.12,
        (6, False): 3.60,
        (7, False): 4.08
    }

    view = uidoc.ActiveView

    tags = FilteredElementCollector(doc, view.Id)\
        .OfCategory(BuiltInCategory.OST_DoorTags)\
        .WhereElementIsNotElementType()\
        .ToElements()
    
    if not tags:
        print('❌ No Window tags found')
        return
    with revit_groupTransaction(doc,'Move Window Tags'):
        move_el = ElementTransformUtils.MoveElement  

        with revit_transaction(doc,'Move Tags'):
            for tag in tags:
                tagged_el_id = tag.GetTaggedLocalElementIds()

                if tagged_el_id is None or tagged_el_id.Count == 0:
                    continue

                tagged_el = doc.GetElement(_first(tagged_el_id))
                if tagged_el is None or not isinstance(tagged_el, FamilyInstance):
                    continue
                tagged_el_location = tagged_el.Location
                if tagged_el_location is None or getattr(tagged_el_location, 'Point', None) is None:
                    continue

                base = tagged_el_location.Point
                tag_position = tag.TagHeadPosition


                tagged_el_fOrientation = tagged_el.FacingOrientation
                dx, dy = tagged_el_fOrientation.X, tagged_el_fOrientation.Y  
                len2 = dx*dx + dy*dy
                if len2 <= EPS:
                    continue
                if abs(len2 - 1.0) > 1e-6:
                    inv = 1.0 / (len2 ** 0.5)
                    dx *= inv; dy *= inv


                diag_xor = (dx > 0.0 and dy < 0.0) or (dx < 0.0 and dy > 0.0)

                try:
                    text = tag.TagText or ''
                except:
                    text = ''
                n = _linecount(text)
                name = tag.Name.lower()
                
                if '100' in name:
                    if not 'ok' in name:
                        d = offsets_100.get((n, diag_xor))
                        if d is None:
                            d = offsets_100.get((n, True)) or offsets_100.get((n, False)) or 2.0
                    elif 'ok' in name:
                        if diag_xor == True:
                            d = (offsets_100.get((n, diag_xor)))*-1.00
                        elif diag_xor == False:
                            d = (offsets_100.get((n, diag_xor)))*-1.00
                        if d is None:
                            d = (offsets_100.get((n, True)))*-1.00 or (offsets_100.get((n, False)))*-1.00 or 2.0
                elif '50' in name:
                    if not 'ok' in name:
                        d = offsets_50.get((n, diag_xor))
                        if d is None:
                            d = offsets_50.get((n, True)) or offsets_50.get((n, False)) or 2.0
                    elif 'ok' in name:
                        d = (offsets_50.get((n, diag_xor)))*-0.60
                        if d is None:
                            d = (offsets_50.get((n, True)) or offsets_50.get((n, False)) or 2.0)*-0.60
                
                else:
                    if not 'ok' in name:
                        d = offsets_200.get((n, diag_xor))
                        if d is None:
                            d = offsets_200.get((n, True)) or offsets_200.get((n, False)) or 2.0
                    elif 'ok' in name:
                        d = (offsets_200.get((n, diag_xor)))*-0.60
                        if d is None:
                            d = (offsets_200.get((n, True)) or offsets_200.get((n, False)) or 2.0)*-0.60


                move_x = (base.X + dx * d) - tag_position.X
                move_y = (base.Y + dy * d) - tag_position.Y
                if abs(move_x) <= EPS and abs(move_y) <= EPS:
                    continue

                move = XYZ(move_x, move_y, 0.0)


                if hasattr(tag, 'Pinned') and tag.Pinned:
                    tag.Pinned = False

                try:
                    move_el(doc, tag.Id, move)
                except:
                    print('❌ Failed to move tag')
                    continue

def _first(it):
    """ Return the first item in the iterator, or None if the iterator is empty. """
    for x in it:
        return x
    return None


def _linecount(text):
    if not text:
        return 1
    c = 0
    for ln in text.splitlines():
        if ln and ln.strip():
            c += 1
    if c < 1:
        return 1
    return c

#  _      ____  _  _     
# / \__/|/  _ \/ \/ \  /|
# | |\/||| / \|| || |\ ||
# | |  ||| |-||| || | \||
# \_/  \|\_/ \|\_/\_/  \| MAIN SCRIPT

if __name__ == '__main__':
    main()
