
# Hover Mouse: The Final Master Checklist

This is the definitive guide to running **Hover Mouse** on a Raspberry Pi 3/4. Follow these steps exactly.

## Phase 1: The "Factory Reset" (Do this first if things are broken)
If you have been tinkering and things aren't working, start clean.

1.  **Stop any running snippets**: Ctrl+C on your Pi terminal.
2.  **Forget on Mac**: Go to Mac Settings -> Bluetooth -> Right Click "Hover Mouse" -> Forget.
3.  **Reset Pi Bluetooth**:
    ```bash
    sudo systemctl restart bluetooth
    sudo bluetoothctl power off
    sudo bluetoothctl power on
    ```

## Phase 2: Configuration Check
Verify these files are correct on your Pi.

1.  **Bluetooth Config** (`/etc/bluetooth/main.conf`):
    - Run: `sudo nano /etc/bluetooth/main.conf`
    - Check: `Class = 0x0005C0` (Uncommented!)
    - Check: `Name = Hover Mouse` (Optional, but good)

2.  **Service Config** (`/lib/systemd/system/bluetooth.service`):
    - Run: `sudo nano /lib/systemd/system/bluetooth.service`
    - Check: `ExecStart=/usr/libexec/bluetooth/bluetoothd -C`
    - (The `-C` is mandatory for our code to register itself).
    - If you changed this, run: `sudo systemctl daemon-reload` and `sudo systemctl restart bluetooth`.

3.  **Code Update**:
    - Ensure you have the latest `backend/utils/bt_service.py` (It must use PSM 19 for Interrupt).
    - Ensure you have `backend/input/hid_controller.py`.

## Phase 3: The Launch Sequence
Run these commands in order every time you want to start.

1.  **Open Terminal**:
2.  **Activate Environment** (If using MiniForge):
    ```bash
    source ~/.bashrc
    mamba activate hover
    ```
    *(Prompt should show `(hover)`)*.

3.  **Navigate**:
    ```bash
    cd ~/shehacks10/backend
    ```

4.  **Launch**:
    ```bash
    sudo /home/shehacks10/miniforge3/envs/hover/bin/python main.py --hid
    ```
    *(Replace path with your actual python path if different, find it with `which python`)*.

## Phase 4: The Connection Handshake
1.  **Wait** for the Pi to print:
    ```
    Registering HID Profile via DBus...
    HID Profile Registered.
    HIDController: Waiting for Bluetooth connection on (L2CAP 17/19)...
    ```

2.  **Go to your Mac**:
    - Open Bluetooth Settings.
    - If "Hover Mouse" is there but "Not Connected", click **Connect**.
    - If it's not there, wait for it to appear (make sure Pi is discoverable using `sudo bluetoothctl discoverable on` in another tab if needed, but the script usually handles existing pairings).

3.  **Success Indicator**:
    - Pi prints: `HIDController: Control connection from ...`
    - Pi prints: `HIDController: Interrupt connection from ...`

4.  **Action**:
    - Move your hand in front of the camera.
    - Cursor moves on Mac!
    - "Picture Frame" gesture (two hands) triggers Screenshot.
