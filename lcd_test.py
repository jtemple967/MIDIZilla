# import liquidcrystal_i2c
# lcd = liquidcrystal_i2c.LiquidCrystal_I2C(0x27, 1, numlines=4)
# lcd.printline(0,"Hello")

# import board
# import busio
# import adafruit_character_lcd.character_lcd_i2c as character_lcd
# i2c = busio.I2C(board.GP27, board.GP26)
# cols = 16
# rows = 2
# lcd = character_lcd.Character_LCD_I2C(i2c, cols, rows, address=0x27, backlight_inverted=True)

# import board
# import busio
# import time
# from adafruit_bus_device.i2c_device import I2CDevice
# 
# DEV_ADDR = 0x27
# WRITE_DATA = "TEST"
# 
# i2c = busio.I2C(board.GP27, board.GP26)
# device = I2CDevice(i2c, DEV_ADDR)
# 
# with device as bus_device:
#     data = bytes(0 | (1<<0x08))
#     print(data)
#     bus_device.write(data)
# #     for c in WRITE_DATA:
# #         bus_device.write(bytes([ord(c)]))
#     time.sleep(3)

# import board
# import busio
# import time
# 
# from lcd.lcd import LCD, LCD_BACKLIGHT, LCD_NOBACKLIGHT
# from lcd.i2c_pcf8574_interface import I2CPCF8574Interface
# 
# from lcd.lcd import CursorMode
# 
# i2c = busio.I2C(board.GP27, board.GP26)

# Talk to the LCD at I2C address 0x27.
# The number of rows and columns defaults to 4x20, so those
# arguments could be omitted in this case.
# lcd = LCD(I2CPCF8574Interface(i2c, 0x27), num_rows=4, num_cols=20)
# 
# lcd.set_cursor_mode(CursorMode.HIDE)
# lcd.print("abc ")
# time.sleep(2)
# lcd.clear()
# lcd.print("Turning backlight off...")
# time.sleep(2)
# lcd.set_backlight(LCD_NOBACKLIGHT)
# time.sleep(2)
# lcd.clear()
# lcd.print("Backlight back on...")
# lcd.set_backlight(LCD_BACKLIGHT)
# time.sleep(2)
# lcd.clear()
# lcd.print("This is quite long and will wrap onto the next line automatically.")
# time.sleep(3)
# lcd.clear()

# Start at the second line, fifth column (numbering from zero).
# lcd.set_cursor_pos(1, 0)
# lcd.print("Here I am")
# lcd.set_cursor_pos(1, 0)
# 
# # Make the cursor visible as a line.
# lcd.set_cursor_mode(CursorMode.BLINK)
# time.sleep(3)
# lcd.clear()
from lcdzilla.lcdzilla import lcdzilla
import json
import board

f = open('lcd_def.json')
screen_defs = json.load(f)
f.close()

lcd = lcdzilla(lcdzilla.LCD_PFC8574, 0x27, board.GP27, board.GP26, num_lines=4, num_characters=20)
lcd.set_alpha(screen_defs['alpha_characters'])
lcd.set_numbers(screen_defs['number_characters'])

lcd.load_screen(screen_defs['splash_screen'])
