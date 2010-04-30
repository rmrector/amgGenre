import sys, re, urllib2

searchURL= 'http://www.allmusic.com/cg/amg.dll?p=amg&opt1=2&sql='
infoURL  = 'http://www.allmusic.com/cg/amg.dll?p=amg&'

title = 'Destination: Beautiful'
print "URL:", searchURL + urllib2.quote(title, safe=':')

try:
	u = urllib2.urlopen(searchURL + urllib2.quote(title, safe=':'))
	d = u.read()
	d = re.sub('&amp;amp;', '&', d)
	d = re.sub('&amp;', '&', d)
	print "Search:", re.findall(r'<span class="title">(?P<search>.*?)</span>', d)[0]
	temp = re.findall(r'trlink".*?"cell">(?P<year>\d\d\d\d).*?word;">(?P<artist>.*?)</TD.*?(?P<link>sql=10:.*?)">(?P<title>.*?)</.*?-word;">(?P<label>.*?)</', d)
	u.close()
	#for i in temp:
		#print i[1], "-", i[3], "(" + i[0] + ")"
	print temp[0][1], "-", temp[0][3], "(" + temp[0][0] + ")"
	newurl = infoURL + temp[0][2]
	print newurl
	u = urllib2.urlopen(newurl)
	d = u.read()
	d = re.sub('&amp;amp;', '&', d)
	d = re.sub('&amp;', '&', d)
	temp = re.findall(r'Genre Listing-->(?P<genre>.*?)--End Genre', d)
	#print temp
	genresList = re.findall('sql=.*?>(?P<genre>.*?)</a', temp[0])
	for g in genresList:
		print g

	
except Exception, e:
	print e

