import os
import requests
import json
from io import BytesIO
import base64
from PIL import Image, ImageFile, ImageFilter, ImageCms
import copy
from time import sleep


# -----------READ/WRITE FUNCTIONS------------
def open_image_from_url(url):
    response = requests.get(url, stream=True)
    if not response.ok:
        print(response)

    image = Image.open(BytesIO(response.content))
    return image


def open_image_from_path(path):
    f = open(path, 'rb')
    buffer = BytesIO(f.read())
    image = Image.open(buffer)
    return image

    return BytesIO(response.content)


def im_2_B(image):
    # Convert Image to buffer
    buff = BytesIO()

    if image.mode == 'CMYK':
        image = ImageCms.profileToProfile(image, 'ISOcoated_v2_eci.icc', 'sRGB Color Space Profile.icm', renderingIntent=0, outputMode='RGB')

    image.save(buff, format='PNG',icc_profile=image.info.get('icc_profile'))
    img_str = buff.getvalue()
    return img_str


def im_2_buffer(image):
    # Convert Image to bytes 
    buff = BytesIO()

    if image.mode == 'CMYK':
        image = ImageCms.profileToProfile(image, 'ISOcoated_v2_eci.icc', 'sRGB Color Space Profile.icm', renderingIntent=0, outputMode='RGB')

    image.save(buff, format='PNG',icc_profile=image.info.get('icc_profile'))
    return buff


def b64_2_img(data):
    # Convert Base64 to Image
    buff = BytesIO(base64.b64decode(data))
    return Image.open(buff)
    

def im_2_b64(image):
    # Convert Image 
    buff = BytesIO()
    image.save(buff, format='PNG')
    img_str = base64.b64encode(buff.getvalue()).decode('utf-8')
    return img_str


# -----------PROCESSING FUNCTIONS------------
def start_call(email, password, server_mode='production'):
    # Get token
    URL_API = 'https://api.piktid.com/api'
    print(f'Logging to: {URL_API}')

    response = requests.post(URL_API+'/tokens', data={}, auth=(email, password))
    response_json = json.loads(response.text)
    ACCESS_TOKEN = response_json['access_token']
    REFRESH_TOKEN = response_json['refresh_token']

    return {'access_token': ACCESS_TOKEN, 'refresh_token': REFRESH_TOKEN, 'url_api': URL_API}


def refresh_call(TOKEN_DICTIONARY):
    # Get token using only access and refresh tokens, no mail and psw
    URL_API = TOKEN_DICTIONARY.get('url_api')
    response = requests.put(URL_API+'/tokens', json=TOKEN_DICTIONARY)
    response_json = json.loads(response.text)
    ACCESS_TOKEN = response_json['access_token']
    REFRESH_TOKEN = response_json['refresh_token']

    return {'access_token': ACCESS_TOKEN, 'refresh_token': REFRESH_TOKEN, 'url_api': URL_API}


def resume_call(ACCESS_TOKEN, REFRESH_TOKEN):

    URL_API = 'https://api.piktid.com/api'

    return {'access_token': ACCESS_TOKEN, 'refresh_token': REFRESH_TOKEN, 'url_api': URL_API}


