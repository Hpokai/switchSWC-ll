#!/usr/bin/env python3
# coding=utf-8

import serial
import time
import RPi.GPIO as GPIO
import random
import queue
import copy

from swc_DataDecoder import CSerialPortEncode
from swc_DataDecoder import CSerialPortDecode

'''
class CIO:
    def __str__(self):
        return "Modularize GPIO."

    def __init__(self):
        print('')

    def SetOutput(self, pin):
        # to use RPi board pin numbers
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(pin, GPIO.OUT)

    def SetInput(self, pin):
        # to use RPi board pin numbers
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(pin, GPIO.IN)

    def WriteOutputHigh(self, pin):
        self.SetOutput(pin)
        GPIO.output(pin, GPIO.HIGH)

    def WriteOutputLow(self, pin):
        self.SetOutput(pin)
        GPIO.output(pin, GPIO.LOW)

    def ReadInput(self, pin):
        self.SetInput(pin)
        state = GPIO.input(pin)

        ret = 'high'
        if state == GPIO.LOW:
            ret = 'low'

        return ret

    def Close(self):
        GPIO.cleanup()
'''

class CSerial:
    def __str__(self):
        return "CSerial: Modularize Serial Port."

    def __init__(self, baudrate=74880, timeout=3):
        # Set gpio 12 as output pin and low voltage.
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(12, GPIO.OUT)
        GPIO.output(12, GPIO.LOW)

        self.isInit = True
        self.timeout = timeout
        try:
            self.ser = serial.Serial('/dev/ttyAMA0',
                                     baudrate=baudrate,
                                     parity=serial.PARITY_NONE,
                                     stopbits=serial.STOPBITS_ONE,
                                     bytesize=serial.EIGHTBITS,
                                     timeout=timeout
                                     )
        except serial.SerialException as error:
            print('Serial Exception: Init Fail.({})'.format(error))
            self.isInit = False

    def OpenPort(self):
        if self.isInit is True:
            self.ClosePort()
            try:
                self.ser.open()
            except Exception as err:
                print('err = ',err)
                self.isInit = False
            else:
                print('{} Active Device: {}\n'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), self.ser.name))
            self.ser.flush()

        return self.isInit

    def WriteData(self, data):
        self.ser.flushInput()
        self.ser.flushOutput()
        # Set gpio 12 high voltage.
        GPIO.output(12, GPIO.HIGH)
        time.sleep(0.01)

        local_data = []
        local_data.extend(data)
        ret, send_num = True, 0
        if self.isInit is True:
            try:
                send_num = self.ser.write(local_data)
            except serial.SerialException as error:
                print('Serial Exception: ', error)
                ret = False
            finally:
                time.sleep(0.030)

                #Set gpio 12 low voltage.
                GPIO.output(12, GPIO.LOW)
                
                time.sleep(0.01)
                return ret, send_num
        else:
            #Set gpio 12 low voltage.
            GPIO.output(12, GPIO.LOW)
            
            time.sleep(0.01)
            return self.isInit, send_num

    def SetTimeout(self, timeout, default=False):
        if default is False:
            self.ser.timeout = timeout
        else:
            self.ser.timeout = self.timeout

    def ReadData(self):
        if self.isInit is True:
            # print('isInit= True')
            ret = ''
            # self.ser.flushInput()
            # self.ser.flushOutput()
            try:
                # ret = self.ser.readline().decode()
                # ret = self.ser.readline()
                # ret = self.ser.read(size=256)
                run, tm_out = 1, 0
                while run:
                    try:
                        ret = self.ser.read_all()
                        print('ret = ', ret)
                    except Exception as err:
                        print('err = ', err)
                    if len(ret) > 5:
                        run = 0
                    else:
                        tm_out += 1
                        if tm_out > self.ser.timeout*5:
                            raise serial.SerialTimeoutException
                        time.sleep(0.2)

            except (serial.SerialException, serial.SerialTimeoutException) as error:
                print('Serial TimeoutException: ', error)
                ret = ''
            except KeyboardInterrupt as error:
                print('KeyboardInterrupt: ', error)
                ret = None
            finally:
                return ret
        else:
            return None

    def ClosePort(self):
        GPIO.cleanup()
        if self.isInit is True:
            if self.ser.isOpen() is True:
                self.ser.close()


