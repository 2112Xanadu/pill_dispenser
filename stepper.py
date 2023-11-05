from machine import Pin

class Stepper:
    def __init__(self, in0, in1, in2, in3):
        self._pins = [ Pin(in0, Pin.OUT, value = 0),
                       Pin(in1, Pin.OUT, value = 0),
                       Pin(in2, Pin.OUT, value = 0),
                       Pin(in3, Pin.OUT, value = 0) ]
        self._steps = [ (1, 0, 0, 0),
                        (1, 1, 0, 0),
                        (0, 1, 0, 0),
                        (0, 1, 1, 0),
                        (0, 0, 1, 0),
                        (0, 0, 1, 1),
                        (0, 0, 0, 1),
                        (1, 0, 0, 1) ]
        self._idx = 0
        
    def step(self, dir):
        if dir: self._idx -= 1
        else: self._idx += 1
        self._idx = self._idx % 8
        self._pins[0](self._steps[self._idx][0])
        self._pins[1](self._steps[self._idx][1])
        self._pins[2](self._steps[self._idx][2])
        self._pins[3](self._steps[self._idx][3])

