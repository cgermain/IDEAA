import os
from os.path import join
import subprocess

debug = False
# debug = True

def select_only_one(mgf_read_path, mgf_write_path, mgf_txt_write_path, mz_error, reporter_type, min_intensity, min_reporters, should_select):
	print "Selecting only one, not precompiled"
	perl_file = 'mgf_select_only_one.pl'

	if os.path.isfile(mgf_txt_write_path):
		return "mgf_txt_write_path is already a file"
	if should_select == "1" and os.path.isfile(mgf_write_path):
		return "mgf_write_path is already a file"

	this_dir = os.path.dirname(os.path.realpath(__file__))

	perl_array = ['perl', join(this_dir, perl_file), mgf_read_path, \
		mgf_write_path, mgf_txt_write_path, str(mz_error), reporter_type, \
		str(min_intensity), str(min_reporters), str(should_select)]

	print "Debug: " + str(debug)
	if debug:
		output = subprocess.check_output(perl_array)
		print output
		return output
	else:
		a = subprocess.call(perl_array)
		if a:
			return "Error selecting from mgf (no recalibration)"
		else:
			return 0

def select_only_one_recalibrate(mgf_read_path, mgf_write_path, mgf_txt_write_path, mz_error, reporter_type, min_intensity, min_reporters, should_select, recal_mz_error):
	this_dir = os.path.dirname(os.path.realpath(__file__))
	perl_file = 'mgf_select_only_one_with_recalibrate.pl'

	if os.path.isfile(mgf_txt_write_path):
		return "mgf_txt_write_path is already a file"
	if should_select == "1" and os.path.isfile(mgf_write_path):
		return "mgf_write_path is already a file"


	perl_array = ['perl', join(this_dir, perl_file), mgf_read_path, mgf_write_path, \
		mgf_txt_write_path, str(mz_error), reporter_type, str(min_intensity), \
		str(min_reporters), str(should_select), str(recal_mz_error)]
	print perl_array

	print "Debug: " + str(debug)
	if debug:
		output = subprocess.check_output(perl_array)
		print output
		return output
	else:
		a = subprocess.call(perl_array)
		if a:
			return "Error selecting from mgf (with recalibration)"
		else:
			return 0

	


def test_drive():
	print "GREAT JOB SUCCESS NOW"
	return "Good job very nice"
