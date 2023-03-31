import serial

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
        self.timeout = 1

    def chng_chan(self, channel):

        command = f"g01{channel}"
        command = f"{command}{calculate_checksum(command)}\r\n"

        response = self.send_command(command)

        if response:
            new_chan = self.resp_chng_chan(response)
           
        if new_chan != channel:
            raise Exception("Wrong Channel")

        return channel

    def get_temp(self):

        command = "q0450475B\r\n"

        response = self.send_command(command)

        if response:
            temperature = self.resp_get_temp(response)

        return temperature

    def ccr_enter(self):

        command = "f0200D8\r\n"

        response = self.send_command(command)

        if response:
            self.resp_ccr_enter(response)

        return True

    def ccr_exit(self):

        command = "E005B\r\n"
        self.send_raw(command)

		# TODO: Exiting CCR reboots the radio, so there's no response.
		# Perhaps after issuing an exit, we should send some CCDI specific
		# to check if the radio is back in CCDI mode.


	# TODO: When the radio is in CCDI, the radio doesn't response to a pulse.
	# We should probably send some CCDI specific QUERY command to check if 
	# is in CCDI mode instead the radio
    def ccr_pulse(self):

        command = "Q01P"
        command = f"{command}{calculate_checksum(command)}\r\n"

        response = self.send_command(command)

        # A pulse has a dedicated response, so first we check the ack is valid
        # then we check the outcome of the pulse
        if response and self.resp_ccr_ack(response):

            return self.resp_ccr_pulse(response)


    def ccr_tx(self, freq):

        command = f"T09{freq}"
        command = f"{command}{calculate_checksum(command)}\r\n"

        response = self.send_command(command)

        if response:
            return self.resp_ccr_ack(response)


    def ccr_rx(self, freq):

        command = f"R09{freq}"
        command = f"{command}{calculate_checksum(command)}\r\n"

        response = self.send_command(command)

        if response:
            return self.resp_ccr_ack(response)


    def ccr_pwr(self, pwr):

        command = f"P01{pwr}"
        command = f"{command}{calculate_checksum(command)}\r\n"

        response = self.send_command(command)

        if response:
            return self.resp_ccr_ack(response)


    def send_command(self, command):

        with serial.Serial(self.port, self.baud, timeout=self.timeout) as ser:
            # Send the message
            ser.write(command.encode(encoding="ascii"))
            # Read the reply

            try:
                response = self.check_response(ser.read_until().decode(encoding="ascii"))
                return response
            except Exception:
                raise
            
            raise Exception("Validation failed")


    def send_raw(self, command):
        with serial.Serial(self.port, self.baud, timeout=self.timeout) as ser:
            # Send the message
            ser.write(command.encode(encoding="ascii"))


    def check_response(self, response):
        
        if response == ".":
            raise Exception("Already Set")

        # TODO: The response to the temp query sends two replies, one with celsius and one with millivolts.
        # For now we split any replies and just ignore the second. This works, but is a bit messy.
        response = [s.lstrip(".") if s.startswith(".") else s for s in response.split("\r")][0]

        if response == "":
            raise Exception("Timed out waiting for response")

        if not validate_checksum(response):
            raise Exception(f"Checksum failed: {response}")

        return response

    def resp_chng_chan(self, response):

        # Progress Response
        if response[0] == "p":

            if response[3:6] == "210":

                channel = response[6:-2]
                return channel

        raise Exception("Invalid response to chang_chan")


    #TODO: Once the radio has been in CCR mode, this command seems to fail with 
	# the response e03005A3. This indicates a "TM8000 Not Ready Error" and 
	# requires removing the power to fix. Test and confirm?
    def resp_get_temp(self, response):

        if response[0] == "j":

            if response[3:6] == "047":
                temperature = response[6:8]
                return temperature
        
        raise Exception(f"Invalid response to get_temp: {response}")


    def resp_ccr_enter(self, response):

        if response == "M01R00":
            return True
        
        raise Exception("Invalid response to enter_ccr")


    def resp_ccr_ack(self, response):

        # CCR Positive Response
        if response[0] == "+":
            return True

        # CCR Negative Response
        elif response[0] == "-":

            if response[3:5] == "01":
                raise Exception ("Invalid command")

            if response[3:5] == "02":
                raise Exception ("Checksum Error")

            if response[3:5] == "03":
                raise Exception ("Parameter Error")

            if response[3:5] == "05":
                raise Exception ("Radio Busy")

            if response[3:5] == "06":
                raise Exception ("Command Error")
        
        # CCR Pulse Response
        elif response[0] == "Q":
            return True

        else:
            raise Exception(f"Response not implemented: {response}")


    def resp_ccr_pulse(self, response):

        if response == "Q01D0A":
            return True
        else:
            return False 


class Response:
    def __init__(self, response):

        self.response = response
        
        if self.response == ".":
            raise Exception("Already Set")

        self.response = response.replace('.', '').replace('\r', '')

        if self.response == "":
            raise Exception("Timed out waiting for response")

        # TODO: The response to the temp query sends two replies, one with celsius and one with millivolts.
        # For now we split any replies and just ignore the second. This works, but is a bit messy.
        self.response = [s.lstrip(".") if s.startswith(".") else s for s in response.split("\r")][0]

        if not validate_checksum(self.response):
            raise Exception(f"Checksum failed: {self.response}")

        if self.response == "M01R00":
            self.ccr_mode = True

        self.type_char = self.response[0]

        # Error Response
        if self.type_char == "e":

            if self.response[4:5] == "1":
                raise Exception("System Error")

            elif self.response[3:4] == "0":

                if self.response[4:6] == "01":
                    raise Exception ("Unsupported")

                if self.response[4:6] == "02":
                    raise Exception ("Checksum Error")

                if self.response[4:6] == "03":
                    raise Exception ("Parameter Error")

                if self.response[4:6] == "04":
                    raise Exception ("Not Ready")

                if self.response[4:6] == "05":
                    raise Exception ("Command Error")
            else:
                raise Exception(f"Undefined Error: {self.response}")

        # Progress Response
        if self.type_char == "p":

            if self.response[3:6] == "210":

                self.function = "User Initiated Channel Change"
                self.change_type = "Single Channel"
                self.channel = self.response[6:-2]

            else:
                raise Exception(f"Progress response not implemented: {self.response}")

        # Temperature Response
        elif self.type_char == "j":

            if self.response[3:6] == "047":
                self.temperature = self.response[6:8]

        # CCR Positive Response
        elif self.type_char == "+":
            self.ccr_ack = True

        # CCR Negative Response
        elif self.type_char == "-":

            if self.response[3:5] == "01":
                raise Exception ("Invalid command")

            if self.response[3:5] == "02":
                raise Exception ("Checksum Error")

            if self.response[3:5] == "03":
                raise Exception ("Parameter Error")

            if self.response[3:5] == "05":
                raise Exception ("Radio Busy")

            if self.response[3:5] == "06":
                raise Exception ("Command Error")

        else:
            raise Exception(f"Response not implemented: {self.response}")
