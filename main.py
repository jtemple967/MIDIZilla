import traceback
import sys
import time
import board
import digitalio
# import network
import json
from lcdzilla.lcdzilla import lcdzilla
import usb_midi
import adafruit_midi
import simpleio
from analogio import AnalogIn
from adafruit_midi.control_change import ControlChange

debug = False

def load_cc_values():
    return [cur_mapping['cc1'], cur_mapping['cc2'], cur_mapping['cc3'],
                 cur_mapping['cc4'], cur_mapping['cc5'], cur_mapping['cc6'], cur_mapping['ex']]

def load_cc_labels():
    cc_label_list = []
    if cur_mapping['cc1'] >= 0:
        cc_label_list.append(cur_mapping['cc1_lbl'])
    else:
        cc_label_list.append("Off")
    if cur_mapping['cc2'] >= 0:
        cc_label_list.append(cur_mapping['cc2_lbl'])
    else:
        cc_label_list.append("Off")
    if cur_mapping['cc3'] >= 0:
        cc_label_list.append(cur_mapping['cc3_lbl'])
    else:
        cc_label_list.append("Off")
    if cur_mapping['cc4'] >= 0:
        cc_label_list.append(cur_mapping['cc4_lbl'])
    else:
        cc_label_list.append("Off")
    if cur_mapping['cc5'] >= 0:
        cc_label_list.append(cur_mapping['cc5_lbl'])
    else:
        cc_label_list.append("Off")
    if cur_mapping['cc6'] >= 0:
        cc_label_list.append(cur_mapping['cc6_lbl'])
    else:
        cc_label_list.append("Off")
    if cur_mapping['ex'] >= 0:
        cc_label_list.append(cur_mapping['ex_lbl'])
    else:
        cc_label_list.append("Off")
    return cc_label_list

def build_map_select(cur_map):
    mapping_screen_def = []
    for idx, line in enumerate(screen_defs["select_mapping"]):
        for field in line:
            if "id" in field and field["id"] != "selectmapping":
                mapping_screen_def.append(line)
            if "id" in field and field["id"] == "selectmapping":
                for mapping_idx, mapping in enumerate(config_data["mappings"]):
                    if mapping["name"] == cur_map["name"]:
                        map_name = "*" + mapping["name"]
                    else:
                        map_name = mapping["name"]
                    new_line = [{"text":map_name,"select":True,"id":"selectmapping","key":mapping["name"]}]
                    mapping_screen_def.append(new_line)
        if debug:
            print("Select mapping screen: {0}".format(mapping_screen_def))
    return mapping_screen_def

def test_leds():
    for x in range(3):
        for led in cc_leds:
            led.value = True
        fault.value = True
        target = time.monotonic() + .5
        while time.monotonic() < target:
            pass
        for led in cc_leds:
            led.value = False
        fault.value = False
        target = time.monotonic() + .5
        while time.monotonic() < target:
            pass

# Startup process
try:
    
    # Create the pin for our fault LED. Turn on your fault light. Let it shine whever you go...
    fault = digitalio.DigitalInOut(board.GP11)
    fault.direction = digitalio.Direction.OUTPUT
    fault.value = False
    
    # Load the screen definitions
    if debug:
        print("Loading screen definitions...")
    f = open('lcd_def.json')
    screen_defs = json.load(f)
    f.close()
    if debug:
        print("Screen definitions loaded...")

    #  Pins for the footswitches. Adjust this as needed for more/less footswitches
    cc_pins = [board.GP18, board.GP19, board.GP20, board.GP21, board.GP22,
                 board.GP27]
    cc_buttons = []
    cc_button_states = []
    cc_led_pins = [board.GP12, board.GP13, board.GP14, board.GP15, board.GP16, board.GP17]
    cc_leds = []

    for pin in cc_pins:
        cc_pin = digitalio.DigitalInOut(pin)
        cc_pin.direction = digitalio.Direction.INPUT
        cc_pin.pull = digitalio.Pull.UP
        cc_buttons.append(cc_pin)
        cc_button_states.append(False)
        
    # Pin for the expression pedal
    ex_pin = AnalogIn(board.A0)
    mod_val2 = 0
        
    # Build the cc LED pin array, toggle on/off as a LED test
    for pin in cc_led_pins:
        cc_led = digitalio.DigitalInOut(pin)
        cc_led.direction = digitalio.Direction.OUTPUT
