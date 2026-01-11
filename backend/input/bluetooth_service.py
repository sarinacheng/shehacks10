
import os
import sys
import time
import socket
import logging
import dbus
import dbus.service
import dbus.mainloop.glib
from gi.repository import GLib

logger = logging.getLogger(__name__)

# Constants
P_CTRL = 17  # HID Control PSM
P_INTR = 19  # HID Interrupt PSM

# HID Report Descriptor
# This descriptor defines a device that acts as both a Mouse and a Keyboard.
# It is critical this byte array is correct for the host to accept input.
HID_REPORT_DESCRIPTOR = [
    0x05, 0x01,  # Usage Page (Generic Desktop)
    0x09, 0x02,  # Usage (Mouse)
    0xa1, 0x01,  # Collection (Application)
    0x85, 0x01,  #   Report ID (1)
    0x09, 0x01,  #   Usage (Pointer)
    0xa1, 0x00,  #   Collection (Physical)
    0x05, 0x09,  #     Usage Page (Button)
    0x19, 0x01,  #     Usage Minimum (1)
    0x29, 0x03,  #     Usage Maximum (3)
    0x15, 0x00,  #     Logical Minimum (0)
    0x25, 0x01,  #     Logical Maximum (1)
    0x95, 0x03,  #     Report Count (3)
    0x75, 0x01,  #     Report Size (1)
    0x81, 0x02,  #     Input (Data, Var, Abs)
    0x95, 0x01,  #     Report Count (1)
    0x75, 0x05,  #     Report Size (5)
    0x81, 0x03,  #     Input (Cnst, Var, Abs)
    0x05, 0x01,  #     Usage Page (Generic Desktop)
    0x09, 0x30,  #     Usage (X)
    0x09, 0x31,  #     Usage (Y)
    0x09, 0x38,  #     Usage (Wheel)
    0x15, 0x81,  #     Logical Minimum (-127)
    0x25, 0x7f,  #     Logical Maximum (127)
    0x75, 0x08,  #     Report Size (8)
    0x95, 0x03,  #     Report Count (3)
    0x81, 0x06,  #     Input (Data, Var, Rel)
    0xc0,        #   End Collection
    0xc0,        # End Collection

    0x05, 0x01,  # Usage Page (Generic Desktop)
    0x09, 0x06,  # Usage (Keyboard)
    0xa1, 0x01,  # Collection (Application)
    0x85, 0x02,  #   Report ID (2)
    0x05, 0x07,  #   Usage Page (Key Codes)
    0x19, 0xe0,  #   Usage Minimum (224)
    0x29, 0xe7,  #   Usage Maximum (231)
    0x15, 0x00,  #   Logical Minimum (0)
    0x25, 0x01,  #   Logical Maximum (1)
    0x75, 0x01,  #   Report Size (1)
    0x95, 0x08,  #   Report Count (8)
    0x81, 0x02,  #   Input (Data, Variable, Absolute)
    0x95, 0x01,  #   Report Count (1)
    0x75, 0x08,  #   Report Size (8)
    0x81, 0x01,  #   Input (Constant) reserved byte(1)
    0x95, 0x05,  #   Report Count (5)
    0x75, 0x01,  #   Report Size (1)
    0x05, 0x08,  #   Usage Page (LEDs)
    0x19, 0x01,  #   Usage Minimum (1)
    0x29, 0x05,  #   Usage Maximum (5)
    0x91, 0x02,  #   Output (Data, Variable, Absolute)
    0x95, 0x01,  #   Report Count (1)
    0x75, 0x03,  #   Report Size (3)
    0x91, 0x01,  #   Output (Constant)
    0x95, 0x06,  #   Report Count (6)
    0x75, 0x08,  #   Report Size (8)
    0x15, 0x00,  #   Logical Minimum (0)
    0x25, 0x65,  #   Logical Maximum (101)
    0x05, 0x07,  #   Usage Page (Key Codes)
    0x19, 0x00,  #   Usage Minimum (0)
    0x29, 0x65,  #   Usage Maximum (101)
    0x81, 0x00,  #   Input (Data, Array)
    0xc0         # End Collection
]

