#!/usr/bin/env python3
# coding=utf-8

import sys
import socket
import socketserver
import queue
import time
from swc_DataDecoder import CSocketDecode
from swc_DataDecoder import CSocketEncode



class MyTCPHandler(socketserver.StreamRequestHandler):
    """
    The RequestHandler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """
    timeout = 30

    def handle(self):
        print('Got connection from ', self.client_address)
        # self.request is the TCP socket connected to the client
        self.csd = CSocketDecode()
        self.cse = CSocketEncode()

        run_forever = True
        cnt = 0
        
        while run_forever:
            try:
                self.data = self.request.recv(1024).strip()
            except Exception as error:
                print('{} socket exception: {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), error))
                run_forever = False
                break
            else:
                if self.data == b'':
                    cnt += 1
                    print('cnt = ', cnt)
                    if cnt >= 10:
                        print('No data 10 times continuously.')
                        run_forever = False
                        break
                else:
                    cnt = 0
                    self.csd.decode(self.data.decode())
                    if self.csd.cmd != None:
                        self.server.sock_q.put([self.csd.cmd, self.csd.get_value])
                        
                        ret, wait = '', True
                        while wait:
                            try:
                                ret = self.server.ret_q.get(block=True, timeout=1)
                            except queue.Empty:
                                wait = True
                            except (KeyboardInterrupt, SystemExit):
                                wait = False
                            else:
                                self.server.ret_q.task_done()
                                wait = False
                            
                            time.sleep(0.5)

                        if ret != '':
                            print('async recv = \n{}'.format(ret))
                            send_data = self.cse.encode(ret, self.csd.get_eq_ip)
                            print('send_data = \n{}'.format(send_data))
                            self.request.sendall(send_data.encode())
                    else:
                        pass
            
            time.sleep(0.5)

        self.request.close()
        print('close\n')

    def EncodeData(self, data):
        text = str()
        if data[0] == 'EQSId' or data[0] == 'EQId':
            text = data[0] + '*' + self.csp.get_eq_ip
            fake_id = {1: 'SN00021', 2: 'SN00005', 3: 'FF', 4: 'SN00003', 5: 'SN00100', 6: 'FF',
                       7: 'FF', 8: 'SN00110', 9: 'SN00201', 10: 'SN001111', 11: 'SN00006', 12: 'SN00007'}
            for index in range(1,13):
                text = '{}#{}, {}'.format(text, index, fake_id[index])
        elif data[0] == 'EQBaudrate':
            text = data[0] + '*' + self.csp.get_eq_ip
            fake_id = {1: 1, 2: 1, 3: 0, 4: 1, 5: 1, 6: 0, 7: 0, 8: 1, 9: 1, 10: 1, 11: 1, 12: 1}
            for index in range(1,13):
                text = '{}#{}, {}'.format(text, index, fake_id[index])
        elif data[0] == 'EQType':
            text = data[0] + '*' + self.csp.get_eq_ip
            text = '{}#{}'.format(text, 'OK-Type')
        elif data[0] == 'EQCmd':
            text = data[0] + '*' + self.csp.get_eq_ip
            text = '{}#{}'.format(text, 'OK-Cmd')
        else:
            text = data[0] + '*' + self.csp.get_eq_ip
            fake_id = {1: '@01-03-02-00-10-5F-A4',
                       2: '@01-03-02-11-20-6E-B9@02-11-7E-E2-F5-7F-22',
                       3: 'FF',
                       4: '@01-C3-F2-E1-D0-6E-B9@02-B1-AE-E2-FA-7F-32@03-B3-3E-32-8A-78-82',
                       5: '@52-B1-AE-E3-FA-7F-32',
                       6: 'FF',
                       7: 'FF',
                       8: '@01-03-02-00-10-5A-A4@01-03-02-00-10-5F-A4@02-B1-AE-E2-FA-7F-32',
                       9: '@02-B1-A2-E2-FA-7B-32@52-B1-AE-E3-FA-7F-32@52-B1-AE-E3-FA-7F-32@52-B1-AE-E3-FA-7F-32@52-B1-AE-E3-FA-7F-32',
                       10: '@03-B1-A5-E2-FA-7C-32',
                       11: '@04-B1-A9-E2-FA-7D-32@52-B1-AE-E3-FA-7F-32',
                       12: '@07-B1-A0-E2-FA-7F-32'}
            for index in range(1,13):
                text = '{}#{}, {}'.format(text, index, fake_id[index])

        text = '{}*&'.format(text)
        print('text =', text)
        return text
    

class AsyncSocketServer():
    '''
    Module of TCP Socket Server.
    '''
    allow_reuse_address = True

    def __init__(self, host, port, sock_q, ret_q):
        self.host = host
        self.port = port
        self.server = None
        self.sock_q = sock_q
        self.ret_q = ret_q

    def start(self):
        # Create the server, binding to localhost on port
        print('TCPServer Start -> ', time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        self.server = socketserver.TCPServer((self.host, self.port), MyTCPHandler)
        self.server.sock_q = self.sock_q
        self.server.ret_q = self.ret_q

        try:
            self.server.serve_forever(poll_interval=1)
        except (KeyboardInterrupt, Exception, SystemExit) as err:
            print('Error: ', err)
        finally:
            # if self.server is not None:
            print('shutdown')
            self.server.shutdown()
            sys.exit(0)


            
