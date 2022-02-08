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

import re
import sys
import socket
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
        return f'{self.code} {self.body}'

class HTTPClient(object):
    #def get_host_port(self,url):

    def connect(self, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        return None

    def get_code(self, data):
        return int(data.split('\r\n')[0].split(' ')[1])

    def get_headers(self,data):
        return data.split('\r\n\r\n')[0]

    def parse_header(self, header):
        header_dict = {}
        for line in header.split('\r\n'):
            if ':' in line:
                key, value = line.split(': ')
                header_dict[key] = value

        return header_dict

    def get_body(self, data):
        return data.split('\r\n\r\n')[1]
    
    def build_request(self, options, command="GET", args=None):
        '''
        
        References:
            - https://stackoverflow.com/questions/17667903/python-socket-receive-large-amount-of-data
        '''

        date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        target = options['target']
        host = options['host']

        header = (
            f'{command} {target} HTTP/1.1\r\n'
            f'Date: {date}\r\n'
            f'Host: {host}\r\n'
            f'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36\r\n'
        )

        if command == "POST":
            length = len(options['query']) #TODO get length of body
            header += (
                f'Content-Type: application/x-www-form-urlencoded\r\n'
                f'Content-Length: {length}\r\n'
                f'Connection: close\r\n'
            )

        header += '\r\n'

        # send the query
        if command == 'POST':
            queries = options['query']
            return header + queries

        return header
    
    def sendall(self, data):
        if data:
            self.socket.sendall(data.encode('utf-8'))
        else:
            self.socket.shutdown(socket.SHUT_WR)
        
    def close(self):
        self.socket.close()

    # read everything from the socket
    def recvall(self, sock):
        '''
        References
            - https://stackoverflow.com/questions/4824451/detect-end-of-http-request-body/4824738
            - https://www.binarytides.com/receive-full-data-with-the-recv-socket-function-in-python/
            - https://stackoverflow.com/questions/17667903/python-socket-receive-large-amount-of-data
            - http://stupidpythonideas.blogspot.com/2013/05/sockets-are-byte-streams-not-message.html
        '''
        buffer = bytearray()
        done = False
        while not done:
            part = sock.recv(1024)
            # parse the header 

            if (part):
                buffer.extend(part)
                
                # if the part ends in \r\n\r\n, then it is the header
                if b'\r\n\r\n' in part:
                    header = self.get_headers(part.decode('utf-8'))
                    result = self.parse_header(header)
                    
                    # If the header has a Content-Length, then we need to read that many bytes
                    if 'Content-Length' in result.keys():
                        content_length = int(result['Content-Length'])
                        if len(buffer) >= content_length:
                            done = True

            else:
                # if buffer matches content length, we are done
                self.close()
                done = True 
                
        return buffer.decode('utf-8')
    
    def parse_url(self, url):

        parsed_url = {}

        u = urlparse(url)
        if u.path:
            target = u.path
        else:
            target = '/'
        parsed_url['target'] = target

        if u.hostname:
            host = u.hostname
        else:
            host = u.path
        parsed_url['host'] = host

        if u.port:
            port = u.port
        else:
            port = 80  # arbitrary port
        parsed_url['port'] = port

        parsed_url['query'] = u.query

        print(parsed_url)

        return parsed_url
    
    def GET(self, url, args=None):
        code = 500 # internal server error
        data = ''
        
        options = self.parse_url(url)
        host = options['host']
        port = options['port']

        try:
            # Connect to server and send data
            print('> Connecting to server...')
            self.connect(host, port)

            # Send a request in bytes 
            print('> Requesting data...')
            request = self.build_request(options, 'GET')
            print(request)
            self.sendall(request)

            print('> Receiving data...')
            data = self.recvall(self.socket)

        except Exception as e:
            print("[ERROR in GET]: ", e)
        
        finally:
            # Parse the response
            code = self.get_code(data)
            header = self.get_headers(data)
            print(header)

            body = self.get_body(data)
            return HTTPResponse(code, body)

    def POST(self, url, args=None):
        '''
            References:
                - https://reqbin.com/req/zvtstmpb/post-request-example

        '''
        # TODO: implement POST 
        code = 500
        body = ""

        url = 'https://www.google.com/search?q=cat' #FIXME: temporarily hardcoded, getting a zsh error when trying to use this url

        options = self.parse_url(url)
        host = options['host']
        port = options['port']
        args = options['query']

        if args is None:
            print("[ERROR]: No POST arguments provided")
            code = 400
            body = 'Bad Request'
            return HTTPResponse(code, body)
        
        try:
            # Connect to server and send data
            print('> Connecting to server...')
            self.connect(host, port)

            # Build a request in bytes
            request = self.build_request(options, 'POST')
            print(request)
            # Send the request 
            print('> Sending data...')
            self.sendall(request)
            
            # Get the response 
            response = self.recvall(self.socket)
            print(response)

        except Exception as e:
            print("[ERROR in POST]: ", e)
        
        
        


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
