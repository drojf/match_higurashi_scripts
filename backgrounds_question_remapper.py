
from utility import load_rows


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

