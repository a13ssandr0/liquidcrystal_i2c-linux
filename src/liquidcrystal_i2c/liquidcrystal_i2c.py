from smbus import SMBus
from time import sleep
from re import match

# other commands
LCD_CLEARDISPLAY = 0x01
LCD_RETURNHOME = 0x02
LCD_ENTRYMODESET = 0x04
LCD_DISPLAYCONTROL = 0x08
LCD_CURSORSHIFT = 0x10
LCD_FUNCTIONSET = 0x20
LCD_SETCGRAMADDR = 0x40
LCD_SETDDRAMADDR = 0x80

# flags for display entry mode
LCD_ENTRYRIGHT = 0x00
LCD_ENTRYLEFT = 0x02
LCD_ENTRYSHIFTINCREMENT = 0x01
LCD_ENTRYSHIFTDECREMENT = 0x00

# flags for display on/off control
LCD_DISPLAYON = 0x04
LCD_DISPLAYOFF = 0x00
LCD_CURSORON = 0x02
LCD_CURSOROFF = 0x00
LCD_BLINKON = 0x01
LCD_BLINKOFF = 0x00

# flags for display/cursor shift
LCD_DISPLAYMOVE = 0x08
LCD_CURSORMOVE = 0x00
LCD_MOVERIGHT = 0x04
LCD_MOVELEFT = 0x00

# flags for function set
LCD_8BITMODE = 0x10
LCD_4BITMODE = 0x00
LCD_2LINE = 0x08
LCD_1LINE = 0x00
LCD_5x10DOTS = 0x04
LCD_5x8DOTS = 0x00

# flags for backlight control
LCD_BACKLIGHT = 0x08
LCD_NOBACKLIGHT = 0x00

En = 0b00000100  # Enable bit
Rw = 0b00000010  # Read/Write bit
Rs = 0b00000001  # Register select bit

