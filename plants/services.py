import random
import string
import time
import datetime
import copy
import decimal
import math
import numpy as np
import cv2
import io
from PIL import Image
from pylibdmtx import pylibdmtx
from django.utils.translation import gettext as _
from plants.models import Log, Plant, Attribute
from plants.entities import RichPlant
from users.models import User
from taggit.models import Tag


# Plants

def get_user_plants(user_id, access=[], tag_id=None, seeds=None):
    """Returns Plant-objects of user by user id"""
    if not access: 
        access = [0,1,2]  # wbithot specifying acces type - returns all plants 
    plant_ids = Log.objects.filter(data__owner=user_id).values_list('plant', flat=True)
    if seeds in [True, False]:
        if tag_id:
            tag = Tag.objects.get(id=tag_id)
            plants = Plant.objects.filter(id__in=plant_ids, tags__in=[tag], access_type__in=access, is_seed=seeds)
        else:
            plants = Plant.objects.filter(id__in=plant_ids, access_type__in=access, is_seed=seeds)
    else:
        if tag_id:
            tag = Tag.objects.get(id=tag_id)
            plants = Plant.objects.filter(id__in=plant_ids, tags__in=[tag], access_type__in=access)
        else:
            plants = Plant.objects.filter(id__in=plant_ids, access_type__in=access)
    return plants

def get_user_richplants(user_id, access=[], genus=None, tag_id=None, seeds=None) -> list:
    """Returns RichPlant-objects of user by user id"""
    if seeds in [True, False]:
        plants = get_user_plants(user_id, access, tag_id, seeds=seeds)
    else:
        plants = get_user_plants(user_id, access, tag_id)
    rich_plants = []
    for plant in plants:
        rich_plant = RichPlant(plant)
        if genus: 
            genus_in_plant = rich_plant.attrs.genus
            if genus_in_plant.lower() == genus.lower():
                rich_plants.append(rich_plant)
        else:
            rich_plants.append(rich_plant)
    return rich_plants

def create_new_plant(user: User) -> Plant:
    """New Plant creation"""
    new_upid = get_new_upid()
    new_plant = Plant(uid=new_upid, creator=user)
    new_plant.save()
    return new_plant

def get_new_upid():
    """Unique Plant ID Generator"""
    while True: 
        # Example: '798670'
        random_string = ''.join(random.choices(string.digits, k=6))
        
        # Check uniqueness
        if Plant.objects.filter(uid=random_string).count() == 0:
            upid = random_string
            break
    return upid

def filter_plants(rich_plants: list, filter_data: dict) -> list:
    """Filter plants according to filtered data"""
    plant_pass_grade = {}
    
    # pass grade calculation
    for plant in rich_plants:
        plant_pass_grade[plant] = 0
        for attr_name in filter_data:
            for val in filter_data[attr_name]:
                if getattr(plant.attrs, attr_name) == val:
                    plant_pass_grade[plant] += 1
    
    # check grade 
    filter_plants = []
    for plant in plant_pass_grade:
        if plant_pass_grade[plant] == len(filter_data):
            filter_plants.append(plant)

    return filter_plants

def detect_data_matrix(image) -> list:
    """
    | Detects PUIDs on image. 
    | Return list of dics with PUID and position (top, left)
    | or empty list
    """

    start_time_decoding = time.time()

    # resize image if it's too large
    image_for_decode = copy.deepcopy(image)
    i = Image.open(image_for_decode)
    w, h = i.size

    # optimal size of one side of image for decoding
    opt_size = 600
    if w > opt_size  or h > opt_size: 
        start_time_resizing = time.time()
        side = w if w > h else h
        scale_factor = opt_size / side
        image_resized = i.resize((int(w*scale_factor), int(h*scale_factor)),)
        img_byte_arr = io.BytesIO()
        image_resized.save(img_byte_arr, format='PNG')
        img = cv2.imdecode(np.frombuffer(img_byte_arr.getvalue(), np.uint8), 1)
        # TODO: add logger maybe?
        print(f'Resizing time: { time.time() - start_time_resizing } sec')
    else:
        image = image.file
        img = cv2.imdecode(np.frombuffer(image.read(), np.uint8), 1)

    height, width, channels = img.shape
   
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret,thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    result: list = pylibdmtx.decode(thresh)

    detected_puids = []
    for i in result:
        puid = {
            'puid': i.data.decode("utf-8"),
            'left': i.rect.left,
            'top': i.rect.top,
        }
        detected_puids.append(puid)

    # TODO: is it necessary to remove duplicates?

    # enrich dictionaries with information about position 
    if len(detected_puids) > 1:
        detected_puids = get_matrix_position_clarification(detected_puids, width, height)


    # TODO: add logger maybe?
    print(f'PUID decoding image ({w}x{h}) time: { time.time() - start_time_decoding } sec')

    return detected_puids

