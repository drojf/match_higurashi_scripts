import csv

LAST_EPISODE = 9

def save_rows(rows, csv_path, header_row=None):
	with open(csv_path, 'w', newline='') as csvfile:
		writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
		if header_row:
			writer.writerow(header_row)
		for row in rows:
			writer.writerow(row)


def load_rows(csv_path):
	rows = []
	with open(csv_path, newline='') as csvfile:
		reader = csv.reader(csvfile, delimiter=',', quotechar='"')
		for row in reader:
			rows.append(row)
	return rows