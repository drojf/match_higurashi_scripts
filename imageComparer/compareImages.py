import os
import json
import platform
import re
import subprocess

import traceback
import threading
import csv

import http.server as server
from http.server import HTTPServer
import urllib.parse as urlparse
from tkinter import Tk
from tkinter import filedialog

from typing import List, Optional, Dict

collapseWhiteSpaceRegex = re.compile(r"[\s\b]+")

class SpriteMatchResult:
	def __init__(self, csvRow):
		"""

		:param csvRow: a csvRow object from a csv.reader
		"""
		self.ps3_script = csvRow[0]
		self.ps3_filename = os.path.basename(csvRow[1])
		self.ryukishi_filename = csvRow[2]

		#TODO: remove this when creating the CSV, not here!
		self.ryukishi_filename = self.ryukishi_filename.strip()
		self.ps3_filename = self.ps3_filename.rstrip('_')

	def __repr__(self):
		return f'{self.ps3_filename} -> {self.ryukishi_filename}'

	def asArray(self):
		return [self.ps3_script, self.ps3_filename, self.ryukishi_filename]

class ImageComparison:
	def __init__(self, sprite_match_reults : List[SpriteMatchResult], ps3_filename_to_filepath_map, ryukishi_filename_to_filepath_map):
		self.sprite_match_reults = sprite_match_reults
		self.ps3_filename_to_filepath_map = ps3_filename_to_filepath_map
		self.ryukishi_filename_to_filepath_map = ryukishi_filename_to_filepath_map

	def getRowAndBestMatches(self, rowIndex):
		row = self.sprite_match_reults[rowIndex]
		ps3_filepath = self.ps3_filename_to_filepath_map.get(row.ps3_filename.lower(), f'FILE LOOKUP FAILED ON [{row.ps3_filename}] (lookup name is {row.ps3_filename.lower()})')
		ryukishi_filepath = self.ryukishi_filename_to_filepath_map.get(row.ryukishi_filename.lower(), f'FILE_LOOKUP_FAILED_FOR [{row.ryukishi_filename}] (lookup name is {row.ryukishi_filename.lower()})')
		return row, ps3_filepath, ryukishi_filepath

	def getNumRows(self):
		return len(self.sprite_match_reults)

class Globals:
	# Define constants used throughout the script. Use function calls to enforce variables as const
	IS_WINDOWS = platform.system() == "Windows"
	IS_LINUX = platform.system() == "Linux"
	IS_MAC = platform.system() == "Darwin"

def trySystemOpen(path, normalizePath=False):
	"""
	Tries to open a given path using the system 'open' function
	The path can be a on-disk folder or a URL
	NOTE: this function call does not block! (uses subprocess.Popen)
	NOTE: paths won't open properly on windows if they contain backslashes. Set 'normalizePath' to handle this problem.
	:param path: the path to show
	:return: true if successful, false otherwise
	"""
	try:
		if normalizePath:
			path = os.path.normpath(path)

		if Globals.IS_WINDOWS:
			return subprocess.Popen(["explorer", path]) == 0
		elif Globals.IS_MAC:
			return subprocess.Popen(["open", path]) == 0
		else:
			return subprocess.Popen(["xdg-open", path]) == 0
	except:
		return False

def _makeJSONResponse(responseType, responseDataJson):
	# type: (str, object) -> str
	return json.dumps({
		'responseType': responseType,
		'responseData': responseDataJson,
	})


def _decodeJSONRequest(jsonString):
	# type: (str) -> (str, object)
	json_compatible_dict = json.loads(jsonString)
	return (json_compatible_dict['requestType'], json_compatible_dict['requestData'])

