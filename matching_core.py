import os
import pathlib
import re
from typing import Callable, Set, List, Tuple, Iterator, Optional

from match_statistics import MatchStatistics

class CustomMatcher:
	def __init__(self, regexForMatching : re.Pattern, matchIndex : int):
		self.regex = regexForMatching
		self.matchIndex = matchIndex

	def try_get_value(self, input_line : str):
		match = self.regex.search(input_line)
		if match:
			# all_matches = match.groups()
			# print(match.group(self.matchIndex))
			return match.group(self.matchIndex)
		return None

class MatchConfiguration:
	def __init__(self,
				 steamMatcher: CustomMatcher,
				 ps3Matcher: CustomMatcher,
				 ps3_name_modification_function=lambda x:x, #default to a passthrough function
				 ps3_whitelist_function=lambda x: True,
				 enable_matcher_background_filter=False): #default to function which allows all names
		self.ps3_name_modification_function = ps3_name_modification_function #type: Callable[[str], str]
		self.ps3_whitelist_function = ps3_whitelist_function #type: Callable[[str], bool]
		self.enable_matcher_background_filter = enable_matcher_background_filter  #type: Callable[[str], bool]
		self.steamMatcher = steamMatcher #type: CustomMatcher
		self.ps3Matcher = ps3Matcher #type: CustomMatcher



def get_ps3_sprite_names_from_file(ps3_script_path: str,
									config: MatchConfiguration) -> Set[str]:
	"""
	This function extracts all the ps3 sprite names from a Higurashi script (assuming it has been modded with the ps3
	sprites)

	:param ps3_script_path: a path to a Higurashi script file, modded with the ps3 sprites
	:param name_modification_function: a function taking a ps3 sprite name as argument and returning a modified ps3 sprite name.
	Each ps3 sprite name will be modified by this function before being returned

	:return: a set containing the found ps3 sprite names
	"""
	all_sprite_names = set()
	with open(ps3_script_path, encoding='utf-8') as ps3_script_file:
		for line in ps3_script_file.readlines():
			sprite_name = config.ps3Matcher.try_get_value(line)
			if sprite_name and config.ps3_whitelist_function(sprite_name):
				modified_name = config.ps3_name_modification_function(sprite_name)
				all_sprite_names.add(modified_name)

	return all_sprite_names


def get_comment_chunk_pairs_from_text(text: str) -> Iterator[Tuple[str, str]]:
	"""
	Take every odd/even result from the split_text array.
	There will always be one more child text than comment line,
	so skip the first child text (start at index 2 instead of 0)

	:param text: The text which will be split on comment lines
	:return: The text split into a list of tuples. Each tuple is of the form (comment, textBetweenComment).
	"""
	split_text = re.split(r'(//.*$)', text, flags=re.MULTILINE)

	child_text = split_text[2::2]
	comment_lines = split_text[1::2]

	return zip(comment_lines, child_text)

#englishTextMarkerRegex = re.compile(r'\s*NULL\s*,\s*([^,]+)', re.IGNORECASE)
outputLineFunctionCaptureRegex = re.compile(r'OutputLine\([^,]+,\s*"([^"]+)[^)]+\)', re.IGNORECASE)

def get_comment_chunk_pairs_from_text_alt(text: str) -> Iterator[Tuple[str, str]]:
	"""
	Take every odd/even result from the split_text array.
	There will always be one more child text than comment line,
	so skip the first child text (start at index 2 instead of 0)

	:param text: The text which will be split on comment lines
	:return: The text split into a list of tuples. Each tuple is of the form (comment, textBetweenComment).
	"""
	split_text = outputLineFunctionCaptureRegex.split(text)

	child_text = split_text[2::2]
	comment_lines = split_text[1::2]

	return zip(comment_lines, child_text)

