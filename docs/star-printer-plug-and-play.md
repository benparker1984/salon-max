# Star TSP100 Plug-And-Play Setup

This is the deployment path for making the Star TSP100 work as a plug-and-play printer on Salon Max tills.

## Goal

Future salons should be able to:

- plug a supported Star TSP100 USB printer into the Pi
- have the printer queue appear automatically
- print receipts and open the cash drawer without using Star config software

## What must be on the Pi image

One time on the base Pi image:

1. Build and install the official **Star Linux CUPS Driver** from source
2. Copy the Salon Max auto-config script into place
3. Install the udev rule
4. Reload udev rules

Once that is done, the end customer should only need to plug the printer in.

## Files

- `ops/install_star_cups_driver_from_source.sh`
- `ops/star_tsp100_autoconfigure.sh`
- `ops/99-salonmax-star-printer.rules`

## One-time install steps on the Pi image

### 1. Copy the Star driver archive onto the Pi

Example:

```bash
scp "C:\Users\benpa\Downloads\Star_CUPS_Driver-3.17.0_linux.tar.gz" benparker1984@100.71.173.23:/home/benparker1984/
```

### 2. Install build dependencies on the Pi image

```bash
sudo apt update
sudo apt install -y build-essential libcups2-dev cups
```

### 3. Build and install the Star CUPS driver from source

```bash
chmod +x /home/benparker1984/Salon-Max/ops/install_star_cups_driver_from_source.sh
/home/benparker1984/Salon-Max/ops/install_star_cups_driver_from_source.sh /home/benparker1984/Star_CUPS_Driver-3.17.0_linux.tar.gz
```

### 4. Install Salon Max auto-config

After the Star driver is installed:

```bash
sudo chmod +x /home/benparker1984/Salon-Max/ops/star_tsp100_autoconfigure.sh
sudo cp /home/benparker1984/Salon-Max/ops/99-salonmax-star-printer.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
```

## Manual test

With the printer plugged in:

```bash
sudo /home/benparker1984/Salon-Max/ops/star_tsp100_autoconfigure.sh
```

Then check:

```bash
lpstat -v
```

The queue should appear as:

```text
star_tsp100
```

## Notes

- The build script compiles Star's source package on the Pi, which avoids the `x86_64.rpm` limitation in the downloaded archive.
- The auto-config script looks for a USB Star printer and the installed Star CUPS model.
- If the official Star driver is missing, the script exits and logs the problem.
- The current udev rule targets the tested USB device:
  - Vendor: `0519`
  - Product: `0003`

## Why this approach

This avoids requiring each customer to:

- install Star Windows software
- change printer emulation manually
- build queues by hand in CUPS

Instead, the printer behavior becomes part of the Salon Max Pi image.
