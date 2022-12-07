# GetYourBytes
A simply Python utility to download files over slow connections

## Key Features

- High performance downloads using urllib3 w/ asyncio
- Will resume partially completed downloads (where supported by the server)
- Is highly resilient to unstable connections
- Can accept a list of URLs from a file
- Live bandwidth monitoring
