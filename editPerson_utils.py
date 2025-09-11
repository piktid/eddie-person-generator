import os
import sys
import json
import requests
from io import BytesIO
from PIL import Image, ImageFile, ImageFilter
from random import randint

from editPerson_api import (upload_target_call, generate_variation_call, open_image_from_url, handle_notifications,
                           upload_v2_request, upload_file_to_s3, upload_url_to_s3, 
                           handle_upload_notifications, handle_download_notifications)
from editPerson_dict import valid_keywords


def variate_person(PARAM_DICTIONARY, TOKEN_DICTIONARY, use_v2=False):
    """
    Main function to generate person variations
    Args:
        PARAM_DICTIONARY: Parameters dictionary
        TOKEN_DICTIONARY: Token dictionary
        use_v2: If True, use v2 workflow (upload/v2, S3, new notifications), else use v1 workflow
    """
    if use_v2:
        return variate_person_v2(PARAM_DICTIONARY, TOKEN_DICTIONARY)
    else:
        return variate_person_v1(PARAM_DICTIONARY, TOKEN_DICTIONARY)


def variate_person_v1(PARAM_DICTIONARY, TOKEN_DICTIONARY):
    """
    Original v1 workflow
    """
    ID_IMAGE = PARAM_DICTIONARY.get('ID_IMAGE')

    if ID_IMAGE is None:
        print('Uploading the target image (v1)')
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


def variate_person_v2(PARAM_DICTIONARY, TOKEN_DICTIONARY):
    """
    New v2 workflow:
    1. Request upload/v2 endpoint to get id_image, fileKey and uploadUrl
    2. Upload file using uploadUrl
    3. Wait for upload notifications to get image processing results
    4. Generate variation (similar to before)
    5. Wait for notifications to get generation results
    """
    ID_IMAGE = PARAM_DICTIONARY.get('ID_IMAGE')

    if ID_IMAGE is None:
        print('Starting v2 upload process...')
        
        # Step 1: Request upload/v2 endpoint
        upload_response = upload_v2_request(PARAM_DICTIONARY=PARAM_DICTIONARY, TOKEN_DICTIONARY=TOKEN_DICTIONARY)
        ID_IMAGE = upload_response.get('image_id')
        file_key = upload_response.get('link', {}).get('image', {}).get('fileKey')
        upload_url = upload_response.get('link', {}).get('image', {}).get('uploadUrl')
        
        print(f'Got upload details - ID: {ID_IMAGE}, FileKey: {file_key}, UploadURL: {upload_url}')
        
        if not ID_IMAGE or not file_key or not upload_url:
            print('Error: Missing required upload parameters')
            return False, None, None
            
        PARAM_DICTIONARY['ID_IMAGE'] = ID_IMAGE
        
        # Step 2: Upload file to S3
        INPUT_PATH = PARAM_DICTIONARY.get('INPUT_PATH')
        INPUT_URL = PARAM_DICTIONARY.get('INPUT_URL')
        
        upload_success = False
        if INPUT_PATH is not None:
            upload_success = upload_file_to_s3(INPUT_PATH, upload_url, file_key)
        elif INPUT_URL is not None:
            upload_success = upload_url_to_s3(INPUT_URL, upload_url, file_key)
        else:
            print('Error: No input file or URL provided')
            return False, None, ID_IMAGE
            
        if not upload_success:
            print('Error: Failed to upload file to S3')
            return False, None, ID_IMAGE
            
        # Step 3: Wait for upload notifications
        print('Waiting for upload processing...')
        upload_success, upload_data = handle_upload_notifications(PARAM_DICTIONARY, TOKEN_DICTIONARY)
        
        if not upload_success:
            print('Error: Upload processing timeout')
            return False, None, ID_IMAGE
            
        print(f'Upload processing completed: {upload_data}')
        
    else:
        print(f'Input image is already available with code: {ID_IMAGE}, proceeding..')

    # Step 4: Generate variation
    KEYWORD = PARAM_DICTIONARY.get('KEYWORD')
    ID_PERSON = PARAM_DICTIONARY.get('ID_PERSON')
    
    if KEYWORD is not None:
        if KEYWORD not in valid_keywords["location"]:
            print(f'Error: keyword {KEYWORD} is not valid, valid keywords are: {valid_keywords["location"]}')
            return False, None, ID_IMAGE
        print(f'Generating a new person using {ID_IMAGE} for idx_person: {ID_PERSON} and keyword: {KEYWORD}')
    else:
        print('Error: keyword is not provided')
        return False, None, ID_IMAGE

    generation_response = generate_variation_call(PARAM_DICTIONARY=PARAM_DICTIONARY, TOKEN_DICTIONARY=TOKEN_DICTIONARY)
    print(f'Generation response: {generation_response}')
    
    ID_TASK = generation_response.get('id_task')
    if not ID_TASK:
        print('Error: No task ID received from generation')
        return False, None, ID_IMAGE
        
    PARAM_DICTIONARY['ID_TASK'] = ID_TASK

    # Step 5: Wait for download notifications
    print('Waiting for generation to complete...')
    download_success, download_data = handle_download_notifications(PARAM_DICTIONARY, TOKEN_DICTIONARY)
    
    if not download_success:
        print('Error: Generation timeout')
        return False, None, ID_IMAGE

    print(f'Generation completed: {download_data}')
    
    # Extract download link from the response
    # The structure might be different in v2, adjust as needed
    download_link = None
    if 'links' in download_data and len(download_data['links']) > 0:
        download_link = download_data['links'][0].get('l')
    elif 'link' in download_data:
        download_link = download_data['link']
    
    if not download_link:
        print('Error: No download link found in response')
        return False, None, ID_IMAGE
        
    print('New image ready for download:', download_link)

    # Save the generated image
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
 
 