class CSerialSever:
    ProcessMode_define = ('Handshake', 'EqSetting', 'EqRoutine')
    
    def __init__(self, sock_q, ret_q):
        self.server = None
        self.sock_q = sock_q
        self.ret_q = ret_q
        
        GPIO.setmode(GPIO.BOARD)
        self.cs = CSerial()

        self.cspe = CSerialPortEncode()
        self.cspd = CSerialPortDecode()

        self.is_initial = True
        self.ProcessMode_selected = 'Handshake'
        self.run_forever = True

        self.is_re_EqSetting = False
        self.is_re_Handshake = False

        self.re_EqSetting_data = None

        self.reHandshakeTimeout_start = 0
        self.reHandshakeTimeout_end = 0

        self.cmd_storage = dict()

    # data structure = DS
    def init_data_structure(self):
        port = [{'GPIO Pin': 11, 'Enable': False, 'Addr': None, 'Id': None, 'Baudrate': 0, 'Type': None, 'Data': None},
                {'GPIO Pin': 13, 'Enable': False, 'Addr': None, 'Id': None, 'Baudrate': 0, 'Type': None, 'Data': None},
                {'GPIO Pin': 16, 'Enable': False, 'Addr': None, 'Id': None, 'Baudrate': 0, 'Type': None, 'Data': None},
                {'GPIO Pin': 15, 'Enable': False, 'Addr': None, 'Id': None, 'Baudrate': 0, 'Type': None, 'Data': None},
                {'GPIO Pin': 18, 'Enable': False, 'Addr': None, 'Id': None, 'Baudrate': 0, 'Type': None, 'Data': None},
                {'GPIO Pin': 26, 'Enable': False, 'Addr': None, 'Id': None, 'Baudrate': 0, 'Type': None, 'Data': None},
                {'GPIO Pin': 24, 'Enable': False, 'Addr': None, 'Id': None, 'Baudrate': 0, 'Type': None, 'Data': None},
                {'GPIO Pin': 22, 'Enable': False, 'Addr': None, 'Id': None, 'Baudrate': 0, 'Type': None, 'Data': None},
                {'GPIO Pin': 33, 'Enable': False, 'Addr': None, 'Id': None, 'Baudrate': 0, 'Type': None, 'Data': None},
                {'GPIO Pin': 29, 'Enable': False, 'Addr': None, 'Id': None, 'Baudrate': 0, 'Type': None, 'Data': None},
                {'GPIO Pin': 32, 'Enable': False, 'Addr': None, 'Id': None, 'Baudrate': 0, 'Type': None, 'Data': None},
                {'GPIO Pin': 31, 'Enable': False, 'Addr': None, 'Id': None, 'Baudrate': 0, 'Type': None, 'Data': None}]

        # 0 for cmd from 
        self.ds = {0: None,
                   1: port[0],
                   2: port[1],
                   3: port[2],
                   4: port[3],
                   5: port[4],
                   6: port[5],
                   7: port[6],
                   8: port[7],
                   9: port[8],
                   10: port[9],
                   11: port[10],
                   12: port[11]}

    def start(self):
        print('SerialServer Start -> ', time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

        self.init_data_structure()
        self.Set_GPIO_input_mode()

        while self.run_forever:
            try:
                if self.ProcessMode_selected == 'Handshake':
                    self.run_Handshake()
                elif self.ProcessMode_selected == 'EqSetting':
                    self.run_EqSetting()
                elif self.ProcessMode_selected == 'EqRoutine':
                    self.run_EqRoutine()

                time.sleep(0.1)
            except KeyboardInterrupt as error:
                print('{} Except: {}.'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), error))
                run_forever = False
                
        self.cs.ClosePort()

    def Set_GPIO_input_mode(self):
        # default_pin = (11, 13, 16, 15, 18, 26, 24, 22, 33, 29, 32, 31)
        for index in range(1, 13):
            pin = self.ds[index]['GPIO Pin']
            GPIO.setup(pin, GPIO.IN)
            
    def run_Handshake(self):
        print('\n{} STATE: {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 'run_Handshake'))
        self.process_Handshake()
        print('\nDS: \n{}'.format(self.ds))

        if self.is_initial is True:
            self.ProcessMode_selected = 'EqSetting'
            self.is_initial = False
        else:
            self.is_re_Handshake = False
            self.ProcessMode_selected = 'EqRoutine'
            self.reHandshakeTimeout_start = time.time()

    def run_EqSetting(self):
        print('\n{} STATE: {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 'run_EqSetting'))

        if self.is_re_EqSetting is False:
            while self.run_forever:
                try:
                    ret = self.sock_q.get(block=True, timeout=1)
                except queue.Empty:
                    print('sock_q.get')
                    # pass
                else:
                    print('sock_q.get = ', ret)
                    break
                
                time.sleep(1)
        else:
            # re_EqSetting = True
            ret = self.re_EqSetting_data
            self.is_re_EqSetting = False

        cmd, data = ret[0], ret[1]
        self.process_EqSetting(cmd, data)

        send_ds = copy.deepcopy(self.ds)
        self.ret_q.put(send_ds)

        # the lastest cmd is 'EQCmd', should go to next process mode
        if cmd == 'EQCmd':
            self.is_re_EqSetting = False
            self.is_re_Handshake = False
            self.ProcessMode_selected = 'EqRoutine'
            self.reHandshakeTimeout_start = time.time()

    def run_EqRoutine(self):
        print('\n{} STATE: {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 'run_EqRoutine'))

        for port_num in range(1, 13):
            cmd, data = None, None
            try:
                ret = self.sock_q.get(block=True, timeout=0.2)
            except queue.Empty:
                print('sock_q.get = Empty')
            else:
                cmd, data = ret[0], ret[1]
                print('\n{} CMD: {}, Data: {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), cmd, data))

            # if cmd = EQSId, then change mode = EqSetting (self.is_re_EqSetting = True).
            if cmd == 'EQSId':
                self.re_EqSetting_data = copy.deepcopy(ret)
                self.is_re_EqSetting = True
                self.ProcessMode_selected = 'EqSetting'
                break
            else:
                # Acquire the i-th sensor data.
                self.process_EqRoutine(port_num)

                # if cmd = EQId or EQData, then set the latest DS[i].SN or DS[i].Data to ret_q.
                if cmd == 'EQId' or cmd == 'EQData':
                    self.ds[0] = cmd
                    send_ds = copy.deepcopy(self.ds)
                    self.ret_q.put(send_ds)

        if self.is_re_EqSetting is False:
            self.reHandshakeTimeout_end = time.time()
            elapsed_time_sec = self.reHandshakeTimeout_end - self.reHandshakeTimeout_start
            print('elapsed_time_sec = {}'.format(elapsed_time_sec))
            if elapsed_time_sec > 120:
                self.is_re_Handshake = True
                self.ProcessMode_selected = 'Handshake'

    def process_Handshake (self):
        print('{} STATE: {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 'process_Handshake'))

        # test the 12th port.
        for port_num in range(1, 13):
        # for port_num in range(1, 7):
            if self.ds[port_num]['Enable'] is False:
                state = 'M_PWR_ON'

                print('{} port({}): {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), port_num, state))

                recv_dict = dict()
                ret, recv_dict = self.serial_run(state, port_num)
                print('{} port({}): {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), port_num, ret))
                print('{} Data: {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), recv_dict))

                if ret is False:
                    self.turnoff_port_power(port_num, True)

                else:
                    # wait for nano initial
                    time.sleep(2.0)
                    # read GPIO[i] input state
                    io_state = GPIO.input(self.ds[port_num]['GPIO Pin'])
                    print('{} GPIO({}): {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), port_num, io_state is GPIO.HIGH))

                    is_handshake_successful = None
                    if io_state is GPIO.HIGH:
                        state = 'GetPortAddr'
                        ret, recv_dict = self.serial_run(state, port_num)
                        print('{} port({}): {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), port_num, ret))
                        print('{} Data: {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), recv_dict))
                        is_handshake_successful = ret

                        if is_handshake_successful is True:
                            self.got_port_address(port_num)

                            self.ds[port_num]['Enable'] = True
                            self.ds[port_num]['Addr'] = [recv_dict['DataRecv'][0], recv_dict['DataRecv'][1]]
                            # print(self.ds[port_num])

                    if io_state is GPIO.LOW or is_handshake_successful is False:
                        self.turnoff_port_power(port_num, True)
                time.sleep(0.5)

    def process_EqSetting(self, local_cmd, local_data):
        print('{} step: {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 'process_EqSetting'))
        self.ds[0] = local_cmd

        if local_cmd == 'EQSId':
            print('{} CMD: {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), local_cmd))

            for port_num in range(1, 13):
                if self.ds[port_num]['Enable'] is True:
                    ret, recv_dict = self.serial_run('EQId', port_num, self.ds[port_num]['Addr'])
                    print('{} port({}): {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), port_num, ret))
                    print('{} Data: {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), recv_dict))

                    if ret is True:
                        self.ds[port_num]['Id'] = [x for x in recv_dict['DataRecv']]
                    else:
                        self.turnoff_port_power(port_num)

        elif local_cmd == 'EQBaudrate':
            print('{} CMD: {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), local_cmd))

            for port_num in range(1, 13):
                if self.ds[port_num]['Enable'] is True:
                    ret, recv_dict = self.serial_run('EQBaudrate', port_num, self.ds[port_num]['Addr'], local_data[port_num])
                    print('{} port({}): {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), port_num, ret))
                    print('{} Data: {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), recv_dict))

                    if ret is True:
                        self.ds[port_num]['Baudrate'] = 1
                    else:
                        self.turnoff_port_power(port_num)

        elif local_cmd == 'EQType':
            print('{} CMD: {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), local_cmd))

            for port_num in range(1, 13):
                self.ds[port_num]['Type'] = local_data[port_num]

        elif local_cmd == 'EQCmd':
            print('{} CMD: {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), local_cmd))

            self.cmd_storage = copy.deepcopy(local_data)
            local_data.clear()

    def process_EqRoutine(self, port_num):
        print('{} step: {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 'process_EqRoutine'))

        if self.ds[port_num]['Enable'] == True and self.ds[port_num]['Id'] != None:
            ret, recv_dict = self.serial_run('EQData', port_num, self.ds[port_num]['Addr'], self.ds[port_num]['Type'])
            print('{} port({}): {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), port_num, ret))
            print('{} Data: {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), recv_dict))

            if ret:
                if recv_dict['DataRecv'][0] != 0xbb:
                    for i in range(1, 13):
                        if self.ds[i]['Enable'] == True and self.ds[i]['Id'] != None:
                            if self.ds[i]['Addr'][0] == recv_dict['addr0'] and self.ds[i]['Addr'][1] == recv_dict['addr1']:
                                self.ds[i]['Data'] = [format(recv_dict['DataRecv'][x], 'X') for x in range(len(recv_dict['DataRecv']))]
                    '''
                    self.ds[port_num]['Data'] = [format(recv_dict['DataRecv'][x], 'X') for x in range(len(recv_dict['DataRecv']))]
                    '''
                print(self.ds[port_num])
            else:
                self.turnoff_port_power(port_num)

    def turnoff_port_power(self, port_num, force=False):
        io_state = GPIO.input(self.ds[port_num]['GPIO Pin'])
        print('{} Turn Off Power: {}: {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), port_num, io_state))

        if io_state == GPIO.LOW or force == True:
            self.ds[port_num]['Enable'] = False
            self.ds[port_num]['Addr'] = None
            self.ds[port_num]['Id'] = None
            self.ds[port_num]['Baudrate'] = 0
            self.ds[port_num]['Type'] = None
            self.ds[port_num]['Data'] = None

            ret, recv_dict = self.serial_run('M_PWR_OFF', port_num)
            print('{} port({}): {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), port_num, ret))
            print('{} Data: {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), recv_dict))

    def prepare_parameters(self, state, port_num, addr=None, setting_data=None):
        print('{} step: {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 'prepare parameters'))

        para = ''
        if state is 'M_PWR_ON':
            para = self.cspe.encode([0xff, 0xfd], state, port_num)
        # elif state is 'M_PWR_OFF':
        #     para = self.cspe.encode([0xff, 0xfd], state, port_num)
        elif state is 'GetPortAddr':
            para = self.cspe.encode([0xff, 0xfe], state, port_num)
        elif state is 'GotAddr':
            para = self.cspe.encode([0xff, 0xfc], state, port_num)
        elif state is 'EQBaudrate':
            self.cspe.set_baudrate(setting_data[0], setting_data[1], setting_data[2], setting_data[3])
            para = self.cspe.encode(addr, state, port_num)
        elif state is 'EQId':
            para = self.cspe.encode(addr, state, port_num)
        elif state is 'EQData':
            # The 2nd para is for Huskey only.
            self.cspe.set_data(setting_data, 'temperature')
            para = self.cspe.encode(addr, state, port_num)

        print('{} Para: {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), [hex(para[i]) for i in range(len(para))]))
        return para

    def got_port_address(self, port_num):
        parameters = self.prepare_parameters('GotAddr', port_num)
        print('{} step: {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 'Do SEND data'))

        sdata = bytearray(parameters)
        ret, send_num = self.cs.WriteData(sdata)
        print('{} write({}): {}\n'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                                        send_num,
                                        [hex(sdata[i]) for i in range(len(sdata))]))

    def serial_run(self, state, port_num, addr=None, setting_data=None):
        print('{} STATE: {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 'serial_run'))

        need_recv, need_send = False, False
        cnt = 0
        parameters = None
        is_run = True
        rdata = None
        ret, recv_dict = False, dict()

        re_try = 2

        while is_run is True:
            if need_recv is True:
                print('{} step: {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 'Do RECV data'))

                rdata = self.cs.ReadData()
                if rdata is '':
                    print('{} step: {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 'RECV timeout'))
                    if state == 'EQData':
                        cnt = re_try
                    if cnt < re_try:
                        # re-send data
                        cnt += 1
                    else:
                        # this port fail
                        need_recv = False
                        need_send = False
                        is_run = False
                        ret = False

                else:
                    print('{} step: {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 'Decode data'))

                    # Check CRC and length
                    try:
                        is_correct, recv_dict = self.cspd.decode(state, rdata)
                    except ValueError as err:
                        print('{} step: {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 'Data Value Error'))

                        if cnt < re_try:
                            # re-send data
                            cnt += 1
                        else:
                            # this port fail
                            need_recv = False
                            need_send = False
                            is_run = False
                            ret = False
                    else:
                        if is_correct is True:
                            print('{} step: {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 'Data correct'))

                            need_recv = False
                            need_send = False
                            is_run = False
                            ret = True
                        else:
                            print('{} step: {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 'Data incorrect'))

                            if cnt < re_try:
                                # re-send data
                                cnt += 1
                            else:
                                # this port fail
                                need_recv = False
                                need_send = False
                                is_run = False
                                ret = False
            else:
                print('{} step: {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 'Need not RECV data'))

                # select state to prepare parameters
                parameters = self.prepare_parameters(state, port_num, addr, setting_data)
                need_send = True
                need_recv = True
                # cnt = 0
                # state = 'wait_{}'.format(state)

            if need_send is True:
                print('{} step: {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 'Do SEND data'))

                sdata = bytearray(parameters)
                ret, send_num = self.cs.WriteData(sdata)
                print('{} write({}): {}\n'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                                                send_num,
                                                [hex(sdata[i]) for i in range(len(sdata))]))

            time.sleep(0.2)

        return ret, recv_dict

if __name__ == "__main__":
    '''
    cio = CIO()
    cio.SetOutput(12)
    cio.WriteOutputLow(12)

    time.sleep(1.0)
    '''
    print('--- Serial start ---')
    cs = CSerial(timeout=5)
    if cs.isInit is True:

        if cs.OpenPort() is True:
            # time.sleep(0.5)
            total, wrong = 0, 0
            cnt = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            hex_str = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
            while 1:
                try:
                    '''
                    cio.WriteOutputHigh(12)
                    print('{} Out "HIGH".'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
                    '''
                    # ser.flushOutput()

                    byte_num = 32

                    rnd = random.randint(0, 11)
                    cnt[rnd] += 1
                    print('cnt[{}] = {}'.format(rnd, cnt[rnd]))
                    print(cnt)

                    ba = bytearray([0x7B])
                    ba.append(0x30 + hex_str[rnd])
                    for i in range(byte_num - 1):
                        ba.append(0x30 + random.randint(0, 74))
                    ba.append(0x7D)

                    ret, send_num = cs.WriteData(ba)
                    print('{} write({}): {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                                                    send_num,
                                                    ba.decode()))

                    '''
                        baudrate 38400: limit 0.005 sec / under 16 byte
                                              0.010 sec / 32 byte
                                              0.020 sec / 64 byte
                                              0.025 sec / 96 byte
                        baudrate 57600: limit 0.015 sec / 64 byte
                                              0.020 sec / 96 byte
                        baudrate 74880: limit 0.010 sec / 64 byte
                                              0.015 sec / 96 byte
                    '''
                    '''
                    time.sleep(0.015)
                    cio.WriteOutputLow(12)
                    print('{} Out "LOW".'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
                    time.sleep(0.001)
                    '''

                    data = cs.ReadData()
                    if data is not None:
                        data = data[:-1]
                        print("{} readline: {}".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), data))

                        if data != ba.decode()[1:-1]:
                            wrong += 1
                        total += 1

                        print(' =======================================\n',
                              'Wrong: {}, Total: {}, Percetage: {}%\n'.format(wrong, total, 100 * (total - wrong) / total),
                              '=======================================\n')

                        time.sleep(1.0)
                    else:
                        break

                except KeyboardInterrupt:
                    break

        print('\n{} Serial Down.'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
        cs.ClosePort()
        # cio.Close()

