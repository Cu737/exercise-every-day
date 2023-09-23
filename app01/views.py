
import mediapipe as mp
from django.shortcuts import render, redirect
import cv2
from django.http import StreamingHttpResponse
from django.views.decorators.clickjacking import xframe_options_exempt


# Create your views here.
def login(request):
    """
    转入登录页面
    :param request:
    :return:
    """
    return render(request, "login.html")


def index(request):
    """
    转入主页
    :param request:
    :return:
    """
    return render(request, "index.html")


def game(request):
    return render(request, "game.html")


def gen_display(camera):
    mp_draw = mp.solutions.drawing_utils
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands()
    # 循环读取摄像头的画面
    while True:
        # 读取一帧图片
        ret, frame = camera.read()
        if ret:
            # 将图片进行编码

            frameRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(frameRGB)

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # 关键点可视化
                    mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    # 输出中指尖的坐标
                    print(hand_landmarks.landmark[12])

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
