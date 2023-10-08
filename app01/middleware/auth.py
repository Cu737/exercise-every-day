from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import HttpResponse, redirect


class AuthMiddleware(MiddlewareMixin):

    def process_request(self, request):

        # 0.排除不需要的页面
        if request.path_info in ["/login/", "/image/code/","/signup/"]:
            return

        if request.path_info == '/':
            return redirect('login/')

        # 1.读取当前访问的用户的session信息,如果能读到,说明已登录过,就可以继续向后走
        info_dict = request.session.get("info")
        if info_dict:
            return

        # 2.如果没有登录信息
        return redirect("/login/")
