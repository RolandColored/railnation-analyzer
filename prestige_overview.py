import argparse
import csv

from tqdm import tqdm

from server import ServerCaller
from time import sleep


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate prestige overview for association members')
    parser.add_argument('session_id', help='The current PHPSESSID')
    parser.add_argument('--server', default='s204.railnation.de', help='The server where the session is active')
    args = parser.parse_args()

    # let's go
    api = ServerCaller(args.server, args.session_id)

    # association analysis
    assoc_info = api.call('CorporationInterface', 'getOtherMemberBuildings',
                          ["00000000-0000-0000-0000-000000000000"])
    print(f"Info for {len(assoc_info['Body'])} members")

    # fetch all prestige details
    prestiges = {}
    for user_id, member in tqdm(assoc_info['Body'].items()):
        prestiges[user_id] = {}
        prestiges[user_id]['overview'] = api.call('BudgetInterface', 'getPrestigeHistoryDetails',
                          [user_id, 9])['Body']['balance']
        sleep(1)
        prestiges[user_id]['cities'] = api.call('BudgetInterface', 'getPrestigeHistoryDetails',
                          [user_id, 9, '0', '1'])['Body']['balance']
        sleep(1)
        prestiges[user_id]['landmarks'] = api.call('BudgetInterface', 'getPrestigeHistoryDetails',
                          [user_id, 9, '0', '2'])['Body']['balance']
        sleep(2)

    # fetch all profiles for the nick names
    user_ids = list(prestiges.keys())
    profiles = api.call('ProfileInterface', 'getVCard', [user_ids], short_call=1236)['Body']

    # prepare all city and landmarks for the csv header line
    cities = set(city['type'] for user_id, prestige in prestiges.items() for city in prestige['cities'] )
    landmarks = set(landmark['type'] for user_id, prestige in prestiges.items() for landmark in prestige['landmarks'] )

    with open('prestige.csv', 'w', newline='') as csvfile:
        fieldnames = ['member', 'transports', 'invests', 'trainstation', 'other', 'competition', 'medal', '-cities-'] + list(cities) + ['-landmarks-'] + list(landmarks)
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for user_id, prestige in prestiges.items():
            overview_dict = {
                'transports': [row for row in prestige['overview'] if row['type'] == '0'],
                 'invests': [row for row in prestige['overview'] if row['type'] == '3'],
                 'trainstation': [row for row in prestige['overview'] if row['type'] == '4'],
                 'other': [row for row in prestige['overview'] if row['type'] == '6'],
                 'competition': [row for row in prestige['overview'] if row['type'] == '7'],
                 'medal': [row for row in prestige['overview'] if row['type'] == '8'],
            }
            write_dict = {'member': profiles[user_id]['userName']}
            for key, value in overview_dict.items():
                if len(value) > 0:
                    write_dict[key] = value[0]['prestige']

            for row in prestige['cities']:
                write_dict[row['type']] = row['prestige']
            for row in prestige['landmarks']:
                write_dict[row['type']] = row['prestige']

            writer.writerow(write_dict)
