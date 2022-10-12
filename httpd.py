import argparse
import locale
import os
import select
import signal
import socket
import re
from multiprocessing import Pool
from urllib.parse import unquote
from datetime import datetime

HOST = "localhost"
PORT = 80
servername = "CustomServer/1.0"
connection = "keep-alive"
http_content_type = {
    "html": "text/html",
    "css": "text/css",
    "js": "text/javascript",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "gif": "image/gif",
    "swf": "application/x-shockwave-flash",
    "txt": "text/plain",
    "ico": "image/x-icon",
}
head200 = "200 OK"
head404 = "404 NOT FOUND"
head405 = "405 Method Not Allowed\r\nAllow: GET, HEAD"
head400 = "400 Bad Request"


def head_result(code):
    if code == 200:
        return head200
    if code == 404:
        return head404
    if code == 400:
        return head400
    if code == 405:
        return head405


def head(content_length, content_type, code):
    locale.setlocale(locale.LC_ALL, "")
    header = f"HTTP/1.1 {head_result(code)}\r\nDate:{datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')}\r\nServer: {servername}\r\nContent-Length: {content_length}\r\nContent-Type: {content_type}\r\nConnection: {connection}\r\n\r\n"
    return header.encode()


def parse_headers(request):
    try:
        headers = request.split("\n")
        method = headers[0].split()[0]
        address = headers[0].split()[1]
    except IndexError:
        return None, None
    return address, method


def open_page(arg):
    with open(arg, "rb") as page:
        response = page.read()
        filesize = os.path.getsize(arg)
    return response, filesize


def validate_adr(address, args):
    try:
        if address == "/":
            response, filesize = open_page("index.html")
            return response, head(filesize, "text/html;", 200)
        address = unquote(address)

        if re.fullmatch(r".*/\w*/", address):
            response, filesize = open_page(f"{args}{address}index.html")
            return response, head(filesize, "text/html;", 200)

        if re.fullmatch(r".*/.*\.\S*", address):
            if address[-1:] == "/":
                raise FileNotFoundError
            if "?" in address:
                file_type = re.fullmatch(r"(?P<root>.*/.*)\.(?P<type>.*)\?.*", address)
            else:
                file_type = re.fullmatch(r"(?P<root>.*/.*)\.(?P<type>.*)", address)

            content_type = http_content_type[file_type[2]]
            response, filesize = open_page(f"{args}/{file_type[1]}.{file_type[2]}")
            return response, head(filesize, content_type, 200)

        if re.fullmatch(r".*/\S*", address):
            response, filesize = open_page(f"{args}{address}/index.html")
            return response, head(filesize, "text/html;", 200)

    except FileNotFoundError:
        response, filesize = open_page("404.html")
        return response, head(filesize, "text/html;", 404)
    except KeyError:
        response, filesize = open_page("400.html")
        return response, head(filesize, "text/html;", 400)


def main(args):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(1)
    while True:
        data = b""
        while data[-4:] != b"\r\n\r\n":
            conn, addr = s.accept()
            try:
                conn.settimeout(5)
                data = conn.recv(1024)
            except Exception as e:
                print(e)
                conn.close()
        address, method = parse_headers(data.decode())
        if (method == None or method == "POST"):
            response, filesize = open_page("405.html")
            conn.sendall(head(filesize, "text/html;", 405) + response)
            conn.close()
            continue
        response, heads = validate_adr(address, args)
        if method == "GET":
            conn.sendall(heads + response)
            conn.close()
        if method == "HEAD":
            conn.sendall(heads)
            conn.close()
    s.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", "-r", help="Укажите путь к файлу DOCUMENT_ROOT")
    parser.add_argument("--worker", "-w", help="Укажите количество worker-ов")
    args = parser.parse_args()
    main(args.root)
    p = Pool(
        int(args.worker),
    )
    try:
        p.apply(main, args=(args.root,))
        p.close()
        p.join()
    except Exception as e:
        print("Ошибка:", e)
