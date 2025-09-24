# encoding: utf-8

#  _  _      ____  ____  ____  _____ 
# / \/ \__/|/  __\/  _ \/  __\/__ __\
# | || |\/|||  \/|| / \||  \/|  / \  
# | || |  |||  __/| \_/||    /  | |  
# \_/\_/  \|\_/   \____/\_/\_\  \_/  
# IMPORTS
#===========================================================================================================#

# STANDARD LIBRARY IMPORTS
from datetime import date

# Imports from Autodesk and pyRevit

from tools._transactions import revit_transaction

def update_lookup_parameters(doc,object,param_names,param_values):
    if len(param_names) != len(param_values):
        raise ValueError("Parameter namen and param_values must have same length")
    for param_name, param_value in zip(param_names, param_values):
        param_to_set = object.LookupParameter(param_name)
        if param_to_set is None:
            print('Parameter {} not found').format(param_name)
            continue
        if param_to_set.IsReadOnly:
            print('Parameter {} is read-only').format(param_name)
            continue
            
        with revit_transaction(doc, "Change lookUp parameter"):
            param_to_set.Set(param_value)
            

def change_ProjectParameter_Value(doc,parameter_name,parameter_value):
    parameter = doc.ProjectInformation.LookupParameter (parameter_name)
    if parameter:
        parameter.Set(parameter_value)
        #print("Uptdated: {} to {}".format(parameter_name, parameter.AsString()))
    else:
       print("No paranmeter named {}") .format(parameter_name)
    return parameter
            