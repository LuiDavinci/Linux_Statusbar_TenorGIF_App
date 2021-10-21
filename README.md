# Statusbar-TenorGIF App for Linux

A quick and dirty QT Statusbar implementation for grabbing GIFs from Tenor, since there is no offical one and I didnt find an unofficial one. 
This was intended for use under Linux, however it was also functional enough on MacOS. 

----------------
### Quick Demo:

![Quick Demo](quick_demo.gif)
The Application might look different depending on what graphical desktop environment you have installed. I have KDE and the theme used during this GIF-Recording was [this](https://store.kde.org/p/1415021/) one made by [yeyushengfan258](https://github.com/yeyushengfan258).

----------------

### Features:

* Search GIFs from Tenor (Sorted either by Ranked or Random) *Default: Ranked* 
* Autocomplete Searchterms
* Show Trending GIFS
* Show Trending Search Terms
* Saves Configuration of Column Count and Hide Preference in *app/settings.json*
* Global Shortcut to reopen Window even if hidden or minimized. 
*Default Shortcut: **Ctrl + Shift + G** customizable through app/settings.json*
* Copy GIF Link by clicking on GIF (works on some Applications e.g Discord) 
* Save GIF by right-clicking on GIF
* Closing Application completely either with Ctrl+Q, use Quit in Menubar or by right-clicking Statusbar Icon.
----------------


### Install:
First go get yourself a free API-Key from [here](https://tenor.com/developer/keyregistration).

Then clone the project:
```bash
> git clone https://github.com/LuiDavinci/Linux_Statusbar_TenorGIF_App.git
```
Now open **app/\_\_init\_\_.py** with any editor and swap out _YOURAPIKEYHERE_ with your newly attained API-Key.

You can now navigate back to the project root **Linux_Statusbar_TenorGIF_App/**

##### The Plain Python Way
Make sure to have at least Python 3.8 (It's been tested with 3.9 as well)

```bash
> python3.8 -m pip install -r requirements.txt
```
After that's done you simply start the App
```bash
> python3.8 main.py
```
Done!

##### The Conda Way (Recommended)
Make sure you have [Conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/linux.html) installed. Then in your terminal you do:
```bash
> conda create --name WhateverNameYouWant python=3.8
```
Finish the creation and afterwards do:
```bash
> conda activate WhateverNameYouWant
> pip install -r requirements.txt
> python main.py
```
Done!

----------------

### Disclaimer:

The reason this app was created was simply because I was too lazy to visit [Tenor](https://tenor.com/) everytime I wanted a GIF. That means this is indeed a **quick and dirty implementation** with **no focus on elegant, smart or performant code**. I also doubt any updates will be coming. However feel free to use pull-request or the issue tab.