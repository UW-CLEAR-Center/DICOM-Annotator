import json

class nameRules:
    def __init__(self):
        # the module name of this software (also the root dir of the software)
        self.moduleName = 'DicomAnnotator'

        # read the configuration file
        with open(self.moduleName + '/configurations.json') as f:
            configs = json.load(f)

        # edit/view mode
        self.edit = 'Edit'
        self.view = 'View Only'
        
        # temp_file
        self.temp_dirname = '.temp/'
        self.temp_filename = [self.temp_dirname + s for s in ['usrnm', 'taborder', 'scoringsys', 'timelog']] # [username, taborder, scoring system]

        # region identifiers
        self.VBLabelList = configs['region_identifiers']

        # region labels, checkbox
        self.region_label_checkbox = configs['region_labels']['checkbox']

        # coordinate types
        self.CoordTypeList = ['sup_post', 'sup_ant', 'inf_ant', 'inf_post']

        # VBDict keys
        self.SupPostCoords = 'SupPost'
        self.SupAntCoords = 'SupAnt'
        self.InfAntCoords = 'InfAnt'
        self.InfPostCoords = 'InfPost'
        self.Fracture = 'Fracture'
        
        # controversial dict keys
        self.Modifier = 'Modifier'
        self.ConPart = 'ConPart'
        self.ConStatus = 'ConStatus'

        # fractured systems
        self.mABQ = 'mABQ'
        self.ABQ = 'ABQ'
        self.SQ = 'SQ'

        self.candidateScoringSys = [self.mABQ, self.ABQ, self.SQ]
		
        # image label
        self.OstLabels = configs['image_label']

        # touch/untouch status
        self.touch = 'T'
        self.untouch = 'U'

        # contoversial status
        self.controversial = 'C'
        self.uncontroversial = 'UC'

        # readable status
        self.readable = 'R'
        self.unreadable = 'UR'

        # hardware status
        self.hardware = 'Yes'
        self.nohardware = 'No'

        # orientation
        self.face_user_right = 'Faces User Right'
        self.face_user_left = 'Faces User Left'

        # csv headers
        self.head_imgID = 'Image ID'
        self.head_status = 'Status'
        self.head_vbLabel = 'VB Label'

        self.head_SupPostX = 'SupPost X'
        self.head_SupPostY = 'SupPost Y'
        self.head_SupAntX = 'SupAnt X'
        self.head_SupAntY = 'SupAnt Y'
        self.head_InfAntX = 'InfAnt X'
        self.head_InfAntY = 'InfAnt Y'
        self.head_InfPostX = 'InfPost X'
        self.head_InfPostY = 'InfPost Y'

        self.head_frac = 'Fracture?'
        self.head_modifier = 'Last Modifier'
        self.head_conStatus = 'Controversial Status'
        self.head_conParts = 'Comments'
        self.head_readableStatus = 'Readable?'
        self.head_hardwareStatus = 'hasHardware?'
        self.head_orientation = 'Orientation'
        self.head_ostLabeling = 'hasOsteoporosis?'

        self.head_min_intensity = 'min_intensity'
        self.head_max_intensity = 'max_intensity'
        self.head_inverse_gray = 'is_inversed_gray?'

        self.csv_headers = [self.head_imgID, 
                            self.head_status, 
                            self.head_vbLabel, 
                            self.head_SupPostX, 
                            self.head_SupPostY, 
                            self.head_SupAntX, 
                            self.head_SupAntY, 
                            self.head_InfAntX,
                            self.head_InfAntY,
                            self.head_InfPostX,
                            self.head_InfPostY,
                            self.head_frac, 
                            self.head_modifier, 
                            self.head_conStatus, 
                            self.head_conParts, 
                            self.head_readableStatus, 
                            self.head_hardwareStatus, 
                            self.head_orientation,
                            self.head_ostLabeling,
                            self.head_min_intensity,
                            self.head_max_intensity,
                            self.head_inverse_gray]

        # save status
        self.saved = 'saved'
        self.unsaved = 'unsaved'

class ScoringSysDef:

    def __init__(self, score_sys):
        # fracture types
        ## common labels may be shared by different scoring systems
        nr = nameRules()
        self.normal = 'Normal'
        self.non_ost_deform = 'Non-fracture Deformity'

        ## mABQ system
        if score_sys == nr.mABQ:
            mABQ0 = 'mABQ0 Fracture\n(< 20% height loss)'
            mABQ1 = 'mABQ1 Fracture\n(20%-25% height loss)'
            mABQ2 = 'mABQ2 Fracture\n(25%-40% height loss)'
            mABQ3 = 'mABQ3 Fracture\n(> 40% height loss)'
            self.OstFxLabels = [mABQ0, mABQ1, mABQ2, mABQ3]
            self.FxScoreSysLabels = [self.normal, self.non_ost_deform, mABQ0, mABQ1, mABQ2, mABQ3]
        
        ## ABQ system
        elif score_sys == nr.ABQ:
            ABQ_fx = 'Osteoporotic Fracture'
            self.OstFxLabels = [ABQ_fx]
            self.FxScoreSysLabels = [self.normal, self.non_ost_deform, ABQ_fx]

        ## SQ system
        elif score_sys == nr.SQ:
            self.normal = 'Grade-0 No Deformity'
            self.non_ost_deform = None
            SQ_grade1 = 'Grade-1 20-25%'
            SQ_grade2 = 'Grade-2 26-40%'
            SQ_grade3 = 'Grade-3 >40%'
            self.OstFxLabels = [SQ_grade1, SQ_grade2, SQ_grade3]
            self.FxScoreSysLabels = [self.normal, self.non_ost_deform, SQ_grade1, SQ_grade2, SQ_grade3]
        
        # # the dict for all scoring system
        # self.OstFxLabelDict = {self.mABQ: self.mABQ_ost_fx, self.ABQ: self.ABQ_ost_fx, self.SQ: self.SQ_ost_fx}
        # self.FxScoreSysDict = {self.mABQ: self.mABQ_labels, self.ABQ: self.ABQ_labels, self.SQ: self.SQ_labels}












