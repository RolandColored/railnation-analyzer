import argparse
import random
import time

import networkx as nx

from server import ServerCaller


def verify_session(api):
    server = api.call('ServerInfoInterface', 'getInfo', None)
    print(f'Logged in to {server["Body"]["worldName"]}')
    return server['Infos']['activeUser']


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Collect all train spotters')
    parser.add_argument('session_id', help='The current PHPSESSID')
    parser.add_argument('--server', default='s1.railnation.de', help='The server where the session is active')
    args = parser.parse_args()

    # let's go
    api = ServerCaller(args.server, args.session_id)

    # train spotters
    spotters = api.call('TrainSpotterInterface', 'getWaitingAndCollected', short_call=1236)
    print(f'Found {len(spotters["Body"]["Waiting"]["TrainSpotter"])} train spotters')

    collected_spotters = list(
        api.bulk_call('TrainSpotterInterface', 'collect', spotters['Body']['Waiting']['TrainSpotter']))
    print(f'Collected {len(collected_spotters)} train spotters')

