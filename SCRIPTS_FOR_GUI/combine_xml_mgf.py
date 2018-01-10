from pandas import Series, DataFrame
import pandas as pd
import numpy as np
import sys, os, shutil
import utility
from os.path import join
from datetime import datetime
from collections import defaultdict

TIME_FORMAT =  "%Y-%m-%d_%H-%M-%S"

#all of the initial files have got to be relative to this directory.
this_dir = os.path.dirname(os.path.realpath(__file__))

def remove_duplicate_lines(filename):
	suffix = '_with_duplicates_removed'
	lines_seen = set()
	write_dest = filename + suffix
	outfile = open(write_dest, "w")
	for line in open(filename, "r"):
		if line not in lines_seen:
			outfile.write(line)
			lines_seen.add(line)
		else:
			print "duplicate line removed: " + str(line)
	outfile.close()
	os.remove(filename)
	os.rename(write_dest, filename)


def clear_directory_of_files(directory):
	print "clearing dir of files"
	for item in os.listdir(directory):
		if os.path.isfile(item):
			toRemove = directory + os.sep + item
			os.remove(directory + os.sep + item)
			print toRemove + " removed"


def transform_firstline_for_n_and_c(firstline):
	stripped = firstline.strip()
	split = stripped.split('\t')
	num_fields = len(split)
	i = 0
	while i < num_fields - 1:
		first = split[i]
		second = split[i+1]
		if second.endswith('.1'):
			pre_end = second.partition('.1')[0]
			if pre_end != first:
				print "Changeing first line so rep. ions end in N or C instead of .1. " +\
							" This should only happen when two rep. ions have the same integer-mass." +\
							" For some reason it is happening elsewhere. Printing old first line for debugging."
				print firstline
				raise Exception("very strange these headers are not equal, they should be.")
			new_first = pre_end + "N"
			new_second = pre_end + "C"
			split[i] = new_first
			split[i+1]=new_second
			i += 1
		i += 1
	new_firstline = '\t'.join(split)
	return new_firstline
	

def add_a_or_b_label_to_sorted_mfg_txt_file(filename):
	a = open(filename, "r")
	temp_filename = filename + "_PLACEHOLDER"
	temp_file = open(temp_filename, "w")

	first_line = a.readline()
	first_line = transform_firstline_for_n_and_c(first_line)

	temp_file.write(first_line.strip() + "\treplicate_spec_flag\n")
	first_line_arr = first_line.split('\t')
	filename_index = first_line_arr.index("filename")
	scan_index = first_line_arr.index("scan")
	charge_index = first_line_arr.index("charge")

	if scan_index == -1 or filename_index == -1 or charge_index == -1:
		raise Exception("something is wrong with the file formatting")
	scan_list = []
	first = True
	most_recent = (None, None, None)
	for line in a:
		line_arr = line.split("\t")
		curr_scan = line_arr[scan_index]
		curr_filename = line_arr[filename_index]
		curr_charge = line_arr[charge_index]
		tup = (curr_filename, curr_scan, curr_charge)
		if (not first) and (not (most_recent[1] == tup[1])):
			all_charges_in_list = [l.split("\t")[charge_index] for l in scan_list]

			if len(scan_list) == 0:
				# continue even if the scan list is empty 
				pass
				# raise Exception("In add a or b, shouldn't be zero")
			elif len(scan_list) == 1:
				temp_file.write(scan_list[0].strip() + "\tA\n")
			#if the charges match, write it out as A
			#indicates we created a second entry for this scan with different sequences
			elif all(x==all_charges_in_list[0] for x in all_charges_in_list):
				for l in scan_list:
					temp_file.write(l.strip() + "\tA\n")
			#write it out as a B so it can either be dropna'd or continue onto being C labeled
			else:
				for l in scan_list:
					temp_file.write(l.strip() + "\tB\n")
			scan_list = []
		scan_list.append(line)
		most_recent = tup
		first = False

	#process the last scan_list
	all_charges_in_list = [l.split("\t")[charge_index] for l in scan_list]

	if len(scan_list) == 0:
		# continue even if the scan list is empty 
		pass
		# raise Exception("In add a or b, shouldn't be zero")
	elif len(scan_list) == 1:
		temp_file.write(scan_list[0].strip() + "\tA\n")
	#if the charges match, write it out as A
	#indicates we created a second entry for this scan with different sequences
	elif all(x==all_charges_in_list[0] for x in all_charges_in_list):
		for l in scan_list:
			temp_file.write(l.strip() + "\tA\n")
	#write it out as a B so it can either be dropna'd or continue onto being C labeled
	else:
		for l in scan_list:
			temp_file.write(l.strip() + "\tB\n")

	a.close()
	temp_file.close()
	os.remove(filename)
	os.rename(temp_filename,filename)


