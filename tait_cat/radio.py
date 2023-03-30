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

        if response.channel != channel:
            raise Exception("Wrong Channel")

        return True

    def get_temp(self):

        command = "q0450475B\r\n"

        response = self.send_command(command)

        temperature = response.temperature

        return temperature        

    def send_command(self, command):

        with serial.Serial(self.port, self.baud, timeout=self.timeout) as ser:
            # Send the message
            ser.write(command.encode(encoding="ascii"))
            # Read the reply

            try:
                response = Response(ser.read_until().decode(encoding="ascii"))
            except Exception:
                raise

        return response
            

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
                self.function = "Unknown"

        elif self.type_char == "j":

            if self.response[3:6] == "047":
                self.temperature = self.response[6:8]

        else:
            raise Exception(f"Progress response not implemented: {self.response}")
