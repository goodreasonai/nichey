from urllib.parse import urlparse
import os
from requests.structures import CaseInsensitiveDict
import mimetypes
import tiktoken


def get_mime_type_from_headers(headers: CaseInsensitiveDict):
    content_type: str = headers.get('content-type')
    if not content_type:
        return None
    mime_type = content_type.split(';')[0].strip()
    return mime_type


def get_ext_from_path(path, with_dot=False):
    splitsville = os.path.splitext(path)
    if len(splitsville) > 1:
        has_dot = splitsville[1]
        if not len(has_dot):
            return None
        if with_dot or has_dot[0] != '.':
            return has_dot
        return has_dot[1:]
    return None


# Includes extension
def get_filename_from_path(path):
    splitsville = os.path.split(path)
    if len(splitsville) > 1:
        return splitsville[1]
    return None


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


# No dot
def get_ext_from_mime_type(mimetype):
    extensions = mimetypes.guess_all_extensions(mimetype)
    if len(extensions):
        with_dot = extensions[0]
        if with_dot[0] == '.':
            return with_dot[1:]
        return with_dot
    return None


def get_mime_type_from_ext(ext):
    # Ensure the extension has a leading dot
    if not ext.startswith('.'):
        ext = '.' + ext
    mime_type, _ = mimetypes.guess_type('file' + ext)
    return mime_type


tokenizer = tiktoken.get_encoding("gpt2")  # GPT2 tokenizer is also used for GPT-3, and maybe GPT-4?
def get_token_estimate(txt):
    tokens = tokenizer.encode(txt)
    return len(tokens)
