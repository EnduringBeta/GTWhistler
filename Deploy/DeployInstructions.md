GTWhistler is written to run on a Raspberry Pi 2B with Raspbian installed via NOOBS (https://www.raspberrypi.org/downloads/noobs/), though it can run on any system with internet access and the ability to execute Python code.

The `gtwhistler.service` file assumes the program is placed in the `pi` user's home directory, under `Projects`. Use `git clone [repo URL]` to get it!

Once the repository is cloned, some imports must be installed:

1. Run `sudo python3 -m pip install TwitterAPI`. (Running just `pip install TwitterAPI` might install it for an older version of Python. Running without `sudo` seems to install just for the current user `pi`, which the service doesn't run as.)
2. Run `sudo python3 -m pip install pytz`.
3. You can test the program works before trying the service steps using `python3 GTWhistler.py`. (This assumes you are in `/home/pi/Projects/GTWhistler/`.)

---

In order to make the program start automatically upon boot of the Pi, a service must be made. Many options exist for starting a program on power-up, but using `systemd` gives one additional advantage: if ever the process stops executing, it will be restarted. If GTWhistler.py completes execution, which should only happen if an error in the main loop occurs, it will eventually start up again without needing to interface with the Pi.

The `gtwhistler.service` file holds the needed information for creating this service. Follow the below instructions to make it work:

1. Copy this file to `/lib/systemd/system/`.
2. Run `sudo systemctl daemon-reload` to register the service.
3. Run `sudo systemctl enable gtwhistler.service` to make it run on boot.
4. Run `sudo systemctl start gtwhistler.service` to make it start immediately.
5. Debug any issues you find using `systemctl status gtwhistler` or running the program yourself with `/usr/bin/python3 /home/pi/Projects/GTWhistler/GTWhistler.py`.
6. Restart the Pi to confirm the service starts on boot with `sudo reboot`.

---

Maintenance tips:

* `journalctl -u gtwhistler` can show how the service was recently run
* Use `tail -f /home/pi/Projects/GTWhistler/GTW_log.txt` to show recent logs from the program. Use `nano` or `vi` on the file to look through it.

---

The following links were helpful in this process:

* https://www.dexterindustries.com/howto/run-a-program-on-your-raspberry-pi-at-startup/
* https://learn.sparkfun.com/tutorials/how-to-run-a-raspberry-pi-program-on-startup#method-3-systemd
* https://stackoverflow.com/questions/48195340/systemd-with-multiple-execstart
* https://wiki.debian.org/systemd/Services

