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
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from pyrevit import revit, forms, DB
from pyrevit.framework import List
import math

#  _     ____  ____  _  ____  ____  _     _____ ____ 
# / \ |\/  _ \/  __\/ \/  _ \/  __\/ \   /  __// ___\
# | | //| / \||  \/|| || / \|| | //| |   |  \  |    \
# | \// | |-|||    /| || |-||| |_\\| |_/\|  /_ \___ |
# \__/  \_/ \|\_/\_\\_/\_/ \|\____/\____/\____\\____/ VARIABLES
#----------------------------- GLOBALS / CONTEXT --------------------------------------#
uidoc = __revit__.ActiveUIDocument
app = __revit__.Application
doc   = revit.doc
view  = revit.active_view
print(doc.Title)
linked_open_docs = []
linked_open_docssss = []
opened_docs = []
for p in app.Documents:
    if p.IsLinked:
        linked_open_docs.append(p.Title)
    if not p.IsLinked and p.Title not in doc.Title and p.Title in linked_open_docs:
        opened_docs.append(p.Title)
for p in app.Documents:
    if p.IsLinked and p.Title in opened_docs:
            linked_open_docssss.append(p.Title)
print(linked_open_docssss,opened_docs)

# Finn alle RevitLinkInstances
link_instances = FilteredElementCollector(doc).OfClass(RevitLinkInstance).ToElements()
pbp = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_ProjectBasePoint).FirstElement()
pbp_pos = pbp.Position

east_ft  = pbp.get_Parameter(BuiltInParameter.BASEPOINT_EASTWEST_PARAM).AsDouble()
north_ft = pbp.get_Parameter(BuiltInParameter.BASEPOINT_NORTHSOUTH_PARAM).AsDouble()
elev_ft  = pbp.get_Parameter(BuiltInParameter.BASEPOINT_ELEVATION_PARAM).AsDouble()
ang_rad  = pbp.get_Parameter(BuiltInParameter.BASEPOINT_ANGLETON_PARAM).AsDouble()
east = UnitUtils.ConvertFromInternalUnits(east_ft, UnitTypeId.Meters)
north = UnitUtils.ConvertFromInternalUnits(north_ft, UnitTypeId.Meters)
print(north, east)
for link_instance in link_instances:
    # Få tak i det linkede dokumentet
    linked_doc = link_instance.GetLinkDocument()
    linked_doc_title = linked_doc.Title
    if linked_doc_title in linked_open_docssss:
        if linked_doc:
            # Hent Project Base Point fra det linkede dokumentet
            link_pbp = FilteredElementCollector(linked_doc).OfCategory(BuiltInCategory.OST_ProjectBasePoint).FirstElement()
            if link_pbp:
                # Hent koordinater i det linkede dokumentets koordinatsystem
                linked_location = link_pbp.Position
                
                
                # Transformér til det aktive dokumentets koordinatsystem
                transform = link_instance.GetTransform()
                transformed_point = transform.OfPoint(linked_location)
                print("Transformed point:{}".format(transformed_point))
                east_link = UnitUtils.ConvertFromInternalUnits(transformed_point.X, UnitTypeId.Meters)
                north_link = UnitUtils.ConvertFromInternalUnits(transformed_point.Y, UnitTypeId.Meters)
                elevation_link = UnitUtils.ConvertFromInternalUnits(transformed_point.Z, UnitTypeId.Meters)
                
                new_east = east + east_link
                new_north = north + north_link
                if elevation_link < 0.0:

                    new_elev = -(elevation_link)
                else:
                    new_elev = elevation_link
                x_axis = transform.BasisY
                print("North: {}, Easth: {} ,Elevation: {}".format(new_north, new_east, new_elev))

                # Linkens rotasjon i forhold til verdens X-akse
                angle_radians = math.atan2(x_axis.Y, x_axis.X)
                angle_degrees = math.degrees(angle_radians)

                # Normaliser til 0-360
                if angle_degrees < 0:
                    angle_degrees += 360

                # Hent prosjektets rotasjon (radianer -> grader)
                project_rotation_deg = math.degrees(ang_rad)
                

                # Revit måler fra nord (Y-akse), så vi må rotere referansen 90°
                angle_from_north = 90 - angle_degrees

                # Juster for prosjektets rotasjon
                angle_to_true_north = angle_from_north - project_rotation_deg

                # Normaliser igjen
                angle_to_true_north = angle_to_true_north % 360

                print("True North: {}°".format(angle_to_true_north))
