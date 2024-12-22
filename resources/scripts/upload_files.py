import os
import requests

def upload_jpg_files(temp_folder_path: str, upload_url: str):
    # Check if the provided directory exists
    if not os.path.isdir(temp_folder_path):
        print(f"Directory {temp_folder_path} does not exist.")
        return

    # Iterate over all files in the directory
    for filename in os.listdir(temp_folder_path):
        # Check if the file is a .jpg file
        if filename.endswith('.jpg'):
            file_path = os.path.join(temp_folder_path, filename)
            try:
                # Open the file in binary mode
                with open(file_path, 'rb') as file:
                    # Prepare the files payload as expected by FastAPI
                    files = {'file': (filename, file, 'image/jpeg')}
                    # Make a POST request to upload the file
                    response = requests.post(upload_url, files=files)
                    # Check the response status
                    if response.status_code == 200:
                        print(f"Successfully uploaded {filename}.")
                    else:
                        print(f"Failed to upload {filename}. Status code: {response.status_code}, Response: {response.text}")
            except Exception as e:
                print(f"Error reading {filename}: {e}")
        else:
            print(f"Skipping {filename}: Not a .jpg file.")

# Usage
if __name__ == "__main__":
    TEMP_FOLDER_PATH = './temp'  # Adjust this path if necessary
    UPLOAD_URL = 'http://localhost:8000/upload-file/'  # Adjust the URL according to your server

    upload_jpg_files(TEMP_FOLDER_PATH, UPLOAD_URL)
