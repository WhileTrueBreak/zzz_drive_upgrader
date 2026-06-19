from read_disk import get_main_stat, get_sub_stat, get_disk_title

import cv2
import numpy as np
import pyautogui
import re

main_stat_name_dict = {
    'physical dmg bonus%': 'physical dmg%',
    'fire dmg bonus%': 'fire dmg%',
    'ice dmg bonus%': 'ice dmg%',
    'electric dmg bonus%': 'electric dmg%',
    'ether dmg bonus%': 'ether dmg%',
    'wind dmg bonus%': 'wind dmg%',
}

def extract_float(s):
    match = re.search(r'[-+]?\d*\.\d+|[-+]?\d+', s)
    return float(match.group()) if match else None

def parse_disk_title(title):
    pattern = r'^(.*?)\s*\[(\d+)\]$'
    match = re.search(pattern, title)
    if match:
        return match.group(1), match.group(2)
    return None, None

def parse_main_stat(stat_line):
    pattern = r'^([\w\s]*) (.*)$'
    match = re.search(pattern, stat_line)
    if match:
        stat = match.group(1)
        value = match.group(2).replace(',', '')
        if value.endswith('%'):
            stat += '%'
            value = value[:-1]
        if stat in main_stat_name_dict:
            stat = main_stat_name_dict[stat]
        return stat, extract_float(value)
    return None, None

def parse_sub_stat(stat_line):
    pattern = r'^([\w\s]*) (.*)$'
    match = re.search(pattern, stat_line)
    if match:
        stat = match.group(1)
        value = match.group(2)
        if value.endswith('%'):
            stat += '%'
            value = value[:-1]
        return stat, extract_float(value)
    return None, None

def decode_disk(img):
    title = get_disk_title(img)
    name, disk_num = parse_disk_title(title)
    if not disk_num:
        print('No disk number found')
        return None
    main_stat_line = get_main_stat(img)
    main_stat_name, main_stat_value = parse_main_stat(main_stat_line)
    if not main_stat_name:
        print('No main stat found')
        return None
    main_stat = {'name': main_stat_name, 'value': main_stat_value}
    sub_stats = []
    for i in range(4):
        sub_stat_line = get_sub_stat(img, i)
        sub_stat_name, sub_stat_value = parse_sub_stat(sub_stat_line)
        if not sub_stat_name:
            print(f'No sub stat {i+1} found')
            continue
        sub_stats.append({'name': sub_stat_name, 'value': sub_stat_value})
    
    return {'name': name, 'disk_num': disk_num, 'main_stat': main_stat, 'sub_stats': sub_stats}

def parse_num_disks(text):
    pattern = r'\[(.*)\/'
    match = re.search(pattern, text)
    if match:
        num = match.group(1)
        return int(extract_float(num))
    return None

if __name__ == "__main__":

    # Take screenshot and convert to grayscale
    img = pyautogui.screenshot()
    img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Run extraction
    print(decode_disk(img))