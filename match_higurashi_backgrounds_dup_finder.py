import hashlib
import csv
import os

from PIL import Image
import imagehash
from collections import defaultdict


def sha_hash(image):
	image_as_bytes = image.tobytes()
	h = hashlib.sha256()
	h.update(image_as_bytes)
	return h.hexdigest()


def index_folder(scan_path, csv_path):
	"""
	Recursively indexes images, ignoring images with the same name, and ignoring file name case/extension
	The CSV file will be of the format [IMAGE_KEY, IMAGE_CONTENT_SHA, PERCEPTUAL_HASH, FULL_PATH]
	Where IMAGE_KEY is the filename stripped of its extension, and lowercase
	:param scan_path:
	:param csv_path:
	:return:
	"""
	mapping = {}
	total_visited = 0
	same_key = 0

	for root, dirs, file_names in os.walk(scan_path):
		for file_name in file_names:
			total_visited += 1
			file_name_key = file_name.lower().split('.', maxsplit=1)[0]
			if file_name_key in mapping:
				same_key += 1
				continue

			path = os.path.join(root, file_name)
			image = Image.open(os.path.join(path))
			sha = sha_hash(image)
			phash = imagehash.phash(image)
			mapping[file_name_key] = [sha, phash, path]
			print(f"Name: {file_name} Sha: {sha} phash: {phash}")

	print(f"Visited: {total_visited} Images with same name: {same_key}")

	with open(csv_path, 'w', newline='') as csvfile:
		writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
		for (image_name, properties) in mapping.items():
			writer.writerow([image_name] + properties)


def load_index(csv_path):
	index = []
	with open(csv_path, newline='') as csvfile:
		reader = csv.reader(csvfile, delimiter=',', quotechar='"')
		for row in reader:
			index.append(row)

	return index


def find_duplicates(grouped_dict: dict):
	duplicates = []
	for k,v in grouped_dict.items():
		if len(v) > 1:
			# print(f"Group: {v}")
			duplicates.append(v)
	return duplicates


def save_rows(rows, csv_path, header_row=None):
	with open(csv_path, 'w', newline='') as csvfile:
		writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
		if header_row:
			writer.writerow(header_row)
		for row in rows:
			writer.writerow(row)


def load_rows(csv_path):
	rows = []
	with open(csv_path, newline='') as csvfile:
		reader = csv.reader(csvfile, delimiter=',', quotechar='"')
		for row in reader:
			rows.append(row)
	return rows


def save_dupes(index, sha_dupes_path, phash_dupes_path):
	sha_groups = defaultdict(list)
	phash_groups = defaultdict(list)

	for name, sha, phash, path in index:
		sha_groups[sha].append(name)
		phash_groups[phash].append(name)

	sha_dupes = sorted(find_duplicates(sha_groups))
	phash_dupes = sorted(find_duplicates(phash_groups))

	print(f"Found {len(sha_dupes)} sha dupes and {len(phash_groups)} phash dups")

	save_rows(sha_dupes, sha_dupes_path)
	save_rows(phash_dupes, phash_dupes_path)


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

def merge_auto_matching_and_naegles(auto_matching_path, naegles_path, output_path):
	auto_rows = load_rows(auto_matching_path)[1:]  # Skip column description row
	naegles_rows = load_rows(naegles_path)

	# This does a database JOIN where the ps3 name is the common ID
	all_ps3_names = set()
	auto_as_dict = {}
	naegles_as_dict = {}
	last_file_found_mapping = {}

	for row in auto_rows:
		auto_first_file_found = row[0]
		auto_ps3_filename = row[1]
		auto_ryukishi_filename = row[2]
		all_ps3_names.add(auto_ps3_filename)
		auto_as_dict[auto_ps3_filename] = auto_ryukishi_filename
		last_file_found_mapping[auto_ps3_filename] = auto_first_file_found


	for row in naegles_rows:
		all_ps3_names.add(row[0])
		naegles_as_dict[row[0]] = row[1]

	merged_dict = {}

	for ps3_name in all_ps3_names:
		merged_dict[ps3_name] = [auto_as_dict.get(ps3_name, 'NO_MATCH'), naegles_as_dict.get(ps3_name, 'NO_MATCH')]

	output_rows = []
	for ps3_name, v in merged_dict.items():
		auto_result = v[0]
		naegles_result = v[1]
		auto_has_match = auto_result != 'NO_MATCH'
		naegles_has_match = naegles_result != 'NO_MATCH'

		status = 'UNDEFINED'
		if auto_has_match and naegles_has_match:
			# Check for disagreement
			if auto_result.strip() != naegles_result.strip():
				status = 'CONTRADICTORY'
			else:
				status = 'IDENTICAL'
		elif auto_has_match:
			status = 'AUTOMATIC'
		elif naegles_has_match:
			status = 'NAEGLES'
		else:
			# If neither matched
			status = 'NO_MATCH'

		if naegles_has_match:
			final_choice = naegles_result
		else:
			final_choice = auto_result

		output_rows.append([last_file_found_mapping.get(ps3_name, "unknown"), ps3_name, auto_result, naegles_result, final_choice, status])

	# Sort the rows, but ignore the first row which is the first file the ps3? was found
	output_rows = sorted(output_rows, key=lambda r: r[1:])

	save_rows(output_rows, output_path, header_row=["last_file_found", "ps3_name", "auto", "naegles", "final_choice", "status"])

def identify_cg(final_mapping_file_path, ps3_filename_to_path_mapping_file_path, output_path):
	filename_to_path_dict = dict(load_rows(ps3_filename_to_path_mapping_file_path))
	ps3_final_mapping_all_rows = load_rows(final_mapping_file_path)
	ps3_final_mapping_rows = ps3_final_mapping_all_rows[1:]

	out_rows = [ps3_final_mapping_all_rows[0] + ['ps3_path']]

	for row in ps3_final_mapping_rows:
		ps3_path = row[1]
		path = filename_to_path_dict.get(ps3_path)
		if path is None:
			print(ps3_path, path)
			raise Exception(f"No file path for {ps3_path} on row [{row}]")
		else:
			print(ps3_path, path)

		out_rows.append(row + [path])

	save_rows(out_rows, output_path)


if __name__ == '__main__':
	scan_folder = r'C:\temp\higu_backgrounds_imageComparer\external\ryukishi'
	csv_path = r'background_matching_intermediate\ryukishi_image_signatures.csv'
	sha_dupes_path = r'background_matching_intermediate\ryukishi_sha_dups_out.csv'
	phash_dupes_path = r'background_matching_intermediate\ryukishi_phash_dups_out.csv'
	auto_matching_path = 'background_matching_intermediate/auto_matching.csv'
	naegles_remapped_path = 'background_matching_intermediate/naegles_remapped.csv'
	merged_output_path = 'background_matching_intermediate/merged_mapping.csv'
	final_manual_mapping = 'background_matching/manual_background_mapping.csv'
	ps3_filename_to_path_mapping_file_path = 'imageComparer/ps3_mapping.csv'
	manual_background_mapping_with_paths_path = 'background_matching/manual_bg_map_paths_generated.csv'

	do_indexing = False

	# if do_indexing:
	# 	index_folder(scan_folder, csv_path)
	#
	# index = load_index(csv_path)
	# save_dupes(index, sha_dupes_path, phash_dupes_path)

	# remap_naegles()

	merge_auto_matching_and_naegles(auto_matching_path, naegles_remapped_path, merged_output_path)