#this reevaluates the A/B labels after sequences have been duplicated
def add_c_labels_to_duplicate_marker_column(filename):
	a = open(filename, "r")
	temp_filename = filename + "_PLACEHOLDER"
	temp_file = open(temp_filename, "w")

	first_line = a.readline()
	temp_file.write(first_line)
	first_line_arr = first_line.split('\t')
	filename_index = first_line_arr.index("filename")
	scan_index = first_line_arr.index("scan")
	charge_index = first_line_arr.index("charge")
	duplicate_index = first_line_arr.index("replicate_spec_flag")
	log_e_index = first_line_arr.index("protein log(e)")
	unique_peptide_index = first_line_arr.index("unique peptides")

	if scan_index == -1 or filename_index == -1 or duplicate_index == -1 or log_e_index == -1 or charge_index == -1 or unique_peptide_index == -1:
		raise Exception("something is wrong with the file formatting")
	
	scan_list = []
	first = True
	most_recent = (None, None, None)

	for line in a:
		line_arr = line.split("\t")
		curr_scan = line_arr[scan_index]
		curr_filename = line_arr[filename_index]
		curr_charge = line_arr[charge_index]
		curr_replicate_spec_flag = line_arr[duplicate_index]
		tup = (curr_filename, curr_scan, curr_charge)
		if (not first) and (not (most_recent[1] == tup[1])):
			if len(scan_list) == 0:
				# continue even if the scan list is empty
				pass 
				# raise Exception("Shouldn't be zero")
			elif len(scan_list) == 1:
				temp_file.write("\t".join(scan_list[0]))
			#if multiple items are in the scan list
			else:
				#if all of the charges are equal, they're all A's
				if all(scan[charge_index] == scan_list[0][charge_index] for scan in scan_list):
					new_list = [(float(l[log_e_index]), l) for l in scan_list]
					new_list = sorted(new_list)
					letters = utility.long_alphabet()
					for i in range(len(new_list)):
						arr = new_list[i][1]
						arr[duplicate_index] = "A"
						#add a ranking to each unique peptide
						arr[unique_peptide_index] = arr[unique_peptide_index]+letters[i]
						temp_file.write("\t".join(arr)) 
				
				#if there are multiple duplicate charges in the list, they're A's
				#if there are single charges, they're B's
				#if there are multiple single charges, they're C's
				else:

					final_scan_list_to_sort = []
					scan_dict = defaultdict(list)
					for scan in scan_list:
						scan_dict[scan[charge_index]].append(scan)

					single_charges = []
					multiple_charges = []

					#for each charge, if its unique, add that scan to the single charges list (meaning these are Cs)
					for key in scan_dict:
						if len(scan_dict[key]) == 1:
							single_charges.append(scan_dict[key])
						else:
							multiple_charges.append(scan_dict[key])

					#flatten the list of lists
					single_charges_combined = [item for sublist in single_charges for item in sublist]
					multiple_charges_combined = [item for sublist in multiple_charges for item in sublist]

					#if there are multiple single charges, write them out as C's
					if len(single_charges) > 1:
						c_new_scanlist = [(float(l[log_e_index]), l) for l in single_charges_combined]
						c_new_scanlist = sorted(c_new_scanlist)
						letters = utility.long_alphabet()
						for i in range(len(c_new_scanlist)):
							c_new_scanlist[i][1][duplicate_index] = "C" + str(i + 1)
							unique_peptide_count = c_new_scanlist[i][1][unique_peptide_index]
							if (int(unique_peptide_count) > 1):
								c_new_scanlist[i][1][unique_peptide_index] = unique_peptide_count + letters[i]
							final_scan_list_to_sort.append(c_new_scanlist[i][1])

					#if there is just one, write it back out as a B
					else:
						single_charges_combined[0][duplicate_index] = "B"
						final_scan_list_to_sort.append(single_charges_combined[0])

					letters = utility.long_alphabet()
					#We've found a mix of A's and B/C, so we have to relabel them	
					for i, charges in enumerate(multiple_charges_combined):
						charges[duplicate_index] = "A"
						charges[unique_peptide_index] = charges[unique_peptide_index] + letters[i]
						final_scan_list_to_sort.append(charges)

					#sort the final list
					final_scan_list_to_sort = [(float(l[log_e_index]), l) for l in final_scan_list_to_sort]
					final_scan_list_sorted = sorted(final_scan_list_to_sort)
					for sorted_scan in final_scan_list_sorted:
						temp_file.write("\t".join(sorted_scan[1]))

			scan_list = []
		scan_list.append(line_arr)
		most_recent = tup
		first = False

	#catch the last scanlist and process it
	if len(scan_list) == 0:
		# continue even if the scan list is empty
		pass 
		# raise Exception("Shouldn't be zero")
	elif len(scan_list) == 1:
		temp_file.write("\t".join(scan_list[0]))
	#if multiple items are in the scan list
	else:
		#if all of the charges are equal, they're all A's
		if all(scan[charge_index] == scan_list[0][charge_index] for scan in scan_list):
			#print "Found a group of A's"
			new_list = [(float(l[log_e_index]), l) for l in scan_list]
			new_list = sorted(new_list)
			letters = utility.long_alphabet()
			for i in range(len(new_list)):
				arr = new_list[i][1]
				arr[duplicate_index] = "A"
				#add a ranking to each unique peptide
				arr[unique_peptide_index] = arr[unique_peptide_index]+letters[i]
				temp_file.write("\t".join(arr)) 
		
		#if there are multiple duplicate charges in the list, they're A's
		#if there are single charges, they're B's
		#if there are multiple single charges, they're C's
		else:
			final_scan_list_to_sort = []
			scan_dict = defaultdict(list)
			for scan in scan_list:
				scan_dict[scan[charge_index]].append(scan)

			single_charges = []
			multiple_charges = []

			#for each charge, if its unique, add that scan to the single charges list (meaning these are Cs)
			for key in scan_dict:
				if len(scan_dict[key]) == 1:
					single_charges.append(scan_dict[key])
				else:
					multiple_charges.append(scan_dict[key])

			#flatten the list of lists
			single_charges_combined = [item for sublist in single_charges for item in sublist]
			multiple_charges_combined = [item for sublist in multiple_charges for item in sublist]

			#if there are multiple single charges, write them out as C's
			if len(single_charges) > 1:
				c_new_scanlist = [(float(l[log_e_index]), l) for l in single_charges_combined]
				c_new_scanlist = sorted(c_new_scanlist)
				letters = utility.long_alphabet()
				for i in range(len(c_new_scanlist)):
					c_new_scanlist[i][1][duplicate_index] = "C" + str(i + 1)
					unique_peptide_count = c_new_scanlist[i][1][unique_peptide_index]
					if (int(unique_peptide_count) > 1):
						c_new_scanlist[i][1][unique_peptide_index] = unique_peptide_count + letters[i]
					final_scan_list_to_sort.append(c_new_scanlist[i][1])
			#if there is just one, write it back out as a B
			else:
				single_charges_combined[0][duplicate_index] = "B"
				final_scan_list_to_sort.append(single_charges_combined[0])

			#We've found a mix of A's and B/C, so we have to relabel them	
			letters = utility.long_alphabet()
			for i, charges in enumerate(multiple_charges_combined):
				charges[duplicate_index] = "A"
				charges[unique_peptide_index] = charges[unique_peptide_index] + letters[i]
				final_scan_list_to_sort.append(charges)

			#sort the final list
			final_scan_list_to_sort = [(float(l[log_e_index]), l) for l in final_scan_list_to_sort]
			final_scan_list_sorted = sorted(final_scan_list_to_sort)
			for sorted_scan in final_scan_list_sorted:
				temp_file.write("\t".join(sorted_scan[1]))

	a.close()
	temp_file.close()
	os.remove(filename)
	os.rename(temp_filename,filename)


