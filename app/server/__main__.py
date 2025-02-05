import json
from argparse import ArgumentParser
from socket import socket
from resolvers import resolve

import yaml

from protocol import validate_request, make_response

parser = ArgumentParser()
parser.add_argument(
    '-c', '--config', type=str,
    required=False, help='Sets config file path'
)

args = parser.parse_args()

default_config = {'host': 'localhost',
                  'port': 1080,
                  'buffersize': 1024
                  }

if args.config:
    with open(args.config) as file:
        config = yaml.load(file, Loader=yaml.Loader)
        default_config.update(default_config)

host, port = (default_config.get('host'), default_config.get('port'))

try:
    sock = socket()
    sock.bind((host, port))
    sock.listen(5)

    print('server was started with {}:{}'.format(default_config.get('host'), default_config.get('port')))

    while True:
        client, address = sock.accept()
        print('client was connected with {}:{}'.format(address[0], address[1]))
        b_request = client.recv(default_config.get('buffersize'))
        request = json.loads(b_request.decode())

        if validate_request(request):
            action_name = request.get('action')
            controller = resolve(action_name)
            if controller:
                try:
                    print('controller: {} resolved with request: {}'.format(action_name, request))
                    response = controller(request)
                except Exception as err:
                    print('controller: {} error: {}'.format(action_name, err))
                    response = make_response(request, 500, 'internal server error')
            else:
                print('controller: {} not found'.format(action_name))
                response = make_response(request, 404, 'action with name {} not supported'.format(action_name))
        else:
            print('controller wrong request: {}'.format(request))
            response = make_response(request, 400, 'wrong request format')

        client.send(json.dumps(response).encode())

        client.close()

except KeyboardInterrupt:
    print('server shutdown')
