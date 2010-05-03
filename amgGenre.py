#!/usr/bin/python

import sys, re, urllib2, os, unicodedata

from mutagen.oggvorbis import OggVorbis
from mutagen.flac import FLAC
from subprocess import Popen, PIPE
from itertools import chain

albumSearchURL= 'http://www.allmusic.com/cg/amg.dll?p=amg&opt1=2&sql='
artistSearchURL= 'http://www.allmusic.com/cg/amg.dll?p=amg&opt1=1&sql='
infoURL  = 'http://www.allmusic.com/cg/amg.dll?p=amg&'
urlSafeSearch = ':(),!'

def run_zenity(type, *args):
	return Popen(['zenity', type] + list(args), stdin=PIPE, stdout=PIPE)

def ZenityList(column_names, text=None, boolstyle=None, editable=False, 
							select_col=None, sep='|', data=[]):
	"""Present a list of items to select.

	This will raise a Zenity List Dialog populated with the colomns and rows 
	specified and return either the cell or row that was selected or None if 
	the user hit cancel.

	column_names - A tuple or list containing the names of the columns.
	title - The title of the dialog box.
	boolstyle - Whether the first columns should be a bool option ("checklist",
	            "radiolist") or None if it should be a text field.
	editable - True if the user can edit the cells.
	select_col - The column number of the selected cell to return or "ALL" to 
	             return the entire row.
	sep - Token to use as the row separator when parsing Zenity's return. 
	      Cells should not contain this token.
	data - A list or tuple of tuples that contain the cells in the row.  The 
	      size of the row's tuple must be equal to the number of columns."""

	args = []
	args.append('--width=500')
	args.append('--height=550')
	for column in column_names:
		args.append('--column=%s' % column)

	if text:
		args.append('--text=%s' % text)
	if boolstyle:
		if not (boolstyle == 'checklist' or boolstyle == 'radiolist'):
			raise ValueError('"%s" is not a proper boolean column style.' % boolstyle)
		args.append('--' + boolstyle)
	if editable:
		args.append('--editable')
	if select_col:
		args.append('--print-column=%s' % select_col)
	if sep != '|':
		args.append('--separator=%s' % sep)

	for datum in chain(*data):
		args.append(datum)

	p = run_zenity('--list', *args)

	if p.wait() == 0:
		return p.stdout.read().strip().split(sep)

def ZenityProgress(text='', percentage=0, auto_close=False, pulsate=False, title=''):
    """Show a progress dialog to the user.
    
    This will raise a Zenity Progress Dialog.  It returns a callback that 
    accepts two arguments.  The first is a numeric value of the percent 
    complete.  The second is a message about the progress.

    NOTE: This function sends the SIGHUP signal if the user hits the cancel 
          button.  You must connect to this signal if you do not want your 
          application to exit.
    
    text - The initial message about the progress.
    percentage - The initial percentage to set the progress bar to.
    auto_close - True if the dialog should close automatically if it reaches 
                 100%.
    pulsate - True is the status should pulsate instead of progress."""

    args = []
    args.append('--width=400')
    if title:
	    args.append('--title=%s' % title)
    if text:
      args.append('--text=%s' % text)
    if percentage:
      args.append('--percentage=%s' % percentage)
    if auto_close:
      args.append('--auto-close=%s' % auto_close)
    if pulsate:
      args.append('--pulsate=%s' % pulsate)

    #p = Popen(["zenity", '--progress'] + args, stdin=PIPE, stdout=PIPE)
    p = run_zenity('--progress', *args)

    def update(percent, message=''):
        if type(percent) == float:
            percent = int(percent * 100)
        p.stdin.write(str(percent) + '\n')
        if message:
            p.stdin.write('# %s\n' % message)
        return p.returncode

    return update, p

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
			update = None
			p = None
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
						title = re.sub('\xc6','AE', title)
						title = unicodedata.normalize('NFKD', title).encode('ASCII', 'ignore')
						title = re.sub('( \(.*\)$)', '', title)
						single = False
						if title == "!Single":
							single = True
						artist = audio["artist"][0]
						artist = re.sub('\xc6','AE', artist)
						artist = unicodedata.normalize('NFKD', artist).encode('ASCII', 'ignore')

						if not single:
							update, p = ZenityProgress(text = 'Looking for album... ' + title, auto_close = True, title = 'Setting genres...')
							data = grabby(albumSearchURL + urllib2.quote(title, safe=urlSafeSearch))
							searcharg = arg + " (" +re.findall(r'<span class="title">(?P<search>.*?)</span>', data)[0] + ")"
							searcharg = re.sub('&', '&amp;', searcharg)
							temp = re.findall(r'trlink".*?"cell">(?P<year>\d\d\d\d).*?word;">(?P<artist>.*?)</TD.*?(?P<link>sql=10:.*?)">(?P<title>.*?)</.*?-word;">(?P<label>.*?)</', data)
							optionlist = []
							for i in temp:
								optionlist.append((re.sub('"', '\\"', unicode(i[1] + " - " + i[3] + " (" + i[0] + ")", "iso-8859-1")), i[2]))
							if p.poll() == 1:
								sys.exit()
							selected = ZenityList(("Name", "URL"), searcharg, select_col = 2, data = optionlist)
							if not selected == None and not selected[0] == '':
								if p.poll() == 1:
									sys.exit()
								data = grabby(infoURL + selected[0])
								temp = re.findall(r'Styles Listing-->(?P<genre>.*?)--End Genre', data)
								if len(temp):
									genresList = re.findall('sql=.*?>(?P<genre>.*?)</a', unicode(temp[0], "iso-8859-1"))
								else:
									if p.poll() == 1:
										sys.exit()
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
				total = len(os.listdir(arg))
				count = 0
				genreslistsp = ''
				for g in genresList:
					if(len(genreslistsp) > 0):
						genreslistsp += ", "
					genreslistsp += "\"" + g + "\""
				for sf in os.listdir(arg):
					if p.poll() == 1:
						sys.exit()
					count += 1
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
							update(float(count) / total, str(count) + "/" + str(total) + ": " + audio['title'][0])
							#print "\"" + audio["title"][0] + "\" genre set to " + genreslistsp
				genresList = None

if __name__ == '__main__':
	main()

