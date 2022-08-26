import csv
from collections import defaultdict
from utility import save_rows, load_rows

def identify_cg(final_mapping_file_path, ps3_filename_to_path_mapping_file_path, ryukishi_filename_to_path_mapping_file_path, output_path):
	def append_paths_to_rows(bg_mapping_rows, bg_mapping_rows_filename_column_index, filename_to_path_dict, column_name):
		header = bg_mapping_rows[0]
		body = bg_mapping_rows[1:]

		out_rows = [header + [column_name]]

		for row in body:
			filename = row[bg_mapping_rows_filename_column_index]
			path = filename_to_path_dict.get(filename)
			if filename == 'NO_MATCH':
				print("Ignoring NO_MATCH on row", row)
				out_rows.append(row + ['NO_MATCH'])
			elif path is None:
				print(filename, path)
				raise Exception(f"No file path for {filename} on row [{row}]")
			else:
				print(filename, path)
				out_rows.append(row + [path])

		return out_rows

	ps3_filename_to_path_dict = dict(load_rows(ps3_filename_to_path_mapping_file_path))
	ryukishi_filename_to_path_dict = dict(load_rows(ryukishi_filename_to_path_mapping_file_path))
	bg_mapping_rows = load_rows(final_mapping_file_path)

	rows_with_ps3_paths = append_paths_to_rows(bg_mapping_rows, 1, ps3_filename_to_path_dict, 'ps3_path')
	rows_with_both_paths = append_paths_to_rows(rows_with_ps3_paths, 4, ryukishi_filename_to_path_dict, 'ryukishi_path')

	save_rows(rows_with_both_paths, output_path)

def identify_cg_easy():
	identify_cg(
		final_mapping_file_path='background_matching/manual_background_mapping.csv',
		ps3_filename_to_path_mapping_file_path='imageComparer/ps3_mapping.csv',
		ryukishi_filename_to_path_mapping_file_path='imageComparer/ryukishi_mapping.csv',
		output_path='background_matching/manual_bg_map_paths_generated.csv'
	)

if __name__ == '__main__':
	identify_cg_easy()