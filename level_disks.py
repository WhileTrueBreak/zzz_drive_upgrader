from read_disk import get_main_stat, get_sub_stat, get_disk_title, get_num_disks
from disk_parser import decode_disk, parse_num_disks
from game_controller import *
from search_build_guide import merge_builds, load_disk_builds, NORMALISE_TARGET_VALUE, remap_substat_values
from file_reader import load_jsonl, append_to_jsonl

import keyboard
import cv2
import numpy as np
import pyautogui
import re
import bisect
from itertools import product
import copy
from enum import Enum
import time
import json
from pprint import pprint
import matplotlib.pyplot as plt

from pynput import keyboard
import threading

STOP_FLAG = False

def on_press(key):
    global STOP_FLAG
    try:
        # Check for the 'p' key (case-insensitive)
        if hasattr(key, 'char') and key.char and key.char.lower() == 'p':
            print("\n[P] pressed — stopping script.")
            STOP_FLAG = True
            return False  # stop listener thread
    except Exception:
        pass

def start_keyboard_listener():
    listener = keyboard.Listener(on_press=on_press)
    listener.daemon = True  # will close with main program
    listener.start()
    print("Keyboard listener started.")
    print("Press 'p' to stop the script.")
    return listener

sub_stat_increases = {
    "hp": 118,
    "hp%": 3.0,
    "atk": 19,
    "atk%": 3.0,
    "def": 15,
    "def%": 4.8,
    "pen": 9,
    "crit rate%": 2.4,
    "crit dmg%": 4.8, 
    "anomaly proficiency": 9
}
main_stat_values = {
    "hp":                   [550, 880, 1210, 1540, 1870, 2200],
    "atk":                  [79, 126, 173, 221, 268, 316],
    "def":                  [46, 73, 101, 128, 156, 184],
    "hp%":                  [7.5, 12, 16.5, 21, 25.5, 30],
    "atk%":                 [7.5, 12, 16.5, 21, 25.5, 30],
    "def%":                 [12, 19.2, 26.4, 33.6, 40.8, 48],
    "crit rate%":           [6, 9.6, 13.2, 16.8, 20.4, 24],
    "crit dmg%":            [12, 19.2, 26.4, 33.6, 40.8, 48],
    "anomaly proficiency":  [23, 36, 50, 64, 78, 92],
    "pen ratio%":           [6, 9.6, 13.2, 16.8, 20.4, 24],
    "physical dmg bonus%":  [7.5, 12, 16.5, 21, 25.5, 30],
    "fire dmg bonus%":      [7.5, 12, 16.5, 21, 25.5, 30],
    "ice dmg bonus%":       [7.5, 12, 16.5, 21, 25.5, 30],
    "electric dmg bonus%":  [7.5, 12, 16.5, 21, 25.5, 30],
    "ether dmg bonus%":     [7.5, 12, 16.5, 21, 25.5, 30],
    "anomaly mastery%":     [7.5, 12, 16.5, 21, 25.5, 30],
    "energy regen%":        [15, 24, 33, 42, 51, 60],
    "impact%":              [4.5, 7.2, 9.9, 12.6, 15.3, 18],
}

def get_disk_upgrades(disk):
    if disk == None:
        return None
    stat_arr = main_stat_values[disk['main_stat']['name']]
    main_stat_value = disk['main_stat']['value']
    index = bisect.bisect_right(stat_arr, main_stat_value) - 1
    if index >= 0:
        return 5 - index
    else:
        print(f"No element in array is ≤ {main_stat_value}")
        return None

def get_substat_upgrades(disk, index):
    if disk == None:
        return None
    substat = disk['sub_stats'][index]
    return substat['value']//sub_stat_increases[substat['name']]

def get_disk_value(disk, disk_build):
    if disk == None:
        return None
    build_subset_values = disk_build['substat_values']
    disk_substat_values = [build_subset_values[substat['name']] for substat in disk['sub_stats']]
    total_disk_value = 0
    for i, substat in enumerate(disk['sub_stats']):
        total_disk_value += get_substat_upgrades(disk, i)*disk_substat_values[i]
    return total_disk_value

def clone_disk(disk):
    if disk == None:
        return None
    return copy.deepcopy(disk)

