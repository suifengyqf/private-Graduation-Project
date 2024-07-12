from .CloudAPI import COS
import matplotlib.pyplot as plt
import matplotlib
def figure_train(data):
    matplotlib.use('Agg')
    # 提取需要绘制的数据列
    epochs = [entry["epoch"] for entry in data]
    train_acc = [entry["train_acc"] for entry in data]
    val_acc = [entry["val_acc"] for entry in data]
    train_loss = [entry["train_loss"] for entry in data]
    val_loss = [entry["val_loss"] for entry in data]

    # 创建第一个图表对象和子图
    fig1 = plt.figure(1)
    ax1 = fig1.add_subplot(111)
    ax1.plot(epochs, train_acc, label='Train Accuracy')
    ax1.plot(epochs, val_acc, label='Validation Accuracy')
    ax1.set_title('Training and Validation Accuracy')
    ax1.set_xlabel('Epochs')
    ax1.set_ylabel('Accuracy')
    ax1.legend()

    # 创建第二个图表对象和子图
    fig2 = plt.figure(2)
    ax2 = fig2.add_subplot(111)
    ax2.plot(epochs, train_loss, label='Train Loss')
    ax2.plot(epochs, val_loss, label='Validation Loss')
    ax2.set_title('Training and Validation Loss')
    ax2.set_xlabel('Epochs')
    ax2.set_ylabel('Loss')
    ax2.legend()
    path1 = r'D:\PycharmProjects\一站式平台\templates\static\images\figure\train_acc.png'
    path2 = r'D:\PycharmProjects\一站式平台\templates\static\images\figure\train_loss.png'
    fig1.savefig(path1)
    fig2.savefig(path2)
    return path1, path2

def check_login(username,password):
    if COS().judge_database_if_exist(username):
        df = COS().read_user_from_dataset()
        confirmpwd = str(df.loc[df['phoneNumber'] == int(username), 'password'].values[0])
        if password == confirmpwd:
            return None
        else:
            return '密码错误'
    return "账号或密码错误，请重新输入"

#检测手机号输入是否合规
def checkphonenumber(phone_number):
    """
    验证手机号是否合规
    参数：
    phone_number: 手机号
    返回值：
    如果手机号合规，返回None；否则，返回相应的错误消息
    """
    if len(phone_number) == 0:
        return '请输入手机号'
    elif len(phone_number) != 11:
        return '请输入有效的手机号'
    elif COS().judge_database_if_exist(phone_number):
        return '该手机号已被注册'
    else:
        return None

#检测密码输入是否合规
def checkpwd(pwd):
    """
    验证密码是否合理
    :param pwd: 密码
    :return:
    如果密码合规，返回None；否则，返回相应的错误消息
    """
    if len(pwd) == 0:
        return "请输入密码"
    elif len(pwd) < 6 or len(pwd) > 20:
        return "密码长度在6-20个字符,请输入符合要求的密码"
    else:
        return None

#检测确认密码输入是否正确
def checkconfirmpwd(pwd,confirmpwd):
    if len(confirmpwd) == 0:
        return "请再次输入密码"
    elif pwd != confirmpwd:
        return "两次输入的密码不一致"
    else:
        return None


