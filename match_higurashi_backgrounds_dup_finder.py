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


def save_rows(rows, csv_path):
	with open(csv_path, 'w', newline='') as csvfile:
		writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
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
	naegles_matches = load_rows('naegles_mapping.csv')
	remapper = QuestionArcsBackgroundRemapper('ryukishi_sha_dups.csv')

	remapped_rows = []
	for row in naegles_matches:
		ps3_name = row[0]
		qa_name = row[1]
		remapped_qa_name = remapper.get_mapping(qa_name.lower())

		if remapped_qa_name is not None:
			qa_name = remapped_qa_name

		remapped_rows.append([ps3_name, qa_name])

	save_rows(remapped_rows, 'naegles_remapped.csv')

scan_folder = r'C:\temp\higu_backgrounds_imageComparer\external\ryukishi'
csv_path = 'ryukishi_image_signatures.csv'
sha_dupes_path = 'ryukishi_sha_dups_out.csv'
phash_dupes_path = 'ryukishi_phash_dups_out.csv'
do_indexing = False

if do_indexing:
	index_folder(scan_folder, csv_path)

index = load_index(csv_path)
save_dupes(index, sha_dupes_path, phash_dupes_path)

#remap_naegles()
