import pathlib
import re


def get_comment_chunk_pairs_from_text(text):
	split_text = re.split(r'(//.*$)', text, flags=re.MULTILINE)

	# take every odd/even result from the split_text array
	# there will always be one more child text than comment line,
	# so skip the first child text (start at index 2 instead of 0)
	child_text = split_text[2::2]
	comment_lines = split_text[1::2]

	return zip(comment_lines, child_text)


original_script_path = "onik_001.txt"
ps3_script_path = "onik_001_new.txt"

original_text = pathlib.Path(original_script_path).read_text(encoding='utf-8')
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

for (original_chunk, ps3_chunk) in ps3_chunk_to_steam_chunk:
	print("got match:")
	print(original_chunk)
	print("matches with:")
	print(ps3_chunk)