class LCD():

    # constructor also replaces lcd::begin()
    def __init__(self, bus=None, addr=0x27, cols=16, rows=2, charsize=LCD_5x8DOTS):
        if bus==None: # linux systems have multiple i2c buses user has to select one
            raise SyntaxError("missing i2c bus number")
        self._bus = SMBus(bus)
        self._addr = addr
        self._cols = cols
        self._rows = rows
        self._charsize = charsize
        self._backlightval = LCD_BACKLIGHT
        self._displayfunction = LCD_4BITMODE | LCD_2LINE if (self._rows > 1) else LCD_1LINE | LCD_5x10DOTS if (
            # for some 1 line displays you can select a 10 pixel high font
            not self._charsize == 0 and self._rows == 1) else LCD_5x8DOTS

        # put the LCD into 4 bit mode
        # this is according to the hitachi HD44780 datasheet
        # figure 24, pg 46

        # we start in 8bit mode, try to set 4 bit mode
        self.write4bits(0x03 << 4)
        # second try
        self.write4bits(0x03 << 4)
        # third go!
        self.write4bits(0x03 << 4)
        # finally, set to 4-bit interface
        self.write4bits(0x02 << 4)
        # set # lines, font size, etc.
        self.command(LCD_FUNCTIONSET | self._displayfunction)
        # turn the display on with no cursor or blinking default
        self._displaycontrol = LCD_DISPLAYON | LCD_CURSOROFF | LCD_BLINKOFF
        self.display()
        # clear it off
        self.clear()
        # Initialize to default text direction (for roman languages)
        self._displaymode = LCD_ENTRYLEFT | LCD_ENTRYSHIFTDECREMENT
        # set the entry mode
        self.command(LCD_ENTRYMODESET | self._displaymode)
        # we're ready!
        self.home()
        

    # *********** low level data pushing commands *********

    # write either command or data
    def send(self, cmd, mode=0):
        self.write4bits(mode | (cmd & 0xF0))
        self.write4bits(mode | ((cmd << 4) & 0xF0))

    def write4bits(self, data):
        self.expanderWrite(data)
        self.pulseEnable(data)

    def expanderWrite(self, cmd):
        self._bus.write_byte(self._addr, cmd | self._backlightval)
        sleep(0.0001)

    # clocks EN to latch command
    def pulseEnable(self, data):
        self.expanderWrite(data | En)
        sleep(.0005)
        self.expanderWrite(data & ~En)
        sleep(.0001)

    # ********** mid level commands, for sending data/cmds
    def command(self, value):
        self.send(value, 0)

    def write(self, value):
        self.send(value, Rs)

    #********* high level commands, for the user!
    # clear lcd
    def clear(self):
        self.command(LCD_CLEARDISPLAY)

    # set cursor to home
    def home(self):
        self.command(LCD_RETURNHOME)

    def setCursor(self, col, row):
        row_offsets = [0x00, 0x40, 0x14, 0x54]
        if row > self._rows:
            row = self._rows-1  # we count rows starting w/0
        self.command(LCD_SETDDRAMADDR | (col + row_offsets[row]))

    # Turn the display on/off (quickly)
    def noDisplay(self):
        self._displaycontrol &= ~LCD_DISPLAYON
        self.command(LCD_DISPLAYCONTROL | self._displaycontrol)
    def display(self):
        self._displaycontrol |= LCD_DISPLAYON
        self.command(LCD_DISPLAYCONTROL | self._displaycontrol)

    # Turns the underline cursor on/off
    def noCursor(self):
        self._displaycontrol &= ~LCD_CURSORON
        self.command(LCD_DISPLAYCONTROL | self._displaycontrol)
    def cursor(self):
        self._displaycontrol |= LCD_CURSORON
        self.command(LCD_DISPLAYCONTROL | self._displaycontrol)

    # Turn on and off the blinking cursor
    def noBlink(self):
        self._displaycontrol &= ~LCD_BLINKON
        self.command(LCD_DISPLAYCONTROL | self._displaycontrol)
    def blink(self):
        self._displaycontrol |= LCD_BLINKON
        self.command(LCD_DISPLAYCONTROL | self._displaycontrol)

    # These commands scroll the display without changing the RAM
    def scrollDisplayLeft(self):
        self.command(LCD_CURSORSHIFT | LCD_DISPLAYMOVE | LCD_MOVELEFT)
    def scrollDisplayRight(self):
        self.command(LCD_CURSORSHIFT | LCD_DISPLAYMOVE | LCD_MOVERIGHT)

    # This is for text that flows Left to Right
    def leftToRight(self):
        self._displaymode |= LCD_ENTRYLEFT
        self.command(LCD_ENTRYMODESET | self._displaymode)

    # This is for text that flows Left to Right
    def rightToLeft(self):
        self._displaymode &= ~LCD_ENTRYLEFT
        self.command(LCD_ENTRYMODESET | self._displaymode)

    # This will 'right justify' text from the cursor
    def autoscroll(self):
        self._displaymode |= LCD_ENTRYSHIFTINCREMENT
        self.command(LCD_ENTRYMODESET | self._displaymode)

    # This will 'left justify' text from the cursor
    def noAutoscroll(self):
        self._displaymode &= ~LCD_ENTRYSHIFTINCREMENT
        self.command(LCD_ENTRYMODESET | self._displaymode)

    # Allows us to fill the first 8 CGRAM locations
    # with custom characters
    def createChar(self, location, charmap):
        if not type(charmap) == list:
            raise TypeError(
                "object of type {} is not a list".format(type(charmap)))
        if location < 0 or location > 7:
            # instead of `location &= 0x7` from LiquidCrystal_I2C we warn the user
            raise ValueError(
                "custom characters can only use positions between 0 and 7, position {} is invalid".format(location))
        if len(charmap) > 8:
            raise ValueError(
                "custom characters cannot be taller than 8 lines, provided: {}".format(len(charmap)))
        elif len(charmap) < 8:
            # add blank lines to shorter characters
            for line_num in range(len(charmap), 8):
                charmap[line_num] = 0x00
        for row in charmap:
            if not type(row) == int:
                raise TypeError(
                    "custom characters must be defined as a list of integers")

        self.command(LCD_SETCGRAMADDR | (location << 3))
        for line_num in range(8):
            self.write(charmap[line_num])

    # Turn the (optional) backlight off/on
    def noBacklight(self):
        self._backlightval = LCD_NOBACKLIGHT
        self.expanderWrite(0)
    def backlight(self):
        self._backlightval = LCD_BACKLIGHT
        self.expanderWrite(0)

    # put string function
    def print(self, string):
        for char in string:
            self.write(ord(char))

    # put extended string function. Extended string may contain placeholder like {0xFF} for 
    # displaying the particular symbol from the symbol table
    def printExt(self, string):
        # Process the string
        while string:
            # Trying to find pattern {0xFF} representing a symbol
            result = match(r'\{0[xX][0-9a-fA-F]{2}\}', string)
            if result:
                self.write(int(result.group(0)[1:-1], 16))
                string = string[6:]
            else:
                self.write(ord(string[0]))
                string = string[1:]