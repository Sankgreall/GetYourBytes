# GetYourBytes
A simple Python utility to download files over slow connections

## Key Features

- Use over TOR to handle downloads from dark web pages
- High-performance downloads using urllib3 w/ asyncio
- Will resume partially completed downloads (where supported by the server)
- Highly resilient to unstable connections
- Can accept a list of URLs from a file
- Live bandwidth monitoring

## Dark Web Download Guide

Downloading content from dark web sites is tricky. There are many factors to consider, including the route you use to access the TOR network.

To ensure a faster connection, follow the steps below. Note, this will potentially open you up to attacks that could compromise your anonymity. As a rule of thumb, if you don't understand why, seek advice before attempting this.

1. `git clone https://github.com/hephaest0s/creatorrc`
2. `cd createtoorc`
3. `python -m pip install stem`
4. `python creatorrc.py --speetor`
5. `sudo cp ./tor_config.txt /etc/torrc`
6. `tor`

Once the Tor connection is established, run GetYourBytes as usual.
