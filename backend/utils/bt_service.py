
import os
# Force DBus to look at the system socket, not the conda environment's imaginary one
if "DBUS_SYSTEM_BUS_ADDRESS" not in os.environ:
    os.environ["DBUS_SYSTEM_BUS_ADDRESS"] = "unix:path=/var/run/dbus/system_bus_socket"

import dbus
import dbus.service
import dbus.mainloop.glib
from gi.repository import GLib

# Standard HID SDP Record (Mouse + Keyboard)
SDP_RECORD_XML = """
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
  <attribute id="0x0009">
    <sequence>
      <sequence>
        <uuid value="0x1124" />
        <uint16 value="0x0100" />
      </sequence>
    </sequence>
  </attribute>
  <attribute id="0x000d">
    <sequence>
      <sequence>
        <sequence>
          <uuid value="0x0100" />
          <uint16 value="0x0011" />
        </sequence>
        <sequence>
          <uuid value="0x0011" />
        </sequence>
      </sequence>
    </sequence>
  </attribute>
  <attribute id="0x0100">
    <text value="Hover Mouse" />
  </attribute>
  <attribute id="0x0101">
    <text value="Raspberry Pi" />
  </attribute>
  <attribute id="0x0200">
    <uint16 value="0x0100" />
  </attribute>
  <attribute id="0x0201">
    <uint16 value="0x0111" />
  </attribute>
  <attribute id="0x0207">
    <sequence>
      <sequence>
        <uint16 value="0x0409" />
        <uint16 value="0x0100" />
      </sequence>
    </sequence>
  </attribute>
  <attribute id="0x0217">
    <uint16 value="0x0000" />
  </attribute>
</record>
"""

class BluetoothService(dbus.service.Object):
    def __init__(self):
        bus_name = dbus.service.BusName("org.bluez", bus=dbus.SystemBus())
        dbus.service.Object.__init__(self, bus_name, "/org/bluez/example/service")

class Profile(dbus.service.Object):
    fd = -1

    def __init__(self, bus, path):
        dbus.service.Object.__init__(self, bus, path)

    @dbus.service.method("org.bluez.Profile1", in_signature="", out_signature="")
    def Release(self):
        print("Release")
        pass # Loop.quit()

    @dbus.service.method("org.bluez.Profile1", in_signature="", out_signature="")
    def Cancel(self):
        print("Cancel")

    @dbus.service.method("org.bluez.Profile1", in_signature="oha{sv}", out_signature="")
    def NewConnection(self, path, fd, properties):
        self.fd = fd.take()
        print("NewConnection(%s, %d)" % (path, self.fd))

    @dbus.service.method("org.bluez.Profile1", in_signature="o", out_signature="")
    def RequestDisconnection(self, path):
        print("RequestDisconnection(%s)" % (path))

def register_hid_profile():
    print("Registering HID Profile via DBus...")
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()
    manager = dbus.Interface(bus.get_object("org.bluez", "/org/bluez"), "org.bluez.ProfileManager1")

    path = "/org/bluez/hover/hid"
    uuid = "00001124-0000-1000-8000-00805f9b34fb" # HID Service UUID
    opts = {
        "ServiceRecord": SDP_RECORD_XML,
        "Role": "server",
        "RequireAuthentication": False,
        "RequireAuthorization": False
    }

    try:
        manager.RegisterProfile(path, uuid, opts)
        print("HID Profile Registered.")
    except Exception as e:
        print(f"Failed to register HID profile: {e}")

# Note: We are not running a GLib loop here because we just want to register and let BlueZ manage connections
# We will handle the actual L2CAP connection in the main Thread or a separate socket listener.
