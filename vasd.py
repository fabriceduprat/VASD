# -*- coding: utf-8 -*-
"Main VASD starting script"

import os
import sys
import time
import datetime
import subprocess
from tkinter import ttk, Tk, IntVar, W, E, DISABLED, ACTIVE, RAISED, RIDGE, FLAT, Entry, Frame, Label, Button, Radiobutton
import multiprocessing
from functools import partial
import cv2
import schedule
from colorama import Fore, Style, init
import video_analysis
import vasd_functions as vf


###################################################################################################
def analysis(dir_serie):
    "Analyse video files present in vf.DIR_IN_PROGRESS and move files (videos and CSV files) to dir_serie"

    #print(f"DEBUG PROC_ANALYSIS Is alive in analysis? {vf.PROC_ANALYSIS.is_alive()}")
    while True:
        #print(f"DEBUG PROC_ANALYSIS Is alive in analysis? {vf.PROC_ANALYSIS.is_alive()}")
        #print(f"DEBUG {vf.get_formatted_datetime_now()}, <analysis> while loop starts")
        all_files_ready = [] # List of all files (videos, csv, and wav files) ready to be transfered
        files_size_1 = [] # List of the videos size after first check
        files_size_2 = [] # List of the videos size after second check
        files_name = [] # List of all videos
        list_videos_to_analyse = [] # List of videos ready for analysis
        # First size check of all files present in "in-progress" directory
        for file in os.listdir(vf.DIR_IN_PROGRESS):
            files_size_1.append(os.path.getsize(os.path.join(vf.DIR_IN_PROGRESS, file)))
            files_name.append(file)
        # wait 5 min
        time.sleep(300)
        # Second size check
        for file in files_name:
            files_size_2.append(os.path.getsize(os.path.join(vf.DIR_IN_PROGRESS, file)))

        for index, file in enumerate(files_name):  # enumerate each video file
            vidcap = None
            size_change = files_size_2[index] - files_size_1[index]
            csv_exists = os.path.exists(os.path.join(vf.DIR_IN_PROGRESS, file+".csv"))
            #print(f"DEBUG {vf.get_formatted_datetime_now()}, <analysis> file[{index}]: {file} -> size_change: {size_change} csv_exist: {csv_exists}, len files_size_1:{len(files_size_1)}, files_size_2:{len(files_size_2)}")
            # If video file creation is finished (size1=size2) and not already analysed then add to list_videos_to_analyse
            if (file.endswith(".mp4") and size_change == 0 and not csv_exists):
                try:
                    # Read video to analyse
                    vidcap = cv2.VideoCapture(os.path.join(vf.DIR_IN_PROGRESS, file))
                except cv2.error as cv2_error:
                    print(f"{vf.get_formatted_datetime_now()}, Error reading file {file}: {cv2_error}")
                    continue
                # Calculate coordinates according to type of acquisition
                roicoord = []
                # Get width, height of current video
                _, _ = vidcap.read()
                video_width = int(vidcap.get(cv2.CAP_PROP_FRAME_WIDTH))
                video_height = int(vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                video_fps = float(vidcap.get(cv2.CAP_PROP_FPS))
                vidcap.release()
                if not video_height or not video_width:
                    print(f"{vf.get_formatted_datetime_now()}, No dimensions found for file {file}, size_change={size_change}")
                    video_width = 2
                    video_height = 2
                if file[0] == 'B':   # Both halves of video to analyse
                    roicoord = [((1, 1), (int(video_width / 2), video_height - 1)), ((int(video_width / 2) + 1, 1), (video_width - 1, video_height - 1))]
                else:               # Full video to analyse
                    roicoord = [((1, 1), (video_width - 1, video_height - 1))]
                # Add videos infos to list of files to analyse
                list_videos_to_analyse.append([video_fps, vf.DIR_IN_PROGRESS, file, roicoord, vf.CURRENT_ANALYSED_INDEX, vf.TOTAL_VIDEO_FILES])
                vf.CURRENT_ANALYSED_INDEX += 1

            # If csv file with finished analysed, then save name to all_files_ready
            elif (file.endswith(".csv") and not size_change):
                all_files_ready.append(file)

        # Start analysing all video files with finished acquisition
        number_videos = len(list_videos_to_analyse)
        if number_videos > 0:
            with multiprocessing.Pool(processes=number_videos) as pool:
                # Analyse each video in one process
                pool.map(video_analysis.one_video_analysis, list_videos_to_analyse)
        # Move csv files present in all_files_ready and corresponding video files to the corresponding subdirectories (ex: R_nameright_CAM1, A_nameleft_CAM2, ...) according to their names
        for file in all_files_ready:      # all csv files to be moved
            for directory in os.listdir(dir_serie):         # all existing subdirectories (1 for each camera)
                dir_files = os.path.join(dir_serie, directory)
                if file.startswith(directory):
                    try:
                        os.rename(os.path.join(vf.DIR_IN_PROGRESS, file), os.path.join(dir_files, file))
                    except OSError as err:
                        print(f"{vf.get_formatted_datetime_now()} Error when trying to move <{file}> from <{vf.DIR_IN_PROGRESS}> to <{dir_files}>")
                        print(f"Error: {err}")
                    try:
                        os.rename(os.path.join(vf.DIR_IN_PROGRESS, file[:-4]), os.path.join(dir_files, file[:-4]))
                    except OSError as err:
                        print(f"{vf.get_formatted_datetime_now()} Error when trying to move <{file[:-4]}> from <{vf.DIR_IN_PROGRESS}> to <{dir_files}>")
                        print(f"Error: {err}")

        time.sleep(300) # wait 5 min before rechecking files present in "in_progress" directory (while loop)


def start_analysis(dir_serie, total_hours):
    "Runs an analysis process (multiprocessing module)"

    print(Style.BRIGHT + Fore.GREEN + f"###### {vf.get_formatted_datetime_now()} ###### Start analysis process #######")
    print(Style.RESET_ALL)
    vf.PROC_ANALYSIS = multiprocessing.Process(target=analysis,
                                               args=(dir_serie,)
                                              )
    vf.PROC_ANALYSIS.start()
    # print(f"DEBUG PROC_ANALYSIS Is alive after creation in start_analysis? {vf.PROC_ANALYSIS.is_alive()}")


def stop_analysis(time_sec):
    "Stop the analysis process started by start_analysis()"

    time.sleep(time_sec)
    # print(f"DEBUG PROC_ANALYSIS Is still alive after time sleep in stop_analysis? {vf.PROC_ANALYSIS.is_alive()}")
    if vf.PROC_ANALYSIS:
        if vf.PROC_ANALYSIS.is_alive():
            vf.PROC_ANALYSIS.terminate()
            # print(f"DEBUG PROC_ANALYSIS Is still alive after terminate in stop_analysis? {vf.PROC_ANALYSIS.is_alive()}")
        vf.PROC_ANALYSIS.join()
    # print(f"DEBUG PROC_ANALYSIS Is still alive after join in stop_analysis? {vf.PROC_ANALYSIS.is_alive()}")

def acquire_left(dir_serie, channel_id, mouse_id):
    "Starts acquisition process for left area of the camera (channel_id=camera number, mouse_id=tag of the mouse)"

    # Reassign standard output to the original one (terminal)
    sys.stdout = sys.__stdout__
    channel_id = int(channel_id)
    mydate = datetime.datetime.now()
    videodate = mydate.strftime("%Y_%m_%d_%Hh%Mm%Ss")        # for ffmpeg command ex: 2020_11_23_15h00m00s
    # Parameters of ffmpeg command:
    # -r vf.CAMERA_FPS | Set frame rate (input and/or output stream)
    # -rtsp_transport tcp | Use TCP (interleaving within the RTSP control channel) as lower transport protocol
    # -t duration | Duration of the generated video file
    # -i input | input video flux url
    # -filter_complex : Use to crop video (width:height:Xstart:Ystart) and map it to a "label"
    # -map[label]
    # -c:v codec | Select an encoder video (libx265)
    # -metadata key=value | Set the title of the video
    # -loglevel level | Set logging level and flags displayed in the terminal (error, warning, debug)
    # -y Overwrite output files without asking
    # filename of output video
    # shell=True compulsory

    # For debug: ffmpeg -loglevel debug -r 15 -rtsp_transport tcp -i "rtsp://admin:eeg@192.168.79.42:554/cam/realmonitor?channel=1&subtype=0"
    # -filter_complex [0:v]crop=in_w/2:in_h:0:0[out_L] -map [out_L] -t 00:01:00 -r 15 -y -c:v libx265 -metadata title="mouse_id" videoL.mp4
    # ffmpeg command with parameters , 2>&1 redirect standard error to standard output
    ffinput = f'ffmpeg -loglevel error -r {vf.CAMERA_FPS[channel_id]} -rtsp_transport tcp -i "{vf.CAMERA_ADDRESS[int(channel_id)]}" '       # input video stream
    fffilter = '-filter_complex [0:v]crop=in_w/2:in_h:0:0[out_L] '                                                              # cropping of video input
    ffoutput1 = f"-map [out_L] -t {'01:00:00'} -r {vf.CAMERA_FPS[channel_id]} -y -c:v libx265 "                        # output video parameters
    ffoutput2 = f'-metadata title="{mouse_id} [CAM{channel_id} Left {videodate}]" '                        # title in metadata
    outputfile = os.path.join(vf.DIR_IN_PROGRESS, f"L_{mouse_id}_CAM{channel_id}_{videodate}.mp4")
    ffoutput3 = f'{outputfile} >> {os.path.join(dir_serie, "ffmpeg.log")} 2>&1'                   # output file name
    if vf.CAMERA_TYPE[channel_id] == "Video+Audio":
        ffoutput1 = f"-map [out_L] -map 0:a:0 -t {'01:00:00' } -r {vf.CAMERA_FPS[channel_id]} -y -c:v libx265 "         # output video+audio parameters
    subprocess.Popen(ffinput + fffilter + ffoutput1 + ffoutput2 + ffoutput3, shell=True)
    # print("DEBUG "+ffinput+fffilter+ffoutput1+ffoutput2+ffoutput3)
    # print(f"DEBUG {vf.get_formatted_datetime_now()}, <acquire_left> started with L_{mouse_id}_CAM{channel_id}_{videodate}.mp4")


def acquire_right(dir_serie, channel_id, mouse_id):
    "Starts acquisition process for right area of the camera (channel_id= camera number, mouse_id=tag of the mouse)"

    # Reassign standard output to the original one (terminal)
    sys.stdout = sys.__stdout__
    channel_id = int(channel_id)
    mydate = datetime.datetime.now()
    videodate = mydate.strftime("%Y_%m_%d_%Hh%Mm%Ss")        # for ffmpeg command ex: 2020_11_23_15h00m00s

    # For debug: ffmpeg -loglevel debug -r 15 -rtsp_transport tcp -i "rtsp://admin:eeg@192.168.79.42:554/cam/realmonitor?channel=2&subtype=0"
    # -filter_complex [0:v]crop=in_w/2:in_h:in_w/2:0[out_R] -map [out_R] -t 00:01:00 -r 15 -y -c:v libx265 -metadata title="mouse_id" videoR.mp4
    # ffmpeg command with parameters (see above)
    ffinput = f'ffmpeg -loglevel error -r {vf.CAMERA_FPS[channel_id]} -rtsp_transport tcp -i "{vf.CAMERA_ADDRESS[int(channel_id)]}" '       # input video stream
    fffilter = '-filter_complex [0:v]crop=in_w/2:in_h:in_w/2:0[out_R] '                                                         # cropping of video input
    ffoutput1 = f'-map [out_R] -t {"01:00:00"} -r {vf.CAMERA_FPS[channel_id]} -y -c:v libx265 '                                             # output video parameters
    ffoutput2 = f'-metadata title="{mouse_id} [CAM{channel_id} Right {videodate}]" '                                     # title in metadata
    outputfile = os.path.join(vf.DIR_IN_PROGRESS, f"R_{mouse_id}_CAM{channel_id}_{videodate}.mp4")
    ffoutput3 = f'{outputfile} >> {os.path.join(dir_serie, "ffmpeg.log")} 2>&1'                   # output file name
    if vf.CAMERA_TYPE[channel_id] == "Video+Audio":
        ffoutput1 = f'-map [out_R] -map 0:a:0 -t {"01:00:00"} -r {vf.CAMERA_FPS[channel_id]} -y -c:v libx265 '                              # output video+audio parameters
    subprocess.Popen(ffinput + fffilter + ffoutput1 + ffoutput2 + ffoutput3, shell=True)
    # print("DEBUG "+ffinput+fffilter+ffoutput1+ffoutput2+ffoutput3)
    # print(f"DEBUG {vf.get_formatted_datetime_now()}, <acquire_right> started with R_{mouse_id}_CAM{channel_id}_{videodate}.mp4")


def acquire_both(dir_serie, channel_id, mouse_id):
    "Starts acquisition process for left and right areas of the camera (channel_id= camera number, mouse_id=tag of the mouse)"

    # Reassign standard output to the original one (terminal)
    sys.stdout = sys.__stdout__
    mydate = datetime.datetime.now()
    videodate = mydate.strftime("%Y_%m_%d_%Hh%Mm%Ss")        # for ffmpeg command ex: 2020_11_23_15h00m00s
    # For debug: ffmpeg -loglevel debug -r 12 -rtsp_transport tcp -i "rtsp://admin:eeg@192.168.79.43:554/12" -t 00:01:00 -r 12 -y -c:v libx265 -metadata title="all" videoaudio.mp4
    # ffmpeg command with parameters (see above)
    ffinput = f'ffmpeg -loglevel error -r {vf.CAMERA_FPS[int(channel_id)]} -rtsp_transport tcp -i "{vf.CAMERA_ADDRESS[int(channel_id)]}" '       # input video stream
    ffoutput1 = f'-t {"01:00:00"} -r {vf.CAMERA_FPS[int(channel_id)]} -y -c:v libx265 '                                                          # output video parameters
    ffoutput2 = f'-metadata title="{mouse_id} [CAM{channel_id} Both {videodate}]" '                                       # title in output metadata
    outputfile = os.path.join(vf.DIR_IN_PROGRESS, f"B_{mouse_id}_CAM{channel_id}_{videodate}.mp4")
    ffoutput3 = f'{outputfile} >> {os.path.join(dir_serie, "ffmpeg.log")} 2>&1'                   # output file name
    subprocess.Popen(ffinput + ffoutput1 + ffoutput2 + ffoutput3, shell=True)
    # print("DEBUG "+ffinput+ffoutput1+ffoutput2+ffoutput3)
    # print(f"DEBUG {vf.get_formatted_datetime_now()}, <acquire_both> started with B_{mouse_id}_CAM{channel_id}_{videodate}.mp4")


def acquire_all(dir_serie, channel_id, mouse_id):
    "Starts acquisition process for entire area of the camera (channel_id=camera number, mouse_id=tag of the mouse)"

    # Reassign standard output to the original one (terminal)
    sys.stdout = sys.__stdout__
    channel_id = int(channel_id)
    mydate = datetime.datetime.now()
    videodate = mydate.strftime("%Y_%m_%d_%Hh%Mm%Ss")        # for ffmpeg command ex: 2020_11_23_15h00m00s
    # For debug: ffmpeg -loglevel debug -r 12 -rtsp_transport tcp -i "rtsp://admin:eeg@192.168.79.43:554/12" -t 00:01:00 -r 12 -y -c:v libx265 -metadata title="all" videoaudio.mp4
    # ffmpeg command with parameters (see above)
    ffinput = f'ffmpeg -loglevel error -r {vf.CAMERA_FPS[channel_id]} -rtsp_transport tcp -i "{vf.CAMERA_ADDRESS[int(channel_id)]}" '       # input video stream
    ffoutput1 = f'-t {"01:00:00"} -r {vf.CAMERA_FPS[channel_id]} -y -c:v libx265 '                                                          # output video parameters
    ffoutput2 = f'-metadata title="{mouse_id} [CAM{channel_id} All {videodate}]" '                                       # title in output metadata
    outputfile = os.path.join(vf.DIR_IN_PROGRESS, f"A_{mouse_id}_CAM{channel_id}_{videodate}.mp4")
    ffoutput3 = f'{outputfile} >> {os.path.join(dir_serie, "ffmpeg.log")} 2>&1'                   # output file name
    subprocess.Popen(ffinput + ffoutput1 + ffoutput2 + ffoutput3, shell=True)
    # print("DEBUG "+ffinput+ffoutput1+ffoutput2+ffoutput3)
    # print(f"DEBUG {vf.get_formatted_datetime_now()}, <acquire_all> started with A_{mouse_id}_CAM{channel_id}_{videodate}.mp4")

def start_acquisition(dir_serie, acquisition_choices, stop_hour, total_hours, end_date_format):
    """Start acquisition process of videos with user choices in list acquisition_choices, with following infos:
        [0] camera/channel index
        [1] side (Left, Right, All, Both)
        [2] mouse id
    """

    #print(f"DEBUG {vf.get_formatted_datetime_now()}, <start_acquisition> job list:")
    #for job in schedule.jobs:
    #    print(f"       DEBUG {job}")

    myprocess = []
    vf.CURRENT_RECORD_INDEX = vf.CURRENT_RECORD_INDEX + 1

    video_input = {'Left' : acquire_left,
                   'Right' : acquire_right,
                   'Both' : acquire_both,
                   'All' : acquire_all,
                  }
    # For each choice split the infos and creates a list of ffmpeg processes (using video_input mapping dictionnary)
    for val in acquisition_choices:
        split_val = val.split('_')
        myprocess.append(multiprocessing.Process(target=video_input[split_val[1]],
                                                 args=(dir_serie, split_val[0], split_val[2])
                                                )
                        )

    # Start all the ffmpeg processes for video acquisition
    for index, _ in enumerate(acquisition_choices):
        myprocess[index].start()
        #print(f"DEBUG {vf.get_formatted_datetime_now()}, <start_acquisition> Start process # {index}")

    # Wait for all ffmpeg processes to complete
    for index, _ in enumerate(acquisition_choices):
        myprocess[index].join()
    print(Style.BRIGHT + Fore.GREEN + f"{vf.get_formatted_datetime_now()} Acquisition of hour {vf.CURRENT_RECORD_INDEX} / {total_hours} hours (Will end the {end_date_format} at {stop_hour}:00)")
    print(Style.RESET_ALL)


def store_choices(cbox_channel, id_entry, var_radio, cbox_schedule):
    """Stores and format users choices for acquisition
    """

    # clear all items
    acquisition_choices = []
    acquisition_choices_tmp = []

    # loop for getting user's choices : camera/channel id ,left or right, mouse id
    for i in range(vf.NB_CAMERAS):
        cbox_value = cbox_channel[i].get()             # get comboboxes values (camera/channel and Left/Right/All/Both)
        mouse_id = id_entry[i].get()       # get entries values (mouse id)
        mouse_id_format = vf.check_string(mouse_id)
        acquisition_choices_tmp.append(cbox_value + '_' + mouse_id_format)   # concatenate choices in 1 string per camera

    # Remove camera/channel if 'No recording' is choosen
    for val in acquisition_choices_tmp:
        if not val.startswith('No recording'):
            acquisition_choices.append(val)

    # Get the continuous or repeated recording choice
    type_acquisition = var_radio.get()

    # Get Start hour
    start_hour = cbox_schedule[0].get()
    # Get Stop hour
    stop_hour = cbox_schedule[1].get()
    # Get hour preceding Stop hour
    index_stop_hour = vf.SCHED_HOURS.index(stop_hour)
    if index_stop_hour == 0:
        stop_before_hour = "23"
    else:
        stop_before_hour = vf.SCHED_HOURS[index_stop_hour - 1]
    # Get duration of acquisition
    duration = cbox_schedule[2].get()
    #print(f"DEBUG {vf.get_formatted_datetime_now()}, <store_choices> acquisition choices: {acquisition_choices}")
    return acquisition_choices, int(start_hour), int(stop_hour), int(stop_before_hour), int(duration), int(type_acquisition)


def infos_to_terminal(start_hour, stop_hour, duration, type_acquisition, nb_used_cameras):
    "Show infos in terminal"
    start_date = datetime.date.today()  # initialise start date today
    hour_now =  datetime.datetime.now().hour

    if start_hour < hour_now:    # acquisition starts tomorrow
        start_date = start_date + datetime.timedelta(1)

    # Continuous acquisition
    if type_acquisition == 1:
        if stop_hour > start_hour:
            end_date = start_date + datetime.timedelta(days=duration - 1)
            total_hours = (duration - 1) * 24 + stop_hour - start_hour
        else:
            end_date = start_date + datetime.timedelta(days=duration)
            total_hours = (duration - 1) * 24 +(24 - start_hour + stop_hour)
        infos = f"CONTINUOUS ACQUISITION will start the {start_date.strftime('%d/%m/%Y')} at {start_hour}:00 and finish the {end_date.strftime('%d/%m/%Y')} at {stop_hour}:00"

    # Repeated acquisition
    else:       # Repeated = 2
        if stop_hour > start_hour:        # start and stop same day
            end_date = start_date + datetime.timedelta(days=duration - 1)
            total_hours = duration * (stop_hour - start_hour)
        else:      # start one day and stop the day after
            end_date = start_date + datetime.timedelta(days=duration)
            total_hours = duration * (24 - start_hour + stop_hour)
        infos = f"REPEATED ACQUISITION from {start_hour}:00 to {stop_hour}:00 will start the {start_date.strftime('%d/%m/%Y')} and finish the {end_date.strftime('%d/%m/%Y')}"

    #print(f"DEBUG {vf.get_formatted_datetime_now()}, <infos_to_terminal> total_hours: {total_hours}")
    vf.TOTAL_VIDEO_FILES = total_hours * nb_used_cameras
    print(Style.BRIGHT+ Fore.GREEN + f"######")
    print(Style.BRIGHT+ Fore.GREEN + f"{infos}")

    print(Style.BRIGHT+ Fore.GREEN + f"Total is {total_hours} hours of recording with {nb_used_cameras} camera(s) ({vf.TOTAL_VIDEO_FILES} video files will be created)")
    print(Style.BRIGHT+ Fore.GREEN + "######")
    print(Style.RESET_ALL)
    return total_hours, end_date.strftime('%d/%m/%Y')


def make_dirs(serie_name, acquis_choices):
    "Creates in-progress and current serie directories"

    # Set name of serie directory
    mydate = datetime.datetime.now()
    seriedate = mydate.strftime("%Y_%m_%d")
    dir_serie = os.path.join(vf.BASE_DIR, 'analysed', seriedate + "_"+ serie_name)     # ex: /2020_11_25_serie

    # Rename terminal window with serie date
    sys.stdout.write("\x1b]2;VASD v" + vf.VASD_VERSION + " serie " + seriedate + "\x07")
    print(Style.BRIGHT+ Fore.GREEN + f"###### {vf.get_formatted_datetime_now()} ###### VASD {vf.VASD_VERSION} ######")

    if not os.path.exists(vf.DIR_IN_PROGRESS):
        os.makedirs(vf.DIR_IN_PROGRESS)
        print(f"Directory {vf.DIR_IN_PROGRESS} Created ")
    else:
        print(f"Directory {vf.DIR_IN_PROGRESS} already exists")

    if not os.path.exists(dir_serie):
        os.makedirs(dir_serie)
        print(f"Directory {dir_serie} Created ")
    else:
        print(f"Directory {dir_serie} already exists")

    dir_all_cams = []                                                           # List of directory names for analysed files
    for val in acquis_choices:
        split_val = val.split('_')
        if split_val[1] == 'Both':                           # ACQUIRE BOTH:
            dir_both = os.path.join(dir_serie, f"B_{split_val[2]}_CAM{split_val[0]}")          # B_idmouse_CAMindexcamera
            dir_all_cams.append(dir_both)
        elif split_val[1] == 'Left':                         # ACQUIRE LEFT:
            dir_left = os.path.join(dir_serie, f"L_{split_val[2]}_CAM{split_val[0]}")          # L_idmouse_CAMindexcamera
            dir_all_cams.append(dir_left)
        elif split_val[1] == 'Right':                        # ACQUIRE RIGHT:
            dir_right = os.path.join(dir_serie, f"R_{split_val[2]}_CAM{split_val[0]}")         # R_idmouse_CAMindexcamera
            dir_all_cams.append(dir_right)
        else:                                                # ACQUIRE ALL:
            dir_all = os.path.join(dir_serie, f"A_{split_val[2]}_CAM{split_val[0]}")           # A_idmouse_CAMindexcamera
            dir_all_cams.append(dir_all)

    for dir_name in dir_all_cams:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
            print(f"Directory {dir_name} created")
        else:
            print(f"Directory {dir_name} already exists")
    print(Style.RESET_ALL)
    return dir_serie, len(dir_all_cams)


def master_start_schedule(root, serie_name_entry, id_entry, test_cameras, cbox_channel, cbox_schedule, button_start_sched, button_stop_acq, button_stop_all, button_rad_continuous, button_rad_repeated, var_radio):
    "Starts all schedule processes (master_schedule_run) if Start button pressed"

    # serie name
    serie_name = vf.check_string(serie_name_entry.get())
    # Get user choices from tkinter interface
    acquisition_choices, start_hour, stop_hour, stop_before_hour, duration, type_acquisition = store_choices(cbox_channel, id_entry, var_radio, cbox_schedule)
    # Check useless choices
    if start_hour == stop_hour and duration == 1:
        print("Start canceled because scheduled acquisition is null")
        return
    # Create needed directories (1 per camera)
    dir_serie, nb_used_cameras = make_dirs(serie_name, acquisition_choices)
    # Print infos to terminal
    total_hours, end_date_format = infos_to_terminal(start_hour, stop_hour, duration, type_acquisition, nb_used_cameras)

    #print(f"DEBUG {vf.get_formatted_datetime_now()} <master_start_schedule>")

    # Active or disable (shade) tkinter objects during script running
    serie_name_entry.config(state=DISABLED)
    for i in range(vf.NB_CAMERAS):
        cbox_channel[i].config(state=DISABLED)
        id_entry[i].config(state=DISABLED)
        test_cameras[i].config(state=DISABLED)
    for i in range(3):
        cbox_schedule[i].config(state=DISABLED)
    button_start_sched.config(state=DISABLED)
    button_rad_continuous.config(state=DISABLED)
    button_rad_repeated.config(state=DISABLED)
    button_stop_all.config(state=ACTIVE)
    button_stop_acq.config(state=ACTIVE)

    # Starts master_schedule_run in a process
    vf.PROC_SCHED = multiprocessing.Process(target=master_schedule_run,
                                            args=(root, dir_serie, start_hour, stop_hour, stop_before_hour, acquisition_choices, duration, total_hours, end_date_format, type_acquisition,
                                                  serie_name_entry, id_entry, test_cameras, cbox_channel, cbox_schedule, button_start_sched, button_stop_acq, button_stop_all, button_rad_continuous, button_rad_repeated)
                                           )
    vf.PROC_SCHED.start()
    # vf.PROC_SCHED.join()


def master_stop_schedule(root, serie_name_entry, id_entry, test_cameras, cbox_channel, cbox_schedule, button_start_sched, button_stop_acq, button_stop_all, button_rad_continuous, button_rad_repeated, stop_all):
    "Terminate all schedule and acquisition processes if Stop buttons pressed or if end of scheduling"

    if stop_all == 1:
        # manual acquisition stop, analysis will stop after 2h
        stop_analysis(7200)
        print(Style.BRIGHT + Fore.RED + f'###### {vf.get_formatted_datetime_now()} ######VASD ###### Acquisition is stopped by user, analysis will stop in 1 hour ######')
    elif stop_all == 2:
        # manual acquisition+analysis stop, analysis is stopped immediately
        stop_analysis(0)
        print(Style.BRIGHT + Fore.RED + f'###### {vf.get_formatted_datetime_now()} ###### VASD ###### Acquisition is stopped by user ######')
    elif stop_all == 3:
        # scheduling is finished, analysis will stop after 2h
        stop_analysis(7200)
        print(Style.BRIGHT + Fore.RED + f'###### {vf.get_formatted_datetime_now()} ###### VASD ###### SCHEDULED ACQUISITION IS FINISHED ######')
    print(Style.RESET_ALL)
    # Script is waiting for user entry, active or disable (shade) tkinter objects
    serie_name_entry.config(state='normal')
    for i in range(vf.NB_CAMERAS):
        cbox_channel[i].config(state=ACTIVE)
        id_entry[i].config(state='normal')
        test_cameras[i].config(state=ACTIVE)
    for i in range(3):
        cbox_schedule[i].config(state='readonly')
    button_start_sched.config(state=ACTIVE)
    button_rad_continuous.config(state=ACTIVE)
    button_rad_repeated.config(state=ACTIVE)
    button_stop_all.config(state=DISABLED)
    button_stop_acq.config(state=DISABLED)
    root.update_idletasks()
    subprocess.call("pkill ffmpeg", shell=True)       # Linux
    # acquisition is stopped immediately
    if vf.PROC_SCHED:
        vf.PROC_SCHED.terminate()
        vf.PROC_SCHED.join()
    # print(f"proc_sched Is still alive after terminate: {vf.PROC_SCHED.is_alive()}")


def master_schedule_run(root, dir_serie, start_hour, stop_hour, stop_before_hour, acquisition_choices, duration, total_hours, end_date_format, type_acquisition,
                        serie_name_entry, id_entry, test_cameras, cbox_channel, cbox_schedule, button_start_sched, button_stop_acq, button_stop_all, button_rad_continuous, button_rad_repeated):
    "Runs the funtion start_acquisition() with scheduling"

    # Reassign standard output to the original one (terminal)
    sys.stdout = sys.__stdout__

    def start_hourly_tasks(dir_serie, acquisition_choices, stop_hour, total_hours, end_date_format, type_acquisition):
        "Start immediately an acquisition and create an hourly scheduled job ('hourly-tasks')"

        print(Style.BRIGHT + Fore.GREEN + f'###### {vf.get_formatted_datetime_now()} ###### VASD ###### Start hourly tasks ######')
        print(Style.RESET_ALL)
        # Start immediately first acquisition(s) and analysis
        start_analysis(dir_serie, total_hours)
        start_acquisition(dir_serie, acquisition_choices, stop_hour, total_hours, end_date_format)
        # Add a schedule with acquisition(s) every hour (HOURLY-TASK) whatever choice exists
        schedule.every(60).minutes.at(':00').do(lambda: start_acquisition(dir_serie, acquisition_choices, stop_hour, total_hours, end_date_format)).tag('hourly-tasks')
        #print(f"DEBUG {vf.get_formatted_datetime_now()}, schedule.every({60}).minutes.at(':00').do(lambda: start_acquisition({dir_serie}, {acquisition_choices}, {stop_hour}, {total_hours}, {end_date_format})).tag('hourly-tasks')")
        # If continuous acquisition then cancel initial task to avoid rescheduling everyday
        if type_acquisition == 1:
            # print("DEBUG <start_hourly_tasks> > clear initial task")
            return schedule.CancelJob       # cancel itself to be executed only once


    def clear_hourly_tasks(type_acquisition):
        "Stop hourly scheduled tasks ('hourly-tasks')"

        # clear scheduled jobs with tag 'hourly-tasks'
        schedule.clear('hourly-tasks')
        #print(f"DEBUG {vf.get_formatted_datetime_now()}, <clear_hourly_tasks>")
        if type_acquisition == 2:
            print(Style.BRIGHT + Fore.RED + f'###### {vf.get_formatted_datetime_now()} ###### VASD Repeated acquisition, stop hourly acquisition ######')
            print(Style.RESET_ALL)


    def clear_daily_tasks(root, serie_name_entry, id_entry, test_cameras, cbox_channel, cbox_schedule, button_start_sched, button_stop_acq, button_stop_all, button_rad_continuous, button_rad_repeated):
        """ Stop daily scheduled tasks ('daily-tasks')
        """
        schedule.clear('daily-tasks')
        master_stop_schedule(root, serie_name_entry, id_entry, test_cameras, cbox_channel, cbox_schedule, button_start_sched, button_stop_acq,
                             button_stop_all, button_rad_continuous, button_rad_repeated, 3)
        #print(f"DEBUG {vf.get_formatted_datetime_now()}, <clear_daily_tasks> cancel all daily tasks, END OF SCHEDULING")
        return schedule.CancelJob       # cancel itself to be executed only once

    start_hour_padded = str(stop_before_hour).zfill(2)
    stop_before_hour_padded = str(stop_before_hour).zfill(2)
    # CONTINUOUS ACQUISITION
    if type_acquisition == 1:
        # START: start hourly acquisition at start time (='initial-task')
        schedule.every().day.at(str(start_hour).zfill(2) + ":00:00").do(
            lambda: start_hourly_tasks(dir_serie, acquisition_choices, stop_hour, total_hours, end_date_format, type_acquisition))
        #print(f"DEBUG {vf.get_formatted_datetime_now()}, <master_schedule_run> SCHEDULE START OF CONTINUOUS ACQUISITION:")
        #print(f"DEBUG schedule.every().day.at({str(start_hour).zfill(2) + ':00:00'}).do(lambda: start_hourly_tasks({dir_serie}, {acquisition_choices}, {stop_hour}, {total_hours}, {end_date_format}, {type_acquisition})).tag('initial-task')")
        schedule.every(int(duration)).days.at(str(stop_before_hour).zfill(2) + ':59:00').do(
            lambda: clear_hourly_tasks(type_acquisition)).tag('daily-tasks')
        #print(f"DEBUG {vf.get_formatted_datetime_now()}, <master_schedule_run> continuous, FINAL STOP, schedule.every(int({duration})).days. at({str(stop_before_hour).zfill(2) + ':59:00'}) do clear_hourly_tasks({type_acquisition}).tag('daily-tasks')")
        schedule.every(int(duration)).days.at(str(stop_before_hour).zfill(2) + ':59:40').do(
            lambda: clear_daily_tasks(root, serie_name_entry, id_entry, test_cameras, cbox_channel, cbox_schedule, button_start_sched, button_stop_acq, button_stop_all, button_rad_continuous, button_rad_repeated))
        #print(f"DEBUG {vf.get_formatted_datetime_now()}, <master_schedule_run> continuous, FINAL STOP, schedule.every(int({duration})).days. at({str(stop_before_hour).zfill(2) + ':59:40'}) do clear_daily_tasks(tkinter objects))")

    # REPEATED ACQUISITION
    if type_acquisition == 2:
        #print(f"DEBUG {vf.get_formatted_datetime_now()}, <master_schedule_run> SCHEDULE DAILY START OF REPEATED ACQUISITION:")
        # DAILY START : start hourly acquisition every day at start time (= daily-tasks)
        schedule.every().day.at(str(start_hour).zfill(2) + ":00:00").do(
            lambda: start_hourly_tasks(dir_serie, acquisition_choices, stop_hour, total_hours, end_date_format, type_acquisition)).tag('daily-tasks')
        #print(f"schedule.every().day.at({str(start_hour).zfill(2) + ':00:00'}).do(lambda: start_hourly_tasks({dir_serie}, {acquisition_choices}, {stop_hour}, {total_hours}, {end_date_format}, {type_acquisition})).tag('daily-tasks')")
        # DAILY STOP: every days at stop time stop the hourly-tasks and analysis (= daily-tasks)
        schedule.every().day.at(str(stop_before_hour).zfill(2) + ':59:00').do(
            lambda: clear_hourly_tasks(type_acquisition)).tag('daily-tasks')
        #print(f"DEBUG {vf.get_formatted_datetime_now()}, <master_schedule_run> repeated, DAILY STOP, schedule.every().day. at({str(stop_before_hour) + ':59:00'}) do clear_hourly_tasks({type_acquisition}).tag('daily-tasks')")
        schedule.every().day.at(str(stop_before_hour).zfill(2) + ':59:20').do(
            lambda: stop_analysis(7200)).tag('daily-tasks')
        #print(f"DEBUG {vf.get_formatted_datetime_now()}, <master_schedule_run> repeated, DAILY STOP, schedule.every().day. at({str(stop_before_hour) + ':59:20'}) do stop_analysis(7200)).tag('daily-tasks')")
        schedule.every(int(duration)).days.at(str(stop_before_hour).zfill(2) + ':59:40').do(
            lambda: clear_daily_tasks(root, serie_name_entry, id_entry, test_cameras, cbox_channel, cbox_schedule, button_start_sched, button_stop_acq, button_stop_all, button_rad_continuous, button_rad_repeated))
        #print(f"DEBUG {vf.get_formatted_datetime_now()}, <master_schedule_run> repeated, FINAL STOP, schedule.every(int({duration})).days at({str(stop_before_hour) + ':59:40'}) do clear_daily_tasks(tkinter objects) )")

    #  Listen to all jobs and start them on scheduled time
    while schedule.jobs:
        schedule.run_pending()
        time.sleep(0.1)
    #print(f"DEBUG {vf.get_formatted_datetime_now()}, while loop finished")


def gui():
    "VASD graphical user interface"

    # CREATES GUI
    root = Tk()
    root.title("VASD, Video Acquisition and Seizure Detection")
    # Get window size
    screen_width = root.winfo_screenwidth()

    # Top frame
    top_frame = Frame(root,
                      borderwidth=3,
                      relief=RAISED,
                      background=vf.COLOR_MENU,
                     )
    top_frame.grid(row=0, column=0, sticky=W+E)
    Label(top_frame,
          text="VASD v"+vf.VASD_VERSION,
          font=vf.FONT_TITLE,
          background=vf.COLOR_MENU,
          foreground=vf.COLOR_TEXT_LIGHT,
          borderwidth=0,
          relief=FLAT,
         ).grid(row=0, column=0, pady=10, sticky=W+E)

    # Button frame
    menu_btn_frame = Frame(top_frame,
                           borderwidth=2,
                           relief=RIDGE,
                           background=vf.COLOR_MENU,
                          )   #frame with navigation buttons
    menu_btn_frame.grid(row=0, column=5, padx=40, pady=10, sticky=E)
    Button(menu_btn_frame,
           text="Help",
           font=vf.FONT_BUTTON,
           state="normal",
           background=vf.COLOR_BUTTON,
           activebackground=vf.COLOR_BUTTON_ACTIVE,
           command=lambda: vf.user_guide(vf.VASD_VERSION),
          ).grid(row=0, column=4, padx=40, pady=1, sticky=E)
    Button(menu_btn_frame,
           text="Exit",
           font=vf.FONT_BUTTON,
           state="normal",
           background=vf.COLOR_BUTTON,
           activebackground=vf.COLOR_BUTTON_ACTIVE,
           command=lambda: vf.exit_vasd(),
          ).grid(row=0, column=5, padx=40, pady=1, sticky=E)

    # Main frame
    main_frame = Frame(root,
                       borderwidth=3,
                       relief=RAISED,
                       background=vf.COLOR_BACKGROUND,
                       )
    main_frame.grid(row=1, column=0, sticky=W+E)
    var_radio = IntVar()            # for radio buttons : continuous (1) or repeat (2)
    var_radio.set(1)                # default choice : continuous
    channel_choices = []
    test_cameras = []
    label_cameras = []
    cbox_channel = []
    cbox_schedule = []
    id_entry = []

    # Creates tkinter objects
    # Entry of serie name (row 0)
    Label(main_frame,
          text="Serie name",
          font=vf.FONT_LABEL,
          foreground="black",
          background=vf.COLOR_BACKGROUND,
          borderwidth=1,
          relief=RIDGE,
          width=15,
          justify='left'
          ).grid(row=0, column=0, padx=3, pady=10, sticky=W)
    mydate = datetime.datetime.now()
    seriedate = mydate.strftime("%Y_%m_%d")
    Label(main_frame,
          text=f"/ {seriedate}_",
          font=vf.FONT_LABEL,
          foreground="black",
          background=vf.COLOR_BACKGROUND,
          borderwidth=0,
          width=15,
          justify='right'
          ).grid(row=0, column=1, padx=3, pady=10, sticky=E)
    serie_name_entry = Entry(main_frame,
                             width=15,
                             background=vf.COLOR_LISTBOX,
                             borderwidth=2,
                             relief=RIDGE,
                             font=vf.FONT_LISTBOX,
                             foreground='black',
                             justify='left'
                            )
    serie_name_entry.grid(row=0, column=2, padx=3, pady=3, sticky=W)
    Label(main_frame,
          text="For all entries, max 10 and only letters, digits, or dash (-)",
          font=vf.FONT_LABEL,
          background=vf.COLOR_MENU,
          foreground=vf.COLOR_TEXT_LIGHT,
          borderwidth=1,
          relief=RAISED,
          justify='center'
          ).grid(row=0, column=3, columnspan=2, padx=3, pady=10, sticky=E)

    # Choices of cameras (row 1)
    Label(main_frame,
          text="Camera(s) and side(s) to acquire",
          font=vf.FONT_LABEL,
          background=vf.COLOR_MENU,
          foreground=vf.COLOR_TEXT_LIGHT,
          borderwidth=1,
          relief=RAISED,
          justify='left'
          ).grid(row=1, column=0, columnspan=2, padx=3, pady=10, sticky=W)
    # Side labels
    label_mouse_id = Label(main_frame,
                           text="IDs",
                           font=vf.FONT_LABEL,
                           foreground="black",
                           background=vf.COLOR_BACKGROUND,
                           borderwidth=1,
                           relief=RIDGE,
                           width=15,
                           justify='center'
                           )
    label_mouse_id.grid(row=1, column=3, padx=3, pady=3)

    # Choices for cameras 1 to NB_CAMERAS (rows 2 to NB_CAMERAS+2)
    for i in range(0, vf.NB_CAMERAS):
        choices = ['No recording', '' + str(i) + '_Left', '' + str(i) + '_Right', '' + str(i) + '_Both', '' + str(i) + '_All']
        channel_choices.append(choices)
        test_cameras.append(Button(main_frame,
                                   text="Test camera "+ str(i),
                                   font=vf.FONT_BUTTON,
                                   state="normal",
                                   background=vf.COLOR_BUTTON,
                                   activebackground=vf.COLOR_BUTTON_ACTIVE,
                                   justify='center',
                                   command=partial(vf.test_stream, i, screen_width),
                                  )
                           )
        test_cameras[i].grid(row=i+2, column=0, padx=3, pady=3)
        label_cameras.append(Label(main_frame,
                                   text=str(i)+" : "+vf.CAMERA_TYPE[i]+'',
                                   font=vf.FONT_LABEL,
                                   foreground="black",
                                   background=vf.COLOR_BACKGROUND,
                                   borderwidth=1,
                                   justify='center',
                                   relief=RIDGE,
                                  )
                            )
        label_cameras[i].grid(row=i+2, column=1, padx=3, pady=3)
        cbox_channel.append(ttk.Combobox(main_frame,
                                         values=channel_choices[i],
                                         font=vf.FONT_LABEL,
                                         justify='center',
                                         width=15,
                                         state='readonly'
                                         )
                            )
        cbox_channel[i].grid(row=i+2, column=2, padx=3, pady=3)
        cbox_channel[i].current(0)
        id_entry.append(Entry(main_frame,
                              width=17,
                              background=vf.COLOR_LISTBOX,
                              borderwidth=2,
                              relief=RIDGE,
                              font=vf.FONT_LISTBOX,
                              foreground='black',
                              justify='center'
                             )
                       )
        id_entry[i].grid(row=i+2, column=3, padx=3, pady=3)

    # Scheduling label (row NB_CAMERAS+4)
    label_schedule_rec = Label(main_frame, text="Scheduling of acquisition",
                               font=vf.FONT_LABEL,
                               background=vf.COLOR_MENU,
                               foreground=vf.COLOR_TEXT_LIGHT,
                               justify='left',
                               relief=RAISED,
                               )
    label_schedule_rec.grid(row=vf.NB_CAMERAS+4, column=0, columnspan=2, padx=3, pady=20, sticky=W)

    # Choices for Start and Stop Time (row NB_CAMERAS+5)
    date_today = datetime.datetime.now() + datetime.timedelta(hours=1)    # Get next hour for default display
    hour_now_format = date_today.strftime('%H')
    label_schedule_start = Label(main_frame,
                                 text="Start time [hours]",
                                 font=vf.FONT_LABEL,
                                 foreground="black",
                                 background=vf.COLOR_BACKGROUND,
                                 borderwidth=1,
                                 relief=RIDGE,
                                 width=15,
                                 justify='center'
                                 )
    label_schedule_start.grid(row=vf.NB_CAMERAS+5, column=0, padx=3, pady=3, sticky=E)
    if hour_now_format in vf.SCHED_HOURS:
        index_select = vf.SCHED_HOURS.index(hour_now_format)
    cbox_schedule.append(ttk.Combobox(main_frame,
                                      values=vf.SCHED_HOURS[:],
                                      justify='center',
                                      width=15,
                                      state='readonly'
                                      )
                        )
    cbox_schedule[0].current(index_select)      # default start time is following hour
    cbox_schedule[0].grid(row=vf.NB_CAMERAS+5, column=1, padx=3, pady=3, sticky=W)
    label_schedule_stop = Label(main_frame,
                                text="Stop time [hours]",
                                font=vf.FONT_LABEL,
                                foreground="black",
                                background=vf.COLOR_BACKGROUND,
                                borderwidth=1,
                                relief=RIDGE,
                                width=15,
                                justify='right'
                                )
    label_schedule_stop.grid(row=vf.NB_CAMERAS+5, column=2, padx=3, pady=3, sticky=E)
    cbox_schedule.append(ttk.Combobox(main_frame,
                                      values=vf.SCHED_HOURS[:],
                                      justify='center',
                                      width=15,
                                      state='readonly'
                                      )
                        )
    cbox_schedule[1].current(0)
    cbox_schedule[1].grid(row=vf.NB_CAMERAS+5, column=3, padx=3, pady=3, sticky=W)   # stop time

    # Choices for Duration (row NB_CAMERAS+6)
    label_schedule_days = Label(main_frame,
                                text="Duration [days]",
                                font=vf.FONT_LABEL,
                                foreground="black",
                                background=vf.COLOR_BACKGROUND,
                                borderwidth=1,
                                relief=RIDGE,
                                width=15,
                                justify='center'
                                )
    label_schedule_days.grid(row=vf.NB_CAMERAS+6, column=0, padx=3, pady=3, sticky=E)
    cbox_schedule.append(ttk.Combobox(main_frame,
                                      values=vf.SCHED_DAYS[:],
                                      justify='center',
                                      width=15,
                                      state='readonly'
                                      )
                        )
    cbox_schedule[2].grid(row=vf.NB_CAMERAS+6, column=1, padx=3, pady=3, sticky=W)   # duration
    cbox_schedule[2].current(0)
    # Choices for continuous or repeated acquisition (row NB_CAMERAS+5)
    button_rad_continuous = Radiobutton(main_frame,
                                        text="Continuous",
                                        variable=var_radio,
                                        value=1,
                                        width=15,
                                        justify='center'
                                        )
    button_rad_continuous.grid(row=vf.NB_CAMERAS+6, column=2, padx=3, pady=3)
    button_rad_repeated = Radiobutton(main_frame,
                                      text="Repeated each day",
                                      variable=var_radio,
                                      value=2,
                                      width=15,
                                      justify='center'
                                      )
    button_rad_repeated.grid(row=vf.NB_CAMERAS+6, column=3, padx=3, pady=3)

    # Buttons Start Acquisition+Analysis and Stop Acquisition (row NB_CAMERAS+8)
    button_start_sched = Button(main_frame,
                                text="Start Acquisition+Analysis",
                                font=vf.FONT_BUTTON,
                                background=vf.COLOR_BUTTON,
                                activebackground=vf.COLOR_BUTTON_ACTIVE,
                                command=lambda: master_start_schedule(root, serie_name_entry, id_entry, test_cameras, cbox_channel,
                                                                      cbox_schedule, button_start_sched, button_stop_acq,
                                                                      button_stop_all, button_rad_continuous, button_rad_repeated, var_radio
                                                                      ),
                                justify='center',
                                state=ACTIVE
                                )
    button_start_sched.grid(row=vf.NB_CAMERAS+8, column=0, columnspan=2, padx=5, pady=30)
    # STOP ACQUISITION button: manually stop all acquisitions immediately, analysis will stop in 1 hour (stop_all=1)
    button_stop_acq = Button(main_frame,
                             text="Stop Acquisition",
                             font=vf.FONT_BUTTON,
                             background=vf.COLOR_BUTTON,
                             activebackground=vf.COLOR_BUTTON_ACTIVE,
                             command=lambda: master_stop_schedule(root, serie_name_entry, id_entry, test_cameras, cbox_channel,
                                                                  cbox_schedule, button_start_sched, button_stop_acq,
                                                                  button_stop_all, button_rad_continuous, button_rad_repeated, 1
                                                                  ),
                             justify='center',
                             state=DISABLED
                            )
    button_stop_acq.grid(row=vf.NB_CAMERAS+8, column=2, columnspan=2, padx=5, pady=30)
    # STOP ACQUISITION+ANALYSIS button: manually stop all acquisitions and analysis immediately (stop_all=2)
    button_stop_all = Button(main_frame,
                             text="Stop Acquisition+Analysis",
                             font=vf.FONT_BUTTON,
                             background=vf.COLOR_BUTTON,
                             activebackground=vf.COLOR_BUTTON_ACTIVE,
                             command=lambda: master_stop_schedule(root, serie_name_entry, id_entry, test_cameras, cbox_channel,
                                                                  cbox_schedule, button_start_sched, button_stop_acq,
                                                                  button_stop_all, button_rad_continuous, button_rad_repeated, 2
                                                                  ),
                             justify='center',
                             state=DISABLED
                            )
    button_stop_all.grid(row=vf.NB_CAMERAS+8, column=4, columnspan=2, padx=5, pady=30)

    root.mainloop()



############### MAIN START ####################
init(autoreset=True) # reset terminal color (default color=black)
if __name__ == "__main__":
    # Start user interface in a process
    # multiprocessing.set_start_method('spawn')
    vf.PROC_GUI = multiprocessing.Process(target=gui)
    vf.PROC_GUI.start()
    vf.PROC_GUI.join()
    print("end of script")