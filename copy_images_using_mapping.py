import csv
import itertools
import os
import shutil
from pathlib import Path


def main():
	root_folder = 'imageComparer'
	ps3_folder = 'imageComparer/external/ps3'
	output_folder = 'higu_backgrounds_output'
	csv_path = 'background_matching/manual_bg_map_paths_generated.csv'

	# Load all the rows
	with open(csv_path, newline='') as csvfile:
		reader = csv.reader(csvfile, delimiter=',', quotechar='"')
		header_row = reader.__next__()
		print(f"Header: {header_row}\n")
		all_rows = [row for row in reader]

	# Create mapping of ps3 filename -> ryukishi path
	# Ignore rows with "NO_MATCH"
	print("> Generating Mapping")
	mapping = {}
	for row in all_rows:
		# ps3_path = row[6]
		ps3_filename = row[1]  # PS3 filename without extension
		ryukishi_path = row[7]
		if ps3_filename == 'NO_MATCH' or ryukishi_path == 'NO_MATCH':
			print(f"WARNING: not adding file with no match to mapping: [{ps3_filename}] [{ryukishi_path}]")
		else:
			mapping[ps3_filename.lower()] = ryukishi_path

	# Use *.* instead of * to match only files
	# Use ? to match a single character for ep1, ep2, ep3 etc.
	for full_path in itertools.chain(
			Path(ps3_folder).rglob('ep?/background/*.*'),
			Path(ps3_folder).rglob('ep?/flashback/*.*')
	):
		basename = os.path.basename(full_path)
		name_no_ext, ext = os.path.splitext(basename)
		ryukishi_path = mapping.get(name_no_ext.lower(), None)
		if ryukishi_path is None:
			print(f"WARNING: mapping[{name_no_ext}] not found for {full_path}")
		else:
			src_path = os.path.join(root_folder, ryukishi_path)
			dst_path = os.path.join(output_folder, full_path)
			print(f"Copying {src_path} -> {dst_path}")
			if os.path.exists(dst_path):
				raise Exception(f"Error: output file already exists {dst_path}")

			os.makedirs(os.path.dirname(dst_path), exist_ok=True)
			# TODO: handle special images (greyscale, sepia etc.)
			shutil.copy(src_path, dst_path)


if __name__ == '__main__':
	main()
