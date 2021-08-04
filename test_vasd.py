# -*- coding: utf-8 -*-
"Script to test VASD package, must be started from within /vasd directory"

import unittest
import os
import sys
import json
from pkgutil import iter_modules
# code to test
from vasd import video_analysis


class SimpleTestCase(unittest.TestCase):

    def test_packages(self):
        "Test if required packages are installed"

        def module_exists(module_name):
            return module_name in (name for loader, name, ispkg in iter_modules())

        test_passed = True
        required_packages = {
                             "cv2": "opencv-python",
                             "numpy": "numpy",
                             "schedule": "schedule",
                             "colorama": "colorama",
                             "ffprobe-python": "ffprobe-python"
                             }

        for package_name, pip_name in required_packages.items():
            if not module_exists(package_name):
                print(f"Needed package not installed, use command >pip install {pip_name} (or conda install {pip_name} if using anaconda)")
                test_passed = False
        assert test_passed, "Needed package import error"


    def test_read_write(self):
        "Test of reading/writing to parameters.json"

        test_passed = True
        params_pathfile = os.path.join(sys.path[0], 'params', 'parameters.json')
        try:
            with open(params_pathfile, 'r') as filereader:
                myparams = json.load(filereader)
        except IOError as json_error:
            print(f"Error reading {params_pathfile}")
            test_passed = False
        if myparams:
            try:
                with open(params_pathfile, 'w') as filewriter:
                    filewriter.write(json.dumps(myparams, indent=""))
            except IOError as json_error:
                print(f"Error writing to {params_pathfile}")
                test_passed = False
        assert test_passed, "Read/Write error to params/parameters.json, check file is present and not corrupted"


    def test_video_analysis(self):
        "Test of video analysis script with defaultvideo.mp4"
        # 4 ROIs set for defaultvideo.mp4"
        roi_coord = [[[0, 0], [500, 580]], [[501, 0], [998, 580]], [[0, 585], [500, 1158]], [[503, 583], [998, 1158]]]
        # fps, video_path, video_filename, roi coordinates, video index, total nb video
        data = [15, os.path.join(sys.path[0], "params"), "defaultvideo.mp4", roi_coord, 0, 1]
        sum_intensities = video_analysis.one_video_analysis(data)
        sum_intensities = round(sum_intensities, 1)
        assert (367. < sum_intensities < 369.), f"Video analysis error, sum {sum_intensities} not in range 367-369"


if __name__ == "__main__":
    unittest.main() # run all tests