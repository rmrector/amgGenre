amgGenre
========

I dislike coming up with genres for new music added to my library, and
Rock/Pop or Classical just doesn't give me the detail I would like; enter
AllMusic Styles.

A script that pulls Style information from [AllMusic](http://www.allmusic.com)
and sets them as the genre for music files.

This only works on Ogg Vorbis and FLAC files, and writes Vorbis tags.

Works on Linux; probably works wherever Python and pyGTK does (Windows, OSX).

Usage
-----

    amgGenre.py [DIRECTORY]...

No options, just one or more directories each containing one album.

Works well as a Nautilus script.

To force it to use a specific page from allmusic (artist or album), add the
`r123456` or `p123456` portion of the url for that page to the directory name,
inside parenthesis `(r123456)`. It will automatically apply Styles from that
page to the genre tag of all music files inside the directory.

Dependencies
------------
* [pyGTK](http://pygtk.org/)
* [Mutagen](http://code.google.com/p/mutagen/)
