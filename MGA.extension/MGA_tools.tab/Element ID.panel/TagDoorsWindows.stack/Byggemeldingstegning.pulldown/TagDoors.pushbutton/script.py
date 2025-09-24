def add_tags(doc, element, views, tag_family, wall_normal, element_type):
    if not tag_family:
        logging.debug("❌Tag family not found")
        return
    
    tag_offset_distance =  4.3
    

    for view in views:
        view_name = view.Name.lower()
        level_name = doc.GetElement(element.LevelId).Name.lower()
        
        if elements_visible_in_view(doc, view, element) and level_name in view_name:
            tag_offset = wall_normal.Multiply(1.2)
            tag_location = element.Location.Point.Add(tag_offset)

            if view.Id not in placed_tag_positions:
                placed_tag_positions[view.Id] = []

            
            for placed_tag in placed_tag_positions[view.Id]:
                
                if tag_location.DistanceTo(placed_tag) < tag_offset_distance:
                    tag_location = tag_location.Add(XYZ(0, -(tag_offset_distance/5), 0))
            
            ref = Reference(element)
            
            tag =IndependentTag.Create(
                doc,
                tag_family.Id,
                view.Id,
                ref,
                False,
                TagOrientation.Horizontal,
                tag_location

            )
            
            placed_tag_positions[view.Id].append(tag_location)
            logging.debug("Tag added to {} for {}".format(view_name, element_type))

# Get all tags of a category🏷️
def get_tags(category):
    return list(FilteredElementCollector(doc).OfCategory(category).WhereElementIsElementType())

# Find a tag🏷️
def find_tags(tags, keywords, alternative=None):
    tag = next((tag for tag in tags if keywords in tag.Family.Name),None)
    if tag:
        return tag
    
    if alternative:
        return next((tag for tag in tags if alternative in tag.Family.Name),None)

    return None