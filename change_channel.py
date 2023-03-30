import sys
import serial
import tait_cat as tait


if __name__ == "__main__":
    if len(sys.argv) > 2:
        port = sys.argv[1]
        channel = sys.argv[2]
        radio = tait.Radio(port)

        # Change Channel
        if radio.chng_chan(channel):
            print(f"Changed to channel {channel}")

    else:
        print("Please provide a port and channel arguments.")

