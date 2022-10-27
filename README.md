# hdrdiff
View and compare HDR and floating point images

## Features
- Supports EXR and most other common image formats
- View single images or diff
- View individual channels
- Pan and zoom images
- Scale and offset brightness
- Display numeric pixel values

## Installation
- Clone the repo
- Create the virtual env: `PIPENV_VENV_IN_PROJECT=1 pipenv install`
- Symlink `run.sh` to a directory in your PATH

Note: uses PyQt5 by default, but that doesn't seem to be installable
on Mac (maybe only ARM?). The run script will switch to PyQt6 on Mac
so you'll need to install that manually in the virtualenv.