def start_server(working_directory, post_handlers, serverStartedCallback=lambda _: None):
	# type: (str, dict, function) -> None
	"""
	Starts a http server which handles POST requests with callbacks by the given 'post_handlers' argument.

	:param working_directory: the directory to serve files from
	:param post_handlers:
		post_handlers is a dictionary of { str : function }
		the string represents the 'path/url' that the post request was sent to
		the function represents the action to take when the post request with the specified 'path/url' is received:
		- the fn takes one argument, which is the data/body of the post request, as a UTF-8 string
		- the fn should return the response in the form of a UTF-8 string

	:return: None
	:exception: see serve_forever() of the SimpleHTTPRequestHandler class. In particular, if you try to run two
				instances of this server on the same computer, you will get a:
				"OSError: [WinError 10048] Only one usage of each socket address is normally permitted"
	"""
	class CustomHandler(server.SimpleHTTPRequestHandler):
		"""
		This class inherits from SimpleHTTPRequestHandler. It acts as a webserver, which serves the files in the
		working_directory variable captured from the outer scope. On POST requests, it executes the
		function in the post_handlers dict corresponding to the POST address. The following changes were also made:
		- The subdirectory working_directory is served, instead of the current working directory
		- Trying to list a directory gives a 404 instead
		- All returned files have caching disabled
		- If an exception occurs while handling a request, the exception is passed to the browser
		"""
		def list_directory(self, path):
			""" This override function always returns a 404 when a directory listing is requested """
			self.send_error(404, "No permission to list directory")
			return None

		def send_head(self):
			"""
			Copy and pasted from  SimpleHTTPRequestHandler class because it's difficult
			to alter the headers without modifying the function directly

			Common code for GET and HEAD commands.

			This sends the response code and MIME headers.

			Return value is either a file object (which has to be copied
			to the outputfile by the caller unless the command was HEAD,
			and must be closed by the caller under all circumstances), or
			None, in which case the caller has nothing further to do.

			"""
			originalPath = self.translate_path(self.path)
			# --------- THE FOLLOWING WAS ADDED ---------
			# Python 3 has the ability to change web directory built-in, but Python 2 does not.
			relativePath = os.path.relpath(originalPath, os.getcwd())
			path = os.path.join(working_directory, relativePath) # working_directory is captured from outer scope!
			print(f"requested {self.path}, will send {path}")
			# --------- END ADDED SECTION ---------
			f = None
			if os.path.isdir(path):
				parts = urlparse.urlsplit(self.path)
				if not parts.path.endswith('/'):
					# redirect browser - doing basically what apache does
					self.send_response(301)
					new_parts = (parts[0], parts[1], parts[2] + '/',
					             parts[3], parts[4])
					new_url = urlparse.urlunsplit(new_parts)
					self.send_header("Location", new_url)
					self.end_headers()
					return None
				for index in "index.html", "index.htm":
					index = os.path.join(path, index)
					if os.path.exists(index):
						path = index
						break
				else:
					return self.list_directory(path)
			ctype = self.guess_type(path)
			try:
				# Always read in binary mode. Opening files in text mode may cause
				# newline translations, making the actual size of the content
				# transmitted *less* than the content-length!
				f = open(path, 'rb')
			except IOError:
				self.send_error(404, "File not found")
				print(f"ERROR: {path} not found!")
				return None
			try:
				self.send_response(200)
				self.send_header("Content-type", ctype)
				fs = os.fstat(f.fileno())
				self.send_header("Content-Length", str(fs[6]))
				self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
				# --------- THE FOLLOWING WAS ADDED ---------
				self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
				self.send_header('Pragma', 'no-cache')
				self.send_header('Expires', '0')
				# --------- END ADDED SECTION ---------
				self.end_headers()
				return f
			except:
				f.close()
				raise

		# Suppress log requests - use own logging. Errors logged with "log_error" will still be printed.
		def log_request(self, code='-', size='-'):
			pass

		def do_POST(self):
			content_length = int(self.headers['Content-Length'])
			body_as_string = self.rfile.read(content_length).decode('utf-8')

			path_without_slash = self.path.lstrip('/')

			try:
				response_function = post_handlers[path_without_slash]
				try:
					response_string = response_function(body_as_string)
				except:
					errorMessage = traceback.format_exc()
					response = 'Exception @ POSTPath: [{}] Data: [{}]\n\n{}'.format(path_without_slash, body_as_string, errorMessage)
					response_string = _makeJSONResponse('error', response)
					traceback.print_exc()
			except KeyError:
				response = 'Error @ POSTPath: [{}] Data: [{}]'.format(path_without_slash, body_as_string)
				print(response)
				response_string = _makeJSONResponse('error', response)

			# TODO: decide to keep or remove caching. Leave in for development.
			# Add headers to prevent caching (of ALL files)
			# See: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control#Preventing_caching
			# Only 'Cache-Control' is required, but the other two aid in backwards compatibility
			self.send_response(200)
			self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
			self.send_header('Pragma', 'no-cache')
			self.send_header('Expires', '0')
			# For now, assume all data sent back is JSON
			self.send_header('Content-Type', 'application/json')
			self.end_headers()
			self.wfile.write(response_string.encode('utf-8'))

	# The default HTTPServer allows multiple servers on the same address without error
	# we would prefer for an error to be raised, so you know if you had multiple copies of the installer open at once
	class HTTPServerNoReuse(HTTPServer):
		allow_reuse_address = 0

	# This program is only intended to be used on a loopback (non-public facing) interface.
	# Do not modify the INTERFACE_IP variable.
	# Using Port '0' lets the OS choose an unused port
	httpd = HTTPServerNoReuse(("127.0.0.1", 0), CustomHandler)

	# note: calling the http server constructor will immediately start listening for connections,
	# however it won't give a response until "serve_forever()" is called. This allows running the
	# serverStartedCallback() before we block by calling serve_forever()
	serverStartedCallback(httpd)
	httpd.serve_forever()

