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
import sys, os

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
        '''
            Connect to the specified host and port using the socket object 

            Args:
                host    (str)   :   The host specified in the request
                port    (int)   :   The port specified in the request
        '''
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        return None

    def get_code(self, data):
        '''
            Returns the status code of the response

            Args:
                data    (str)   :   The response data from the server

            Returns:
                code    (int)   :   The status code of the response
        '''
        return int(data.split('\r\n')[0].split(' ')[1])

    def get_headers(self,data):
        '''
            Returns the headers of the response

            Args:
                data    (str)   :   The response data from the server
            
            Returns:
                header  (str)   :   The headers of the response
        '''
        return data.split('\r\n\r\n')[0]

    def parse_header(self, header):
        '''
            Parses the header into a dictionary format

            Args:
                header    (str)   :   The header to be parsed
            
            Returns
                header_dict    (dict)  :   The parsed header with {option : value}
        '''
        header_dict = {}
        for line in header.split('\r\n'):
            if ':' in line:
                key, value = line.split(': ')
                header_dict[key] = value

        return header_dict

    def get_body(self, data):
        return data.split('\r\n\r\n')[1]
    
    def build_request(self, options, command="GET"):
        '''
            Builds the request to be sent to the server
            References:
                - https://stackoverflow.com/questions/17667903/python-socket-receive-large-amount-of-data

            Args:
                options    (dict)   :   The parsed URL options
                command    (str)    :   The command to be sent to the server
            
            Returns:
                request    (str)    :   The final request (header + body) to be sent to the server
        
        '''

        # Set the date, target url and host from the parsed url
        date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        target = options['target']
        host = options['host']

        # Build the request : common to both GET and POST 
        header = (
            f'{command} {target} HTTP/1.1\r\n'
            f'Date: {date}\r\n'
            f'Host: {host}\r\n'
            f'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36\r\n'
        )

        # If the request is a POST, add the content-length and content-type headers
        if command == "POST":
            length = len(options['query']) 
            header += (
                f'Content-Type: application/x-www-form-urlencoded\r\n'
                f'Content-Length: {length}\r\n'
                f'Connection: close\r\n'
            )

        header += '\r\n'

        # Add the body if it is a POST 
        if command == 'POST':
            queries = options['query']
            return header + queries

        return header
    
    def sendall(self, data):
        '''
            Sends the data to the server

            Args:
                data    (str)   :   The data to be sent to the server
        '''
        if data:
            self.socket.sendall(data.encode('utf-8'))
        else:
            self.socket.shutdown(socket.SHUT_WR)
        
    def close(self):
        self.socket.close()

    # read everything from the socket
    def recvall(self, sock):
        '''
            Reads everything from the server socket. If a Content-Length header is present, read until the Content-Length is reached.

            References
                - https://stackoverflow.com/questions/4824451/detect-end-of-http-request-body/4824738
                - https://www.binarytides.com/receive-full-data-with-the-recv-socket-function-in-python/
                - https://stackoverflow.com/questions/17667903/python-socket-receive-large-amount-of-data
                - http://stupidpythonideas.blogspot.com/2013/05/sockets-are-byte-streams-not-message.html
            
            Args:
                sock    (socket)    :   The socket object 

            Returns:
                data    (str)   :   The decoded data received from the server
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
        '''
            Parses the URL into a dictionary format

            Args:
                url    (str)   :   The url to be parsed
            
            Returns:
                options    (dict)   :   The parsed url with {url_option : value}
        '''

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

        return parsed_url
    
    def GET(self, url):
        '''
            Sends a GET request to the server
            
            Args:
                url    (str)   :   The requested url
            
            Returns:
                response    (str)   :   The response from the server
        '''
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
            body = self.get_body(data)

            return HTTPResponse(code, body)

    def POST(self, url, args=None):
        '''
            Sends a POST request to the server
            References:
                - https://reqbin.com/req/zvtstmpb/post-request-example
                - https://stackoverflow.com/questions/28670835/python-socket-client-post-parameters
                - https://stackoverflow.com/questions/5725430/http-test-server-accepting-get-post-requests
                - https://stackoverflow.com/questions/1278705/when-i-catch-an-exception-how-do-i-get-the-type-file-and-line-number

            Args:
                url    (str)   :   The requested url
                args   (dict)  :   The body to be sent to the server
            
            Returns:
                response    (str)   :   The response from the server

        '''
        code = 500
        body = ""

        options = self.parse_url(url)
        host = options['host']
        port = options['port']

        if args:
            queries = args
        else: 
            queries = options['query']

        if queries is None:
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
            print('> Receiving data...')
            response = self.recvall(self.socket)
            print(response)

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            print(f'[{exc_type} in line {exc_tb.tb_lineno}]: {e}')
        
        finally:
            
            print('> Response:')
            code = self.get_code(response)
            body =  self.get_body(response)

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
