#!/bin/bash

# update yt-dlp
source venv/bin/activate && pip install --upgrade --pre "yt-dlp[default,curl-cffi]"

# update gallery-dl
venv/bin/python -m pip install -U --no-cache-dir --force-reinstall "git+https://github.com/mikf/gallery-dl.git@master"

# update pyrogtgfork
source venv/bin/activate && pip install --upgrade pyrotgfork
source venv/bin/activate && pip install --upgrade TgCrypto