class InstallerGUIException(Exception):
	def __init__(self, errorReason):
		# type: (str) -> None
		self.errorReason = errorReason  # type: str

	def __str__(self):
		return self.errorReason

class InstallerGUI:
	def __init__(self, workingDirectory, image_comparison_load_function):
		"""
		:param allSubModList: a list of SubModConfigs derived from the json file (should contain ALL submods in the file)
		"""
		self.messageBuffer = []
		self.threadHandle = None # type: Optional[threading.Thread]
		self.selectedModName = None # type: Optional[str] # user sets this while navigating the website
		self.workingDirectory = workingDirectory
		self.currentRowIndex = 0

		self.image_comparison = None # type: ImageComparison
		def reload_csv():
			self.image_comparison = image_comparison_load_function() # type: ImageComparison

		self.reload_csv = reload_csv
		self.reload_csv()

		self.mapping = {}

		mapping_path = "mapping.txt"

		if os.path.exists(mapping_path):
			with open(mapping_path, 'r', encoding='utf-8') as mapping_file:
				for line in mapping_file:
					if len(line.strip()) > 0:
						lImage, rImage = line.strip().split("|||")
						self.mapping[lImage] = rImage

		self.mapping_file = open(mapping_path, 'a', encoding='utf-8')

	# An example of how this class can be used.
	def server_test(self):
		def handleInstallerData(body_string):
			# type: (str) -> str
			requestType, requestData = _decodeJSONRequest(body_string)
			if requestType != 'statusUpdate':
				print('Got Request [{}] Data [{}]\n'.format(requestType, requestData))

			def getRowAbsolute(requestData):
				self.currentRowIndex = int(requestData['index'])
				if self.currentRowIndex < 0:
					return None

				row, ps3_filepath, ryukishi_filepath = self.image_comparison.getRowAndBestMatches(self.currentRowIndex)

				fixed_ps3_filepath = ps3_filepath.replace('\\','/')
				fixed_ryukishi_filepath = ryukishi_filepath.replace('\\','/')
				mapped_val = self.mapping.get(fixed_ps3_filepath)

				already_matched =  mapped_val is not None and mapped_val == fixed_ryukishi_filepath

				retval = {
					'leftImage': fixed_ps3_filepath,
					'rightImage': fixed_ryukishi_filepath,
					'currentRow': row.asArray(),
					'currentRowIndex': self.currentRowIndex,
					'alreadyMatched': already_matched,
					'totalRows': self.image_comparison.getNumRows()
				}
				return retval

			def getNext(requestData):
				offset = requestData['offset']
				ind = (self.currentRowIndex + int(offset)) % self.image_comparison.getNumRows()
				return getRowAbsolute({'index': str(ind)})

			def getNextUnsaved(requetData):
				for i in range(0, self.image_comparison.getNumRows()):
					retRow = getRowAbsolute({'index': str(i)})
					if not retRow['alreadyMatched']:
						return retRow

				return None

			def reloadCSV(requestData):
				self.reload_csv()
				return {}

			def saveMapping(requestData):
				lImage = requestData["leftImage"]
				rImage = requestData["rightImage"]

				if not os.path.exists(lImage) or not os.path.exists(rImage):
					return None

				self.mapping[lImage] = rImage
				self.mapping_file.write(f'{lImage}|||{rImage}\n')
				self.mapping_file.flush()
				return {'status': 'OK'}

			def unknownRequestHandler(requestData):
				return 'Invalid request type [{}]. Should be one of [{}]'.format(requestType, requestTypeToRequestHandlers.items())

			requestTypeToRequestHandlers = {
				'getNext': getNext,
				'getRowAbsolute': getRowAbsolute,
				'saveMapping': saveMapping,
				'getNextUnsaved': getNextUnsaved,
				'reloadCSV': reloadCSV,
			}

			requestHandler = requestTypeToRequestHandlers.get(requestType, None)

			# Check for unknown request
			if not requestHandler:
				return _makeJSONResponse('unknownRequest', unknownRequestHandler(requestData))

			# Try and execute the request. If an exception is thrown, display the reason to the user on the web GUI
			try:
				responseDataJson = requestHandler(requestData)
			except Exception as exception:
				print('Exception Thrown handling request {}: {}'.format(requestType, exception))
				traceback.print_exc()
				return _makeJSONResponse('error', {
					'errorReason': 'Exception handling [{}] request: {}'.format(requestType, traceback.format_exc())
				})

			return _makeJSONResponse(responseType=requestType, responseDataJson=responseDataJson)

		# add handlers for each post URL here. currently only 'installer_data' is used.
		post_handlers = {
			'installer_data': handleInstallerData,
		}

		def on_server_started(web_server):
			web_server_url = 'http://{}:{}'.format(*web_server.server_address)
			trySystemOpen(web_server_url)
			print("Please open {} in your browser if it didn't open automatically".format(web_server_url))

		start_server(working_directory=self.workingDirectory,
		             post_handlers=post_handlers,
		             serverStartedCallback=on_server_started)

