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
from DicomAnnotator.app.sanity_check import *

import numpy as np
import copy

nr = nameRules()
ModuleName = nr.moduleName

class InfoStorageDicts:
    """
    The dictionaries used in the backend
    """

    def __init__(self, ImgIDList, csv_path):
        self.VBLabelList = nr.VBLabelList
        self.ImgIDList = ImgIDList
        self.fpath = csv_path
    
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
            VBDict = dict((vb, {nr.SupPostCoords:(None,None), \
                                nr.SupAntCoords:(None,None), \
                                nr.InfAntCoords:(None,None), \
                                nr.InfPostCoords:(None,None), \
                                nr.Fracture: self.ScoreSys.normal}) \
                       for vb in self.VBLabelList)
            hwDict = dict((vb, nr.nohardware) for vb in self.VBLabelList)
            self.StoreDict[ID] = VBDict
            self.StatusDict[ID] = nr.untouch
            self.ControversialDict[ID] = {nr.Modifier:None, nr.ConPart:'', nr.ConStatus:nr.uncontroversial}
            self.ReadableStatusDict[ID] = nr.readable
            self.HardwareStatusDict[ID] = hwDict
            self.OrientationDict[ID] = nr.face_user_left
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
                    if row[nr.head_status] != '':
                        self.StatusDict[row[nr.head_imgID]] = row[nr.head_status]
                        
                    if row[nr.head_SupPostX] != '' and row[nr.head_SupPostY] != '':
                        self.StoreDict[row[nr.head_imgID]][row[nr.head_vbLabel]][nr.SupPostCoords] = (float(row[nr.head_SupPostX]), float(row[nr.head_SupPostY]))
                    if row[nr.head_SupAntX] != '' and row[nr.head_SupAntY] != '':
                        self.StoreDict[row[nr.head_imgID]][row[nr.head_vbLabel]][nr.SupAntCoords] = (float(row[nr.head_SupAntX]), float(row[nr.head_SupAntY]))
                    if row[nr.head_InfAntX] != '' and row[nr.head_InfAntY] != '':
                        self.StoreDict[row[nr.head_imgID]][row[nr.head_vbLabel]][nr.InfAntCoords] = (float(row[nr.head_InfAntX]), float(row[nr.head_InfAntY]))
                    if row[nr.head_InfPostX] != '' and row[nr.head_InfPostY] != '':
                        self.StoreDict[row[nr.head_imgID]][row[nr.head_vbLabel]][nr.InfPostCoords] = (float(row[nr.head_InfPostX]), float(row[nr.head_InfPostY]))
                    
                    if row[nr.head_frac] != '':
                        self.StoreDict[row[nr.head_imgID]][row[nr.head_vbLabel]][nr.Fracture] = row[nr.head_frac]
                    if row[nr.head_modifier] != '':
                        self.ControversialDict[row[nr.head_imgID]][nr.Modifier] = row[nr.head_modifier]
                    
                    if row[nr.head_conParts] != '':
                        self.ControversialDict[row[nr.head_imgID]][nr.ConPart] = row[nr.head_conParts]
                    if row[nr.head_conStatus] != '':
                        self.ControversialDict[row[nr.head_imgID]][nr.ConStatus] = row[nr.head_conStatus]
                    if row[nr.head_readableStatus] != '':
                        self.ReadableStatusDict[row[nr.head_imgID]] = row[nr.head_readableStatus]
                    if row[nr.head_hardwareStatus] != '':
                        self.HardwareStatusDict[row[nr.head_imgID]][row[nr.head_vbLabel]] = row[nr.head_hardwareStatus]
                    if row[nr.head_orientation] != '':
                        self.OrientationDict[row[nr.head_imgID]] = row[nr.head_orientation]
                    if row[nr.head_ostLabeling] != '':
                        self.OstLabelingDict[row[nr.head_imgID]] = row[nr.head_ostLabeling]
                        
                    if row[nr.head_min_intensity] != '' and row[nr.head_max_intensity] != '':
                        self.WindowLevelDict[row[nr.head_imgID]] = (float(row[nr.head_min_intensity]), float(row[nr.head_max_intensity]))

                    if row[nr.head_inverse_gray] == 'True':
                        self.InverseGrayDict[row[nr.head_imgID]] = True
