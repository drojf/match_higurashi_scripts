import json
import argparse

#these regexes are slightly different as DrawBust* has one argument before the bust name, ModDraw* has two
import sys

from match_statistics import MatchStatistics
from match_statistics_to_csv import convertMatchingToCSV
from matching_core import get_matching_script_paths_between_folders, update_match_statistics


class MyParser(argparse.ArgumentParser):
	def error(self, message):
		sys.stderr.write('error: %s\n' % message)
		self.print_help()
		sys.exit(2)

def write_to_file(text : str, path : str):
	with open(path, 'w', encoding='utf-8') as output_file:
		output_file.write(text)

def normalize_time_of_day(ps3_image_path : str):
	return ps3_image_path.replace('/normal/','/').replace('/sunset/', '/').replace('/night/','/')


def keep_only_ryushiki_ps3(ps3_name):
	raise NotImplemented()

parser = MyParser(description='Match sprites between steam and ps3 scripts, given two input folders containing scripts as .txt files.')
parser.add_argument('steam_scripts_folder', type=str, help='path containing steam scripts as .txt files')
parser.add_argument('ps3_scripts_folder', type=str, help='path containing ps3 scripts as .txt files')
parser.add_argument('output_file_path', type=str, help='name of file where results are written (JSON format)')
parser.add_argument('--ignore_time_of_day', type=bool, default=False, help='ignore "normal", "sunset", "night" in ps3 paths')
parser.add_argument('--whitelist', type=bool, default=False, help='whitelist ps3 names')

args = parser.parse_args()

match_statistics = MatchStatistics()
reverse_match_statistics = MatchStatistics()

ps3_filter_function = None
if args.ignore_time_of_day:
	print("NOTE: ignoring time of day")
	ps3_filter_function = normalize_time_of_day
else:
	print("NOTE: Keeping time of day")

ps3_whitelist_function = None
if args.whitelist:
	print("NOTE: whitelist not applied")
	ps3_whitelist_function = keep_only_ryushiki_ps3
else:
	print("NOTE: applying whitelist")


matching_script_paths = get_matching_script_paths_between_folders(args.steam_scripts_folder, args.ps3_scripts_folder)
for steam_script_path, ps3_script_path in matching_script_paths:
	update_match_statistics(match_statistics,
	                        reverse_match_statistics.statistics,
	                        steam_script_path,
	                        ps3_script_path,
	                        ps3_filter_function,
	                        ps3_whitelist_function=ps3_whitelist_function)

print("\n\n----------------------------------------------")
y = convertMatchingToCSV(match_statistics)
for x in y:
	print(x)
write_to_file('\n'.join(y), args.output_file_path + '.csv')

print("\n\n----------------------------------------------")
y = convertMatchingToCSV(reverse_match_statistics)
for x in y:
	print(x)
write_to_file('\n'.join(y), args.output_file_path + '.reversed.csv')


json_string = json.dumps(match_statistics.statistics, sort_keys=True, indent=4)

print(json_string)
write_to_file(json_string, args.output_file_path)

#dump reverse statistics
json_string = json.dumps(reverse_match_statistics.statistics, sort_keys=True, indent=4)

print(json_string)
write_to_file(json_string, args.output_file_path + '.reversed.txt')

#normal night sunset
