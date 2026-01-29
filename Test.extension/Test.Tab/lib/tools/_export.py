# encoding: utf-8
"""
Verkyøy for eksport av tegning fra Revit
"""
# Imports
import encodings
from hmac import new
import os
import csv
from Autodesk.Revit.DB import\
    FilteredElementCollector\
    ,ViewSheetSet\
    ,PrintRange
from tools._transactions import revit_transaction

uiapp = __revit__  # Using __revit__ to access Revit's application
app = uiapp.Application

def print_exising_sheet_set(doc, sheet_set, temp_file_location, filename):
    print_manager = doc.PrintManager
    try:
        print_manager.PrintToFile = True
        print_manager.PrintRange = PrintRange.Select
        print_manager.CombinedFile = True
        
    except Exception as e:
        print(e)
    
    pdf_filename = os.path.join("{}\{}.pdf").format(temp_file_location, filename)

    if os.path.exists(pdf_filename):
        print("PDF file, {} already exist".format(filename))
        os.remove(pdf_filename)
        print("Existing PDF deleted")

    print_manager.PrintToFileName = pdf_filename
    
    with revit_transaction(doc, "Set up print settings"):
        print_manager.Apply()
        try: 
            print_manager.SelectNewPrintDriver("Foxit PhantomPDF Printer")
            print_manager.CombinedFile = True
        except:
            print("Printer: Foxit PhantomPDF Printer Printer do not exsist")
            try:
                print_manager.SelectNewPrintDriver("Adobe PDF")
                print_manager.CombinedFile = True
            except:
                print("Printer: Adobe PDF do not exsist")
                try:
                    print_manager.SelectNewPrintDriver("Microsoft Print to PDF")
                    print_manager.CombinedFile = True
                except:
                    print_manager.CombinedFile = False
                    raise Exception("Printer not found: Microsoft Print to PDF, PDF-XChange, or Adobe PDF. Please install one of these printers and try again.")
        
        print_manager.Apply()

        view_sheet_setting = print_manager.ViewSheetSetting
        view_sheet_setting.CurrentViewSheetSet = sheet_set

    print_manager.SubmitPrint()
    print("PDF print job sent successfully. Check file at {}".format(pdf_filename))

def get_existing_sheet_set(doc, set_name):
    sheet_sets = FilteredElementCollector(doc).OfClass(ViewSheetSet).ToElements()
    for sheet_set in sheet_sets:
        if sheet_set.Name == set_name:
            return sheet_set
    return None           

def export_to_csv(column_order, data, filename):

    clean_data = []
    for row in data:
        cleaned_row = {}
        for key, value in row.items():
            # Fjern spesialtegn eller erstatte dem med riktige tegn (f.eks. '\xf8' til 'ø')
            cleaned_row[key] = str(value).replace('\xf8', 'ø').replace('\x80', '')
        clean_data.append(cleaned_row)


    with open(filename, "w") as file:
        writer = csv.writer(file, delimiter=";", quotechar='"', quoting=csv.QUOTE_MINIMAL)
    
        # Skriv overskrifter
        writer.writerow(column_order)
            # Skriv dataene til CSV
        for row in clean_data:
            ordered_row = [row.get(key, '') for key in column_order]  # Bruk `get()` for å unngå KeyError
            writer.writerow(ordered_row)

        file.flush()
        file.close()