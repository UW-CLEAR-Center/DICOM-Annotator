#!/bin/bash
source $1/anaconda3/bin/activate
conda init
source /home/$USER/.bashrc
ENVS=$(conda env list | awk '{print $1}' )
flag=$false
for env in $ENVS; 
do 
	if [ "$env" == "DicomAnnotatorEnv" ]; then 
		flag=$true; 
	fi;
done
if ! $flag ; then
	conda config --append channels anaconda
	conda config --append channels conda-forge
	conda config --append channels simpleitk
	conda create -n DicomAnnotatorEnv python=3.7 --file ./requirements.txt
fi
conda activate DicomAnnotatorEnv
export PYTHONPATH=$PYTHONPATH:$PWD
python DicomAnnotator/main.py
