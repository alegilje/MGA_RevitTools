# encoding: utf-8
import json
from datetime import date
class Metadata_Handler:
    def __init__(self, metadata_file, log = None):
        self.metadata_file = metadata_file
        self.file_name = None
        self.metadata = {}
        self.log = log

    def metadata_load(self):
        """Loads metadata from a file"""
        try:
            with open(self.metadata_file, 'r') as f:
                self.metadata = json.load(f)
                
                return self.metadata
        except Exception as e:
            self.log.warning("Metadata load failed. Line 20. An error occurred while loading metadata: {}. Initializing as empty dictionary.".format(e))
            self.metadata = {}  # Initialiser til en tom dictionary ved feil
            return self.metadata

        
    def metadata_get_file(self, file_name):
        """Gets metadata for a specific file from a metadata collection
        
        Args:
            metadata (dict): The metadata collection to query
            file_name (str): The name of the file to get metadata for
        
        Returns:
            dict: The metadata for the given file or None if not found
        """
        self.file_name = file_name
        file_metadata = self.metadata.get(self.file_name, None)
        if file_metadata:
            return file_metadata
        else:
            self.log.info("No metadata found for file: {}".format(file_name))
            return None

    def metadata_get_key(self, key):
        """Henter en spesifikk nøkkelverdi for en fil."""

        if not isinstance(self.metadata, dict):
            self.log.warning("Line 47. Error: Metadata is not a dictionary.")
            return None
        if self.file_name not in self.metadata:
            self.log.warning("Line 50.Error: File '{}' not found in metadata.".format(self.file_name))
            return None
        return self.metadata.get(self.file_name, {}).get(key, None)
    

    def metadata_save(self):
        # Sjekk strukturen til metadata før lagring og konverter alle verdier til strenger
        try:
            cleaned_metadata = {
                file_name: {key: str(value) for key, value in file_data.items()}
                for file_name, file_data in self.metadata.items()
            }
            self.log.info("Saving metadata: {}".format(cleaned_metadata))
            
            # Lagre til fil
            with open(self.metadata_file, 'w') as f:
                json.dump(cleaned_metadata, f, indent=4)
                self.log.info("Metadata saved to file: {}".format(self.metadata_file))
        except Exception as e:
            self.log.error("An error occurred while saving metadata: {}".format(e))


    def metadata_update(self, metadata_dict):
        """Updates the version number for a file in the metadata."""
        if self.file_name not in self.metadata:
            self.metadata[self.file_name] = {}
            self.log.info("Metadata_Update:Added new metadata for file: {}".format(self.file_name))

        # Oppdater nøkler og verdier basert på metadata_dict
        for key, value in metadata_dict.items():
            self.log.info("----Metadata_Update:Updating metadata for file: {}, Key: {}, Value: {}".format(self.file_name, key, value))
            # Hvis det er en nested dictionary, behandle den uten å konvertere til streng
            if isinstance(value, dict):
                self.log.warning("Metadata_Update:Warning: Nested dictionary detected for key '{}'. No conversion to string.".format(key))
            self.metadata[self.file_name][key] = value  # Behold original datatypen for verdien

            if "last_updated" not in self.metadata[self.file_name]:
                self.metadata[self.file_name]["last_updated"] = str(date.today().strftime('%d.%m.%y'))
            return self.metadata
            



    def metadata_create_new(self, metadata):
        """Creates a new metadata file."""
        if not isinstance(metadata, dict):
            raise TypeError("metadata must be a dictionary")
        self.metadata = metadata  # Sørg for at metadata er en dictionary
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f)
                self.log.info("Created new metadata file: {}, Metadata: {}".format(self.metadata_file, metadata))
        except Exception as e:
            raise IOError("Create_Metadata: An error occurred while creating the metadata file: {}".format(e))
        return self.metadata_file