def take_in_file_sorted_by_filename_scan_output_file_with_duplicate_marker_column(filename):
	a = open(filename, "r")
	temp_file = open(filename + "_PLACEHOLDER", "w")
	
	first_line = a.readline()
	temp_file.write(first_line.strip() + "\treplicate_spec_flag\n")

	first_line_arr = first_line.split('\t')
	log_e_index = first_line_arr.index("peptide expectation") #Hopefully it's there
	scan_index = first_line_arr.index("scan")
	filename_index = first_line_arr.index("filename")
	if scan_index == -1 or filename_index == -1:
		raise Exception("something is wrong with the file formatting")
	scan_list = []
	curr_values = (None, None)
	for line in a:
		line_arr = line.split("\t")
		curr_scan = line_arr[scan_index]
		curr_log_e = float(line_arr[log_e_index])
		curr_filename = line_arr[filename_index]
		tup = (curr_filename, curr_scan)
		if curr_values == tup:
			#dealing with duplicates
			scan_list.append((log_e, line))
		else:
			scan_list = sorted(scan_list)
			lines = [elem[1] for elem in scan_list]
			if len(lines) == 0:
				raise Exception("length zero?")
			elif len(lines) == 1:
				for i in range(len(lines)):
					#needed?
					print i
			else:
				print "line length > 1"


