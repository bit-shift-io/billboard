# billboard
A simple python digital billboard signage application
- It will flip between images in a folder or network drive
- It will automatically switch to a UDP stream when it becomes active
- Configuration is simple at the top of the file

# running
To run manually
Create a folder in $Home/Slideshow/ with your images, then run.
./tool-billboard.py

# install
If you want to have this launch at startup
./tool-billboard.py -i

# remove/uninstall
If you want to remove from startup
./tool-billboard.py -r (or -u)

