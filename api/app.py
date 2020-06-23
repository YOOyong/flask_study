from flask import Flask , jsonify, request , current_app
from flask.json import JSONEncoder
from sqlalchemy import create_engine, text

class CustomJSONEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, set):
            return list(o)

        return JSONEncoder.default(self, o)

def get_user(user_id):
    user = current_app.database.execute(text(
        '''
        select 
            id,
            name,
            email,
            profile
        from users
        where id = :user_id'''
    ), {'user_id' : user_id}).fetchone()

    return {
        'id':user['id'],
        'name':user['name'],
        'email':user['email'],
        'profile':user['profile']
    } if user else None

def insert_user(user):
    return current_app.database.execute(text("""
    insert into users(
        name,
        email,
        profile,
        hashed_password)
    values (
        :name,
        :email,
        :profile,
        :password
        )"""
    ), user).lastrowid

def insert_tweet(user_tweet):
    return current_app.database.execute(text("""
        insert into tweets (
            user_id,
            tweet)
        values (
            :id,
            :tweet
        )
    """), user_tweet).rowcount

def insert_follow(user_follow):
    return current_app.database.execute(text("""
    insert into users_follow_list (
    user_id,
    follow_user_id
    ) values (
    :id,
    :follow
    )
    """), user_follow).rowcount

def insert_unfollow(user_unfollow):
    return current_app.database.execute(text("""
    delete from users_follow_list
    where user_id = :id
    and follow_user_id = :unfollow
    """), user_unfollow).rowcount

def get_timeline(user_id):
    timeline = current_app.database.execute(text("""
    select t.user_id,
    t.tweet
    from tweets t 
    left join users_follow_list ufl on ufl.user_id = :user_id
    where t.user_id = :user_id 
    or t.user_id= ufl.follow_user_id
    """), {'user_id': user_id}).fetchall()


    return [{'user_id':tweet['user_id'],
             'tweeet': tweet['tweet']} for tweet in timeline]

def create_app(test_config = None):   # flask 에서 create_app 함수를 자동으로 인식하여 실행
    app= Flask(__name__)

    if test_config is None:
        app.config.from_pyfile("config.py")  # 없으면 config.py 설정을 따른다
    else:
        app.config.update(test_config)   # test config가 있으면 설정 적용

    database = create_engine(app.config['DB_URL'], encoding= 'utf-8', max_overflow= 0)
    app.database = database

    @app.route('/sign_up', methods = ['post'])
    def sign_up():
        new_user = request.json
        new_user_id = insert_user(new_user)
        new_user = get_user(new_user_id)

        return jsonify(new_user)

    @app.route('/tweet', methods = ['post'])
    def tweet():
        user_tweet = request.json
        tweet = user_tweet['tweet']

        if len(tweet) > 300:
            return '300자 초과', 400

        insert_tweet(user_tweet)

        return '', 200

    @app.route('/follow',methods  = ['post'])
    def follow():
        payload = request.json
        insert_follow(payload)

        return '', 200


    @app.route('/unfollow', methods = ['post'])
    def unfollow():
        payload = request.json
        insert_unfollow(payload)

        return '', 200

    @app.route('/timeline/<int:user_id>', methods = ['get'])
    def timeline(user_id):
        return jsonify({
            'user_id':user_id,
            'timeline' : get_timeline(user_id)
        })


    return app