def remove_log_e_duplicates(filename):
	a = open(filename, "r")

	first_line = a.readline()
	first_line_arr = first_line.split('\t')
	log_e_index = first_line_arr.index("peptide expectation") #Hopefully it's there
	scan_index = first_line_arr.index("scan")

	scan_set = set()
	least_dict = {}
	duplicates_set = set()

	# reads rest of file
	for line in a:
		line_arr = line.split("\t")
		scan = line_arr[scan_index]
		log_e = float(line_arr[log_e_index])

		if scan not in scan_set:
			scan_set.add(scan)
			least_dict[scan] = log_e
		else: #we've seen it before
			least_dict[scan] = min(least_dict[scan], log_e)
			duplicates_set.add(scan) #find the smallest scan, add it to duplicates
		# Here, we've run through the file, found all the duplicates, found the smallest value.
		# Now, we just need to re-run through, writing the least only.

	a.close()
	a = open(filename, "r") #get to the beginning again
	tempdest = filename + "_with_duplicates_deleted" 
	# os.remove(tempdest)  # there were errors before because it was appending instead of overwriting. 
	b = open(tempdest, "w")

	first_line = a.readline()
	b.write(first_line)

	already_written = set() #this is a little annoying, but what if there's two things with the same
							#scan and the same error? Then we get duplicates. And certainty is worth speed.

	for line in a:
		line_arr = line.split("\t")
		scan = line_arr[scan_index]
		log_e = float(line_arr[log_e_index])

		if scan not in already_written:
			if log_e == least_dict[scan]:
				b.write(line)
				already_written.add(scan)
	b.close()
	a.close()

	os.remove(filename) #On windows you've got to remove the destination first.
	os.rename(tempdest, filename)


def check_for_selected_xmldir_lineup(selected_mgfdir, xmldir):
	if not os.path.isdir(selected_mgfdir):
		return False, "Selected mgf directory doesn't exist"
	if not os.path.isdir(xmldir):
		return False, "xmldir doesn't exist"
	for filename in os.listdir(xmldir):
		if filename.endswith('.reporter'):
			reporter_filename = join(selected_mgfdir, filename)
			if not os.path.isfile(reporter_filename):
				return False, str(filename) + " does not exist in the selected mgfdir"
	return True, None

