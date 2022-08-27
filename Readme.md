# Higurashi Sprite/Background Matching

## Latest Matching

The latest sprite matching is kept in `imageCompararer/noconsole_output.txt.csv`

## Usage

### Important files

The file `imageComparer/noconsole_output.txt.csv` contains the latest sprite matching.
The file `imageComparer/manual_background_mapping.csv` contains the latest background matching (?).

### Sprite Matching

1. Update the `LAST_EPISODE` variable in utility.py, to reflect the number of episodes currently released (see the `steam_scripts` folder and `ps3_scripts` folder)
  - Note: the generated files (`noconsole_output.*`) in the root directory will have every line changed compared to the previous version. This is normal.
2. Run `py match_higurashi_sprites.py`. This will generate an automated matching.
3. Run `py update_existing_matching.py`. This will merge the just generated automated matching with the file at `imageComparer/noconsole_output.txt.csv`, and output it `merged_output.csv`
4. Replace `imageComparer/noconsole_output.txt.csv` with `merged_output.csv` (you should compare the differences between these two files to make sure everything is correct)

## Background matching

See the script `match_higurashi_backgrounds.py`. I can't remember how much I got working, but you can ask me to have a look at it if it would be useful to you.

## Descriptions of what each folder contains

- automatic sprite match folders:
  - normal: This folder shouldn't be used - it contains matches which consider the time-of-day variants, which isn't important to us as we can regenerate the time-of-day variants ourselves if we know the base sprite
  - ignore_time_of_day: This contains the automated matches (output of the `match_higurashi_sprites_.py` script) which should be used. It ignores/merges the time-of-day variants.
- misc: I don't exactly remember, but Naegles helped me match some images (manually?) in the past. This folder contains the work they did.
- preprocessed_common: Contains extra images not present in the unmodded game, which are common to all arcs
- preprocessed_small: Contains extra images not present in the unmodded game, which are different for each arc (or not present for some arcs)
- ps3_scripts: Contains our mod's scripts, which reference the PS3 sprites and backgrounds
- steam_scripts: Contains the unmodded scripts, which reference the OG sprites and backgrounds