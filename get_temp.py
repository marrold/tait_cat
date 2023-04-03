import sys
import tait_cat as tait

if __name__ == "__main__":
    if len(sys.argv) > 1:
        port = sys.argv[1]
        radio = tait.Radio(port)
        
        # Get temperature
        temp, adc = radio.get_temp()
        print(f"Temp: {temp} ADC: {adc}")

    else:
        print("Please provide a port")