import requests

headers = {"x-access-key": "ZqYGaV2KkBvX1DTrfJMwyaP92VRjOuaU","accept": "application/json"}
def get_followers(username, url):
    followers = {}
    followers_len = -1
    params = {"username":username}
    res = requests.get(url, headers=headers, params=params).json()
    print(res)
    return res