#         cc_led.value = True
#         target = time.monotonic() + .25
#         while time.monotonic() < target:
#             pass
#         cc_led.value = False
        cc_leds.append(cc_led)
    if debug:
        test_leds()
        
    # In my configuration one of the switches is a mode switch
    mode_select = digitalio.DigitalInOut(board.GP28)
    mode_select.direction = digitalio.Direction.INPUT
    mode_select.pull = digitalio.Pull.UP
    mode_select_state = None

    # Pins for the navigation buttons.
    menu = digitalio.DigitalInOut(board.GP2)
    menu_state = None
    select = digitalio.DigitalInOut(board.GP3)
    select_state = None
    up = digitalio.DigitalInOut(board.GP4)
    up_state = None
    up_long_press = False
    down = digitalio.DigitalInOut(board.GP5)
    down_state = None
    down_long_press = False
    left = digitalio.DigitalInOut(board.GP6)
    left_state = None
    right = digitalio.DigitalInOut(board.GP7)
    right_state = None
    f1 = digitalio.DigitalInOut(board.GP8)
    f1_state = None
    f2 = digitalio.DigitalInOut(board.GP9)
    f2_state = None
    f3 = digitalio.DigitalInOut(board.GP10)
    f3_state = None
#     f4 = digitalio.DigitalInOut(board.RUN)
#     f4_state = None
    navigation = [menu, select, up, down, left, right, f1, f2, f3]

    for button in navigation:
        button.direction = digitalio.Direction.INPUT
        button.pull = digitalio.Pull.UP
        
    # Create the LCD
    lcd = lcdzilla(lcdzilla.LCD_PFC8574, 0x27, board.GP1, board.GP0, num_lines=4, num_characters=20)
    lcd.set_debug(debug)
    lcd.set_alpha_lower(screen_defs['alpha_lower_characters'])
    lcd.set_alpha_upper(screen_defs['alpha_upper_characters'])
    lcd.set_symbols(screen_defs['symbol_characters'])
    lcd.set_numbers(screen_defs['number_characters'])
    lcd.set_character_set_key("F1")
    lcd.set_bkspc_key("F2")

    # Create the USB midi device
    midi = adafruit_midi.MIDI(midi_out=usb_midi.ports[1], out_channel=1)
    
    main_state = None
    state_change = False
    clock = None
    key_value = None

    config_data = None
    config_dft = {
        "mappings" : [
            {
                'name':'default',
                'cc1':60,
                'cc2':61,
                'cc3':62,
                'cc4':63,
                'cc5':-1,
                'cc6':-1,
                'ex':-1,
                'cc1_lbl':"Chrs",
                'cc2_lbl':"Fuzz",
                'cc3_lbl':"Loop",
                'cc4_lbl':"Tune",
                'cc5_lbl':"",
                'cc6_lbl':"",
                'ex_lbl':""
            }
        ],
        'wifi_ssid':"",
        'wifi_pwd':"",
        'modep_host':"",
        'pedalboards':[],
        'cc_mappng':[],
        'cur_mapping':"default"
    }
    cur_mapping = None
    save_config = False
    
    # Get the config file data
    try:
        config_file = open('config.json', 'r')
        if config_file:
            config_data = json.load(config_file)
            config_file.close()
            if debug:
                print("Loaded config file: {0}".format(config_data))
    except Exception as ex:
        config_data = config_dft
        if debug:
            print("Didn't load config file, using default. Error: {0}".format(ex))
        
    # Set the current mapping
    for mapping in config_data["mappings"]:
        if mapping['name'] == config_data["cur_mapping"]:
            cur_mapping = mapping
    # If current mapping is not found then use the default mapping
    if not cur_mapping:
        for mapping in config_data["mappings"]:
            if mapping["name"] == "default":
                cur_mapping = mapping
                config_data["cur_mapping"] = "default"

    # Load the midi control codes array
    cc_values = load_cc_values()
    # Load the button labels array
    cc_labels = load_cc_labels()

except Exception as ex:
    fault.value = True
    with open("error.log", "w") as log_file:
       traceback.print_exception(ex, ex, ex.__traceback__, file=log_file)
    sys.exit(1)
    
if debug:
    print(config_data)
    print(cc_buttons)
    print(cc_values)

while True:
    
    try:
        
        # Here we are checking if the buttons were released but they were previously pressed.
        state_reset = False
        if menu.value and menu_state:
            menu_state = None
            state_reset = True
        if select.value and select_state:
            select_state = None
            state_reset = True
        if up.value and up_state:
            up_state = None
            up_long_press = False
            state_reset = True
        if down.value and down_state:
            down_state = None
            down_long_press = False
            state_reset = True
        if left.value and left_state:
            left_state = None
            state_reset = True
        if right.value and right_state:
            right_state = None
            state_reset = True
        if f1.value and f1_state:
            f1_state = None
            state_reset = True
        if f2.value and f2_state:
            f2_state = None
            state_reset = True
        if f3.value and f3_state:
            f3_state = None
            state_reset = True
