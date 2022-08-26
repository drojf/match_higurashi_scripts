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
