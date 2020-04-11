# get_ipython().run_line_magic('matplotlib', 'qt')
from os.path import exists, join
import os
import sys
from argparse import ArgumentParser
import matplotlib.pyplot as plt
plt.switch_backend('qt5Agg')
import json
import numpy as np

from DicomAnnotator.app.myApp import *
from DicomAnnotator.utils.namerules import *
from DicomAnnotator.utils.cofig_process import *

"""
Construct the ImgIDList
"""
def get_ImgIDList(root_dir):
    rst = []
    for root, dirs, files in os.walk(root_dir):     
        for file in files:
            if file.endswith('.dcm') or file.endswith('.tiff') or file.endswith('.png') or file.endswith('jpg') or file.endswith('jpeg'):
                # rst.append(join(root,file))
                rst.append(file)
    rst.sort()
    return rst

plt.close('all')

parser = ArgumentParser()
# parser.add_argument("-r", "--img-root-dir", type=str,
# 					help="the image root directory. Can't be empty or nonexisted. Default is images/", default= 'images')
# parser.add_argument("-f", "--csv-filename", type=str, default='results.csv',
# 					help="the csv file to read in and save on, default name is SpineLabels.csv. If there is no such file, the program will create the file after you press the save button in UI. Default is results.csv",)
# parser.add_argument("-z", "--zoom-scale", type=float,
# 					help="zoom basic scale, should > 1, default is 1.2", default=1.2)
parser.add_argument("-b", "--begin-image", default=None,
					help="begin at which image, default is the first untouched image. The range should be 0 to (# of images - 1). Begin with the default image if out of the range")
# parser.add_argument("-w", "--window-level-scale", default=1, type=float,
# 					help="window/level changing scale, the smaller, the slower, default is 1")
parser.add_argument("-u", "--upper-gray-relax-coeff", default=3, type=float,
					help="the max upper gray can be reached is {u * (grayscale of white of the images + 1) - 1} when window/level, default is 3")
parser.add_argument("-l", "--lower-gray-relax-coeff", default=2, type=float,
					help="the lower upper gray can be reached is {- l * (grayscale of white of the images + 1)} when window/level, default is 2")
parser.add_argument("-d", "--debug-mode", action="store_true",
					help="whether turn on debug model",)
parser.add_argument("-p", "--block-points", action="store_true",
					help="whether can place or remove points on images",)
parser.add_argument("-c", "--config_dir", default=os.getcwd(), type=str,
					help="whether can place or remove points on images",)
# parser.add_argument("-g", "--image-format", type=str, default='dcm',
# 					help="The image format. Currently only support dcm and tiff",)
args = parser.parse_args()

config_filepath = os.path.join(args.config_dir, 'DicomAnnotator', 'configurations.json')
configs = configuration_processing(config_filepath)

nr = nameRules(configs)

ImageIDList = get_ImgIDList(configs['input_directory'])
if len(ImageIDList) == 0:
    print('There is no image in the directory or the directory does not exist!')
    sys.exit()
if args.begin_image:
    args.begin_image = int(args.begin_image)
    if args.begin_image > len(ImageIDList):
        args.begin_image = None


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = SpineLabelingApp( ImageIDList,
                             configs,
                             nr,
                             begin=args.begin_image,
                             upper_gray_relax_coeff=args.upper_gray_relax_coeff,
                             lower_gray_relax_coeff=args.lower_gray_relax_coeff,
                             block_points=args.block_points,
                             debug_mode=args.debug_mode,
                           )
    main.setWindowTitle('Spine Labeling App')
    main.show()
    sys.exit(app.exec_())
