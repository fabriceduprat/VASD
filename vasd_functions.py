# -*- coding: utf-8 -*-
"""Module with most VASD functions :
    - intput/output,
    - acquisition parameters (read from params/parameters.json)
    - user guide
"""

import os
import tkinter as tk                    # standard library
import json                             # standard library
import datetime
import cv2
import numpy as np


def exit_vasd():
    "Exit VASD script"
    os._exit(1)

##### INITIALISATIONS
# Read parameters from json file
vasd_directory = os.path.dirname(os.path.abspath(__file__))     # current directory
if os.path.exists(os.path.join(vasd_directory, 'params', 'parameters.json')):
    try:
        with open(os.path.join(vasd_directory, 'params', 'parameters.json'), 'r') as filereader:
            vasd_params = json.load(filereader)
    except IOError as json_error:
        print(f"Error reading parameters.json: {json_error}")
        exit_vasd()
else:
    print("Cannot find parameters.json")
    exit_vasd()

# Set constants
VASD_VERSION = vasd_params['VERSION']
CAMERA_ADDRESS = tuple(vasd_params['CAMERA_ADDRESS'])
NB_CAMERAS = len(CAMERA_ADDRESS)
CAMERA_FPS = tuple(vasd_params['CAMERA_FPS'])
audio_video = ("Video", "Video+Audio")
CAMERA_TYPE = tuple([audio_video[x] for x in vasd_params['AUDIO']])     # Transform 0 / 1 into Video / Video+Audio
s_hours = [str(x) for x in range(24)]
SCHED_HOURS = [i.zfill(2) for i in s_hours]     # zero padded hours
SCHED_DAYS = [str(x) for x in range(1, 100)]

BASE_DIR = os.path.normpath(vasd_params['BASE_DIR'])        # base directory to store all files
DIR_IN_PROGRESS = os.path.join(BASE_DIR, 'in_progress')     # sub directory for files not yet analysed
PROC_ANALYSIS = None            # to share analysis process reference
PROC_SCHED = None               # to share scheduling process reference
PROC_GUI = None                 # to share main gui process reference
CURRENT_RECORD_INDEX = 0        # to follow index of currently recorded file
TOTAL_VIDEO_FILES = 0           # to count the total video files tghat will be acquired
CURRENT_ANALYSED_INDEX = 1      # to follow index of currently analysed file
COLOR_MENU = "cadetblue"                # cadetblue  (95, 158, 160)  #5f9ea0
COLOR_TEXT_LIGHT = "snow"               # snow  (255, 250, 250)  #fffafa
COLOR_BUTTON = "#D3D3D3"                # lightgray  (211, 211, 211)  #d3d3d3
COLOR_BUTTON_ACTIVE = "#87CEFA"         # lightskyblue  (135, 206, 250)  #87cefa
COLOR_BACKGROUND = "azure"              # azure  (240, 255, 255)  #f0ffff
COLOR_LISTBOX = "snow"                  # snow  (255, 250, 250)  #fffafa
FONT_TITLE = ("Times", 20, "bold")          #font
FONT_LABEL = ("Times", 10, "bold italic")   #font
FONT_BUTTON = ("Times", 9, "bold")          #font
FONT_LISTBOX = ("Times", 11)                #font



def get_formatted_datetime_now():
    " Return current date and time european format, ex: 23/11/2019 15:34:57"
    mydate = datetime.datetime.now()
    return mydate.strftime("%d/%m/%Y %H:%M:%S")


def check_string(text):
    "Return the string without special characters except dash '-', and only the first 10 digits if two long"
    clean_text = ''.join(c for c in text if (c.isalpha() or c.isdigit() or c == "-"))
    if len(clean_text) > 10:
        return clean_text[:10]
    else:
        return clean_text