#         if f4.value and f4_state:
#             f4_state = None
#             state_reset = True            
        if mode_select.value and mode_select_state:
            mode_select_state = None
            state_reset = True
        for i in range(len(cc_buttons)):
            if cc_buttons[i].value and cc_button_states[i]:
                cc_button_states[i] = False
                state_reset = True

        # Sleep for a short time so the button is not detected to be pressed again
        if state_reset:
            clock = None
            target = time.monotonic() + .10
            while time.monotonic() < target:
                pass
            # time.sleep(.10)

        # Determine what button was pressed, if any. A menu button pressed will
        # immediately change the state to config state. Note that we'll only
        # process the menu button press the first time until the button is released and
        # the state is reset at the top of the loop.  This prevents the same action from
        # happening multiple times in one press. Pressing the menu key in config mode
        # will put the device back in Midi mode.
        if not menu.value and not menu_state:
            menu_state = True
            if debug:
                print("You pressed the menu key")
            if main_state != "Config":
                main_state = "Config"
                state_change = True
            else:
                main_state = "Midi"
                state_change = True
        
        # The mode select button will put the board into mapping select mode
        if not mode_select.value and not mode_select_state and main_state != "MapSelect":
            if debug:
                print("Pressed mode select")
            main_state = "MapSelect"
            state_change = True
            
        if main_state == None:
            # Show the splash on the LCD
            lcd.load_screen(screen_defs["splash_screen"])
            target = time.monotonic() + 3
            while time.monotonic() < target:
                pass
            # time.sleep(3)
            main_state = "Midi"
            state_change = True
        elif main_state == "Midi":
            if state_change:
                # Load the midi information into the screen definition
                for line in screen_defs["midi_screen"]:
                    for subfield in line:
                        cc_array = -1
                        if "id" in subfield and subfield["id"] == "cc1":
                            cc_array = 0
                        elif "id" in subfield and subfield["id"] == "cc2":
                            cc_array = 1
                        elif "id" in subfield and subfield["id"] == "cc3":
                            cc_array = 2
                        elif "id" in subfield and subfield["id"] == "cc4":
                            cc_array = 3
                        elif "id" in subfield and subfield["id"] == "cc5":
                            cc_array = 4
                        elif "id" in subfield and subfield["id"] == "cc6":
                            cc_array = 5
                        elif "id" in subfield and subfield["id"] == "ex":
                            cc_array = 6
                        if cc_array >= 0:
                            if cc_array <= 5:
                                subfield["text"] = "{0}-{1}".format(cc_array+1, cc_labels[cc_array])
                            else:
                                subfield["text"] = "E-{0}".format(cc_labels[cc_array])
                lcd.load_screen(screen_defs["midi_screen"])
                lcd.load_status_line(cur_mapping["name"])
                state_change = False
            # Check if any cc button was pressed
            for i in range(len(cc_buttons)):
                if not cc_buttons[i].value and not cc_button_states[i]:
                    # Don't send a control code if < 0
                    if cc_values[i] >= 0:
                        modulation = ((not cc_leds[i].value)*127)
                        if debug:
                            print("Modulation: {0}".format(modulation))
                        midi.send(ControlChange(cc_values[i], modulation))
                        cc_button_states[i] = True
                        cc_leds[i].value = not cc_leds[i].value
                        status_text = ">>>{0}<<<".format(cc_labels[i])
                        if debug:
                            print(status_text)
                        # lcd.load_status_line(status_text)
                    else:
                        lcd.load_status_line("Switch {0} not mapped".format(str(i+1)))
            # If the expression pedal is enabled then get the value of the pedal. If
            # changed by more than 2 then send the control code with value
            if cur_mapping["ex"] >= 0:
                mod_val1 = round(simpleio.map_range(ex_pin.value, 0, 65535, 0, 127))
                if abs(mod_val1 - mod_val2) > 2:
                    if debug:
                        print("Mod1: {0}; Mod2: {1}".format(mod_val1, mod_val2))
                    mod_val2 = mod_val1
                    modulation = int(mod_val2)
                    midi.send(ControlChange(cc_values[6], modulation))
            # time.sleep(1)
        elif main_state == "MapSelect":
            if state_change:
                mapping_screen_def = build_map_select(cur_mapping)
                lcd.load_screen(mapping_screen_def)
                state_change = False
            # Selected a map
            if not mode_select.value and not mode_select_state:
                mode_select_state = True
                subfield = lcd.enter()
                # Exiting map select mode goes back to MIDI mode
                if 'previous' in subfield:
                    main_state = "Midi"
                    state_change = True
                elif "id" in subfield and subfield["id"] == "selectmapping":
                    config_data["cur_mapping"] = subfield["text"]
                    for mapping in config_data["mappings"]:
                        if mapping["name"] == subfield["key"]:
                            cur_mapping = mapping
                            break
                    save_config = True
                    main_state = "Midi"
                    state_change = True
            # Pressing button 3 is same as the up key
            if not cc_buttons[2].value and not cc_button_states[2]:
                cc_button_states[2] = True
                lcd.cursor_up()
            # Pressing button 6 is the same as the down key
            if not cc_buttons[5].value and not cc_button_states[5]:
                cc_button_states[5] = True
                lcd.cursor_down()
                                
        elif main_state == "Config":

            # Have we entered up key long press?
            if not up.value and clock and time.monotonic() >= (clock+1):
                up_long_press = True
            if not down.value and clock and time.monotonic() >= (clock+1):
                down_long_press = True
                
            if state_change:
                for line in screen_defs["config_screen"]:
                    for field in line:
                        if 'id' in field and field['id'] == "mapping_label":
                            field['text'] = cur_mapping["name"]
                lcd.load_screen(screen_defs["config_screen"])
                state_change = False
            if not up.value and (not up_state or up_long_press):
                up_state = True
                if debug:
                    lcd.print_debug()
                lcd.cursor_up()
                # The up and down keys can be long pressed to speed up value changing. Save the
                # current time for checking for long press
                clock = time.monotonic()
                if debug:
                    print("You pressed the up key")
            elif not down.value and (not down_state or down_long_press):
                down_state = True
                lcd.cursor_down()
                clock = time.monotonic()
                if debug:
                    print("You pressed the down key")
            elif not left.value and not left_state:
                left_state = True
                lcd.cursor_left()
                if debug:
                    print("You pressed the left key")
            elif not right.value and not right_state:
                right_state = True
                lcd.cursor_right()
                if debug:
                    print("You pressed the right key")
            elif not select.value and not select_state:
                select_state = True
                subfield = lcd.enter()
                if debug:
                    print("You pressed the select key")
                    print(subfield)
                # Don't do anything if the subfield return was nothing. An input error occurred
                if subfield:
                    # Exiting config goes back to Midi send mode
                    if 'previous' in subfield and subfield['previous'] == 'Midi':
                        main_state = "Midi"
                        state_change = True
                    # Else the menu has another prior screen
                    elif 'previous' in subfield:
                        lcd.load_screen(screen_defs[subfield['previous']])
                    # Else the menu has a next which just displays another submenu
                    elif 'next' in subfield:
                        lcd.load_screen(screen_defs[subfield['next']])
                    # Else test LEDs
                    elif 'id' in subfield and subfield['id'] == 'test_leds':
                        if debug:
                            print("Testing LEDs")
                        test_leds()
                    # Switch edit menu
                    elif 'id' in subfield and subfield['id'] == 'editswitch':
                        key_value = subfield["key"]
                        # If the switch is currently disabled then only show an option to
                        # enable the switch
                        if cur_mapping[key_value] == -1:
                            for line in screen_defs["enable_switch"]:
                                for field in line:
                                    if "id" in field and field["id"] == "switch_label":
                                        field["text"] = subfield["text"]
                                    if "key" in field:
                                        field["key"] = key_value
                            lcd.load_screen(screen_defs["enable_switch"])
                        else:
                            for line in screen_defs["edit_switch"]:
                                for field in line:
                                    if "id" in field and field["id"] == "switch_label":
                                        field["text"] = subfield["text"]
                                    if "id" in field and field["id"] == "disableswitch":
                                        field["key"] = key_value
                            lcd.load_screen(screen_defs["edit_switch"])
                    # Edit control code
                    elif 'id' in subfield and subfield['id'] == 'editcc':
                        for line in screen_defs["edit_cc"]:
                            for field in line:
                                if "id" in field and field["id"] == "ccvalue":
                                    field["text"] = cur_mapping[key_value]
                                    field["key"] = key_value 
                        lcd.load_screen(screen_defs["edit_cc"])
                    # Edit switch label
                    elif 'id' in subfield and subfield['id'] == 'editlabel':
                        for line in screen_defs["edit_label"]:
                            for field in line:
                                if "id" in field and field["id"] == "labelvalue":
                                    field["text"] = cur_mapping[(key_value + "_lbl")]
                                    field["key"] = key_value + "_lbl"
                        lcd.load_screen(screen_defs["edit_label"])
                    # Set the current mapping name in the save as text field
                    elif 'id' in subfield and subfield['id'] == "savemappingas":
                        for line in screen_defs["save_mapping"]:
                            for field in line:
                                if "id" in field and field["id"] == "mappingname":
                                    field["text"] = cur_mapping["name"]
                        lcd.load_screen(screen_defs["save_mapping"])
                    elif 'id' in subfield and subfield['id'] == "select_mapping":
                        mapping_screen_def = build_map_select(cur_mapping)
                        lcd.load_screen(mapping_screen_def)            
                    # Switch enabled
                    elif 'id' in subfield and subfield['id'] == "enableswitch":
                        cur_mapping[subfield["key"]] = 0
                        lcd.load_screen(screen_defs["config_switch"])
                        save_config = True
                    # Switch disabled
                    elif 'id' in subfield and subfield['id'] == "disableswitch":
                        cur_mapping[subfield["key"]] = -1
                        lcd.load_screen(screen_defs["config_switch"])
                        save_config = True
                    # Control code updated
                    elif 'id' in subfield and subfield['id'] == "ccvalue":
                        cur_mapping[subfield["key"]] = subfield['text']
                        lcd.load_screen(screen_defs["edit_switch"])
                        save_config = True
                    # Label value updated
                    elif 'id' in subfield and subfield['id'] == "labelvalue":
                        cur_mapping[subfield["key"]] = subfield["text"]
                        lcd.load_screen(screen_defs["edit_switch"])
                        save_config = True
                    # Mapping selected
                    elif 'id' in subfield and subfield['id'] == "selectmapping":
                        mapping_name = subfield["key"]
                        config_data["cur_mapping"] = mapping_name
                        main_state = "Midi"
                        state_change = True
                        save_config = True
                    # Saving mapping name as..
                    elif 'id' in subfield and subfield['id'] == "mappingname":
                        mapping_name = subfield["text"]
                        if debug:
                            print("Looking for mapping: {0}".format(mapping_name))
                            print("Current config: {0}".format(config_data))
                        for mapping in config_data["mappings"]:
                            if debug:
                                print("Mapping name: {0}".format(mapping["name"]))
                            if mapping["name"] == mapping_name:
                                mapping = cur_mapping
                                save_config = True
                        if not save_config:
                            if debug:
                                print("Didn't find mapping, appending new value")
                            new_mapping = cur_mapping.copy()
                            new_mapping["name"] = mapping_name
                            if debug:
                                print("New mapping: {0}".format(new_mapping))
                            config_data["mappings"].append(new_mapping)
                            save_config = True
                        config_data["cur_mapping"] = mapping_name
                        if debug:
                            print("Config after change: {0}".format(config_data))
                        # lcd.load_screen(screen_defs["config_screen"])
                        state_change = True
                        
                    # Delete mapping
                    elif 'id' in subfield and subfield['id'] == "deletemapping":
                        if cur_mapping["name"] == "default":
                            lcd.load_screen(screen_defs["cannot_delete"])
                        else:
                            for mapping_idx, mapping in enumerate(config_data["mappings"]):
                                if mapping["name"] == cur_mapping["name"]:
                                    del config_data["mappings"][mapping_idx]
