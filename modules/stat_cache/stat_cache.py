import os
import sys
import shutil

from utils.utils import make_dirs, cache_data, restore_data 


class StatCache(object):
	
	def __init__(self, stat_cache_dir, backup_folder):
		self._stat_cache_dir = stat_cache_dir 	#str, abs path
		self._backup_folder = backup_folder 	#str, abs path

		#latest file backup
		self._latest_stat_cache_dir = os.path.join(stat_cache_dir, "latest")
		make_dirs(self._latest_stat_cache_dir)

		#newest file backup; compared to latest
		self._new_stat_cache_dir = os.path.join(stat_cache_dir, "new")
		make_dirs(self._new_stat_cache_dir)

		#root stat file
		self._root_stat = os.path.join(self._latest_stat_cache_dir,
			os.path.basename(self._backup_folder) + ".dir")

		self.initialized = True

		self.metadata = {
			"previous": {},
			"key": "",
			"new": {}
		}

	def getLocalPath(self, path):
		# return str(path.path).replace(self._backup_folder, "")[1:]	#drop the leading slash
		common = os.path.commonpath([path, self._backup_folder])
		localPath = str(os.path.abspath(path)).replace(common, "")[1:]	#drop the leading slash
		if localPath == "":
			return os.path.basename(self._backup_folder)
		return os.path.join(os.path.basename(self._backup_folder), localPath)

	def getSuffix(self, path):
		#directory stat files have the following name: <directory_name>.dir
		#file stat files have the following name: <file_name>.file
		if os.path.isdir(path):	#is a dir
			suffix = ".dir"
		else:				#is a file
			suffix = ".file"
		return suffix

	def recursive_file_check(self, path):
		modified = False

		localPath = self.getLocalPath(path)
		suffix = self.getSuffix(path)

		newStatPath = os.path.join(self._new_stat_cache_dir, localPath + suffix)
		latestStatPath = os.path.join(self._latest_stat_cache_dir, localPath + suffix)

		# print(os.path.basename(latestStatPath))

		if not os.path.isfile(latestStatPath):
			#stat file does not exist for path, so it must be new
			# print("DNE")
			modified = True
		#stat and write
		statResult = os.stat(path)
		cache_data(statResult, newStatPath)
		#compare to existing stat file, if it exists (not modified yet)
		if not modified and statResult.st_ctime != restore_data(latestStatPath).st_ctime:
			# print("DIFF TIME")
			# print(statResult.st_ctime)
			print(restore_data(latestStatPath))
			modified = True

		#if this is a directory, recursively check
		if os.path.isdir(path):
			for f in os.scandir(path):
				file_updated = self.recursive_file_check(f)
				if not modified and file_updated:
					modified = True
		return modified

	def is_backup_folder_modified(self):
		modified = False
		if not os.path.isfile(self._root_stat):	#first time executing
			modified = True	#should this be modified? data might not be in cloud yet
			# self.initialized = False
			self.recursive_file_check(self._backup_folder)
		else:
			# self.initialized = True
			modified = self.recursive_file_check(self._backup_folder)
		return modified

	def set_metadata(self, data):
		# TODO: load the metadata pulled from blockchain into here
		pass

	def update_new_cache(self):
		if self.initialized:	#we only want to update the latest with the new cache if new cache is present
			shutil.rmtree(self._latest_stat_cache_dir)
			shutil.move(self._new_stat_cache_dir, self._latest_stat_cache_dir)
