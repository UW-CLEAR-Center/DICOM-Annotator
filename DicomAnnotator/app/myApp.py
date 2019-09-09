import SimpleITK as sitk
import tifffile as tiff
import matplotlib.pyplot as plt
from IPython.display import display

import csv
import sys
import time
import math
from os.path import join

from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui

from DicomAnnotator.utils.namerules import *
from DicomAnnotator.app.instructions import *
from DicomAnnotator.app.sanity_check import *
from DicomAnnotator.app.layouts import AppLayouts
from DicomAnnotator.app.storage_dicts import InfoStorageDicts

import numpy as np

nr = nameRules()
ModuleName = nr.moduleName
tt = toolTips()
with open(ModuleName+'/app/instructions.html') as f:
    instructions = f.read()

def display_decor( func ):
    '''
    A decorator function to skip the unreadable images and display the new image
    '''
    def wrapper(*args):
        self = args[0]
        oriImgPointer = self.ImgPointer
        func(self)
        curImgPointer = self.ImgPointer
        while self.ReadableStatusDict[self.ImgIDList[self.ImgPointer]] == nr.unreadable:
            func(self)
            if self.ImgPointer == curImgPointer:
                self.ImgPointer = oriImgPointer
                return
        if oriImgPointer != curImgPointer:
            self.init_display()
        # disable these widgets if prohibit to modify points
        if self.block_points:
            self.clearall_button.setEnabled(False)
            for i in range(len(self.VBLabelList)):
                self.clear_coords_btns[i].setEnabled(False)
                self.clear_point_btns[i].setEnabled(False)
                self.clear_last_btns[i].setEnabled(False)

    return wrapper


def unsave_decor(func):
    '''
    A decorator function to change the save_status_label to unsaved
    '''
    def wrapper(*args):
        self = args[0]       
        func(*args)
        if not self.init_display_flag and self.mode == nr.edit:
            self.save_status = nr.unsaved
            self.update_save_status_label()
    return wrapper

