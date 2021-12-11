import json
import os
import sys
from time import sleep
from typing import Union

from globals import DEBUG

if DEBUG:
    in_filename = ''
    out_filename = ''
else:
    in_filename = str(sys.argv[0]).strip()
    out_filename = str(sys.argv[1]).strip()

MAX_TRIES = 100
JSON_MAX_SIZE = 65536


def send_request_(request):
    dump = json.dumps(request)

    in_file_fd = os.open(in_filename, os.O_RDWR)
    os.write(in_file_fd, dump.encode())
    os.close(in_file_fd)
    print('Sent request')

    out_file_fd = os.open(out_filename, os.O_RDONLY)
    data = os.read(out_file_fd, JSON_MAX_SIZE).decode()
    os.close(out_file_fd)

    try:
        response = json.loads(data)
        print(f'Received response: {data[:50]}...')
        return response
    except json.decoder.JSONDecodeError as exc:
        print(f'Data: {data}')
        raise ValueError(f'Could not parse response: {exc}')


def send_request(request):
    def send_acknowledgement(result):
        # print('Sent acknowledgement: ', result)
        in_file_fd = os.open(in_filename, os.O_RDWR)
        os.write(in_file_fd, result.encode())
        os.close(in_file_fd)

    def recv_data():
        out_file_fd = os.open(out_filename, os.O_RDONLY)
        raw_data = b''
        data_piece = os.read(out_file_fd, JSON_MAX_SIZE)
        while data_piece:
            raw_data += data_piece
            data_piece = os.read(out_file_fd, JSON_MAX_SIZE)
        data = raw_data.decode()
        os.close(out_file_fd)

        try:
            response = json.loads(data)
            return response
        except json.decoder.JSONDecodeError as exc:
            send_acknowledgement("error")
            return None

    dump = json.dumps(request)

    in_file_fd = os.open(in_filename, os.O_RDWR)
    os.write(in_file_fd, dump.encode())
    os.close(in_file_fd)
    print('Sent request')

    result, attempt = None, 0
    while attempt <= MAX_TRIES:
        sleep(0.2)
        attempt += 1
        result = recv_data()
        if result is not None:
            send_acknowledgement("success")
            break

    out_file_fd = os.open(out_filename, os.O_RDONLY)
    acknowledgement_end = os.read(out_file_fd, JSON_MAX_SIZE).decode()
    os.close(out_file_fd)
    # print(f'Received acknowledgement response: {acknowledgement_end[:50]}...')

    if result is None:
        print(f'Could not receive response. Attempts tried: {attempt}')
    else:
        print(f'Received response from attempt #{attempt}, response: {str(result)[:50]}...')

    print('\n\n')

    return result


