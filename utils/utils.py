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


def send_request(request):
    def _send_request(_request):
        dump = json.dumps(_request)

        in_file_fd = os.open(in_filename, os.O_RDWR)
        os.write(in_file_fd, dump.encode())
        os.close(in_file_fd)

        out_file_fd = os.open(out_filename, os.O_RDONLY)
        data = os.read(out_file_fd, 32768).decode()
        os.close(out_file_fd)

        try:
            response = json.loads(data)
            return response
        except json.decoder.JSONDecodeError as exc:
            return None
    for attempt in range(1, MAX_TRIES+1):
        response = _send_request(request)

        if response is not None:
            print(f'Success from attempt #{attempt}')
            return response

    print(f'Failed to decode response')
