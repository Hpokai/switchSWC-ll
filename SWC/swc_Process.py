#!/usr/bin/env python3
# coding=utf-8

import queue
from threading import Timer, Thread, Event
import time
import random
from swc_AsyncSocketServer import AsyncSocketServer
from swc_ComPort import CSerialSever


class CSerialThread(Thread):
    def __str__(self):
        return "Run Serial Communication in one thread."

    def __init__(self, setting_queue, return_queue):
        Thread.__init__(self)
        self.setting_queue = setting_queue
        self.return_queue = return_queue
        self.stop_event = Event()

    def run(self):
        print('CSerialThread: --- Serial start ---')
        '''
        while not self.stop_event.isSet():
            # print('CSerialThread: to get something......')
            try:
                ret = self.setting_queue.get(block=True, timeout=1)
            except queue.Empty:
                # print('CSerialThread: Empty queue')
                pass
            else:
                self.setting_queue.task_done()
                print("({}) {} wrote:".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 'Serial recv (from Server)'), end=' ')
                print(ret)
                self.return_queue.put(ret)

            time.sleep(1)
        '''
        self.css = CSerialSever(self.setting_queue, self.return_queue)
        self.css.start()
        
        print('CSerialThread: Thread end')

    def join(self, timeout=None):
        print('CSerialThread: thread join!')
        self.css.run_forever = False
        self.stop_event.set()
        Thread.join(self, timeout)


class CEthernetThread(Thread):
    def __str__(self):
        return "Run Ethernet Communication in one thread."

    def __init__(self, setting_queue, return_queue):
        Thread.__init__(self)
        self.setting_queue = setting_queue
        self.return_queue = return_queue
        self.stop_event = Event()

    def run(self):
        print('CEthernetThread: --- Ethernet start ---')
        ass = AsyncSocketServer('', 5000, self.setting_queue, self.return_queue)
        ass.start()
        
        print('CEthernetThread: Thread end')

    def join(self, timeout=None):
        print('CEthernetThread: thread join!')
        self.stop_event.set()
        Thread.join(self, timeout)


if __name__ == "__main__":
    # server cmd -> SWC FW
    set_q = queue.Queue(10)
    # SWC FW -> server cmd
    ret_q = queue.Queue(10)

    cst = CSerialThread(set_q, ret_q)
    cst.start()

    # Wait SWC handshake complete!
    time.sleep(5)

    cet = CEthernetThread(set_q, ret_q)
    cet.start()

    while 1:
        try:
            time.sleep(0.5)
        except KeyboardInterrupt as err:
            break

    set_q.join()
    ret_q.join()
    cst.join()
    # cet.join()
    print('main close')
