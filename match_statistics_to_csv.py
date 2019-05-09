from match_statistics import MatchStatistics


class MatchRow:
	def __init__(self, ps3file, source, highestCount, confidence, sorted_scores):
		self.ps3file = ps3file
		self.source = source
		self.highestCount = highestCount
		self.confidence = confidence
		self.sorted_scores = sorted_scores


def pad_array(arr, target_length, pad_value):
	addon = [pad_value] * (target_length - len(arr))
	return arr + addon


def get_sorted_matches(matches):
	return sorted(matches.items(), key=lambda x:x[1], reverse=True)


def convertMatchingToCSV(match_statistics : MatchStatistics) -> [str]:
	rows = []
	for sourceMatch, destinationMatches in match_statistics.statistics.items():
		sourceFile = match_statistics.sprite_to_file_mapping.get(sourceMatch, "")

		if len(destinationMatches) > 0:
			sorted_matches = get_sorted_matches(destinationMatches)
			best_match = sorted_matches[0]
			total_score = sum([x[1] for x in sorted_matches])
			best_match_confidence = best_match[1] / total_score * 100

			# highestCountName, highestCount, confidence = getBestMatchAndConfidence(destinationMatches)
			rows.append(MatchRow(sourceFile, sourceMatch, best_match[1], best_match_confidence, sorted_matches))
		else:
			rows.append(MatchRow(sourceFile, sourceMatch, 0, 0, []))

	rows.sort(key=lambda x: x.source)
	rows.sort(key=lambda x: x.confidence, reverse=True)
	rows.sort(key=lambda x: x.highestCount, reverse=True)

	#for consistent CSV rows, determine the max number of columns first
	max_matches = 0
	for row in rows:
		if len(row.sorted_scores) > max_matches:
			max_matches = len(row.sorted_scores)

	rows_as_strings = []
	header_matches = ','.join(pad_array(['all matches'], max_matches, 'match'))
	rows_as_strings.append(f'ps3 sprite file, source image, count of best match, confidence,{header_matches}')
	for row in rows:
		matches = [f'{x[1]}:{x[0]}' for x in row.sorted_scores]
		matches = pad_array(matches, max_matches, '')
		rows_as_strings.append(f"{row.ps3file},{row.source},{row.highestCount},{row.confidence:.0f}%,{','.join(matches)}")

	return rows_as_strings