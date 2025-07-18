To run MIDIZilla from a Raspberry Pi Pico:

* Install Circuit Python on the Pico: https://learn.adafruit.com/getting-started-with-raspberry-pi-pico-circuitpython/circuitpython
* On your CircuitPy drive copy the following files from this repository to the root of the drive:
   boot.py
   config.json
   lcd_def.json
   main.py
* Create a folder named "lib" if not already present
* In the "lib" folder, add the following:
  The "adafruit_midi" folder from the adafruit/Adafruit_CircuitPython_MIDI repository: https://github.com/adafruit/Adafruit_CircuitPython_MIDI
  Create a folder named "lcdzilla" and copy the contents of the following repository to this folder: https://github.com/jtemple967/lcdzilla
  The "lcd" folder from Dan Halbert's CircuitPython_LCD repository: https://github.com/dhalbert/CircuitPython_LCD/tree/main

Note that this code has not been tested with recent changes to AdaFruit's MIDI library for CitcuitPython. Dan Halbert's LCD library has 
not changed as of the writing of this document.