# UPLOAD ENDPOINTS
def upload_target_call(PARAM_DICTIONARY, TOKEN_DICTIONARY):

    OPTIONS_DICT = PARAM_DICTIONARY.get('OPTIONS', {})

    # start the generation process given the image parameters
    TOKEN = TOKEN_DICTIONARY.get('access_token', '')
    URL_API = TOKEN_DICTIONARY.get('url_api')

    target_full_path = PARAM_DICTIONARY.get('INPUT_PATH')
    if target_full_path is None:
        target_url = PARAM_DICTIONARY.get('INPUT_URL')

        # request with url
        response = requests.post(URL_API+'/edit/target', 
                                 headers={'Authorization': 'Bearer '+TOKEN},
                                 data={'url': target_url, 'options': json.dumps(OPTIONS_DICT)},
                                 )

        if response.status_code == 401:
            TOKEN_DICTIONARY = refresh_call(TOKEN_DICTIONARY)
            TOKEN = TOKEN_DICTIONARY.get('access_token', '')
            # try with new TOKEN
            response = requests.post(URL_API+'/edit/target', 
                                     headers={'Authorization': 'Bearer '+TOKEN},
                                     data={'url': target_url, 'options': json.dumps(OPTIONS_DICT)},
                                     )
    else:
        image_file = open(target_full_path, 'rb')
        # request with file
        response = requests.post(URL_API+'/edit/target', 
                                 headers={'Authorization': 'Bearer '+TOKEN},
                                 files={'file': image_file},
                                 data={'options': json.dumps(OPTIONS_DICT)},
                                 )

        if response.status_code == 401:
            TOKEN_DICTIONARY = refresh_call(TOKEN_DICTIONARY)
            TOKEN = TOKEN_DICTIONARY.get('access_token', '')
            # try with new TOKEN
            response = requests.post(URL_API+'/edit/target', 
                                     headers={'Authorization': 'Bearer '+TOKEN},
                                     files={'file': image_file},
                                     data={'options': json.dumps(OPTIONS_DICT)},
                                     )

    response_json = json.loads(response.text)
    print(f"Upload successful. Response json: {response_json}")

    return response_json


def generate_variation_call(PARAM_DICTIONARY, TOKEN_DICTIONARY):

    ID_IMAGE = PARAM_DICTIONARY.get('ID_IMAGE')
    ID_PERSON = PARAM_DICTIONARY.get('ID_PERSON')
    KEYWORD = PARAM_DICTIONARY.get('KEYWORD')
    data = {
            'category': 'person',
            'id_image': ID_IMAGE,
            'id_person': ID_PERSON
        }

    data = {**data, 'keyword': json.dumps({'location': KEYWORD})}

    OPTIONS_DICT = {} # TODO: add other options

    SEED = PARAM_DICTIONARY.get('SEED')

    if SEED is not None:
        OPTIONS_DICT = {**OPTIONS_DICT, 'seed': SEED}

    data = {**data, 'options': json.dumps(OPTIONS_DICT)}

    print(f'data to send to generation: {data}')

    # start the generation process given the image parameters
    TOKEN = TOKEN_DICTIONARY.get('access_token', '')
    URL_API = TOKEN_DICTIONARY.get('url_api')

    response = requests.post(URL_API+'/edit/generate',
                             headers={'Authorization': 'Bearer '+TOKEN},
                             json=data
                             )
    # if the access token is expired
    if response.status_code == 401:
        TOKEN_DICTIONARY = refresh_call(TOKEN_DICTIONARY)
        TOKEN = TOKEN_DICTIONARY.get('access_token', '')
        # try with new TOKEN
        response = requests.post(URL_API+'/edit/generate',
                                 headers={'Authorization': 'Bearer '+TOKEN},
                                 json=data
                                 )

    # print(response.text)
    response_json = json.loads(response.text)
    return response_json


# -----------NOTIFICATIONS FUNCTIONS------------
def get_notification_by_name(name_list, TOKEN_DICTIONARY):
    # name_list='new_generation, progress, error'
    TOKEN = TOKEN_DICTIONARY.get('access_token', '')
    URL_API = TOKEN_DICTIONARY.get('url_api')

    response = requests.post(URL_API+'/notification_by_name_json',
                             headers={'Authorization': 'Bearer '+TOKEN},
                             json={'name_list': name_list},
                             # timeout=100,
                             )
    # if the access token is expired
    if response.status_code == 401:
        # try with new TOKEN
        TOKEN_DICTIONARY = refresh_call(TOKEN_DICTIONARY)
        TOKEN = TOKEN_DICTIONARY.get('access_token', '')
        response = requests.post(URL_API+'/notification_by_name_json',
                                 headers={'Authorization': 'Bearer '+TOKEN},
                                 json={'name_list': name_list},
                                 # timeout=100,
                                 )
    # print(response.text)
    response_json = json.loads(response.text)
    return response_json.get('notifications_list')


