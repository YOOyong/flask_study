import config
import pytest
import bcrypt
import json
from sqlalchemy import create_engine, text
from app import create_app



database = create_engine(config.test_config['DB_URL'], encoding='utf-8', max_overflow=0)

@pytest.fixture
def api():
    app = create_app(config.test_config)
    app.config['TEST'] = True
    api= app.test_client()

    return api

def setup_function():
    ##create a test user
    hashed_password = bcrypt.hashpw(
        b"test_password",
        bcrypt.gensalt()
    )
    new_users = [{
        'id' : 1,
        'name' : '유용준',
        'email' : 'phg5656@gmail.com',
        'profile' : 'test',
        'hashed_password': hashed_password
        },{
        'id' : 2,
        'name' : '이지은',
        'email' : 'test@gmail.com',
        'profile' : 'singer',
        'hashed_' : hashed_password
        }
    ]
    database.execute(text("""
        insert into users (
            id,
            name,
            email,
            profile,
            hashed_password
        ) values (
            :id,
            :name,
            :email,
            :profile,
            :hashed_password
        )
    """), new_users)

    ## user 2의 트윗 미리 생성해 두기
    database.execute(text("""
        insert into tweets (
            user_id,
            tweet
        ) values (
            2,
            "this is a test"
        )
    """))


def teardown_function():
    database.execute(text("set FOREIGN_KEY_CHECKS=0"))
    database.execute(text("truncate users"))
    database.execute(text("truncate tweets"))
    database.execute(text("truncate users_follow_list"))
    database.execute(text("set FOREIGN_KEY_CHECKS=1"))

def test_login(api):
    resp = api.post('/login',
                    data = json.dumps({
                        'email' : 'phg5656@gmail.com',
                        'password' : 'test password'
                    }),
                    content_type = 'application/json'
    )
    assert b"access_token" in resp.data

def test_unauthorized(api):
    #access token없을 때 404 리턴하는지 확인

    resp = api.post(
        '/tweet',
        data = json.dumps({'tweet' : 'hello'}),
        content_type = 'application/json'
    )

    assert resp.status_code == 401

    resp = api.post(
        '/follow',
        data = json.dumps({'follow' : 2}),
        content_type = 'application/json'
    )
    assert resp.status_code == 401

    resp = api.post(
        '/unfollow',
        data = json.dumps({'unfollow':2}),
        content_type = 'application/json'
    )
    assert resp.status_code == 401

def test_tweet(api):
    ## 로그인
    resp = api.post(
        '/login',
        data = json.dumps({'email': 'phg5656@gmail.com',
                           'password': 'test password'}),
        content_type = 'application/json'
    )

    resp_json = json.loads(resp.data.decode('utf-8'))
    access_token = resp.json['access_token']

    ## tweet
    resp = api.post(
        '/tweet',
        data = json.dumps({
            'tweet' : 'test tweet'
        }),
        content_type = 'application/json',
        headers = {'Authorization': access_token}
    )
    assert resp.status_code == 200

    ##tweet 확인

    resp = api.get(f'/timeline/1')
    tweets = json.loads(resp.data.decode('utf-8'))

    assert resp.status_code == 200

    assert tweets == {
        'user_id': 1,
        'timeline': [
            {
                'user_id':1,
                'tweet':'test tweet'
            }
        ]
    }

def test_follow(api):
    # 로그인
    resp = api.post(
        '/login',
        data = json.dumps({'email':'phg5656@gmail.com', 'password':'test password'}),
        content_type = 'application/json'
    )
    resp_json = json.loads(resp.data.decode('utf-8'))
    access_token = resp_json['access_code']

    ## 먼저 사용자의 1의 트윗을 확인해서 트윗 리스트가 빈걸 확인
    resp = api.get(f'/timeline/1')
    tweets = json.loads(resp.data.decode('utf-8'))
    assert resp.status_code == 200
    assert tweets =={
        'user_id':1,
        'timeline': []
    }

    # follow 사용자 아이디
    resp = api.post(
        '/follow',
        data = json.dumps({'follow': 2}),
        content_type = 'application/json',
        headers = {'Authorization':access_token}
    )
    assert resp.status_code == 200

    #이제 사용자 1의 트윗 확인해서 사용자 2의 트윗이 리턴 되는걸 확인
    resp = api.get(f'/timeline/1')
    tweets = json.loads(resp.data.decode('utf-8'))

    assert resp.status_code == 200
    assert tweets  == {
        'user_id' : 1,
        'timeline': [
            {
                'user_id' :2,
                'tweet' : "test tweet"
            }
        ]
    }

def test_unfollow(api):
    # 로그인
    resp = api.post(
        '/login',
        data=json.dumps({'email': 'phg5656@gmail.com', 'password': 'test password'}),
        content_type='application/json'
    )
    resp_json = json.loads(resp.data.decode('utf-8'))
    access_token = resp_json['access_code']

    # follow 사용자 아이디  =2
    resp = api.post(
        '/follow',
        data = json.dumps({'follow':2}),
        content_type = 'application/json',
        headers = {'Authorization' : access_token}

    )
    assert resp.status_code == 200

    # 이제 사용자 1의 트윗에서 사용자 2의 트윗이 리턴되는것을 확인
    resp = api.get(f'/timeline/1')
    tweets = json.loads(resp.data.decode('utf-8'))
    assert resp.status_code == 200
    assert tweets == {
        'user_id':1,
        'timeline': [
            {
                'user_id' : 2,
                'tweet' : 'test tweet'
            }
        ]
    }

    #unfollow 사용자 id = 2
    resp = api.post(
        '/unfollow',
        data = json.dumps({'unfollow':2}),
        content_type = 'application/json',
        headers = {'Authorization': access_token}
    )
    assert resp.status_code ==200

    ## 이제 사용자 1 의 트윗을 확인해 2 의 트윗이 나오지 않는걸 확인
    resp = api.get(f'/timeline/1')
    tweets = json.loads(resp.data.decode('utf-8'))

    assert resp.status_code == 200
    assert tweets == {
        'user_id' : 1,
        'timeline': []
    }