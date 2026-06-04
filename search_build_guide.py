import requests
from bs4 import BeautifulSoup
import re
from itertools import chain
from pprint import pprint
import json
from scipy.optimize import minimize_scalar
import os
from datetime import datetime
from functools import lru_cache

from colorama import just_fix_windows_console
from colorama import Fore, Back, Style
just_fix_windows_console()

NORMALISE_TARGET_VALUE = 4

def load_disk_builds(file):
    with open(file, 'r') as f:
        return json.load(f)

def get_all_character_build_page():
    url = 'https://www.prydwen.gg/zenless/characters'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        character_elements = soup.find_all('div', class_='avatar-card')
        character_links = []
        for element in character_elements:
            # Find the first span within the character element
            span_element = element.find('span')
            
            if span_element:
                # Find the first <a> within the span
                a_element = span_element.find('a')
                
                if a_element and 'href' in a_element.attrs:
                    href = a_element['href']
                    character_links.append(href)
        return character_links

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def get_char_element(char_link):
    url = f'https://www.prydwen.gg{char_link}'
    soup = get_url_soup(url)
    if not soup: return None

    name_div = soup.find('div', class_='left-info')
    name = name_div.find('strong')
    if name.has_attr('class'):
        return name['class'][0]
    return 'Unknown'
    
def parse_disk_name(text):
    match = re.match(r'(.*) \(\d-pc\)', text)
    if match:
        return match.group(1)
    return text

