import tempfile
import os
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from requests_toolbelt.multipart.decoder import MultipartDecoder
from .utils import get_mime_type_from_headers, guess_filename_from_url, get_filename_from_headers
from requests.structures import CaseInsensitiveDict
import requests
import json
import sys


class ScrapeMetadata():
    def __init__(self):
        self.author: str = ""
        self.desc: str = ""
        self.title: str = ""
        self.preview_image_url: str = ""
        self.favicon_url: str = ""
        self.content_type: str = ""


class ScrapeDataConsumer:
    def __init__(self, data_path):
        self.data_path = data_path

    def __enter__(self):
        # Returning the path to the data file
        return self.data_path

    def __exit__(self, exc_type, exc_value, traceback):
        # Remove the temporary file when done
        if os.path.exists(self.data_path):
            os.remove(self.data_path)


class ScrapeScreenshotConsumer:
    def __init__(self, data_paths, data_types):
        self.data_paths = data_paths
        self.data_types = data_types

    def __enter__(self):
        # Returning the path to the data file
        return self.data_paths, self.data_types

    def __exit__(self, exc_type, exc_value, traceback):
        # Remove the temporary file when done
        for path in self.data_paths:
            if os.path.exists(path):
                os.remove(path)


class ScrapeResponse():
    success: bool
    status: int
    url: str
    headers: dict
    data_path: str
    screenshot_paths: list
    screenshot_mimetypes: list
    metadata: ScrapeMetadata
    def __init__(self, success, status, url, headers):
        self.success = success
        self.status = status
        self.url = url
        self.screenshot_paths = []
        self.screenshot_mimetypes = []
        self.headers = CaseInsensitiveDict(headers)
        self._determine_content_type()
        self.data_path = None

    def _determine_content_type(self):
        meta = ScrapeMetadata()
        meta.content_type = get_mime_type_from_headers(self.headers)
        # If it's HTML, we'll get it from the <title> tag, so we don't have to do this here
        if meta.content_type != 'text/html':
            filename = get_filename_from_headers(self.headers)
            if filename:
                meta.title = filename
            else:
                guessed_filename = guess_filename_from_url(self.url)
                if guessed_filename:
                    meta.title = guessed_filename
        self.metadata = meta

    def _set_metadata_from_html(self, content):
        soup = BeautifulSoup(content, 'html.parser')

        # TITLE: Get title if exists
        if soup.title.string:
            self.metadata.title = soup.title.string.strip()

        # DESCRIPTION: Check the open graph description first, then meta description
        og_description = soup.find('meta', attrs={'property': 'og:description', 'content': True})
        if og_description:
            self.metadata.desc = og_description['content'].strip()
        else:
            # Fallback to meta description
            meta_description = soup.find('meta', attrs={'name': 'description', 'content': True})
            if meta_description:
                self.metadata.desc = meta_description['content'].strip()
        
        # AUTHOR: Check Open Graph author first
        og_author = soup.find('meta', attrs={'property': 'og:author', 'content': True})
        if og_author:
            self.metadata.author = og_author['content'].strip()
        else:
            # Fallback to meta author if og:description not found
            meta_author = soup.find('meta', attrs={'name': 'author', 'content': True})
            if meta_author:
                self.metadata.author = meta_author['content'].strip()

        # PREVIEW IMAGE
        og_image = soup.find('meta', attrs={'property': 'og:image', 'content': True})
        if og_image:
            self.metadata.preview_image_url = og_image['content']
        else:
            # Fallback to Twitter image if og:image not found
            twitter_image = soup.find('meta', attrs={'name': 'twitter:image', 'content': True})
            if twitter_image:
                self.metadata.preview_image_url = twitter_image['content']

        # FAVICON
        favicon = soup.find('link', rel=lambda x: x and x.lower() in ['icon', 'shortcut icon'])
        favicon_url = favicon['href'] if favicon and favicon.has_attr('href') else None
        if favicon_url:
            # Resolving the favicon URL against the base URL
            self.metadata.favicon_url = urljoin(self.url, favicon_url)

    def set_data(self, content):
        try:
            tmp = None
            if self.metadata.content_type == 'text/html':
                self._set_metadata_from_html(content)
            tmp = tempfile.NamedTemporaryFile(delete=False)
            tmp.write(content)
            self.data_path = tmp.name
        finally:
            if tmp:
                tmp.close()

    def add_screenshot(self, content, mimetype):
        try:
            tmp = tempfile.NamedTemporaryFile(delete=False)
            tmp.write(content)
            self.screenshot_paths.append(tmp.name)
            self.screenshot_mimetypes.append(mimetype)
        finally:
            tmp.close()

    def consume_data(self):
        # Designed to be used like...
        # with scrape.consume_data() as data_path:
        #     # ... do stuff with data_path
        # And removes the file when done.
        if not self.data_path:
            raise Exception("There is no scraped data")
        curr_data_path = self.data_path
        self.data_path = None
        return ScrapeDataConsumer(curr_data_path)
    
    def consume_screenshots(self):
        if not len(self.screenshot_paths):
            return ScrapeScreenshotConsumer([], [])
        these_paths = list(self.screenshot_paths)
        these_types = list(self.screenshot_mimetypes)
        self.screenshot_paths = []
        self.screenshot_mimetypes = []
        return ScrapeScreenshotConsumer(these_paths, these_types)

    def close(self):
        cleaned = 0
        if self.data_path and os.path.exists(self.data_path):
            os.remove(self.data_path)
            cleaned += 1
        if len(self.screenshot_paths):
            print(f"Scrape response screnshots being removed in garbage collection; this is a sign of buggy code. Scraped URL was '{self.url}'.")
            for ss in self.screenshot_paths:
                if os.path.exists(ss):
                    os.remove(ss)
                    cleaned += 1
        return cleaned

    def __del__(self):
        # Ensure the temporary file is deleted when the object is destroyed
        try:
            cleaned = self.close()
            if cleaned:
                print(f"{cleaned} Scrape response data items being removed in garbage collection; this is a sign of buggy code. Scraped URL was '{self.url}'.")

        except Exception as e:
            print(f"Error cleaning up ScrapeResponse for '{self.url}' during object deletion: {e}")


