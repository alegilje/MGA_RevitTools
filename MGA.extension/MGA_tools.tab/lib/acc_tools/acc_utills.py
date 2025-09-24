# encoding: utf-8


import os
import requests


from pyrevit import forms




def download_file_from_ACC(download_url, file_name, temp_file_location, request_header, textblock_print=None):
     if textblock_print is not None:
          if not os.path.exists(temp_file_location):
                    textblock_print.Text +=("Can not find folder. Choose one:")
                    temp_file_location = forms.pick_folder(title="Velg en mappe hvor filen skal lagres\n")
          
          file_response = requests.get(download_url)
          if file_response.status_code == 200:
               file_path = os.path.join(temp_file_location, file_name)
               try:
                    with open(file_path, 'wb') as file:
                         file.write(file_response.content)
                    textblock_print.Text += ("File '{}' downloaded successfully.\n".format(file_name))
                    return file_path
               
               except (ValueError, KeyError, TypeError) as e:
                    textblock_print.Text +=("Error: {}\n".format(e))
          
          else:
               textblock_print.Text +=("Failed to download the file: HTTP Status Code {}\n".format(file_response.status_code))
     else:
          if not os.path.exists(temp_file_location):
                    print("Can not find folder. Choose one:")
                    temp_file_location = forms.pick_folder(title="Velg en mappe hvor filen skal lagres")
          
          file_response = requests.get(download_url)
          if file_response.status_code == 200:
               file_path = os.path.join(temp_file_location, file_name)
               try:
                    with open(file_path, 'wb') as file:
                         file.write(file_response.content)
                    print("File '{}' downloaded successfully.".format(file_name))
                    return file_path
               
               except (ValueError, KeyError, TypeError) as e:
                    print("Error: {}".format(e))
          
          else:
               print("Failed to download the file: HTTP Status Code {}".format(file_response.status_code))

        


       














