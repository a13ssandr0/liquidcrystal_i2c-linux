# LiquidCrystal_I2C-linux
This repository is a python port of the Arduino [LiquidCrystal_I2C](https://gitlab.informatika.org/IF3111-2017-K01-01/arduino/-/tree/e226a48d5cb3735b7fa6f08e3169188495677fe6/Arduino-LiquidCrystal-I2C-library-master) library.

With this library you can connect your I2C lcd to your linux box (using available GPIOs, but also via the I2C pins of your [VGA port](https://dave.cheney.net/tag/hd44780)) and control it like you did with the C++ library.

# Table of Contents
1. [Supported devices](#supported-devices)
2. [Installation](#Installation)
3. [Implementation](#Implementation)
   - [Systemd](#systemd)
4. [Contributions](#contributions)
5. [Thanks](#thanks)

# Supported devices
  This library by default will handle most common type of character lcds based on the Hitachi HD44780 with PCF8574 I2C backpack:

  40x2, 20x4, 20x2, 16x2, 16x1 (type 2), 16x4

  displays not supported by this:
  - 16x1 (type 1), This uses a discontigous memory for the single line
    (It's not particularly difficult to make it work, but you have to use it as an 8x2 display)
  - 40x4 is dual 40x2 displays using dual E signals which is not supported

  See here for further explanation of lcd memory addressing:
  http://web.alfredstate.edu/weimandn/lcd/lcd_addressing/lcd_addressing_index.html


# Installation
0. Use `raspi-config` to enable the I2C interface (only for Raspberry Pi and similar boards)

1. Enable i2c kernel module
  ```sh
  sudo modprobe i2c-dev
  ```

2. Add your user to i2c group
  ```sh
  sudo usermod -a -G i2c $(whoami)
  ```
  To apply group change, depending on the case, you may need to:
  - Close and reopen your terminal window (if you are in a desktop environment)
  - Log-out and log-in again in your tty session (if you use a computer without a desktop environment)
  - Restart your ssh session (if you are connected to a remote device, maybe a Raspberry)

3. List all available I2C buses
  ```sh
  ls /dev/i2c-*
  ```

4. Scan for devices on the first bus
  ```sh
  i2cdetect -y 0
  ```

5. Connect your device

6. Scan again the same bus and look for new devices. If you see a new device you're done, otherwise repeat from step 4, scanning the other available buses until you find your device. (each bus corresponds to a physical connection so, if you change the device, you don't need to scan all the buses)<br>If you still can't find it try checking the cables and trying again.

7. Installing the library
  ```sh
  python3 -m pip install liquidcrystal_i2c-linux
  ```

<!--8. Start trying one of the [**demos**](#demos)-->

# Documentation
- Initialization


## Systemd
Use the following procedure to run any LCD Python script as a (systemd) service:

1. Create a new unit file in `/lib/systemd/system/` called `i2c-lcd.service`:
   ```sh
   sudo nano /lib/systemd/system/i2c-lcd.service
   ```

2. Copy and paste the following in the new unit file:
   ```sh
   [Unit]
   Description=Python script for an hd44780 LCD

   [Service]
   Type=simple
   ## Edit the following according to the script permissions
   User=<YOUR-USERNAME>
   #Group=users

   ## Edit the following with the full path to your script
   ExecStart=/usr/bin/python /path/to/script.py

   Restart=always
   RestartSec=5

   KillMode=process
   KillSignal=SIGINT

   [Install]
   WantedBy=multi-user.target
   ```

3. Enable the service and start it:
   ```sh
   sudo systemctl enable i2c-lcd.service
   sudo systemctl start i2c-lcd.service
   ```

4. Check that the LCD is displaying the correct information; otherwise, check the service status:
   ```sh
   systemctl status i2c-lcd.service
   ```

# Thanks
I'd like to thank the creators of the C++ library for their awesome work, and [The Raspberry Pi guy](https://github.com/the-raspberry-pi-guy) for the `print_ext` function, derived from his `lcd_display_extended_string`.
