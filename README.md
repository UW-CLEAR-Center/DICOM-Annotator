# DICOM-Annotator
# How to open the app
- The app is running in conda virtual environment. To install all required packages, run
$ conda create --name <env> --file requirements.txt
- Activate the virtual environment.
- Then run
$ export PYTHONPATH="$PYTHONPATH:/path/to/dir/DicomAnnotator/"
- Go into the folder
$ cd /path/to/dir
- Modify the configuration file (configurations.json)
- Run the app by
$ python DicomAnnotator/main.py

# Attributes in the configuraion file
## input_directory
The directory from which the program can read the input images. Cannot be empty or nonexisted.
## zooming_speed
Determines how fast the image zooms in/out when the annotator scrolls the mouse wheel. It Should > 1, and 1.2 is a good choice.
## window_level_sensitivity
Controls the rate at which the window and the level change when the mouse moves a unit of length. The smaller the attribute is, the slower the window/level rate is. 1 is a good choice.
## output_path
Specifies the path in which the result file will be stored. If there is no such file, the program will create the file after you press the save button in the start page.
## region_identifiers
The list of region identifiers.
## image_label
The list of categories of the image label.
## region_labels
Specifies the region labels
### checkbox:
If the category is binary, a user can click a checkbox to annotator "yes". This attribute specifies the situation of "yes".

# Optional arguments:
##  -h
show this help message and exit
##  -b
begin at which image, default is the first untouched image. The range should be 0 to (# of images - 1). Begin with the default image if out of the range
##  -u
the max upper gray can be reached is {u * (grayscale of white of the images + 1) - 1} when window/level, default is 3
##  -l
the lower upper gray can be reached is {- l * (grayscale of white of the images + 1)} when window/level, default is 2
##  -d
whether turn on debug model
##  -p
whether can place or remove points on images

# Funding:
This work was completed by investigators at the University of Washington's Clinical Learning, Evidence And Research (CLEAR) Center for Musculoskeletal Disorders and supported by a research grant from the National Institute of Arthritis and Musculoskeletal and Skin Diseases (NIAMS) of the National Institutes of Health, under Award Number P30AR072572. 

# Citation:
If you would like to use this code for a research project please use the acknowledgement below all publications.  This helps us continue to support this program and continue to innovate.
DICOMAnnotator was developed through the University of Washington's Clinical Learning, Evidence And Research (CLEAR) Center for Musculoskeletal Disorders and supported by a research grant from the National Institute of Arthritis and Musculoskeletal and Skin Diseases (NIAMS) of the National Institutes of Health, under Award Number P30AR072572.
