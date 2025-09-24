# -*- coding: utf-8 -*-

#  _  _      ____  ____  ____  _____ 
# / \/ \__/|/  __\/  _ \/  __\/__ __\
# | || |\/|||  \/|| / \||  \/|  / \  
# | || |  |||  __/| \_/||    /  | |  
# \_/\_/  \|\_/   \____/\_/\_\  \_/ IMPORTS
#----------------------------------STANDARD LIBRARY IMPORTS----------------------------------#
import os, re, shutil, zipfile

#---------------------------- AUTODESK REVIT AND PYREVIT IMPORTS ----------------------------#
from Autodesk.Revit.DB import FilteredElementCollector, TextNote
from Autodesk.Revit.UI import TaskDialog


#  _     ____  ____  _  ____  ____  _     _____ ____ 
# / \ |\/  _ \/  __\/ \/  _ \/  __\/ \   /  __// ___\
# | | //| / \||  \/|| || / \|| | //| |   |  \  |    \
# | \// | |-|||    /| || |-||| |_\\| |_/\|  /_ \___ |
# \__/  \_/ \|\_/\_\\_/\_/ \|\____/\____/\____\\____/ VARIABLES
# === 1. Dynamiske stier og søkemappe ===

uidoc = __revit__.ActiveUIDocument
doc   = uidoc.Document

brukerprofil = os.environ['USERPROFILE']

#  _____ _     _      ____  _____  _  ____  _      ____ 
# /    // \ /\/ \  /|/   _\/__ __\/ \/  _ \/ \  /|/ ___\
# |  __\| | ||| |\ |||  /    / \  | || / \|| |\ |||    \
# | |   | \_/|| | \|||  \__  | |  | || \_/|| | \||\___ |
# \_/   \____/\_/  \|\____/  \_/  \_/\____/\_/  \|\____/ FUNCTIONS

#----------------------------------------MAIN------------------------------------------------#
def main():
    # Mulige stier til Byggdetaljer
    mulige_sokestier = [
        os.path.join(brukerprofil, 'DC', 'ACCDocs', 'MGA', 'Boligbank', 'Project Files', 'Byggdetaljer'),
        os.path.join(brukerprofil, 'MGA', 'Boligbank', 'Project Files', 'Byggdetaljer'),
    ]

    sok_mappe = None
    for sti in mulige_sokestier:
        if os.path.exists(sti):
            sok_mappe = sti
            break
          
    if not sok_mappe:
        TaskDialog.Show("❌Error", "Søkemappen 'Byggdetaljer' ble ikke funnet under brukeren:{}. Legg til Boligbank under Selected Project i Autodesk Desktop Connector.".format(brukerprofil))
        raise SystemExit()

    nedlastinger = os.path.join(brukerprofil, 'Downloads')

    revit_filnavn = os.path.splitext(doc.PathName)[0]
    revit_filnavn = os.path.basename(revit_filnavn)
    destinasjonsmappe = os.path.join(nedlastinger, revit_filnavn + ' - Detaljer')

    # Sørg for at en helt ren mappe opprettes (hvis rest fra tidligere)
    if os.path.exists(destinasjonsmappe):
        shutil.rmtree(destinasjonsmappe)
    os.makedirs(destinasjonsmappe)

    # === 3. Hent alle tekstnotater i prosjektet ===
    textnotes = FilteredElementCollector(doc).OfClass(TextNote)

    # === 4. Finn detaljhenvisninger (f.eks. 21.103, 23.450-E osv.) ===
    detaljmønster = re.compile(r'\b\d{2}\.\d{3}(?:-[a-zA-Z0-9]+)?\b')
    detaljkoder = set()

    for note in textnotes:
        tekst = note.Text.strip()
        funn = detaljmønster.findall(tekst)
        detaljkoder.update(funn)

    if not detaljkoder: # Hvis ingen detaljkoder ble funnet, prøv å finne detaljkoder 
        TaskDialog.Show("❌Error", "Ingen detaljkoder ble funnet i prosjektet.")
        raise SystemExit()

    # === 5. Kopier samsvarende PDF-filer fra søkemappen ===
    kopierte_filer = 0
    for root, dirs, files in os.walk(sok_mappe):
        for fil in files:
            if not fil.lower().endswith('.pdf'):
                continue

            filnavn = os.path.splitext(fil)[0]
            normalized_filnavn = filnavn.replace(" ", "").replace("–", "-").lower()

            for kode in detaljkoder:
                normalized_kode = kode.replace(" ", "").replace("–", "-").lower()
                if normalized_filnavn.startswith(normalized_kode):
                    kilde_fil = os.path.join(root, fil)
                    dest_fil = os.path.join(destinasjonsmappe, fil)
                    if not os.path.exists(dest_fil):
                        shutil.copy2(kilde_fil, dest_fil)
                        kopierte_filer += 1
                    break

    # === 6. Lag ZIP-fil av eksportmappen ===
    zip_filsti = os.path.join(nedlastinger, revit_filnavn + ' - Detaljer.zip')
    with zipfile.ZipFile(zip_filsti, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for foldername, subfolders, filenames in os.walk(destinasjonsmappe):
            for filename in filenames:
                full_path = os.path.join(foldername, filename)
                rel_path = os.path.relpath(full_path, destinasjonsmappe)
                zipf.write(full_path, rel_path)

    # === 7. Slett u-zippet mappe etterpå ===
    shutil.rmtree(destinasjonsmappe)

    # === 8. Ferdigmelding ===
    TaskDialog.Show("✅ Success", " Ferdig! {} PDF-filer ble kopiert og pakket i:\n{}".format(kopierte_filer, zip_filsti))

#  _      ____  _  _     
# / \__/|/  _ \/ \/ \  /|
# | |\/||| / \|| || |\ ||
# | |  ||| |-||| || | \||
# \_/  \|\_/ \|\_/\_/  \| MAIN SCRIPT

if __name__ == '__main__':
    main()