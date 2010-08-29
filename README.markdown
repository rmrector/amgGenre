amgGenre
========

I dislike coming up with genres for new music added to my library, and Rock/Pop
or Rap or Classical just doesn't give me the detail I would like;
enter allmusic Styles.

A script that pulls Style information from [allmusic](http://www.allmusic.com)
and sets them as the genre for music files.

This script works on Ogg Vorbis and FLAC files, and writes Vorbis tags.

It uses zenity as the GUI, with a bit of help from
[PyZenity](http://www.brianramos.com/?page_id=110). See LICENSE for
license information.

Usage
-----

    ./amgGenre.py [DIRECTORY]...

No options, just one or more directories each containing one album.

Works well as a Nautilus script.

To force it to use a specific page from allmusic (artist or album), add the 
`sql=10:xxxxxxxxxxxx` portion of the url for that page to the directory name.
It will automatically apply Styles from that page to the genre tag of all music
files inside the directory.
