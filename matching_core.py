import os
import pathlib
import re

from match_statistics import MatchStatistics

steamBustRegex = re.compile(r'DrawBust[^\(]+\(\s*\d*\s*,\s*\"([^\"]+)')
ps3BustRegex = re.compile(r'ModDraw[^\(]+\(\s*\d*\s*,\s*\d*\s*,\s*\"([^\"]+)')


def get_ps3_sprite_names_from_file(ps3_script_path, ps3FilterFunction) -> set:
	all_sprite_names = set()
	with open(ps3_script_path, encoding='utf-8') as ps3_script_file:
		for line in ps3_script_file.readlines():
			match = ps3BustRegex.search(line)
			if match:
				all_sprite_names.add(ps3FilterFunction(match.group(1)))

	return all_sprite_names

def get_comment_chunk_pairs_from_text(text):
	split_text = re.split(r'(//.*$)', text, flags=re.MULTILINE)

	# take every odd/even result from the split_text array
	# there will always be one more child text than comment line,
	# so skip the first child text (start at index 2 instead of 0)
	child_text = split_text[2::2]
	comment_lines = split_text[1::2]

	return zip(comment_lines, child_text)


# tries to match chunks from steam script to ps3 script.
# any unmatched chunks are ignored
def get_matching_chunks_from_file(steam_script_path, ps3_script_path):
	original_text = pathlib.Path(steam_script_path).read_text(encoding='utf-8')
	ps3_script_text = pathlib.Path(ps3_script_path).read_text(encoding='utf-8')

	# get chunks from text
	original_pairs = get_comment_chunk_pairs_from_text(original_text)
	ps3_pairs = get_comment_chunk_pairs_from_text(ps3_script_text)

	original_chunk_dictionary = {k: v for (k, v) in original_pairs}

	# look up each new ps3 comment in the original dictionary
	ps3_chunk_to_steam_chunk = []

	for ps3_comment, ps3_chunk in ps3_pairs:
		original_chunk = original_chunk_dictionary.get(ps3_comment, False)
		if original_chunk:
			ps3_chunk_to_steam_chunk.append((original_chunk, ps3_chunk))

	return ps3_chunk_to_steam_chunk


def try_get_steam_to_ps3_matching_from_chunks(steam_chunk : str, ps3_chunk : str):
	# print(steam_chunk)
	steam_match = steamBustRegex.search(steam_chunk)
	if not steam_match:
		return None

	ps3_match = ps3BustRegex.search(ps3_chunk)
	if not ps3_match:
		return None

	if steam_match.group(1) and ps3_match.group(1):
		return (steam_match.group(1), ps3_match.group(1))
	else:
		return None

def update_match_statistics(match_statistics : MatchStatistics, reverse_match_statistics, steam_script_path, ps3_script_path, ps3_filter_function=None, ps3_whitelist_function=None):
	original_to_steam_chunk_list = get_matching_chunks_from_file(steam_script_path, ps3_script_path)

	if not ps3_filter_function:
		ps3_filter_function = lambda x: x
	# 'match_statistics' is a dict of dicts. It records how many of each type of match has been seen previously.
	# The key of the outer dict is the ps3 filename. The value of the outer dict is another dict, described below
	# The key of the inner dict is the steam filename. The value of the inner dict is the count of number of matches for that steam filename.
	# Example:
	#
	# {
	#  'sprite/normal/me1a_def_a1_': {'me_se_de_a1': 5, 'me_se_wi_a2': 1},
	#  'sprite/normal/me1a_huteki_a1_': {'re_se_de_a1': 1},
	#  'sprite/normal/me1a_tohoho_a1_': {'me_se_th_a1': 1},
	#  'sprite/normal/me1a_warai_a1_': {'me_se_wa_a1': 4},
	#  'sprite/normal/me1a_wink_a1_': {'me_se_wi_a1': 6, 'me_se_wi_a2': 1},
	#  'sprite/normal/me1b_akuwarai_a1_': {'me_se_aw_b1': 1, 'me_se_aw_b2': 1},
	#  }
	#
	# match statistics is provided as an argument so that a single object reused as each new file has it's matches collected

	for (original_chunk, ps3_chunk) in original_to_steam_chunk_list:
		mapping = try_get_steam_to_ps3_matching_from_chunks(original_chunk, ps3_chunk)
		if mapping:
			steam_name, ps3_name = mapping
			#the image 'black' is not a sprite, so shouldn't be used for matching
			if steam_name == 'black' or ps3_name == 'black':
				continue
			ps3_name = ps3_filter_function(ps3_name)

			# If the filtered ps3 filename is not in the white list, don't try to match it
			if ps3_whitelist_function:
				if not ps3_whitelist_function(ps3_name):
					continue

			#do the forward mapping
			match_count = match_statistics.statistics.setdefault(ps3_name, {})
			match_count.setdefault(steam_name, 0)
			match_count[steam_name] += 1
			#do the backward mapping
			match_count = reverse_match_statistics.setdefault(steam_name, {})
			match_count.setdefault(ps3_name, 0)
			match_count[ps3_name] += 1

	# get the complete list of ps3 sprite names from the ps3 script file
	# this is done as a separate function to reduce the chance that an error is made and a sprite is missed
	all_ps3_sprite_names = get_ps3_sprite_names_from_file(ps3_script_path, ps3_filter_function)

	# If any ps3 sprite names are missing from the matching, these sprites were 'never matched'. Set them to match with 'None'
	for ps3_sprite_name in all_ps3_sprite_names:
		match_statistics.sprite_to_file_mapping[ps3_sprite_name] = os.path.basename(ps3_script_path)
		if ps3_sprite_name not in match_statistics.statistics:
			print("The following sprite was unmatched:" + ps3_sprite_name)
			match_statistics.statistics[ps3_sprite_name] = {}

	return match_statistics


def get_matching_script_paths_between_folders(steam_folder_path, ps3_folder_path):
	"""

	:param steam_folder_path: path to folder containing steam scripts (will only search root folder)
	:param ps3_folder_path:   path to folder containing ps3   scripts (will only search root folder)
	"""

	matching_paths = []

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
