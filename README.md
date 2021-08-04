What is VASD ?

This package is designed for neuroscience research, but can be used in other fields.
It enables to acquire and analyse a large number of video files from IP cameras. It performs a motion analysis to ease the identification of convulsive seizures in rodent models. It goes with SASDI, a package that enables to display the results of the motion analysis (stored in csv files).

INSTALLING

Copy all VASD files in a directory called /vasd/, also copy the /params subdirectory and its content.
Install python environment (https://www.python.org/downloads/, or https://docs.anaconda.com/), recommended versions are 3.8 or 3.9.
Install some needed packages, use the command pip install -r requirements.txt from the /vasd directory.

TESTING

After installing the required packages and VASD, please launch the test script to check everything is properly installed:
  - open a terminal
  - switch to the /vasd/ directory
  - start the test by entering: python test_vasd.py
The script will perform the following tests using "unittest" standard library module:
      1) Check the presence of all required packages, BEWARE it does not check the version, in case of problem please check that the installed package version (you can use the command "pip list" from a terminal) is sufficient for VASD (indicated in requirements.txt),
      2) Check the parameters file '/vasd/params/parameters.json' can be read/write,
      3) Check the motion analysis gives the proper value on the '/vasd/params/defaultvideo.mp4' test file.

CONFIGURING

You need to manually change the default parameters in file '/vasd/params/parameters.json'.
Make sure to keep the dict structure {key1: value1, key2: value2, lastkey: lastvalue} (no quote after last value).

  - "VERSION"
  Current version of VASD, do not change, for example:
        {           (beginning of the dictionnary)
        "VERSION": "3.0",

  - "BASE_DIR"
  Path of the directory for storing data (videos and analysis files), different from the package directory, for example:
        "BASE_DIR": "/home/data/vasd_data",

  - "CAMERA_ADDRESS"
  Make sure to keep the list structure [val1, val2, lastval] (no quote after last value)
  This is the list of the rtsp commands to access the video flux of your cameras, see your camera documentation for exact syntax.
  For each camera or DVR box (Digital Video Recorder, usually one IP address for the box that is connected to many cameras identified in rtsp address, "channel=x" in the example below).
  You need to ask a fixed IP address (ex: 111.222.333.444) to your network manager and choose a login/password (can be the same for all cameras, ex: mylog / mypass), for example:
        "CAMERA_ADDRESS": [
        "rtsp://mylog:mypass@111.222.333.444:554/12",
        "rtsp://mylo:mypass@111.222.333.445/cam/realmonitor?channel=1",
        "rtsp://mylog:mypass@111.222.333.445/cam/realmonitor?channel=2",
        "rtsp://mylog:mypass@111.222.333.445/cam/realmonitor?channel=3"
        ],

  - "CAMERA_FPS"
  You can probably set the fps (frame par seconds) of your camera (see its documentation), the higher fps will produce heavier files, fps between 15 and 20 are sufficient for detecting convulsive seizures.
  When each camera is set to your need, modify fps in parameters.json to make sure the acquisition is perform with the correct fps, for example:
        "CAMERA_FPS": [
        "15",
        "20",
        "20",
        "20"
        ],

   - "AUDIO"
   This is to indicate if the camera also acquire (1) or not (0) an audio flux, for example:
        "AUDIO": [
        1,
        0,
        0,
        0
        ]
        }       (end of the dictionnary)

STARTING

To start the script, type the following command in a terminal from the vasd directory (use 'cd' to switch to sasdi directory):
    python vasd.py
OR from any directory type the full path:
    python complete/path/to/vasd/vasd.py

USER GUIDE

Run VASD and then click on the "Help" button to get detailed instructions.

IF YOU HAVE PROBLEM WITH THE SCRIPT

Fabrice DUPRAT: duprat@ipmc.cnrs.fr
For python packages installation and network setting, please see your network manager.
