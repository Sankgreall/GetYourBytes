import os
import time
import json
from urllib.parse import urlparse
import urllib3
from urllib3.contrib.socks import SOCKSProxyManager
from tenacity import retry, stop_after_delay, wait_exponential

# How long should we keep polling a dead connection?
WAIT_TIME_IN_SECONDS = 3 * 24 * 3600 # 3 days
MAX_RETRY_DELAY_IN_SECONDS = 60 * 30 # 30 minutes

def read_urls_from_file(file_path):
    with open(file_path, 'r') as f:
        for line in f:
            yield line.strip()

def log_retry(retry_state):
    print(f"Retry attempt {retry_state.attempt_number}: Waiting {retry_state.next_action.sleep} seconds before next attempt.")

def friendly_time(total_time):
    # Calculate the total download time in minutes, seconds, and milliseconds
    minutes, seconds = divmod(total_time, 60)
    seconds, milliseconds = divmod(seconds, 1)

    # Format the total download time as a string
    total_time_str = f"{int(minutes)} minute"
    if minutes != 1:
        total_time_str += "s"
    if seconds > 0:
        total_time_str += f" {int(seconds)} second"
        if seconds != 1:
            total_time_str += "s"
    if milliseconds > 0:
        total_time_str += f" {int(milliseconds * 1000)} millisecond"
        if milliseconds != 1:
            total_time_str += "s"

    return total_time_str

def friendly_bandwidth(bandwidth_in_bytes):
    if bandwidth_in_bytes >= 1024**2:
        average_bandwidth_str = f"{bandwidth_in_bytes / 1024**2:.2f} MiB/s"
    else:
        average_bandwidth_str = f"{bandwidth_in_bytes / 1024:.2f} KiB/s"

    return average_bandwidth_str

def bytes_to_friendly_value(bytes_value):
    if bytes_value < 1024:
        return f"{bytes_value} bytes"
    elif bytes_value < 1024**2:
        return f"{bytes_value/1024:.2f} KB"
    elif bytes_value < 1024**3:
        return f"{bytes_value/1024**2:.2f} MB"
    else:
        return f"{bytes_value/1024**3:.2f} GB"

def generate_save_file_path(url, base_directory, header_filename=None):
    
    # Parse the URL to extract the path
    parsed_url = urlparse(url)
    path = parsed_url.path

    # Remove the leading slash to prevent absolute path creation
    if path.startswith('/'):
        path = path[1:]

    # Extract directory path and replace filename if header_filename is provided
    if header_filename:
        # Remove the last component (original filename) from the path
        directory_path = os.path.dirname(path)
        # Combine the directory path with the new filename
        path = os.path.join(directory_path, header_filename)

    # Generate the save path with folder structure
    save_path = os.path.join(base_directory, path)

    # Create directories if they don't exist
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    return save_path

@retry(
    stop=stop_after_delay(WAIT_TIME_IN_SECONDS), # Stop after a defined number of days
    wait=wait_exponential(multiplier=2, max=MAX_RETRY_DELAY_IN_SECONDS), # Exponential backoff 
    # before_sleep=before_sleep_print
)
async def download_file(url, output_dir, retry_delay, use_tor=False):

    if use_tor:
        http = SOCKSProxyManager('socks5h://localhost:9050/')
    
    else:
        # Create an HTTP client
        http = urllib3.PoolManager()

    # Set placeholder header variable
    headers = {}

    # Use the client to send a request to the server to obtain the response headers
    response_headers = http.request('HEAD', url)

    # If there a filename in the returned headers
    header_filename = None
    if 'Content-Disposition' in response_headers.headers:
        content_disposition = response_headers.headers['Content-Disposition']
        filename_index = content_disposition.find('filename=')
        if filename_index != -1:
            header_filename = content_disposition[filename_index+len('filename='):].strip('"')

    # Create the save_path
    save_path = generate_save_file_path(url, output_dir, header_filename=header_filename)

    # Get the file size from the response headers
    download_size = int(response_headers.headers.get('Content-Length', 0))

    # Check if the server supports partial content retrieval
    if 'Accept-Ranges' in response_headers.headers and response_headers.headers['Accept-Ranges'] == 'bytes':
        print(f"[INFO] -- Server supports partial content retrieval.")
        supports_partial_content = True

    else:
        print(f"[WARN] -- Server does not support partial content retrieval.")
        supports_partial_content = False

    # IF
    # - the server does not support partial content retrieval 
    # - file does not exist
    # - The server reported size is zero (bad header?)
    # THEN download the entire file
    if not supports_partial_content or not os.path.exists(save_path) or download_size == 0:
        # We must overwrite any existing file
        append_write = "wb"

        # Print the total file size
        print(f"[INFO] -- Downloading {url} to {save_path}")

    # If server supports partial content retrival and the file exists, resume download
    elif supports_partial_content and os.path.exists(save_path):
        # We must append data to the file
        append_write = "ab"

        # If the file already exists, get the current size of the file in bytes
        file_size = os.path.getsize(save_path)

        # Calculate the size of the content we need to download
        remainder_size = download_size - file_size

        print(f"[INFO] -- Resuming download from {url} to {save_path}")

        # If remainder size is defined and less than 0
        if remainder_size < 0:
            print(f"[ERROR] -- Remainder size is invalid {remainder_size}, exiting")
            return

        # If remainder size is defined and greater than or equal to 0
        elif remainder_size > 0:

            # Set the URL header to include the current size of the file
            # This will tell the server to resume the download from the point where it was interrupted
            headers = {"Range": f"Bytes={file_size}-"}

            print(f"[INFO] -- Downloading the remaining {bytes_to_friendly_value(remainder_size)}")

        # If remaining size is 0
        else:
            print(f"[INFO] -- File has already been downloaded.")
            return
        
    # Record the start time of the download
    download_start_time = time.time()

    # Open the file for writing using the urllib3 library
    with http.request('GET', url, preload_content=False, headers=headers) as response, open(save_path, append_write) as out_file:
        
        # Update download_size if we are resuming a download
        try:
            if remainder_size > 0:
                download_size = remainder_size
        except:
            pass

        total_data = 0
        # Read the response as a stream and output to file
        while True:
            data = response.read(1024)
            if not data:
                break
            out_file.write(data)
            total_data += len(data)

            # Calculate the current bandwidth
            elapsed_time = time.time() - download_start_time
            current_bandwidth = total_data / elapsed_time

            if download_size > 0:
                download_progress = (total_data / download_size) * 100
                print(f'\r[INFO] -- Download progress: {download_progress:.2f}% -- Bandwidth: {friendly_bandwidth(current_bandwidth)}', end='')
            else:
                print(f'\r[INFO] -- Unable to report on bandwidth. Server is reporting a file size of 0 bytes, which is wrong.', end='')
    

    # Print a message to indicate that the download is complete
    # Replace the above with this line
    print(f"\r[INFO] -- {url} downloaded successfully!")



