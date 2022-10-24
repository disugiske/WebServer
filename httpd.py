import argparse
import locale
import logging
import os
import socket
import re
import sys
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

head_result = {
    200: "200 OK",
    404: "404 NOT FOUND",
    400: "400 Bad Request",
    405: "405 Method Not Allowed\r\nAllow: GET, HEAD"
}



def head(content_length, content_type, code):
    locale.setlocale(locale.LC_ALL, "")
    header = f"HTTP/1.1 {head_result[code]}\r\nDate:{datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')}\r\nServer: {servername}\r\nContent-Length: {content_length}\r\nContent-Type: {content_type}\r\nConnection: {connection}\r\n\r\n"
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
        page_response = page.read()
        filesize = os.path.getsize(arg)
    return page_response, filesize


def validate_adr(address, args):
    try:
        if address == "/":
            page_response, filesize = open_page("index.html")
            return page_response, head(filesize, "text/html;", 200)
        address = unquote(address)

        if re.fullmatch(r".*/\w*/", address):
            page_response, filesize = open_page(f"{args}{address}index.html")
            return page_response, head(filesize, "text/html;", 200)

        if re.fullmatch(r".*/.*\.\S*", address):
            if address[-1:] == "/":
                raise FileNotFoundError
            if "?" in address:
                file_type = re.fullmatch(r"(?P<root>.*/.*)\.(?P<type>.*)\?.*", address)
            else:
                file_type = re.fullmatch(r"(?P<root>.*/.*)\.(?P<type>.*)", address)

            content_type = http_content_type[file_type[2]]
            page_response, filesize = open_page(f"{args}/{file_type[1]}.{file_type[2]}")
            return page_response, head(filesize, content_type, 200)

        if re.fullmatch(r".*/\S*", address):
            page_response, filesize = open_page(f"{args}{address}/index.html")
            return page_response, head(filesize, "text/html;", 200)

    except FileNotFoundError:
        page_response, filesize = open_page("404.html")
        return page_response, head(filesize, "text/html;", 404)
    except KeyError:
        page_response, filesize = open_page("400.html")
        return page_response, head(filesize, "text/html;", 400)


def main(args):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(1)
    logging.info('Start server')
    while True:
        data = b""
        while data[-4:] != b"\r\n\r\n":
            conn, addr = s.accept()
            try:
                conn.settimeout(5)
                data = conn.recv(1024)
            except Exception as e:
                logging.exception("Error!", e)
                conn.close()
        address, method = parse_headers(data.decode())
        logging.info(f"{method} method on {address}")
        if (method == None or method == "POST"):
            page_response, filesize = open_page("405.html")
            conn.sendall(head(filesize, "text/html;", 405) + page_response)
            conn.close()
            continue
        page_response, heads = validate_adr(address, args)
        if method == "GET":
            conn.sendall(heads + page_response)
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
    logging.basicConfig(filename="server.log", level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    handler = logging.StreamHandler(stream=sys.stdout)
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
