import csv
import os
import re

prefix_list = [
	r'^aka',  # Akane
	r'^aks\d',  # Akasaka
	r'^ha\d',  # Hanyuu
	r'^iri\d',  # Irie
	r'^kasa',  # Kasai
	r'^kei\d',  # Keiichi
	r'^me\d',  # Mion
	r'^oisi\d',  # Oishi
	r'^oko',  # Okonogi
	r'^re\d',  # Rena
	r'^ri\d',  # Rika
	r'^rina',  # Rina
	r'^sa\d',  # Satoko
	r'^sato\d',  # Satoshi
	r'^si\d',  # Shion
	r'^ta\d',  # Takano
	r'^tie',  # Chie
	r'^tetu',  # Teppei
	r'^tomi\d',  # Tomitake
]

prefix_regexes = [re.compile(x, re.IGNORECASE) for x in prefix_list]

valid_rows = []

with open('ignore_time_of_day/ignore_time_of_day.txt.csv', 'r', encoding='utf-8', newline='') as csvfile:
	spamreader = csv.reader(csvfile)
	#first row is always header
	header = spamreader.__next__()
	for row in spamreader:
		ps3_path = row[1]
		ps3_name = os.path.basename(ps3_path)

		is_whitelisted = False
		for regex in prefix_regexes:
			if regex.search(ps3_name):
				is_whitelisted = True
				break

		if is_whitelisted:
			valid_rows.append(row)

print(f"Got {len(valid_rows)} valid rows")
for r in valid_rows:
	print(r)

with open('ignore_time_of_day/ignore_time_of_day.filtered.txt.csv', 'w', encoding='utf-8', newline='') as outputfile:
	spamwriter = csv.writer(outputfile)
	spamwriter.writerow(header)
	for r in valid_rows:
		spamwriter.writerow(r)