def get_matrix_position_clarification(pid_dics: list, image_width, image_height) -> list:
    """
    | Input: list of dics with PUID and position (top, left)
    | Output: same list of dics, but with list of position clarification, 
    |         where this PUID-matrix can be found on the photo and
    |         where this PUID-matrix is located relative to other matrices.
    | List shoud contain more than one item.
    | New list key is: `position_clarifications` 
    """

    EMPTY_POSITION_MATRIX = [
        [0, 0, 0],
        [0, 0, 0],
        [0, 0, 0],
    ]
    VERTICAL_POSITIONS = ['upper', 'middle', 'lower']
    HORIZONT_POSITIONS = ['left', 'middle', 'right']

    for i in pid_dics: 
        clarifications = []
        # get position clarification relative to image
        v = math.trunc( (image_height - i['top']) / (image_height/3) )
        h = math.trunc( i['left'] / (image_width/3) )
        position_matrix =  copy.deepcopy(EMPTY_POSITION_MATRIX)
        position_matrix[v][h] = 1
      
        if position_matrix[1][1] == 1:
            clrf = 'In the center of the photo.'
            clarifications.append(clrf)
        else:
            v_position = VERTICAL_POSITIONS[v]
            h_position = HORIZONT_POSITIONS[h]
            clrf = 'In the %s %s area of the photo.' % (v_position, h_position)
            clarifications.append(clrf)

        # get position clarification relative to other matrices
        position_relative_to_other = []
        for j in pid_dics: 
            v_diff = i['top'] - j['top']
            h_diff = i['left'] - j['left']

            abs_v_diff = abs(i['top'] - j['top'])
            abs_h_diff = abs(i['left'] - j['left'])
            
            if abs_v_diff > image_height / 10:   # more than 10% from image height
                if v_diff > 0:
                    clrf = 'Is higher than PUID: %s.' % j['puid']
                    clarifications.append(clrf)
                else:
                    clrf = 'Is lower than PUID: %s.' % j['puid']
                    clarifications.append(clrf)

            if abs_h_diff > image_width / 10:   # more than 10% from image width
                if h_diff > 0:
                    clrf = 'To the right of PUID: %s.' % j['puid']
                    clarifications.append(clrf)
                else:
                    clrf = 'To the left of PUID: %s.' % j['puid']
                    clarifications.append(clrf)

        if clarifications:
            i['position_clarifications'] = clarifications

    return pid_dics


def get_date_from_exif(image):
    """Get date when a photo was taken from EXIF"""
    image_to_read_exif = copy.deepcopy(image)
    i = Image.open(image_to_read_exif)

    try:
        dt_str = i._getexif()[36867]
        dt = datetime.datetime.strptime(dt_str, '%Y:%m:%d %H:%M:%S')
        return dt.strftime('%Y-%m-%d')
    except:
        return None


# Attributes

def get_filtered_attr_values_from_post(post_data) -> dict:
    """
    Convert post-data to filterable attrs dict:

    {
        'genus': ['Lithops', 'Conophytum'], 
        'species': ['karasmontana', 'Leslie'],
    }
    """
    filter_data = {}

    for key in post_data:
        if 'checkbox' in key:
            key = key.split('-')
            attr_name = key[1]
            attr_value = key[2]

            if attr_name in filter_data:
                filter_data[attr_name].append(attr_value)
            else:
                filter_data[attr_name] = [attr_value, ]
    return filter_data

