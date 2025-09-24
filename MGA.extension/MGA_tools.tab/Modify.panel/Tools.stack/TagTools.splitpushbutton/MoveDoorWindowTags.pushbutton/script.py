# encoding: utf-8
import os


this_dir = os.path.dirname(__file__)


# Go up one folder (to Mark.splitpushbutton) then into DoorID.pushbutton
door_script = os.path.abspath(os.path.join(this_dir, '..', 'MoveDoorTags.pushbutton', 'script.py'))
window_script = os.path.abspath(os.path.join(this_dir, '..', 'MoveWindowTags.pushbutton', 'script.py'))




# Kjøre dem med execfile (IronPython)
exec(open(door_script).read())
exec(open(window_script).read()) 


