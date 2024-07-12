import socket
import re
import threading
import os
import argparse
import gzip


def home(verb: str = None) -> bytes:
    verb = verb or 'GET'
    if verb != 'GET':
        return not_found()
    return 'HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 0\r\n\r\n'.encode()

def not_found() -> bytes:
    return 'HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\nContent-Length: 0\r\n\r\n'.encode()

def echo(value: str, headers: dict[str, str], content_type: str = None, verb: str = None) -> bytes:
    content_type = content_type or 'text/plain'
    verb = verb or 'GET'
    if verb != 'GET':
        return not_found()
    encodings = headers.get('Accept-Encoding')
    if not encodings or 'gzip' not in encodings.split(', '):
        return f'HTTP/1.1 200 OK\r\nContent-Type: {content_type}\r\nContent-Length: {len(value)}\r\n\r\n{value}'.encode()
    compressed_body = gzip.compress(value.encode())
    return f'HTTP/1.1 200 OK\r\nContent-Encoding: gzip\r\nContent-Type: {content_type}\r\nContent-Length: {len(compressed_body)}\r\n\r\n'.encode() + compressed_body

def get_files(filename: str, directory: str) -> bytes:
    file_path = os.path.join(directory, filename)
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        return not_found()

    with open(file_path, 'r') as f:
        file_content = f.read()
        return echo(file_content, {}, 'application/octet-stream')
    
def post_files(filename: str, directory: str, body: str) -> bytes:
    file_path = os.path.join(directory, filename)

    with open(file_path, 'w') as f:
        size = f.write(body)
    return f'HTTP/1.1 201 Created\r\n\r\nContent-Type: application/octet-stream\r\nContent-Length: {size}\r\n\r\n'.encode()

def user_agent(headers: dict[str, str], verb: str = None) -> bytes:
    verb = verb or 'GET'
    if verb != 'GET':
        return not_found()
    user_agent = headers.get('User-Agent', '')
    return echo(user_agent, headers)

def handle_request(request_target: str, headers: dict[str, str], directory: str, verb: str, body: str) -> bytes:
    if request_target == '/':
        return home(verb)
    
    if request_target == '/user-agent':
        return user_agent(headers, verb)
    
    echo_match = re.match(r'^/echo/(.+)$', request_target)
    if echo_match:
        return echo(echo_match.group(1), headers, verb=verb)
    
    files_match = re.match(r'^/files/(.+)$', request_target)
    if files_match:
        return post_files(files_match.group(1), directory, body) if verb == 'POST' else get_files(files_match.group(1), directory)
    
    return not_found()

def parse_headers(raw_headers: list[str]) -> dict[str, str]:
    headers = {}
    for header in raw_headers:
        if ': ' in header:
            key, value = header.split(': ', 1)
            headers[key] = value
    return headers

def client_handler(client_socket, directory: str) -> bytes:
    try:
        request_data = client_socket.recv(1024).decode()
        request_parts = request_data.split('\r\n')
        request_line, *raw_headers, _, body = request_parts
        
        verb, request_target, http_version = request_line.split(' ')
        headers = parse_headers(raw_headers)
        
        response = handle_request(request_target, headers, directory, verb, body)
        client_socket.sendall(response)
    except Exception as e:
        print(f"Error handling request: {e}")
    finally:
        client_socket.close()

def main(directory: str | None):
    directory = directory or ''
    
    print(f'Starting server with files directory: {directory}')
    server_socket = socket.create_server(('localhost', 4221), reuse_port=True)
    
    while True:
        try:
            client_socket, client_address = server_socket.accept()
            print(f"New connection from {client_address}")
            client_thread = threading.Thread(target=client_handler, args=(client_socket, directory))
            client_thread.start()
        except Exception as e:
            print(f"Error accepting connection: {e}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='HTTP Server')
    parser.add_argument('--directory', required=False, help='Directory to serve files from')
    args = parser.parse_args()
    
    main(args.directory)