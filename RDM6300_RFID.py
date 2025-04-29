# MIT License

# Copyright(c) 2021 Jaimyn Mayer

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files(the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and / or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import machine
import ubinascii


class Rdm6300:
    uart = None

    def __init__(self, tx, rx, uart_nr=1):
        """[Initialise the UART driver]
        Args:
            uart (UART): The UART object to use.
        """
        self.uart = machine.UART(
            uart_nr, baudrate=9600, timeout=2, timeout_char=10, tx=tx, rx=rx)
        self.uart.init(9600)
        
        # sometimes there's unwanted data in the buffer when we boot up
        # read it until it's all gone
        while self.uart.any():
            self.uart.read()

    def _parse_packet(self, packet):
        """Attempts to parse a packet from the RFID chip.

        Args:
            packet (bytes): The packet to try and parse.
        """
        card_data = packet[1:11]  # raw bytes of the card data
        calculated_checksum = 0  # holds the checksum we calculate from the card id

        # loop through each byte in the card data and calculate the checksum by XORing them all
        for x in ubinascii.unhexlify(card_data):
            calculated_checksum = calculated_checksum ^ x

        # if we get to here it means we received a valid packet, hurray!
        # lets remove the first byte (not part of the card ID) and convert it to a string
        card_id = card_data[2:].decode('ascii')

        # return a string of the decimal (integer) representation
        try:
            return str(int(card_id, 16))
        except:
            return str(int(card_id))

    def read_card(self):
        """Attempts to read a card from the RDM6300 reader.

        Returns:
            string: A string of the card ID as a decimal (normally the value printed on the card)
        """
        # if we have data waiting for us
        if self.uart.any():
            data = self.uart.read()
            if data:
                return self._parse_packet(data)

            return None
