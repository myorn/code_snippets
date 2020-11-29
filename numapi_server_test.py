"""Testing numAPI."""
import requests
from random import randint


API_HOST = 'http://localhost:5555'
PROXY = {'http': 'http://192.168.0.3:8080'}


def test_ok_states():
    payload = {
        'fragment': '',
        'notfound': 'floor' if randint(1, 2) // 2 == 1 else 'ceil',
        'default': 'yes it is',
        'min': randint(1, 99),
        'max': randint(100, 1000),
        # im getting errors from numapi when it got a big number (>99987582)
        # or when it's random with min bigger than max
        # but only when notfound is floor, for example
        # /random?fragment=&notfound=floor&default=yes+it+is&min=43&max=-3
        # /2938740239874/date?fragment=&notfound=floor&default=yes+it+is&min=7&max=100
        # it looks kinda logical but
        # numapi response is "internal server error" :)
    }
    nums = 'random', 1, 2, -100, -1000000, 99987582
    txtargs = 'trivia', 'math', 'date', 'year'
    for x in nums:
        req_str = f'{API_HOST}/{x}'
        ok_check(requests.get(req_str, proxies=PROXY, params=payload))
        for y in txtargs:
            ok_check(requests.get(req_str + f'/{y}', proxies=PROXY, params=payload))

    ok_check(requests.get(f'{API_HOST}/{nums[4]}/{nums[5]}', proxies=PROXY, params=payload))
    ok_check(requests.get(f'{API_HOST}/{nums[4]}/{nums[5]}/date', proxies=PROXY, params=payload))

    print('ALL OK')


def test_not_ok_states():
    payload = {
        'fragment': '1234',
        'notfound': 'fleil',
        'min': 'hello',
        'max': 'its me',
    }

    nums = 'random', 1, 2, -100, -100000000, 2938740239874
    txtargs = 'trivia', 'math', 'date', 'year'
    for x in nums:
        not_ok_check(requests.get(f'{API_HOST}/random/{x}', proxies=PROXY))
        not_ok_check(requests.get(f'{API_HOST}/{x}/{x}/{x}', proxies=PROXY))
        for y in txtargs:
            not_ok_check(requests.get(f'{API_HOST}/{x}/{y}/date', proxies=PROXY))
    for y in txtargs:
        not_ok_check(requests.get(f'{API_HOST}/{y}', proxies=PROXY))
        not_ok_check(requests.get(f'{API_HOST}/{y}/{y}', proxies=PROXY))
        not_ok_check(requests.get(f'{API_HOST}/{y}/{y}/{y}', proxies=PROXY))

    for key in payload:
        not_ok_check(requests.get(f'{API_HOST}/{nums[1]}/{nums[2]}',
                              proxies=PROXY, params={key: payload[key]}))
    print('ALL (not)OK\n')


def ok_check(resp):
    print(resp.url)
    assert resp.status_code == 200
    assert resp.headers['Content-Type'] == 'application/json'
    body = resp.json()
    assert isinstance(body['text'], str)
    assert isinstance(body['number'], (int, str)) or body['number'] is None
    print('ok')


def not_ok_check(resp):
    print(resp.url)
    assert resp.status_code == 422
    assert resp.headers['Content-Type'] == 'application/json'
    body = resp.json()
    assert 'errors' in body
    print('ok')


test_ok_states()
test_not_ok_states()
print('FINISHED!')
