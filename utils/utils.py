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


def send_request(request):
    dump = json.dumps(request)

    in_file_fd = os.open(in_filename, os.O_RDWR)
    os.write(in_file_fd, dump.encode())
    os.close(in_file_fd)

    out_file_fd = os.open(out_filename, os.O_RDONLY)
    data = os.read(out_file_fd, 32768)
    os.close(out_file_fd)
    try:
        response = json.loads(data.decode())
        return response
    except json.decoder.JSONDecodeError as exc:
        print(f'Failed to decode response: {exc}')
        print(f'Raw data: {data}')