def delete_notification(notification_id, TOKEN_DICTIONARY):
    TOKEN = TOKEN_DICTIONARY.get('access_token','')
    URL_API = TOKEN_DICTIONARY.get('url_api')

    print(f'notification_id: {notification_id}')
    response = requests.delete(URL_API+'/notification/delete_json',
                            headers={'Authorization': 'Bearer '+TOKEN},
                            json={'id': notification_id},
                            # timeout=100,
                            )
    # if the access token is expired
    if response.status_code == 401:
        # try with new TOKEN
        TOKEN_DICTIONARY = refresh_call(TOKEN_DICTIONARY)
        TOKEN = TOKEN_DICTIONARY.get('access_token', '')
        response = requests.delete(URL_API+'/notification/delete_json',
            headers={'Authorization': 'Bearer '+TOKEN},
            json={'id':notification_id},
            #timeout=100,
        )

    # print(response.text)
    return response.text


# -----------V2 UPLOAD FUNCTIONS------------
def upload_v2_request(PARAM_DICTIONARY, TOKEN_DICTIONARY):
    """
    Request upload/v2 endpoint to get id_image, fileKey and uploadUrl
    """
    TOKEN = TOKEN_DICTIONARY.get('access_token', '')
    URL_API = TOKEN_DICTIONARY.get('url_api')
    
    # Activity for this repo is "edit"
    activity = "edit"
    options = '{}'
    
    data = {
        'activity': activity,
        'options': options
    }
    
    print(f'Requesting upload/v2 with data: {data}')
    
    response = requests.post(URL_API+'/upload/v2', 
                            headers={'Authorization': 'Bearer '+TOKEN, 'Content-Type': 'application/json'},
                            json=data
                            )
    
    if response.status_code == 401:
        TOKEN_DICTIONARY = refresh_call(TOKEN_DICTIONARY)
        TOKEN = TOKEN_DICTIONARY.get('access_token', '')
        # try with new TOKEN
        response = requests.post(URL_API+'/upload/v2', 
                                headers={'Authorization': 'Bearer '+TOKEN, 'Content-Type': 'application/json'},
                                json=data
                                )
    
    response_json = json.loads(response.text)
    print(f"Upload v2 request successful. Response json: {response_json}")
    
    return response_json


