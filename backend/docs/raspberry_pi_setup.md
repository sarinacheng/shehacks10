# Raspberry Pi "Hover Mouse" Setup Guide

This guide explains how to turn your Raspberry Pi 3/4/Zero into a Bluetooth HID device that runs the Hover Mouse code.

## 1. Prerequisites
- Raspberry Pi running Raspberry Pi OS.
- **Internet Connection**:
  - If you get "Could not resolve host", your Pi is not connected.
  - Run `sudo raspi-config`, go to **System Options > Wireless LAN**, and enter your WiFi credentials.
  - Or connect an Ethernet cable.

## 2. Install Dependencies
Newer Raspberry Pi OS versions enforce "managed environments" (PEP 668). We should use a Virtual Environment.

### A. System Libraries
```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-opencv libopencv-dev python3-venv python3-dbus
sudo apt-get install -y python3-evdev bluez
```

### B. Clone the Repository
**Option 1: Git (Easiest)**
```bash
cd ~
git clone https://github.com/sarinacheng/shehacks10.git
cd shehacks10/backend
```

**Option 2: Copy from Laptop (If Git fails/No Internet)**
Run this **on your Laptop (Mac)**:
```bash
# Go to the folder containing your project
cd /Users/sarina/Coding/Hackathons

# ZIP the entire project
zip -r shehacks10.zip shehacks10/

# Send to Pi (replace raspberrypi.local with your Pi's IP)
scp shehacks10.zip pi@raspberrypi.local:~/

# On Pi: Unzip and enter directory
unzip shehacks10.zip
cd shehacks10/backend
```

### C. Python Libraries (Virtual Environment)
Now that we are in the project directory:
```bash
# Create venv folder
python3 -m venv venv
sudo iw dev wlan0 scan | grep -i country

# Activate it (you must do this every time you open a new terminal)
source venv/bin/activate

# Install requirements using the venv's pip explicitly
./venv/bin/pip install -r requirements.txt

# OR if that still fails:
pip install -r requirements.txt --break-system-packages
```

*Alternative (Not Recommended):* If you really want to install globally, use `pip3 install -r requirements.txt --break-system-packages`.

## 3. Configure Bluetooth HID
To make the Pi advertise itself as a Mouse/Keyboard so your Mac will accept it, we need to change its "Class of Device".

1. **Edit the Bluetooth Config**:
   ```bash
   sudo nano /etc/bluetooth/main.conf
   ```

2. **Change the `Class` setting**:
   Find the line `#Class = ...` (it might be commented out).
   Change it to:
   ```ini
   Class = 0x0005C0
   ```
   *(This code tells other devices: "I am a Peripheral with Keyboard and Mouse capabilities")*

   **Optional (Rename Device)**:
   Uncomment/Change `#Name = ...` to:
   ```ini
   Name = Hover Mouse
   ```

3. **Restart Bluetooth**:
   ```bash
   sudo systemctl restart bluetooth
   ```

4. **Make Discoverable & Pair (Headless Method)**:
   Run `sudo bluetoothctl`. You will enter a special shell `[bluetooth]#`.
   
   Enter these commands one by one:
   ```bash
   power on
   agent on
   default-agent
   discoverable on
   pairable on
   ```
   
   **Now, initiate the connection from your Mac.**
   
   When you click "Connect" on your Mac, look at your Pi terminal!
   You will see a message like: `[agent] Passkey: 123456`.
   
   Type `yes` and hit Enter to confirm the code matches.
   
   Finally, verify it is trusted:
   ```bash
   trust <MAC_ADDRESS_OF_MAC>
   exit
   ```

   **IMPORTANT: Enable Compatibility Mode**
   For the new SDP registration to work, we need to modify the bluetooth service.
   1. Edit the service file:
      ```bash
      sudo nano /lib/systemd/system/bluetooth.service
      ```
   2. Find the line starting with `ExecStart=...` and add `-C`.
      Change: `ExecStart=/usr/libexec/bluetooth/bluetoothd`
      To: `ExecStart=/usr/libexec/bluetooth/bluetoothd -C`
   3. Save and reload:
      ```bash
      sudo systemctl daemon-reload
      sudo systemctl restart bluetooth
      # You might need to make it discoverable again in bluetoothctl
      ```

   **Now, initiate the connection from your Mac.**

## 4. Camera Setup
You have two options for the camera:

### Option A: USB Webcam (Recommended)
Just plug it into a USB port. It usually appears as `/dev/video0`.
The code uses `index=0` by default, so it should work immediately.

### Option B: Raspberry Pi Camera Module (Ribbon Cable)
If you are using the official Pi Camera:
1. Ensure it is connected properly.
2. **Legacy OS (Buster)**: Enable camera in `sudo raspi-config` -> Interface Options.
3. **Newer OS (Bullseye/Bookworm)**: OpenCV might not see the camera by default because of `libcamera`.
   - **Fix**: Edit `/boot/config.txt` and change `dtoverlay=vc4-kms-v3d` to `dtoverlay=vc4-fkms-v3d` (or enable legacy camera support in `raspi-config` if available).
   - Alternatively, plug in a USB webcam to avoid driver headaches.

## 5. Running the Code
Because we need `sudo` for Bluetooth/HID, but we also need our `venv` libraries, we must point `sudo` to the venv's python directly:

