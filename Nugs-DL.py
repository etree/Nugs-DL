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
from mutagen.flac import FLAC, Picture

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
	return json.loads(jsonf.rstrip()[21:-2])			
			
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
		
def fetchTrackUrl(trackId):
	trackUrlgetResp = session.get(f"https://streamapi.nugs.net/bigriver/subplayer.aspx?orgn=nndesktop&HLS=1&callback=angular.callbacks._h&platformID=1&trackID={trackId}")
	if trackUrlgetResp.status_code != 200:
		print(f"Failed to fetch track URL. Response from API: {trackUrlgetResp.text}")
		osCommands("p")
	else:		
		return cleanJson(trackUrlgetResp.text)["streamLink"]

def wrap(trackTitle, trackNum, trackTotal):
	def reporthook(blocknum, blocksize, totalsize):
		readsofar = blocknum * blocksize
		if totalsize > 0:
			percent = readsofar * 1e2 / totalsize
			l = f"Downloading track {trackNum} of {trackTotal}: {trackTitle} - 16-bit / 44.1 kHz FLAC"
			s = "\r%5.f%%" % (
			percent)
			sys.stderr.write(f"{l}{percent:5.0f}%\r")	
			if readsofar >= totalsize:
				sys.stderr.write("\n")
	return reporthook

def fetchTrack(trackUrl, trackTitle, trackNum, trackTotal):
	urllib.request.urlretrieve(trackUrl, f"{trackNum}.flac", wrap(trackTitle, trackNum, trackTotal))
	
def fetchMetadata(albumId):
	metadataGetResp = session.get(f"https://streamapi.nugs.net/api.aspx?orgn=nndesktop&callback=angular.callbacks._4&containerID={albumId}&method=catalog.container&nht=1", verify = False)
	return cleanJson(metadataGetResp.text)
	
def fetchAlbumCov(metaj):
	albumCovGetResp = requests.get(f"http://api.livedownloads.com{metaj['Response']['pics'][0]['url']}", verify = False)
	if albumCovGetResp.status_code != 200:
		print(f"Failed to fetch album cover. Response from API: {albumCovGetResp.text}")
		osCommands("p")
	else:
		if os.path.isfile("cover.jpg"):
			os.remove("cover.jpg")
		with open ("cover.jpg", "wb") as f:
			f.write(albumCovGetResp.content)
	
def writeFlacTags(file, albumArtist, albumTitle, trackTitle, trackNum, trackTotal):
	audio = FLAC(file)
	# write notes from nugs to notes.txt if avail?
	audio['albumartist'] = albumArtist
	audio['artist'] = albumArtist
	audio['album'] = albumTitle
	audio['title'] = trackTitle
	audio['tracknumber'] = str(trackNum)
	audio['tracktotal'] = str(trackTotal)
	audio.save()
	
def writeFlacAlbumCov(file):
	audio = File(file)
	image = Picture()
	image.type = 3
	mime = "image/jpeg"
	with open("cover.jpg", "rb") as f:
		image.data = f.read()
		audio.clear_pictures()
		audio.add_picture(image)
		audio.save()

def renameFiles(trackTitle, trackNum):
	if not str(trackNum).startswith("0"):
		if int(trackNum) < 10:
			finalFilename = f"0{trackNum}. {trackTitle}.flac"
		else:
			finalFilename = f"{trackNum}. {trackTitle}.flac"
	else:
		finalFilename = f"{trackNum}. {trackTitle}.flac"
	if GetOsType():
		finalFilename = re.sub(r'[\\/:*?"><|]', '-', finalFilename)
	else:
		finalFilename = re.sub('/', '-', finalFilename)
	if os.path.isfile(finalFilename):
		os.remove(finalFilename)
	os.rename(f"{trackNum}.flac", finalFilename)

def albumDirPrep(albumDir):
	if GetOsType():
		albumDir = re.sub(r'[\\/:*?"><|]', '-', albumDir)
	else:
		albumDir = re.sub('/', '-', albumDir)	
	if not os.path.isdir(albumDir):
		os.mkdir(albumDir)
	os.chdir(albumDir)
	
def main():
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
			albumTitle = metaj['Response']['containerInfo']
			print(f"{albumArtist} - {albumTitle}\n")
			albumDirPrep(f"{albumArtist} - {albumTitle}")
			trackTotal = len([x for x in metaj["Response"]["tracks"]])
			fetchAlbumCov(metaj)
			i = 0
			for item in [x for x in metaj["Response"]["tracks"]]:
				i += 1
				fetchTrack(fetchTrackUrl(item["trackID"]), item["songTitle"], i, trackTotal)
				writeFlacTags(f"{i}.flac", albumArtist, albumTitle, item["songTitle"], i, trackTotal)
				writeFlacAlbumCov(f"{i}.flac")
				renameFiles(item["songTitle"], i)
			os.remove("cover.jpg")
			os.chdir("..")
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
		email, pwd = config["email"], config["password"]
	login(email, pwd)
	fetchSubInfo()
	while True:
		main()