def test_stream(camera_index, screen_width):
    "Show stream images to test address (no audio)"

    # Initialisations
    videocap = cv2.VideoCapture(CAMERA_ADDRESS[camera_index])
    _, frame = videocap.read()  # read frame from video stream
    video_height, video_width = frame.shape[:2]
    display_width = int(screen_width / 2)
    display_height = int((display_width / video_width) * video_height)
    window_name = f"Test camera #{camera_index}"
    display_text = "Q to quit, audio is not available"
    quit_text_size, _ = cv2.getTextSize(text=display_text,
                                        fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                                        fontScale=0.6,
                                        thickness=2,
                                        )
    # Main loop reading stream and displaying resized images with legend
    while True:
        _, frame = videocap.read()  # read frame from video stream
        if np.any(frame):
            resized_image = cv2.resize(frame, (display_width, display_height), interpolation=cv2.INTER_AREA)
            cv2.putText(img=resized_image,
                        text=display_text,
                        org=(10, quit_text_size[1]+10),
                        fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                        fontScale=0.6,
                        color=(0, 255, 0),
                        thickness=2,
                        )
            cv2.imshow(window_name, resized_image)
        # Press Q on keyboard to exit
        if cv2.waitKey(25) & 0xFF == ord('q'):
            videocap.release()  # release capture
            cv2.destroyAllWindows()
            break


