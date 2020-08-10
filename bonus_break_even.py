import argparse
from server import ServerCaller

from statistics import mean
from collections import defaultdict

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Calculate break-even for bonus workers')
    parser.add_argument('session_id', help='The current PHPSESSID')
    parser.add_argument('--server', default='s204.railnation.de', help='The server where the session is active')
    args = parser.parse_args()

    # let's go
    api = ServerCaller(args.server, args.session_id)

    # association analysis
    assoc_info = api.call('CorporationInterface', 'getOtherMemberBuildings',
                          ["00000000-0000-0000-0000-000000000000"])
    # 7: Hotel, 8: Restaurant, 9: Mall
    print(f"Info for {len(assoc_info['Body'])} members")

    buildings = {
        "7": api.properties('building_hotel', version='8984d44e15dc4d3481b18a42aa1969e6'),
        "8": api.properties('building_restaurant', version='8984d44e15dc4d3481b18a42aa1969e6'),
        "9": api.properties('building_mall', version='8984d44e15dc4d3481b18a42aa1969e6'),
    }

    all_balances = [int(value['moneyAmount']) for _, value in assoc_info['Body'].items()]
    print(f"Current mean balance of all members: {mean(all_balances):,.0f}")

    member_buildings = defaultdict(lambda: dict())

    for user_id, member in assoc_info['Body'].items():
        for key, value in member.items():
            if key in buildings:
                building = buildings[key]
                member_buildings[user_id][building['name']] = building['levels'][value['level']]['effect']

    all_restaurants = [float(value['Restaurant']['FARM']['MONEY']) * (float(member_buildings[user_id]['Hotel']['INCOME_BONUS']['MONEY']) / 100 + 1)
                       for user_id, value in member_buildings.items()]
    all_malls = [float(value['Mall']['FARM']['MONEY']) * (float(member_buildings[user_id]['Hotel']['INCOME_BONUS']['MONEY']) / 100 + 1)
                 for user_id, value in member_buildings.items()]
    all_hotels = [int(value['Hotel']['FARM']['PRESTIGE']) for _, value in member_buildings.items()]

    # daily income
    durations = {
        'Restaurant': 90,
        'Mall': 360,
        'Hotel': 180
    }

    restaurant_income = mean(all_restaurants) * (24 * 60 / durations['Restaurant'])
    mall_income = mean(all_malls) * (24 * 60 / durations['Mall'])
    total_income = restaurant_income + mall_income

    hotel_income = mean(all_hotels) * (24 * 60 / durations['Hotel'])
    print('- Regular -')
    print(f"Mean income per member per day: {total_income:,.0f}")
    print(f"Mean prestige per member per day: {hotel_income:,.0f}")

    # With bonus worker
    durations_worker = {k: v * 0.6 for k, v in durations.items()}

    restaurant_income = mean(all_restaurants) * (24 * 60 / durations_worker['Restaurant'])
    mall_income = mean(all_malls) * (24 * 60 / durations_worker['Mall'])
    total_income = restaurant_income + mall_income

    hotel_income = mean(all_hotels) * (24 * 60 / durations_worker['Hotel'])

    print('- With bonus worker -')
    print(f"Mean income per member per day: {total_income:,.0f}")
    print(f"Mean prestige per member per day: {hotel_income:,.0f}")

