import argparse
import random
import time

import networkx as nx

from server import ServerCaller


def track_network(api):
    server = api.call('ServerInfoInterface', 'getInfo', None)
    print(f'Logged in to {server["Body"]["worldName"]}')

    tracks = api.call('RailInterface', 'getForUser', data=[server['Infos']['activeUser']], short_call=1236)
    track_edges = [(track['FromId'], track['ToId']) for track in tracks['Body']]

    tracks_graph = nx.Graph()
    tracks_graph.add_edges_from(track_edges)
    print(f'Layed {len(track_edges)} tracks')
    return tracks_graph


def pp_per_rank(base, rank):
    return max(2, round(base * 0.8 ** (rank - 1)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Invest in all connected factories')
    parser.add_argument('session_id', help='The current PHPSESSID')
    parser.add_argument('--server', default='s1.railnation.de', help='The server where the session is active')
    parser.add_argument('--max_invest_count', default=2, type=int, help='Maximum of invest clicks per factory')
    parser.add_argument('--max_invest_costs', default=10000, type=int, help='Maximum costs for an individual invest')
    args = parser.parse_args()

    # let's go
    api = ServerCaller(args.server, args.session_id)
    tracks_graph = track_network(api)

    # factory properties
    factory_properties = api.properties('factories')
    factory_growth_properties = api.properties('factory_growth')
    factories = api.call('LocationInterface', 'getAllFactories', short_call=1236)['Body']

    factories = [factory for factory in factories if factory['Id'] in tracks_graph.nodes]
    print(f'Connected to {len(factories)} factories')

    # iterate over all connected factories
    for factory in factories:
        print(f"> Opening factory {factory['Id']}, money left: {api.money}")
        if factory['Level'] == 1:
            print('Skipping Level 1 factory')  # because we do not know yet how to detect unrevealed factories yet
            continue

        factory_details = api.call('LocationInterface', 'getFactoryDetails', [factory['Id']])['Body']
        invest_rank = api.call('LocationInterface', 'getInvestmentScreenRank', [factory['Id']])['Body']

        # gathering information
        outgoing_good = factory_details['StoragesInfo']['Outgoing'][0]
        current_pp = pp_per_rank(int(factory_properties[outgoing_good]['prestige']),
                                 int(invest_rank['UserPositionRank'] + 1)) \
            if invest_rank['UserPositionRank'] >= 0 else 0
        pagination_length = min(5, invest_rank['PlayerCount'])
        invest_screen = api.call('LocationInterface', 'getInvestmentScreen',
                                 [factory['Id'], outgoing_good, 0, pagination_length])['Body']

        invest_count = invest_screen['UserInvest']['InvestCount'] if invest_screen['UserInvest'] is not None else 0
        print(f"Currently on rank {invest_rank['UserPositionRank'] + 1} ({current_pp} PP) with {invest_count} invests")

        # start investing
        if invest_screen['CorpLosesMajority'] != '00000000-0000-0000-0000-000000000000':
            print('Skipping invest because of majority breach')
            continue

        if invest_count < args.max_invest_count:
            print(f"Investing for {invest_screen['Costs']}")
            if invest_screen['Costs'] > api.money or invest_screen['Costs'] > args.max_invest_costs:
                print("Not enough money or above invest limit")
                continue
            invest_count = api.call('LocationInterface', 'invest', [factory['Id']])['Body']
        time.sleep(random.randint(1, 3))
    print('-- Done --')
