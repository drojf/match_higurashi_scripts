# Higurashi Sprite/Background Matching

## Latest Matching

The latest sprite matching is kept in `imageCompararer/noconsole_output.txt.csv`

## Usage

### Important files

The file `imageComparer/noconsole_output.txt.csv` contains the latest sprite matching.
The file `imageComparer/manual_background_mapping.csv` contains the latest background matching (?).

### ImageComparer / `copy_images_using_mapping.py` setup

TODO: create an archive with all the image assets in advance?

1. For each game:
  1. Copy the modded game's `CG` folder to `imageComparer\external\ps3\ep[EPISODE_NUMBER]\CG`. For example, `imageComparer\external\ps3\ep9\CG` for episode 9 modded
  2. Copy the unmodded game's `CG` folder to `imageComparer\external\ryukishi\ep[EPISODE_NUMBER]\CG`. For example `imageComparer\external\ryukishi\ep9\CG` for episode 9 unmodded

### Sprite Matching

**NOTE: For legacy reasons, the "manual match" column of the sprite matching file is never used. That column is only used in the background file.**

1. Update the `LAST_EPISODE` variable in utility.py, to reflect the number of episodes currently released (see the `steam_scripts` folder and `ps3_scripts` folder)
  - Note: the generated files (`noconsole_output.*`) in the root directory will have every line changed compared to the previous version. This is normal.
2. Run `py match_higurashi_sprites.py`. This will generate an automated matching.
3. Run `py update_existing_matching.py`. This will merge the just generated automated matching with the file at `imageComparer/noconsole_output.txt.csv`, and output it `merged_output.csv`
4. Replace `imageComparer/noconsole_output.txt.csv` with `merged_output.csv` (you should compare the differences between these two files to make sure everything is correct)
5. Review the new rows in the file by calling `py compareImages.py sprite` from within the `imageComparer` folder
  - Make sure image comparer is setup and has all the CG files available (see above)
  - You only need to check the new rows
  - Check the automatic matches seem correct
  - Search the .csv file for `NO_MATCH`- and fill in those matches
6. Run `validate_matching.py [CHAPTER_NUMBER]`, and fix any problems that come up
7. Tell enumag to re-run his script for the new chapter with the updated mapping, and he should give you back a batch file
  - enumag will give you back a .sh file which copies the files.
  - add the line `set -e` to the top of this script if you want it to stop on the first error
8. The batch file expects all the games `CG` folders merged together, then the top level `CG` folder renamed as `sprites`.
  - drojf TODO: prepare a pre-generated version of this folder so it doens't need to be regenerated each timee
  - script also expects a `transparent.png` dummy file which will bue substituted for characters who have no matching sprites
9. Add the latest chapter's `CG` folder to the existing `CG` folder pack
10. Run the script enumag gave you, fix if necessary
11. This will produce an OGSprites folder to be included in the OG sprites and background pack

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

## Note about ep9 (Rei) onwards unmodded CG folder structure

The folder structure has changed for the unmodded Higurashi games from ep9 (rei) onwards.

### Old folder structure

Previously, most images were placed directly in the CG folder with a unique filename.

### New folder structure

Now sprites use the pattern `StreamingAssets\CG\sprites\[CHARACTER_NAME](\[VARIANT])\[FILENAME].png`:
 - The default outfit is like: `StreamingAssets\CG\sprites\mion\me_akuwaraia1.png`
 - The variant outfits are in a subfolder like: `StreamingAssets\CG\sprites\mion\sifuku\me_akuwaraia1.png`
 - Note that zoomed in images/eye images are in a folder like `StreamingAssets\CG\sprites\mion\eye\me_eyex1.png`

Backgrounds use the pattern `StreamingAssets\CG\sprites\[LOCATION]\[FILENAME].png`

I have tried to compensate for this in the matching/image copying scripts, but please keep this in mind when browsing the files.