def combine_plain_parsed_xml_mgf(selected_mgfdir, xmldir, timestamp):
	try:
		this_dir = os.path.dirname(os.path.realpath(__file__))	

		# I should check here to make sure the files line up.
		linesup, message = check_for_selected_xmldir_lineup(selected_mgfdir, xmldir)
		if not linesup:
			print "XML doesn't line up in plain parse"
			return message

		xmldir = join(xmldir,"")
		parent_xml_filename = os.path.basename(os.path.normpath(xmldir))
		for filename in os.listdir(xmldir):
			if filename.endswith('.reporter'):
				print "Processing: " + filename
				xml_filename = join(xmldir, filename)
				mgf_txt_filename = join(selected_mgfdir, filename)
				mgf = pd.read_table(mgf_txt_filename, index_col=['filename','scan','charge'])
				mgf.sort_index()
				testing_filename = mgf_txt_filename.split('.reporter')[0] + '_duplicate_sorted' + '.reporter'
				mgf.to_csv(testing_filename, sep='\t')
				add_a_or_b_label_to_sorted_mfg_txt_file(testing_filename)
				mgf = pd.read_table(testing_filename, index_col=['filename','scan','charge'])
				xml = pd.read_table(xml_filename, index_col=['filename','scan','charge'])
				dfc=pd.merge(mgf,xml, left_index=True, right_index=True)
				dfc_=dfc.dropna()
				dfc_=dfc_.drop("labeling",1)
				csv_filename = join(xmldir, filename + '_nocal_table.txt')
				dfc_.to_csv(csv_filename,sep='\t')
				os.remove(testing_filename)
				data = pd.read_table(csv_filename)
				this_filename = join(xmldir, filename + '_nocal_table_corrected.txt')
				data.to_csv(this_filename,sep='\t',index=False)

		first=1
		outfile_name = join(selected_mgfdir, parent_xml_filename + '_' + timestamp + '.txt')
		with open(outfile_name, 'w') as outfile:
			for filename in os.listdir(xmldir):
				if filename.endswith('_nocal_table_corrected.txt'):
					with open(join(xmldir, filename)) as infile:
						for line in infile:
							if (not 'other proteins' in line) or (first==1):
								first = 0
								outfile.write(line)
		add_c_labels_to_duplicate_marker_column(outfile_name)
		return
	except Exception as err:
		print err
		return "Error combining xml and mgf in plain parse"

