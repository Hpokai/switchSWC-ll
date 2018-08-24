#!/usr/bin/env python3
# coding=utf-8
import copy

from PyCRC.CRC16 import CRC16


class CSocketDecode:
    def __str__(self):
        return "Decode data from socket."

    def __init__(self):
        self.eqid_value_dict = dict()
        self.eqbaudrate_value_dict = dict()
        self.eqtype_value_dict = dict()
        self.eqcmd_value_dict = dict()
        self.eqdata_value_dict = dict()

        self.ip = ''

        self.data = ''
        self.cmd = ''
        self.value_dict = dict()
        # self.parse()

    def decode(self, data):
        self.data = data
        start = str.find(self.data, '*')
        if start is not -1:
            self.cmd = self.data[0:start]

            if self.cmd.__eq__('EQSId') or self.cmd.__eq__('EQId'):
                self.eqid_value_dict.clear()
                self.deEQId(self.data[start+1:])
            elif self.cmd.__eq__('EQBaudrate'):
                self.eqbaudrate_value_dict.clear()
                self.deEQBaudrate(self.data[start+1:])
            elif self.cmd.__eq__('EQType'):
                self.eqtype_value_dict.clear()
                self.deEQType(self.data[start + 1:])
            elif self.cmd.__eq__('EQCmd'):
                self.deEQCmd(self.data[start + 1:])
            elif self.cmd.__eq__('EQData'):
                self.deEQData(self.data[start + 1:])
            else:
                pass
        else:
            self.cmd = None
            print('No Cmd.')



    def deEQId(self, str_setting):
        str_split = str_setting.split('#')
        self.ip = str_split[0][1:]

        for i in range(1, 13):
            key = str_split[i].split(',')
            self.eqid_value_dict[int(key[0])] = key[1]

        self.value_dict = self.eqid_value_dict
        # print(self.eqid_value_dict)

    def deEQBaudrate(self, str_setting):
        str_split = str_setting.split('#')

        for i in range(1, 13):
            key = str_split[i].split(',')
            self.eqbaudrate_value_dict[int(key[0])] = key[1:]

        self.value_dict = self.eqbaudrate_value_dict
        # print(self.eqbaudrate_value_dict)

    def deEQType(self, str_setting):
        str_split = str_setting.split('@')
        temp_dict = dict()
        temp_key_list = list()
        for i in range(1, 13):
            self.eqtype_value_dict.setdefault(i, '')

        for x in str_split:
            if x.find('$') is not -1:
                key = x.split('$')
                temp_dict.setdefault(key[0], key[1].split(':')[-1])
        # print(temp_dict)

        temp_key_list.extend(temp_dict.keys())
        # print('temp_list: ', temp_key_list)

        for kls in temp_key_list:
            if temp_dict[kls].find(',') is not -1:
                value = list(map(int, temp_dict[kls].split(',')))
                for v in value:
                    self.eqtype_value_dict[v] = kls
            else:
                value = int(temp_dict[kls])
                if value is not 0:
                    self.eqtype_value_dict[value] = kls

        self.value_dict = self.eqtype_value_dict
        # print(self.eqtype_value_dict)

    def deEQCmd(self, str_setting):
        # print(str_setting)
        str_split = str_setting.split('@')
        for x in str_split:
            if x.find(':') is not -1:
                key = x.split(':')
                if key[0] not in self.eqcmd_value_dict:
                    self.eqcmd_value_dict.setdefault(key[0], [])
                    # print('Add ' + key[0])
                self.eqcmd_value_dict[key[0]].append(key[1])

        self.value_dict = self.eqcmd_value_dict
        # print(self.eqcmd_value_dict)

    def deEQData(self, str_setting):
        # print(str_setting)
        str_split = str_setting.split('#')
        self.eqdata_value_dict.setdefault('num', int(str_split[1]))

        self.value_dict = self.eqdata_value_dict
        # print(self.eqdata_value_dict)

    @property
    def get_value(self):
        return self.value_dict

    @property
    def get_cmd(self):
        if self.cmd.__eq__(''):
            return None
        else:
            return self.cmd

    @property
    def get_eq_ip(self):
        if self.ip.__eq__(''):
            return None
        else:
            return self.ip

    @property
    def get_eqid_value(self):
        return self.eqid_value_dict

    @property
    def get_eqbaudrate_value(self):
        return self.eqbaudrate_value_dict

    @property
    def get_eqtype_value(self):
        return self.eqtype_value_dict

    @property
    def get_eqcmd_value(self):
        return self.eqcmd_value_dict

    @property
    def get_eqdata_value(self):
        return self.eqdata_value_dict


