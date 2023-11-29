import asyncio
import argparse
import re
import os
import time

from functions import download_file, read_urls_from_file, friendly_time

########################################
####    INPUT ARGUMENTS
########################################

# Create an ArgumentParser object
parser = argparse.ArgumentParser()

# Add mutually exclusive arguments to the parser
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('-u', '--url', type=str, help='URL of the file to download')
group.add_argument('-f', '--file', type=str, help='Path to the file containing URLs to download')
parser.add_argument('--tor', action='store_true', help='Route through Tor')


# Add remaining arguments
parser.add_argument('-o', '--output_dir', type=str, help='Local directory where the file should be saved', default=os.path.join(os.getcwd(), 'downloaded'))
parser.add_argument('-r', '--retry_delay', type=int, help='Number of seconds to wait before retrying a failed download attempt', default=5)

# Parse the arguments
args = parser.parse_args()

########################################
####    ARGUMENT VALIDATION
########################################

# Validate the URL
if args.url and not re.match(r'^https?://(?:[a-zA-Z0-9-_]+\.)+[a-zA-Z0-9-_]+(?::\d+)?(?:/[a-zA-Z0-9-_./?#%]*)?$', args.url):
    print('[ERROR] -- Please provide a valid URL in the format https://example.com')
    exit(1)

# Validate the output directory and create if non-existant
print(args.output_dir)
if args.output_dir:
    # If output directory exists as a directory
    if not os.path.isdir(args.output_dir):
        try:
            # Create directory
            os.makedirs(args.output_dir)
        except OSError as e:
            print(f'[ERROR] -- Could not create directory {args.output_dir}. Please provide a valid directory path.')
            exit(1)

# Validate the file containing URLs exists
if args.file and not os.path.isfile(args.file):
    print(f'[ERROR] -- Please provide a valid file path')
    exit(1)

# Record the start time of the download
download_start_time = time.time()    

# Record total data downloaded
total_data = 0

if args.file:

    # Download each URL from the file
    for line_number, url in enumerate(read_urls_from_file(args.file), start=1):

        # Validate the url
        if not re.match(r'^https?://(?:[a-zA-Z0-9-_]+\.)+[a-zA-Z0-9-_]+(?::\d+)?(?:/[a-zA-Z0-9-_./?#%]*)?$', url):
            print(f"[WARN] -- Invalid URL detected on line {line_number}, skipping...")
            continue

        # Download file
        asyncio.run(download_file(url, args.output_dir, args.retry_delay, args.tor))
else:
    # Download the specified URL
    asyncio.run(download_file(args.url, args.output_dir, args.retry_delay, args.tor))

# Track the end time
download_end_time = time.time()

# Calculate the total download time
total_time = download_end_time - download_start_time
#total_bandwidth = total_data / total_time

# Output the total download time and average bandwidth
print("")
print("------------------------------")
print("")
print("Total download time:", friendly_time(total_time))
#print("Average bandwidth:", friendly_bandwidth(friendly_bandwidth))