import math
import os
import sys
import pyautogui
from keyboard import press
from multiprocessing import Queue
import ctypes
import random

VIEW_BUTTON = (1693,835)
START_UPGRADE_BUTTON = (1420,224)
ADD_TO_NEXT_BUTTON = (1294,871)
UPGRADE_BUTTON = (1522,869)
UPGRADE_BACK_BUTTON = (118,53)
REFUND_COMFIRM_BUTTON = (954,728)

TRASH_TOGGLE = (1443, 834)
LOCK_TOGGLE = (1530, 832)

FILTER_BUTTON = (152, 927)
S_FILTER_BUTTON = (1425, 439)

DELAY_RAND_MIN = 0
DELAY_RAND_MAX = 0.2

def pyautogui_sleep(delay):
    global DELAY_RAND_MIN, DELAY_RAND_MAX
    act_delay = delay + random.uniform(DELAY_RAND_MIN, DELAY_RAND_MAX)
    pyautogui.sleep(act_delay)

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def switchToZZZ():
    ZZZWindow = pyautogui.getWindowsWithTitle("ZenlessZoneZero")[0]
    if ZZZWindow.isActive == False:
        print("Switching to ZenlessZoneZero...")
        pyautogui.press(
            "altleft"
        )  # Somehow this is needed to switch to the window, Why though?
        ZZZWindow.activate()
        pyautogui_sleep(1)
        print("Switched to ZenlessZoneZero")

def upgrade_once(click_delay=0.5, is_last=False):
    if not is_admin():
        print("Please run as admin")
        sys.exit(1)
    switchToZZZ()
    pyautogui.moveTo(START_UPGRADE_BUTTON)
    pyautogui.click()
    pyautogui_sleep(click_delay)
    pyautogui.moveTo(ADD_TO_NEXT_BUTTON)
    pyautogui.click()
    pyautogui_sleep(click_delay)
    pyautogui.moveTo(UPGRADE_BUTTON)
    pyautogui.click()
    pyautogui_sleep(click_delay)
    if not is_last:
        pyautogui.moveTo(UPGRADE_BACK_BUTTON)
        pyautogui.click()
        pyautogui_sleep(click_delay)
    else:
        pyautogui_sleep(click_delay)
        pyautogui.moveTo(REFUND_COMFIRM_BUTTON)
        pyautogui.click()
        pyautogui_sleep(click_delay)

def view_disk(click_delay=0.5):
    if not is_admin():
        print("Please run as admin")
        sys.exit(1)
    switchToZZZ()
    pyautogui.moveTo(VIEW_BUTTON)
    pyautogui.click()
    pyautogui_sleep(click_delay)

def go_back(click_delay=0.5):
    if not is_admin():
        print("Please run as admin")
        sys.exit(1)
    switchToZZZ()
    pyautogui.moveTo(UPGRADE_BACK_BUTTON)
    pyautogui.click()
    pyautogui_sleep(click_delay)

def toggle_trash(click_delay=0.5):
    if not is_admin():
        print("Please run as admin")
        sys.exit(1)
    pyautogui_sleep(click_delay)
    pyautogui.click(TRASH_TOGGLE)
    pyautogui_sleep(click_delay)

def toggle_lock(click_delay=0.5):
    if not is_admin():
        print("Please run as admin")
        sys.exit(1)
    pyautogui_sleep(click_delay)
    pyautogui.click(LOCK_TOGGLE)
    pyautogui_sleep(click_delay)

def cycle_next(click_delay=0.5):
    if not is_admin():
        print("Please run as admin")
        sys.exit(1)
    switchToZZZ()
    pyautogui.moveTo(FILTER_BUTTON)
    pyautogui.click()
    pyautogui_sleep(click_delay)
    pyautogui.moveTo(S_FILTER_BUTTON)
    pyautogui.click()
    pyautogui_sleep(click_delay)
    pyautogui.moveTo(S_FILTER_BUTTON)
    pyautogui.click()
    pyautogui_sleep(click_delay)
    pyautogui.moveTo(UPGRADE_BACK_BUTTON)
    pyautogui.click()
    pyautogui_sleep(click_delay)

if __name__ == "__main__":
    cycle_next()
    # switchToZZZ()
    # upgrade_once()
