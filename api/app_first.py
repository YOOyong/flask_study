from flask import Flask , jsonify , request
from flask.json import JSONEncoder
from sqlalchemy import create_engine, text


app = Flask(__name__)   # import 한 flask 클래스를 객체화
app.users = {}
app.id_count = 1
app.tweets = []  #사용자들의 트윗을 저장할 딕셔너리들의 리스트/ 딕셔너리의 key는 id, value 는 트윗


class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)

        return JSONEncoder.default(self, obj)


app.json_encoder = CustomJSONEncoder


@app.route('/sign-up', methods = ['post'])  #post 요청은 request에 넣어져 옴
def sign_up():
    new_user = request.json  #http 요청으로 전송된 새 회원 데이터를 저장 request.json은 파이썬 딕셔너리로 반환하는 역할
    new_user['id'] = app.id_count  #id count 변수 값으를 id로 한다
    app.users[app.id_count] = new_user # app.users의 id count index 위치에 새 유저 저장.
    app.id_count = app.id_count + 1   #이런 방식은 동시 요청이 있을 때 문제가 있을 수 있음. *atomic 연산 찾아보길

    return jsonify(new_user)


@app.route("/ping" , methods = ['GET']) #app.route로 엔드포인트 생성
def ping():
    return 'pong'


@app.route("/tweet", methods=['post'])
def tweet():
    payload = request.json  #입력받은 트윗을 딕셔너리로 받아옴
    user_id = int(payload['id'])
    tweet = payload['tweet']      # 받은 request를 변수에 빼놓는다

    if user_id not in app.users:
        return '없는 사용자', 400

    if len(tweet) > 300:
        return '300자 초과',400

    user_id = int(payload['id'])   # 중복코드???
    app.tweets.append({
        'user_id' : user_id,
        'tweet' : tweet
    })

    return '',200

@app.route('/follow', methods = ['post'])
def follow():
    payload = request.json
    user_id = int(payload['id'])
    user_id_to_follow = int(payload['follow'])

    if user_id not in app.users or user_id_to_follow not in app.users:
        return '없는 유저', 400

    user = app.users[user_id]  #해당 아이디를 가진 유저 딕셔너리 가져옴
    user.setdefault('follow' , set()).add(user_id_to_follow)   #setdefault 는 유용한 딕셔너리 함수 찾아봐!
    # setdefault(키값, 초기값) 키가 있으면 있는거 반환, 없으면 초기값으로 새로 만들고 반환
    # 반환된 follow list set에 add로 새 팔로우 추가
    return jsonify(user)


@app.route('/unfollow', methods = ['post'])
def unfollow():
    payload = request.json
    user_id = int(payload['id'])
    user_id_to_unfollow = int(payload['unfollow'])

    if user_id not in app.users or user_id_to_unfollow not in app.users:
        return 'non exist user', 400
    
    user = app.users[user_id]  # 신청한 유저를 유저변수에 저장
    user.setdefault('follow', set()).discard(user_id_to_unfollow)
    
    return jsonify(user)   # 작업이 끝나면 유저 딕셔너리를 보여줌

#flask에서 ping함수의 reuturn을 http 형식으로 바꾸어 보내줌
# http는 stateless 기 때문에 각 http통신간 서로 연결 x
# 로그인 여부등은 쿠키나 세션으로 해결
#쿠키는 브라우저에서 세션은 서버에서

@app.route('/timeline/<int:user_id>',methods = ['get'])
def timeline(user_id):
    if user_id not in app.users:
        return 'non exist user',400

    follow_list = app.users[user_id].get('follow', set())
    follow_list.add(user_id) # 내 트윗도 보기위해

    timelines = [tweet for tweet in app.tweets if tweet['user_id'] in follow_list]

    return jsonify({
        'user_id': user_id,
        'timeline': timelines
    })
