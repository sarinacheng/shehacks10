#!/bin/bash

# setup_pi.sh - Setup script for Raspberry Pi 3 (64-bit) Hover Mouse

set -e

echo "[INFO] Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

echo "[INFO] Installing system dependencies for Bluetooth and OpenCV..."
sudo apt-get install -y \
    python3-dev \
    python3-pip \
    python3-venv \
    bluez \
    libbluetooth-dev \
    libglib2.0-dev \
    libgtk-3-dev \
    libdbus-1-dev \
    libgirepository1.0-dev \
    libcairo2-dev \
    pkg-config \
    libhdf5-dev \
    libhdf5-serial-dev \
    libatlas-base-dev \
    libjasper-dev \
    libqtgui4 \
    libqt4-test \
    libopencv-dev

# Configuring Bluetooth to run in compatibility mode (often needed for PyBluez/DBus interactions)
echo "[INFO] Configuring Bluetooth Daemon..."
if ! grep -q "ExecStart=/usr/lib/bluetooth/bluetoothd -C" /lib/systemd/system/bluetooth.service; then
    sudo sed -i 's|ExecStart=/usr/lib/bluetooth/bluetoothd|ExecStart=/usr/lib/bluetooth/bluetoothd -C|g' /lib/systemd/system/bluetooth.service
    sudo systemctl daemon-reload
    sudo systemctl restart bluetooth
fi

echo "[INFO] Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate

echo "[INFO] Upgrading pip..."
pip install --upgrade pip

echo "[INFO] Installing Python dependencies..."
# Special handling for Mediapipe on Pi if pre-built wheels are missing, 
# but usually 0.10.x has wheels for aarch64.
pip install -r requirements.txt

echo "[INFO] Setup Complete."
echo ""
echo "To run the application:"
echo "1. Activate venv: source venv/bin/activate"
echo "2. Run main (as root for Bluetooth Access): sudo ./venv/bin/python main.py"
