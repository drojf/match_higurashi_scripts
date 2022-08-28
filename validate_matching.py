import os
from pathlib import Path
import re
import sys
from matching_core import get_matching_script_paths_between_folders
import utility


class PS3ScriptContext:
    def __init__(self, script, line):
        self.script = script
        self.line = line


def FindRegexInScripts(episode_to_check, regex):
    matchDict = set()
    contextDict = {}

    # Search scripts for ps3 sprites
    for episode_num in range(1, utility.LAST_EPISODE + 1):
        if episode_to_check is not None and episode_num != episode_to_check:
            continue

        ps3_ep_dir = f'ps3_scripts\\ep{episode_num}'
        # print(ps3_ep_dir)

        for file in os.listdir(ps3_ep_dir):
            fullPath = os.path.join(ps3_ep_dir, file)
            with open(fullPath, 'r', encoding='utf-8') as f:
                for line_any_slash in f.readlines():
                    line = line_any_slash.replace('\\', '/')
                    for match in regex.findall(line):
                        matchDict.add(match)
                        contextDict[match] = PS3ScriptContext(fullPath, line)

    return sorted(list(matchDict)), contextDict


def loadandCheckMatchingFromFile(filePath, only_warn_auto_match):
    sprite_matching_rows = utility.load_rows(filePath)
    matching_set = set()
    no_match_list = []
    for row in sprite_matching_rows:
        name = row[1]
        matching_ryukishi_name = row[2]
        match_type = row[5]
        matching_set.add(name)

        if only_warn_auto_match and match_type in ['NAEGLES', 'EFFECT', 'IDENTICAL', 'CONTRADICTORY']:
             continue

        if matching_ryukishi_name in ['NO_MATCH', '']:
                no_match_list.append(f'ERROR: in {filePath}, ps3 name {name} has no match!')

    return matching_set, no_match_list

def PrintStringsWithNoMatch(nameList, matchingSet, contextDict, csv_path, printContext) -> bool:
    errorCount = 0
    for name in nameList:
        if name not in matchingSet:
            errorCount += 1
            print(f"ERROR: {name} is used in game script, but has no matching in {csv_path}")
            if printContext:
                context = contextDict[name]
                print(f"Context [{context.script}]: {context.line.strip()}")

    print(f"ERROR: {errorCount} backgrounds had no match!")

    return errorCount == 0

# Check whether the sprite matching
def CheckSprites(printContext, episode):
    sprite_regex = re.compile('"(sprite\\/[^"]*)"')
    portrait_regex = re.compile('"(portrait\\/[^"]*)"')

    ps3_script_used_sprites, contextDict = FindRegexInScripts(episode, sprite_regex)
    ps3_script_portrait_sprites, _ = FindRegexInScripts(episode, portrait_regex)

    print(f"Found {len(ps3_script_used_sprites)} unique sprites in the ep{episode} game script")

    # Load the manual sprite matching
    sprite_matching_csv = 'imageComparer\\noconsole_output.txt.csv'
    sprite_matching_set, no_match_list = loadandCheckMatchingFromFile(sprite_matching_csv, only_warn_auto_match=False)

    for no_match_description in no_match_list:
        print(no_match_description)

    print(f"Found {len(sprite_matching_set)} rows in the sprite matching csv {sprite_matching_csv}")

    PrintStringsWithNoMatch(ps3_script_used_sprites, sprite_matching_set, contextDict, sprite_matching_csv, printContext)

    print("--------- Portrait Sprites Needing Manual Generation -----------")
    ps3_portrait_sprites = sorted(list(ps3_script_portrait_sprites))
    for portrait in ps3_portrait_sprites:
        print(portrait)


def CheckBackgrounds(printContext, episode):
    background_regex = re.compile('"(bg\\/[^"]*)"')

    ps3_script_used_bgs, contextDict = FindRegexInScripts(episode, background_regex)

    print(f"Found {len(ps3_script_used_bgs)} unique backgrounds in the ep{episode} game script")

    # Load the manual sprite matching
    bg_matching_csv = 'imageComparer\\manual_background_mapping.csv'
    bg_matching_set, no_match_list = loadandCheckMatchingFromFile(bg_matching_csv, only_warn_auto_match=True)

    print(f"Found {len(bg_matching_set)} rows in the sprite matching csv {bg_matching_csv}")

    # Get only the filename part of the path
    ps3_script_used_bgs = [Path(x).name for x in ps3_script_used_bgs]
    # print(ps3_script_used_bgs)
    # exit(-1)

    success = PrintStringsWithNoMatch(ps3_script_used_bgs, bg_matching_set, contextDict, bg_matching_csv, printContext)

    # Print rows which are unmatched and have been matched automatically
    for no_match_description in no_match_list:
        print(no_match_description)

    return len(no_match_list) == 0 and success


if __name__ == '__main__':
    printContext = False

    # Set to None to check all episodes
    if len(sys.argv) != 2:
        print("Please specify which chapter number to validate eg `python validate_matching.py 9`")
        exit(-1)

    episode = int(sys.argv[1])

    print(f"Checking episode [{episode}]")

    print(f"------------- Checking Sprites -----------------")
    CheckSprites(printContext, episode)

    print(f"------------- Checking Backgrounds -----------------")
    CheckBackgrounds(printContext, episode)
