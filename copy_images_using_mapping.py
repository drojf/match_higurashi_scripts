import csv
import itertools
import os
import shutil
import sys
from PIL import Image, ImagePalette, ImageOps
from pathlib import Path

import backgrounds_legacy_identify_cg
import validate_matching
from imageComparer.compareImages import buildFilenameFilepathMap, normalizeFilenameAndRemoveExtension
from utility import LAST_EPISODE

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
	"""
	This function resizes a ryukishi image ONLY if it thinks it is necessary to work properly in the game
	otherwise it will leave it alone (assuming you set SMALL_IMAGE_MODE to True and FOUR_THREE_ASPECT to True)

	NOTE: "Normal" Images vs "Special" images
	 - "Normal" images are when the PS3 image is of standard resolutions (1440p, 1080p, 720p)
	   - The corresponding ryukishi images are handled using the settings below
	 - "Special images" are ones which are not the above resolutions
	   - These images are usually for special situations (like events, or special effects), and therefore
	     may need to be a specific resolution to work properly
	   - For this reason, special ryukishi images are always resized to match their PS3 counterpart, so that
	     they work properly in-game.

	SMALL_IMAGE_MODE:
	 - If set to True, all ryukishi images will be resized to the same size as the original PS3 image
	 - If set to False, will resize according to below:

	FOUR_THREE_ASPECT:
	 - If SMALL_IMAGE_MODE is set to False, this setting is ignored
	 - If set to TRUE, no resizing of "Normal" ryukishi images will be performed, and if a non-4:3 ryukishi image
	   is detected, an exception will be thrown
	 - If set to FALSE, "Normal" ryukishi images will be resized to 16:9 aspect ratio. I don't think there is any
	   use for this any more, since the engine can automatically resize ryukishi backgrounds to 16:9.
	"""

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
	"""
	Given the path to a modded image / PS3 image (src_ps3_path) and a unmodded / Ryukishi image (src_ryukishi_path):
	 - Do some checks on the Ryukishi image to make sure it's the right format etc.
	 - Resize the image if necessary for it to work in our mod (see the resize_image() function)
	 - Apply any filter effects if the PS3 path implies it should have some effect (like 'flashback', 'greyscale' etc.)
	 - Save the new image to dst_path
	"""
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


def main_legacy_ch_1_8(small_image_mode, four_three_aspect):
	"""
	This function copies (with filter effects/resize when necessary) unmodded background images so they match
	the folder structure of our mod. It does the following:
	 - compile previous mapping files into one file
	 - iterate over all the 'normal' modded ps3 images and output a corresponding modified ryukishi image suitble for the mod
	 - repeat the above but for the 'scenario' images, which are handled slightly differently
	 - copy any manually pre-processed images (files which have been hand edited) directly to the output folder
	 - an extra step which copies files from the output folder to a format which our mod accepts (I'm not sure why this step is necessary...)
	"""
	# Regenerate the `background_matching/manual_bg_map_paths_generated.csv` file
	backgrounds_legacy_identify_cg.identify_cg_easy()

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
	for i in range(1, LAST_EPISODE + 1):
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

	for i in range(1, LAST_EPISODE + 1):
		src_path = os.path.join(output_folder, ps3_folder, f'ep{i}')

		# Copy pre-processed images common to all projects
		shutil.copytree('preprocessed_common', src_path, dirs_exist_ok=True)

		# move files from path `higu_backgrounds_output/imageComparer/external/ps3/epX` to
		# `higu_backgrounds_output/epX/HigurashiEp0X_Data/StreamingAssets`
		dest_containing_folder = os.path.join(output_folder, f'ep{i}/HigurashiEp0{i}_Data/StreamingAssets')
		dest_path = os.path.join(dest_containing_folder, 'OGBackgrounds')
		os.makedirs(dest_containing_folder, exist_ok=True)
		os.rename(src_path, dest_path)

