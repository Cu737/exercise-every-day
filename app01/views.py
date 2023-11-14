import mediapipe as mp
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

q_left = deque(maxlen=15)
left_flag = 0
q_right = deque(maxlen=15)
right_flag = 0


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
        # print(form.cleaned_data)

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
        return redirect("/index/")
    return redirect('/login')


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


def index(request):
    """
    转入主页
    :param request:
    :return:
    """
    return render(request, "index.html")


def game(request):
    global left_flag
    global right_flag

    if (left_flag == 1) and request.method == "POST":
        print("发送左")
        left_flag = 0
        return JsonResponse({"list":list(q_left)})
    if (right_flag == 1) and request.method == "POST":
        print("发送右")
        right_flag = 0
        return JsonResponse({"list":list(q_right)})

    if request.method == "GET":
        return render(request, "game.html")
    return HttpResponse()


def logout(request):
    """ 退出登录 """

    # 清楚当前session
    request.session.clear()

    return redirect("/login/")


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
            results = hands.process(frameRGB)

            if results.multi_hand_landmarks:

                for hand_landmarks in results.multi_hand_landmarks:
                    handedness = results.multi_handedness[0]
                    # print(handedness.classification[0].label)
                    # 关键点可视化
                    mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    if handedness.classification[0].label == 'Left':

                        # 输出中指尖的坐标
                        # print("左")
                        # print(hand_landmarks.landmark[12].x)
                        q_left.append({"left_x": hand_landmarks.landmark[8].x * 650,
                                       "left_y": hand_landmarks.landmark[8].y * 500}
                                      )
                        left_flag = 1
                    else:
                        q_right.append({"right_x": hand_landmarks.landmark[8].x * 650,
                                        "right_y": hand_landmarks.landmark[8].y * 500}
                                       )
                        right_flag = 1

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
