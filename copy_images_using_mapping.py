import csv
import itertools
import os
import shutil
from PIL import Image, ImagePalette, ImageOps
from pathlib import Path

import match_higurashi_backgrounds_dup_finder

# This function is taken from https://stackoverflow.com/questions/43864101/python-pil-check-if-image-is-transparent
def has_transparency(img):
	if img.mode == "P":
		transparent = img.info.get("transparency", -1)
		for _, index in img.getcolors():
			if index == transparent:
				return True
	elif img.mode == "RGBA":
		extrema = img.getextrema()
		if extrema[3][0] < 255:
			return True

	return False


def resize_image(ps3_image, ryukishi_image, SMALL_IMAGE_MODE, FOUR_THREE_ASPECT):
	if not SMALL_IMAGE_MODE:
		return ryukishi_image.resize(ps3_image.size)

	# Assume special image size if ps3 size is not one of the standard resolutions, so forcibly resize to exactly
	# the PS3 image size
	if ps3_image.size not in [(2560, 1440), (1920, 1080), (1280, 720)]:
		return ryukishi_image.resize(ps3_image.size)

	if FOUR_THREE_ASPECT:
		# If in 4:3 aspect ratio don't resize the original as it's already 4:3
		if ryukishi_image.size[0] != int(ryukishi_image.size[1] * 4 / 3):
			raise Exception(f"Ryukishi image is of the wrong aspect! {ryukishi_image.size}")
		return ryukishi_image
	else:
		# If in 16:9 aspect ratio mode, resize to 16:9 resoltuion
		return ryukishi_image.resize((round(ryukishi_image.size[1] * 16 / 9), ryukishi_image.size[1]))


def process_image(src_ps3_path: str, src_ryukishi_path: str, dst_path: str, SMALL_IMAGE_MODE: bool, FOUR_THREE_ASPECT: bool):
	containing_path = str(Path(src_ps3_path).parent)
	containing_path_lower = containing_path.lower()

	ps3_image = Image.open(src_ps3_path)

	ryukishi_image = Image.open(src_ryukishi_path)
	output_image_mode = 'RGB'
	if has_transparency(ryukishi_image):
		output_image_mode = 'RGBA'

	# Convert paletted images to RGB first
	if ryukishi_image.mode in ['P', '1']:
		print(f"WARNING: converting paletted or binary image [{src_ryukishi_path}] to RGB/RGBA")
		ryukishi_image = ryukishi_image.convert(output_image_mode)

	# Check for strange image modes
	if ryukishi_image.mode not in ['RGB', 'RGBA', 'L']:
		raise Exception(f"Unhandled image mode: [{ryukishi_image.mode}]")

	out_noeffect = resize_image(ps3_image, ryukishi_image, SMALL_IMAGE_MODE, FOUR_THREE_ASPECT)

	if 'flashback' in containing_path_lower:
		# TODO: handle transparency when applying flashback effect! Currently converting to greyscale ('L') loses alpha
		out = out_noeffect.convert('L')
		out.putpalette(ImagePalette.sepia())
		out = out.convert(output_image_mode)
		# Adjust the strength of the sepia effect by blending with the original image
		# 0 = no sepia, 1 = full sepia
		out = Image.blend(out_noeffect, out, .7)
	elif 'greyscale' in containing_path_lower:
		# TODO: handle transparency when applying greyscale effect! Currently converting to greyscale ('L') loses alpha
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


def main(small_image_mode, four_three_aspect):
	# Regenerate the `background_matching/manual_bg_map_paths_generated.csv` file
	match_higurashi_backgrounds_dup_finder.identify_cg_easy()

	# This script expects the folder imageComparer/external/ps3/ep1 to contain the PS3 CG folder for episode 1
	# and imageComparer/external/ryukishi/ep1 to contain the original ryukishi CG folder for episode 1
	# and so on for each episode.
	root_folder = 'imageComparer'
	ps3_folder = 'imageComparer/external/ps3'
	ryukishi_folder = 'imageComparer/external/ryukishi'
	output_folder = 'higu_backgrounds_output'
	csv_path = 'background_matching/manual_bg_map_paths_generated.csv'

	if os.path.exists(output_folder):
		raise Exception(f"Output folder [{output_folder}] already exists - please delete it!")

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
		ps3_filename = row[1]  # PS3 filename without extension
		ryukishi_path = row[7]
		match_type = row[5]
		if match_type == 'EFFECT':
			print(f"WARNING: Discarding mapping for effect image [{ps3_filename}] [{ryukishi_path}]")
		elif ps3_filename == 'NO_MATCH' or ryukishi_path == 'NO_MATCH':
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
			process_image(str(full_path), src_path, dst_path, small_image_mode, four_three_aspect)

	# Special handling for the "background.png" file in the "scenario" folder - just copy the
	# 'CG/scenario_a.png' image from the ryukishi folder
	print("Scenario folder handling")
	for i in range(1, 9):
		# This is no longer carried out - game will automatically prefer the images in the CG folder if they don't exist
		# First, copy the entire scenario folder
		# shutil.copytree(src=os.path.join(ps3_folder, f'ep{i}/scenario'),
		# 				dst=os.path.join(output_folder, ps3_folder, f'ep{i}/scenario'),
		# 				dirs_exist_ok=True)

		# Copy just the ryukishi `scenario_a.png` file
		full_path = os.path.join(ps3_folder, f'ep{i}/scenario/background.png')
		src_path = os.path.join(ryukishi_folder, f'ep{i}/scenario_a.png')
		dst_path = os.path.join(output_folder, full_path)

		print(f"Copying {src_path} -> {dst_path}")

		os.makedirs(os.path.dirname(dst_path), exist_ok=True)
		process_image(str(full_path), src_path, dst_path, small_image_mode, four_three_aspect)

	# Copy pre-processed images
	print(f"Copying 'preprocessed' folder -> {output_folder}")
	preprocessed_folder = 'preprocessed'
	if small_image_mode:
		preprocessed_folder = 'preprocessed_small'
	shutil.copytree(preprocessed_folder, output_folder,  dirs_exist_ok=True)

	for i in range(1, 9):
		src_path = os.path.join(output_folder, ps3_folder, f'ep{i}')

		# Copy pre-processed images common to all projects
		shutil.copytree('preprocessed_common', src_path, dirs_exist_ok=True)

		# move files from path `higu_backgrounds_output/imageComparer/external/ps3/epX` to
		# `higu_backgrounds_output/epX/HigurashiEp0X_Data/StreamingAssets`
		dest_containing_folder = os.path.join(output_folder, f'ep{i}/HigurashiEp0{i}_Data/StreamingAssets')
		dest_path = os.path.join(dest_containing_folder, 'OGBackgrounds')
		os.makedirs(dest_containing_folder, exist_ok=True)
		os.rename(src_path, dest_path)

if __name__ == '__main__':
	main(small_image_mode=True, four_three_aspect=True)
