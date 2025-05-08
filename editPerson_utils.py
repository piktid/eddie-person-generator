import os
import sys
import json
import requests
from io import BytesIO
from PIL import Image, ImageFile, ImageFilter
from random import randint

from editPerson_api import upload_target_call, generate_variation_call, open_image_from_url, handle_notifications
from editPerson_dict import valid_keywords


def variate_person(PARAM_DICTIONARY, TOKEN_DICTIONARY):

    ID_IMAGE = PARAM_DICTIONARY.get('ID_IMAGE')

    if ID_IMAGE is None:
        print('Uploading the target image')
        response_json = upload_target_call(PARAM_DICTIONARY=PARAM_DICTIONARY, TOKEN_DICTIONARY=TOKEN_DICTIONARY)
        ID_IMAGE = response_json.get('id_image')
        PARAM_DICTIONARY['ID_IMAGE'] = ID_IMAGE
    else:
        print(f'Input image is already available with code: {ID_IMAGE}, proceeding..')

    KEYWORD = PARAM_DICTIONARY.get('KEYWORD')
    ID_PERSON = PARAM_DICTIONARY.get('ID_PERSON')
    if KEYWORD is not None:
        if KEYWORD not in valid_keywords["location"]:
            print(f'Error: keyword {KEYWORD} is not valid, valid keywords are: {valid_keywords["location"]}')
            return False
        print(f'Generating a new person using {ID_IMAGE} for idx_person: {ID_PERSON} and keyword: {KEYWORD}')
    else:
        print('Error: keyword is not provided')
        return False

    response_json = generate_variation_call(PARAM_DICTIONARY=PARAM_DICTIONARY, TOKEN_DICTIONARY=TOKEN_DICTIONARY)
    print(response_json)

    flag_response, response_notifications = handle_notifications(PARAM_DICTIONARY, TOKEN_DICTIONARY)
    if flag_response is False:
        # Error
        print('Error retrieving the generated images. No images found after 120 attempts')
        return False

    # Get the first link from the response
    download_link = ((response_notifications.get("links"))[0]).get("l") 
    print('new image ready for download:', download_link)

    flag_save, final_path = save_replaced_img(download_link, PARAM_DICTIONARY, TOKEN_DICTIONARY)
    if flag_save is False:
        print('Error: failed to save the generated image')
        return False, None, ID_IMAGE

    return flag_save, final_path, ID_IMAGE


def save_replaced_img(link, PARAM_DICTIONARY, TOKEN_DICTIONARY):
    print('Saving the generated image')
    try:
        options_str = ''
        seed = PARAM_DICTIONARY.get('SEED', 0)
        keyword = PARAM_DICTIONARY.get('KEYWORD', None)
        if keyword is not None:
            options_str = options_str+keyword+'_'
        
        path_output = PARAM_DICTIONARY.get('OUTPUT_PATH', None)

        if PARAM_DICTIONARY.get('INPUT_PATH', None) is not None:
            filename_with_extension = PARAM_DICTIONARY.get('INPUT_PATH')
        elif PARAM_DICTIONARY.get('INPUT_URL', None) is not None:
            filename_with_extension = PARAM_DICTIONARY.get('INPUT_URL')
        else:
            filename_with_extension = link
        
        if path_output is None:
            path_output = os.path.abspath(os.getcwd())
        
        img_format = filename_with_extension.split('.')[-1]
        image_path = os.path.join(path_output, filename_with_extension.split('/')[-1])
        final_path = image_path.split('.')[0]+'_'+str(seed)+'_'+options_str+'.'+img_format
        print(f'Final path: {final_path}')

        # save the generated image in the generated folder
        src_img = open_image_from_url(link)
        try:
            src_img.save(final_path, subsampling=0, quality=95, icc_profile=src_img.info.get('icc_profile'))
        except:
            src_img.save(final_path)
    except Exception as e:
        print(f'Error: {e}')
        return False, None

    return True, final_path
 