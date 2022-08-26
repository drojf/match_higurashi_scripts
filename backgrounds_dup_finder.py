import csv
import os
import imagehash
from tkinter import Image
from utility import save_rows, load_rows
from collections import defaultdict
from PIL import Image

def sha_hash(image):
	image_as_bytes = image.tobytes()
	h = hashlib.sha256()
	h.update(image_as_bytes)
	return h.hexdigest()


def load_index(csv_path):
	index = []
	with open(csv_path, newline='') as csvfile:
		reader = csv.reader(csvfile, delimiter=',', quotechar='"')
		for row in reader:
			index.append(row)

	return index


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


def find_duplicates(grouped_dict: dict):
	duplicates = []
	for k,v in grouped_dict.items():
		if len(v) > 1:
			# print(f"Group: {v}")
			duplicates.append(v)
	return duplicates


# NOTE: this function is currently not called anywhere.
# Scan for duplicate images
def scan_dupes(phash_dupes_path, ryukishi_filename_to_path_mapping_file_path):
	dup_dict = {}

	with open(phash_dupes_path, newline='') as csvfile:
		reader = csv.reader(csvfile, delimiter=',', quotechar='"')
		for row in reader:
			dup_dict[row[0]] = row[1]

	ryukishi_image_names = set()

	with open(ryukishi_filename_to_path_mapping_file_path, newline='') as csvfile:
		reader = csv.reader(csvfile, delimiter=',', quotechar='"')
		for row in reader:
			ryukishi_image_names.add(row[0])

	with open(final_manual_mapping, newline='') as csvfile:
		reader = csv.reader(csvfile, delimiter=',', quotechar='"')
		reader.__next__()
		for row in reader:
			if row[1] in ryukishi_image_names:
				if row[4] == row[1]:
					continue

				if row[4] in dup_dict:
					if dup_dict[row[4]] == row[1]:
						continue

				print(row[1])


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


if __name__ == '__main__':
	scan_folder = r'C:\temp\higu_backgrounds_imageComparer\external\ryukishi'
	csv_path = r'background_matching_intermediate\ryukishi_image_signatures.csv'
	sha_dupes_path = r'background_matching_intermediate\ryukishi_sha_dups_out.csv'
	phash_dupes_path = r'background_matching_intermediate\ryukishi_phash_dups.csv'

	do_indexing = False

	if do_indexing:
		index_folder(scan_folder, csv_path)
	
	index = load_index(csv_path)
	save_dupes(index, sha_dupes_path, phash_dupes_path)