def normalizeFilenameAndRemoveExtension(path):
	name, ext = os.path.splitext(path)
	return name.lower()

# Todo: hopefully this method of stripping the facial expression part of the name is good enough
def normalizePS3PathToName(path):
	partially_normalized = normalizeFilenameAndRemoveExtension(path)
	return partially_normalized[:-2]

def buildFilenameFilepathMap(folder, pathFilterString, pathToNameFunction, warnDuplicates=False, excludeFilterString=None, allowedExtensions=(".png", ".jpg")):
	"""
	returns a dict of lowercaseFileNameNoExtension -> fullPathWithExtension
	pathFilterString must be a string which all expected paths would contain. For example 'StreamingAssets\CG\sprite\normal'
	:param folder:
	:param pathFilterString:
	:param extensionIncludingDot:
	:param warnDuplicates:
	:return:
	"""
	retDict = {}
	for root, dirs, files in os.walk(folder):
		for filename in files:
			if os.path.splitext(filename)[1].lower() in allowedExtensions:
				fullPath = os.path.join(root, filename)
				if pathFilterString is None or pathFilterString in fullPath:
					if excludeFilterString is None or excludeFilterString not in fullPath:
						normalizedName = pathToNameFunction(filename)
						existingPath = retDict.get(normalizedName)
						if existingPath:
							if warnDuplicates:
								print(f"WARNING: duplicate filename {filename} in {existingPath} -> {fullPath}")
						else:
							retDict[normalizedName] = fullPath

	return retDict

def readCSVAsSpriteMatches(csvFilePath):
	sprite_match_results: List[SpriteMatchResult] = []

	with open(csvFilePath, newline='') as csvfile:
		spamreader = csv.reader(csvfile)
		for i, row in enumerate(spamreader):
			if i == 0:
				print('CSV Headers (ignored): ' + ', '.join(row))
				continue

			print(', '.join(row))
			sprite_match_results.append(SpriteMatchResult(row))

	return sprite_match_results

