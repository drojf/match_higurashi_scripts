import csv
import itertools
import os
import shutil
from PIL import Image, ImagePalette, ImageOps
from pathlib import Path


def process_image(src_ps3_path: str, src_ryukishi_path: str, dst_path: str):
	containing_path = str(Path(src_ps3_path).parent)
	containing_path_lower = containing_path.lower()
	#containing_folder = os.path.basename()
	#image_type = containing_folder.lower()

	ps3_image = Image.open(src_ps3_path)
	# print(containing_path, ps3_image.format, ps3_image.size, ps3_image.mode)

	ryukishi_image = Image.open(src_ryukishi_path)
	out_noeffect = ryukishi_image.resize(ps3_image.size)

	if 'flashback' in containing_path_lower:
		out = out_noeffect.convert('L')
		out.putpalette(ImagePalette.sepia())
		out = out.convert('RGB')
		# Adjust the strength of the sepia effect by blending with the original image
		# 0 = no sepia, 1 = full sepia
		out = Image.blend(out_noeffect, out, .7)
	elif 'greyscale' in containing_path_lower:
		out = out_noeffect.convert('L')
	elif 'negative' in containing_path_lower:
		out = ImageOps.invert(out_noeffect)
	elif 'blur' in containing_path_lower:
		# This folder uses a zoom motion blur effect which I'm not sure how to implement uisng PIL
		# This folder will have to be done manually
		print(f"WARNING: file {dst_path} should have zoom motion blur applied manually")
		out = out_noeffect
	else:
		out = out_noeffect

	out.save(dst_path)


def main():
	# process_image('C:\\temp\\flashback\\kawa4.png',
	#               'C:\\temp\\flashback\\kawa4_ryu.png',
	#               'C:\\temp\\flashback\\kawa4fixed.png')
	#
	# exit(-1)

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
			Path(ps3_folder).rglob('ep?/*.*'), # Files in the root of the CG folder
			Path(ps3_folder).rglob('ep?/background/**/*.*'), # Files in the CG/background folder, recursively
			Path(ps3_folder).rglob('ep?/flashback/**/*.*'),  # Files in the CG/flashback folder, recursively
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
			process_image(str(full_path), src_path, dst_path)

			# TODO: handle special images (greyscale, sepia etc.)
			#####shutil.copy(src_path, dst_path)

	# # Special handling for the "background.png" file in the "scenario" folder - just copy the
	# # 'CG/scenario_a.png' image from the ryukishi folder
	# for i in range(1,9):
	# 	full_path =
	# 	process_image(str(full_path), src_path, dst_path)




if __name__ == '__main__':
	main()