def get_filteraible_attr_values(rich_plants: list) -> dict:
    """
    Returns all availiable filterable attrs dict:

    {
        'genus': [
                {'val':'lithops', 'checked':1},
                {'val':'conophytum', 'checked':1}, 
                {'val':'ophtalmophyllum', 'checked':1},
            ],
        'species':[
                {'val':'karasmontana', 'checked':1},
                {'val':'lesley', 'checked':1},
                {'val':'dorothea', 'checked':1},
            ],
    }    
    """
    filter_data = {}

    # generate blank structure with attr names
    for attr_name in Attribute.keys.get_all_keys():
        filter_data[attr_name] = []

    used_values = {}

    # fill
    for rp in rich_plants: 
        for attr_name in rp.attrs_as_dic:
            if attr_name not in used_values:
                used_values[attr_name] = []
            if check_is_attr_filterable(attr_name):
                value = rp.attrs_as_dic[attr_name]
                if value not in used_values[attr_name]:
                    filter_data[attr_name].append({'val':rp.attrs_as_dic[attr_name], 'checked':1})
                    used_values[attr_name].append(value)
    return filter_data

def filter_data_update(full_filled_filter_data, post_filter_data):
    # reset all checked status to 0 
    for attr_name in full_filled_filter_data:
        for d in full_filled_filter_data[attr_name]:
            d['checked'] = 0

    # set checked status to 1 as in posted data
    for post_attr_name in post_filter_data:
        for post_val in post_filter_data[post_attr_name]:
            for d in full_filled_filter_data[post_attr_name]:
                if d['val'] == post_val:
                    d['checked'] = 1

    return full_filled_filter_data

def check_is_attr_filterable(attr_key):
    attr = Attribute.objects.get(key=attr_key)
    return attr.filterable

def check_is_attr_show_in_list(attr):
    attr = Attribute.objects.get(key=attr_key)
    return attr.show_in_list

def get_attrs_titles_with_transl() -> dict:
    """Returns attribut titles and translation"""
    attr_titles = []
    attrs = Attribute.objects.filter(show_in_list=True).order_by('weight')
    for attr in attrs:
        attr_titles.append(attr.name)

    result = {}
    for title in attr_titles:
        result[title] = _(title)
    return result

def get_attr_keys_not_showing_in_list() -> list:
    attrs = Attribute.objects.filter(show_in_list=False)
    attr_keys = []
    for attr in attrs:
        attr_keys.append(attr.key)
    return(attr_keys)


# Users

def check_are_users_friends(user_1, user_2):
    """Check if one user is friend of another"""
    if user_1 in user_2.friends.all():
        return True
    else:
        return False

def check_is_user_friend_of_plant_owner(user, target_rich_plant):
    """Check if user is friend of Rich plant owner """
    target_user = User.objects.get(id=target_rich_plant.owner)
    if user in target_user.friends.all():
        return True
    else:
        return False

def check_is_user_owner_of_plant(user, target_rich_plant):
    """Check if user is owner of Rich plant"""
    if user.id == target_rich_plant.owner:
        return True
    else:
        return False


# Logs

def create_log(action_type: Log.ActionChoices, user: User, plant: Plant, data: dict, action_time=None):
    """Create new log"""

    for key in data:
        # selialize date fields
        if isinstance(data[key], datetime.date) or isinstance(data[key], datetime.datetime):
            data[key] = data[key].isoformat()
        # remove extra spaces in string attrs
        if type(data[key]) == str:
                data[key] = data[key].strip().replace('  ', ' ')

    new_log = Log(
        action_type = action_type,
        user = user, 
        plant = plant, 
        data = data
    )

    if action_time: 
        new_log.action_time = action_time
        
    new_log.save()