# photo_organizer
Browse through subdirectories to chain move/rename/delete photos

The goal of this tool is to solve the following problem:  
How do I do to give a meaning full name to thousands of picture without opening the next directory, open the photo, select "rename", enter the new name, save, ...  Also, when I work on bunch of photos organizing, I don't do anything else, so, full screen it is

State of the project:  
**!!!!! Verify the content of the Trash before emptying it, who knows... there could be bugs causing wrong files to be sent to trash !!!!!**  
Discovering photos in subdirectories, renaming and deleting photos works.

TODO:  
* Option to move photos to new directory / create new sub directory
* Replace photo with "deleted" icon after a photo is deleted
* Option to open photos with 3rd party app
* Filter photos (size, date, ...)
* Sort photos (date, name, ...)
* Send "commit" to a thread and provide visual feedback that commit was called
* Photo display size selector or automate display photo size with screen size
* Add keyboard shortcuts
* Improve look and ergonomy
* Error handling
* Tests
* Clean code (I'm not a developer, just writing this tool because I couldn't find existing one on the market)

Usage:  
At the current stage, if you don't know how to install a python package, the tool is not ready for you to use yet.
Once installed, run it with the "photo_organizer", select the directory where your photos are located and start renaming.  Don't forget to click "commit" before leaving the tool.

![Screenshot](screenshots/Screenshot1.png?raw=true "Screenshot")
