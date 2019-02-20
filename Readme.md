Example: 

`python match_higurashi_sprites.py "C:\games\Steam\steamapps\common\Higurashi When They Cry\HigurashiEp01_Data\StreamingAssets\Scripts" "C:\drojf\large_projects\umineko\onikakushi\Update" out.txt`

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