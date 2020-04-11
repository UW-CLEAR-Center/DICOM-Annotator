from os.path import exists, join
import os
import csv
import sys
import time
import math

from PyQt5.QtWidgets import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backend_bases import Event as pltEvent
from PyQt5 import QtCore, QtGui

from DicomAnnotator.utils.namerules import *
from DicomAnnotator.app.instructions import *

import numpy as np
import copy

class InfoStorageDicts:
    """
    The dictionaries used in the backend
    """

    def __init__(self, ImgIDList, csv_path, configs, nameRules):
        self.VBLabelList = configs['region_identifier_list']
        self.ImgIDList = ImgIDList
        self.fpath = csv_path
        self.configs = configs
        self.nr = nameRules
    
    def _empty_dicts(self):
        """
        Construct the empty dicts
        """
        self.StoreDict = {}
        self.StatusDict = {}
        self.ControversialDict = {}
        self.ReadableStatusDict = {}
        self.HardwareStatusDict = {}
        self.OrientationDict = {}
        self.OstLabelingDict = {}
        self.WindowLevelDict = {}
        self.InverseGrayDict = {}
        for ID in self.ImgIDList:
            temp_dict = {}
            for name in self.configs['bounding_polygon_vertices_names']:
                temp_dict[name] = (None, None)
            temp_dict[self.nr.Fracture] = self.ScoreSys.default
            VBDict = dict((vb, temp_dict.copy()) \
                       for vb in self.VBLabelList)
            hwDict = dict((vb, self.nr.nohardware) for vb in self.VBLabelList)
            self.StoreDict[ID] = VBDict
            self.StatusDict[ID] = self.nr.untouch
            self.ControversialDict[ID] = {self.nr.Modifier:None, self.nr.ConPart:'', self.nr.ConStatus:self.nr.uncontroversial}
            self.ReadableStatusDict[ID] = self.nr.readable
            self.HardwareStatusDict[ID] = hwDict
            self.OrientationDict[ID] = self.nr.face_user_left
            self.OstLabelingDict[ID] = None
            self.WindowLevelDict[ID] = (None, None)
            self.InverseGrayDict[ID] = False


    
    def dict_constructor(self):
        """
        Read the csv file and construct StoreDict and Status Dict;
        will initiate when click start button
        """
        self._empty_dicts()
        if exists(self.fpath):
            with open(self.fpath) as csv_file:
                reader = csv.DictReader(csv_file)
                for row in reader:
                    if row[self.nr.head_status] != '':
                        self.StatusDict[row[self.nr.head_imgID]] = row[self.nr.head_status]
                    for i, coord in enumerate(self.configs['bounding_polygon_vertices_names']):
                        head_X = self.nr.head_vertices[int(2 * i)]
                        head_Y = self.nr.head_vertices[int(2 * i + 1)]
                        if row[head_X] != '' and row[head_Y] != '':
                            self.StoreDict[row[self.nr.head_imgID]][row[self.nr.head_vbLabel]][coord] = (float(row[head_X]), float(row[head_Y]))
                    
                    if row[self.nr.head_frac] != '':
                        self.StoreDict[row[self.nr.head_imgID]][row[self.nr.head_vbLabel]][self.nr.Fracture] = row[self.nr.head_frac]
                    if row[self.nr.head_modifier] != '':
                        self.ControversialDict[row[self.nr.head_imgID]][self.nr.Modifier] = row[self.nr.head_modifier]
                    
                    if row[self.nr.head_conParts] != '':
                        self.ControversialDict[row[self.nr.head_imgID]][self.nr.ConPart] = row[self.nr.head_conParts]
                    if row[self.nr.head_conStatus] != '':
                        self.ControversialDict[row[self.nr.head_imgID]][self.nr.ConStatus] = row[self.nr.head_conStatus]
                    if row[self.nr.head_readableStatus] != '':
                        self.ReadableStatusDict[row[self.nr.head_imgID]] = row[self.nr.head_readableStatus]
                    if row[self.nr.head_hardwareStatus] != '':
                        self.HardwareStatusDict[row[self.nr.head_imgID]][row[self.nr.head_vbLabel]] = row[self.nr.head_hardwareStatus]
                    if row[self.nr.head_orientation] != '':
                        self.OrientationDict[row[self.nr.head_imgID]] = row[self.nr.head_orientation]
                    if row[self.nr.head_ostLabeling] != '':
                        self.OstLabelingDict[row[self.nr.head_imgID]] = row[self.nr.head_ostLabeling]
                        
                    if row[self.nr.head_min_intensity] != '' and row[self.nr.head_max_intensity] != '':
                        self.WindowLevelDict[row[self.nr.head_imgID]] = (float(row[self.nr.head_min_intensity]), float(row[self.nr.head_max_intensity]))

                    if row[self.nr.head_inverse_gray] == 'True':
                        self.InverseGrayDict[row[self.nr.head_imgID]] = True