def user_guide(vasd_version):
    """ INPUT vasd version,
        DISPLAY the user guide informations
    """

    message = []
    message.append('')
    message.append('Video Acquisition and Seizure Detection')
    message.append('')
    message.append('  __________________________________________________________________________________________________________________________')
    message.append('Acquisition parameters are read from vasd/params/parameters.json file.')
    message.append('WARNING: You need to modify by hand these parameters before first use, see the README.md file for explanations.')
    message.append('  __________________________________________________________________________________________________________________________')
    message.append('')
    message.append('VASD enable the acquisition of 1 to 8 IP cameras, recording mp4 videos of 1 hour (codec H265) using full field, left part, or right part of each camera.')
    message.append('The motion analysis is automatically done and output in a csv file, companion package SASDI is recommended to interpret analysis.')
    message.append('')
    message.append('  __________________________________________________________________________________________________________________________')
    message.append('')
    message.append('HOW TO USE THE INTERFACE ?')
    message.append('')
    message.append('')
    message.append('>> Test access to the IP cameras:')
    message.append('Test the cameras you want to acquire with corresponding buttons (ex: "Test camera 0"), allow few seconds before the display window opens.')
    message.append('Use Q key to close the video player. If the camera also acquire audio you will not be able to check it at that step.')
    message.append('')
    message.append('>> Serie name:')
    message.append('Enter a name for the serie (limitations: max 10 characters, only letters and digits, no spaces, no special characters except dash "-" ), ex: test-serie.')
    message.append('It can be left empty, because the current date (format "year_month_date_") will be added before the choosen name as indicated (ex: "2021_06_24_test-serie").')
    message.append('The serie name is used to create the main directory containing one subdirectory for each camera.')
    message.append('This main directory is created in the BASE_DIR directory indicated in "parameters.json" (see README.md).')
    message.append('')
    message.append('>> Cameras and sides choices:')
    message.append('Next to the index of each camera (1, 2, 3, ...) the recorded stream "Video only" or "Video+Audio" is indicated for information.')
    message.append('Choose which sides you want to acquire and analyse with the drop-down menus (x_ is the index of each camera):')
    message.append('     - No recording: this camera will be unused.')
    message.append('     - x_Left: acquire and analyse only the left half side of the video field,')
    message.append('     - x_Right: acquire and analyse only the right half side of the video field,')
    message.append('     - x_Both: acquire the full video field, and analyse both sides separately,')
    message.append('     - x_All: acquire and analyse the full video field as one.')
    message.append('')
    message.append('>> Animals identification:')
    message.append('Enter animals IDs (ex: "787")for each camera (same limitations as above, can be empty).')
    message.append('If using "Both sides" mode with 2 animals, you can use dash sign "-" to separate the 2 IDs (ex: "178-247")')
    message.append('')
    message.append('>> Scheduling of acquisition:')
    message.append('In all cases, 1 hour long videos will be recorded starting each exact hour (ex: at 20:00, 21:00, 22:00, etc ...).')
    message.append('Choose "Start time" and "Stop time" (in hours, ex: 20 and 8 for 20:00 and 8:00), and "Duration" of recording (in days, ex: 3).')
    message.append('VASD will start at first occurence of "Start time" hour and then, after "Duration" days, definitely stop at first occurence of "Stop time" hour.')
    message.append('There are two modes of acquisition:')
    message.append('     - CONTINUOUS: Videos will be continuously recorded each hour, starting at "Start time", for the choosen number of days, until "Stop time".')
    message.append('                   Ex1: from today at 19:00 until same day next week ("Duration" is 7) at 10:00.')
    message.append('                   Choose 1 day duration for an acquisition duration < 24h:')
    message.append('                       Ex2: start today at 10:00 and stop today at 23:00 (last video is recorded between 22:00 and 23:00), Ex3: start today at 20:00 and stop tomorrow at 8:00.')
    message.append('     - REPEATED: Videos will be recorded exclusively between "Start time" and "Stop time" for one cycle, then stop.')
    message.append('                 The cycle is repeated to obtain the choosen number of "Duration" days (only one cycle if: and  "Duration" is 1).')
    message.append('                 Ex: night recording between 20:00 and 8:00 for 3 days.')
    message.append('Notes: - The start hour is always the next occurence, you cannot program a start at 11:00 tomorrow if current time is before 11:00 (wait after 11:00 to start VASD).')
    message.append('       - With a duration of 1 day, the two modes are identical (one cycle).')
    message.append('       - Dates are displayed with the format date/month/year (ex: "24/12/2020"), except for directory and file names (ex: "2020_12_24", "2020_12_24_15h00m00s") to obtain a sorted display based on names.')
    message.append('')
    message.append('>> Starting and Stopping acquisition and analysis:')
    message.append('Clicking on the "Start Acquisition+Analysis" button starts all processes.')
    message.append('Clicking on the "Stop Acquisition" button will stop immediately acquisition, analysis of already acquired videos will go on for 2 hours to make sure they are all processed, ongoing video acquisition is definitely lost.')
    message.append('Clicking on the "Stop Acquisition+Analysis" button will stop immediately acquisition and analysis, ongoing analysis of acquired videos is lost (you can perform analysis later with SASDI), ongoing video acquisition is definitely lost.')
    message.append('')
    message.append('>> Exiting the script:')
    message.append('Clicking on "Exit" button will terminate the script and thus immediately stop all acquisitions and analysis if there are some.')
    message.append('  __________________________________________________________________________________________________________________________')
    message.append('')
    message.append('Reading motion analysis files and corresponding videos to confirm convulsive seizures is done with the SASDI package.')
    message.append('All videos from one camera and their analysis files are stored in a single subdirectory,')
    message.append('the sides (L, R, B, A for Left, Right, Both, All), animal IDs, and camera indices (1, 2, 3, ...) are used for subdirectories names, ex:"/L_787_CAM2/".')
    message.append('The sides, animal IDs, camera indices, acquisition date ("year_month_date" format) and time (hour, minutes, seconds, "00h00m00s" format) are used for video filenames, ex:"A_788_CAM3_2021_07_28_17h00m00s.mp4".')
    message.append('Extension for video files is "video_filename.mp4," and for motion results is "video_filename.mp4.csv".')
    message.append('Motion results are stored in standard csv files (columns delimitted by space " ") readable by many softwares.')
    message.append('First column is time (in seconds) from beginning of analysed video, second column is normalised motion analysis values (all sides), same for third colum (only present for "Both" sides analysis).')
    message.append('Motion is calculated between each consecutive frames as the sum of pixel by pixel intensity variations normalised to maximal possible variation (with median blurring and thresholding to remove artefacts and background).')
    message.append('')
    message.append('  __________________________________________________________________________________________________________________________')
    message.append('Dr Fabrice DUPRAT, duprat@ipmc.cnrs.fr, july 2021')


    # Define the tkinter window and its title
    master = tk.Tk()
    master.title("VASD v"+vasd_version)
    # Define vertical and horizontal scrollbars:
    y_defil_bar = tk.Scrollbar(master, orient='vertical')
    y_defil_bar.grid(row=0, column=1, sticky='ns')
    x_defil_bar = tk.Scrollbar(master, orient='horizontal')
    x_defil_bar.grid(row=1, column=0, sticky='ew')
    # Define the listbox to display help
    mylist = tk.Listbox(master,
                        width=150,                             # in characters
                        height=30,                             # in lines
                        font=FONT_LISTBOX,
                        background=COLOR_LISTBOX,
                        borderwidth=2,
                        relief=tk.SUNKEN,
                        xscrollcommand=x_defil_bar.set,
                        yscrollcommand=y_defil_bar.set,
                       )
    for line in message:
        mylist.insert(tk.END, line)
    mylist.grid(row=0, column=0, sticky='nsew')
    x_defil_bar['command'] = mylist.xview
    y_defil_bar['command'] = mylist.yview