#                                     config_data["mappings"].remove(mapping_idx)
                                    config_data["cur_mapping"] = "default"
                                    save_config = True
                                    state_change = True
                            
            # The F1 key will switch between character states
            elif not f1.value and not f1_state:
                f1_state = True
                lcd.sel_character_set()
                if debug:
                    print("You pressed the F1 key")
            # The F2 key will be a backspace key
            elif not f2.value and not f2_state:
                f2_state = True
                lcd.backspace()
                if debug:
                    print("You pressed the F2 key")
            # F3 doesn't do anything right now
            elif not f3.value and not f3_state:
                f3_state = True
                if debug:
                    print("You pressed the F3 key")
#             # F4 now activates the RUN button
#             elif not f4.value and not f4_state:
#                 f4_state = True
#                 if debug:
#                     print("You pressed the F4 key")

        # Save the config
        if save_config:
            # Ensure the current mapping is loaded
            for mapping in config_data["mappings"]:
                if mapping["name"] == config_data["cur_mapping"]:
                    cur_mapping = mapping
                    break
            # Reload the cc values and labels
            cc_values = load_cc_values()
            cc_labels = load_cc_labels()
            # Save the config
            with open('config.json', 'w') as f:
                json.dump(config_data, f)
            save_config = False
            
    except Exception as ex:
        fault.value = True
        try:
            with open("error.log", "w") as log_file:
               traceback.print_exception(ex, ex, ex.__traceback__, file=log_file)
        except Exception as ex2:
            pass