def upload_file_to_s3(file_path, upload_url, file_key):
    """
    Upload file to S3 using the signed URL
    """
    print(f'Uploading file {file_path} to S3...')
    
    try:
        with open(file_path, 'rb') as file:
            headers = {
                'Content-Type': 'image/png',
                'x-amz-meta-original-filename': file_key
            }
            
            response = requests.put(upload_url, 
                                  headers=headers,
                                  data=file)
            
            if response.status_code in [200, 204]:
                print("Upload successful!")
                return True
            else:
                print(f"Upload failed with status: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"Error uploading file: {e}")
        return False


def upload_url_to_s3(url, upload_url, file_key):
    """
    Upload file from URL to S3 using the signed URL
    """
    print(f'Uploading file from URL {url} to S3...')
    
    try:
        # Download the file first
        response = requests.get(url)
        response.raise_for_status()
        
        headers = {
            'Content-Type': 'image/png',
            'x-amz-meta-original-filename': file_key
        }
        
        upload_response = requests.put(upload_url, 
                                    headers=headers,
                                    data=response.content)
        
        if upload_response.status_code in [200, 204]:
            print("Upload successful!")
            return True
        else:
            print(f"Upload failed with status: {upload_response.status_code}")
            print(f"Response: {upload_response.text}")
            return False
            
    except Exception as e:
        print(f"Error uploading file from URL: {e}")
        return False


# -----------V2 NOTIFICATIONS FUNCTIONS------------
def get_notification_by_name_v2(name_list, TOKEN_DICTIONARY, id_image=None, id_task=None):
    """
    Get notifications with optional id_image or id_task filtering
    """
    TOKEN = TOKEN_DICTIONARY.get('access_token', '')
    URL_API = TOKEN_DICTIONARY.get('url_api')
    
    # Use the new notification endpoint
    notification_url = 'https://my3cinm78f.execute-api.eu-central-1.amazonaws.com/notifications'
    
    data = {'name_list': name_list}
    
    if id_image is not None:
        data['id_image'] = id_image
    if id_task is not None:
        data['id_task'] = id_task
    
    response = requests.post(notification_url,
                            headers={'Authorization': 'Bearer '+TOKEN, 'Content-Type': 'application/json'},
                            json=data,
                            timeout=100
                            )
    
    # if the access token is expired
    if response.status_code == 401:
        # try with new TOKEN
        TOKEN_DICTIONARY = refresh_call(TOKEN_DICTIONARY)
        TOKEN = TOKEN_DICTIONARY.get('access_token', '')
        response = requests.post(notification_url,
                                headers={'Authorization': 'Bearer '+TOKEN, 'Content-Type': 'application/json'},
                                json=data,
                                timeout=100
                                )
    
    # print(response.text)
    response_json = json.loads(response.text)
    return response_json.get('notifications_list', [])


def handle_upload_notifications(PARAM_DICTIONARY, TOKEN_DICTIONARY):
    """
    Handle upload notifications to get image processing results
    """
    ID_IMAGE = PARAM_DICTIONARY.get('ID_IMAGE')
    
    print(f'Waiting for upload notifications for image {ID_IMAGE}...')
    
    # check notifications to verify the upload status
    i = 0
    while i < 120:  # max 120 iterations -> then timeout
        i = i+1
        notifications_list = get_notification_by_name_v2('upload', TOKEN_DICTIONARY, id_image=ID_IMAGE)
        print(f'Upload notifications: {notifications_list}')
        
        if len(notifications_list) > 0:
            print(f'Upload processing completed for image_id {ID_IMAGE}')
            return True, notifications_list[0].get('data', {})

        # wait
        print('waiting for upload notification...')
        sleep(5)

    return False, {}


def handle_download_notifications(PARAM_DICTIONARY, TOKEN_DICTIONARY):
    """
    Handle download notifications to get generation results
    """
    ID_TASK = PARAM_DICTIONARY.get('ID_TASK')
    
    print(f'Waiting for download notifications for task {ID_TASK}...')
    
    # check notifications to verify the generation status
    i = 0
    while i < 120:  # max 120 iterations -> then timeout
        i = i+1
        notifications_list = get_notification_by_name_v2('edit_generate', TOKEN_DICTIONARY, id_task=ID_TASK)
        print(f'Download notifications: {notifications_list}')
        
        if len(notifications_list) > 0:
            print(f'Generation completed for task_id {ID_TASK}')
            return True, notifications_list[0].get('data', {})

        # wait
        print('waiting for download notification...')
        sleep(5)

    return False, {}


def handle_notifications(PARAM_DICTIONARY, TOKEN_DICTIONARY):

    ID_IMAGE = PARAM_DICTIONARY.get('ID_IMAGE')
    ID_PERSON = PARAM_DICTIONARY.get('ID_PERSON')

    # check notifications to verify the generation status
    i = 0
    while i < 120:  # max 120 iterations -> then timeout
        i = i+1
        notifications_list = get_notification_by_name('edit_generate', TOKEN_DICTIONARY)
        print(notifications_list)
        notifications_to_remove = [n for n in notifications_list if (n.get('name') == 'edit_generate' and n.get('data').get('address') == ID_IMAGE and n.get('data').get('id_person') == ID_PERSON)]

        print(f'notifications_to_remove: {notifications_to_remove}')
        # remove notifications
        result_delete = [delete_notification(n.get('id'), TOKEN_DICTIONARY) for n in notifications_to_remove]
        print(result_delete)

        if len(notifications_to_remove) > 0:
            print(f'download for image_id {ID_IMAGE} completed')
            return True, {**notifications_to_remove[0].get('data', {})}

        # wait
        print('waiting for notification...')
        sleep(5)

    return False, {}
