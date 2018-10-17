import operator
from beem import Steem
from beem.price import Price
from beem.market import Market
from beem.account import Account
from datetime import datetime
from datetime import timedelta

########################################################################################################################
# Installation instructions for the VM!                                                                                #
# sudo apt-get install build-essential libssl-dev python-dev                                                           #
# sudo apt install python3-pip                                                                                         #
# sudo pip3 install -U beem                                                                                            #
########################################################################################################################


# User class which holds information for each user (delegator).
class User:
    def __init__(self, username=None, steem_payout=0, sbd_payout=0, amount_delegated=0, apr=0):
        self.username = username
        self.steem_payout = steem_payout
        self.sbd_payout = sbd_payout
        self.amount_delegated = amount_delegated
        self.apr = apr

    def update_username(self, username):
        self.username = username

    def update_steem_payout(self, steem_payout):
        self.steem_payout = steem_payout

    def update_sbd_payout(self, sbd_payout):
        self.sbd_payout = sbd_payout

    def update_amount_delegated(self, amount_delegated):
        self.amount_delegated = amount_delegated

    def update_apr(self, apr):
        self.apr = apr


# Converts given vests to an amount in STEEM.
def convert_VESTS_to_STEEM(vests):
    result = vests / 1000000 * spmv
    return float(result)


# Calculates the APR/ROI based on a given payout * 365 days.
def calculate_APR(steem_payout, sbd_payout, amount_delegated):
    if amount_delegated != 0:
        apr = round((float(sbd_payout) * float(steem_per_sbd) + float(steem_payout)) * 365 / float(amount_delegated) * 100, 2)
    else:
        apr = 0
    return apr


# Calculates the @hybridbot payment.
def calculate_hybridbot_payment():
    result = round(float(users['hybridbot'].sbd_payout) * float(steem_per_sbd) + float(users['hybridbot'].steem_payout), 3)
    return result


# USE ONLY IF YOU WANT TO PULL KEYS FROM KEYS.TXT (MUST BE IN THE SAME DIRECTORY AS THIS PYTHON FILE!)
def get_keys():
    with open('keys.txt', 'r') as f:
        keys = f.read().split()
    return keys


##########################################################
# Initialize STEEM blockchain connections and variables. #
##########################################################
# s = Steem(keys=['<PRIVATE_POSTING_KEY>', '<PRIVATE_ACTIVE_KEY>'])
s = Steem(keys=get_keys())
m = Market()
spmv = s.get_steem_per_mvest()
steem_per_sbd = str(m.ticker()['latest']).split()[0]
d = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
# td = d - timedelta(days=1) FOR TESTING PURPOSES
users = {}
chart = ''

# Check all @hybridbot transfers and if criteria is met, create a user and update the steem and sbd payout for user.
for h in Account('hybridbot').history(start=d, only_ops=['transfer']):
    if h['to'] != 'hybridbot' and '#' in h['memo']:
        if h['to'] not in users:
            users[h['to']] = User(username=h['to'])
        users[h['to']].update_username(h['to'])
        if 'STEEM' in h['amount']:
            steem = h['amount'].split()
            users[h['to']].update_steem_payout(steem[0])
        if 'SBD' in h['amount']:
            sbd = h['amount'].split()
            users[h['to']].update_sbd_payout(sbd[0])

# Update the amount delegated for each user.
for u in users:
    user_delegations = Account(u).get_vesting_delegations()
    for d in user_delegations:
        if d['delegatee'] == 'hybridbot' and users[u].amount_delegated is 0:
            vests = float(d['vesting_shares'].split()[0])
            users[u].update_amount_delegated(convert_VESTS_to_STEEM(vests))

# Create an HTML chart entry and fills in values for each user.
for u in (sorted(users.values(), key=operator.attrgetter('amount_delegated'), reverse=True)):
    if u.username != 'hybridbot':
        chart = chart + '<tr><td><a href="/@{0}">@{0}</a></td><td>{1}SP</td><td>{2}</td><td>{3}</td><td>{4:.2f}%</td></tr>'.format(u.username, int(u.amount_delegated), u.steem_payout, u.sbd_payout, calculate_APR(u.steem_payout, u.sbd_payout, u.amount_delegated))

# Create post information.
title = 'Hybridbot Testing - {0}'.format(datetime.today().strftime('%m/%d/%Y'))
body = '<center>![](https://cdn.steemitimages.com/DQmZiSNMCC1JG5H3rkLQWXV138yyaX3TWmVfXh37JugtYxD/image.png)</center' \
       '>\n\nWe want to thank each of our delegators for their support of @hybridbot. Delegators receive 95% of ' \
       'all bids that are sent to @hybridbot in accordance with the amount of delegation they have contributed. ' \
       'The remaining 5% is sent to @prizeportal to help support content creators on @dlive.\n\nToday, we\'ve been' \
       ' able to support @dlivecommunity with a payment of {0} STEEM while our delegators received ' \
       'the following payments:\n\n<table><thead><tr><th>Delegator</th><th>Amount ' \
       'Delegated</th><th>Steem Payout</th><th>SBD Payout</th><th>APR</th></tr></thead><tbody>{1}' \
       '</table>\n\n'.format(str(calculate_hybridbot_payment()), chart)
tags = ['promotion', 'test', 'bots', 'bidbot']

# Post the report so Patrick can get more delegators. :)
s.post(title=title, body=body, author='hybridbot', tags=tags)
