# Authro     : ThreeDog
# Data       : 2019-05-24
# Function   : 此模块提供用户调用的所有函数。用户输入 ls cd find 等命令均调用此模块的函数。
# Remark     : 调用方法通过getattr，即反射的形式实现调用。因此函数名很重要不可乱写
# 函数调用的操作对象均是用户列表，因此传入将users列表作为parent参数传入

from Common import cmd_list
from Common import history
from Common import emoj_list
from tdinput import td_input
from translator import tdtr

class Cmd(object):
    def __init__(self,parent=None):
        self.parent = parent

    def ls(self,arg):
        '''
        获取最新消息列表
        '''
        if len(arg) == 0:         # ls 没有参数：获取所有消息列表
            if not self.parent.hasNewMsg():  # 没有新消息
                print(tdtr("消息列表为空"))
            else:
                for user in self.parent.getUsers():
                    if user.hasNewMsg(): # 消息列表必须不为空
                        # 如果消息列表不为空，就把这个人的消息都打印出来
                        print(tdtr("【id:{:^3} 】 {:^10} 发来 {:^3} 条未读消息").format(user.id,user.getName(),len(user.msgs)))

        elif arg[0] == '-a':    # ls -a 获取全部好友 + 群聊
            print(tdtr("好友 | 群聊列表："))
            for user in self.parent.getUsers():
                print(" {:^4}：{:^4} {:^3} ".format(user.id,user.type,user.getName()))

        elif arg[0] == '-f':    # ls -f 好友列表
            print(tdtr("好友列表："))
            for user in filter(lambda x : x.type == tdtr('【好友】') , self.parent.getUsers()):
                print(" {:^4}：{:^4} {:^3} ".format(user.id,user.type,user.getName()))

        elif arg[0] == '-r':    # ls -f 群聊列表
            print(tdtr("群聊列表："))
            for user in filter(lambda x : x.type == tdtr('【群聊】') , self.parent.getUsers()):
                print(" {:^4}：{:^4} {:^3} ".format(user.id,user.type,user.getName()))


        else :
            print(tdtr('参数错误，请重试'))

    def cd(self,arg):
        '''
        进入聊天室， cd {id}  进入与id进行聊天的界面
        '''
        if len(arg) == 0 :
            print(tdtr("cd命令需要参数"))
            return
        elif arg[0] == '..' or arg[0] == '../':
            # 返回主页
            return
        else:
            try:
                user_id = int(arg[0])
            except Exception :
                print(tdtr("cd后请输入一个数字"))
                return
            user = self.parent.getUserByID(user_id)
            if user is None: # 未找到用户 直接返回
                print(tdtr("用户id不存在，请重试"))
                return 
            self.parent.current_user = user
            self.cls(None)
            # 进入与其聊天的死循环
            while True:
                # 进入后先把队列中的消息打印
                while user.hasNewMsg():
                    msg = user.takeMsg()
                    print("【{}】{} ===> ：{}".format(msg.createTime,msg.getName(),msg.text))
                print(tdtr(" 与 {} 聊天中 >>> ").format(user.getName()),end = '')
                msg = td_input()
                if msg.strip() == 'cd ..' or msg.strip() == 'cd ../':
                    # 退出聊天，把当前正在沟通的用户置为None
                    self.parent.current_user = None
                    break
                if msg.strip() == "emoj":
                    print(tdtr("检测到您的输入为：emoj，如果发送消息内容即为emoj直接回车键发送，如果查看所有emoj表情，请输入1："))
                    res = td_input()
                    if res != "1":
                        pass
                    else:
                        print(emoj_list)
                        continue

                # 如果输入内容包含疑似cmd字符串，这个len不为0
                if len(list(filter(lambda x:True if x in msg else False,cmd_list))) > 0:
                    print(tdtr("您的输入中包含疑似shell终端命令的字符串，确认发送此消息吗？y or n"))
                    res = td_input()
                    if res == 'y' or res == 'yes':
                        pass
                    else:
                        continue
                # 如果能走到这一步就发送数据
                if user.id == 0 or user.id == '0':  # 处理发送给文件助手的消息
                    self.parent.sendMsg(msg,'filehelper')
                else:
                    self.parent.sendMsg(msg,user.userName) # 将信息发送给user  userName是微信用于识别的用户名

    def find(self,arg):
        '''
        通过字符串查找对象 , 命令示例： find 张三 李四 三级狗
        '''
        if len(arg) == 0:
            print(tdtr("参数错误，请重试"))
            return

        result = []
        print(tdtr("查找到以下好友|群聊："))
        for keywords in arg:        # 列表拆分  关键字进行模糊查询
            for user in self.parent.getUsers():
                if keywords in user: # User的in重写过！
                    if user not in result: # 已经存在的不再添加防止重复
                        result.append(user)
        # x 就是每一个user
        # 注意map是一个惰性序列，必须要list一下才会执行
        list(map(lambda x : print(" {:^4}：{:^4} {:^4}  {:^4} ".format(x.id,x.type,x.remarkName,x.nickName)) ,result))

    def cls(self,arg): #清屏
        print("\033c",end='')

    def clear(self,arg): # 同上
        print("\033c",end='')

    def reload(self,arg):
        self.parent.reloadUserList()
    
    def emoj(self,arg): # 显示所有可用的emoj表情
        print(tdtr("所有可用表情如下，在消息中直接添加即可发送："))
        print(emoj_list)

    def group(self,arg):
        '''
        群发模式，请指定群发模式： group id1 id2 id3 id... 消息将发送给指定的所有人
        '''
        user_name_list = []
        if len(arg) == 0 :
            print(tdtr("请指定群发对象的id，例如： 'group 3 34 36 23 74'"))
            return
        elif arg[0] == '-inverse': # 反选模式，指定的好友不会收到消息。
            for uid in [x.id for x in self.parent.getUsers()]:
                if str(uid) not in arg[1:]:
                    user_name_list.append(self.parent.getUserByID(uid).userName)
        else:   # 正选模式
            for uid in arg:
                if uid == ' ': # 过滤掉空格
                    continue  
                try:
                    user_id = int(uid)
                except Exception :
                    continue 
                user_name_list.append(self.parent.getUserByID(user_id).userName)
        while(True):
            print(tdtr("【群发模式】选定的{}位好友将收到此条信息 \n请输入要发送的内容，输入“cd ..”退出\n>>> ").format(len(user_name_list)),end = '')
            msg = td_input()
            if msg == 'cd ..' or msg == 'cd ../':
                # 退出聊天，把当前正在沟通的用户置为None
                self.parent.current_user = None
                break
            # 如果输入内容包含疑似cmd字符串，这个len不为0
            if len(list(filter(lambda x:True if x in msg else False,cmd_list))) > 0:
                print(tdtr("您的输入中包含疑似shell终端命令的字符串，确认发送此消息吗？y or n"))
                res = td_input()
                if res == 'y' or res == 'yes':
                    pass
                else:
                    continue
            # 如果能走到这一步就发送数据
            for name in user_name_list:
                self.parent.sendMsg(msg,name) # 将信息发送给user  userName是微信用于识别的用户名

    def help(self,arg):
        print("\033c \n")
        print("                                 WeChat of Console")
        print("                                     版本：2.0")
        print("                                 维护人：ThreeDog")
        print("     项目源码：https://github.com/TheThreeDog/TouchFish/tree/master/WechatOfConsole")
        print("                          控制台版本微信是可自由分发的开放源代码软件")
        print("                                 帮助乌干达的可怜儿童！")
        print("              输入 help 或 h 或 man <Enter>      查看说明！\n")
        print("              输入 exit <Enter> 退出")
        print("              输入 ls <Enter> 显示所有未读消息")
        print("              输入 ls -a <Enter> 显示所有好友 | 群聊")
        print("              输入 ls -f <Enter> 显示所有好友列表")
        print("              输入 ls -r <Enter> 显示所有群聊列表")
        print("              输入 ignore {id} <Enter> 忽略编号为{id}的好友发来的消息")
        print("              输入 ignore all 忽略掉所有消息")
        print("              输入 find XXX <Enter>：通过姓名模糊查询好友或群聊")
        print("              输入 cls 或 clear <Enter> ：清空屏幕")
        print("              输入 cd {id} <Enter> 进入与编号为{id}的用户|群聊聊天，如 cd 25")
        print("              输入 group {id} {id2} {id3} ... <Enter> 进入群发模式，消息将发送给id id2 id3...指定的所有人")
        print("              输入 group -inverse {id} {id2} {id3} ... <Enter> 进入反选群发模式，消息将发送给除了id id2 id3 之外的所有人")
        print("              在聊天模式中输入 cd .. 或 cd ../ <Enter> 退出到主界面")
        print("              输入 reload <Enter>重新加载好友和群聊列表（如果在程序运行期间用微信加入了新的群聊或好友，执行此函数可将新成员加载如列表）")
        print("              输入 emoj <Enter> 显示所有可用的表情")

    def h(self,arg):
        self.help(arg)

    def man(self,arg):
        self.help(arg)

    def ignore(self,arg):
        '''
        忽略指定的消息 , 命令示例： 
            - ignore 123 忽略掉id为123的用户发送来的所有消息
            - ignore all 忽略掉所有消息
        '''
        if len(arg) == 0:
            print(tdtr("参数错误，请重试"))
            return

        self.parent.ignore(arg[0])