class SpineLabelingApp(AppLayouts, InfoStorageDicts, QDialog):

    def __init__(self,
                 ImgIDList, ImageDir,
                 csv_path,
                 mainPageColumnStretch=[1,10,3],
                 zoom_base_scale=1.2,
                 wl_scale=5,
                 key_wl_scale=20,
                 upper_gray_relax_coeff=3,
                 lower_gray_relax_coeff=2,
                 block_points=False,
                 debug_mode=False,
                 begin=None,
                 parent=None,
                 ):
        self.count = 0
        AppLayouts.__init__(self, ImgIDList, mainPageColumnStretch)
        InfoStorageDicts.__init__(self, ImgIDList, csv_path)
        QDialog.__init__(self, parent)

        self.ImageDir = ImageDir

        self.zoom_base_scale = zoom_base_scale
        self.wl_scale = wl_scale / 10
        self.key_wl_scale = key_wl_scale
        self.acc_zoom_scale = 1 # accumulative zooming scale
        self.upper_gray_relax_coeff = upper_gray_relax_coeff
        self.lower_gray_relax_coeff = lower_gray_relax_coeff

        self.block_points = block_points
        self.debug_mode = debug_mode

        self.time_log_file = nr.temp_filename[3]
        self.begin = begin
        self.num_unreadable = 0       

        self.VBPointer = 0 # the current processed VB, init as L1 
        self.mode = nr.edit # current mode: edit or view
        self.cursor =QtGui.QCursor() # mouse cursor

        self.init_display_flag = True
        self.is_update_table = False
        self.is_update_ost_label = False
        self.last_labeled = None # last labeled vb and corner: (vb, corner)
        self.is_start_ui = True # at the beginning, we will in the start page
        self.start_ui()
        self.start_page_button_function_connecting()


    def start_page_button_function_connecting(self):
        self.tab_order_radiobuttons1.toggled.connect(
            lambda:self.tab_order_radiobutton_on_change1(self.tab_order_radiobuttons1))
        self.tab_order_radiobuttons2.toggled.connect(
            lambda:self.tab_order_radiobutton_on_change2(self.tab_order_radiobuttons2))
        self.start_button.clicked.connect(self.start_button_on_click)

    def main_page_button_function_connecting(self):
        self.unreadable_button.clicked.connect(self.unreadable_button_on_click)
        self.flip_image_button.clicked.connect(self.flip_image_button_on_click)
        self.comment_submit_button.clicked.connect(self.comment_button_on_click)
        self.setcon_button.clicked.connect(self.setcon_button_on_click)
        self.resetcon_button.clicked.connect(self.resetcon_button_on_click)
        self.comment_clear_button.clicked.connect(self.comment_clear_button_on_click)
        self.prevcon_button.clicked.connect(self.prevcon_button_on_click)
        self.nextcon_button.clicked.connect(self.nextcon_button_on_click)
        self.prev_button.clicked.connect(self.prev_button_on_click)
        self.next_button.clicked.connect(self.next_button_on_click)
        self.prevun_button.clicked.connect(self.prevun_button_on_click)
        self.nextun_button.clicked.connect(self.nextun_button_on_click)
        self.help_button.clicked.connect(self.help_button_on_click)
        self.clearall_button.clicked.connect(self.clear_all_button_on_click)
        self.home_button.clicked.connect(self.home_button_on_click)
        self.save_button.clicked.connect(self.save)
        self.mode_radiobuttons1.toggled.connect(
            lambda:self.mode_radiobuttons_on_change(self.mode_radiobuttons1))
        self.mode_radiobuttons2.toggled.connect(
            lambda:self.mode_radiobuttons_on_change(self.mode_radiobuttons2))
        self.points_off_on_button.clicked.connect(self.points_off_on_button_on_click)
        self.inverse_gray_button.clicked.connect(self.inverse_gray_button_on_click)
        for radiobutton in self.ost_radiobuttons:
            radiobutton.toggled.connect(lambda:self.ost_rb_on_change(radiobutton))
        # self.ost_radiobuttons1.toggled.connect(lambda:self.ost_rb_on_change(self.ost_radiobuttons1))
        # self.ost_radiobuttons2.toggled.connect(lambda:self.ost_rb_on_change(self.ost_radiobuttons2))
        # self.ost_radiobuttons3.toggled.connect(lambda:self.ost_rb_on_change(self.ost_radiobuttons3))
        for i, vb in enumerate(self.VBLabelList):
            self.clear_point_btns[i].clicked.connect(self.clear_button_on_click)
            self.clear_coords_btns[i].clicked.connect(self.clear_coords_btns_on_click)
            self.clear_last_btns[i].clicked.connect(self.clear_last_btns_on_click)
            co = 0
            for j, l in enumerate(self.fx_labels):
                if l == None:
                    continue
                self.frac_rbs[i][co].toggled.connect(
                    lambda state, arg=self.frac_rbs[i][co]: self.on_frac_radiobuttons_change(arg))
                co += 1
            self.coords_tables[i].currentChanged.connect(self.on_coords_tab_change)
            self.hardware_checkboxes[i].stateChanged.connect(self.hardware_checkbox_state_change)
        self.table.currentChanged.connect(self.on_tab_change)


    def init_display(self, should_compare_users=True):
        """
        Display the current image
        should_compare_users: if we want to check whether the current user and the last modifier are the same to determine the mode
        """
        self.init_display_flag = True
        cur_image = self.ImgIDList[self.ImgPointer]
        
        # deal with the mode radiobutton
        ## if current user and last modifier are different, use view mode
        if should_compare_users:
            if self.ControversialDict[cur_image][nr.Modifier] != None and self.ControversialDict[cur_image][nr.Modifier] != self.username:
                self.mode_radiobuttons2.setChecked(True)

        self.VBPointer = 0
        # Get the grey value of the image as a numpy array
        if self.ImgIDList[self.ImgPointer].split('.')[-1] == 'dcm':
            self.img = sitk.ReadImage(join(self.ImageDir, self.ImgIDList[self.ImgPointer]))[:,:,0]
            self.npa = sitk.GetArrayViewFromImage(self.img)
        elif self.ImgIDList[self.ImgPointer].split('.')[-1] == 'tiff':
            self.npa = tiff.imread(join(self.ImageDir, self.ImgIDList[self.ImgPointer]))
        possible_max_gray = 2**(math.ceil(math.log2(np.max(self.npa+1)))) -1
        if self.InverseGrayDict[cur_image]:
            self.npa = np.max(self.npa)-self.npa#sitk.GetArrayViewFromImage(self.img)

        # self.prevCursorLoc = self.npa.shape[0]/2, self.npa.shape[1]/2
        self.prevCursorLoc = self.cursor.pos().x(), self.cursor.pos().y()#event.xdata, event.ydata
        
        # flip the image if necessary
        if self.OrientationDict[cur_image] == nr.face_user_right:
            self.npa = np.fliplr(self.npa)
    
        self.min_intensity = self.npa.min()
        self.max_intensity = self.npa.max()
        self.max_gray_value = self.upper_gray_relax_coeff * np.power(2, np.ceil(np.log2(self.max_intensity + 1)))-1
        self.min_gray_value = -self.lower_gray_relax_coeff * np.power(2, np.ceil(np.log2(self.max_intensity + 1)))
        self.gray_range = self.max_gray_value - self.min_gray_value
        
        self.axes.set_xlim(0,len(self.npa[0]))
        self.axes.set_ylim(len(self.npa),0)

        cur_image = self.ImgIDList[self.ImgPointer]
        
        self.update_status()
        self.update_controversial_ui()
        self.update_display()
        self.table.setCurrentIndex(self._init_tab_index())
        self.update_table()
        self.update_coord_tabs()
        self.update_frac_vb_label()
        self.update_save_status_label()
        self.update_ost_labeling()
        
        plt.tight_layout()
        self.init_display_flag = False
    
    def _is_complete_label_unlabel(self, vb):
        """
        if a vb is completely labelled or unlabelled
        0 for totally unlabled,
        2 for totally labeled,
        otherwise 1
        """
        cur_image = self.ImgIDList[self.ImgPointer]
        
        if vb != 'S1':
            if self.StoreDict[cur_image][vb][nr.SupPostCoords] == (None, None) \
            and self.StoreDict[cur_image][vb][nr.SupAntCoords] == (None, None) \
            and self.StoreDict[cur_image][vb][nr.InfAntCoords] == (None, None) \
            and self.StoreDict[cur_image][vb][nr.InfPostCoords] == (None, None):
                return 0

            if self.StoreDict[cur_image][vb][nr.SupPostCoords] != (None, None) \
            and self.StoreDict[cur_image][vb][nr.SupAntCoords] != (None, None) \
            and self.StoreDict[cur_image][vb][nr.InfAntCoords] != (None, None) \
            and self.StoreDict[cur_image][vb][nr.InfPostCoords] != (None, None):
                return 2

            return 1
        if self.StoreDict[cur_image][vb][nr.SupPostCoords] == (None, None) \
        and self.StoreDict[cur_image][vb][nr.SupAntCoords] == (None, None):
            return 0

        if self.StoreDict[cur_image][vb][nr.SupPostCoords] != (None, None) \
        and self.StoreDict[cur_image][vb][nr.SupAntCoords] != (None, None):
            return 2

        return 1
    
    def _init_tab_index(self):
        flags = []
        for vb in self.VBLabelList:
            flags.append(self._is_complete_label_unlabel(vb))
        
        if 1 in flags:
            if self.tabOrder:
                return flags.index(1)
            else:
                return len(self.VBLabelList) - 1 - flags.index(1)
        if all(f == 0 for f in flags) or all(f == 2 for f in flags):
            if self.tabOrder:
                return 0
            else:
                return len(self.VBLabelList) - 1
        _had_2_before = False
        for i, f in enumerate(flags):
            if f == 2:
                _had_2_before = True
            elif _had_2_before:
                if self.tabOrder:
                    return i
                else:
                    return len(self.VBLabelList) - 1 - i
        if self.tabOrder:
            return 0
        else:
            return len(self.VBLabelList) - 1

    def update_display(self):
        """
        Update the display if there is any operation
        """
        cur_imgID = self.ImgIDList[self.ImgPointer]
        # We want to keep the zoom factor which was set prior to display, so we log it before
        # clearing the axes.
        xlim = self.axes.get_xlim()
        ylim = self.axes.get_ylim()
        # Draw the image and localized points.
        self.axes.clear()
        if self.WindowLevelDict[cur_imgID][0] == None or self.WindowLevelDict[cur_imgID][1] == None:
            self.WindowLevelDict[cur_imgID] = (self.min_intensity, self.max_intensity)
            self.cur_min_intensity = self.min_intensity
            self.cur_max_intensity = self.max_intensity
        else:
            self.cur_min_intensity = self.WindowLevelDict[cur_imgID][0]
            self.cur_max_intensity = self.WindowLevelDict[cur_imgID][1]

        self.axes.imshow(self.npa,
                         cmap=plt.cm.Greys_r,
                         vmin=self.cur_min_intensity,
                         vmax=self.cur_max_intensity)
        # Positioning the text is a bit tricky, we position relative to the data coordinate system, but we
        # want to specify the shift in pixels as we are dealing with display. We therefore (a) get the data 
        # point in the display coordinate system in pixel units (b) modify the point using pixel offset and
        # transform back to the data coordinate system for display.
        text_x_offset = 6
        text_y_offset = -8
        text_font = 10       
        marker_size = 40
        
        SupPostPnts = []
        SupAntPnts = []
        InfAntPnts = []
        InfPostPnts = []
        colors = []
        
        if self.points_off_on_status != 0:
            for vb in self.VBLabelList:
                if self.StoreDict[cur_imgID][vb][nr.Fracture] == self.ScoreSys.normal:
                    color = 'yellow'
                elif self.StoreDict[cur_imgID][vb][nr.Fracture] in self.ost_fx:
                    color = 'orange'
                elif self.ScoreSys.non_ost_deform != None and self.StoreDict[cur_imgID][vb][nr.Fracture] == self.ScoreSys.non_ost_deform:
                    color = 'green'
                colors.append(color)
                SupPostPnts.append(self.StoreDict[cur_imgID][vb][nr.SupPostCoords])
                SupAntPnts.append(self.StoreDict[cur_imgID][vb][nr.SupAntCoords])
                InfAntPnts.append(self.StoreDict[cur_imgID][vb][nr.InfAntCoords])
                InfPostPnts.append(self.StoreDict[cur_imgID][vb][nr.InfPostCoords])

            SupPostPnts = np.array(SupPostPnts, dtype=float)
            SupAntPnts = np.array(SupAntPnts, dtype=float)
            InfAntPnts = np.array(InfAntPnts, dtype=float)
            InfPostPnts = np.array(InfPostPnts, dtype=float)
   
            if self.points_off_on_status == 2: 
                self.axes.scatter(
                    SupPostPnts[:,0], SupPostPnts[:,1], s=marker_size, color=colors, marker='+')
                self.axes.scatter(
                    SupAntPnts[:,0], SupAntPnts[:,1], s=marker_size, color=colors, marker='*')
                self.axes.scatter(
                    InfAntPnts[:,0], InfAntPnts[:,1], s=marker_size, color=colors, marker='.')
                self.axes.scatter(
                    InfPostPnts[:,0], InfPostPnts[:,1], s=marker_size, color=colors, marker='X')

                allPnts = np.concatenate([SupPostPnts, SupAntPnts, InfAntPnts, InfPostPnts], axis = 0)
                text_in_data = self.axes.transData.transform(allPnts)
                text_in_data[:,0] += text_x_offset
                text_in_data[:,1] += text_y_offset
                text_in_data_coords = self.axes.transData.inverted().\
                    transform(text_in_data)
                vb_offset = len(self.VBLabelList)
                for i, vb in enumerate(self.VBLabelList):
                    if (not np.isnan(text_in_data_coords[i,0])) and (not np.isnan(text_in_data_coords[i,1])):
                        self.axes.text(
                            text_in_data_coords[i,0], text_in_data_coords[i,1], vb, color=colors[i], fontsize=text_font)
                    if (not np.isnan(text_in_data_coords[i+vb_offset,0])) and (not np.isnan(text_in_data_coords[i+vb_offset,1])):
                        self.axes.text(
                            text_in_data_coords[i+vb_offset,0], text_in_data_coords[i+vb_offset,1], vb, color=colors[i], fontsize=text_font)
                    if (not np.isnan(text_in_data_coords[i+2*vb_offset,0])) and (not np.isnan(text_in_data_coords[i+2*vb_offset,1])):
                        self.axes.text(
                            text_in_data_coords[i+2*vb_offset,0], text_in_data_coords[i+2*vb_offset,1], vb, color=colors[i], fontsize=text_font)
                    if (not np.isnan(text_in_data_coords[i+3*vb_offset,0])) and (not np.isnan(text_in_data_coords[i+3*vb_offset,1])):
                        self.axes.text(
                            text_in_data_coords[i+3*vb_offset,0], text_in_data_coords[i+3*vb_offset,1], vb, color=colors[i], fontsize=text_font)
            elif self.points_off_on_status == 1:
                allPnts = np.array([SupPostPnts, SupAntPnts, InfAntPnts, InfPostPnts])
                allnan_mask = np.all(np.isnan(allPnts), axis=(1,2))
                allPnts = allPnts[~allnan_mask]
                text_in_data_coords = np.nanmean(allPnts, axis=0)
                for i, vb in enumerate(self.VBLabelList):
                    if (not np.isnan(text_in_data_coords[i,0])) and (not np.isnan(text_in_data_coords[i,1])):
                        self.axes.text(
                            text_in_data_coords[i,0], text_in_data_coords[i,1], vb, color=colors[i], fontsize=text_font)
            
        if not self.debug_mode:
            self.axes.set_axis_off()

        # Set the zoom factor back to what it was before we cleared the axes, and rendered our data.
        self.axes.set_xlim(xlim)
        self.axes.set_ylim(ylim)

        self.fig.canvas.draw_idle()

    def update_table(self):
        """
        Update the table
        """
        self.is_update_table = True
        cur_imgID = self.ImgIDList[self.ImgPointer]
        cur_sdict = self.StoreDict[cur_imgID]
        origin_imgpointer = self.VBPointer

        for i, vb in enumerate(self.VBLabelList):
            self.VBPointer = i
            is_set_asterisk = True # if all coords are lablled, then set an asterisk
            if cur_sdict[vb][nr.SupPostCoords][0] != None:
                self.cor_X_Label[0][i].setText(str(cur_sdict[vb][nr.SupPostCoords][0]))
            else:
                self.cor_X_Label[0][i].setText('None')
                is_set_asterisk = False
            if cur_sdict[vb][nr.SupPostCoords][1] != None:
                self.cor_Y_Label[0][i].setText(str(cur_sdict[vb][nr.SupPostCoords][1]))
            else:
                self.cor_Y_Label[0][i].setText('None')
                is_set_asterisk = False
                
            if cur_sdict[vb][nr.SupAntCoords][0] != None:
                self.cor_X_Label[1][i].setText(str(cur_sdict[vb][nr.SupAntCoords][0]))
            else:
                self.cor_X_Label[1][i].setText('None')
                is_set_asterisk = False
            if cur_sdict[vb][nr.SupAntCoords][1] != None:
                self.cor_Y_Label[1][i].setText(str(cur_sdict[vb][nr.SupAntCoords][1]))
            else:
                self.cor_Y_Label[1][i].setText('None')
                is_set_asterisk = False
                
            if cur_sdict[vb][nr.InfAntCoords][0] != None:
                self.cor_X_Label[2][i].setText(str(cur_sdict[vb][nr.InfAntCoords][0]))
            elif vb != 'S1':
                self.cor_X_Label[2][i].setText('None')
                is_set_asterisk = False
            if cur_sdict[vb][nr.InfAntCoords][1] != None:
                self.cor_Y_Label[2][i].setText(str(cur_sdict[vb][nr.InfAntCoords][1]))
            elif vb != 'S1':
                self.cor_Y_Label[2][i].setText('None')
                is_set_asterisk = False
                
            if cur_sdict[vb][nr.InfPostCoords][0] != None:
                self.cor_X_Label[3][i].setText(str(cur_sdict[vb][nr.InfPostCoords][0]))
            elif vb != 'S1':
                self.cor_X_Label[3][i].setText('None')
                is_set_asterisk = False
            if cur_sdict[vb][nr.InfPostCoords][1] != None:
                self.cor_Y_Label[3][i].setText(str(cur_sdict[vb][nr.InfPostCoords][1]))
            elif vb != 'S1':
                self.cor_Y_Label[3][i].setText('None')
                is_set_asterisk = False
            
            if self.tabOrder:
                index = i
            else:
                index = len(self.VBLabelList) - 1 - i
            if is_set_asterisk:
                self.table.tabBar().setTabTextColor(index, QtCore.Qt.blue)
            else:
                self.table.tabBar().setTabTextColor(index, QtCore.Qt.black)
            if self.HardwareStatusDict[cur_imgID][vb] == nr.hardware:
                self.table.tabBar().setTabTextColor(index, QtCore.Qt.green)
            
            if cur_sdict[vb][nr.Fracture] != None:
                co = 0
                for j, label in enumerate(self.fx_labels):
                    if label != None:
                        if cur_sdict[vb][nr.Fracture] == label:
                            self.frac_rbs[i][co].setChecked(True)
                            break
                        co += 1
            else:
                self.frac_rbs[index][0].setChecked(True)
            
        self.update_hardware_checkboxes()
                    
        self.VBPointer = origin_imgpointer
        self.is_update_table = False

    def update_status(self):     
        """
        update the status dict
        """   
        cur_imgID = self.ImgIDList[self.ImgPointer]
        
        if self.ReadableStatusDict[cur_imgID] == nr.unreadable:
            return
        
        cur_sdict = self.StoreDict[cur_imgID]

        flag = False
        for vb in self.VBLabelList:
            if cur_sdict[vb][nr.SupPostCoords][0] != None \
                or cur_sdict[vb][nr.SupPostCoords][1] != None \
                or cur_sdict[vb][nr.SupAntCoords][0] != None \
                or cur_sdict[vb][nr.SupAntCoords][1] != None \
                or cur_sdict[vb][nr.InfAntCoords][0] != None \
                or cur_sdict[vb][nr.InfAntCoords][1] != None \
                or cur_sdict[vb][nr.InfPostCoords][0] != None \
                or cur_sdict[vb][nr.InfPostCoords][1] != None \
                or self.HardwareStatusDict[cur_imgID] == nr.hardware:
                self.StatusDict[cur_imgID] = nr.touch
                flag = True
                break

        if not flag:
            self.StatusDict[cur_imgID] = nr.untouch

        # update the status label in the UI
        if self.StatusDict[cur_imgID] == nr.untouch:
            status_text = 'untouched'
        else:
            status_text = 'touched'
        self.status_label.setText('Status: '+status_text)
        # update the num_labelled label in the UI
        num_u = 0
        for ID in self.ImgIDList:
            if self.StatusDict[ID] == nr.untouch:
                num_u += 1
        self.num_labelled_label.setText('Untouched/Total: '+str(num_u)+'/'+str(len(self.ImgIDList)-self.num_unreadable))
        self.ImgeID_label.setText('Image '+str(self.ImgPointer+1)+':\n'+self.ImgIDList[self.ImgPointer])

        # updaet last modifier label
        text = 'Last Modifier: '
        if self.ControversialDict[cur_imgID][nr.Modifier] != None:
            text += self.ControversialDict[cur_imgID][nr.Modifier] 
        else:
            text += 'None'
        self.modifier_label.setText(text)

    def update_controversial_ui(self):
        '''
        update controversial ui
        '''
        cur_imgID = self.ImgIDList[self.ImgPointer]
        # update controversial label
        if self.ControversialDict[cur_imgID][nr.ConStatus] == nr.controversial:
            self.controversial_label.setText('Do you want to unflag the image?')
            self.setcon_button.setEnabled(False)
            self.resetcon_button.setEnabled(True)
            self.controversial_label.setStyleSheet('color: red')
        else:
            self.controversial_label.setText('Do you want to flag the image?    ')
            self.setcon_button.setEnabled(True)
            self.resetcon_button.setEnabled(False)
            self.controversial_label.setStyleSheet('color: black')
            
        # updaet comment label
        if self.ControversialDict[cur_imgID][nr.ConPart] != '':
            self.comment_label.setText('Comments:\n'+ self.ControversialDict[cur_imgID][nr.ConPart])
        else:
            self.comment_label.setText('\n\n\n\n')
        # update textbox
        self.comment_textbox.setText('')

    def update_coord_tabs(self):
        """
        update coord tabs
        """
        cur_imgID = self.ImgIDList[self.ImgPointer]
        cur_sdict = self.StoreDict[cur_imgID]
        cur_vb = self.VBLabelList[self.VBPointer]
        self.CoordType = self.CoordTypeList[0]
        self.coords_tables[self.VBPointer].setCurrentIndex(0)
        if cur_sdict[cur_vb][nr.SupPostCoords][0] == None or cur_sdict[cur_vb][nr.SupPostCoords][1] == None:
            self.CoordType = self.CoordTypeList[0]
            self.coords_tables[self.VBPointer].setCurrentIndex(0)
        elif cur_sdict[cur_vb][nr.SupAntCoords][0] == None or cur_sdict[cur_vb][nr.SupAntCoords][1] == None:
            self.CoordType = self.CoordTypeList[1]
            self.coords_tables[self.VBPointer].setCurrentIndex(1)
        elif cur_vb != 'S1' \
        and (cur_sdict[cur_vb][nr.InfAntCoords][0] == None or cur_sdict[cur_vb][nr.InfAntCoords][1] == None):
            self.CoordType = self.CoordTypeList[2]
            self.coords_tables[self.VBPointer].setCurrentIndex(2)
        elif cur_vb != 'S1' \
        and (cur_sdict[cur_vb][nr.InfPostCoords][0] == None or cur_sdict[cur_vb][nr.InfPostCoords][1] == None):
            self.CoordType = self.CoordTypeList[3]
            self.coords_tables[self.VBPointer].setCurrentIndex(3)
                    
    def update_frac_vb_label(self):
        """
        update fracture VB lable
        """
        cur_imgID = self.ImgIDList[self.ImgPointer]
        cur_sdict = self.StoreDict[cur_imgID]

        text_ost = ''
        text_normal = ''
        text_nonost = ''
        for i, vb in enumerate(self.VBLabelList):
            if cur_sdict[vb][nr.Fracture] in self.ost_fx:
                text_ost += vb + ' '
            elif cur_sdict[vb][nr.Fracture] == self.ScoreSys.normal:
                text_normal += vb + ' '
            elif self.ScoreSys.non_ost_deform != None and cur_sdict[vb][nr.Fracture] == self.ScoreSys.non_ost_deform:
                text_nonost += vb + ' '
        self.frac_vb_label.setText(text_ost)
        self.normal_vb_label.setText(text_normal)
        if self.ScoreSys.non_ost_deform != None:
            self.nonost_vb_label.setText(text_nonost)

    def update_save_status_label(self):
        '''
        update save status label
        '''
        if self.save_status == nr.saved:
            color = 'black'
        else:
            color = 'red'
        self.save_status_label.setText(self.save_status)
        self.save_status_label.setStyleSheet('color: '+ color)
    
    def update_hardware_checkboxes(self):
        '''
        update hardware checkbox
        '''
        self.is_update_hw_cbx = True
        cur_imgID = self.ImgIDList[self.ImgPointer]
        
        for i, vb in enumerate(self.VBLabelList):
            if self.tabOrder:
                index = i
            else:
                index = len(self.VBLabelList) - 1 - i
            if self.HardwareStatusDict[cur_imgID][vb] != None:
                if self.HardwareStatusDict[cur_imgID][vb] == nr.nohardware:
                    self.hardware_checkboxes[index].setChecked(False)
                elif self.HardwareStatusDict[cur_imgID][vb] == nr.hardware:
                    self.hardware_checkboxes[index].setChecked(True)
        self.count += 1
        self.is_update_hw_cbx = False
    
    def update_ost_labeling(self):
        '''
        update osteoporosis radiobuttons
        '''
        self.is_update_ost_label = True
        cur_imgID = self.ImgIDList[self.ImgPointer]
        flag = False
        for i, category in enumerate(nr.OstLabels):
            if self.OstLabelingDict[cur_imgID] == category:
                self.ost_radiobuttons[i].setChecked(True)
                flag = True
                break
        if not flag:
            self.ost_group.setExclusive(False)
            for radiobutton in self.ost_radiobuttons:
                radiobutton.setChecked(False)
            self.ost_group.setExclusive(True)
            
        # if self.OstLabelingDict[cur_imgID] == nr.hasNoOst:
        #     self.ost_radiobuttons1.setChecked(True)
        # elif self.OstLabelingDict[cur_imgID] == nr.hasOst:
        #     self.ost_radiobuttons2.setChecked(True)
        # elif self.OstLabelingDict[cur_imgID] == nr.unsureOst:
        #     self.ost_radiobuttons3.setChecked(True)
        # else:
        #     self.ost_group.setExclusive(False)
        #     self.ost_radiobuttons1.setChecked(False)
        #     self.ost_radiobuttons2.setChecked(False)
        #     self.ost_radiobuttons3.setChecked(False)
        #     self.ost_group.setExclusive(True)
        self.is_update_ost_label = False


    # functions of tab_order_radiobutton
    def tab_order_radiobutton_on_change1(self, change):
        if change:
            self.tabOrder = True
    def tab_order_radiobutton_on_change2(self, change):
        if change:
            self.tabOrder = False

    # The function of start button
    def start_button_on_click(self):
        if self.userTextbox.text() == '':
            QMessageBox.question(self, 'Username', 'Please enter a username', QMessageBox.Ok, QMessageBox.Ok)
            return
        self.username = self.userTextbox.text()
        with open(self.usrnm_temp_file,  'w+') as usrnm_file:
            usrnm_file.write(self.username)
        with open(self.taborder_temp_file,  'w+') as file:
            file.write(str(self.tabOrder))
        
        self.fx_score_sys = nr.candidateScoringSys[self.score_sys_select.currentIndex()]
        with open(self.scoresys_temp_file,  'w+') as file:
            file.write(self.fx_score_sys)
            
        self.ScoreSys = ScoringSysDef(self.fx_score_sys)
        self.fx_labels = self.ScoreSys.FxScoreSysLabels
        self.ost_fx = self.ScoreSys.OstFxLabels
        # construct the backend storing dicts, etc
        self.dict_constructor()
        
        for ID in self.ImgIDList:
            if self.ReadableStatusDict[ID] == nr.unreadable:
                self.num_unreadable += 1

        # The first image that will be shown
        # self.ImgPointer is always pointing to the image that is shown currently
        self.ImgPointer = 0
        for i, ID in enumerate(self.ImgIDList):
            if self.ReadableStatusDict[ID] == nr.readable:
                    self.ImgPointer = i
                    break
                
        if self.begin != None:
            self.ImgPointer = self.begin
        else:
            for index, ID in enumerate(self.ImgIDList):
                if self.StatusDict[ID] == nr.untouch and self.ReadableStatusDict[ID] == nr.readable:
                    self.ImgPointer = index
                    break

        self._clearLayout(self.start_layout)
        self.start_button.deleteLater()
        self.start_button = None
        self.press = None
        self.non_canvas_key_flag = False
        
        if self.StatusDict[self.ImgIDList[self.ImgPointer]] == nr.untouch:
            self.time_log_flag = True
        else:
            self.time_log_flag = False
        
        # basic framework of the UI
        ui = self.main_ui()
        self.main_page_button_function_connecting()
        display(ui)
        # disable these widgets if prohibit to modify points
        if self.block_points:
            self.clearall_button.setEnabled(False)
            for i in range(len(self.VBLabelList)):
                self.clear_coords_btns[i].setEnabled(False)
                self.clear_point_btns[i].setEnabled(False)
                self.clear_last_btns[i].setEnabled(False)
        self.init_display()
        self.showMaximized()
        
        # Connect the mouse button press to the canvas
        self.fig.canvas.mpl_connect('button_press_event', self.image_click)
        # Connect the scoll event with zooming
        self.fig.canvas.mpl_connect('scroll_event',self.scoll_zoom)
        # Connect the mouse motion event
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.fig.canvas.mpl_connect('button_release_event', self.on_release)
        self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)
        self.fig.canvas.mpl_connect('key_release_event', self.on_key_release)
        
        with open(self.time_log_file,  'a+') as f:
            f.write('\nBegin time: {}\n'.format(time.asctime( time.localtime(time.time()))))
        
        self.now = time.time()
        self.is_start_ui = False
    
    # function of unreadable button
    def unreadable_button_on_click(self):
        self._readable_status_dialog()
        self.last_labeled = None

    ## the dialog that appear after click unreadable button
    def _readable_status_dialog(self):
        self.readable_dialog = QDialog()
        self.readable_dialog.setWindowTitle('Set Unreadable  Alert!')
        dlabel = QLabel('By setting the image unreadable, the image will never show up again. Are you sure you want to set unreadable?')
        self.rdNoButton = QPushButton('No')
        self.rdNoButton.clicked.connect(self.readable_dialog.reject)
        self.rdYesButton = QPushButton('Yes')
        self.rdYesButton.clicked.connect(self._readable_dialog_yes_button_on_click)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.rdNoButton)
        button_layout.addWidget(self.rdYesButton)
        self.readDiaLayout = QVBoxLayout()
        self.readDiaLayout.addWidget(dlabel)
        self.readDiaLayout.addLayout(button_layout)
        self.readable_dialog.setLayout(self.readDiaLayout)
        self.readable_dialog.exec_()
   
    @ unsave_decor
    def _readable_dialog_yes_button_on_click(self,button):
        self.ReadableStatusDict[self.ImgIDList[self.ImgPointer]] = nr.unreadable
        self.num_unreadable += 1
        self.StatusDict[self.ImgIDList[self.ImgPointer]] = nr.touch
        self.ControversialDict[self.ImgIDList[self.ImgPointer]][nr.Modifier] = self.username
        self.modifier_label.setText('Last Modifier: '+self.ControversialDict[self.ImgIDList[self.ImgPointer]][nr.Modifier])
        self.next_button_on_click()
        self.readable_dialog.close()

    # the function of flip the image button
    @ unsave_decor
    def flip_image_button_on_click(self, button):
        if self.mode == nr.edit:
            cur_image = self.ImgIDList[self.ImgPointer]
            self.ControversialDict[cur_image][nr.Modifier] = self.username
            self.modifier_label.setText('Last Modifier: '+self.ControversialDict[cur_image][nr.Modifier])
            if self.OrientationDict[cur_image] == nr.face_user_right:
                self.OrientationDict[cur_image] = nr.face_user_left
            else:
                self.OrientationDict[cur_image] = nr.face_user_right
            self.npa = np.fliplr(self.npa)
            self._hflip_corner_points()
            self.update_display()

    def _hflip_corner_points(self):
        cur_image = self.ImgIDList[self.ImgPointer]
        image_width = self.npa.shape[1]
        for vb in self.VBLabelList:
            if self.StoreDict[cur_image][vb][nr.SupPostCoords] != (None, None):
                temp = image_width - self.StoreDict[cur_image][vb][nr.SupPostCoords][0]
                self.StoreDict[cur_image][vb][nr.SupPostCoords] =\
                    (temp, self.StoreDict[cur_image][vb][nr.SupPostCoords][1])
            if self.StoreDict[cur_image][vb][nr.SupAntCoords] != (None, None):
                temp = image_width - self.StoreDict[cur_image][vb][nr.SupAntCoords][0]
                self.StoreDict[cur_image][vb][nr.SupAntCoords] =\
                    (temp, self.StoreDict[cur_image][vb][nr.SupAntCoords][1])
            if vb != 'S1' and self.StoreDict[cur_image][vb][nr.InfAntCoords] != (None, None):
                temp = image_width - self.StoreDict[cur_image][vb][nr.InfAntCoords][0]
                self.StoreDict[cur_image][vb][nr.InfAntCoords] =\
                    (temp, self.StoreDict[cur_image][vb][nr.InfAntCoords][1])
            if vb != 'S1' and self.StoreDict[cur_image][vb][nr.InfPostCoords] != (None, None):
                temp = image_width - self.StoreDict[cur_image][vb][nr.InfPostCoords][0]
                self.StoreDict[cur_image][vb][nr.InfPostCoords] =\
                    (temp, self.StoreDict[cur_image][vb][nr.InfPostCoords][1])

    # the function of comment_submit_button
    @ unsave_decor
    def comment_button_on_click(self, button):
        text = self.username + '\'s idea: ' + self.comment_textbox.toPlainText() + '\n'
        self.ControversialDict[self.ImgIDList[self.ImgPointer]][nr.ConPart] += text
        self.comment_label.setText('Comments:\n'+self.ControversialDict[self.ImgIDList[self.ImgPointer]][nr.ConPart])
        self.comment_textbox.setText('')

    # the function of setcon_button
    @ unsave_decor
    def setcon_button_on_click(self, button):
        self.ControversialDict[self.ImgIDList[self.ImgPointer]][nr.ConStatus] = nr.controversial
        self.controversial_label.setText('Do you want to unflag the image?')
        self.setcon_button.setEnabled(False)
        self.resetcon_button.setEnabled(True)
        self.controversial_label.setStyleSheet('color: red')

    # the function of setcon_button
    @ unsave_decor
    def resetcon_button_on_click(self, button):
        self.ControversialDict[self.ImgIDList[self.ImgPointer]][nr.ConStatus] = nr.uncontroversial
        self.controversial_label.setText('Do you want to flag the image?    ')
        self.setcon_button.setEnabled(True)
        self.resetcon_button.setEnabled(False)
        self.controversial_label.setStyleSheet('color: black')
    
    # the function of comment clear button
    @ unsave_decor
    def comment_clear_button_on_click(self,button):
        self.ControversialDict[self.ImgIDList[self.ImgPointer]][nr.ConPart] = ''
        self.comment_label.setText('\n\n\n\n')

    # The function of prevcon button
    @ display_decor
    def prevcon_button_on_click(self):
        flag = False
        for i in range(1,len(self.ImgIDList)):
            index = (self.ImgPointer - i) % len(self.ImgIDList)
            if(self.ControversialDict[self.ImgIDList[index]][nr.ConStatus] == nr.controversial):
                flag = True
                break
        if flag:
            self.ImgPointer = index
        self.last_labeled = None


    # The function of nextcon button
    @ display_decor
    def nextcon_button_on_click(self):
        flag = False
        for i in range(1,len(self.ImgIDList)):
            index = (self.ImgPointer + i) % len(self.ImgIDList)
            if(self.ControversialDict[self.ImgIDList[index]][nr.ConStatus] == nr.controversial):
                flag = True
                break
        if flag:
            self.ImgPointer = index
        self.last_labeled = None

    # The function of prev button
    @ display_decor
    def prev_button_on_click(self):
        last_time = self.now
        self.now = time.time()
        if self.time_log_flag:
            with open(self.time_log_file,  'a+') as file:
                file.write("\ntotal: {}\n".format(self.now-last_time))
        self.save()
        self.ImgPointer = (self.ImgPointer - 1) % len(self.ImgIDList)
        self.last_labeled = None
        
        if self.StatusDict[self.ImgIDList[self.ImgPointer]] == nr.untouch:
            self.time_log_flag = True
        else:
            self.time_log_flag = False

    # The function of next button
    @ display_decor
    def next_button_on_click(self):
        last_time = self.now
        self.now = time.time()
        if self.time_log_flag:
            with open(self.time_log_file,  'a+') as file:
                file.write("\ntotal: {}\n".format(self.now-last_time))
        self.save()
        self.ImgPointer = (self.ImgPointer + 1) % len(self.ImgIDList)
        self.last_labeled = None
        if self.StatusDict[self.ImgIDList[self.ImgPointer]] == nr.untouch:
            self.time_log_flag = True
        else:
            self.time_log_flag = False

    # The function of prevun button
    @ display_decor
    def prevun_button_on_click(self):
        last_time = self.now
        self.now = time.time()
        if self.time_log_flag:
            with open(self.time_log_file,  'a+') as file:
                file.write("\ntotal: {}\n".format(self.now-last_time))
        self.save()
        flag = False
        for i in range(1,len(self.ImgIDList)):
            index = (self.ImgPointer - i) % len(self.ImgIDList)
            if(self.StatusDict[self.ImgIDList[index]] == nr.untouch):
                flag = True
                break
        if flag:
            self.ImgPointer = index
        self.last_labeled = None
        self.time_log_flag = True

    # The function of nextun button
    @ display_decor
    def nextun_button_on_click(self):
        last_time = self.now
        self.now = time.time()
        if self.time_log_flag:
            with open(self.time_log_file,  'a+') as file:
                file.write("\ntotal: {}\n".format(self.now-last_time))
        self.save()
        flag = False
        for i in range(1,len(self.ImgIDList)):
            index = (self.ImgPointer + i) % len(self.ImgIDList)
            if(self.StatusDict[self.ImgIDList[index]] == nr.untouch):
                flag = True
                break
        if flag:
            self.ImgPointer = index
        self.last_labeled = None
        self.time_log_flag = True

    # The function of clearall button: clear all the info of current image
    @ unsave_decor
    def clear_all_button_on_click(self, button):
        if self.mode != nr.edit or self.points_off_on_status != 2:
            return
        cur_imgID = self.ImgIDList[self.ImgPointer]
        self.ControversialDict[cur_imgID][nr.Modifier] = self.username
        for i, vb in enumerate(self.VBLabelList):
            self.StoreDict[cur_imgID][vb][nr.SupPostCoords] = (None,None)
            self.StoreDict[cur_imgID][vb][nr.SupAntCoords] = (None,None)
            self.StoreDict[cur_imgID][vb][nr.InfAntCoords] = (None,None)
            self.StoreDict[cur_imgID][vb][nr.InfPostCoords] = (None,None)
            self.StoreDict[cur_imgID][vb][nr.Fracture] = self.ScoreSys.normal
            self.HardwareStatusDict[cur_imgID][vb] = nr.nohardware
        self.OstLabelingDict[cur_imgID] = None
        self.update_status()
        self.update_display()
        self.update_ost_labeling()
        self.VBPointer = 0
        if self.tabOrder:
            self.table.setCurrentIndex(0)
        else:
            self.table.setCurrentIndex(len(self.VBLabelList) - 1)
        self.CoordType = self.CoordTypeList[0]
        self.coords_tables[self.VBPointer].setCurrentIndex(0)
        self.update_table()
        self.last_labeled = None

    # Function of home button: restore the original image after zooming and changing window level
    def home_button_on_click(self, button):
        self.axes.set_xlim(0,len(self.npa[0]))
        self.axes.set_ylim(len(self.npa),0)
        self.acc_zoom_scale = 1
        self.WindowLevelDict[self.ImgIDList[self.ImgPointer]] = (self.min_intensity, self.max_intensity)
        self.update_display()
    
    
    # Function of help button: show a dialogue with some instructions
    def help_button_on_click(self, button):
        self.instruction_dialog = QDialog()
        self.instruction_dialog.setWindowTitle('Instructions')
        dlabel = QLabel(instructions)
        self.insYesButton = QPushButton('OK')
        self.insYesButton.clicked.connect(self.instruction_dialog.accept)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.insYesButton)
        self.insDiaLayout = QVBoxLayout()
        self.insDiaLayout.addWidget(dlabel)
        self.insDiaLayout.addLayout(button_layout)
        self.instruction_dialog.setLayout(self.insDiaLayout)
        self.instruction_dialog.exec_()

    # The function of save button: save current StoreDict and StatusDict into the csv file
    def save(self):
        # store labeled stats
        csv_cols = nr.csv_headers
        with open(self.fpath, 'w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=csv_cols)
            writer.writeheader()
                
            for ID in self.ImgIDList:
                status = self.StatusDict[ID]
                VB_dict = self.StoreDict[ID]
                mod = self.ControversialDict[ID][nr.Modifier]
                con_status = self.ControversialDict[ID][nr.ConStatus]
                con_part = self.ControversialDict[ID][nr.ConPart]
                readable = self.ReadableStatusDict[ID]
                orientation = self.OrientationDict[ID]
                ost_labeling = self.OstLabelingDict[ID]
                min_intensity = self.WindowLevelDict[ID][0]
                max_intensity = self.WindowLevelDict[ID][1]
                inverse_gray = str(self.InverseGrayDict[ID])
                for i, vb in enumerate(self.VBLabelList):          
                    SupPost_x = VB_dict[vb][nr.SupPostCoords][0]
                    SupPost_y = VB_dict[vb][nr.SupPostCoords][1]
                    SupAnt_x = VB_dict[vb][nr.SupAntCoords][0]
                    SupAnt_y = VB_dict[vb][nr.SupAntCoords][1]
                    InfAnt_x = VB_dict[vb][nr.InfAntCoords][0]
                    InfAnt_y = VB_dict[vb][nr.InfAntCoords][1]
                    InfPost_x = VB_dict[vb][nr.InfPostCoords][0]
                    InfPost_y = VB_dict[vb][nr.InfPostCoords][1]
                    hardware = self.HardwareStatusDict[ID][vb]
                    
                    f = VB_dict[vb][nr.Fracture]
                    csv_dict = {
                                nr.head_imgID: ID,
                                nr.head_status: status,
                                nr.head_vbLabel: vb,
                                nr.head_SupPostX: SupPost_x, nr.head_SupPostY: SupPost_y,
                                nr.head_SupAntX: SupAnt_x, nr.head_SupAntY: SupAnt_y,
                                nr.head_InfAntX: InfAnt_x, nr.head_InfAntY: InfAnt_y,
                                nr.head_InfPostX: InfPost_x, nr.head_InfPostY: InfPost_y,                        
                                nr.head_frac:f,
                                nr.head_modifier: mod,
                                nr.head_conStatus: con_status,
                                nr.head_conParts: con_part,
                                nr.head_readableStatus: readable,
                                nr.head_hardwareStatus: hardware,
                                nr.head_orientation: orientation,
                                nr.head_ostLabeling: ost_labeling,
                                nr.head_min_intensity:min_intensity,
                                nr.head_max_intensity:max_intensity,
                                nr.head_inverse_gray: inverse_gray
                                }
                    writer.writerow(csv_dict)        
        
        self.save_status = nr.saved
        self.update_save_status_label()

    # What happen when the status of mode radiobuttons is changing
    ## main function
    def mode_radiobuttons_on_change(self, change):
        cur_image = self.ImgIDList[self.ImgPointer]
        last_modifier = self.ControversialDict[self.ImgIDList[self.ImgPointer]][nr.Modifier]
        if self.mode == change.text():
            return
        if change.text() == nr.edit:
            self.mode = nr.edit
            self._batch_widgets_enabled(True)
            if self.ControversialDict[cur_image][nr.Modifier] != None and  self.ControversialDict[cur_image][nr.Modifier] != self.username:
                self.ControversialDict[cur_image][nr.Modifier] = self.username
                self._modify_assure_dialog(last_modifier)
                self.modifier_label.setText('Last Modifier: '+self.ControversialDict[self.ImgIDList[self.ImgPointer]][nr.Modifier])
        else:
            self.mode = nr.view
            self._batch_widgets_enabled(False)
    ## the dialog to let people make sure that s/he really want to modify
    def _modify_assure_dialog(self, last_modifier):
        self.modify_dialog = QDialog()
        self.modify_dialog.setWindowTitle('Change to Edit Mode Alert!')
        dlabel = QLabel('This image was labelled by others. Are you sure you want to change to edit mode?')
        self.dNoButton = QPushButton('No')
        self.dNoButton.clicked.connect(lambda:self._dialog_no_button_on_click(last_modifier))
        self.dYesButton = QPushButton('Yes')
        self.dYesButton.clicked.connect(self.modify_dialog.accept)
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.dNoButton)
        button_layout.addWidget(self.dYesButton)
        self.diaLayout = QVBoxLayout()
        self.diaLayout.addWidget(dlabel)
        self.diaLayout.addLayout(button_layout)
        self.modify_dialog.setLayout(self.diaLayout)
        self.modify_dialog.exec_()
    ## the function of no button in the modify dialog
    def _dialog_no_button_on_click(self,last_modifier):
        cur_image = self.ImgIDList[self.ImgPointer]
        self.ControversialDict[cur_image][nr.Modifier] = last_modifier
        self.mode_radiobuttons2.setChecked(True)
        self._batch_widgets_enabled(False)
        self.modify_dialog.close()
    ## batch_widgets_enabled
    def _batch_widgets_enabled(self, isEnabled):
        ### these widgets remain disabled if prohibit to modify points
        if self.block_points:
            self.clearall_button.setEnabled(isEnabled)
            for i in range(len(self.VBLabelList)):
                self.clear_coords_btns[i].setEnabled(isEnabled)
                self.clear_point_btns[i].setEnabled(isEnabled)
                self.clear_last_btns[i].setEnabled(isEnabled)
                
        self.unreadable_button.setEnabled(isEnabled)
        self.flip_image_button.setEnabled(isEnabled)
        for radiobutton in self.ost_radiobuttons:
            radiobutton.setEnabled(isEnabled)
        # self.ost_radiobuttons1.setEnabled(isEnabled)
        # self.ost_radiobuttons2.setEnabled(isEnabled)
        # self.ost_radiobuttons3.setEnabled(isEnabled)
        for i in range(len(self.VBLabelList)):
            self.hardware_checkboxes[i].setEnabled(isEnabled)
            co = 0
            for j,l in enumerate(self.fx_labels):
                if l != None:
                    self.frac_rbs[i][co].setEnabled(isEnabled)
                    co += 1

    # function of the labeling points on/off button
    def points_off_on_button_on_click(self):
        # self.points_off_on_status = not self.points_off_on_status
        self.points_off_on_status = (self.points_off_on_status + 1) % 3
        if self.points_off_on_status == 2:
            self.points_off_on_button.setText('Toggle Off Labeled Points')
            self.points_off_on_button.setStyleSheet('QPushButton {color: black;}')
            self.points_off_on_button.setToolTip(tt.points_toggle_off)
        elif self.points_off_on_status == 0:
            self.points_off_on_button.setText('Toggle On Labeled Level names')
            self.points_off_on_button.setStyleSheet('QPushButton {color: red;}')
            self.points_off_on_button.setToolTip(tt.level_toggle_on)
        else:
            self.points_off_on_button.setText('Toggle On Labeled Points')
            self.points_off_on_button.setStyleSheet('QPushButton {color: red;}')
            self.points_off_on_button.setToolTip(tt.points_toggle_on)
        self.update_display()

    # function of inverse gray button
    def inverse_gray_button_on_click(self):
        self.InverseGrayDict[self.ImgIDList[self.ImgPointer]] = not self.InverseGrayDict[self.ImgIDList[self.ImgPointer]]
        self.init_display(False)

    # The function of clear activated point buttons
    @ unsave_decor
    def clear_button_on_click(self, button):
        if self.mode != nr.edit or self.points_off_on_status != 2:
            return
        cur_imgID = self.ImgIDList[self.ImgPointer]
        cur_VB = self.VBLabelList[self.VBPointer]

        self.ControversialDict[cur_imgID][nr.Modifier] = self.username
        if self.CoordType == self.CoordTypeList[0]:
            self.StoreDict[cur_imgID][cur_VB][nr.SupPostCoords] = (None,None)
        elif self.CoordType == self.CoordTypeList[1]:
            self.StoreDict[cur_imgID][cur_VB][nr.SupAntCoords] = (None,None)
        elif self.CoordType == self.CoordTypeList[2]:
            self.StoreDict[cur_imgID][cur_VB][nr.InfAntCoords] = (None,None)
        elif self.CoordType == self.CoordTypeList[3]:
            self.StoreDict[cur_imgID][cur_VB][nr.InfPostCoords] = (None,None)

        self.update_status()
        self.update_display()
        self.update_table()

    # function of clear coords btns in the table tabs
    @ unsave_decor
    def clear_coords_btns_on_click(self, button):
        if self.mode != nr.edit or self.points_off_on_status != 2:
            return
        cur_imgID = self.ImgIDList[self.ImgPointer]
        cur_VB = self.VBLabelList[self.VBPointer]

        self.ControversialDict[cur_imgID][nr.Modifier] = self.username
        self.StoreDict[cur_imgID][cur_VB][nr.SupPostCoords] = (None,None)
        self.StoreDict[cur_imgID][cur_VB][nr.SupAntCoords] = (None,None)
        self.StoreDict[cur_imgID][cur_VB][nr.InfAntCoords] = (None,None)
        self.StoreDict[cur_imgID][cur_VB][nr.InfPostCoords] = (None,None)

        self.update_status()
        self.update_display()
        self.update_table()
        
        # highlight the center coords tab
        self.update_coord_tabs()
        self.last_labeled = None
    
    # function of clear last btns in the table tabs
    @ unsave_decor
    def clear_last_btns_on_click(self, button):
        if self.mode != nr.edit or self.last_labeled == None or self.points_off_on_status != 2:
            return
        cur_imgID = self.ImgIDList[self.ImgPointer]
        last_VB = self.last_labeled[0]
        last_cor = self.last_labeled[1]

        self.ControversialDict[cur_imgID][nr.Modifier] = self.username
        if last_cor == nr.CoordTypeList[0]:
            self.StoreDict[cur_imgID][last_VB][nr.SupPostCoords] = (None,None)
        elif last_cor == nr.CoordTypeList[1]:
            self.StoreDict[cur_imgID][last_VB][nr.SupAntCoords] = (None,None)
        elif last_cor == nr.CoordTypeList[2]:
            self.StoreDict[cur_imgID][last_VB][nr.InfAntCoords] = (None,None)
        elif last_cor == nr.CoordTypeList[3]:
            self.StoreDict[cur_imgID][last_VB][nr.InfPostCoords] = (None,None)
        
        if self.tabOrder:
            self.table.setCurrentIndex(self.VBLabelList.index(last_VB))
        else:
            self.table.setCurrentIndex(len(self.VBLabelList) - 1 - self.VBLabelList.index(last_VB))
        
        self.CoordType = last_cor
        self.last_labeled = None
            
        self.update_status()
        self.update_display()
        self.update_table()
        self.coords_tables[self.VBPointer].setCurrentIndex(self.CoordTypeList.index(last_cor))
 
    # What happen when storing tabs on change (i.e., the activated VB changes)
    def on_tab_change(self, change):
        if not self.is_update_table and self.time_log_flag:
            with open(self.time_log_file,  'a+') as file:
                file.write("\t")
        if self.tabOrder:
            self.VBPointer = change
        else:
            self.VBPointer = len(self.VBLabelList) - 1 - change
        self.update_coord_tabs()
        # if not self.points_off_on_status:
        #     self.update_display()

    # What happen when fracture radiobutton on change
    def on_frac_radiobuttons_change(self, change):
        cur_imgID = self.ImgIDList[self.ImgPointer]
        cur_sdict = self.StoreDict[cur_imgID]
        cur_VB = self.VBLabelList[self.VBPointer]
        
        # when changing the radio buttons, this function will be called two times
        # the first time change.text() = previous button text, because it's unchecked
        # the second time change.text() = changed button text, because it's checked
        # we need to judge whether it's first called or second called
        original_frac = self.StoreDict[cur_imgID][cur_VB][nr.Fracture]
        if original_frac != change.text():
            self.StoreDict[cur_imgID][cur_VB][nr.Fracture] = change.text()
            self.update_display()
            self.update_frac_vb_label()

        if original_frac != change.text() and not self.init_display_flag:
            self.save_status = nr.unsaved
            self.update_save_status_label()
            self.ControversialDict[cur_imgID][nr.Modifier] = self.username
            self.modifier_label.setText('Last Modifier: '+self.ControversialDict[cur_imgID][nr.Modifier])
           
    # What happen when coords tabs on change (i.e., the activated VB changes)
    def on_coords_tab_change(self, change):
        self.CoordType = self.CoordTypeList[change]

    # trigger with the hardware checkbox
    @ unsave_decor
    def hardware_checkbox_state_change(self, state):
        if self.mode != nr.edit:
            return
        cur_image = self.ImgIDList[self.ImgPointer]
        if not self.init_display_flag:
            if state == QtCore.Qt.Checked:
                self.HardwareStatusDict[cur_image][self.VBLabelList[self.VBPointer]] = nr.hardware
            else:
                self.HardwareStatusDict[cur_image][self.VBLabelList[self.VBPointer]] = nr.nohardware
            
            self.update_table()
            # self.update_hardware_checkboxes()
            self.ControversialDict[cur_image][nr.Modifier] = self.username
            self.modifier_label.setText('Last Modifier: '+self.ControversialDict[cur_image][nr.Modifier])


    # ost radiobuttons on change
    def ost_rb_on_change(self, change):
        cur_imgID = self.ImgIDList[self.ImgPointer]
        if self.mode != nr.edit:
            flag = False
            for i, category in enumerate(nr.OstLabels):
                if self.OstLabelingDict[cur_imgID] == category:
                    self.ost_radiobuttons[i].setChecked(True)
                    flag = True
                    break
            if not flag:
                self.ost_group.setExclusive(False)
                for radiobutton in self.ost_radiobuttons:
                    radiobutton.setChecked(False)
                self.ost_group.setExclusive(True)
            # if self.OstLabelingDict[cur_imgID] == nr.hasNoOst:
            #     self.ost_radiobuttons1.setChecked(True)
            # elif self.OstLabelingDict[cur_imgID] == nr.hasOst:
            #     self.ost_radiobuttons2.setChecked(True)
            # elif self.OstLabelingDict[cur_imgID] == nr.unsureOst:
            #     self.ost_radiobuttons3.setChecked(True)
            # else:
            #     self.ost_group.setExclusive(False)
            #     self.ost_radiobuttons1.setChecked(False)
            #     self.ost_radiobuttons2.setChecked(False)
            #     self.ost_radiobuttons3.setChecked(False)
            #     self.ost_group.setExclusive(True)
            return
        # when changing the radio buttons, this function will be called two times
        # the first time change.text() = previous button text, because it's unchecked
        # the second time change.text() = changed button text, because it's checked
        # we need to judge whether it's first called or second called
        original_ost = self.OstLabelingDict[cur_imgID]
        if not self.is_update_ost_label:
            if original_ost != change.text():
                self.OstLabelingDict[cur_imgID] = change.text()

            if original_ost != change.text() and not self.init_display_flag:
                self.save_status = nr.unsaved
                self.update_save_status_label()
                self.ControversialDict[cur_imgID][nr.Modifier] = self.username
                self.modifier_label.setText('Last Modifier: '+self.ControversialDict[cur_imgID][nr.Modifier])

    def image_click(self, event):
        """
        What to do after clicking on image
        """
        # left click
        if event.inaxes==self.axes:
            if event.button == 1:
                if not event.dblclick:
                    if not self.block_points and self.mode == nr.edit and self.points_off_on_status == 2:
                        last_time = self.now
                        self.now = time.time()
                        if self.time_log_flag:
                            with open(self.time_log_file,  'a+') as file:
                                file.write("{} ".format(self.now-last_time))
                        
                        cur_imgID = self.ImgIDList[self.ImgPointer]
                        cur_VB = self.VBLabelList[self.VBPointer]
                        self.ControversialDict[cur_imgID][nr.Modifier] = self.username
                        if self.CoordType == self.CoordTypeList[0]:
                            self.StoreDict[cur_imgID][cur_VB][nr.SupPostCoords] = (event.xdata, event.ydata)
                        elif self.CoordType == self.CoordTypeList[1]:
                            self.StoreDict[cur_imgID][cur_VB][nr.SupAntCoords] = (event.xdata, event.ydata)
                        elif self.CoordType == self.CoordTypeList[2]:
                            self.StoreDict[cur_imgID][cur_VB][nr.InfAntCoords] = (event.xdata, event.ydata)
                        elif self.CoordType == self.CoordTypeList[3]:
                            self.StoreDict[cur_imgID][cur_VB][nr.InfPostCoords] = (event.xdata, event.ydata)

                        self.last_labeled = (cur_VB, self.CoordType)
                        self.update_status()
                        self.update_display()
                        self.update_table()
                        self.update_coord_tabs()
                        self.save_status = nr.unsaved
                        self.update_save_status_label()
                        
                        # sanity check
                        if self.StoreDict[cur_imgID][cur_VB][nr.SupPostCoords] != (None, None) \
                            and self.StoreDict[cur_imgID][cur_VB][nr.SupAntCoords] != (None, None) \
                            and self.StoreDict[cur_imgID][cur_VB][nr.InfAntCoords] != (None, None) \
                            and self.StoreDict[cur_imgID][cur_VB][nr.InfPostCoords] != (None, None):
                            points = [self.StoreDict[cur_imgID][cur_VB][nr.SupPostCoords],
                                      self.StoreDict[cur_imgID][cur_VB][nr.SupAntCoords],
                                      self.StoreDict[cur_imgID][cur_VB][nr.InfAntCoords],
                                      self.StoreDict[cur_imgID][cur_VB][nr.InfPostCoords]
                                     ]
  
                            # if not checkAntiClockwise(points):
                            if not sanity_check(points):
                                self.sanity_dialog = QDialog()
                                self.sanity_dialog.setWindowTitle('Alarm!')
                                dlabel = QLabel("Are you sure you are marking in the anti-clockwise order or the image is correctly oriented?")
                                self.sanityYesButton = QPushButton('Yes')
                                self.sanityYesButton.clicked.connect(self.sanity_dialog.accept)

                                button_layout = QHBoxLayout()
                                button_layout.addWidget(self.sanityYesButton)
                                self.sanityDiaLayout = QVBoxLayout()
                                self.sanityDiaLayout.addWidget(dlabel)
                                self.sanityDiaLayout.addLayout(button_layout)
                                self.sanity_dialog.setLayout(self.sanityDiaLayout)
                                self.sanity_dialog.exec_()
                                       
            elif event.button == 3:
                if event.dblclick:
                    # no zooming
                    if not self.non_canvas_key_flag:
                        self.axes.set_xlim(0,len(self.npa[0]))
                        self.axes.set_ylim(len(self.npa),0)
                        self.acc_zoom_scale = 1
                    # original window label
                    else:
                        self.WindowLevelDict[self.ImgIDList[self.ImgPointer]] = (self.min_intensity, self.max_intensity)
                    self.update_display()
                else:
                    self.press = event.xdata, event.ydata
                    
    def on_motion(self, event):
        # Mouse motion after mouse right single click
        if event.xdata == None or event.ydata == None:
            return
        
        if self.press != None and not self.non_canvas_key_flag:
            if self.press == None and not self.non_canvas_key_flag: return
            if event.inaxes != self.axes: return
            xpress, ypress = self.press
            dx = event.xdata - xpress
            dy = event.ydata - ypress
            cur_xlim = self.axes.get_xlim()
            cur_ylim = self.axes.get_ylim()
            self.axes.set_xlim([cur_xlim[0] - dx, cur_xlim[1] - dx])
            self.axes.set_ylim([cur_ylim[0] - dy, cur_ylim[1] - dy])
            self.update_display()

        if not self.non_canvas_key_flag:
            self.prevCursorLoc = self.cursor.pos().x(), self.cursor.pos().y()
        # Mouse motion after holding shift key
        if self.non_canvas_key_flag:
            xpress, ypress = self.prevCursorLoc
            xdata =self.cursor.pos().x() 
            ydata =self.cursor.pos().y() 
            dx = xdata - xpress
            dy = ydata - ypress
            self.window_level(dx, dy)
            self.prevCursorLoc = xdata, ydata

    """
    window/level
    """
    def window_level(self, dwindow, dlevel):
        du = (dwindow - dlevel) / QDesktopWidget().screenGeometry().width()
        dl = - (dlevel + dwindow)/ QDesktopWidget().screenGeometry().width()

        dgray = self.gray_range * du * self.wl_scale
        if self.cur_max_intensity + dgray < self.max_gray_value \
            and self.cur_max_intensity + dgray > self.cur_min_intensity:
            self.cur_max_intensity += dgray

        dgray = self.gray_range * dl * self.wl_scale
        if self.cur_min_intensity + dgray > self.min_gray_value \
            and self.cur_min_intensity + dgray < self.cur_max_intensity:
            self.cur_min_intensity += dgray

        self.WindowLevelDict[self.ImgIDList[self.ImgPointer]] = (self.cur_min_intensity, self.cur_max_intensity)
        self.update_display()
    
    def on_release(self, event):
        """
        Mouse release after motion
        """
        self.press = None
        # self.update_display()


    def on_key_press(self, event):
        """
        key press: connect to the canvas
        """
        sys.stdout.flush()
        self.key_press_whole(event, 0)


    def on_key_release(self, event):
        """
        key release: connect to the canvas
        """
        self.non_canvas_key_flag = False
        # self.update_display()

    def scoll_zoom(self, event):
        """
        What to do after scolling
        """
        if event.xdata == None or event.ydata == None:
            return
        # get the current x and y limits
        cur_xlim = self.axes.get_xlim()
        cur_ylim = self.axes.get_ylim()
        xdata = event.xdata # get event x location
        ydata = event.ydata # get event y location
        left_xdata = xdata - cur_xlim[0]
        right_xdata = cur_xlim[1] - xdata
        up_ydata = ydata - cur_ylim[0]
        down_ydata = cur_ylim[1] - ydata
        if event.button == 'down':
            # deal with zoom in
            scale_factor = 1/self.zoom_base_scale
        elif event.button == 'up':
            # deal with zoom out
            scale_factor = self.zoom_base_scale
        else:
            # deal with something that should never happen
            scale_factor = 1
        self.acc_zoom_scale *= (1 / scale_factor)
        # set new limits
        self.axes.set_xlim([xdata - left_xdata*scale_factor,
                 xdata + right_xdata*scale_factor])
        self.axes.set_ylim([ydata - up_ydata*scale_factor,
                 ydata + down_ydata*scale_factor])
        self.update_display()
        
        
    def keyPressEvent(self, event):
        """
        keyboard shortcuts: connected to the whole window except canvas
        """
        self.key_press_whole(event, 1)
    
    def keyReleaseEvent(self, event):
        """
        key release event
        """
        self.non_canvas_key_flag = False

    def key_press_whole(self, event, signal_from):
        """
        keyborad: connect to the whole window
        """
        if self.is_start_ui:
            return
        if signal_from == 0: # 0 for from canvas
            if event.key == '[':
                self.prev_button_on_click()
            if event.key == ']':
                self.next_button_on_click()
            if event.key == 'backspace':
                self.clear_last_btns_on_click(0)
            if event.key == 'enter':
                self.VBPointer = (self.VBPointer + 1)%len(self.VBLabelList)
                if self.tabOrder:
                    self.table.setCurrentIndex(self.VBPointer)
                else:
                    self.table.setCurrentIndex(len(self.VBLabelList) - 1 - self.VBPointer)
            if event.key == 'shift':
                self.non_canvas_key_flag = True
            if event.key == 'w':
                d = -self.key_wl_scale
                self.window_level(0,d)
            if event.key == 's':
                d = self.key_wl_scale
                self.window_level(0,d)
            if event.key == 'a':
                d = -self.key_wl_scale
                self.window_level(d,0)
            if event.key == 'd':
                d = self.key_wl_scale
                self.window_level(d,0)
        elif signal_from == 1: # 1 for from other part
            if event.key() == QtCore.Qt.Key_BracketLeft:
                self.prev_button_on_click()
            if event.key() == QtCore.Qt.Key_BracketRight:
                self.next_button_on_click()
            if event.key() == QtCore.Qt.Key_Backspace:
                self.clear_last_btns_on_click(0)
            if event.key() == QtCore.Qt.Key_Return:
                self.VBPointer = (self.VBPointer + 1)%len(self.VBLabelList)
                if self.tabOrder:
                    self.table.setCurrentIndex(self.VBPointer)
                else:
                    self.table.setCurrentIndex(len(self.VBLabelList) - 1 - self.VBPointer)
            if event.key() == QtCore.Qt.Key_Shift:
                self.non_canvas_key_flag = True
            if event.key() == QtCore.Qt.Key_W:
                d = -self.key_wl_scale
                self.window_level(0,d)
            if event.key() == QtCore.Qt.Key_S:
                d = self.key_wl_scale
                self.window_level(0,d)
            if event.key() == QtCore.Qt.Key_A:
                d = -self.key_wl_scale
                self.window_level(d,0)
            if event.key() == QtCore.Qt.Key_D:
                d = self.key_wl_scale
                self.window_level(d,0)


    def closeEvent(self, event):
        """
        save when closing
        """
        if self.is_start_ui:
            return
        self.save()
        event.accept()
