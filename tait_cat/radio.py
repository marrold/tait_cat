import serial
import time

# TODO: Handle serial errrors. eg serial.serialutil.SerialException: [Errno 19] could not open port /dev/ttyUSB0: [Errno 19] No such device: '/dev/ttyUSB0'
# TODO: Add bandwidth and ctcss commands
# TODO: Load presets from csv file?


def calculate_checksum(message):

    modulo_2_sum = sum(ord(c) for c in message) % 256
    twos_complement = (256 - modulo_2_sum) % 256
    checksum_hex = format(twos_complement, "02X")
    return checksum_hex


def validate_checksum(message):

    command = message[:-2]
    checksum = message[-2:]
    calcualted_checksum = calculate_checksum(command)

    if checksum == calcualted_checksum:
        return True
    else:
        return False


class Radio:

    def __init__(self, port, baud=9600, timeout=1):

        self.port = port
        self.baud = baud
        self.timeout = 0.1


    def chng_chan(self, channel):

        command = f"g{str(len(channel)).zfill(2)}{channel}"

        response = self.send_command(command)

        if response:

            if response[0] == ".": # TODO: This should probably raise an exception thats caught later
                return channel

            elif response[0] == "e":
                self.handle_ccdi_error(response)

            elif response[0] == "p" and response[3:6] == "210":
                new_chan = response[6:-2]
                if new_chan != channel:
                    raise Exception("Wrong Channel")
                else:
                    return channel

            else:
                raise Exception(f"Invalid response to chang_chan: {response}")
    

    def get_temp(self):

        command = "q045047"

        response = self.send_command(command, 2)

        if response:
            temp, adc = self.resp_get_temp(response)
        else:
            raise Exception("get_temp failed")

        return temp, adc


    def get_ser(self):

        command = "q014"

        response = self.send_command(command)

        if response:
            version = self.resp_get_ser(response)
        else:
            raise Exception("get_ser failed")
    
        return version


    def ccdi_pulse(self):

        # Abuse getting the serial to figure out if we're in CCDI or CCR mode
        command = "q014"

        response = self.send_command(command)

        if response:
            version = self.resp_ccdi_pulse(response)
        else:
            raise Exception("ccdi_pulse failed")
    
        return version        


    def query_mode(self):

        if self.ccdi_pulse():
            return "CCDI"
        
        elif self.ccr_pulse():
            return "CCR"
        
        else:
            raise Exception("Couldn't determine mode")


    def ccr_enter(self):

        command = "f0200"

        response = self.send_command(command)

        if response:
            return self.resp_ccr_enter(response)

        else:
            raise Exception("ccr_enter failed")


    def ccr_exit(self):

        command = "E00"

        self.send_raw(command)

        # You don't get a response when the radio exits CCR mode
        # as it reboots.
        # Lets loop and wait for the radio to reboot, checking 
        # until we know the radio is back in CCDI mode
        for i in range(10):

            time.sleep(1)

            # Ignore all exceptions whilst the radio reboots
            try:
                if self.query_mode() == "CCDI":
                    return True
            except Exception:
                pass

        raise Exception("timeout whilst waiting to exit CCR mode")


    def ccr_pulse(self):

        command = "Q01P"

        pulse_fail = False
        try:
            response = self.send_command(command)

        except Exception: #TODO: Catch a better exception?
            raise
            #pulse_fail = True

        if pulse_fail and self.ccdi_pulse() is True:
            raise Exception("Radio is in CCDI mode")

        # A pulse has a dedicated response, so first we check the ack is valid
        # then we check the outcome of the pulse
        if response and response[0 == "+"]:
            return self.resp_ccr_pulse(response)
        else:
            self.handle_error(response)

        raise Exception("ccr_pulse failed")


    def ccr_tx(self, freq):

        command = f"T09{freq}"

        response = self.send_command(command)

        if response:
            return self.resp_ccr_ack(response)


    def ccr_rx(self, freq):

        command = f"R09{freq}"

        response = self.send_command(command)

        if response:
            return self.resp_ccr_ack(response)


    def ccr_pwr(self, pwr):

        command = f"P01{pwr}"

        response = self.send_command(command)

        if response:
            return self.resp_ccr_ack(response)


    def read_serial(self, ser, chars):

        response = ser.read(chars).decode(encoding="ascii")

        if response == "":
            raise Exception("Timeout occurred while reading from serial interface.")
        else:
            return response


    def send_command(self, command, num_responses=1):

        command = f"{command}{calculate_checksum(command)}\r\n"
        responses = []
        
        with serial.Serial(self.port, self.baud, timeout=self.timeout) as ser:
            # Send the message
            ser.write(command.encode(encoding="ascii"))

            for i in range(num_responses):

                try:
                    # Read until a period is received, discarding anything that's not a period
                    response = ""
                    while True:
                        ch = self.read_serial(ser, 1)
                        if ch in ['.', '-', '+', 'e', 'Q']: #TODO: This should include M?
                            response = response + ch
                            break

                    if response == ".":
                        # Capture the length and remaining characters
                        command = self.read_serial(ser, 1)
                        size = self.read_serial(ser, 2)
                        length = int(size) + 2
                        response += f"{command}{size}{self.read_serial(ser, length)}"
                    else:
                        size = self.read_serial(ser, 2)
                        length = int(size) + 2
                        response += f"{size}{self.read_serial(ser, length)}"

                except Exception: # TODO: We only really want to catch serial timeouts here
                    if response != ".":
                        response = ""
                    pass
            
                # If the response is empty we must have timed out. Skip this iteration.
                if response == "":
                    continue

                # Remove any carriage returns from the response
                response = response.replace('\r', '')

                # Some responses only return a period. We don't strip or checksum them.
                if response != ".":
                    response = response.lstrip(".")

                    if not validate_checksum(response):
                        raise Exception(f"Checksum failed: {response}")
                
                # Add the response to the list
                responses.append(response)

        if num_responses == 1:
            if len(responses) > 0:
                responses = responses[0]
            else:
                responses = None 

        return responses


    def send_raw(self, command):

        command = f"{command}{calculate_checksum(command)}\r\n"

        with serial.Serial(self.port, self.baud, timeout=self.timeout) as ser:
            # Send the message
            ser.write(command.encode(encoding="ascii"))


    def resp_chng_chan(self, response, channel):

        if response[0] == ".": # TODO: This should probably raise an exception thats caught later
            return channel

        elif response[0] == "p" and response[3:6] == "210":
            return response[6:-2]

        elif response[0] == "e":
            self.handle_ccdi_error(response)

        raise Exception(f"Invalid response to chang_chan: {response}")


    #TODO: Once the radio has been in CCR mode, this command seems to fail occasionally with 
    # the response e03005A3. This indicates a "TM8000 Not Ready Error" and 
    # requires removing the power to fix. Test and confirm?
    def resp_get_temp(self, response):

        temp = None
        adc = None

        for i, r in enumerate(response):

            if r[0] == "j" and r[3:6] == "047":
                if i == 0:
                    temp = r[6:8]
                elif i == 1:
                    adc = r[6:9]

            elif r == "e03005A3":
                raise Exception(f"Radio responded with command error, has it been in CCR mode? If so reboot")

            elif response[0] == "e":
                self.handle_ccdi_error(response)

            elif response[0] == "-":
                raise Exception(f"Radio is in CCR mode")

        if temp and adc:
            return temp, adc

        raise Exception(f"Invalid response to get_temp: {response}")


    def resp_get_ser(self, response):

        if response[0] == "n":

            serial = response[3:-2]
            return serial

        elif response[0] == "e":
            self.handle_ccdi_error(response)
        
        raise Exception(f"Invalid response to get_ser: {response}")


    def resp_ccdi_pulse(self, response):

        if response[0] == "n":
            return True
        elif response[0] == "-":
            return False
        elif response[0] == "e":
            self.handle_ccdi_error(response)

        raise Exception(f"Invalid response to ccdi_pulse: {response}")


    def resp_ccr_enter(self, response):

        if response == "M01R00":
            return True

        elif response[0] == "-": # If we get a negative response we're already in CCR mode
            return True

        elif response[0] == "e":
            self.handle_ccdi_error(response)
        
        raise Exception(f"Invalid response to enter_ccr: {response}")


    def resp_ccr_ack(self, response):

        # CCR Positive Response
        if response[0] == "+":
            return True

        # CCR Negative Response
        elif response[0] == "-":
            self.handle_ccr_error(response)

        else:
            raise Exception(f"Response not implemented: {response}")


    def resp_ccr_pulse(self, response):

        if response == "Q01D0A":
            return True
        else:
            return False


    def handle_error(self, response):

        print(f"HANDLE ERROR: {response}")

        if response[0] == "e":
            self.handle_ccdi_error(response)
        elif response[0] == "-":
            self.handle_ccr_error(response)
        else:
            return True


    def handle_ccr_error(self, response):

        if response[3:5] == "01":
            raise Exception ("Invalid command")

        elif response[3:5] == "02":
            raise Exception ("Checksum Error")

        elif response[3:5] == "03":
            raise Exception ("Parameter Error")

        elif response[3:5] == "05":
            raise Exception ("Radio Busy")

        elif response[3:5] == "06":
            raise Exception ("Command Error")

        else:
            raise Exception(f"Undefined CCR Error: {response}")


    def handle_ccdi_error(self, response):

        if response[4:5] == "1":
            raise Exception(f"System Error: {response}")

        elif response[3:4] == "0":

            if response[4:6] == "01":
                raise Exception (f"Unsupported: {response}")

            if response[4:6] == "02":
                raise Exception (f"Checksum Error: {response}")

            if response[4:6] == "03":
                raise Exception (f"Parameter Error: {response}")

            if response[4:6] == "04":
                raise Exception (f"Not Ready: {response}")

            if response[4:6] == "05":
                raise Exception (f"Command Error: {response}")
        else:
            raise Exception(f"Undefined CCDI Error: {response}")