def main(small_image_mode, four_three_aspect):
	"""
	This function copies (with filter effects/resize when necessary) unmodded background images so they match
	the folder structure of our mod. It does the following:
	 - compile previous mapping files into one file
	 - iterate over all the 'normal' modded ps3 images and output a corresponding modified ryukishi image suitble for the mod
	 - repeat the above but for the 'scenario' images, which are handled slightly differently
	 - copy any manually pre-processed images (files which have been hand edited) directly to the output folder
	 - an extra step which copies files from the output folder to a format which our mod accepts (I'm not sure why this step is necessary...)
	"""
	debugPrint = False

	# Set to None to check all episodes
	if len(sys.argv) != 2:
		print("Please specify which chapter number to generate eg `python copy_images_using_mapping.py 9`")
		exit(-1)

	episode = int(sys.argv[1])

	# Validate backgrounds before running this script
	if validate_matching.CheckBackgrounds(printContext=False, episode=episode):
		print('Validation successful')
	else:
		raise SystemExit('Validation FAILED - please check console output for specific errors. Background generation aborted')

	# Regenerate the `background_matching/manual_bg_map_paths_generated.csv` file
	# backgrounds_identify_cg.identify_cg_easy()

	output_folder = 'higu_backgrounds_output'

	csv_path = 'imageComparer/manual_background_mapping.csv'
	input_ryukishi_images_merged = 'imageComparer\\external\\ryukishi'
	input_modded_current_chapter = 'imageComparer\\external\\ps3'

	# check the input ryukishi graphics folder exists
	if not os.path.exists(input_ryukishi_images_merged):
		raise SystemExit(f"ERROR: ryukishi image input folder [{input_ryukishi_images_merged}] is missing.\n"
		"please create it and copy in the unmodded CG folders from all (they can overwrite each other)")

	# check the input modded ps3 graphics folder exists
	if not os.path.exists(input_modded_current_chapter):
		raise SystemExit(f"ERROR: ryukishi image input folder [{input_modded_current_chapter}] is missing.\n"
		"please create it and copy in the unmodded CG folders from all (they can overwrite each other)")


	# # Load all the rows
	with open(csv_path, newline='') as csvfile:
		reader = csv.reader(csvfile, delimiter=',', quotechar='"')
		header_row = reader.__next__()
		print(f"Header: {header_row}\n")
		all_rows = [row for row in reader]

	# Create a mapping of ryukishi filename -> ryukishi filepath
	ryukishi_filename_to_filepath_map = buildFilenameFilepathMap(	folder=input_ryukishi_images_merged,
																	pathFilterStrings=None,
																	pathToNameFunction=normalizeFilenameAndRemoveExtension,
																	warnLevel=0)

	print(f"Loaded {len(ryukishi_filename_to_filepath_map)} ryukishi filename to filepath mappings")

	# Create mapping of ps3 filename -> ryukishi path
	# Ignore rows with "NO_MATCH"
	print("> Generating Mapping")
	num_effect = 0
	num_no_match = 0
	ps3_filename_to_ryukishi_name = {}
	for row in all_rows:
		ps3_filename = row[1]  # PS3 filename without extension
		best_ryukishi_match = row[4]
		match_type = row[5]
		if match_type == 'EFFECT':
			num_effect += 1
			if debugPrint:
				print(f"WARNING: Discarding mapping for effect image [{ps3_filename}] [{best_ryukishi_match}]")
		elif ps3_filename == 'NO_MATCH' or best_ryukishi_match == 'NO_MATCH':
			num_no_match += 1
			if debugPrint:
				print(f"WARNING: not adding file with no match to mapping: [{ps3_filename}] [{best_ryukishi_match}]")
		else:
			ps3_filename_to_ryukishi_name[ps3_filename.lower()] = best_ryukishi_match

	print(f"Skipping {num_effect} effect images and {num_no_match} images with no match")

	# Use *.* instead of * to match only files
	# Use ? to match a single character for ep1, ep2, ep3 etc.
	ps3_paths_to_replace = list(itertools.chain(
			Path(input_modded_current_chapter).rglob('bg/**/*.*'),
	))

	print(f"Attempting to replace {len(ps3_paths_to_replace)} modded ps3 images")

	errors = 0

	for input_modded_path in ps3_paths_to_replace:
		# Determine which ryukishi image should be copied
		basename = os.path.basename(input_modded_path)
		name_no_ext, ext = os.path.splitext(basename)
		ryukishi_name = ps3_filename_to_ryukishi_name.get(name_no_ext.lower(), None)

		output_path = os.path.join(output_folder, input_modded_path)
		os.makedirs(os.path.dirname(output_path), exist_ok=True)

		if ryukishi_name is None:
			print(f"WARNING: mapping[{name_no_ext}] not found for {input_modded_path}")
			with open(output_path + '.NO_MATCH', 'w') as f:
				pass

			errors += 1
		else:
			ryukishi_unmodded_path = ryukishi_filename_to_filepath_map[ryukishi_name]

			if debugPrint:
				print(f"Replacing {input_modded_path} with {ryukishi_unmodded_path} saved to {output_path}")

			if os.path.exists(output_path):
				raise Exception(f"Error: output file already exists {output_path}")

			process_image(input_modded_path, ryukishi_unmodded_path, output_path, small_image_mode, four_three_aspect)

	if errors > 0:
		print(f"-------- {errors} ERRORS OCCURED - please check logs and check for *.NO_MATCH files in the output folder --------")
	else:
		print(f"-------- SUCCESS --------")

if __name__ == '__main__':
	main(small_image_mode=True, four_three_aspect=True)
