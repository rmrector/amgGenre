#!/usr/bin/python

#TODO: pick from artist discography

from mutagen.flac import FLAC
from mutagen.oggvorbis import OggVorbis
import gobject
import gtk
import os
import pygtk
import re
import sys
import urllib2
pygtk.require('2.0')

class AmgGenreGrabber:
	def __init__(self, path_list):
		self.single = "!Single"
		self.various_artists = "Various Artists"
		self.search_url = "http://www.allmusic.com/search/" # + 'album/' or 'artist/'
		self.info_url = "http://www.allmusic.com/" # + 'album/' or 'artist/'
		self.url_safe = ':(),!'

		self.count = -1
		self.close_dialog = False

		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.window.set_title("AMG Genre Grabber")
		self.window.set_default_size(450, 500)
		self.window.connect("delete_event", self.delete_event)
		self.window.set_border_width(5)

		self.init_gui()

		self.window.show_all()

		gobject.idle_add(self.get_search_list, path_list)

	def init_gui(self):
		box1 = gtk.VBox(False, 0)

		box2 = gtk.HBox(False, 0)
		self.count_label = gtk.Label()
		self.count_label.set_justify(gtk.JUSTIFY_LEFT)
		self.album_label = gtk.Label()
		self.album_label.set_justify(gtk.JUSTIFY_LEFT)
		self.album_label.set_line_wrap(True)

		box2.pack_start(self.count_label, False, False, 0)
		box2.pack_start(self.album_label, False, False, 5)

		box1.pack_start(box2, False, False, 5)

		scrolled_window = gtk.ScrolledWindow()
		scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		# Why won't this friggin' shadow go away?
		scrolled_window.set_shadow_type(gtk.SHADOW_NONE)
		scrolled_window.set_property ('shadow-type', gtk.SHADOW_NONE)

		self.liststore = gtk.ListStore(str, str)
		self.treeview = gtk.TreeView(self.liststore)
		self.treeview.set_model(self.liststore)
		self.treeview.connect("row-activated", self.row_activated)
		self.cell = gtk.CellRendererText()
		self.cell2 = gtk.CellRendererText()
		self.treeviewcolumn = gtk.TreeViewColumn("Name", self.cell, text=0)
		self.treeviewcolumn.set_resizable(True)
		self.treeviewcolumn.set_reorderable(True)
		self.treeviewcolumn2 = gtk.TreeViewColumn("URL", self.cell2, text=1)
		self.treeviewcolumn2.set_resizable(True)
		self.treeviewcolumn2.set_reorderable(True)
		self.treeview.append_column(self.treeviewcolumn)
		self.treeview.append_column(self.treeviewcolumn2)

		scrolled_window.add(self.treeview)

		box1.pack_start(scrolled_window, True, True, 0)

		button_box = gtk.HButtonBox()
		button_box.set_layout(gtk.BUTTONBOX_END)
		button_box.set_spacing(10)

		ok_button = gtk.Button("OK")
		ok_button.connect("clicked", self.ok_button_clicked)
		skip_button = gtk.Button("Skip")
		skip_button.connect("clicked", self.skip_button_clicked)
		cancel_button = gtk.Button("Cancel")
		cancel_button.connect("clicked", self.cancel_button_clicked)

		button_box.pack_end(cancel_button)
		button_box.pack_end(skip_button)
		button_box.pack_end(ok_button)

		box1.pack_start(button_box, False, False, 3)

		self.status_bar = gtk.Statusbar()
		self.status_bar.set_has_resize_grip(True)
		self.context_id = self.status_bar.get_context_id("Status Bar")

		box1.pack_start(self.status_bar, False, False, 0)

		self.window.add(box1)

	def get_search_list(self, path_list):
		self.search_list = []
		for path in path_list:
			if os.path.isdir(path):
				music_found = False
				for f in os.listdir(path):
					file_path = os.path.join(path, f)
					if os.path.isfile(file_path):
						if file_path.lower().endswith(".ogg") or file_path.lower().endswith(".flac"):
							if file_path.lower().endswith(".ogg"):
								audio = OggVorbis(file_path)
							elif file_path.lower().endswith(".flac"):
								audio = FLAC(file_path)
							self.search_list.append([path, audio["album"][0], audio["albumartist"][0], None])
							music_found = True
							break
				if not music_found:
					self.search_list.append([path, "", "", "does not contain ogg/flac files"])
			else:
				self.search_list.append([path, "", "", "is not a valid directory"])
		self.search_on_list()

	def search_on_list(self):
		self.count += 1
		try:
			self.count_label.set_text("%i/%i: " % (self.count + 1, len(self.search_list)))
			self.album_label.set_text(os.path.basename(self.search_list[self.count][0]))
			m = re.search(r'\(([p|r][0-9]+)\)', self.search_list[self.count][0])
			if not self.search_list[self.count][3] == None:
				message_dialog = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK)
				message_dialog.set_markup("<b>%s</b> %s." % (self.search_list[self.count][0], self.search_list[self.count][3]))
				message_dialog.run()
				message_dialog.destroy()
				self.search_on_list()
			elif m:
				self.status_bar.push(self.context_id, "Direct lookup found: " + m.group(1))
				if m.group(1)[0] == 'p':
					gobject.idle_add(self.grab_genre, "artist/" + m.group(1))
				elif m.group(1)[0] == 'r':
					gobject.idle_add(self.grab_genre, "album/" + m.group(1))
			else:
				self.status_bar.push(self.context_id, "Searching...")
				model = self.treeview.get_model()
				self.treeview.scroll_to_point(0, 0)
				model.clear()
				if self.search_list[self.count][1] == self.single:
					gobject.idle_add(self.search_artist(self.search_list[self.count][2]))
				else:
					gobject.idle_add(self.search_album, self.search_list[self.count][1], self.search_list[self.count][2])
				return True
		except IndexError:
			return False

	def search_artist(self, artist):
		self.treeviewcolumn.set_title("Artist")
		data = self.grab_url(self.search_url + "artist/" + urllib2.quote(artist.encode("utf-8"), safe=self.url_safe) + "/exact:0")
		model = self.treeview.get_model()
		self.treeview.scroll_to_point(0, 0)
		model.clear()
		artist_list = []
		for m in re.finditer(r'-(?P<link>p[0-9]+)">(?P<artist>.*?)</a></td>.*?<td>(?P<genre>.*?)</td>.*?<td>(?P<years>.*?)</td>', data, re.S):
			artist_list.append(["%s - %s (%s)" % (m.group("artist"), m.group("genre"), m.group("years")), 'artist/' + m.group("link")])
		artist_list = self.sort_album_list(artist_list, artist)
		for i in artist_list:
			model.append(i)
		self.treeviewcolumn.queue_resize()
		self.status_bar.pop(self.context_id)
		if len(artist_list) == 0:
			self.status_bar.push(self.context_id, "No artists found")
			gobject.timeout_add(2500, self.clear_status_bar)

	def search_album(self, album, artist):
		self.treeviewcolumn.set_title("Album")
		data = self.grab_url(self.search_url + "album/" + urllib2.quote(album.encode("utf-8"), safe=self.url_safe))
		model = self.treeview.get_model()
		album_list = []
		for m in re.finditer(r'-(?P<link>r[0-9]+)">(?P<album>.*?)</a></td>.*?<td>(?P<artist>.*?)</td>.*?<td>(?P<label>.*?)</td>.*?<td>(?P<year>\d\d\d\d)</td>', data, re.S):
			album_list.append(["%s - %s (%s)" % (m.group("artist"), m.group("album"), m.group("year")), 'album/' + m.group("link")])
		album_list = self.sort_album_list(album_list, artist)
		for i in album_list:
			model.append(i)
		if artist != self.various_artists:
			model.append(["Search on artist (%s)?" % artist, "search/artist"])
		self.treeviewcolumn.queue_resize()
		self.status_bar.pop(self.context_id)
		if len(album_list) == 0:
			self.status_bar.push(self.context_id, "No albums found")
			gobject.timeout_add(2500, self.clear_status_bar)

	def list_option(self):
		model, iter = self.treeview.get_selection().get_selected()
		if iter != None:
			name, url = model.get(iter, 0, 1)
			if name.startswith("Search on artist ("):
				self.status_bar.push(self.context_id, "Searching for artist...")
				gobject.idle_add(self.search_artist, self.search_list[self.count][2])
			else:
				self.status_bar.push(self.context_id, "Grabbing genres...")
				gobject.idle_add(self.grab_genre, url)
		else:
			self.status_bar.pop(self.context_id)
			self.status_bar.push(self.context_id, "Select an option")
			gobject.timeout_add(2500, self.clear_status_bar)

	def grab_genre(self, url):
		data = self.grab_url(self.info_url + url)
		genre_list = []
		for m in re.finditer(r'/explore/style/.*?-d[0-9]*">(?P<genre>.*?)</a>', data):
			genre_list.append(m.group('genre'))
		self.status_bar.pop(self.context_id)
		if len(genre_list) == 0:
			if url.find("artist") != -1:
				message_dialog = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK)
				message_dialog.set_markup("No genres found for artist <b>%s</b>, giving up." % self.search_list[self.count][2])
				message_dialog.run()
				message_dialog.destroy()
				self.status_bar.pop(self.context_id)
			else:
				message_dialog = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK)
				message_dialog.set_markup("No genres found for album <b>%s</b>, searching on artist <b>%s</b>." % (self.search_list[self.count][1], self.search_list[self.count][2]))
				message_dialog.run()
				message_dialog.destroy()
				self.status_bar.pop(self.context_id)
				self.status_bar.push(self.context_id, "Searching for artist...")
				gobject.idle_add(self.search_artist, self.search_list[self.count][2])
		else:
			task = self.set_genre(genre_list)
			self.status_bar.pop(self.context_id)
			gobject.idle_add(task.next)

	def clear_status_bar(self):
		self.status_bar.pop(self.context_id)
		return False

	def set_genre(self, genre_list):
		dialog = gtk.Dialog("Setting genres...", self.window, gtk.DIALOG_MODAL,
		                   (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT))
		dialog.connect("response", self.dialog_response)
		progress_bar = gtk.ProgressBar()
		progress_bar.set_size_request(300, -1)
		label = gtk.Label(", ".join(genre_list))
		label.set_line_wrap(True)
		label.set_padding(-1, 5)
		dialog.get_content_area().pack_start(label)
		dialog.get_content_area().pack_start(progress_bar)
		dialog.get_content_area().set_spacing(5)
		dialog.show_all()
		self.status_bar.push(self.context_id, "Setting genres...")
		file_list = []
		for f in os.listdir(self.search_list[self.count][0]):
			if f.lower().endswith(".ogg") or f.lower().endswith(".flac"):
				file_list.append(f)
		file_list.sort()

		count = 0
		for f in file_list:
			if f.lower().endswith(".ogg") or f.lower().endswith(".flac"):
				if self.close_dialog:
					self.close_dialog = False
					break
				count += 1
				progress_bar.set_text(f)
				progress_bar.set_fraction(float(count) / len(file_list))
				if f.lower().endswith(".ogg"):
					audio = OggVorbis(os.path.join(self.search_list[self.count][0], f))
				if f.lower().endswith(".flac"):
					audio = FLAC(os.path.join(self.search_list[self.count][0], f))
				audio['genre'] = genre_list
				audio.save()
				yield True
		self.status_bar.pop(self.context_id)
		dialog.destroy()
		if not self.search_on_list():
			gtk.main_quit()
		yield False

	def grab_url(self, url):
		r = 3
		while r > 0:
			try:
				u = urllib2.urlopen(url)
				d = u.read()
				d = re.sub('&amp;amp;', '&', d)
				d = re.sub('&amp;', '&', d)
				u.close()
				return d
			except Exception, e:
				print e
				r -= 1
		print url
		print "URL broken; dying"
		gtk.main_quit()

	def sort_album_list(self, list, artist):
		first_list = []
		second_list = []
		third_list = []
		for i in list[:]:
			if i[0].lower().startswith(artist.lower()):
				first_list.append(i)
				list.remove(i)
				continue
			if i[0].lower()[:3] == artist.lower()[:3]:
				second_list.append(i)
				list.remove(i)
				continue
			if i[0].lower()[0] == artist.lower()[0]:
				third_list.append(i)
				list.remove(i)
				continue
		first_list.extend(second_list)
		first_list.extend(third_list)
		first_list.extend(list)
		return first_list

	def delete_event(self, widget, event, data=None):
		gtk.main_quit()

	def ok_button_clicked(self, w):
		gobject.idle_add(self.list_option)

	def skip_button_clicked(self, w):
		if not self.search_on_list():
			gtk.main_quit()

	def cancel_button_clicked(self, w):
		gtk.main_quit()

	def row_activated(self, treeview, path, view_column):
		gobject.idle_add(self.list_option)

	def dialog_response(self, dialog, response):
		if response in [gtk.RESPONSE_REJECT.real, gtk.RESPONSE_DELETE_EVENT.real]:
			self.close_dialog = True
			dialog.destroy()

if __name__ == "__main__":
	if(len(sys.argv) > 1):
		AmgGenreGrabber(sys.argv[1:])
	else:
		print "Usage: amgGenre.py [DIRECTORY]..."
		sys.exit()
	gtk.main()
