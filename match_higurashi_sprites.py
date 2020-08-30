import json
import argparse

#these regexes are slightly different as DrawBust* has one argument before the bust name, ModDraw* has two
import re
import sys

from match_statistics import MatchStatistics
from match_statistics_to_csv import convertMatchingToCSV
from matching_core import get_matching_script_paths_between_folders, update_match_statistics, MatchConfiguration, CustomMatcher

LAST_EPISODE = 8


def save_statistics(match_statistics, reverse_match_statistics, output_path):
	def write_to_file(text: str, path: str):
		with open(path, 'w', encoding='utf-8') as output_file:
			output_file.write(text)

	print("\n\n----------------------------------------------")
	y = convertMatchingToCSV(match_statistics, sort_by_score=False)
	for x in y:
		print(x)
	write_to_file('\n'.join(y) + '\n', output_path + '.csv')

	print("\n\n----------------------------------------------")
	y = convertMatchingToCSV(match_statistics, sort_by_score=False, simple=True)
	for x in y:
		print(x)
	write_to_file('\n'.join(y) + '\n', output_path + '.simple.csv')

	print("\n\n----------------------------------------------")
	y = convertMatchingToCSV(reverse_match_statistics, sort_by_score=False)
	for x in y:
		print(x)
	write_to_file('\n'.join(y) + '\n', output_path + '.reversed.csv')


	json_string = json.dumps(match_statistics.statistics, sort_keys=True, indent=4)

	print(json_string)
	write_to_file(json_string, output_path)

	#dump reverse statistics
	json_string = json.dumps(reverse_match_statistics.statistics, sort_keys=True, indent=4)

	print(json_string)
	write_to_file(json_string, output_path + '.reversed.txt')


def doSpriteMatching():
	steamBustRegex = re.compile(r'(DrawBust|ChangeBust)[^\(]+\(\s*\d*\s*,\s*\"([^\"]+)')
	steamBustMatcher = CustomMatcher(steamBustRegex, 2)
	ps3BustRegex = re.compile(r'ModDraw[^\(]+\(\s*\d*\s*,\s*\d*\s*,\s*\"([^\"]+)')
	ps3BustMatcher = CustomMatcher(ps3BustRegex, 1)

	class MyParser(argparse.ArgumentParser):
		def error(self, message):
			sys.stderr.write('error: %s\n' % message)
			self.print_help()
			sys.exit(2)

	def normalize_time_of_day_and_portrait(ps3_image_path : str) -> str:
		return ps3_image_path.replace('/normal/','/').replace('/sunset/', '/').replace('/night/','/').replace('portrait/','sprite/')


	def keep_only_ryushiki_ps3(ps3_name):
		raise NotImplemented()


	match_statistics = MatchStatistics()
	reverse_match_statistics = MatchStatistics()
	output_path = 'noconsole_output.txt'

	NO_CONSOLE = True
	if NO_CONSOLE:
		for episode_num in range(1, LAST_EPISODE + 1):
			config = MatchConfiguration(steamBustMatcher,
										ps3BustMatcher,
										ps3_name_modification_function=normalize_time_of_day_and_portrait)

			matching_script_paths = get_matching_script_paths_between_folders(f'steam_scripts\\ep{episode_num}', f'ps3_scripts\\ep{episode_num}')
			for steam_script_path, ps3_script_path in matching_script_paths:
				update_match_statistics(match_statistics,
										reverse_match_statistics,
										steam_script_path,
										ps3_script_path,
										match_configuration=config)
	else:
		parser = MyParser(description='Match sprites between steam and ps3 scripts, given two input folders containing scripts as .txt files.')
		parser.add_argument('steam_scripts_folder', type=str, help='path containing steam scripts as .txt files')
		parser.add_argument('ps3_scripts_folder', type=str, help='path containing ps3 scripts as .txt files')
		parser.add_argument('output_file_path', type=str, help='name of file where results are written (JSON format)')
		parser.add_argument('--ignore_time_of_day_and_portrait', type=bool, default=False, help='ignore "normal", "sunset", "night", "portrait" in ps3 paths')
		parser.add_argument('--whitelist', type=bool, default=False, help='whitelist ps3 names')

		args = parser.parse_args()

		output_path = args.output_file_path

		ps3_filter_function = None
		if args.ignore_time_of_day:
			print("NOTE: ignoring time of day")
			ps3_filter_function = normalize_time_of_day_and_portrait
		else:
			print("NOTE: Keeping time of day")

		ps3_whitelist_function = None
		if args.whitelist:
			print("NOTE: whitelist not applied")
			ps3_whitelist_function = keep_only_ryushiki_ps3
		else:
			print("NOTE: applying whitelist")

		config = MatchConfiguration(steamBustMatcher, ps3BustMatcher)
		config.ps3_name_modification_function = ps3_filter_function
		config.ps3_whitelist_function = ps3_whitelist_function

		matching_script_paths = get_matching_script_paths_between_folders(args.steam_scripts_folder, args.ps3_scripts_folder)
		for steam_script_path, ps3_script_path in matching_script_paths:
			update_match_statistics(match_statistics,
									reverse_match_statistics,
									steam_script_path,
									ps3_script_path,
									match_configuration=config)

	#Save results to csv and json file
	save_statistics(match_statistics, reverse_match_statistics, output_path)


doSpriteMatching()
