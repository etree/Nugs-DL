#!/usr/bin/env python3

# standard
import os
import re
import sys
import json
import time
import urllib
import platform

# third party
import requests
from mutagen import File
from mutagen.mp4 import MP4
from mutagen.flac import FLAC

def GetOsType():
	osPlatform = platform.system()
	if osPlatform == 'Windows':
		return True
	else:
		return False

def osCommands(x):
	if x == "p":
		if GetOsType():
			os.system('pause')
		else:
			os.system("read -rsp $\"\"")
	elif x == "c":
		if GetOsType():
			os.system('cls')
		else:
			os.system("clear")
	else:
		if GetOsType():
			os.system('title Nugs-DL R1 (by Sorrow446)')
		else:
			sys.stdout.write("\x1b]2;Nugs-DL R1 (by Sorrow446)\x07")

def cleanJson(jsonf):
	try:
		return json.loads(jsonf.rstrip()[21:-2])
	except json.decoder.JSONDecodeError:
		return json.loads(jsonf.rstrip()[20:-2])
			
def login(email, pwd):
	loginGetReq = session.get(f"https://streamapi.nugs.net/secureapi.aspx?orgn=nndesktop&callback=angular.callbacks._3&method=user.site.login&pw={pwd}&username={email}")
	if loginGetReq.status_code != 200:
		print(f"Sign in failed. Response from API: {loginGetReq.text}")
		osCommands("p")
	elif "USER_NOT_FOUND" in loginGetReq.text:
		print("Sign in failed. Bad credentials.")
		osCommands("p")

def fetchSubInfo():
	subInfoGetReq = session.get("https://streamapi.nugs.net/secureapi.aspx?orgn=nndesktop&callback=angular.callbacks._0&method=user.site.getSubscriberInfo")
	if subInfoGetReq.status_code != 200:
		print(f"Failed to fetch sub info. Response from API: {subInfoGetReq.text}")
	elif not cleanJson(subInfoGetReq.text)['Response']:
		print("Failed to fetch sub info. Bad credentials.")	
		osCommands("p")
	else:
		print(f"Signed in successfully - {cleanJson(subInfoGetReq.text)['Response']['subscriptionInfo']['planName'][9:]} account\n")
		
def fetchTrackUrl(trackId, x):
	trackUrlgetResp = session.get(f"https://streamapi.nugs.net/bigriver/subplayer.aspx?orgn=nndesktop&HLS=1&callback=angular.callbacks._h&platformID={x}&trackID={trackId}")
	if trackUrlgetResp.status_code != 200:
		print(f"Failed to fetch track URL. Response from API: {trackUrlgetResp.text}")
		osCommands("p")
	else:
		return cleanJson(trackUrlgetResp.text)["streamLink"]

def wrap(trackTitle, trackNum, trackTotal, x):
	def reporthook(blocknum, blocksize, totalsize):
		if quality == "1":
			l = f"Downloading track {trackNum} of {trackTotal}: {trackTitle} - 16-bit / 44.1 kHz FLAC"
		elif quality == "2":
			l = f"Downloading track {trackNum} of {trackTotal}: {trackTitle} - ALAC"
		else:
			l = f"Downloading track {trackNum} of {trackTotal}: {trackTitle} - VBR L4 AAC"
		readsofar = blocknum * blocksize
		if totalsize > 0:
			percent = readsofar * 1e2 / totalsize
			s = "\r%5.f%%" % (
			percent)
			sys.stderr.write(f"{l}{percent:5.0f}%\r")	
			if readsofar >= totalsize:
				sys.stderr.write("\n")
	return reporthook

def fetchTrack(trackUrl, trackTitle, trackNum, trackTotal, fExt, x):
	# add error handling.
	urllib.request.urlretrieve(trackUrl, f"{trackNum}{fExt}", wrap(trackTitle, trackNum, trackTotal, x))
	
def fetchMetadata(albumId):
	metadataGetResp = session.get(f"https://streamapi.nugs.net/api.aspx?orgn=nndesktop&callback=angular.callbacks._4&containerID={albumId}&method=catalog.container&nht=1", verify = False)
	if metadataGetResp.status_code != 200:
		print(f"Failed to fetch metadata. Response from API: {metadataGetResp.text}")
		osCommands("p")
	else:
		return cleanJson(metadataGetResp.text)
	
def writeTags(file, albumTitle, trackNum, trackTotal):
	if file.endswith("c"):
		audio = FLAC(file)
		audio['album'] = albumTitle
		audio['tracktotal'] = str(trackTotal)
	else:
		audio = MP4(file)
		audio["\xa9alb"] = albumTitle
		audio["trkn"] = [(trackNum, trackTotal)]
	audio.save()

def renameFiles(trackTitle, trackNum, fExt):
	if not str(trackNum).startswith("0"):
		if int(trackNum) < 10:
			finalFilename = f"0{trackNum}. {trackTitle}{fExt}"
		else:
			finalFilename = f"{trackNum}. {trackTitle}{fExt}"
	else:
		finalFilename = f"{trackNum}. {trackTitle}{fExt}"
	if GetOsType():
		finalFilename = re.sub(r'[\\/:*?"><|]', '-', finalFilename)
	else:
		finalFilename = re.sub('/', '-', finalFilename)
	if os.path.isfile(finalFilename):
		os.remove(finalFilename)
	os.rename(f"{trackNum}{fExt}", finalFilename)

def albumDirPrep(albumDir):
	if GetOsType():
		albumDir = re.sub(r'[\\/:*?"><|]', '-', albumDir)
	else:
		albumDir = re.sub('/', '-', albumDir)
	if not os.path.isdir("Nugs-DL Downloads"):
		os.mkdir("Nugs-DL Downloads")
	os.chdir("Nugs-DL Downloads")
	if not os.path.isdir(albumDir):
		os.mkdir(albumDir)	
	os.chdir(albumDir)
	
def main(quality):
	url = input("Input Nugs URL: ")
	try:
		if not url.strip():
			osCommands("c")
			return
		elif url.split('/')[-2] != "recording":
			print("Invalid URL.")
			time.sleep(1)
			osCommands("c")
		else:
			osCommands("c")
			metaj = fetchMetadata(url.split('/')[-1])
			albumArtist = metaj["Response"]["artistName"]
			albumTitle = metaj['Response']['containerInfo'].rstrip()
			print(f"{albumArtist} - {albumTitle}\n")
			albumDirPrep(f"{albumArtist} - {albumTitle}")
			trackTotal = len([x for x in metaj["Response"]["tracks"]])
			if quality == "1":
				fExt = ".flac"
				x = "1"
			elif quality == "2":
				fExt = ".m4a"
				x = "0"
			else:
				fExt = ".m4a"
				x = ""
			i = 0
			for item in metaj["Response"]["tracks"]:
				i += 1
				fetchTrack(fetchTrackUrl(item["trackID"], x), item["songTitle"], i, trackTotal, fExt, x)
				writeTags(f"{i}{fExt}", albumTitle, i, trackTotal)
				renameFiles(item["songTitle"], i, fExt)
			os.remove("cover.jpg")
			os.chdir("....")
			print("Returning to URL input screen...")
			time.sleep(1)
			osCommands("c")
	except IndexError:
		print("Invalid URL.")
		time.sleep(1)
		osCommands("c")

if __name__ == '__main__':
	osCommands("t")
	session = requests.session()
	with open("config.json") as f:
		config = json.load(f)
		email, pwd, quality = config["email"], config["password"], config["quality"]
	login(email, pwd)
	fetchSubInfo()
	while True:
		main(quality)
