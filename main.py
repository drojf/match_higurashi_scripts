import pathlib, re

class Chunk:
	def __init__(self, comment_line, child_lines):
		self.comment_line = comment_line
		self.child_lines = child_lines

def get_chunks_from_text(text):
	split_text = re.split(r'(//.*$)', text, flags=re.MULTILINE)

	# take every odd/even result from the split_text array
	# there will always be one more child text than comment line,
	# so skip the first child text (start at index 2 instead of 0)
	child_text = split_text[2::2]
	comment_lines = split_text[1::2]

	combined = zip(comment_lines, child_text)

	return [Chunk(a, b) for a, b in combined]


original_script_path = "onik_001.txt"
new_script_path = "onik_001_new.txt"

original_text = pathlib.Path(original_script_path).read_text(encoding='utf-8')
new_script_text = pathlib.Path(new_script_path).read_text(encoding='utf-8')

# get chunks from text
original_chunks = get_chunks_from_text(original_text)
new_chunks = get_chunks_from_text(new_script_text)

# put chunks in a dictionary
original_chunk_dict = {}
