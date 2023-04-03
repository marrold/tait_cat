import sys
import tait_cat as tait
import time

if __name__ == "__main__":
    if len(sys.argv) > 1:
        port = sys.argv[1]
        radio = tait.Radio(port)

        if radio.query_mode() == "CCR":
            radio.ccr_exit()

        temp, adc = radio.get_temp()
        print(f"Temp: {temp} ADC: {adc}")

        print(f"Serial: {radio.get_ser()}")

        print(f"Mode: {radio.query_mode()}")

        print("Entering CCR")
        radio.ccr_enter()

        print(f"Mode: {radio.query_mode()}")

        print("Set Rx")
        radio.ccr_rx("144500000")

        print("Set Tx")
        radio.ccr_tx("144500000")

        print("Set Power")
        radio.ccr_pwr("1")

        print("Exiting CCR")
        radio.ccr_exit()

        time.sleep(2)

        # print(f"CCR Pulse: {radio.ccr_pulse()}")


        # print("Entering CCR")
        # radio.ccr_enter()

        # time.sleep(1)


        # print(f"CCDI Pulse: {radio.ccdi_pulse()}")


        # # print("Entering CCR")
        # # radio.ccr_enter()

        # time.sleep(1)

        # print(f"CCR Pulse: {radio.ccr_pulse()}")

        # print("Set Rx")
        # print(radio.ccr_rx("144500000"))

        # time.sleep(1)

        # print("Set Tx")
        # print(radio.ccr_tx("144500000"))

        # time.sleep(1)

        # print("Set Tx")
        # print(radio.ccr_tx("144500000"))

        # time.sleep(1)

        # print("Set Power")
        # print(radio.ccr_pwr("1"))

    else:
        print("Please provide a port.")