def get_matching_chunks_from_file(steam_script_path: str, ps3_script_path: str) -> List[Tuple[str, str]]:
	"""
	Tries to match chunks from steam script to ps3 script. The matching assumes the commented lines are
	identical between the two scripts, and matches the chunks just after each identical commented line together.
	Any unmatched chunks are ignored.

	:param steam_script_path: path to a unmodified higurashi script
	:param ps3_script_path: path to a higurashi script modified with the ps3 sprites
	:return: A list of tuples of the form (original_chunk, ps3_chunk), representing matched chunks
	"""
	original_text = pathlib.Path(steam_script_path).read_text(encoding='utf-8')
	ps3_script_text = pathlib.Path(ps3_script_path).read_text(encoding='utf-8')

	# get chunks from text
	original_pairs = list(get_comment_chunk_pairs_from_text(original_text))
	ps3_pairs = list(get_comment_chunk_pairs_from_text(ps3_script_text))

	# If there are not enough matches, use alternate method using OutputLine(...) instead of comments
	if len(original_pairs) < 10 or len(ps3_pairs) < 10:
		original_pairs = list(get_comment_chunk_pairs_from_text_alt(original_text))
		ps3_pairs = list(get_comment_chunk_pairs_from_text_alt(ps3_script_text))

	original_chunk_dictionary = dict(original_pairs)

	# look up each new ps3 comment in the original dictionary
	ps3_chunk_to_steam_chunk = []

	for ps3_comment, ps3_chunk in ps3_pairs:
		original_chunk = original_chunk_dictionary.get(ps3_comment, None)
		if original_chunk:
			ps3_chunk_to_steam_chunk.append((original_chunk, ps3_chunk))

	return ps3_chunk_to_steam_chunk


def try_get_steam_to_ps3_matching_from_chunks(steam_chunk: str,
											  ps3_chunk: str,
											  match_configuration: MatchConfiguration):
	"""
	Given two matched chunks, matches the first found steam sprite name with the first found ps3 sprite name.
	If either the steam or ps3 sprite name is missing, it is not matched
	If there is more than one sprite per chunk, they are ignored - only the first one is used.

	:param steam_chunk: A chunk of the unmodified higurashi script
	:param ps3_chunk: A chunk of the higurashi script modified with ps3 sprites. Must be the matching chunk to the
	'steam_chunk' argument.
	:return:
	"""
	# print(steam_chunk)
	# steam_matcher = match_configuration.steamRegex
	# ps3_matcher = match_configuration.ps3Regex

	def get_matches(chunk, matcher : CustomMatcher):
		matches = []
		for line in chunk.splitlines():
			match = matcher.try_get_value(line)

			if match_configuration.enable_matcher_background_filter:
				if match == 'black' or match == 'white':
					continue

			if match is not None:
				matches.append(match)
		return matches

	steam_matches = get_matches(steam_chunk, match_configuration.steamMatcher)
	ps3_matches = get_matches(ps3_chunk, match_configuration.ps3Matcher)

	# TODO: for now, only accept if the number of ps3 and steam matches are equal
	if len(steam_matches) == len(ps3_matches):
		return [x for x in zip(steam_matches, ps3_matches)]
	else:
		return []

