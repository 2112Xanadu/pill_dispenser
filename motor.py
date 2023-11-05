from machine import Pin, ADC, I2C
from stepper import Stepper
from buttons import Button
from counter import Counter
from led import Led
import ssd1306
import time
from lora import Lora

# Resources:
# https://docs.micropython.org/en/v1.15/library/utime.html
# https://datasheets.raspberrypi.com/pico/raspberry-pi-pico-python-sdk.pdf
# https://docs.micropython.org/en/latest/rp2/quickref.html
# https://lastminuteengineers.com/getting-started-with-raspberry-pi-pico-w/?utm_content=cmp-true
# https://blog.martinfitzpatrick.com/using-micropython-raspberry-pico/
# https://electrocredible.com/raspberry-pi-pico-external-interrupts-button-micropython/
# https://datasheets.raspberrypi.com/picow/connecting-to-the-internet-with-pico-w.pdf
# https://how2electronics.com/getting-started-with-raspberry-pi-pico-w-using-micropython/

# Initializing components
motor = Stepper(2, 3, 4, 5)
opto = Pin(16, mode = Pin.IN, pull = Pin.PULL_UP)
counter = Counter(17)
led = Led(20)
led.off()
pin0 = Button(9, Pin.IN, Pin.PULL_UP)
pin1 = Button(8, Pin.IN, Pin.PULL_UP)
pin2 = Button(7, Pin.IN, Pin.PULL_UP)
lora = Lora(0, Pin(0), Pin(1), 9600)
sda=machine.Pin(14) 
scl=machine.Pin(15) # Sda and scl pins is for the oled 
i2c=machine.I2C(1, sda=sda, scl=scl, freq=400000)
display = ssd1306.SSD1306_I2C(128, 64, i2c)

# Function to display text on the OLED screen
def display_text(text1, text2="", text3="", text4="", text5=""):
    display.poweron()
    display.fill(0) # Clear display
    display.text(text1, 0, 10, 1)
    display.text(text2, 0, 20, 1)
    display.text(text3, 0, 30, 1)
    display.text(text4, 0, 40, 1)
    display.text(text5, 0, 50, 1)
    display.show()
    
display_text("Connecting")

# Constants
MAX_PILL_COUNT = 7
MAX_DAYS = 7
FULL_CIRCLE_STEPS = 140 # rotate dispenser full circle
ONE_SLOT_STEPS = 514 # rotate dispenser one slot forward
NUM_OF_BLINKS = 4

# Variables
day_counter = 0
pill_counter = 0
opto_zero = True

# Time variables
cTime = time.localtime() # Get current time
d_str = '{:02d}.{:02d}.{:02d}'.format(cTime[2], cTime[1], cTime[0]) # Format date
t_str = '{:02d}:{:02d}:{:02d}'.format(cTime[3], cTime[4], cTime[5]) # Format time

# LoRa Initialization and join procedure
lora.at('+ID')
lora.wait('AppEui')
lora.at('+MODE=LWOTAA')
lora.wait('+MODE: LWOTAA')
lora.at('+DR')
lora.wait('EU868')
lora.at('+KEY=APPKEY,"53e221d9552a38648861b92fc83d54d0"')
lora.wait('+KEY: APPKEY')
lora.at('+CLASS=A')
lora.wait('+CLASS: A')
lora.at('+PORT=8')
lora.wait('+PORT: 8')

lora.at('+JOIN')
status, res = lora.wait('+JOIN: Done', 12)
while not status or res.find('failed') >= 0:
    lora.at('+JOIN')
    status, res = lora.wait('+JOIN: Done', 12)

    
