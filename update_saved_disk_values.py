from level_disks import *
from search_build_guide import load_disk_builds
from file_reader import load_jsonl, append_to_jsonl

from pprint import pprint
import shutil

if __name__ == '__main__':
    disk_builds = load_disk_builds('builds_norm.json')
    if os.path.exists('updated_disks.jsonl'):
        os.remove('updated_disks.jsonl')
    for disk_line in load_jsonl('disks.jsonl'):
        disk = disk_line['disk']
        users = check_disk_user(disk, disk_builds)
        disk_line['users'] = users
        append_to_jsonl(disk_line, 'updated_disks.jsonl')
    shutil.copyfile('updated_disks.jsonl', 'disks.jsonl')
    os.remove('updated_disks.jsonl')

