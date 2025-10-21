import os, hashlib
from pathlib import Path

def traverse_directory(directory, restrict_extensions: list=None, ignore_dirs: list = []):
    for root, dirs, files in os.walk(directory):
        # Exclude the directories listed in ignore_dirs
        dirs[:] = [d for d in dirs if d not in ignore_dirs]

        for file in files:
            _, file_extension = os.path.splitext(file)
            if file_extension in restrict_extensions: 
                file_path = os.path.join(root, file)
                yield file_path
                
def get_file_bytes(file_extension, file_path) -> bytes:
    # Ensure the file exists
    file = Path(file_path)
    file_bytes = None
    
    if not file.is_file():
        raise FileNotFoundError(f"The file {file_path} does not exist.")
    
    file_bytes = file.read_bytes()
    file_bytes_str = file_bytes.decode(encoding="utf8")

    return bytes(file_bytes_str, encoding="utf8")

def get_relative_path(path, base_path):
    return os.path.relpath(path, base_path)

def generate_uuid(string: str, length: int=24) -> str:
    
    # Create a SHA-256 hash object
    sha256 = hashlib.sha256()

    # Convert the string to bytes and update the hash object
    sha256.update(string.encode('utf-8'))

    # Get the hexadecimal representation of the hash
    hex_digest = sha256.hexdigest()

    # Return the UUID as a string
    return hex_digest[:length]

def module_path_to_dotted_name(module_path: str) -> str:
    if module_path is None:
        return None
    else:
        return '.'.join(module_path.split('/')[:-1] + [module_path.split('/')[-1].split('.')[0]])

def type_seperator(type_str: str) -> list:
    return type_str.split(" | ")