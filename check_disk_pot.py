from level_disks import *

if __name__ == '__main__':
    listener = start_keyboard_listener()

    switchToZZZ()
    disk_builds = load_disk_builds('builds_norm.json')

    ## Manual check disk potential ##

    img = pyautogui.screenshot()
    img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    disk = decode_disk(img)
    check_disk_stats(disk)

    available_upgrades = get_disk_upgrades(disk)
    disk_potential = check_disk_potential(disk, disk_builds, threshold=DISK_THRESHOLDS)
    if disk_potential == None:
        print("Disk potential could not be calculated")
    else:
        print(f"Disk potential: {disk_potential:.2f}, {available_upgrades} upgrades available")
        users = check_disk_user(disk, disk_builds, threshold=DISK_THRESHOLDS)
        print(f'Users: {list(users.keys())}')