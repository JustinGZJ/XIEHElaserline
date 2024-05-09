import pyvisa as visa
import logging
import requests
import time
import logger as logging


def switch_channel(channel=1, resource='TCPIP::192.168.48.147::INSTR'):
    rm = visa.ResourceManager()
    try:
        instrument = rm.open_resource(resource)
        commands = []

        if channel == 1:
            commands = [
                'ROUTE:CLOSE (@F01A11(0101))',
                'ROUTE:CLOSE (@F01A11(0102))',
                'ROUTE:CLOSE (@F01A12(0001))',
                'ROUTE:CLOSE (@F01A12(0002))',
                'ROUTE:CLOSE (@F01A13(0101))',
                'ROUTE:CLOSE (@F01A13(0102))'
            ]
        elif channel == 2:
            commands = [
                'ROUTE:CLOSE (@F01A11(0001))',
                'ROUTE:CLOSE (@F01A11(0002))',
                'ROUTE:CLOSE (@F01A12(0101))',
                'ROUTE:CLOSE (@F01A12(0102))',
                'ROUTE:CLOSE (@F01A13(0201))',
                'ROUTE:CLOSE (@F01A13(0202))'
            ]
        
        # Send commands one by one
        for cmd in commands:
            instrument.write(cmd)
            # Optionally add a delay or read back responses where necessary
            # response = instrument.read()  # if feedback is needed
            # print(response)

    except visa.VisaIOError as e:
        print(f"Error communicating with the device: {e}")
    finally:
        # Ensures that the connection is closed even if an error occurs
        if 'instrument' in locals():
            instrument.close()
    
    