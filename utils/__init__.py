import os
import zipfile


def unzip(zip_path, dest=None):
    if dest is None:
        dest = os.path.dirname(zip_path)
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(dest)