def calc_disk_potental(disk, disk_build):
    if disk == None:
        return None
    
    num_substats = len(disk['sub_stats'])
    if num_substats == 4:
        build_subset_values = disk_build['substat_values']
        disk_substat_values = [build_subset_values[substat['name']] for substat in disk['sub_stats']]
        rolls_left = get_disk_upgrades(disk)

        disk_value = get_disk_value(disk, disk_build)

        num_permutations = len(disk_substat_values) ** rolls_left
        total = 0
        all_combos = []
        for combo in product(disk_substat_values, repeat=rolls_left):
            total += disk_value+sum(combo)
            all_combos.append(disk_value+sum(combo))
        return total / num_permutations, all_combos
    else:
        current_substats = [substat['name'] for substat in disk['sub_stats']]
        available_substats = [substat for substat in sub_stat_increases.keys() if substat not in current_substats and substat != disk['main_stat']['name']]
        disk_potentials = []
        all_potentials = []
        for substat in available_substats:
            new_disk = clone_disk(disk)
            new_disk['sub_stats'].append({'name': substat, 'value': sub_stat_increases[substat]})
            disk_level = 5-get_disk_upgrades(disk)
            new_disk['main_stat']['value'] = main_stat_values[new_disk['main_stat']['name']][disk_level+1]
            avg_potential, all_combos = calc_disk_potental(new_disk, disk_build)
            all_potentials.extend(all_combos)
            disk_potentials.append(avg_potential)
        return sum(disk_potentials)/len(disk_potentials), all_potentials

def check_disk_stats(disk):
    if disk == None:
        return None
    mainstat = disk['main_stat']
    if mainstat['value'] > main_stat_values[mainstat['name']][5]:
        print(f"Main stat {mainstat['name']} = {mainstat['value']} is too high, possibly missing decimal dot. Fixing to {mainstat['value']/10}")
        mainstat['value'] /= 10
    for substat in disk['sub_stats']:
        if substat['value'] < sub_stat_increases[substat['name']]*7:
            continue
        print(f"Substat {substat['name']} = {substat['value']} is too high, possibly missing decimal dot. Fixing to {substat['value']/10}")
        substat['value'] /= 10

def is_disk_main_stat_good(disk, disk_build):
    if disk == None:
        return None
    if disk['disk_num'] not in disk_build:
        print(f"Disk number {disk['disk_num']} not in disk_build")
        return None
    if disk['main_stat']['name'] not in disk_build[disk['disk_num']]['main_stats']:
        return False
    return True

MAIN_STAT_VALUE = 4
DISK_THRESHOLDS = {
    '1': {'top_percentile': 0.15, 'sub_stat_threshold': 10.5},
    '2': {'top_percentile': 0.15, 'sub_stat_threshold': 10.5},
    '3': {'top_percentile': 0.15, 'sub_stat_threshold': 10.5},
    '4': {'top_percentile': 0.15, 'sub_stat_threshold': 10.5},
    '5': {'top_percentile': 0.15, 'sub_stat_threshold': 10.5},
    '6': {'top_percentile': 0.15, 'sub_stat_threshold': 10.5},
}

class UpgradeStutus(Enum):
    UPGRADE_FINISHED = 0
    BAD_SUBSTATS = 1
    UNKNOWN_DISK = 2
    BAD_MAIN_STAT = 3

def adjust_sub_stat_for_main_stat(disk_build, disk):
    if disk['main_stat']['name'] not in disk_build['substat_values'].keys():
        return disk_build

    new_disk_build = disk_build.copy()
    new_disk_build['substat_values'][disk['main_stat']['name']] = 0
    remap_substat_values(new_disk_build['substat_values'], target_value=NORMALISE_TARGET_VALUE)

    return new_disk_build

def check_disk_potential(disk, disk_builds, threshold=DISK_THRESHOLDS, main_stat_value=MAIN_STAT_VALUE):
    if disk == None:
        return None
    check_disk_stats(disk)
    max_potential = 0
    if disk['name'] not in disk_builds:
        return 0
    for disk_build in disk_builds[disk['name']]:
        is_main_stat_good = is_disk_main_stat_good(disk, disk_build)
        disk_build = adjust_sub_stat_for_main_stat(disk_build, disk)
        if is_main_stat_good == None:
            continue
        disk_potential, all_combos = calc_disk_potental(disk, disk_build)
        if disk_potential == None:
            continue
        sorted_values = sorted(all_combos)
        top_percentile = sorted_values[int(len(sorted_values) * (1-threshold[disk['disk_num']]['top_percentile'])):]
        avg_top_percentile = sum(top_percentile) / len(top_percentile)
        if is_main_stat_good:
            avg_top_percentile += main_stat_value
        if avg_top_percentile > max_potential:
            max_potential = avg_top_percentile
    return max_potential

