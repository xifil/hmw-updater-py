<!-- markdownlint-disable-file MD001 MD033 -->
<h1 align="center"><a href="https://github.com/xifil">xifil</a>/<a href="https://github.com/xifil/hmw-updater-py">hmw-updater-py</a></h1>
<p align="center">the better one 🗣💯</p>

This is a single Python script that will update [HorizonMW](https://github.com/HorizonMW/HorizonMW-Client) - similar to its official launcher. This was created as a friend had problems with the launcher, and overall the launcher was unintuitive and slow in its verification method. This Python script aims for speed above all, caching file hashes automatically removing the requirement to verify every game file on every update/run. This script also natively supports Linux, offering to download [the Linux compatible HorizonMW-Client](https://github.com/MichaelDeets/HorizonMW-Client) if a Wine/non-Windows environment is detected.

## How to 🏃‍♂️🏃‍♂️🏃‍♂️
1. Install any version of [Python 3](https://python.org/downloads/) (make sure to add it to PATH)
2. Download [`hmw-updater.py`](https://) and place it in your **Call of Duty: Modern Warfare Remastered** directory
3. Run `py hmw-updater.py` in your game directory
4. Profit

## Missing features/TODO
- CDN switcher: Currently only uses Amsterdam CDN
- Saved settings
- Changelog
