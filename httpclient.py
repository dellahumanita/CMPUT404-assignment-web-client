#!/usr/bin/env python3
# coding: utf-8
# Copyright 2022 Della Humanita
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Do not use urllib's HTTP GET and POST mechanisms.
# Write your own HTTP GET and POST
# The point is to understand what you have to send and get experience with it

import sys
import socket
import re
# you may use urllib to encode data appropriately
from urllib.parse import urlparse

from datetime import datetime
import os

def help():
    print("httpclient.py [GET/POST] [URL]\n")

class HTTPResponse(object):
    def __init__(self, code=200, body=""):
        self.code = code
        self.body = body
    
    
    def __str__(self):
        return f'{str(self.code)}\n{str(self.body)}'

class HTTPClient(object):
    #def get_host_port(self,url):

    def connect(self, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        return None

    def get_code(self, data):
        # TODO
        return None

    def get_headers(self,data):
        # TODO

        return None

    def get_body(self, data):
        # TODO

        return None
    
    def build_request(self, target, host, command="GET"):
        '''
        
        References:
            - https://stackoverflow.com/questions/45965007/multiline-f-string-in-python
        '''

        
        date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        header = (
            f'{command} / HTTP/1.1\r\n'
            f'Date: {date}\r\n'
            f'Host: {host}\r\n'
        )

        header += '\r\n'

        print("-"*50, '\n', header, "-"*50)

        return header
    
    def sendall(self, data):
        self.socket.sendall(data.encode('utf-8'))
        
    def close(self):
        self.socket.close()

    # read everything from the socket
    def recvall(self, sock):
        # buffer = bytearray()
        # done = False
        # while not done:
        #     part = sock.recv(1024)
        #     print(part)
        #     print(done)
        #     if (part):
        #         buffer.extend(part)
        #     else:
        #         done = True 

        buffer = sock.recv(1024)
        return buffer.decode('utf-8')
    
    def parse_url(self, url):

        parsed_url = {}

        u = urlparse(url)
        if u.path:
            target = u.path
        else:
            target = '/'

        if u.hostname:
            host = u.hostname
        else:
            host = u.path

        if u.port:
            port = u.port
        else:
            port = 80  # arbitrary port

        parsed_url['target'] = target
        parsed_url['host'] = host
        parsed_url['port'] = port

        return parsed_url
    
    def GET(self, url, args=None):
        code = 500 # internal server error
        data = ''

        parsed_url = self.parse_url(url)
        host = parsed_url['host']
        port = parsed_url['port']

        target = parsed_url['target']


        try:
            # Connect to server and send data
            print('Connecting to server...')
            self.connect(host, port)
            # Send a request in bytes 
            print('Requesting data...')
            request  = self.build_request(target, host, 'GET')
            self.sendall(request)

            print('Receiving data...')
            data = self.recvall(self.socket)
            
            # Parse the response 
            code = self.get_code(data)
            headers = self.get_headers(data)
            body = self.get_body(data)

        except Exception as e:
            print("[ERROR]: ", e)
        
        finally:
            self.close()
            return HTTPResponse(code, data)

    def POST(self, url, args=None):
        # TODO
        code = 500
        body = ""
        return HTTPResponse(code, body)

    def command(self, url, command="GET", args=None):
        if (command == "POST"):
            return self.POST( url, args )
        else:
            return self.GET( url, args )
    
if __name__ == "__main__":
    client = HTTPClient()
    command = "GET"
    if (len(sys.argv) <= 1):
        help()
        sys.exit(1)
    elif (len(sys.argv) == 3): 
        print(client.command( sys.argv[2], sys.argv[1] ))
    else:
        print(client.command( sys.argv[1] ))
