from machine import Pin

class Counter:

    def __init__(self, io_pin_nr):
        self.input = Pin(io_pin_nr, mode = Pin.IN, pull = Pin.PULL_UP)
        self.count = 0
        self.input.irq(handler = self.handler, trigger = Pin.IRQ_FALLING, hard = True )

    def handler(self, pin):
        self.count += 1

    def get(self):
        return self.count
    
    def reset(self):
        self.count = 0

