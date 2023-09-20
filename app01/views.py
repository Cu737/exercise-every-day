from django.shortcuts import render, redirect


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
