import mediapipe as mp
import numpy as np
from django.shortcuts import render, redirect
import cv2
from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.clickjacking import xframe_options_exempt

from django.shortcuts import render, redirect, HttpResponse
from django import forms
import pymysql
from . import models
from utils.code import check_code
from django.shortcuts import HttpResponse
from io import BytesIO
from app01.models import UserInfo
from collections import deque

q_left = deque(maxlen=10)
left_flag = 0
q_right = deque(maxlen=10)
right_flag = 0
user = {'username': ""}


def image_code(request):
    """ 生成图片验证码 """
    # 调用pillow函数,生成图片
    img, code_string = check_code()

    # 写入到自己的session中,以便于后续获取验证码再进行校验
    request.session['image_code'] = code_string
    # 给session设置 60s 超时
    request.session.set_expiry(60)

    # 将图片保存到内存
    stream = BytesIO()
    img.save(stream, 'png')
    return HttpResponse(stream.getvalue())


# 用户登录表单
class LoginForm(forms.Form):
    username = forms.CharField(
        # label="用户名",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "请输入用户名"}),
        required=True,
    )
    password = forms.CharField(
        # label="密码",
        # render_value=True 表示当提交后,如果密码输入错误,不会自动清空密码输入框的内容
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "请输入密码"}, ),
        required=True,
    )
    code = forms.CharField(
        # label="验证码",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "请输入验证码"}),
        required=True,
    )

    # def clean_password(self):
    #     pwd = self.cleaned_data.get("password")
    #     return md5(pwd)


# 用户注册表单
class SignupForm(forms.Form):
    username = forms.CharField(
        label="用户名",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "请输入用户名"}),
        required=True,
    )
    password = forms.CharField(
        label="密码",
        # render_value=True 表示当提交后,如果密码输入错误,不会自动清空密码输入框的内容
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "请输入密码"}, ),
        required=True,
    )
    confirmed_password = forms.CharField(
        label="确认密码",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "确认密码"}, ),
        required=True,
    )
    # def clean_password(self):
    #     pwd = self.cleaned_data.get("password")
    #     return md5(pwd)


def login(request):
    """登录"""
    if request.method == "GET":
        form = LoginForm()
        return render(request, 'login.html', {"form": form})

    if 'btn2' in request.POST:
        return redirect('/signup/')

    form = LoginForm(data=request.POST)

    if form.is_valid():
        # 验证成功, 获取到的用户名和密码

        # 拿到用户名，便于后续显示
        global user
        user = {'username': form.cleaned_data['username']}
        # 验证码的校验
        user_input_code = form.cleaned_data.pop('code')
        image_code = request.session.get('image_code', "")
        if image_code.upper() != user_input_code.upper():
            form.add_error("code", "验证码错误")
            return render(request, 'login.html', {"form": form})

        # 去数据库校验用户名和密码是否正确
        User_object = models.UserInfo.objects.filter(**form.cleaned_data).first()
        # 如果数据库中没有查询到数据
        if not User_object:
            # 手动抛出错误显示在"password"字段下
            form.add_error("username", "用户名或密码错误")
            return render(request, 'login.html', {"form": form})

        # 如果用户名密码正确
        # 网站生成随机字符创,写到用户浏览器的cookie中,再写入到服务器的session中
        request.session["info"] = {'username': User_object.username}
        # 重新设置session的超时时间,因为之前设置的session的超时时间的 60s
        request.session.set_expiry(60 * 60 * 24)
        return redirect("/index/home")
    return redirect('/login')


def index_home(request):
    if request.method == 'GET':
        # 处理 GET 请求的逻辑
        return render(request, "home.html", {'user': user})


def index_home_fwc(request):
    if request.method == 'GET':
        # 处理 GET 请求的逻辑
        return render(request, "home_fwc.html", {'user': user})


def index_ranking(request):
    print("aa")
    top_three_users = UserInfo.objects.order_by('-max_score')[:3]
    # top_three_users = [
    #     {'username': 'user1', 'max_score': 100},
    #     {'username': 'user2', 'max_score': 90},
    #     {'username': 'user3', 'max_score': 80},
    # ]
    top_three_fwcers=UserInfo.objects.order_by('-fwc_score')[:3]
    print(top_three_users)
    return render(request, 'ranking.html', {'top_three_users': top_three_users, 'user': user,'fwcer':top_three_fwcers})


