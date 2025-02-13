from urllib.parse import urlparse
import os
from requests.structures import CaseInsensitiveDict

def get_mime_type_from_headers(headers: CaseInsensitiveDict):
    content_type: str = headers.get('content-type')
    if not content_type:
        return None
    mime_type = content_type.split(';')[0].strip()
    return mime_type

def guess_filename_from_url(url):
    parsed_url = urlparse(url)    
    path = parsed_url.path    
    filename = os.path.basename(path)
    if '.' in filename:
        return filename
    else:
        return None

def get_filename_from_headers(headers: CaseInsensitiveDict):
    content_disposition = headers.get('Content-Disposition')

    if content_disposition:
        # Look for the filename in the Content-Disposition header
        filename = None
        cd_parts = content_disposition.split(';')
        for part in cd_parts:
            part: str
            if 'filename=' in part:
                # Strip out the 'filename=' and any surrounding quotes
                filename = part.split('=')[1].strip().strip('"')
                break
        return filename

    return None