class Scraper():
    def __init__(self):
        pass

    def scrape(self, url):
        raise NotImplementedError("Scrape is not implemented")
    

class ScrapeServ(Scraper):
    def __init__(self, url="http://localhost:5006", api_key=None):
        self.url = url
        self.api_key = api_key

    def scrape(self, url):
        headers = {
            'Authorization': f'Bearer {self.api_key}'
        }
        data = {
            'url': url
        }
        try:
            response = requests.post(self.url + '/scrape', json=data, headers=headers, timeout=30)
            response.raise_for_status()
            decoder = MultipartDecoder.from_response(response)

            resp = None
            for i, part in enumerate(decoder.parts):
                if i == 0:  # First is some JSON
                    json_part = json.loads(part.content)
                    status = json_part['status']
                    headers = json_part['headers']
                    resp = ScrapeResponse(False, status, url, headers)
                elif i == 1:  # Next is the actual content of the
                    if part.content:
                        resp.success = True
                        resp.set_data(part.content)
                else:  # Other parts are screenshots, if they exist
                    # Annoyingly the headers are bytes not strings for some reason
                    mimetype: bytes = part.headers[b'Content-Type']
                    mimetype: str = mimetype.decode()
                    resp.add_screenshot(part.content, mimetype)
            
            return resp

        except requests.RequestException as e:
            if e.response:
                try:
                    my_json = e.response.json()
                    message = my_json['error']
                    print(f"Error scraping: {message}", file=sys.stderr)
                except:
                    print(e, file=sys.stderr)
            return ScrapeResponse(False, status=None, url=url, headers={})


class RequestsScraper(Scraper):
    def __init__(self):
        pass

    def scrape(self, url):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
                'Accept': 'application/json, text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9'
            }
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()  # will throw an error if the request isn't good
            status = response.status_code
            website_data = response.content
            resp_headers = response.headers

            resp = ScrapeResponse(True, status, url, resp_headers)
            resp.set_data(website_data)
            return resp

        except requests.RequestException as e:
            print(e, file=sys.stderr)
            if e.response:
                status_code = e.response.status_code
                headers = e.response.headers
                return ScrapeResponse(False, status=status_code, url=url, headers=headers)
            else:
                return ScrapeResponse(False, status=None, url=url, headers={})