def update_match_statistics(match_statistics: MatchStatistics,
							reverse_match_statistics: MatchStatistics,
							steam_script_path: str,
							ps3_script_path: str,
							match_configuration: MatchConfiguration):
	"""
	Given the paths to a folder contain the unmodified steam scripts and a path to the ps3-modded scripts, updates the
	two input match statistics objects with any found sprite mappings.

	TODO: python has built in "defaultdict" and "counter" which I've used before. It can simplify the logic for this function.
	'match_statistics' is a dict of dicts. It records how many of each type of match has been seen previously.
	The key of the outer dict is the ps3 filename. The value of the outer dict is another dict, described below
	The key of the inner dict is the steam filename. The value of the inner dict is the count of number of matches for that steam filename.
	Example:

	{
	 'sprite/normal/me1a_def_a1_': {'me_se_de_a1': 5, 'me_se_wi_a2': 1},
	 'sprite/normal/me1a_huteki_a1_': {'re_se_de_a1': 1},
	 'sprite/normal/me1a_tohoho_a1_': {'me_se_th_a1': 1},
	 'sprite/normal/me1a_warai_a1_': {'me_se_wa_a1': 4},
	 'sprite/normal/me1a_wink_a1_': {'me_se_wi_a1': 6, 'me_se_wi_a2': 1},
	 'sprite/normal/me1b_akuwarai_a1_': {'me_se_aw_b1': 1, 'me_se_aw_b2': 1},
	 }

	match statistics is provided as an argument so that a single object reused as each new file has it's matches collected

	:param match_statistics: match statistics object to be updated with any matches found
	:param reverse_match_statistics: reverse match statistics object to be updated with any matches found
	:param steam_script_path: path to a unmodified higurashi script
	:param ps3_script_path: path to a higurashi script modified with the ps3 sprites
	:param ps3_name_modification_function: all ps3 paths will be modified by this function before being used
	:param ps3_whitelist_function: all ps3 paths will only be used if this function returns true when the path is used as argument
	:return: No return value, arguments match_statistics and reverse_match_statistics are updated
	"""
	original_to_steam_chunk_list = get_matching_chunks_from_file(steam_script_path, ps3_script_path)

	for (original_chunk, ps3_chunk) in original_to_steam_chunk_list:
		mappings = try_get_steam_to_ps3_matching_from_chunks(original_chunk, ps3_chunk, match_configuration)
		for mapping in mappings:
			steam_name, ps3_name = mapping
			#the image 'black' is not a sprite, so shouldn't be used for matching
			if steam_name == 'black' or ps3_name == 'black':
				continue

			# If the filtered ps3 filename is not in the white list, don't try to match it
			if not match_configuration.ps3_whitelist_function(ps3_name):
				continue

			ps3_name = match_configuration.ps3_name_modification_function(ps3_name)

			#do the forward mapping
			match_count = match_statistics.statistics.setdefault(ps3_name, {})
			match_count.setdefault(steam_name, 0)
			match_count[steam_name] += 1
			#do the backward mapping
			match_count = reverse_match_statistics.statistics.setdefault(steam_name, {})
			match_count.setdefault(ps3_name, 0)
			match_count[ps3_name] += 1

	###### Code below this point is just for checking if any ps3 sprites were missed
	# get the complete list of ps3 sprite names from the ps3 script file
	# this is done as a separate function to reduce the chance that an error is made and a sprite is missed
	all_ps3_sprite_names = get_ps3_sprite_names_from_file(ps3_script_path, match_configuration)

	# If any ps3 sprite names are missing from the matching, these sprites were 'never matched'. Set them to match with 'None'
	for ps3_sprite_name in all_ps3_sprite_names:
		ps3_sprite_name = match_configuration.ps3_name_modification_function(ps3_sprite_name)

		match_statistics.sprite_to_file_mapping[ps3_sprite_name] = os.path.basename(ps3_script_path)
		if ps3_sprite_name not in match_statistics.statistics:
			print("The following sprite was unmatched:" + ps3_sprite_name)
			match_statistics.statistics[ps3_sprite_name] = {}
	###### End missed ps3 sprites checking

	return match_statistics


def get_matching_script_paths_between_folders(steam_folder_path, ps3_folder_path):
	"""
	Gets a list of files with the same name between two folders
	Note that if a file exists in the 'ps3_folder_path' but not in the 'steam_folder_path', it won't be detected
	TODO: should re-implement this by listdir()ing both directories, and then comparing the results

	:param steam_folder_path: path to folder containing steam scripts (will only search root folder)
	:param ps3_folder_path:   path to folder containing ps3   scripts (will only search root folder)
	"""

	matching_paths = []

	if not os.path.exists(steam_folder_path):
		raise  Exception(f"Steam folder [{steam_folder_path}] does not exist - can't get matching scripts")

	if not os.path.exists(ps3_folder_path):
		raise Exception(f"PS3 folder [{ps3_folder_path}] does not exist - can't get matching scripts")

	print(f"Testing that files in [{steam_folder_path}] also exist in [{ps3_folder_path}]:")
	for steam_filename in os.listdir(steam_folder_path):
		_, ext = os.path.splitext(steam_filename)
		if ext == '.txt':
			ps3_expected_path = os.path.join(ps3_folder_path, steam_filename)
			if os.path.exists(ps3_expected_path):
				print("Found matchable files for", steam_filename)
				matching_paths.append((os.path.join(steam_folder_path, steam_filename), ps3_expected_path))
			else:
				print(f"Couldn't find matching file for [{steam_filename}] in [{ps3_folder_path}]")
		else:
			print(f"Skipping non .txt file [{steam_filename}]")

	return matching_paths
