import matplotlib.pyplot as plt

from os.path import exists, join
import os
import copy

from PyQt5.QtWidgets import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5 import QtCore, QtGui

from DicomAnnotator.utils.namerules import *
from DicomAnnotator.app.instructions import *

tt = toolTips()

class MyCheckBox(QCheckBox):
    
    def __init__(self, text):
        super().__init__(text)

    def _set_color(self, col):
        
        palette = self.palette()
        palette.setColor(self.foregroundRole(), col)
        self.setPalette(palette)

    color = QtCore.pyqtProperty(QtGui.QColor, fset=_set_color)



class AppWidgets(QMainWindow):
    def __init__(self, 
                 ImgIDList,
                 configs,
                 nameRules,
                 columnStretch,
                 parent=None
                   ):
        QMainWindow.__init__(self, parent)

        self.nr = nameRules
        self.usrnm_temp_file = self.nr.temp_filename[0]
        self.taborder_temp_file = self.nr.temp_filename[1]
        self.scoresys_temp_file = self.nr.temp_filename[2]

        self.configs = configs
        self.columnStretch = columnStretch
        self.ImgIDList = ImgIDList
        self.VBLabelList = configs['region_identifier_list']
        self.CoordTypeList = configs['bounding_polygon_vertices_names']
        self.CoordType = self.CoordTypeList[0]
        self.num_unreadable = 0
            
        self.save_status = self.nr.saved

        # some predefined font size
        ## font size 12
        self.font_12 = QtGui.QFont()
        self.font_12.setPointSize(12)


    def startPageWidgets(self):
        """
        Define the widgets in start page
        """
        # where to input username
        self.userLabel = QLabel('Enter Username: ')
        self.userTextbox = QLineEdit()
        if exists(self.usrnm_temp_file):
            with open(self.usrnm_temp_file, 'r') as f:
                temp = f.read()
                if temp != '':
                    self.userTextbox.setText(temp)

        # tab order selection radiobuttons     
        if exists(self.taborder_temp_file):
            with open(self.taborder_temp_file, 'r') as f:
                temp = f.read()
                if temp == 'False':
                    self.tabOrder = False
                else:
                    self.tabOrder = True
        else:
            self.tabOrder = True
        self.tabOrderLabel = QLabel('Select the order of level tabs you like\t\t')
        self.tab_order_radiobuttons1 = QRadioButton("{} Top".format(self.configs['region_identifier_list'][0]))        
        self.tab_order_radiobuttons2 = QRadioButton("{} Bottom".format(self.configs['region_identifier_list'][0]))   
        if self.tabOrder:
            self.tab_order_radiobuttons1.setChecked(True)
        else:
            self.tab_order_radiobuttons2.setChecked(True)
        self.tab_order_group = QButtonGroup()
        self.tab_order_group.addButton(self.tab_order_radiobuttons1)
        self.tab_order_group.addButton(self.tab_order_radiobuttons2)
        
        # a combo box to select scoring system, default scoring system is self.nr.mABQ
        if exists(self.scoresys_temp_file):
            with open(self.scoresys_temp_file, 'r') as f:
                fx_score_sys = f.read()
        else:
            fx_score_sys = self.nr.mABQ       
        if exists(self.scoresys_temp_file):
            self.score_sys_Label = QLabel('The fracture scoring system selected: ')
        else:
            self.score_sys_Label = QLabel('Select a fracture scoring system: ')
        self.score_sys_select = QComboBox()
        for i, c in enumerate(self.nr.candidateScoringSys):
            self.score_sys_select.addItem(c)
            if c == fx_score_sys:
                self.score_sys_select.setCurrentIndex(i)
        if exists(self.scoresys_temp_file):
            self.score_sys_select.setEnabled(False)

        # the start button
        self.start_button = QPushButton('START')
        


    def mainPageWidgets(self):
        '''
        widgets in main page
        '''

        # widgets in the controversial box
        self.unreadable_button = QPushButton(
            'Set Unreadable', default=False, autoDefault=False)        
        self.flip_image_button = QPushButton(
            'Flip the Image', default=False, autoDefault=False)        
        self.controversial_label = QLabel()
        self.comment_label = QLabel()
        self.comment_label.setStyleSheet('color: red')
        self.comment_label.setWordWrap(True)
        self.comment_title_label = QLabel('Leave comments below:')
        self.comment_title_label.setWordWrap(True)
        self.comment_textbox = QTextEdit()
        self.comment_submit_button = QPushButton(
            'Submit Comments', default=False, autoDefault=False)
        self.setcon_button = QPushButton('Set Flagged',default=False, autoDefault=False)
        self.setcon_button.setStyleSheet("QPushButton:disabled""{ color: gray }")
        self.resetcon_button = QPushButton('Set Unflagged',default=False, autoDefault=False)
        self.resetcon_button.setStyleSheet("QPushButton:disabled""{ color: gray }")
        self.comment_clear_button = QPushButton(
            'Clear Submitted Comments', default=False, autoDefault=False)
        self.prevcon_button = QPushButton('Prev Flagged', default=False, autoDefault=False)
        self.nextcon_button = QPushButton('Next Flagged',default=False, autoDefault=False)

        # widgets in the button grid
        self.prev_button = QPushButton('Prev',default=False, autoDefault=False)
        self.next_button = QPushButton('Next',default=False, autoDefault=False)
        self.prevun_button = QPushButton('Prev Unlabeled',default=False, autoDefault=False)
        self.nextun_button = QPushButton('Next Unlabeled',default=False, autoDefault=False)
        self.help_button = QPushButton('Help',default=False, autoDefault=False)
        self.clearall_button = QPushButton('Clear Case',default=False, autoDefault=False)
        self.home_button = QPushButton('Reset View',default=False, autoDefault=False)
        self.save_button = QPushButton('Save',default=False, autoDefault=False)

        # mode radiobuttons
        self.mode_radiobuttons1 = QRadioButton(self.nr.edit)
        self.mode_radiobuttons1.setChecked(True)
        self.mode_radiobuttons2 = QRadioButton(self.nr.view)
        self.mode_vbox = QVBoxLayout()
        self.mode_group = QButtonGroup()
        self.mode_group.addButton(self.mode_radiobuttons1)
        self.mode_group.addButton(self.mode_radiobuttons2)

        # image labeling status box
        self.status_label = QLabel('Status: untouched',self)
        self.num_labelled_label = QLabel('Untouched/Total: ' + '0/' + str(len(self.ImgIDList)), self)
        self.ImgeID_label = QLabel('Image '+str(self.ImgPointer+1)+':\n'+self.ImgIDList[self.ImgPointer],self)
        self.modifier_label = QLabel('Last Modifier: None')
        self.ImgeID_label.setWordWrap(True)
        self.username_label = QLabel('Current user: '+self.username, self)

        # canvas
        self.save_status_label = QLabel(self.save_status)
        newfont = QtGui.QFont("Times", 18, QtGui.QFont.Bold) 
        self.save_status_label.setFont(newfont)
        self.save_status_label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)
        self.screen = QDesktopWidget().screenGeometry(-1)
        self.resize(self.screen.width(), self.screen.height())
        image_width_scale = self.columnStretch[1] \
            / (self.columnStretch[0] + self.columnStretch[1] +self.columnStretch[2])
        self.figure_resolution = (self.screen.width()*image_width_scale, 
            self.screen.height())    
        self.fig, self.axes = plt.subplots(1,1)
        self.dpi = self.fig.dpi
        self.figure_size = (self.figure_resolution[0]/self.dpi, self.figure_resolution[1]/self.dpi)
        self.fig.set_size_inches(self.figure_size)
        self.canvas = FigureCanvas(self.fig)    
        self.canvas.setFocusPolicy( QtCore.Qt.ClickFocus )
        self.canvas.setFocus()

        # labeling related widgets
        self.points_off_on_status = 2 # 2 is on and show points and levels, 1 is on and only show levels, # 0 is off
        self.points_off_on_button = QPushButton(
            'Toggle Off Labeled Points',default=False, autoDefault=False)
        self.points_off_on_button.setToolTip(tt.points_toggle_off)
        self.inverse_gray_button = QPushButton(
            'Invert the Gray',default=False, autoDefault=False)


        if self.configs['region_labels']['radiobuttons'] is None:
            self.frac_label = QLabel('Osteoporosis Fracture:')
        else:
            if self.configs['non_default_regions_description'] is None:
                self.frac_label = QLabel('Regions not Labeled to {}:'.format(self.ScoreSys.default))
            else:
                self.frac_label = QLabel(self.configs['non_default_regions_description'])
        self.frac_vb_label = QLabel()
        self.frac_vb_label.setWordWrap(True)
        if self.configs['region_labels']['radiobuttons'] is None and self.ScoreSys.non_ost_deform:
            self.nonost_label = QLabel(self.ScoreSys.non_ost_deform+':')
        else:
            self.nonost_label = QLabel()
        self.nonost_vb_label = QLabel()
        self.nonost_vb_label.setWordWrap(True)
        self.normal_label = QLabel(self.ScoreSys.default+':')
        self.normal_vb_label = QLabel()
        self.normal_vb_label.setWordWrap(True)
        self._storing_tabs_builder()

        # osteoporosis radiobuttons related
        self.ost_label = QLabel(self.configs['image_label_description'])
        self.ost_group = QButtonGroup()
        self.ost_radiobuttons = []
        for i, category in enumerate(self.configs['image_label']):
            self.ost_radiobuttons.append(QRadioButton(category))       
            self.ost_group.addButton(self.ost_radiobuttons[i])
        # self.ost_radiobuttons1 = QRadioButton(self.nr.hasNoOst)       
        # self.ost_radiobuttons2 = QRadioButton(self.nr.hasOst)        
        # self.ost_radiobuttons3 = QRadioButton(self.nr.unsureOst)
        # self.ost_group.addButton(self.ost_radiobuttons1)
        # self.ost_group.addButton(self.ost_radiobuttons2)
        # self.ost_group.addButton(self.ost_radiobuttons3)

        # set tooltips and fontsize
        self.set_pushbutton_tooltips()
        self.set_widgets_fontsize()

    def _storing_tabs_builder(self):
        '''
        The table to store vb-level labeling results
        '''
        self.table = QTabWidget()
        self.table.setTabPosition(QTabWidget.West)

        self.tabs = []
        bx_frac = self._frac_radiobuttons_builder()
        bx_coords = self._coord_tabs_builder()
        self._hardware_checkbox_builder()
        self.clear_coords_btns = []
        self.clear_point_btns = []
        self.clear_last_btns = []
        
        VBList = self.VBLabelList.copy()
        if not self.tabOrder:
            VBList.reverse()
        for i, vb in enumerate(VBList):
            if self.tabOrder:
                index = i
            else:
                index = len(self.VBLabelList) - 1 - i
            self.clear_point_btns.append(
                QPushButton('Clear Activated Point', default=False, autoDefault=False))
            self.clear_coords_btns.append(
                QPushButton('Clear Activated Region\'s Points', default=False, autoDefault=False))
            self.clear_last_btns.append(
                QPushButton('Clear Last Labeled Point', default=False, autoDefault=False))
            self.tabs.append(QWidget())
            self.table.addTab(self.tabs[i], vb)
            self.tabs[i].layout = QVBoxLayout()
            self.tabs[i].layout.addStretch()
            self.tabs[i].layout.addWidget(self.hardware_checkboxes[i])
            self.tabs[i].layout.addStretch()
            self.tabs[i].layout.addLayout(bx_frac[index])
            self.tabs[i].layout.addStretch()
            self.tabs[i].layout.addLayout(bx_coords[i])
            self.tabs[i].layout.addStretch()
            self.tabs[i].layout.addWidget(self.clear_coords_btns[i])
            self.tabs[i].layout.addWidget(self.clear_point_btns[i])
            self.tabs[i].layout.addWidget(self.clear_last_btns[i])
            self.tabs[i].layout.addStretch()
            self.tabs[i].setLayout(self.tabs[i].layout)
        

    def _frac_radiobuttons_builder(self):
        self.frac_rbs = [[] for l in self.VBLabelList]
        self.frac_group = []
        vbox = []
        for i, vb in enumerate(self.VBLabelList):
            self.frac_group.append(QButtonGroup())
            vbox.append(QVBoxLayout())
            for j, l in enumerate(self.fx_labels):
                if l == None:
                    continue
                self.frac_rbs[i].append(QRadioButton(l))
                self.frac_group[i].addButton(self.frac_rbs[i][-1])
                vbox[i].addWidget(self.frac_rbs[i][-1])   
        return vbox

    def _coord_tabs_builder(self):
        bx_cor_coords = []
        self.cor_X_Label = []
        self.cor_Y_Label = []
        for i in range(len(self.CoordTypeList)):
            hbox, cor_X_Label, cor_Y_Label = self._corner_coords_label_builder()
            bx_cor_coords.append(hbox)
            self.cor_X_Label.append(cor_X_Label)
            self.cor_Y_Label.append(cor_Y_Label)
        
        self.coords_tables = []
        box = []
        for i, vb in enumerate(self.VBLabelList):
            self.coords_tables.append(QTabWidget())           
            index = self.configs['region_identifier_list'].index(vb)
            for j, name in enumerate(self.configs['bounding_polygon_vertices_names']):
                if j >= self.configs['bounding_polygon_type'][index]:
                    break
                self.bx_tab_sp = QWidget()
                self.bx_tab_sp.layout = bx_cor_coords[j][i]            
                self.coords_tables[i].addTab(self.bx_tab_sp, self.configs['bounding_polygon_vertices_tabs'][j])
                self.bx_tab_sp.setLayout(self.bx_tab_sp.layout)
            
            box.append(QHBoxLayout())
            box[i].addWidget(self.coords_tables[i])
        if not self.tabOrder:
            box.reverse()
        return box

    def _corner_coords_label_builder(self):
        '''
        Corner coords labels in the table
        '''
        cor_X_Label = []
        cor_Y_Label = []
        bx_coords = []
        hbox = []
        for i, vb in enumerate(self.VBLabelList):
            ## coords
            cor_X = QLabel("X: ", self)
            cor_Y = QLabel("Y: ", self)
            cor_X_Label.append(QLabel("None", self))
            cor_Y_Label.append(QLabel("None", self))
            bx_X = QHBoxLayout()
            bx_X.addWidget(cor_X)
            bx_X.addWidget(cor_X_Label[i])
            bx_Y = QHBoxLayout()
            bx_Y.addWidget(cor_Y)
            bx_Y.addWidget(cor_Y_Label[i])
            hbox.append(QVBoxLayout())
            hbox[i].addLayout(bx_X)
            hbox[i].addLayout(bx_Y)
        return hbox, cor_X_Label, cor_Y_Label
    def _hardware_checkbox_builder(self):
        self.hardware_checkboxes = []
        for i, vb in enumerate(self.VBLabelList):
            if self.configs['region_labels']['checkbox'] is None:
                hardware_checkBox = None
            else:
                hardware_checkBox = MyCheckBox(self.configs['region_labels']['checkbox'])
            self.hardware_checkboxes.append(hardware_checkBox)

    def set_pushbutton_tooltips(self):
        """
        the tooltips of each pushbutton in the app
        """
        self.unreadable_button.setToolTip(tt.unreadable)
        self.prev_button.setToolTip(tt.prev)
        self.next_button.setToolTip(tt.next)
        self.prevun_button.setToolTip(tt.prevun)
        self.nextun_button.setToolTip(tt.nextun)
        self.clearall_button.setToolTip(tt.clearall)
        self.home_button.setToolTip(tt.home)
        self.save_button.setToolTip(tt.save)
        self.help_button.setToolTip(tt.help)
        self.setcon_button.setToolTip(tt.setCon)
        self.resetcon_button.setToolTip(tt.resetCon)
        self.prevcon_button.setToolTip(tt.prevCon)
        self.nextcon_button.setToolTip(tt.nextCon)
        self.comment_clear_button.setToolTip(tt.clearcomment)
        self.comment_submit_button.setToolTip(tt.submitcomment)        
        self.flip_image_button.setToolTip(tt.flipimage)
        self.inverse_gray_button.setToolTip(tt.inverse_gray)        
        for i in range(len(self.VBLabelList)):
            self.clear_coords_btns[i].setToolTip(tt.clearlevel)
            self.clear_point_btns[i].setToolTip(tt.clearpoint)
            self.clear_last_btns[i].setToolTip(tt.clearlastlabeled)
       
    def set_widgets_fontsize(self):
        """
        set font size of each widgets in the app
        """
        self.unreadable_button.setFont(self.font_12)
        self.prev_button.setFont(self.font_12)
        self.next_button.setFont(self.font_12)
        self.prevun_button.setFont(self.font_12)
        self.nextun_button.setFont(self.font_12)
        self.clearall_button.setFont(self.font_12)
        self.home_button.setFont(self.font_12)
        self.save_button.setFont(self.font_12)
        self.help_button.setFont(self.font_12)        
        self.setcon_button.setFont(self.font_12)
        self.resetcon_button.setFont(self.font_12)
        self.prevcon_button.setFont(self.font_12)
        self.nextcon_button.setFont(self.font_12)
        self.comment_clear_button.setFont(self.font_12)
        self.comment_submit_button.setFont(self.font_12)        
        self.points_off_on_button.setFont(self.font_12)
        self.inverse_gray_button.setFont(self.font_12)        
        for i in range(len(self.VBLabelList)):
            self.clear_coords_btns[i].setFont(self.font_12)
            self.clear_point_btns[i].setFont(self.font_12)
            self.clear_last_btns[i].setFont(self.font_12)            
            co = 0
            for j, l in enumerate(self.fx_labels):
                if l != None:
                    self.frac_rbs[i][co].setFont(self.font_12)
                    co += 1
            if self.hardware_checkboxes[i] is not None:
                self.hardware_checkboxes[i].setFont(self.font_12)        
        self.mode_radiobuttons1.setFont(self.font_12)
        self.mode_radiobuttons2.setFont(self.font_12)
        self.flip_image_button.setFont(self.font_12)        
        self.status_label.setFont(self.font_12)
        self.num_labelled_label.setFont(self.font_12)
        self.ImgeID_label.setFont(self.font_12)
        self.modifier_label.setFont(self.font_12)
        self.username_label.setFont(self.font_12)       
        self.controversial_label.setFont(self.font_12)
        self.comment_title_label.setFont(self.font_12)        
        self.ost_label.setFont(self.font_12)
        for radiobutton in self.ost_radiobuttons:
            radiobutton.setFont(self.font_12)
        # self.ost_radiobuttons1.setFont(self.font_12)
        # self.ost_radiobuttons2.setFont(self.font_12)
        # self.ost_radiobuttons3.setFont(self.font_12)
