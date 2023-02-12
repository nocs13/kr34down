#!/usr/bin/python3
import sys
import os
import re
import requests
import xml.dom.minidom
from html.parser import HTMLParser

WORKSPACE = "/tmp/k-r34"
FOLDER = ''
LOGLEVEL = 1

BASE_URL = "https://rule34.xxx/index.php?page=post&s=list&tags="
BASE_IMG_URL = "https://rule34.xxx/index.php?page=post&s=view&id="

def log(msg):
    print(msg)

def get_attribute(attribute, attributes):
    for a in attributes:
        if a[0] == attribute:
            return a[1]
    return ''


class KImgParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.img_src = ''
        self.img_name = ''
        self.is_video = False

    def handle_starttag(self, tag, attrs):
        if tag == 'img':
            id = self.get_id(attrs)
            if id != '':
                self.img_src = self.get_img_src(attrs)
                t = self.img_src.split('/')[-1]
                t = t.split('?')[0]
                self.img_name = t
        elif tag == 'video':
            id = self.get_id(attrs)
            if id != 'gelcomVideoPlayer':
                self.is_video = True
        elif tag == 'source':
            s = self.get_img_src(attrs)

            if s != '':
                self.img_src = s
                t = self.img_src.split('/')[-1]
                t = t.split('?')[0]
                self.img_name = t

    def handle_endtag(self, tag):
        if tag == 'video':
            self.is_video = False

    def handle_data(self, data):
        pass

    def get_id(self, attrs):
        for a in attrs:
            if a[0] == 'id':
                return a[1]
        return ''

    def get_img_src(self, attrs):
        for a in attrs:
            if a[0] == 'src':
                return a[1]
        return ''

class KParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.p_type = ''
        self.next_id = ''

    def handle_starttag(self, tag, attrs):
        if tag == 'img' and self.p_type == 'content':
            s = self.get_img_src(attrs)

            try:
                if s != '':
                    id = s.split('?')[1]
                    url = BASE_IMG_URL + str(id)
                    r = requests.get(url);
                    #print("Image id: ",id, 'Status: ', r.status_code)

                    iparser = KImgParser()
                    iparser.feed(r.text)
                    iurl = iparser.img_src

                    if iurl != '':
                        self.save_image(iurl, iparser.img_name)

            except Exception as e:
                print('Image id parse error: ', e)
            pass
        elif tag == 'a':
            a = self.get_alt(attrs)

            if a == 'next':
                h = self.get_href(attrs)
                x = re.findall("&pid=.*", h)

                if len(x) > 0:
                    self.next_id = x[0].split('=')[1]

        cls = self.get_class(attrs)

        if cls == 'content':
            self.p_type = 'content'

    def handle_endtag(self, tag):
        pass

    def handle_data(self, data):
        pass

    def get_alt(self, attrs):
        for a in attrs:
            if a[0] == 'alt':
                return a[1]
        return ''

    def get_href(self, attrs):
        for a in attrs:
            if a[0] == 'href':
                return a[1]
        return ''

    def get_class(self, attrs):
        for a in attrs:
            if a[0] == 'class':
                return a[1]
        return ''

    def get_img_src(self, attrs):
        for a in attrs:
            if a[0] == 'src':
                return a[1]
        return ''

    def save_image(self, url, f):
        try:
            f = open(FOLDER + '/' + f,'wb')
            f.write(requests.get(url).content)
            f.close()
        except Exception as e:
            print('Error: Unable load image. ', str(e))


def print_imgs(url):
  debug = {'verbose': sys.stderr}
  user_agent = {'User-agent': 'Mozilla/5.0'}

  print('Request on url: ' + url)
  res = requests.get(url, headers=user_agent)

  if (res.status_code != 200):
    print(res.status_code)
    print(res)

  parser = KParser()
  parser.feed(res.text)

  while parser.next_id != '':
    #print('Next page id is ', parser.next_id)
    res = requests.get(url + '&pid=' + parser.next_id);
    #print(res.status_code)
    parser.next_id = ''
    parser.feed(res.text)


if len(sys.argv) < 2:
    print('Error: Tag not provided')
    sys.exit(1)

tag = sys.argv[1]
#tag = 'nonude'

if os.path.exists(WORKSPACE) is False:
    os.mkdir(WORKSPACE)

FOLDER = WORKSPACE + '/' + tag

if os.path.exists(FOLDER) is False:
    os.mkdir(FOLDER)
    if os.path.exists(FOLDER) is False:
        print('Error: Cannot create target folder.')
        sys.exit(1)

if __name__ == "__main__":
    print_imgs(BASE_URL + tag)