def check_disk_user(disk, disk_builds, threshold=DISK_THRESHOLDS, main_stat_value=MAIN_STAT_VALUE):
    if disk == None:
        return None
    check_disk_stats(disk)
    users = {}
    for disk_build in disk_builds[disk['name']]:
        is_main_stat_good = is_disk_main_stat_good(disk, disk_build)
        if is_main_stat_good == None:
            continue
        disk_potential, _ = calc_disk_potental(disk, disk_build)
        if disk_potential == None:
            continue
        if is_main_stat_good:
            disk_potential += main_stat_value
        if disk_potential < threshold[disk['disk_num']]['sub_stat_threshold']:
            continue
        for char in disk_build['char']:
            if char in users:
                users[char].append(disk_potential)
            else:
                users[char] = [disk_potential]
        # users.extend(disk_build['char'])
    return users

def upgrade_selected_until_threshold(disk_builds, threshold=DISK_THRESHOLDS):
    while True:
        img = pyautogui.screenshot()
        img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        disk = decode_disk(img)
        check_disk_stats(disk)

        available_upgrades = get_disk_upgrades(disk)
        disk_potential = check_disk_potential(disk, disk_builds, threshold=threshold)
        if disk_potential == None:
            print("Disk potential could not be calculated")
            return UpgradeStutus.UNKNOWN_DISK, disk, None
        if disk_potential >= threshold[disk['disk_num']]['sub_stat_threshold'] and available_upgrades > 0:
            print(f"Disk potential: {disk_potential:.2f}, {available_upgrades} upgrades available")
            upgrade_once(click_delay=0.5, is_last=(available_upgrades==1))
            pyautogui.sleep(2)
        elif disk_potential < threshold[disk['disk_num']]['sub_stat_threshold']:
            print(f"Disk potential: {disk_potential:.2f} is too low, not upgrading")
            return UpgradeStutus.BAD_SUBSTATS, disk, None
        elif available_upgrades == 0:
            print(f"Disk potential: {disk_potential:.2f}, no upgrades available")
            users = check_disk_user(disk, disk_builds, threshold=DISK_THRESHOLDS)
            return UpgradeStutus.UPGRADE_FINISHED, disk, users

def upgrade_current_disk(disk_builds):
    view_disk(click_delay=0.5)
    status, disk, users = upgrade_selected_until_threshold(disk_builds, threshold=DISK_THRESHOLDS)
    go_back(click_delay=0.5)
    if status == UpgradeStutus.UPGRADE_FINISHED:
        print(f'Users: {list(users.keys())}')
        output = {'disk': disk, 'users': users}
        append_to_jsonl(output, 'disks.jsonl')
        toggle_lock(click_delay=0.5)
    elif status == UpgradeStutus.BAD_SUBSTATS:
        toggle_trash(click_delay=0.5)

def update_all_disks(disk_builds):
    global STOP_FLAG
    while True:
        img = pyautogui.screenshot()
        img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        storage_text = get_num_disks(img)
        num_disks = parse_num_disks(storage_text)

        if num_disks == None:
            print('Could not parse number of disks')
            cont = input("Continue? (y/n): ")
            if cont.lower() != 'y':
                break
        else:
            print(f'Num disks left: {num_disks}')
        if num_disks == 0:
            break
        
        upgrade_current_disk(disk_builds)
        if STOP_FLAG: 
            break
        cycle_next()
        if STOP_FLAG: 
            break

if __name__ == '__main__':
    listener = start_keyboard_listener()

    switchToZZZ()
    disk_builds = load_disk_builds('builds_norm.json')
    update_all_disks(disk_builds)

    ## Manual check disk potential ##

    # img = pyautogui.screenshot()
    # img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    # img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # disk = decode_disk(img)
    # check_disk_stats(disk)

    # available_upgrades = get_disk_upgrades(disk)
    # disk_potential = check_disk_potential(disk, disk_builds, threshold=DISK_THRESHOLDS)
    # if disk_potential == None:
    #     print("Disk potential could not be calculated")
    # else:
    #     print(f"Disk potential: {disk_potential:.2f}, {available_upgrades} upgrades available")
    #     users = check_disk_user(disk, disk_builds, threshold=DISK_THRESHOLDS)
    #     print(f'Users: {list(users.keys())}')