```bash
# Make sure you are in the backend folder
cd ~/shehacks10/backend

# Run using the venv's python
sudo ./venv/bin/python3 main.py --hid
```
*Note: Do NOT just run `sudo python3`, as that ignores your virtual environment!*


### "PyObjC requires macOS to build"
This library is for Mac only. If it tries to install on Pi, remove it.

**Fix**: Run this command on the Pi to remove all Mac-specific lines from `requirements.txt`:
```bash
sed -i '/pyobjc/d' requirements.txt
```
Then try installing again.
This usually means `pip` cannot find a pre-built version for your specific Raspberry Pi OS version (e.g., 32-bit vs 64-bit).

**Fix**: Open `requirements.txt` and remove the version numbers.
Change:
`mediapipe==0.10.9`  -> `mediapipe`
`opencv-python==...` -> `opencv-python`

### "No matching distribution" / MediaPipe Error
**Crucial Check:** Run this command on your Pi:
```bash
uname -m
```

*   **If it says `aarch64`**: You are on **64-bit**. Good. The error is likely Python version (needs 3.7-3.11).
*   **If it says `armv7l`**: You are on **32-bit**. **MediaPipe DOES NOT support 32-bit.**
    *   **Solution**: You must reinstall "Raspberry Pi OS (64-bit)" on your SD card.
    *   *Workaround*: None easy. You can try searching for "mediapipe rpi 32bit" community builds, but it's unstable.

**If you are on `aarch64` (64-bit) and it still fails:**
1.  **Upgrade pip**: The default `pip` might be too old to see the correct wheels.
    ```bash
    ./venv/bin/pip install --upgrade pip
    ```
2.  **Check Python Version**:
    ```bash
    python3 --version
    ```
    MediaPipe supports Python 3.8 - 3.11.
    If you are on Python **3.12+** (Raspberry Pi OS Bookworm latest update), MediaPipe might not have official support yet.
    
    *Workaround for Python 3.12*: Try installing a virtual env with Python 3.11 if possible, or wait for MediaPipe update. Or try:
    ```bash
    ./venv/bin/pip install mediapipe-rpi4
    ```

### "Python version is 3.12/3.13" (MediaPipe incompatible)
MediaPipe only works on Python 3.11 or older. You need to create your virtual environment with Python 3.11.

### "Python version is 3.12/3.13" (Trixie/Latest OS)
If `apt install python3.11` fails (common on newer OS versions), use **Miniforge**. It installs a separate Python manager.

1.  **Fix Internet First**:
    If `apt update` failed with "Temporary failure resolving", edit your DNS:
    ```bash
    echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
    ```

2.  **Install Miniforge (Home Directory)**:
    ```bash
    cd ~  # Go to home folder
    
    # Download installer
    wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-aarch64.sh
    
    # Run it
    bash Miniforge3-Linux-aarch64.sh
    # (Press Enter, type 'yes', accept defaults)
    
    # Reload shell
    source ~/.bashrc
    ```

3.  **Create Python 3.11 Environment**:
    ```bash
    mamba create -n hover python=3.11 -y
    mamba activate hover
    ```

4.  **Install Requirements (Project Directory)**:
    mamba activate hover
    cd ~/shehacks10/backend
    # Install PyBluez dependencies
    sudo apt install -y libbluetooth-dev git
    # Install PyBluez from source (pip version is broken on Python 3.11+)
    pip install git+https://github.com/pybluez/pybluez.git#egg=pybluez
    
    mamba install -y dbus-python pygobject
    pip install -r requirements.txt
    ```

5.  **Run with Conda (Replaces Step 5)**:
    Do not use the `venv` command from Step 5. Use this instead:
    ```bash
    # First, find where python is installed:
    which python
    # (Example output: /home/shehacks10/miniforge3/envs/hover/bin/python)

    # Use THAT path with sudo:
    sudo /home/shehacks10/miniforge3/envs/hover/bin/python main.py --hid
    ```
3. **Fix DNS**: If connected but still failing, edit `/etc/resolv.conf` and add `nameserver 8.8.8.8`.

### "externally-managed-environment" Error
- Ensure you are using the venv: `source venv/bin/activate`.
### "Temporary failure in name resolution" (The "Nuclear" Fix)
If you keep seeing this error, your DNS or System Time is broken. Run these commands strictly in order:

1.  **Force DNS to Google (and lock it)**:
    ```bash
    echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
    sudo chattr +i /etc/resolv.conf  # Prevents OS from overwriting it
    ```

2.  **Force System Time Update**:
    (SSL fails if time is wrong. Replace with current date/time!)
    ```bash
    sudo date -s "2025-01-11 12:00:00"
    ```

3.  **Test Connection**:
    ```bash
    ping -c 3 google.com
    ```
    *Only proceed if you see "64 bytes from..."*

4.  **Retry Install**:
    ```bash
    mamba install -y pygobject
    ```

### "Dependency 'girepository-2.0' is required"
This means you are trying to build `PyGObject` from source but are missing the system headers.

1.  **Install Headers**:
    ```bash
    sudo apt install -y libcairo2-dev libgirepository1.0-dev pkg-config python3-dev
    ```

2.  **Ensure you are in the hover environment**:
    Check your prompt. It should say `(hover)`, not `(base)`.
    ```bash
    mamba activate hover
    ```

3.  **Install**:
    ```bash
    pip install PyGObject
    ```
