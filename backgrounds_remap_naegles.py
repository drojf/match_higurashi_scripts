from utility import load_rows, save_rows


class QuestionArcsBackgroundRemapper:
	def __init__(self, ryukishi_sha_dups_csv):
		rows = load_rows(ryukishi_sha_dups_csv)
		index = {}

		for row in rows:
			if not row[0].startswith('bg_'):
				continue

			if len(row) != 2:
				raise Exception(f"ERROR: A bg_ row didn't have 2 columns: [{row}]")

			index[row[0]] = row[1]

		self.index = index

	def get_mapping(self, question_arcs_bg_name):
		return self.index.get(question_arcs_bg_name)


def remap_naegles():
	"""Remap naegle's question-arc style names"""
	naegles_matches = load_rows(r'background_matching_intermediate\naegles_pre_processed.csv')[1:]  #skip first header row
	remapper = QuestionArcsBackgroundRemapper(r'background_matching_intermediate\ryukishi_sha_dups.csv')

	remapped_rows = []
	for row in naegles_matches:
		ps3_name = row[0]
		qa_name = row[1]
		remapped_qa_name = remapper.get_mapping(qa_name.lower())

		if remapped_qa_name is not None:
			qa_name = remapped_qa_name

		remapped_rows.append([ps3_name, qa_name])

	remapped_rows = sorted(remapped_rows)

	save_rows(remapped_rows, r'background_matching_intermediate\naegles_remapped.csv')