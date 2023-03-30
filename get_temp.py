import sys
import tait_cat as tait

if __name__ == "__main__":
    if len(sys.argv) > 1:
        port = sys.argv[1]
        radio = tait.Radio(port)
        
        # Get temperature
        print(f"Temp: {radio.get_temp()}")

    else:
        print("Please provide a port")