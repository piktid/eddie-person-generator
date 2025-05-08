import os
import sys
import argparse
from random import randint

from editPerson_utils import variate_person
from editPerson_api import start_call

if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument('--input_url', help='Image file url', type=str, default='https://images.piktid.com/frontend/studio/superid/upscaler_sample/21z.png')
    parser.add_argument('--input_filepath', help='Input image file absolute path', type=str, default=None)
    parser.add_argument('--output_filepath', help='Output image file absolute path', type=str, default=None)

    # Image parameters
    parser.add_argument('--id_image', help='Target image id, it overwrites the input path', type=str, default=None)
    parser.add_argument('--id_person', help='Person to modify', type=int, default=0)

    # Random generation parameters
    parser.add_argument('--keyword', help='Generation keyword', type=str, default=None)
    parser.add_argument('--seed', help='Generation seed', type=int, default=randint(0, 100000))

    args = parser.parse_args()

    # be sure to export your email and psw as environmental variables
    EMAIL = os.getenv("EDDIE_EMAIL")
    PASSWORD = os.getenv("EDDIE_PASSWORD")

    # Parameters
    ID_IMAGE = args.id_image  # Default is None, otherwise a string of a stored name
    ID_PERSON = args.id_person # Default is 0, otherwise a integer of a stored person

    # Generation parameters
    KEYWORD = args.keyword
    SEED = args.seed

    # Image parameters
    INPUT_URL = args.input_url 
    INPUT_PATH = args.input_filepath
    OUTPUT_PATH = args.output_filepath


    if INPUT_PATH is not None:
        if os.path.exists(INPUT_PATH):
            print(f'Using as input image the file located at: {INPUT_PATH}')
        else:
            print('Wrong filepath, check again')
            sys.exit()
    else:
        print('Input filepath not assigned, trying with URL..')
        if INPUT_URL is not None:
            print(f'Using the input image located at: {INPUT_URL}')
        else:
            print('Wrong input url, check again, exiting..')
            sys.exit()

    # log in
    TOKEN_DICTIONARY = start_call(EMAIL, PASSWORD)
    print(TOKEN_DICTIONARY)
    
    PARAM_DICTIONARY = {
            'INPUT_PATH': INPUT_PATH,
            'OUTPUT_PATH': OUTPUT_PATH,
            'INPUT_URL': INPUT_URL,
            'ID_IMAGE': ID_IMAGE,
            'ID_PERSON': ID_PERSON,
            'KEYWORD': KEYWORD,
            'SEED': SEED
        }

    # run different process based on batch variation or not

    response, final_path, ID_IMAGE = variate_person(PARAM_DICTIONARY, TOKEN_DICTIONARY) 
    
    print(f'Response: {response}, final_path: {final_path}, ID_IMAGE: {ID_IMAGE}')  