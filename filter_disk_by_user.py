from file_reader import load_jsonl, append_to_jsonl

import os

def filter_by_char(file):
    chars = []
    for disk_line in load_jsonl(file):
        chars.extend(disk_line['users'].keys())
    chars = list(set(chars))
    for char in chars:
        if os.path.exists(f'char_disks/{char}_disks.jsonl'):
            os.remove(f'char_disks/{char}_disks.jsonl')
        filtered_disks = []
        for disk_line in load_jsonl(file):
            if char in disk_line['users']:
                filtered_disks.append((disk_line, max(disk_line['users'][char])))
        filtered_disks.sort(key=lambda x: x[1], reverse=True)
        for disk_line, _ in filtered_disks:
            append_to_jsonl(disk_line, f'char_disks/{char}_disks.jsonl')

if __name__ == '__main__':
    filter_by_char('disks.jsonl')