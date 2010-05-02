#!/usr/bin/python

import sys, re, urllib2, os, unicodedata

from mutagen.oggvorbis import OggVorbis
from mutagen.flac import FLAC
from subprocess import Popen, PIPE

albumSearchURL= 'http://www.allmusic.com/cg/amg.dll?p=amg&opt1=2&sql='
artistSearchURL= 'http://www.allmusic.com/cg/amg.dll?p=amg&opt1=1&sql='
infoURL  = 'http://www.allmusic.com/cg/amg.dll?p=amg&'
urlSafeSearch = ':(),!'

def grabby(url):
	retry = 5
	while retry > 0:
		try:
			if retry < 5:
				print "Oops! Trying again. URL:", url
			else:
				print "URL:", url
			u = urllib2.urlopen(url)
			d = u.read()
			d = re.sub('&amp;amp;', '&', d)
			d = re.sub('&amp;', '&', d)
			u.close()
			return d
		except Exception, e:
			print e
			retry -= 1
	print "Retries exceeded, flailing gracefully"

def main():
	for arg in sys.argv[1:]:
		if os.path.isdir(arg):
			genresList = None
			for sf in os.listdir(arg):
				newpath = os.path.join(arg, sf)
				if os.path.isfile(newpath):
					if newpath.lower().endswith(".ogg") or newpath.lower().endswith(".flac"):
						audio = None
						if newpath.lower().endswith(".ogg"):
							audio = OggVorbis(newpath)
						if newpath.lower().endswith(".flac"):
							audio = FLAC(newpath)
						title = audio["album"][0]
						title = unicodedata.normalize('NFKD', title).encode('ASCII', 'ignore')
						title = re.sub('( \(.*\)$)', '', title)
						single = False
						if title == "!Single":
							single = True
						artist = audio["artist"][0]
						artist = unicodedata.normalize('NFKD', artist).encode('ASCII', 'ignore')

						if not single:
							data = grabby(albumSearchURL + urllib2.quote(title, safe=urlSafeSearch))
							searcharg = arg + " (" +re.findall(r'<span class="title">(?P<search>.*?)</span>', data)[0] + ")"
							searcharg = re.sub('&', '&amp;', searcharg)
							temp = re.findall(r'trlink".*?"cell">(?P<year>\d\d\d\d).*?word;">(?P<artist>.*?)</TD.*?(?P<link>sql=10:.*?)">(?P<title>.*?)</.*?-word;">(?P<label>.*?)</', data)
							optionlist = []
							for i in temp:
								optionlist.append((unicode(i[1] + " - " + i[3] + " (" + i[0] + ")", "iso-8859-1"), i[2]))
							optionlistsp = ""
							for n,u in optionlist:
								if(len(optionlistsp) > 0):
									optionlistsp += " "
								optionlistsp += "\"" + re.sub('"', '\\"', n) + "\" \"" + u + "\""
							pn = Popen('zenity --list --print-column=2 --text="%(title)s" --column="Name" \
							--column="URL" %(data)s --display=:0.0 --width=750 --height=500' 
							% {'title': searcharg, 'data': optionlistsp}, shell=True, stdout=PIPE)
							st = pn.communicate()[0]
							optionlist = []
							optionlistsp = ""
							chosen = repr(st)
							if(len(chosen) > 2):
								data = grabby(infoURL + chosen[1:-3])
								temp = re.findall(r'Styles Listing-->(?P<genre>.*?)--End Genre', data)
								if len(temp):
									print "Genres:"
									genresList = re.findall('sql=.*?>(?P<genre>.*?)</a', unicode(temp[0], "iso-8859-1"))
									for g in genresList:
										print g
								else:
									print "Grabbing artist Styles"
									temp = re.findall(r'(?P<artistlink>sql=11:[0-9a-z]*?)">', d)
									data = grabby(infoURL + temp[0])
									temp = re.findall(r'Style Listing-->(?P<genre>.*?)Style Listing--></tr>', data)
									if len(temp):
										print "Genres:"
										genresList = re.findall('sql=.*?>(?P<genre>.*?)</a', unicode(temp[0], "iso-8859-1"))
										for g in genresList:
											print g
									else:
										print "No genre! Completely boring music, apparently."
										#print "Grabbing artist Genre"
										#temp = re.findall(r'<!--Begin Genre Listing-->(?P<genre>.*?)<!--Genre Listing--><', d)
										#if len(temp):
										#	print "Genres:"
										#	genresList = re.findall('sql=.*?>(?P<genre>.*?)</a', temp[0])
										#	for g in genresList:
										#		print g
										#else:
										#	print "No genre! Completely boring music, apparently."
						else:
							data = grabby(artistSearchURL + urllib2.quote(artist, safe=urlSafeSearch))
							searcharg = arg[:-1] + " (" +re.findall(r'<span class="title">(?P<search>.*?)</span>', data)[0] + ")"
							searcharg = re.sub('&', '&amp;', searcharg)
							temp = re.findall(r'Style Listing-->(?P<genre>.*?)Style Listing--></tr>', data)
							if len(temp):
								print "Genres:"
								genresList = re.findall('sql=.*?>(?P<genre>.*?)</a', temp[0])
								for g in genresList:
									print g
							else:
								print "No genre! Completely boring music, apparently."
						break
			if not genresList == None:
				for sf in os.listdir(arg):
					newpath = os.path.join(arg, sf)
					if os.path.isfile(newpath):
						if newpath.lower().endswith(".ogg") or newpath.lower().endswith(".flac"):
							audio = None
							if newpath.lower().endswith(".ogg"):
								audio = OggVorbis(newpath)
							if newpath.lower().endswith(".flac"):
								audio = FLAC(newpath)
							audio["genre"] = genresList
							audio.save()
							genreslistsp = "["
							for g in genresList:
								if(len(genreslistsp) > 1):
									genreslistsp += ", "
								genreslistsp += "\"" + g + "\""
							genreslistsp += "]"
							print "\"" + audio["title"][0] + "\" genre set to " + genreslistsp
				genresList = None

if __name__ == '__main__':
	main()

