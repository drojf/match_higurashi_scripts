import os
import re
import sys
from matching_core import get_matching_script_paths_between_folders
import utility

class PS3ScriptContext:
    def __init__(self, script, line):
        self.script = script
        self.line = line

printContext = False

contextDict = {}

# Set to None to check all episodes
if len(sys.argv) != 2:
    print("Please specify which chapter number to validate")
    exit(-1)

episode_to_check = int(sys.argv[1])

print(f"Checking episode [{episode_to_check}]")

sprite_regex = re.compile('"(sprite\\/[^"]*)"')
sprite_portrait_regex = re.compile('"(portrait\\/[^"]*)"')

ps3_script_used_sprites = set()
ps3_script_portrait_sprites = set()

# Search scripts for ps3 sprites
for episode_num in range(1, utility.LAST_EPISODE + 1):
    if episode_to_check is not None and episode_num != episode_to_check:
        continue

    ps3_ep_dir = f'ps3_scripts\\ep{episode_num}'
    # print(ps3_ep_dir)

    for file in os.listdir(ps3_ep_dir):
        fullPath = os.path.join(ps3_ep_dir, file)
        with open(fullPath, 'r', encoding='utf-8') as f:
            for line in f.readlines():
                for match in sprite_regex.findall(line):
                    ps3_script_used_sprites.add(match)
                    contextDict[match] = PS3ScriptContext(fullPath, line)

                for match in sprite_portrait_regex.findall(line):
                    ps3_script_portrait_sprites.add(match)

# Sort alphabetically
ps3_script_used_sprites = sorted(list(ps3_script_used_sprites))
print(f"Found {len(ps3_script_used_sprites)} unique sprites in the ep{episode_to_check} game script")

# Load the manual sprite matching
sprite_matching_csv = 'imageComparer\\noconsole_output.txt.csv'
sprite_matching_rows = utility.load_rows(sprite_matching_csv)
sprite_matching_ps3_set = set()
for row in sprite_matching_rows:
    ps3_sprite_name = row[1]
    matching_ryukishi_name = row[2]
    sprite_matching_ps3_set.add(ps3_sprite_name)
    if matching_ryukishi_name in ['NO_MATCH', '']:
        print(f'ERROR: in {sprite_matching_csv}, ps3 name {ps3_sprite_name} has no match!')

print(f"Found {len(sprite_matching_ps3_set)} rows in the sprite matching csv {sprite_matching_csv}")


for ps3_used_name in ps3_script_used_sprites:
    if ps3_used_name not in sprite_matching_ps3_set:
        print(f"ERROR: {ps3_used_name} is used in game script, but has no matching in {sprite_matching_csv}")
        if printContext:
            context = contextDict[ps3_used_name]
            print(f"Context [{context.script}]: {context.line.strip()}")

print("--------- Portrait Sprites Needing Manual Generation -----------")
ps3_portrait_sprites = sorted(list(ps3_script_portrait_sprites))
for portrait in ps3_portrait_sprites:
    print(portrait)