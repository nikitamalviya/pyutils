#!/usr/bin/env python3

"""Simple HTTP Server With Upload.

This module builds on BaseHTTPServer by implementing the standard GET
and HEAD requests in a fairly straightforward manner.

see: https://gist.github.com/UniIsland/3346170
"""


__version__ = "0.1"
__all__ = ["SimpleHTTPRequestHandler"]
__author__ = "bones7456"
__home_page__ = "http://li2z.cn/"

import os
import posixpath
import http.server
import urllib.request
import urllib.parse
import urllib.error
import cgi
import shutil
import mimetypes
import re
import sys
from io import BytesIO

# import match_template
# import extract_text
# import config


class SimpleHTTPRequestHandler(http.server.BaseHTTPRequestHandler):

    """Simple HTTP request handler with GET/HEAD/POST commands.

    This serves files from the current directory and any of its
    subdirectories.  The MIME type for files is determined by
    calling the .guess_type() method. And can reveive file uploaded
    by client.

    The GET/HEAD/POST requests are identical except that the HEAD
    request omits the actual contents of the file.

    """

    server_version = "SimpleHTTPWithUpload/" + __version__

    def do_GET(self):
        """Serve a GET request."""
        f = self.send_head()
        if f:
            self.copyfile(f, self.wfile)
            f.close()

    def do_HEAD(self):
        """Serve a HEAD request."""
        f = self.send_head()
        if f:
            f.close()

    def do_POST(self):
        """Serve a POST request."""
        r, res = self.deal_post_data()
        # r, username, filename = self.deal_post_data()

        if isinstance(res, str):
            raise BaseException(res)
        else:
            username, filename = res

        f = BytesIO()
        f.write(b'<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">')
        f.write(b"<html>\n<title>Upload Result Page</title>\n")
        f.write(
            (b"<meta name='viewport' content='width=device-width,initial-scale=1.0,minimum-scale=1.0'>\n"))
        f.write(b"<body style=''>")
        # f.write(info.encode())
        # FIND ME

        f.write(b"<br>")
        f.write(("Username : <span style='color:#00897b; font-weight: bold;font-size: 18px;'>").encode(
            'utf-8') + str(username).encode('utf-8'))
        f.write(b"</span><br><br>")
        f.write(("Filename : <pre style='color:#f44336;'>").encode(
            'utf-8') + str(filename).encode('utf-8'))
        f.write(b"</pre><br>")

        if r:
            f.write(b"<strong>Success</strong>")
            # f.write(f"Success: {{result}}")
        else:
            f.write(b"<strong>Failed:</strong>")

        # f.write(("<br>" % self.headers['referer']).encode())

        f.write(b"</body>\n</html>\n")
        length = f.tell()
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(length))
        self.end_headers()

        if f:
            self.copyfile(f, self.wfile)
            f.close()

            sys.exit('exiting')

    def deal_post_data(self):
        ctype, pdict = cgi.parse_header(self.headers['Content-Type'])
        pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
        pdict['CONTENT-LENGTH'] = int(self.headers['Content-Length'])
        if ctype == 'multipart/form-data':
            form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={
                                    'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': self.headers['Content-Type'], })

            filename = "./%s" % form["file"].filename
            username = "%s" % form["username"].file.read()

            try:
                open(filename, "wb").write(form["file"].file.read())
            except IOError:
                return (False, "Can't create file to write, do you have permission to write?")

        return (True, [username, filename])

    def deal_post_data_old(self):
        print(self.headers)

        content_type = self.headers['content-type']
        if not content_type:
            return (False, "Content-Type header doesn't contain boundary")
        boundary = content_type.split("=")[1].encode()
        remainbytes = int(self.headers['content-length'])
        line = self.rfile.readline()
        remainbytes -= len(line)
        if not boundary in line:
            return (False, "Content NOT begin with boundary")
        line = self.rfile.readline()
        remainbytes -= len(line)
        fn = re.findall(
            r'Content-Disposition.*name="file"; filename="(.*)"', line.decode())
        if not fn:
            return (False, "Can't find out file name...")

        # un = re.findall(
        #     r'Content-Disposition.*name="username";', line.decode())
        # if not un:
        #     return (False, "Can't find out username...")

        # line3 = self.rfile.readline()
        # print(line3)

        # line4 = self.rfile.readline()
        # print(line4)

        username = "FAKE"

        # print(line.decode())

        path = self.translate_path(self.path)
        fn = os.path.join(path, 'uploaded_image', fn[0])

        line = self.rfile.readline()
        remainbytes -= len(line)
        line = self.rfile.readline()
        remainbytes -= len(line)
        try:
            out = open(fn, 'wb')
        except IOError:
            return (False, "Can't create file to write, do you have permission to write?")

        preline = self.rfile.readline()
        remainbytes -= len(preline)
        while remainbytes > 0:
            line = self.rfile.readline()
            remainbytes -= len(line)
            if boundary in line:
                preline = preline[0:-1]
                if preline.endswith(b'\r'):
                    preline = preline[0:-1]
                out.write(preline)
                out.close()
                return (True, [username, fn])
            else:
                out.write(preline)
                preline = line
        return (False, "Unexpect Ends of data.")

    def send_head(self):
        """Common code for GET and HEAD commands.

        This sends the response code and MIME headers.

        Return value is either a file object (which has to be copied
        to the outputfile by the caller unless the command was HEAD,
        and must be closed by the caller under all circumstances), or
        None, in which case the caller has nothing further to do.

        """
        path = self.translate_path(self.path)
        f = None
        if os.path.isdir(path):
            if not self.path.endswith('/'):
                # redirect browser - doing basically what apache does
                self.send_response(301)
                self.send_header("Location", self.path + "/")
                self.end_headers()
                return None
            for index in "index.html", "index.htm":
                index = os.path.join(path, index)
                if os.path.exists(index):
                    path = index
                    break
            else:
                return self.list_directory(path)
        ctype = self.guess_type(path)
        try:
            # Always read in binary mode. Opening files in text mode may cause
            # newline translations, making the actual size of the content
            # transmitted *less* than the content-length!
            f = open(path, 'rb')
        except IOError:
            self.send_error(404, "File not found")
            return None
        self.send_response(200)
        self.send_header("Content-type", ctype)
        fs = os.fstat(f.fileno())
        self.send_header("Content-Length", str(fs[6]))
        self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        self.end_headers()
        return f

    def list_directory(self, path):
        """Helper to produce a directory listing (absent index.html).

        Return value is either a file object, or None (indicating an
        error).  In either case, the headers are sent, making the
        interface the same as for send_head().

        """
        try:
            list = os.listdir(path)
        except os.error:
            self.send_error(404, "No permission to list directory")
            return None
        list.sort(key=lambda a: a.lower())
        f = BytesIO()
        displaypath = cgi.escape(urllib.parse.unquote(self.path))
        f.write(b'<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">')
        f.write(("<html>\n<title>Medicine Scanner</title>\n").encode())
        f.write(("<meta name='viewport' content='width=device-width,initial-scale=1.0,minimum-scale=1.0'>\n").encode())
        f.write(("<body>\n<h2>Medicine Scanner</h2>\n").encode())
        f.write(b"<hr>\n")
        f.write(
            b"<form ENCTYPE=\"multipart/form-data\" target='outputIFrame' method=\"post\">")
        f.write(b"<input name=\"file\" id='file' type=\"file\"/>")
        f.write(b"<input name=\"username\" id='username' type=\"text\"/>")
        f.write(b"<input type=\"submit\" value=\"upload\"/></form>\n")
        f.write(b"<img style='width:auto; height:400px;' id='upload_img' />")
        f.write(b"<iframe style='width:80vw; height:400px;' name='outputIFrame' frameborder=0 allowtransparency='yes' scrolling='no'></iframe>")
        f.write(
            b"<script>document.getElementById('file').onchange=function(){var reader=new FileReader();reader.onload=function(e){document.getElementById('upload_img').src=e.target.result};reader.readAsDataURL(this.files[0])}</script>")

        # f.write(b"<hr>\n<ul>\n")
        # for name in list:
        #     fullname = os.path.join(path, name)
        #     displayname = linkname = name
        #     # Append / for directories or @ for symbolic links
        #     if os.path.isdir(fullname):
        #         displayname = name + "/"
        #         linkname = name + "/"
        #     if os.path.islink(fullname):
        #         displayname = name + "@"
        #         # Note: a link to a directory displays with @ and links with /
        #     f.write(('<li><a href="%s">%s</a>\n'
        #             % (urllib.parse.quote(linkname), cgi.escape(displayname))).encode())

        f.write(b"</ul>\n</body>\n</html>\n")
        length = f.tell()
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        return f

    def translate_path(self, path):
        """Translate a /-separated PATH to the local filename syntax.

        Components that mean special things to the local file system
        (e.g. drive or directory names) are ignored.  (XXX They should
        probably be diagnosed.)

        """
        # abandon query parameters
        path = path.split('?', 1)[0]
        path = path.split('#', 1)[0]
        path = posixpath.normpath(urllib.parse.unquote(path))
        words = path.split('/')
        words = [_f for _f in words if _f]
        path = os.getcwd()
        for word in words:
            drive, word = os.path.splitdrive(word)
            head, word = os.path.split(word)
            if word in (os.curdir, os.pardir):
                continue
            path = os.path.join(path, word)
        return path

    def copyfile(self, source, outputfile):
        """Copy all data between two file objects.

        The SOURCE argument is a file object open for reading
        (or anything with a read() method) and the DESTINATION
        argument is a file object open for writing (or
        anything with a write() method).

        The only reason for overriding this would be to change
        the block size or perhaps to replace newlines by CRLF
        -- note however that this the default server uses this
        to copy binary data as well.

        """
        shutil.copyfileobj(source, outputfile)

    def guess_type(self, path):
        """Guess the type of a file.

        Argument is a PATH (a filename).

        Return value is a string of the form type/subtype,
        usable for a MIME Content-type header.

        The default implementation looks the file's extension
        up in the table self.extensions_map, using application/octet-stream
        as a default; however it would be permissible (if
        slow) to look inside the data to make a better guess.

        """

        base, ext = posixpath.splitext(path)
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        ext = ext.lower()
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        else:
            return self.extensions_map['']

    if not mimetypes.inited:
        mimetypes.init()  # try to read system mime.types
    extensions_map = mimetypes.types_map.copy()
    extensions_map.update({
        '': 'application/octet-stream',  # Default
        '.py': 'text/plain',
        '.c': 'text/plain',
        '.h': 'text/plain',
    })


def test(HandlerClass=SimpleHTTPRequestHandler,
         ServerClass=http.server.HTTPServer):
    http.server.test(HandlerClass, ServerClass, port=8082)


if __name__ == '__main__':
    test()
