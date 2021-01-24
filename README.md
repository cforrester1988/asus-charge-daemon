# asus-charge-daemon

> A daemon exposing D-Bus services for managing the charge level of recent
ASUS notebooks.

Recent ASUS notebooks come with a Windows application to set the maximum battery
charge level, in order to reduce stress on the battery and prolong its lifespan. On
Linux kernels >= version 5.4, the ```asus_nb_wmi``` kernel module exposes a sysfs object to manage this setting.

```asus-charge-daemon``` is a system service that runs in the background, exposing a D-Bus interface on the System Bus, enabling userspace applications to manage the maximum battery charge level.

## Installation

asus-charge-daemon should work with any device running a recent kernel (>= 5.4) with the ```asus_nb_wmi``` module loaded. Use ```lsmod | grep asus_nb_wmi``` to check; if you see a line like ```asus_nb_wmi            32768  0```, then the module is running.

It has been tested with the following ASUS notebooks:

- ASUS VivoBook 15 **X512DA**

A Python version >= 3.7 is necessary to run this daemon. Most Linux distributions come with the right version. To verify that Python is installed on **Debian**/**Ubuntu**-based distributions, use ```apt```:

```console
sudo apt install python3
```

On **Arch**-based distributions, use ```pacman```:

```console
sudo pacman -Syu python
```

On **RHEL/Fedora**-based distributions, use ```rpm```:

```console
sudo rpm -i python3
```

### Manual

A **very** rudimentary installation script is included for easy installation. It will copy the files to the appropriate places, install the Python modules, and run the system service.

Download and run the installation script:

```console
curl https://raw.githubusercontent.com/cforrester1988/asus-charge-daemon/main/install.py -o install.py
chmod +x install.py
sudo ./install.py install
```

To update, run the installation script again, as above. To uninstall:

```console
sudo ./install.py uninstall
```

#### git version

Clone the git repository locally:

```console
$ git clone https://github.com/cforrester1988/asus-charge-daemon.git
Cloning into 'asus-charge-daemon'...
```

Navigate to the directory you cloned the repository into, and run the installation script. Append ```local``` to work with the cloned package, instead of downloading it from PyPA.

```console
cd asus-charge-daemon
sudo ./install.py install local
```

To update, pull the latest changes and reinstall:

```console
git pull
sudo ./install.py reinstall local
```

To uninstall, run the installation script again:

```console
sudo ./install.py uninstall
```

## Version history

- 0.2.0 (2021-01-23)
  - Initial public release.