class CSocketEncode:
    def __str__(self):
        return "Encode data from socket."

    def __init__(self):
        print('socket encode')

    def encode(self, data_dict, ip):
        local_data_dict = dict()
        local_data_dict = copy.deepcopy(data_dict)

        cmd = '{}'.format(local_data_dict[0])
        ret = '{}*{}'.format(cmd, ip)
        text = ''
        if cmd == 'EQSId' or cmd == 'EQId':
            for i in range(1, 13):
                if local_data_dict[i]['Enable'] and local_data_dict[i]['Id'] is not None:
                    try:
                        text = 'SN' + ''.join(format(local_data_dict[i]['Id'][x], 'X') for x in range(len(local_data_dict[i]['Id'])))
                    except:
                        text = 'FFF'
                else:
                    text = 'FF'
                ret = '{}#{}, {}'.format(ret, i, text)
        elif cmd == 'EQBaudrate':
            for i in range(1, 13):
                text = local_data_dict[i]['Baudrate']
                ret = '{}#{}, {}'.format(ret, i, text)
        elif cmd == 'EQType':
            ret = '{}#OK'.format(ret)
        elif cmd == 'EQCmd':
            ret = '{}#OK'.format(ret)
        elif cmd == 'EQData':
            for i in range(1, 13):
                text = ''
                if local_data_dict[i]['Enable'] and local_data_dict[i]['Id'] is not None:
                    loop, length = 0, 0
                    if local_data_dict[i]['Type'] == 'SDC15':
                        loop, length = 12, 10
                    elif local_data_dict[i]['Type'] == 'KCM':
                        loop, length = 1, 8
                    elif local_data_dict[i]['Type'] == 'HUSKY':
                        loop, length = 12, 19

                    if local_data_dict[i]['Data'] == None or local_data_dict[i]['Data'] == 'BB':
                        text = 'FF'
                    else:
                        for j in range(loop):
                            text = text + '@{}'.format('-'.join(local_data_dict[i]['Data'][j*length: (j+1)*length]))
                        text = '{}*'.format(text)
                else:
                    text = 'FF'

                ret = '{}#{}{}'.format(ret, i, text)

        return '{}*&'.format(ret)

class CSerialPortDecode:
    def __str__(self):
        return "Decode data from serial port."

    def __init__(self):
        self.data_list = ['addr0', 'addr1', 'reply', 'length', 'DataRecv']

    def varifacation(self, state, data_dict):
        # print('varifacation: ', data_dict)
        ret = False
        local_data_dict = copy.deepcopy(data_dict)
        # print(local_data_dict['DataRecv'])

        if len(local_data_dict['DataRecv']) > 0:
            if local_data_dict['DataRecv'][0] != 0xbb:
                if state is 'M_PWR_ON':
                    if local_data_dict['DataRecv'][0] != 0xf0:
                        ret = True
                elif state is 'M_PWR_OFF':
                    if local_data_dict['DataRecv'][0] != 0xf0:
                        ret = True
                elif state is 'GetPortAddr':
                    ret = True
                elif state is 'EQBaudrate':
                    if local_data_dict['DataRecv'][0] != 0xdd:
                        ret = True
                elif state is 'EQId':
                    if local_data_dict['DataRecv'][0] != 0xcc:
                        ret = True

            if state is 'EQData':
                if local_data_dict['DataRecv'][0] != 0xff:
                    ret = True

        return ret

    def decode(self, state, data):
        data_dict = dict()
        local_data = [data[i] for i in range(len(data))]
        # print('local_data = ', local_data)

        crc = hex(CRC16(modbus_flag=True).calculate(bytes(local_data[0:-2])))
        high_byte, low_byte = divmod(int(crc, 0), 0x100)
        # print(hex(high_byte), hex(low_byte))

        # check CRC
        if (local_data[-2] is high_byte) and (local_data[-1] is low_byte):
            for i in range(len(self.data_list)-1):
                data_dict[self.data_list[i]] = local_data[i]
            data_dict.setdefault(self.data_list[-1], [local_data[j] for j in range(4, len(local_data)-2)])

            # check length
            if data_dict['length'] is len(local_data):
                # data varifacation
                ret = self.varifacation(state, data_dict)

                return ret, data_dict
            else:
                raise ValueError
        else:
            raise ValueError


