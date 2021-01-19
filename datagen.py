# This code is adapted from the following:
# https://github.com/abisee/cnn-dailymail/blob/master/make_datafiles.py

import hashlib
import sys, os

dm_single_close_quote = u'\u2019' # unicode
dm_double_close_quote = u'\u201d'
END_TOKENS = ['.', '!', '?', '...', "'", "`", '"', dm_single_close_quote, dm_double_close_quote, ")"] # acceptable ways to end a sentence


# These are the number of .story files we expect there to be in cnn_stories_dir and dm_stories_dir
num_expected_cnn_stories = 92579
num_expected_dm_stories = 219506

CHUNK_SIZE = 1000 # num examples per chunk, for the chunked data

all_train_urls = "url_lists/all_train.txt"
all_val_urls = "url_lists/all_val.txt"
all_test_urls = "url_lists/all_test.txt"

cnn_tokenized_stories_dir = "cnn_stories_tokenized"
dm_tokenized_stories_dir = "dm_stories_tokenized"

def read_text_file(text_file):
	lines = []
	with open(text_file, "r") as f:
		for line in f:
			lines.append(line.strip())
	return lines

def get_url_hashes(url_list):
	return [hashhex(url) for url in url_list]


def hashhex(s):
	"""Returns a heximal formated SHA1 hash of the input string."""
	h = hashlib.sha1()
	h.update(s.encode())
	return h.hexdigest()

def fix_missing_period(line):
	"""Adds a period to a line that is missing a period"""
	if "@highlight" in line: return line
	if line=="": return line
	if line[-1] in END_TOKENS: return line
	# print line[-1]
	return line + " ."

def get_art_abs(story_file):
	lines = read_text_file(story_file)

	# Lowercase everything
	lines = [line.lower() for line in lines]

	# Put periods on the ends of lines that are missing them (this is a problem in the dataset because many image captions don't end in periods; consequently they end up in the body of the article as run-on sentences)
	lines = [fix_missing_period(line) for line in lines]

	# Separate out article and abstract sentences
	article_lines = []
	highlights = []
	next_is_highlight = False
	for idx,line in enumerate(lines):
		if line == "":
			continue # empty line
		elif line.startswith("@highlight"):
			next_is_highlight = True
		elif next_is_highlight:
			highlights.append(line)
		else:
			article_lines.append(line)

	return article_lines, highlights


def write_to_jsonl(url_file, out_file):
	"""Reads the tokenized .story files corresponding to the urls listed in the url_file and writes them to a out_file."""
	print("Adding to the jsonl file for URLs listed in %s..." % url_file)
	url_list = read_text_file(url_file)
	url_hashes = get_url_hashes(url_list)
	story_fnames = [s+".story" for s in url_hashes]
	num_stories = len(story_fnames)


	with open(out_file, 'w') as writer:
		for idx,s in enumerate(story_fnames):
			if idx % 1000 == 0:
				print("Writing story %i of %i; %.2f percent done" % (idx, num_stories, float(idx)*100.0/float(num_stories)))

			# Look in the tokenized story dirs to find the .story file corresponding to this url
			if os.path.isfile(os.path.join(cnn_tokenized_stories_dir, s)):
				story_file = os.path.join(cnn_tokenized_stories_dir, s)
			elif os.path.isfile(os.path.join(dm_tokenized_stories_dir, s)):
				story_file = os.path.join(dm_tokenized_stories_dir, s)
			else:
				print("Error: Couldn't find tokenized story file %s in either tokenized story directories %s and %s. Was there an error during tokenization?" % (s, cnn_tokenized_stories_dir, dm_tokenized_stories_dir))
				# Check again if tokenized stories directories contain correct number of files
				print("Checking that the tokenized stories directories %s and %s contain correct number of files..." % (cnn_tokenized_stories_dir, dm_tokenized_stories_dir))
				check_num_stories(cnn_tokenized_stories_dir, num_expected_cnn_stories)
				check_num_stories(dm_tokenized_stories_dir, num_expected_dm_stories)
				raise Exception("Tokenized stories directories %s and %s contain correct number of files but story file %s found in neither." % (cnn_tokenized_stories_dir, dm_tokenized_stories_dir, s))

			# Get the strings to write to .bin file
			article, abstract = get_art_abs(story_file)
			tmp_jsonl = {"article_lines": article, "summary_lines": abstract}
			writer.write(str(tmp_jsonl)+'\n')

	print("Finished writing file %s\n" % out_file)


def check_num_stories(stories_dir, num_expected):
	num_stories = len(os.listdir(stories_dir))
	if num_stories != num_expected:
		raise Exception("stories directory %s contains %i files but should contain %i" % (stories_dir, num_stories, num_expected))

if __name__ == '__main__':
	if len(sys.argv) == 1:
		print("Using default CNN-DailyMail directories ...")
		cnndm_root_dir = '../cnn-dailymail/cnn-dailymail-master'
		cnn_tokenized_stories_dir = os.path.join(cnndm_root_dir, 'cnn_stories_tokenized')
		dm_tokenized_stories_dir = os.path.join(cnndm_root_dir, 'dm_stories_tokenized')
	elif len(sys.argv) == 4:
		cnndm_root_dir = sys.argv[1]
		cnn_tokenized_stories_dir = sys.argv[2]
		dm_tokenized_stories_dir = sys.argv[3]
	else:
		print("USAGE: python datagen.py <cnndm_root_dir> <cnn_tokenized_stories_dir> <dailymail_tokenized_stories_dir>")
		sys.exit()


	# Check the stories directories contain the correct number of .story files
	check_num_stories(cnn_tokenized_stories_dir, num_expected_cnn_stories)
	check_num_stories(dm_tokenized_stories_dir, num_expected_dm_stories)


	# Read the tokenized stories, do a little postprocessing then write to jsonl files
	all_train_urls = os.path.join(cnndm_root_dir, all_train_urls)
	all_val_urls = os.path.join(cnndm_root_dir, all_val_urls)
	all_test_urls = os.path.join(cnndm_root_dir, all_test_urls)
	write_to_jsonl(all_test_urls, "test.jsonl")
	write_to_jsonl(all_val_urls, "val.jsonl")
	write_to_jsonl(all_train_urls, "train.jsonl")
	print('Done with all!')


	# hashed = hashhex('http://web.archive.org/web/20070830193806id_/http://www.cnn.com:80/2007/US/law/08/24/michael.vick/index.html?eref=time_us')
	# print(hashed)