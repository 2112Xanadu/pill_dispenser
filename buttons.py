from machine import Pin, I2C
import time


class Button(Pin):
    def __init__(self, id, mode=- 1, pull=- 1):
        super().__init__(id, mode, pull)
        self.down = False
        pass
    
    def pressed(self):
        if self.down:
            if self.value(): self.down = False
        else:
            if not self.value():
                self.down = True
                return True
        return False