def signup(request):
    """注册"""
    if request.method == "GET":
        form = SignupForm()
        return render(request, 'signup.html', {"form": form})

    form = SignupForm(data=request.POST)
    if form.is_valid():
        # 检查用户名是否已经注册过
        existing_user = models.UserInfo.objects.filter(username=form.cleaned_data['username']).exists()
        if existing_user:
            form.add_error("username", "该用户名已经被注册")
            return render(request, 'signup.html', {"form": form})

        # 检查确认密码是否和密码输入一致
        if form.cleaned_data['password'] == form.cleaned_data['confirmed_password']:
            user_info = UserInfo(username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            user_info.save()
            return redirect('/login/')
        form.add_error("confirmed_password", "密码不一致")
        return render(request, 'signup.html', {"form": form})
    return redirect('/signup/')


def game(request):
    global left_flag
    global right_flag

    if (left_flag == 1) and request.method == "POST":
        print("发送左")
        left_flag = 0
        return JsonResponse({"list": list(q_left)})
    if (right_flag == 1) and request.method == "POST":
        print("发送右")
        right_flag = 0
        return JsonResponse({"list": list(q_right)})

    if request.method == "GET":
        return render(request, "game.html", {'user': user})
    return HttpResponse()



def fwc_view(request):
    return render(request, 'fwc.html')









def logout(request):
    """ 退出登录 """

    # 清楚当前session
    request.session.clear()

    return redirect("/login/")


def calculate_angle(a, b, c):
    a = np.array(a)  # First
    b = np.array(b)  # Mid
    c = np.array(c)  # End

    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)

    if angle > 180.0:
        angle = 360 - angle

    return angle

fwc_counter = 0

def get_counter_data(request):
    global fwc_counter
    return JsonResponse({'counter': fwc_counter})


def gen_display(camera):
    global left_flag
    global right_flag
    mp_draw = mp.solutions.drawing_utils
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(max_num_hands=2)

    # 循环读取摄像头的画面
    while True:
        # 读取一帧图片
        ret, frame = camera.read()
        frame = cv2.flip(frame, 1)

        if ret:
            # 将图片进行编码
            frameRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # 手部检测
            hands_results = hands.process(frameRGB)
            if hands_results.multi_hand_landmarks:
                for hand_landmarks in hands_results.multi_hand_landmarks:
                    handedness = hands_results.multi_handedness[0]
                    mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    if handedness.classification[0].label == 'Left':
                        q_left.append({"left_x": hand_landmarks.landmark[8].x * 650,
                                       "left_y": hand_landmarks.landmark[8].y * 500})
                        left_flag = 1
                    else:
                        q_right.append({"right_x": hand_landmarks.landmark[8].x * 650,
                                        "right_y": hand_landmarks.landmark[8].y * 500})
                        right_flag = 1

            # 编码并传输视频流
            ret, frame = cv2.imencode('.jpeg', frame)
            if ret:
                # 转换为字节类型，并存储在迭代器中
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame.tobytes() + b'\r\n')

def fwc_display(camera):

    mp_draw = mp.solutions.drawing_utils
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
    global fwc_counter
    stage = None
    max_angle = 160
    min_angle = 60

    # 循环读取摄像头的画面
    while True:
        # 读取一帧图片
        ret, frame = camera.read()
        frame = cv2.flip(frame, 1)

        if ret:
            # 将图片进行编码
            frameRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # 俯卧撑检测
            pose_results = pose.process(frameRGB)
            if pose_results.pose_landmarks:
                landmarks = pose_results.pose_landmarks.landmark
                # 获得坐标
                shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                            landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
                elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x,
                         landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
                wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x,
                         landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
                angle = calculate_angle(shoulder, elbow, wrist)

                # 俯卧撑计数器
                if angle > max_angle and stage != 'down':
                    stage = "up"
                if angle > max_angle and stage == 'down':
                    stage = "up"
                    fwc_counter += 1
                    print(fwc_counter)
                if angle < min_angle and stage == 'up':
                    stage = "down"

                    # 绘制出关键点的连接线
                mp_draw.draw_landmarks(frame, pose_results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                       mp_draw.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=2),
                                       mp_draw.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2))

            # 编码并传输视频流
            ret, frame = cv2.imencode('.jpeg', frame)
            if ret:
                # 转换为字节类型，并存储在迭代器中
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame.tobytes() + b'\r\n')


@xframe_options_exempt
def video(request):
    # 创建一个摄像头对象，参数为0表示使用电脑前置摄像头
    camera = cv2.VideoCapture(0)
    # 设置摄像头宽度值
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 500)

    # 使用StreamingHttpResponse类传输视频流，content_type为'multipart/x-mixed-replace; boundary=frame'
    return StreamingHttpResponse(gen_display(camera), content_type='multipart/x-mixed-replace; boundary=frame')

@xframe_options_exempt
def fwc_video(request):
    # 创建一个摄像头对象，参数为0表示使用电脑前置摄像头
    camera = cv2.VideoCapture(0)
    # 设置摄像头宽度值
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 500)

    # 使用StreamingHttpResponse类传输视频流，content_type为'multipart/x-mixed-replace; boundary=frame'
    return StreamingHttpResponse(fwc_display(camera), content_type='multipart/x-mixed-replace; boundary=frame')

from django.http import JsonResponse
import json


def update_score(request):
    if request.method == 'POST':
        body_unicode = request.body.decode('utf-8')
        data = json.loads(body_unicode)
        new_score = data['newScore']
        print(new_score)
        # 在这里进行更新分数的逻辑
        try:
            user_info = UserInfo.objects.get(username=user['username'])
            if user_info.max_score < new_score:
                user_info.max_score = new_score
                user_info.save()
            return JsonResponse({'message': 'Score updated successfully.'})
        except UserInfo.DoesNotExist:
            return JsonResponse({'error': 'User not found.'}, status=404)
    else:
        return JsonResponse({'error': 'Invalid request method.'}, status=400)
