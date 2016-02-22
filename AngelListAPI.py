# Used to make requests to AngelList API https://angel.co/api/spec/search
class AngelAPI(object):
    def __init__(self):
        self.url_root = 'https://api.angel.co/1'
        self.access_token = None # must be set

    def request(self, route, parameters=None):
        url = self.url_root
        url += route
        url += '?'+parameters+'&' if parameters else '?'
        url += 'access_token='+self.access_token
        return requests.get(url).json()
    
    def paginated_request(self, route, parameters=None, verbose=False):
        initial_request = self.request(route, parameters)
        pages = initial_request['last_page']
        responses = [initial_request]
        for i in range(pages-1):
            i += 2
            if verbose:
                print 'Page', i, 'out of', pages
            parameters += '&page={0}'.format(i)
            tmp = self.request(route, parameters)
            responses.append(tmp)
        return responses

###########################
#       Begin script      #
###########################

import pandas as pd
import requests
al = AngelAPI()

# get all investors for a given city - DC in this case
dc_id = al.request('/search/slugs', 'query=washington-dc')['id']
dc_investors = al.paginated_request('/tags/{0}/users'.format(dc_id), 'investors=by_residence')
investors = pd.DataFrame(sum([i['users'] for i in dc_investors], []))

# filter for only the investors that have listed Twitter handles and where DC is the primary location
investors = investors.query('twitter_url != "" and twitter_url == twitter_url')
investors['primary_location'] = investors['locations'].map(lambda x: x[0]['display_name'])
investors = investors.query('primary_location=="Washington, DC"')

# get each investor's individual investment data, and filter for investors that have listed metrics on investments
dc_investor_data = []
for k, v in investors.id.iteritems():
    dc_investor_data.append(al.request('/users/{0}'.format(v), 'include_details=investor'))
investors_full = pd.DataFrame(dc_investor_data)
investors_full['avg_investment_amount'] = investors_full.investor_details.\
    map(lambda x: x['average_amount'] if x.has_key('average_amount') else '')
investors_full['invested_startups_per_year'] = investors_full.investor_details\
    .map(lambda x: x['startups_per_year'] if x.has_key('startups_per_year') else '')
active_investors = investors_full.query('avg_investment_amount=="" and invested_startups_per_year==""')

# parse out the Twitter handles and export to a file
twitter_handles = active_investors.twitter_url.map(lambda x: x.rsplit('/')[-1].replace('@','')).tolist()
with open('investors.txt', 'w') as file:
    for user in twitter_handles:
        file.write('@{}\n'.format(user))

###########################
#   Create Twitter list   #
###########################
'''
Install the [command-line power tool for Twitter](https://github.com/sferik/t)

Issue these commands:

t list create mylist
xargs t list add mylist < investors.txt
'''