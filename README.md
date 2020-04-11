# How to open the app
- First, install Anaconda3. You can use conda_install.sh or you can go to https://docs.anaconda.com/anaconda/install/ for more details.
## If you are a Linux user
- Modify the configuration file (configuration.json).
- Run startApp.sh. You should specify the directory where the Anaconda is installed. For example,
$ ./startApp.sh /home/shared
## If you would like to run the program by yourself
- The app is running in conda virtual environment. To install all required packages, run
$ conda create --name \<env> --file requirements.txt
- Activate the virtual environment.
$ conda activate \<env>
- Go into the folder where the DicomAnnotator folder stored
$ cd /path/to/dir
- Then run
$ export PYTHONPATH="\$PYTHONPATH:$PWD"
- Modify the configuration file (configurations.json)
- Run the app by
$ python DicomAnnotator/main.py

# Attributes in the configuraion file
For most attributes, if you do not put an attribute in the configuration file or you set the attribute to null, then the attribute is set to default value.
## input_directory
A string. The directory from which the program can read the input images. Default is 'images/'.
## zooming_speed
A float number determines how fast the image zooms in/out when the annotator scrolls the mouse wheel. It Should > 1, and 1.2 is a good choice. Default is 1.2.
## window_level_sensitivity
A float number controls the rate at which the window and the level change when the mouse moves a unit of length. The smaller the attribute is, the slower the window/level rate is. 1 is a good choice. Default is 1.
## output_path
A string specifies the path in which the result file will be stored. If there is no such file, the program will create the file after you press the save button in the start page. Default is 'results.csv'.
## region_identifiers
The string list of region identifiers. Default is ['R0', 'R1', ..., 'R9']
## image_label_description
A string describes what the image label is and is shown at the main page’s top-right corner. Default is 'Image Label'.
## image_label
The string list of categories of the image label. Default is [].
## default_image_label
A string determines which image label's candidate category is set to default. Default is null.
## region_labels
Specifies the region labels:
### checkbox:
A string contains the region label’s candidate category in the form of a check box in the main page’s annotation table. Default is null.
### radiobuttons
A two dimensional list of strings contains the region labels’ candidate categories listed as ratio buttons in the main page’s annotation table. Must be set. Otherwise the program will raise error. Currently, only one group of region label's candidate categories can be set.
### default_radiobuttions
A list of strings determines which region label's candidate category are set to default. Default is the first radiobutton in each group of region label's radiobuttons.
## bounding_polygon_type
Determines the bounding polygon's type. Must be set. It can be an integer, then each region should be outlined by this number of points. It also can be a integer list whose length is the same as region_identifiers' length. Each element in the list determines the number of points needed to outline the associated region.
## bounding_polygon_vertice_shape
Determines the shape of points placed on images. Default is '.'. It can be a character, then all points are in this shape. It also can be a list of characters, in which each element detemines the shape of one polygon's vertex.
## bounding_polygon_vertices_tabs
Determines the name of the vertices presented in the annotation table. Default is ['V0', 'V1', ...]. It can be a string (denoted to S), then the vertices' tab names are ['S0', 'S1', ...]. It also can be a list of strings, where each string is associated with a vertex.
## non_default_regions_description
A string determines the description showed in the text box at the bottom-right of the main page. Default is 'Regions not labeleed to x' where 'x' denote the default region label.
## auto_window_level
A boolean value determines whether to turn on the automatic window/level adjustment function.
## The attributes below determines the conlumns' headers in the result file
All of the attributes below are strings or list of strings.
### image_label_header_in_result_file
Header of the column stroing image label. Default is the same as image_label_description.
### bounding_polygon_vertices_names
Headers of the columns storing point coordinates. Default is ['Vertex0 X', 'Vertex0 Y', 'Vertex1 X', 'Vertex1 Y', ..., 'VertexN X', 'VertexN Y'].
### region_identifier_header_in_result_file
Header of the column storing region identifiers. Default is 'Region Identifier'.
### region_label_headers_in_result_file
Headers of the columns storing region labels. For checkbox, default is the name of the checkbox. For radiobuttons, default is ['Region Label 0', 'Region Label 1', ...].

# Splitting an image set and merge result files
The related functional code are in the split_images_merge_results folder.
## How to split an image set
- Go into the split_images_merge_results folder:
$ cd split_images_merge_results
- Open the split_image_set.py file.
- At the beginning of this file, set where all of your images locate (all_images_dir), where the split image subsets output (output_dir), and the annotators' names and their sequence numbers (annotators_dict).
- Run split_image_set.py
	- If you want to evenly randomly split the image set, you use
	$ python split_image_set.py
	- If you want to split the image set by certain rules, you should first generate a csv file by yourself. In this csv file, there should be two columns. One column's header is 'sid', the other 'aid'. Under 'sid', each cell stores an integer ranging from 1 to the number of images; under 'aid', each cell stores an integer ranging form 1 to the number of annotators. Thus, each row means assigning one image to one annotator. Note you do not need to specify the mapping from one image to a sid. split_image_set.py can do it for you. You only need to specify which sid is assigned to which aid. Then you run
	$ python split_image_set.py path_to_the_csv_file
- After running split_image_set.py, the output_dir you set in split_image_set.py is generated, in which there are
	- subfolders, each uses an annotator's name as its folder name. In each subfolder, there is a folder called images. All of the images for this annotator is in the images folder;
	- a csv file called image_sid_filename_mapping.csv storing how split_image_set.py mapped images to sids.

## How to merge result files
- Open merge_results.py.
- Input the result files' paths into result_paths and set the output merged file path (output_path).
- Run merge_results.py
$ python merge_results.py
- After running merge_results.py, the merged result file is generated.
	

# Optional arguments:
For example, 
$ python DicomAnnotator/main.py -h
##  -h
show this help message and exit.
##  -b
begin at which image, default is the first untouched image. The range should be 0 to (# of images - 1). Begin with the default image if out of the range.
##  -u
the max upper gray can be reached is {u * (grayscale of white of the images + 1) - 1} when window/level, default is 3.
##  -l
the lower upper gray can be reached is {- l * (grayscale of white of the images + 1)} when window/level, default is 2.
##  -d
whether turn on debug model.
##  -p
whether can place or remove points on images.

# Funding
This work was completed by investigators at the University of Washington's Clinical Learning, Evidence And Research (CLEAR) Center for Musculoskeletal Disorders and supported by a research grant from the National Institute of Arthritis and Musculoskeletal and Skin Diseases (NIAMS) of the National Institutes of Health, under Award Number P30AR072572.

# Citation
If you would like to use this code for a research project please use this acknowledgement below all publications. This helps us continue to support this program and continue to innovate.

DICOMAnnotator was developed through the University of Washington's Clinical Learning, Evidence And Research (CLEAR) Center for Musculoskeletal Disorders and supported by a research grant from the National Institute of Arthritis and Musculoskeletal and Skin Diseases (NIAMS) of the National Institutes of Health, under Award Number P30AR072572.
