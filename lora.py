from machine import UART, Pin
import random
import time

class Lora:
    def __init__(self, uart_nr, tx_pin, rx_pin, speed):
        self.uart = UART(uart_nr, baudrate=speed, tx=tx_pin, rx=rx_pin, timeout = 1000)

    def at(self, cmd):
        # note: AT-commands require CR-LF to be accepted
        self.uart.write(bytes('AT' + cmd + '\r\n', 'iso-8859-1'))  # write 

    def send(self, cmd):
        # note: AT-commands require CR-LF to be accepted
        self.uart.write(bytes(cmd+'\r\n', 'iso-8859-1'))  # write 
        
    def read(self):
        res = self.uart.read(200)         # read 
        if res != None:
            print(res.decode('iso-8859-1'))
            return len(res)
        else:
            return 0
        
    def wait(self, reply, count=1):
        str = ''
        while count > 0 :
            res = self.uart.read(200)         # read 
            if res != None:
                str = str + res.decode('iso-8859-1')
                print(str)
            count = count - 1
            if str.find(reply) >= 0:
                return True, str
        return False, str            


