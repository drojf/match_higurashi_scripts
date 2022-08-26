import csv
import os

ep8_required_sprites = [
	"aks1_sakebi_",
	"aks1_shinken_",
	"aks2_kakusei_",
	"aks2_niyari_",
	"aks2_sakebi_",
	"aks2_shinken_",
	"ha1_muhyou_",
	"ha1_sakebi_",
	"ha1_shinken_",
	"ha2a_au_",
	"ha2a_def_",
	"ha2a_def2_",
	"ha2a_muhyou_",
	"ha2a_odoroki_",
	"ha2a_sakebi_",
	"ha2a_warai_",
	"ha2a_yowaki_",
	"ha2b_def_",
	"ha2b_def2_",
	"ha2b_warai_",
	"ha3a_au_",
	"ha3a_def_",
	"ha3a_def2_",
	"ha3a_odoroki_",
	"ha3a_warai_",
	"ha3a_yowaki_",
	"oko_def_",
	"oko_kumon_",
	"oko_niyari_",
	"oko_odoroki_",
	"oko_sakebi_",
	"sa2b_hau_b1_",
	"si1b_majime_b1_",
	"si1b_odoroki_b1_",
	"si1b_tohoho_b1_",
	"ta1_iradachi_",
	"ta1_kanashimi_",
	"ta1_sakebi_",
	"ta2_iradachi_",
	"ta2_kanashimi_",
	"ta2_sakebi_",
	"ta3_human_",
	"ta3_iradachi_",
	"ta3_sakebi_",
	"ta5_akuwarai_",
	"ta5_human_",
	"ta5_iradachi_",
	"ta5_sakebi_",
	"tomi1_shinken_",
	"tomi2_shinken_",
	"tomi3_ikari_",
	"tomi3_komaru_",
	"tomi3_shinken_",
	"tomi3_warai_",
]

seen_sprites = set()
new_sprites = set()

with open("merged_output.csv", 'w', encoding='utf-8') as output_file:

	with open('imageComparer/noconsole_output.txt.csv', 'r', encoding='utf-8', newline='') as older_csvfile:
		reader = csv.reader(older_csvfile)
		#first row is always header
		header = reader.__next__()
		output_file.write(','.join(header) + '\n')
		for row in reader:
			ps3_path = row[1]
			ps3_name = os.path.basename(ps3_path)
			seen_sprites.add(ps3_name)
			output_file.write(','.join(row) + '\n')

	with open('noconsole_output.txt.csv', 'r', encoding='utf-8', newline='') as new_csvfile:
		reader = csv.reader(new_csvfile)
		#first row is always header
		header = reader.__next__()
		for row in reader:
			ps3_path = row[1]
			ps3_name = os.path.basename(ps3_path)
			new_sprites.add(ps3_name)
			if ps3_name not in seen_sprites:
				print("NEW ROW: {}".format(row))
				output_file.write(','.join(row) + '\n')

	for sprite_name in ep8_required_sprites:
		if sprite_name not in new_sprites:
			print("Missing: ", sprite_name)
