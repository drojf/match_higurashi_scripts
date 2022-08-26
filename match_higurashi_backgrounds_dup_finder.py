from utility import save_rows, load_rows


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


if __name__ == '__main__':
	auto_matching_path = 'background_matching_intermediate/auto_matching.csv'
	naegles_remapped_path = 'background_matching_intermediate/naegles_remapped.csv'
	merged_output_path = 'background_matching_intermediate/merged_mapping.csv'

	merge_auto_matching_and_naegles(auto_matching_path, naegles_remapped_path, merged_output_path)