# Function to calibrate dispenser
def calibrate_dispenser():
    global day_counter, pill_counter, opto_zero

    display_text("Calibration", "has started.")
    print("Calibrating...")
    # Initialize a variable 'num' to 1, which represents permission to run the calibration
    num = 1
    # Initialize the opto sensor state
    opto_zero = True
    
    # Check if the opto.value() is 0 or 1, if the opto sensor is not triggered
    # opto sensor is in its initial state, and the dispenser is at its start position. If opto.zero is set to 'False', it would not work properly
    if not opto.value():
        opto_zero = True

    # Run the calibration while 'num' is equal to 1
    # Move the dispenser motor one step
    while num == 1:
        motor.step(False) # Right direction
        time.sleep(0.002)
        
        # Check if the opto.value() is equal to 0 -> the opto sensor is triggered. If the 'opto_zero' is 'True', the dispenser would not stop rotating
        if opto.value() and opto_zero:
            opto_zero = False
            
        # Check if the opto.value() is equal to 1 -> the opto sensor is not triggered and 'opto_zero' is 'False'
        # Set 'num' to 0, indicating the calibration is complete
        if not opto.value() and not opto_zero:
            num = 0
            display_text("Calibration", "stopped.", "Press SW_1 to", "get a daily pill", "/SW_2 to see res.")
            print("Calibration stopped.")
            
            # Position dispenser neatly to start position
            for i in range(FULL_CIRCLE_STEPS):
                motor.step(False)
                time.sleep(0.002)
            # Pill counter, day counter and opto sensor state will be reseted
            counter.reset()
            pill_counter = 0
            day_counter = 0


# Function to move dispenser one slot
def move_one_slot():
    global day_counter, pill_counter

    # Set counter to 0, and increment the day_counter
    counter.reset()
    day_counter += 1
    print("Day:", day_counter)
    display_text("Day: %d" % day_counter)

    # Move the dispenser one slot in right direction
    for i in range(ONE_SLOT_STEPS):
        motor.step(False)
        time.sleep(0.002)

    # Check if a pill was detected
    if counter.get() > 0:
        pill_counter += 1
        time.sleep(0.002)
        print("Pill count:", pill_counter)
        display_text("", "Pill count: %d" % pill_counter)
        counter.reset()
    else:
        # Pill was not detected, sending LoRa message
        print("Pill was not detected.")
        display_text("Day: %d" % day_counter, "", "Pill was not", "detected.")
        
        # Turning the LED on and off, pauses for 250 ms
        for i in range(NUM_OF_BLINKS * 2):
            led.toggle()
            time.sleep(0.25)
        send_lora_message(lora, f"Pill not detected. Time: {d_str}, {t_str}")


# Function for LoRa one-way communication
def send_lora_message(lora, message):
    lora.at(f'+MSG="{message}"')
    success, response = lora.wait('MSG: Done', 10)
    if success:
        print("LoRa message sent successfully:", message)
    else:
        print("Failed to send LoRa message:", message)


# Display text on the OLED screen
display_text("Hello patient,", "Please calibrate.", "", "Press SW_0")

# Main loop for button presses and other conditions
while True:
    time.sleep(0.010)

    # SW_0 is pressed
    # Calibrates the pill dispenser
    if pin0.pressed():
        calibrate_dispenser()

    # SW_1 is pressed
    # Checks whether pill_counter has reached the MAX_PILL_COUNT, otherwise moves dispenser one slot ccw
    if pin1.pressed():
        if pill_counter == MAX_PILL_COUNT or (day_counter == MAX_DAYS):
            display_text("Day count was", "reached.", "Please calibrate", "by pressing SW_0", "/SW_2 to see res.")
            print("No more pills for you. Please calibrate", "by pressing SW_0")
            send_lora_message(lora, f"Patient's maximum day count was reached. Time: {d_str}, {t_str}")
            
        elif pill_counter < MAX_PILL_COUNT:
            move_one_slot()  
    
    # SW_2 is pressed
    # Displays measurement results on the OLED screen and sends a message via LoRaWAN
    if pin2.pressed():
        display_text("Measurements:", "During %d days" % day_counter, "you had %d pills." % pill_counter)
        print("Measurements: During %d days" % day_counter, "you had %d pills." % pill_counter, "LoRa message sent %s" % d_str, "%s." % t_str)
        send_lora_message(lora, f"Measurement sent: During {day_counter} days, Pill count {pill_counter}. Time: {d_str}, {t_str}")
        

display.poweroff()