def combine_parsed_xml_mgf(selected_mgfdir, xmldir, reporter_ion_type, normalize_intensities, timestamp):
	try:
		this_dir = os.path.dirname(os.path.realpath(__file__))
		#checking reporter ion type
		if reporter_ion_type=='iTRAQ4':
			start_col=reporter_ion_type+'-114'
			end_col=reporter_ion_type+'-117'
			label_mass_int=144
		elif reporter_ion_type=='iTRAQ8':
			start_col=reporter_ion_type+'-113'
			end_col=reporter_ion_type+'-121'
			label_mass_int=304
		elif reporter_ion_type=='TMT0':
			start_col=reporter_ion_type+'-126'
			end_col=reporter_ion_type+'-126'
			label_mass_int=225
		elif reporter_ion_type=='TMT2':
			start_col=reporter_ion_type+'-126'
			end_col=reporter_ion_type+'-127'
			label_mass_int=225
		elif reporter_ion_type=='TMT6':
			start_col=reporter_ion_type+'-126'
			end_col=reporter_ion_type+'-131'
			label_mass_int=229
		elif reporter_ion_type=='TMT6OLD':
			start_col=reporter_ion_type+'-126'
			end_col=reporter_ion_type+'-131'
			label_mass_int=229
		elif reporter_ion_type=='TMT10':
			start_col=reporter_ion_type+'-126'
			end_col=reporter_ion_type+'-131'
			label_mass_int=229
		elif reporter_ion_type=='TMT11':
			start_col=reporter_ion_type+'-126'
			end_col=reporter_ion_type+'-131C'
			label_mass_int=229
		else:
			print "bad reporter ion type"
			return "BAD REPORTER ION TYPE"

		# I should check here to make sure the files line up.
		linesup, message = check_for_selected_xmldir_lineup(selected_mgfdir, xmldir)
		if not linesup:
			print "XML doesn't line up"
			return message

		xmldir = join(xmldir,"")
		parent_xml_filename = os.path.basename(os.path.normpath(xmldir))
		# if first loop through
		summary_file = selected_mgfdir+"\intensity_summary.txt"

		normalized_intensities = read_intensities_from_summary_and_normalize(summary_file)

		# Problem is that it's an empty folder!
		for filename in os.listdir(xmldir):
			if filename.endswith('.reporter'):
				print "Processing: " + filename
				xml_filename = join(xmldir, filename)
				mgf_txt_filename = join(selected_mgfdir, filename)
				mgf = pd.read_table(mgf_txt_filename, index_col=['filename','scan','charge'])
				mgf.sort_index()
				testing_filename = mgf_txt_filename.split('.reporter')[0] + '_duplicate_sorted' + '.reporter'
				mgf.to_csv(testing_filename, sep='\t')
				add_a_or_b_label_to_sorted_mfg_txt_file(testing_filename)
				#read mgf table
				mgf = pd.read_table(testing_filename, index_col=['filename','scan','charge'])
				xml = pd.read_table(xml_filename, index_col=['filename','scan','charge'])
				dfc=pd.merge(mgf,xml, left_index=True, right_index=True)
				dfc_=dfc.dropna()
				csv_filename = join(xmldir, filename + '_nocal_table.txt')
				#writing to csv
				dfc_.to_csv(csv_filename,sep='\t')
				os.remove(testing_filename)
				data = pd.read_table(csv_filename)

				labels = list(data.columns.values)
				if normalize_intensities[0] == "0":
					norm_start = labels.index(start_col)
					norm_end = labels.index(end_col) + 1

					for ion_type in labels[norm_start:norm_end]:
						data[ion_type+"_norm_total"] = ""

				if normalize_intensities[0] == "0":
					# crossover correction now happens during selection
					# only need to loop through for normalizing total intensities
					for k in range(len(data)):
						# this next line gets the kth row, and the start_col to end_col columns, which are strings like iTRAQ-115.
						temp = data.ix[k,start_col:end_col]
						temp_intensities = [float(intensity)/norm if norm != 0 else 0 for intensity, norm in zip(temp, normalized_intensities)]
						if sum(temp_intensities) == 0:
							normalized_temp_intensities = temp_intensities
						else:
							normalized_temp_intensities = [float(intensity)/sum(temp_intensities) for intensity in temp_intensities]
						if len(normalized_temp_intensities) == 1:
							data.ix[k,start_col+"_norm_total":end_col+"_norm_total"] = normalized_temp_intensities[0]
						else:
							data.ix[k,start_col+"_norm_total":end_col+"_norm_total"] = normalized_temp_intensities
				
				this_filename = join(xmldir, filename + '_nocal_table_corrected.txt')
				data.to_csv(this_filename,sep='\t',index=False)

		first=1
		outfile_name = join(selected_mgfdir, parent_xml_filename + '_' + timestamp + '.txt')
		with open(outfile_name, 'w') as outfile:
			for filename in os.listdir(xmldir):
				if filename.endswith('_nocal_table_corrected.txt'):
					with open(join(xmldir, filename)) as infile:
						for line in infile:
							if (not 'other proteins' in line) or (first==1):
								first = 0
								outfile.write(line)
		add_c_labels_to_duplicate_marker_column(outfile_name)
		return
	except Exception as err:
		print err
		return "Error combining xml and mgf"


def read_intensities_from_summary_and_normalize(filename):
	try:
		summary = open(filename, "r")
		summary.readline() #skip the header
		intensities = [float(intensity) for intensity in summary.readline().split("\t")]
		sum_int = sum(intensities)
		if sum_int != 0:
			return [intensity/sum_int for intensity in intensities]
		else:
			return intensities
	except Exception as err:
		print "Error reading from intensity file"
		print err
		return "Error in intensity file"
						