class BluetoothHIDProfile(dbus.service.Object):
    def __init__(self, bus, path):
        super().__init__(bus, path)
        self.fd = -1

    @dbus.service.method("org.bluez.Profile1", in_signature="", out_signature="")
    def Release(self):
        print("Release")

    @dbus.service.method("org.bluez.Profile1", in_signature="", out_signature="")
    def Cancel(self):
        print("Cancel")

    @dbus.service.method("org.bluez.Profile1", in_signature="jha{sv}", out_signature="")
    def NewConnection(self, path, fd, properties):
        self.fd = fd.take()
        print(f"NewConnection({path}, {self.fd})")
        
    @dbus.service.method("org.bluez.Profile1", in_signature="o", out_signature="")
    def RequestDisconnection(self, path):
        print(f"RequestDisconnection({path})")


class BluetoothService:
    def __init__(self):
        self.scontrol = None
        self.sinterrupt = None
        self.bus = None
        self.profile = None

    def setup(self):
        print("Setting up Bluetooth Service...")
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.bus = dbus.SystemBus()
        
        # Define Service Record
        service_record = self._create_service_record()
        
        # Configure Profile
        opts = {
            "ServiceRecord": service_record,
            "Role": "server",
            "RequireAuthentication": False,  # Changed to False for easier pairing
            "RequireAuthorization": False
        }

        manager = dbus.Interface(self.bus.get_object("org.bluez", "/org/bluez"), "org.bluez.ProfileManager1")
        
        self.profile = BluetoothHIDProfile(self.bus, "/org/bluez/bthid_profile")
        manager.RegisterProfile("/org/bluez/bthid_profile", "00001124-0000-1000-8000-00805f9b34fb", opts)
        print("Bluetooth Profile Registered")

        # Create sockets
        self.scontrol = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_SEQPACKET, socket.BTPROTO_L2CAP)
        self.sinterrupt = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_SEQPACKET, socket.BTPROTO_L2CAP)
        
        self.scontrol.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sinterrupt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Bind sockets to port (PSM)
        # Note: Address must be BDADDR_ANY usually
        self.scontrol.bind((socket.BDADDR_ANY, P_CTRL))
        self.sinterrupt.bind((socket.BDADDR_ANY, P_INTR))

        self.scontrol.listen(1)
        self.sinterrupt.listen(1)
        print("Waiting for Bluetooth connections...")

    def accept_connection(self):
        try:
            ccontrol, cinfo = self.scontrol.accept()
            print(f"Control channel connected from {cinfo}")
            
            cinterrupt, cinfo = self.sinterrupt.accept()
            print(f"Interrupt channel connected from {cinfo}")
            
            return ccontrol, cinterrupt
        except Exception as e:
            print(f"Error accepting connection: {e}")
            return None, None

    def _create_service_record(self):
        # We construct the SDP record XML here. This is standard for BlueZ HID.
        # It's verbose but necessary.
        
        xml = """
        <record>
            <attribute id="0x0001">
                <sequence>
                    <uuid value="0x1124"/>
                </sequence>
            </attribute>
            <attribute id="0x0004">
                <sequence>
                    <sequence>
                        <uuid value="0x0100"/>
                        <uint16 value="0x0100"/>
                    </sequence>
                    <sequence>
                        <uuid value="0x0011"/>
                    </sequence>
                    <sequence>
                        <uuid value="0x0017"/>
                    </sequence>
                </sequence>
            </attribute>
            <attribute id="0x0005">
                <sequence>
                    <uuid value="0x1002"/>
                </sequence>
            </attribute>
            <attribute id="0x0006">
                <sequence>
                    <uint16 value="0x656e"/>
                    <uint16 value="0x006a"/>
                    <uint16 value="0x0100"/>
                </sequence>
            </attribute>
            <attribute id="0x000d">
                <sequence>
                    <sequence>
                        <sequence>
                            <uint16 value="0x0100"/>
                            <uint16 value="0x0011"/>
                        </sequence>
                        <sequence>
                            <uint16 value="0x0011"/>
                        </sequence>
                    </sequence>
                </sequence>
            </attribute>
            <attribute id="0x0100">
                <text value="Hover Mouse"/>
            </attribute>
            <attribute id="0x0101">
                <text value="Hover Mouse Bluetooth"/>
            </attribute>
            <attribute id="0x0201">
                <uint16 value="0x0100"/>
            </attribute>
            <attribute id="0x0202">
                <uint8 value="0x80"/>
            </attribute>
            <attribute id="0x0204">
                <boolean value="true"/>
            </attribute>
            <attribute id="0x0205">
                <boolean value="true"/>
            </attribute>
            <attribute id="0x0206">
                <sequence>
                    <sequence>
                        <uint8 value="0x22"/>
                        <text value="Report Descriptor"/>
                    </sequence>
                </sequence>
            </attribute>
            <attribute id="0x0207">
                <sequence>
                    <sequence>
                        <uint8 value="0x22"/>
                        <text value="Report Descriptor"/>
                    </sequence>
                </sequence>
            </attribute>
            <attribute id="0x020b">
                <uint16 value="0x0100"/>
            </attribute>
            <attribute id="0x020c">
                <uint16 value="0x0c80"/>
            </attribute>
            <attribute id="0x020d">
                <boolean value="false"/>
            </attribute>
            <attribute id="0x020e">
                <boolean value="true"/>
            </attribute>
            <attribute id="0x020f">
                <uint16 value="0x0032"/>
            </attribute>
            <attribute id="0x0210">
                <uint16 value="0x0200"/>
            </attribute>
            <attribute id="0x0211">
                <uint16 value="0x1234"/>
            </attribute>
            <attribute id="0x0212">
                <uint16 value="0x0001"/>
            </attribute>
            <attribute id="0x0213">
                <uint16 value="0x0001"/>
            </attribute>
        </record>
        """
        # Inject the HID Report Descriptor into the XML
        # The descriptor needs to be converted to a hex string sequence
        desc_str = ""
        for b in HID_REPORT_DESCRIPTOR:
            desc_str += f"{b:02x} "
        desc_str = desc_str.strip().upper()
        
        # We simply return the XML. In a robust impl we might parse the descriptor into the XML more dynamically,
        # but hardcoding the structure for HID is standard.
        # IMPORTANT: BlueZ `ServiceRecord` expects a String, and we usually don't need to manually inject the hex bytes 
        # inside the XML if we use the right UUIDs, BUT, the HID descriptor is typically attribute 0x0206.
        # Let's use a simpler known-working SDP record template for HID.
        
        return self._get_sdp_record_xml(desc_str)

    def _get_sdp_record_xml(self, hid_descriptor_hex_spaced):
        # Clean up the hex string for the XML value
        val = "".join(hid_descriptor_hex_spaced.split())
        
        return f"""
<?xml version="1.0" encoding="UTF-8" ?>
<record>
  <attribute id="0x0001">
    <sequence>
      <uuid value="0x1124" />
    </sequence>
  </attribute>
  <attribute id="0x0004">
    <sequence>
      <sequence>
        <uuid value="0x0100" />
        <uint16 value="0x0100" />
      </sequence>
      <sequence>
        <uuid value="0x0011" />
      </sequence>
      <sequence>
        <uuid value="0x0017" />
      </sequence>
    </sequence>
  </attribute>
  <attribute id="0x0005">
    <sequence>
      <uuid value="0x1002" />
    </sequence>
  </attribute>
  <attribute id="0x0006">
    <sequence>
      <uint16 value="0x656e" />
      <uint16 value="0x006a" />
      <uint16 value="0x0100" />
    </sequence>
  </attribute>
  <attribute id="0x000d">
    <sequence>
      <sequence>
        <sequence>
          <uint16 value="0x0100" />
          <uint16 value="0x0011" />
        </sequence>
        <sequence>
          <uint16 value="0x0011" />
        </sequence>
      </sequence>
    </sequence>
  </attribute>
  <attribute id="0x0100">
    <text value="Hover Mouse" />
  </attribute>
  <attribute id="0x0101">
    <text value="Hover Mouse Device" />
  </attribute>
  <attribute id="0x0200">
    <uint16 value="0x0100" />
  </attribute>
  <attribute id="0x0201">
    <uint16 value="0x0111" />
  </attribute>
  <attribute id="0x0202">
    <uint8 value="0x80" />
  </attribute>
  <attribute id="0x0203">
    <uint8 value="0x00" />
  </attribute>
  <attribute id="0x0204">
    <boolean value="true" />
  </attribute>
  <attribute id="0x0205">
    <boolean value="true" />
  </attribute>
  <attribute id="0x0206">
    <sequence>
      <sequence>
        <uint8 value="0x22" />
        <text encoding="hex" value="{val}" />
      </sequence>
    </sequence>
  </attribute>
  <attribute id="0x0207">
    <sequence>
      <sequence>
        <uint16 value="0x0100" />
        <uint16 value="0x0001" />
      </sequence>
    </sequence>
  </attribute>
</record>
"""
