import re

from match_higurashi_backgrounds_dup_finder import QuestionArcsBackgroundRemapper
from match_statistics import MatchStatistics
from match_statistics_to_csv import convertMatchingToCSV
from matching_core import get_matching_script_paths_between_folders, update_match_statistics, MatchConfiguration, CustomMatcher
from match_higurashi_sprites import save_statistics

LAST_EPISODE = 8

def doBackgroundMatching():
	remapper = QuestionArcsBackgroundRemapper('background_matching_intermediate/ryukishi_sha_dups.csv')

	# Treat blur, background/flashback as the same. Remove the "background/" prefix
	def ps3_modification_function(ps3_name : str):
		return ps3_name.replace("blur/", "").replace("background/flashback/", "").replace("background/", "").replace("greyscale/", "").replace("negative/", "").lower()

	def steam_name_modification_function(name: str):
		remapped_name = remapper.get_mapping(name.lower())
		if remapped_name is None:
			return name.lower()
		else:
			return remapped_name


	# The steam and ps3 background functions are the same
	steamBackgroundRegex = re.compile(r'((ChangeScene)|(DrawScene)|(DrawSceneWithMask))\s*\(\s*"([^"]*)"')
	steamBackgroundMatcher = CustomMatcher(steamBackgroundRegex, 5)
	ps3BackgroundMatcher = steamBackgroundMatcher

	match_statistics = MatchStatistics()
	reverse_match_statistics = MatchStatistics()
	output_path = 'background_matching_intermediate/auto_matching'

	# Set configuration for matching
	# Only scan files in the 'background' folder
	config = MatchConfiguration(steamBackgroundMatcher,
								ps3BackgroundMatcher,
								ps3_whitelist_function=lambda x: 'background/' in x.lower(),
								ps3_name_modification_function=ps3_modification_function,
								steam_name_modification_function=steam_name_modification_function,
								enable_matcher_background_filter=True)

	for episode_num in range(1, LAST_EPISODE + 1):
		matching_script_paths = get_matching_script_paths_between_folders(f'steam_scripts\\ep{episode_num}',
																		  f'ps3_scripts\\ep{episode_num}')
		for steam_script_path, ps3_script_path in matching_script_paths:
			update_match_statistics(match_statistics,
									reverse_match_statistics,
									steam_script_path,
									ps3_script_path,
									match_configuration=config)

	#Save results to csv and json file
	save_statistics(match_statistics, reverse_match_statistics, output_path)


doBackgroundMatching()

