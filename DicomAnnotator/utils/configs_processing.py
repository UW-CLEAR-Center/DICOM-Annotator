import json
import numpy as np

def configuration_processing(config_filepath):
    with open(config_filepath) as f:
        configs = json.load(f)
    
    ''' input directory '''
    if 'input_directory' not in configs or configs['input_directory'] is None:
        configs['input_directory'] = 'images/'

    ''' zooming_speed '''
    if 'zooming_speed' not in configs or configs['zooming_speed'] is None:
        configs['zooming_speed'] = 1.2

    ''' window/level sensitivity'''
    if 'window_level_sensitivity' not in configs or configs['window_level_sensitivity'] is None:
        configs['window_level_sensitivity'] = 1

    ''' path_for_result_file'''
    if 'path_for_result_file' not in configs or configs['path_for_result_file'] is None:
        configs['path_for_result_file'] = 'results.csv'

    ''' region_identifier list'''
    if 'list_region_identifiers' not in configs or configs['list_region_identifiers'] is None:
        configs['region_identifier_list'] = ['R' + str(i) for i in range(10)]
    else:
        configs['region_identifier_list'] = configs['list_region_identifiers']


    '''image_label_description'''
    if 'image_label_description' not in configs or configs['image_label_description'] is None:
        configs['image_label_description'] = 'Image Label'

    ''' image_label'''
    if 'image_label' not in configs or configs['image_label'] is None:
        configs['image_label'] = []

    ''' default_image_label '''
    if 'default_image_label' in configs and configs['default_image_label'] is not None and configs['default_image_label'] not in configs['image_label']:
        raise Exception('The default image label was not correctly set!')

    if 'default_image_label' not in configs:
        configs['default_image_label'] = None

    ''' region labels: checkbox'''
    if 'checkbox' not in configs['region_labels']:
        configs['region_labels']['checkbox'] = None

    ''' region labels: radiobuttions'''
    if 'radiobuttons' in configs['region_labels'] and 'nondefault' in configs['region_labels']['radiobuttons']:
        raise Exception('Please change the label name, \"nondefault\", in the region_labels\' radiobuttons!')

    if 'default_radiobuttons' not in configs['region_labels'] or configs['region_labels']['default_radiobuttons'] is None:
        configs['region_labels']['default_radiobuttons'] = [configs['region_labels']['radiobuttons'][i][0] for i in range(len(configs['region_labels']['radiobuttons']))]

    # TODO should realize the function that the number of region labels for each region can be configured
    configs['region_labels']['radiobuttons'] = configs['region_labels']['radiobuttons'][0]
    configs['region_labels']['default_radiobuttons'] = configs['region_labels']['default_radiobuttons'][0]

    ''' bounding_polygon_type '''
    if "number_bounding_polygon_vertices" not in configs:
        raise Exception('Please define the bounding polygon type!')
    configs['bounding_polygon_type'] = configs['number_bounding_polygon_vertices']
    if type(configs['bounding_polygon_type']) is not list:
        bounding_polygon_type = configs['bounding_polygon_type']
        configs['bounding_polygon_type'] = [bounding_polygon_type for i in configs['region_identifier_list']]
    elif len(configs['bounding_polygon_type']) == 1:
        bounding_polygon_type = configs['bounding_polygon_type'][0]
        configs['bounding_polygon_type'] = [bounding_polygon_type for i in configs['region_identifier_list']]
    for t in configs['bounding_polygon_type']:
        if type(t) is not int:
            raise Exception('Please use integer to define bounding_polygon_type!')
    if len(configs['bounding_polygon_type']) != len(configs['region_identifier_list']):
        raise Exception('Not all of the regions have a defined bounding_polygon_type')

    max_num_shapes = np.max(configs['bounding_polygon_type'])
    
    ''' bounding_polygon_vertices_shape '''
    if 'bounding_polygon_vertices_shape' not in configs:
        shape = '.'
        configs['bounding_polygon_vertices_shape'] = [shape for i in range(max_num_shapes)]
    elif configs['bounding_polygon_vertices_shape'] is None:
        shape = '.'
        configs['bounding_polygon_vertices_shape'] = [shape for i in range(max_num_shapes)]
    elif type(configs['bounding_polygon_vertices_shape']) is str:
        shape = configs['bounding_polygon_vertices_shape']
        configs['bounding_polygon_vertices_shape'] = [shape for i in range(max_num_shapes)]
    elif len(configs['bounding_polygon_vertices_shape']) == 1:
        shape = configs['bounding_polygon_vertices_shape'][0]
        configs['bounding_polygon_vertices_shape'] = [shape for i in range(max_num_shapes)]
    elif len(configs['bounding_polygon_vertices_shape']) != max_num_shapes:
        print('The number of defined bounding_polygon_vertices_shape is not enough. Will use the default shape.')
        shape = '.'
        configs['bounding_polygon_vertices_shape'] = [shape for i in range(max_num_shapes)]

    ''' bounding_polygon_vertices_tabs '''
    if 'bounding_polygon_vertices_tabs' not in configs:
        tabname = 'V'
        configs['bounding_polygon_vertices_tabs'] = [tabname+str(i) for i in range(max_num_shapes)]
    elif configs['bounding_polygon_vertices_tabs'] is None:
        tabname = 'V'
        configs['bounding_polygon_vertices_tabs'] = [tabname+str(i) for i in range(max_num_shapes)]
    elif type(configs['bounding_polygon_vertices_tabs']) == str:
        tabname = configs['bounding_polygon_vertices_tabs']
        configs['bounding_polygon_vertices_tabs'] = [tabname+str(i) for i in range(max_num_shapes)]
    elif len(configs['bounding_polygon_vertices_tabs']) == 1:
        tabname = configs['bounding_polygon_vertices_tabs'][0]
        configs['bounding_polygon_vertices_tabs'] = [tabname+str(i) for i in range(max_num_shapes)]
    elif len(configs['bounding_polygon_vertices_tabs']) != max_num_shapes:
        print('The number of defined bounding_polygon_vertices_tabs is not enough. Will use the default tab name.')
        tabname = 'V'
        configs['bounding_polygon_vertices_tabs'] = [tabname+str(i) for i in range(max_num_shapes)]

    if 'non_default_regions_description' not in configs or configs['non_default_regions_description'] is None:
        configs['non_default_regions_description'] = "Regions not labeled to {}:".format(configs['region_labels']['default_radiobuttons'])

    # if 'sanity_check_direction' not in configs or configs['sanity_check_direction'] is None:
    #     configs['sanity_check_direction'] = ''
    if 'auto_window_level' not in configs or configs['auto_window_level'] is None:
        configs['auto_window_level'] = False

    """
    headers in the results
    """
    ''' header of the column storing image label'''
    if "image_label_header_in_result_file" not in configs or configs['image_label_header_in_result_file'] is None:
        configs['image_label_header_in_result_file'] = configs['image_label_description']

    ''' header of the column storing point coordinates'''
    if 'bounding_polygon_vertices_names' not in configs:
        name = 'Vertex'
        configs['bounding_polygon_vertices_names'] = [name+str(i) for i in range(max_num_shapes)]
    elif configs['bounding_polygon_vertices_names'] is None:
        name = 'Vertex'
        configs['bounding_polygon_vertices_names'] = [name+str(i) for i in range(max_num_shapes)]
    elif type(configs['bounding_polygon_vertices_names']) is str:
        name = configs['bounding_polygon_vertices_names']
        configs['bounding_polygon_vertices_names'] = [name+str(i) for i in range(max_num_shapes)]
    elif len(configs['bounding_polygon_vertices_names']) == 1:
        name = configs['bounding_polygon_vertices_names'][0]
        configs['bounding_polygon_vertices_names'] = [name+str(i) for i in range(max_num_shapes)]
    elif len(configs['bounding_polygon_vertices_names']) != max_num_shapes:
        print('The number of defined bounding_polygon_vertices_name is not enough. Will use the default name.')
        name = 'Vertex'
        configs['bounding_polygon_vertices_names'] = [name+str(i) for i in range(max_num_shapes)]

    ''' header of the column showing region identifier '''
    if 'region_identifier_header_in_result_file' not in configs or configs['region_identifier_header_in_result_file'] is None:
        configs['region_identifier_header_in_result_file'] = 'Region Identifier'

    ''' header of the columns storing region labels '''
    if 'region_label_headers_in_result_file' not in configs or configs['region_label_headers_in_result_file'] is None:
        configs['region_label_headers_in_result_file'] = {}
    if 'checkbox' not in configs['region_label_headers_in_result_file'] or configs['region_label_headers_in_result_file']['checkbox'] is None:
        configs['region_label_headers_in_result_file']['checkbox'] = configs['region_labels']['checkbox']
    if 'radiobuttons' not in configs['region_label_headers_in_result_file'] or configs['region_label_headers_in_result_file']['radiobuttons'] is None:
        configs['region_label_headers_in_result_file']['radiobuttons'] = ['Region Label ' + str(i) for i in range(len(configs['region_labels']['radiobuttons']))]
    # currently can only deal with one checkbox and one group of radiobuttons
        configs['region_label_headers_in_result_file']['radiobuttons'] = configs['region_label_headers_in_result_file']['radiobuttons'][0]

    return configs
