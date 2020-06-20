# Higurashi Sprite/Background Matching

## Latest Matching

The latest sprite matching is kept in `imageCompararer/noconsole_output.txt.csv`

## Usage

Double click `run_ignore_time_of_day.bat` or examine it for an exmple usage.

### Arguments

```
usage: match_higurashi_sprites.py [-h]  steam_scripts_folder  ps3_scripts_folder  output_file_path


Match sprites between steam and ps3 scripts, given two input folders
containing scripts as .txt files. The two scripts are matched if they have
the same name in both folders.

positional arguments:
  steam_scripts_folder  path containing steam scripts as .txt files
  ps3_scripts_folder    path containing ps3 scripts as .txt files
  output_file_path      name of file where results are written (JSON format)

optional arguments:
  -h, --help            show this help message and exit
```

## Background matching

See the script `match_higurashi_backgrounds.py`. I can't remember how much I got working, but you can ask me to have a look at it if it would be useful to you.