class CSerialPortEncode:
    def __str__(self):
        return "Encode data to serial port."

    def __init__(self):
        self.Address = [0x00, 0x00]
        self.CMD = {'M_PWR_ON': 0x22, 'M_PWR_OFF': 0x23, 'GetPortAddr': 0x21, 'GotAddr': 0x21, 'EQBaudrate': 0x25, 'EQId': 0x26, 'EQData': 0x27}
        self.Para = 0x00
        self.CRC = [0x00, 0x00]
        self.Data = bytearray()

        self.set_br = ''
        self.set_bits = ''
        self.set_parity = ''
        self.set_stop = ''

        self.set_eq_type = ''
        self.set_cmd_type = ''

    def encode(self, addr, cmd, port_num):        # addr = [0x00, 0x00], cmd = 'EQBr' or 'EQId' or 'EQData'
        data = []
        data.extend(addr)
        # print('addr = {}, data = {}'.format(addr, data))
        data.append(self.CMD[cmd])
        # print('cmd = {}, data = {}'.format(cmd, data))

        if cmd is 'M_PWR_ON':
            self.Para = port_num
            data.append(self.Para)
            # print('GetPortID Para = {}, data = {}'.format(self.Para, data))
        elif cmd is 'M_PWR_OFF':
            self.Para = port_num
            data.append(self.Para)
            # print('GPIOInv Para = {}, data = {}'.format(self.Para, data))
        elif cmd is 'GetPortAddr':
            self.Para = 0xfd
            data.append(self.Para)
            # print('GPIOInv Para = {}, data = {}'.format(self.Para, data))
        elif cmd is 'GotAddr':
            self.Para = port_num
            data.append(self.Para)
            # print('GPIOInv Para = {}, data = {}'.format(self.Para, data))
        elif cmd is 'EQBaudrate':
            self.Para = self.paraEQBr()
            data.append(self.Para)
            # print('Para = {}, data = {}'.format(self.Para, data))
        elif cmd is 'EQId':
            self.Para = 0x00
            data.append(self.Para)
            # print('Para = {}, data = {}'.format(self.Para, data))
        elif cmd is 'EQData':
            self.Para = self.paraEQData()
            data.append(self.Para)
            
        high, low = divmod(int(hex(CRC16(modbus_flag=True).calculate(bytes(data))), 0), 0x100)
        data.append(high)
        data.append(low)

        # print('self.Data = ', self.Data)
        self.Data = data
        return self.Data

    def paraEQBr(self):
        br_dict = {'1200': 0, '2400': 1, '4800': 2, '9600': 3, '19200': 4, '38400': 5, '115200': 6}
        bits_dict = {'7': 0, '8': (1 << 3)}
        parity_dict = {'None': 0, 'Odd': (1 << 5), 'Even': (1 << 6),
                       'N': 0, 'O': (1 << 5), 'E': (1 << 6)}
        stop_dict = {'1': 0, '2': (1 << 7)}

        return (br_dict[self.set_br] + bits_dict[self.set_bits] +
                parity_dict[self.set_parity] + stop_dict[self.set_stop])

    def paraEQData(self):
        eq_type_dict = {'KCM': 0, 'SDC15': 1, 'HUSKY': 2}
        cmd_type_dict = {'temperature': 0, 'setting': (1 << 4)}

        return eq_type_dict[self.set_eq_type] + cmd_type_dict[self.set_cmd_type]

    def set_baudrate(self, br, bits, parity, stop):
        self.set_br = br
        self.set_bits = bits
        self.set_parity = parity
        self.set_stop = stop

    def set_data(self, eq_type, cmd_type):
        self.set_eq_type = eq_type
        self.set_cmd_type = cmd_type


# for testing
if __name__ == "__main__":
    
    cmd = 'EQSId*@192.168.0.22#1,0#2,0#3,0#4,0#5,0#6,0#7,0#8,0#9,0#10,0#11,0#12,0#&'
    '''
    cmd = 'EQCmd*@KCM:010310010001D10A@Husky:04262031222005@Husky:04262032222005@Husky:04262033222005' \
          '@Husky:04262034222005@Husky:04262035222005@Husky:04262036222005@Husky:04262037222005' \
          '@Husky:04262038222005@Husky:04262039222005@Husky:0426203A222005@Husky:0426203B222005' \
          '@Husky:0426203C222005@SDC15:0103238D00025FA4@SDC15:0203238D00025F97@SDC15:0303238D00025E46' \
          '@SDC15:0403238D00025FF1@SDC15:0503238D00025E20@SDC15:0603238D00025E13@SDC15:0703238D00025FC2' \
          '@SDC15:0803238D00025F3D@SDC15:0903238D00025EEC@SDC15:0A03238D00025EDF@SDC15:0B03238D00025F0E' \
          '@SDC15:0C03238D00025EB9@&'
    cmd = 'EQId*@192.168.0.22#1,0#2,0#3,0#4,0#5,0#6,0#7,0#8,0#9,0#10,0#11,0#12,0#&'
    cmd = 'EQBaudrate*#1,19200,8,N,1#2,19200,8,N,1#3,19200,8,N,1#4,9600,8,N,1#5,NULL' \
          '#6,NULL#7,NULL#8,NULL#9,NULL#10,NULL#11,NULL#12,NULL#&'
    
    # cmd = 'EQType*@KCM$N1:4@Husky$N0:0@SDC15$N3:1,2,3@&'
    # cmd = 'EQType*@KCM$N5:4,7,9,10,12@Husky$N1:8@SDC15$N3:1,2,3@&'
    cmd = 'EQData*#12#&'
    '''
    
    csp = CSocketDecode()
    for i in range(1):
        csp.parse(cmd)
        print('CMD: ' + csp.cmd)
        print(csp)
        print(csp.get_eq_ip)
        print(csp.get_eqid_value)
        # print(csp.get_eqbaudrate_value)
        # print(csp.get_eqtype_value)
        # print(csp.get_eqcmd_value)
        #print(csp.get_eqdata_value)