@lru_cache(maxsize=2)
def get_url_soup(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def get_build_disks(char_link):
    url = f'https://www.prydwen.gg{char_link}'
    soup = get_url_soup(url)
    if not soup: return None

    build_guide_content = soup.find('div', class_='build-tips')
    main_disk_elements = build_guide_content.find_all('span', class_='zzz-weapon-name')
    contents = [parse_disk_name(element.text.lower()) for element in main_disk_elements]

    sub_disk_elements = build_guide_content.find_all('div', class_='information')
    sub_disk_list = []
    for sub_disk_element in sub_disk_elements:
        # sub_disk_lists.extend(sub_disk_element.find_all('li', string=re.compile("Recommended")))
        sub_disk_list.extend(sub_disk_element.find_all(lambda tag: tag.name == "li")) # and "Recommended" in tag.get_text()))
    for sub_disk in sub_disk_list:
        sub_disk_texts =[section.find('p').text.lower() for section in sub_disk.find_all('div', class_='zzz-set-min')]
        contents.extend(sub_disk_texts)
    contents = [content.strip() for content in contents]
    contents = list(set(contents))
    return contents

def parse_substat_build(substats_str):
    original_input = substats_str
    substats_str = substats_str.lower()
    substats_strs = substats_str.split(' or ')
    if len(substats_strs) > 1:
        # return [parse_substats(string) for string in substats_strs]
        return list(chain.from_iterable(parse_substat_build(s) for s in substats_strs))
    substats_str = substats_strs[0]
    keys = ["hp%","hp","atk%","atk","def%","def","pen","crit rate%","crit dmg%","anomaly proficiency","anomaly proficiency"]

    substats_str = re.sub(r'\s*\([^)]*\)', '', substats_str)


    substat_regex = r'(hp%)|(hp)|(atk%)|(atk)|(def%)|(def)|(pen)|(crit rate)|(crit dmg)|(anomaly proficiency)|(anomaly profiency)'
    ranking_regex = r'([=></]+)'
    substats = re.findall(substat_regex, substats_str)

    ranking_symbols = re.findall(ranking_regex, substats_str)

    substat_values = {"hp": 0, "hp%": 0, "atk": 0, "atk%": 0, "def": 0, "def%": 0, "pen": 0, "crit rate%": 0, "crit dmg%": 0, "anomaly proficiency": 0}
    current_value = 1
    low_value = 0.25
    decrease_factor = (1-low_value)/ranking_symbols.count('>')

    for i, substat in enumerate(substats):
        substat_index = next((i for i, s in enumerate(substat) if s), None)
        substat_values[keys[substat_index]] = current_value
        if i == len(substats) - 1: break
        if ranking_symbols[i] == '>': current_value -= decrease_factor
    return [substat_values]

def map_main_stats(name):
    mappings = {
        "hp%": "hp%",
        "hp": "hp",
        "atk%": "atk%",
        "atk": "atk",
        "def%": "def%",
        "def": "def",
        "pen": "pen",
        "crit rate": "crit rate%",
        "crit rate%": "crit rate%",
        "crit dmg": "crit dmg%",
        "crit dmg%": "crit dmg%",
        "anomaly proficiency": "anomaly proficiency",
        "pen ratio%": "pen ratio%",
        "physical dmg%": "physical dmg bonus%",
        "fire dmg%": "fire dmg bonus%",
        "ice dmg%": "ice dmg bonus%",
        "electric dmg%": "electric dmg bonus%",
        "ether dmg%": "ether dmg bonus%",
        "anomaly mastery": "anomaly mastery%",
        "energy regen": "energy regen%",
        "impact%": "impact%",
        "impact": "impact%",
    }
    return mappings[name.lower()]

def get_build_stats(char_link):
    url = f'https://www.prydwen.gg{char_link}'
    soup = get_url_soup(url)
    if not soup: return None

    build_guide_content = soup.find('div', class_='build-tips')
    build_main_list = build_guide_content.find_all('div', class_='main-stats')
    build_sub_list = build_guide_content.find('div', class_='sub-stats')

    builds = []
    for n in range(len(build_main_list)):
        main_stat_elements = build_main_list[n].find_all('div', class_='list-stats')
        main_stat_builds = [[],[],[]]
        for i, main_stat_element in enumerate(main_stat_elements):
            stats = re.split('[>=]+', main_stat_element.text)
            for stat in stats:
                main_stat_builds[i].append(stat.strip().lower())
        if build_sub_list is None:
            return None
        substat_build = build_sub_list.find('p').text
        substat_values = parse_substat_build(substat_build)
        builds.append({'main_stat_builds': main_stat_builds, 'substat_values': substat_values})
    return builds

def create_build(disks, stat_builds, char=''):
    if stat_builds is None:
        return None
    build = {}
    for disk in disks:
        disk_builds = []
        for stat_build in stat_builds:
            for substat_value in stat_build['substat_values']:
                disk_builds.append({
                    "substat_values":substat_value,
                    "1": {"main_stats":["hp"],},
                    "2": {"main_stats":["atk"],},
                    "3": {"main_stats":["def"],},
                    "4": {"main_stats":stat_build['main_stat_builds'][0]},
                    "5": {"main_stats":stat_build['main_stat_builds'][1]},
                    "6": {"main_stats":stat_build['main_stat_builds'][2]},
                    "char": [char],
                })
        build[disk] = disk_builds
    return {'disks': build}

def merge_builds(b1, b2):
    for disk in b2:
        if disk not in b1:
            b1[disk] = b2[disk]
            continue
        for disk_build2 in b2[disk]:
            no_match = True
            match_index = -1
            for i, disk_build1 in enumerate(b1[disk]):
                if disk_build2['substat_values'] == disk_build1['substat_values']:
                    no_match = False
                    match_index = i
                    break
            if no_match:
                b1[disk].append(disk_build2)
                continue
            for d4_main in disk_build2['4']['main_stats']:
                if d4_main not in  b1[disk][match_index]['4']['main_stats']:
                    b1[disk][match_index]['4']['main_stats'].append(d4_main)
            for d5_main in disk_build2['5']['main_stats']:
                if d5_main not in  b1[disk][match_index]['5']['main_stats']:
                    b1[disk][match_index]['5']['main_stats'].append(d5_main)
            for d6_main in disk_build2['6']['main_stats']:
                if d6_main not in  b1[disk][match_index]['6']['main_stats']:
                    b1[disk][match_index]['6']['main_stats'].append(d6_main)
            for char in disk_build2['char']:
                if char not in  b1[disk][match_index]['char']:
                    b1[disk][match_index]['char'].append(char)

def normalise_build_values(disk_builds, target_value=4):
    for disk_name in disk_builds:
        for disk_build in disk_builds[disk_name]:
            remap_substat_values(disk_build['substat_values'], target_value=target_value)

def remap_substat_values(substat_values, target_value=4):
    nonzero_substat_values = {key: value for key, value in substat_values.items() if value != 0}
    vals = nonzero_substat_values.values()

    top_4_vals = sorted(vals, reverse=True)[:4]
    multiplier = target_value/sum(top_4_vals)

    # print(f'prev:{substat_values}')
    for key in nonzero_substat_values:
        substat_values[key] = float(round(nonzero_substat_values[key]*multiplier, 2))
    # print(f'next:{substat_values}')

def get_last_profile_updated(char_link):
    url = f"https://www.prydwen.gg{char_link}"
    soup = get_url_soup(url)
    if not soup: return None

    # find the label
    label = soup.find(string=lambda s: s and "Last profile update" in s)

    if label:
        # the date is usually in the next element
        date_str = label.find_next().get_text(strip=True)
        # date_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)
        return datetime.strptime(date_str, "%d/%B/%Y")

    return None

def get_last_version_updates(char_link):
    url = f"https://www.prydwen.gg{char_link}"
    soup = get_url_soup(url)
    if not soup: return None

    update_soup = soup.find('div', {'class': 'last-update'})
    if update_soup == None:
        return [(0,0),(0,0),(0,0)]

    patch_updates = update_soup.find_all("div", {"class": "info"})[:3]

    patches = []
    for patch_update in patch_updates:
        version = re.findall(r'(\d+)\.(\d+)', patch_update.text)
        patches.extend(version)
    return patches

def version_checker(v1, v2):
    if v1[0] > v2[0]: return 1
    elif v1[0] < v2[0]: return -1
    elif v1[1] > v2[1]: return 1
    elif v1[1] < v2[1]: return -1
    return 0

def element_color_map(element):
    if element == 'Physical':
        return Fore.YELLOW
    elif element == 'Fire':
        return Fore.LIGHTRED_EX
    elif element == 'Electric':
        return Fore.BLUE
    elif element == 'Ether':
        return Fore.MAGENTA
    elif element == 'Ice':
        return Fore.CYAN
    elif element == 'Wind':
        return Fore.LIGHTGREEN_EX
    return Fore.LIGHTBLACK_EX
    

if __name__ == "__main__":
    char_links = get_all_character_build_page()

    if not os.path.exists('char_builds'):
        os.makedirs('char_builds')

    build = None
    for i,char_link in enumerate(char_links):
        char = char_link.split('/')[-1]
        element = get_char_element(char_link)

        print("Processing "+element_color_map(element)+f"{char}..."+Style.RESET_ALL)

        version_updates = get_last_version_updates(char_link)

        get_new_builds = False
        last_updated_time = get_last_profile_updated(char_link)
        if os.path.exists(f'char_builds/{char}_build.json') and last_updated_time:
            file_time = os.path.getmtime(f'char_builds/{char}_build.json')
            file_date = datetime.fromtimestamp(file_time)
            get_new_builds = last_updated_time > file_date

        if os.path.exists(f'char_builds/{char}_build.json'):
            with open(f'char_builds/{char}_build.json', 'r') as f:
                try:
                    content = json.load(f)
                    if 'version' in content:
                        for i,v in enumerate(content['version']):
                            if version_checker(version_updates[i], v) != 1: continue
                            get_new_builds = True
                            break
                    else:
                        get_new_builds = True
                except:
                    get_new_builds = True
        else:
            get_new_builds = True

        if get_new_builds:
            print(Fore.RED+"Getting updated build..."+Style.RESET_ALL)
            disks = get_build_disks(char_link)
            stats = get_build_stats(char_link)
            char_build = create_build(disks, stats, char=char)
            char_build['version'] = version_updates
            if char_build is None:
                continue
            
            with open(f'char_builds/{char}_build.json', 'w') as f:
                json.dump(char_build, f, indent=2)
        else:
            print(Fore.GREEN+"Build is up to date."+Style.RESET_ALL)
            char_build = load_disk_builds(f'char_builds/{char}_build.json')
        
        if build is None:
            build = char_build['disks']
        else:
            merge_builds(build, char_build['disks'])
        if i % 5 == 0 and i > 0:
            with open('builds.json', 'w') as f:
                json.dump(build, f, indent=2)
    with open('builds.json', 'w') as f:
        json.dump(build, f, indent=2)
    build = load_disk_builds('builds.json')
    normalise_build_values(build, target_value=NORMALISE_TARGET_VALUE)
    with open('builds_norm.json', 'w') as f:
        json.dump(build, f, indent=2)
