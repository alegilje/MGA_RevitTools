import os

def open_first_file_with_prefix(directory, search_prefix):
    """
    Open the first file in 'directory' that starts with 'search_prefix'.
    
    Parameters:
        directory (str): The path to the folder to search in.
        search_prefix (str): The prefix of the file to look for.
    """
    directory = os.path.expanduser(directory)
    
    for filename in os.listdir(directory):
        if filename.startswith(search_prefix):
            file_path = os.path.join(directory, filename)
            os.startfile(file_path)
            return file_path  # Return the path of the opened file
    
    # If no file is found
    return None