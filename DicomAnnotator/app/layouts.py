from os.path import exists, join
import os

from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui

from DicomAnnotator.utils.namerules import *
from DicomAnnotator.app.instructions import *
from DicomAnnotator.app.sanity_check import *
from DicomAnnotator.app.widgets import AppWidgets


nr = nameRules()
ModuleName = nr.moduleName
tt = toolTips()
if not os.path.exists(nr.temp_dirname):
    os.makedirs(nr.temp_dirname)
with open(ModuleName+'/app/instructions.html') as f:
    instructions = f.read()



class AppLayouts(AppWidgets):
    def __init__(self,
                 ImgIDList,
                 mainPageColumnStretch):
        AppWidgets.__init__(self, ImgIDList, mainPageColumnStretch)


    def start_ui(self):
        ''' The layout of start page'''
        self.startPageWidgets()
        
        self.userHbox = QHBoxLayout()
        self.userHbox.addWidget(self.userLabel)
        self.userHbox.addWidget(self.userTextbox)
        self.scoreSysHbox = QHBoxLayout()
        self.scoreSysHbox.addWidget(self.score_sys_Label)
        self.scoreSysHbox.addWidget(self.score_sys_select)
        self.tabOrderbox = QHBoxLayout()
        self.tabOrderbox.addWidget(self.tabOrderLabel)
        self.tabOrderbox.addWidget(self.tab_order_radiobuttons1)
        self.tabOrderbox.addWidget(self.tab_order_radiobuttons2)
        self.start_layout = QVBoxLayout()
        self.start_layout.addLayout(self.userHbox)
        self.start_layout.addLayout(self.scoreSysHbox)
        self.start_layout.addLayout(self.tabOrderbox)
        self.start_layout.addWidget(self.start_button)
        templayout = QVBoxLayout()
        templayout.addLayout(self.start_layout)
        self.mylayout = QHBoxLayout()
        self.mylayout.addStretch()
        self.mylayout.addLayout(templayout)
        self.mylayout.addStretch()
        self.mylayout.setStretch(0,1)
        self.mylayout.setStretch(1,1)
        self.mylayout.setStretch(2,1)
        cen_wid = QWidget()
        cen_wid.setLayout(self.mylayout)
        self.setCentralWidget(cen_wid)

    def _canvas_layout_builder(self):
        ''' The layer above the canvas and the canvas'''
        # above canvas layout
        self.above_canvas_layout = QHBoxLayout()
        self.above_canvas_layout.addStretch()
        self.above_canvas_layout.addWidget(self.save_status_label)
        self.above_canvas_layout.addStretch()
        # the canvas
        self.canvas_save_layout = QVBoxLayout()
        self.canvas_save_layout.addLayout(self.above_canvas_layout)
        self.canvas_save_layout.addWidget(self.canvas)
        self.canvas_save_layout.setStretch(0,1)
        self.canvas_save_layout.setStretch(1,50)       
        self.mid_layout = QHBoxLayout()
        self.mid_layout.addLayout(self.canvas_save_layout)



    def main_ui(self):
        ''' main page'''
        self.mainPageWidgets()
        self.set_pushbutton_tooltips()
        self.set_widgets_fontsize()

        self._canvas_layout_builder()
        self.mylayout.addLayout(self.mid_layout)
        self._basic_boxes()
        self.operation_ui()
        self.labelling_ui()
        
        self.mid_layout.addLayout(self.labelling_layout)
        self.mid_layout.insertLayout(0,self.operation_layout)

        for i, s in enumerate(self.columnStretch):
             self.mid_layout.setStretch(i, s)


    def _basic_boxes(self):
        '''basic boxes, layouts or components in the main page'''
        self._mode_radiobuttons_builer()
        self._ost_labeling_box_builder()
        self._frac_label_gather_box_builder()
        self._status_box_builder()
        self._controversial_box_builder()

    def labelling_ui(self):
        ''' right side of the main page'''
        self.labelling_layout = QVBoxLayout()
        self.labelling_layout.addLayout(self.ost_labeling_box)
        self.labelling_layout.addWidget(self.table)
        self.labelling_layout.addWidget(self.points_off_on_button)
        self.labelling_layout.addWidget(self.inverse_gray_button)
        self.labelling_layout.addLayout(self.frac_label_gather_box)
        self.labelling_layout.setStretch(0,1)
        self.labelling_layout.setStretch(1,50)
        self.labelling_layout.setStretch(2,1)
        self.labelling_layout.setStretch(2,1)
        self.labelling_layout.setStretch(4,12)

    def operation_ui(self):
        ''' left side of the main page'''
        # edit/view radiobuttons
        self.operation_layout = QVBoxLayout()
        self.operation_layout.addLayout(self.mode_vbox)
        # press buttons
        self._button_grid()
        self.operation_layout.addLayout(self.button_grid)
        # status box
        self.operation_layout.addLayout(self.status_box)
        self.operation_layout.addLayout(self.controversial_box)

    def _mode_radiobuttons_builer(self):
        self.mode_vbox = QVBoxLayout()
        self.mode_vbox.addWidget(self.mode_radiobuttons1)
        self.mode_vbox.addWidget(self.mode_radiobuttons2)

    def _ost_labeling_box_builder(self):
        ost_hbox = QHBoxLayout()
        for radiobutton in self.ost_radiobuttons:
            ost_hbox.addWidget(radiobutton)
        # ost_hbox.addWidget(self.ost_radiobuttons1)
        # ost_hbox.addWidget(self.ost_radiobuttons3)
        # ost_hbox.addWidget(self.ost_radiobuttons2)        
        self.ost_labeling_box = QVBoxLayout()
        self.ost_labeling_box.addWidget(self.ost_label)
        self.ost_labeling_box.addLayout(ost_hbox)

    def _frac_vb_label_builder(self, type_):
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setFrameShadow(QFrame.Raised)
        vbox = QVBoxLayout(frame)
        if type_ in self.ost_fx:
            vbox.addWidget(self.frac_label)
            vbox.addWidget(self.frac_vb_label)
        elif self.ScoreSys.non_ost_deform != None \
            and type_ == self.ScoreSys.non_ost_deform:
            vbox.addWidget(self.nonost_label)
            vbox.addWidget(self.nonost_vb_label)
        elif type_ == self.ScoreSys.normal:
            vbox.addWidget(self.normal_label)
            vbox.addWidget(self.normal_vb_label)
        vbox.addStretch()
        vbox.setStretch(0,1)
        vbox.setStretch(1,4)
        vbox.setStretch(2,10)
        rst_box = QVBoxLayout()
        rst_box.addWidget(frame)
        return rst_box

    def _frac_label_gather_box_builder(self):
        vbox_normal = self._frac_vb_label_builder(type_=self.ScoreSys.normal)
        vbox_ost = self._frac_vb_label_builder(type_=self.ost_fx[0])
        if self.ScoreSys.non_ost_deform != None:
            vbox_nonost = self._frac_vb_label_builder(
                type_=self.ScoreSys.non_ost_deform)
        self.frac_label_gather_box = QVBoxLayout()
        self.frac_label_gather_box.addLayout(vbox_ost)
        if self.ScoreSys.non_ost_deform != None:
            self.frac_label_gather_box.addLayout(vbox_nonost)

    def _status_box_builder(self):
        status_frame = QFrame()
        status_frame.setFrameShape(QFrame.StyledPanel)
        status_frame.setFrameShadow(QFrame.Raised)
        status_box = QVBoxLayout(status_frame)
        status_box.addWidget(self.ImgeID_label)
        status_box.addWidget(self.modifier_label)
        status_box.addWidget(self.username_label)
        status_box.addWidget(self.status_label)
        status_box.addWidget(self.num_labelled_label)
        self.status_box = QVBoxLayout()
        self.status_box.addWidget(status_frame)

    def _controversial_box_builder(self):
        # related buttons
        button_box = QGridLayout()
        button_box.addWidget(self.setcon_button,0,0)
        button_box.addWidget(self.resetcon_button,0,1)
        button_box.addWidget(self.prevcon_button,1,0)
        button_box.addWidget(self.nextcon_button,1,1)        
        # comment clear button and comment label
        comment_label_frame = QFrame()
        comment_label_box = QVBoxLayout(comment_label_frame)
        comment_label_box.addWidget(self.comment_label)
        combutton_frame = QFrame()
        combutton_frame.setFrameShape(QFrame.StyledPanel)
        combutton_frame.setFrameShadow(QFrame.Raised)
        combutton_box = QVBoxLayout(combutton_frame)      
        combutton_box.addWidget(comment_label_frame)
        combutton_box.addWidget(self.comment_clear_button)
        # comment box and submit comment button
        combox_frame = QFrame()
        combox_frame.setFrameShape(QFrame.StyledPanel)
        combox_frame.setFrameShadow(QFrame.Raised)
        combox_box = QVBoxLayout(combox_frame)
        combox_box.addWidget(self.comment_title_label)
        combox_box.addWidget(self.comment_textbox)
        combox_box.addWidget(self.comment_submit_button)
        combox_box.setStretch(0,1)
        combox_box.setStretch(1,4)
        combox_box.setStretch(2,1)
                
        con_frame = QFrame()
        con_frame.setFrameShape(QFrame.StyledPanel)
        con_frame.setFrameShadow(QFrame.Raised)
        controversial_box = QVBoxLayout(con_frame)
        controversial_box.addWidget(self.unreadable_button)
        controversial_box.addWidget(self.flip_image_button)
        controversial_box.addWidget(self.controversial_label)
        controversial_box.addLayout(button_box)
        controversial_box.addWidget(combutton_frame)
        controversial_box.addWidget(combox_frame)
        controversial_box.setStretch(0,1)
        controversial_box.setStretch(1,1)
        controversial_box.setStretch(2,1)
        controversial_box.setStretch(3,2)
        controversial_box.setStretch(4,10)
        controversial_box.setStretch(5,3)
        
        self.controversial_box = QVBoxLayout()
        self.controversial_box.addWidget(con_frame)

    def _button_grid(self):
        ''' buttons at the right up corner'''
        self.button_grid = QGridLayout()
        self.button_grid.addWidget(self.prev_button,0,0)
        self.button_grid.addWidget(self.next_button,0,1)
        self.button_grid.addWidget(self.prevun_button,1,0)
        self.button_grid.addWidget(self.nextun_button,1,1)       
        self.button_grid.addWidget(self.clearall_button,2,0)
        self.button_grid.addWidget(self.home_button,2,1)
        self.button_grid.addWidget(self.save_button,3,0)
        self.button_grid.addWidget(self.help_button,3,1)

    def _clearLayout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self._clearLayout(item.layout())
    
    def tab_order_radiobutton_on_change1(self, change):
        if change:
            self.tabOrder = True
    def tab_order_radiobutton_on_change2(self, change):
        if change:
            self.tabOrder = False
