import json
import os
import sys
from typing import Union

from globals import DEBUG

if DEBUG:
    in_filename = ''
    out_filename = ''
else:
    in_filename = str(sys.argv[0]).strip()
    out_filename = str(sys.argv[1]).strip()

MAX_TRIES = 20


def send_request(request, tries=MAX_TRIES):
    print('Sent request')
    dump = json.dumps(request)

    in_file_fd = os.open(in_filename, os.O_RDWR)
    os.write(in_file_fd, dump.encode())
    os.close(in_file_fd)

    out_file_fd = os.open(out_filename, os.O_RDONLY)
    data = []
    piece_of_data = os.read(out_file_fd, 32768).decode()
    while piece_of_data:
        data.append(piece_of_data)
        piece_of_data = os.read(out_file_fd, 32768).decode()
    data = ''.join(data)
    os.close(out_file_fd)
    # print(data)
    try:
        response = json.loads(data)
        print('Received response')
        return response
    except json.decoder.JSONDecodeError as exc:
        print(f'Error parsing response: {exc}')
