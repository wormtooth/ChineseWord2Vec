"""Download files with a progress bar.
"""

import requests
from tqdm import tqdm


def _save_resp_to_file(resp: requests.Response, path: str, bar: tqdm):
    with open(path, 'wb') as file:
        for data in resp.iter_content(chunk_size=1024):
            size = file.write(data)
            if bar is not None:
                bar.update(size)
    if bar is not None:
        bar.close()

def download(url: str, path: str, show_progress: bool=True):
    """Download file from `url` to `path`.

    Args:
        url (str): The url of the file.
        path (str): The path of the file to save on disk.
        show_progress (bool, optional): Whether to show progress bar. Defaults to True.
    """
    resp = requests.get(url, stream=True)
    total = int(resp.headers.get('content-length', 0))
    bar = None
    if show_progress:
        bar = tqdm(
            desc=path, total=total, unit='iB', unit_scale=True, unit_divisor=1024
        )
    _save_resp_to_file(resp, path, bar)


def download_gdoc(file_id: str, path: str, show_progress: bool=True):
    """Download file from Google drive.

    Args:
        file_id (str): File id of the document on Google drive.
        path (str): The path of the file to save on disk.
        show_progress (bool, optional): Whether to show progress bar. Defaults to True.
    """
    url = 'https://docs.google.com/uc?export=download'
    s = requests.Session()
    params = {'id': file_id}
    resp = s.get(url, params=params, stream=True)
    token = None
    for key, val in resp.cookies.items():
        if key.startswith('download_warning'):
            token = val
            break
    if token is not None:
        params['confirm'] = token
        resp = s.get(url, params=params, stream=True)

    total = int(resp.headers.get('content-length', 0))
    bar = None
    if show_progress:
        bar = tqdm(
            desc=path, total=total, unit='iB', unit_scale=True, unit_divisor=1024
        )
    _save_resp_to_file(resp, path, bar)
