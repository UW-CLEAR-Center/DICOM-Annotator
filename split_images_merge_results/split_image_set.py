import os
import pandas as pd
import random
import shutil
from shutil import copyfile
import sys
import numpy as np

######################################
""" Some parameters one should set """
all_images_dir = '../images'
output_dir = './'

annotators_dict = {1: 'annotator1',
                   2: 'annotator2',
                   3: 'annotator3',
                   4: 'annotator4',
                   5: 'annotator5',
                    }
######################################

for key in annotators_dict:
    dir_ = os.path.join(output_dir, annotators_dict[key], 'images/')
    if os.path.exists(dir_):
        shutil.rmtree(dir_)
    # if not os.path.exists(dir_):
    os.makedirs(dir_)

""" get all images """
def get_all_images(image_dir):
    images = []
    for root, dirs, files in os.walk(image_dir):
        for f in files:
            images.append(f)
    # images_IDs = set(pd.read_csv(result_file)['Image ID'])
    return images

""" build a dataframe 
image_sid image_filename annotator """
def distributing_images(images_dict, annotators_dict, random_template, input_image_dir, output_dir, output_image_dir='images', csv_filename='image_sid_filename_mapping.csv'):
    df_dict = {'image_sid': list(images_dict.keys()), 'image_filename': list(images_dict.values())}
    sids_filenames = pd.DataFrame(data=df_dict)
    sids_filenames.to_csv(os.path.join(output_dir, csv_filename), index=False)
    random_template_sids = list(random_template['sid'])
    random_template_aids = list(random_template['aid'])
    annotators_images_dict = {}
    for i, sid in enumerate(random_template_sids):
        image_file = images_dict[sid]
        image_path = os.path.join(input_image_dir, image_file)
        annotator = annotators_dict[int(random_template_aids[i])]
        des_dir = os.path.join(output_dir, annotator, output_image_dir, image_file)
        copyfile(image_path, des_dir)

        if annotator not in annotators_images_dict:
            annotators_images_dict[annotator] = []
        annotators_images_dict[annotator].append(image_file)
    
    return annotators_images_dict

""" generate the random template which randomly 
splits image set without overlapping between annotators """
def generate_default_random_template(num_images):
    num_annotators = len(annotators_dict)
    image_seq_list = np.arange(num_images) + 1
    np.random.shuffle(image_seq_list)
    random_split_image_seqs = np.array_split(image_seq_list, num_annotators)
    random_seq_list = []
    annotators = []
    for i, seqs in enumerate(random_split_image_seqs):
        for seq in seqs:
            random_seq_list.append(seq)
            annotators.append(i + 1)
    df = pd.DataFrame(data = {'sid': random_seq_list, 'aid': annotators})
    return df


all_images = get_all_images(all_images_dir)
all_images_dict = dict(zip(range(1, len(all_images)+1), all_images))
if len(sys.argv) == 1 or sys.argv[1] is None:
    random_template = generate_default_random_template(len(all_images))
else:
    random_template = pd.read_csv(sys.argv[1])
annotators_images_dict = distributing_images(all_images_dict, annotators_dict, random_template, input_image_dir=all_images_dir, output_dir=output_dir)
