#!/usr/bin/env python3
"""
Mock server for testing CLI commands in CI
"""

import http.server
import socketserver
import json
import threading
import time
import sys

class MockHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/project/test-123':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {
                'project_id': 'test-123',
                'status': 'completed',
                'message': 'Test project',
                'files': ['Cargo.toml', 'src/main.rs']
            }
            self.wfile.write(json.dumps(response).encode())
        elif self.path == '/project/test-123/files/Cargo.toml':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'[package]\nname = "test"\nversion = "0.1.0"')
        elif self.path == '/project/test-123/files/src/main.rs':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'fn main() { println!("Hello"); }')
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/compile':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {'success': True, 'run_output': 'Hello'}
            self.wfile.write(json.dumps(response).encode())
        elif self.path == '/compile-and-fix':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {'success': True, 'combined_text': '[filename: src/main.rs]\nfn main() { println!("Fixed!"); }'}
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass

def main():
    port = 8001
    if len(sys.argv) > 1:
        port = int(sys.argv[1])

    with socketserver.TCPServer(('', port), MockHandler) as httpd:
        print(f'Mock server running on port {port}')
        server_thread = threading.Thread(target=httpd.serve_forever)
        server_thread.daemon = True
        server_thread.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Shutting down mock server...")

if __name__ == '__main__':
    main()