def getBackgroundFilenameMap(warn_duplicate_images):
	# Load ps3 backgrounds
	ps3_filename_to_filepath_map = buildFilenameFilepathMap(folder=r'external\ps3',
															pathFilterString='background', # only allow backgrounds
															pathToNameFunction=normalizeFilenameAndRemoveExtension,
															warnDuplicates=warn_duplicate_images)

	# Load ryukishi backgrounds
	ryukishi_filename_to_filepath_map = buildFilenameFilepathMap(folder=r'external\ryukishi',
															pathFilterString=None,
															pathToNameFunction=normalizeFilenameAndRemoveExtension,
															warnDuplicates=warn_duplicate_images)

	return ps3_filename_to_filepath_map, ryukishi_filename_to_filepath_map

def getSpriteFilenameMap(warn_duplicate_images):
	# Load normal sprites only as first choice
	ps3_filename_to_filepath_map = buildFilenameFilepathMap(folder=r'external\ps3',
															pathFilterString=r'sprite\normal', #Only include the 'normal' sprites, not any other variants
															pathToNameFunction=normalizePS3PathToName,
															warnDuplicates=warn_duplicate_images)

	# Load all sprites, except portrait, as second choice
	ps3_filename_to_filepath_map_all_images = buildFilenameFilepathMap(folder=r'external\ps3',
															pathFilterString=None, #Only include the 'normal' sprites, not any other variants
															pathToNameFunction=normalizePS3PathToName,
															warnDuplicates=warn_duplicate_images,
															excludeFilterString=r'sprite\portrait')

	for ps3_filename, ps3_path in ps3_filename_to_filepath_map_all_images.items():
		if ps3_filename not in ps3_filename_to_filepath_map:
			ps3_filename_to_filepath_map[ps3_filename] = ps3_path

	# Load portrait sprites as third choice
	ps3_filename_to_filepath_map_portrait = buildFilenameFilepathMap(folder=r'external\ps3',
															pathFilterString=r'sprite\portrait', #Only include the 'normal' sprites, not any other variants
															pathToNameFunction=normalizePS3PathToName,
															warnDuplicates=warn_duplicate_images)

	for ps3_filename, ps3_path in ps3_filename_to_filepath_map_portrait.items():
		if ps3_filename not in ps3_filename_to_filepath_map:
			ps3_filename_to_filepath_map[ps3_filename] = ps3_path

	ryukishi_filename_to_filepath_map = buildFilenameFilepathMap(folder=r'external\ryukishi',
															pathFilterString=None,
															pathToNameFunction=normalizeFilenameAndRemoveExtension,
															warnDuplicates=warn_duplicate_images)

	return ps3_filename_to_filepath_map, ryukishi_filename_to_filepath_map

def loadImageComparisonObject(mode):
	################# CONFIG OPTIONS
	WARN_DUPLICATE_IMAGES = False
	################# END CONFIG OPTIONS

	if mode == "background":
		ps3_filename_to_filepath_map, ryukishi_filename_to_filepath_map = getBackgroundFilenameMap(WARN_DUPLICATE_IMAGES)
	else:
		ps3_filename_to_filepath_map, ryukishi_filename_to_filepath_map = getSpriteFilenameMap(WARN_DUPLICATE_IMAGES)

	matches = readCSVAsSpriteMatches(csvFilePath='noconsole_output.txt.csv')

	for match in matches:
		ps3_filepath = ps3_filename_to_filepath_map.get(match.ps3_filename)
		if ps3_filepath:
			print("got match at", ps3_filepath)
		else:
			print(f"no ps3 match found for {match}")

		ryukishi_filepath = ryukishi_filename_to_filepath_map.get(match.ryukishi_filename)
		if ryukishi_filepath:
			print("got match at", ryukishi_filepath)
		else:
			print(f"no ryukishi match found for {match}")

	image_comparison = ImageComparison(matches, ps3_filename_to_filepath_map, ryukishi_filename_to_filepath_map)
	return image_comparison

def startSpriteComparison():
	def loadObject():
		return loadImageComparisonObject(mode=None)

	gui = InstallerGUI(workingDirectory='.', image_comparison_load_function=loadObject)
	gui.server_test()

def startBackgroundComparison():
	def loadObject():
		return loadImageComparisonObject(mode="background")

	gui = InstallerGUI(workingDirectory='.', image_comparison_load_function=loadObject)
	gui.server_test()

if __name__ == '__main__':
	startSpriteComparison()
