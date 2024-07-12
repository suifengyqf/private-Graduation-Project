from django.shortcuts import render,HttpResponse
# Create your views here.
import os
from django.core.files.uploadedfile import TemporaryUploadedFile
import tempfile
from django.views.decorators.csrf import csrf_exempt
from bishe.train import Train
from django.shortcuts import render, redirect, reverse
from bishe.CloudAPI import COS
import pandas as pd
from PIL import Image
from .tools import *
import asyncio
from .predict import predict
import os
import json

def traverse_directory(path):
    # 遍历当前目录下的所有文件和文件夹
    for file_name in os.listdir(path):
        # 拼接文件或文件夹的完整路径
        full_path = os.path.join(path, file_name)

        if os.path.isdir(full_path):
            # 如果是文件夹，递归调用遍历函数
            traverse_directory(full_path)
        else:
            # 如果是文件，进行相应的操作
            check_file(full_path)

def check_file(file):
    if file.endswith('.jpg') or file.endswith('.png') or file.endswith('.jpeg'):
        try:
            Image.open(file)
        except:
            os.remove(file)
    else:
        os.remove(file)

def load_model_architecture(filepath, category: int):
    with open(filepath, 'r',encoding='utf-8') as file:
        code = file.read()
    globals_dict = {}
    exec(code, globals_dict)
    print(globals_dict['CNNModel'])
    model = globals_dict['CNNModel'](category)
    return model

async def train_async(model, epochs, lr, batch_size, model_filename):
    # 异步训练逻辑，根据需要进行修改
    trainer = Train(model, epochs, lr, batch_size, 0, model_filename)
    await trainer.Training()

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        error_message = check_login(username,password)
        if error_message:
            request.session['error_message'] = error_message
            return redirect('../',request.session)
        else:
            request.session['username'] = username
            request.session['password'] = password
            return redirect('../upload',request.session)
    else:
        if request.session.get('error_message'):
            error_message = request.session.get('error_message')
            del request.session['error_message']
            return render(request, 'login.html', {'error_message': error_message})
        else:
            return render(request, 'login.html')

def regist_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        # 检测手机号输入是否合规
        error_message = checkphonenumber(username)
        if error_message:
            request.session['error_message'] = error_message
            return redirect('./',request.session['error_message'])

        #检测密码输入是否有误
        error_message = checkpwd(password)
        if error_message:
            request.session['error_message'] = error_message
            return redirect('./',request.session['error_message'])

        # 检测确认密码输入是否正确
        error_message = checkconfirmpwd(password,confirm_password)
        if error_message:
            request.session['error_message'] = error_message
            return redirect('./',request.session['error_message'])
        COS().create_user_database(username)
        COS().write_user_to_dataset(pd.DataFrame({"phoneNumber": [username], "password": [password]}))
        COS().generate_engineer_folder(username)
        request.session['username'] = username
        request.session['password'] = password
        return redirect('../login',request.session)
    else:
        if request.session.get('error_message'):
            error_message = request.session.get('error_message')
            del request.session['error_message']
            return render(request, 'register.html', {'error_message': error_message})
        else:
            return render(request, 'register.html')

@csrf_exempt
def upload_view(request):
    if request.method == 'POST':
        username = request.session['username']
        #模型文件较小，创建临时文件进行上传
        try:
            nets = request.FILES.getlist('nets')
            for net in nets:
                # 创建临时文件
                _, temp_file_path = tempfile.mkstemp(prefix='uploaded_file_', suffix='.tmp')
                with open(temp_file_path, 'wb') as temp_file:
                    for chunk in net.chunks():
                        temp_file.write(chunk)
                local_file_path = temp_file_path
                COS().upload_net(username,net,local_file_path)
        except:
            pass
        try:
            datasets = request.FILES.getlist('dataset')
            for dataset in datasets:
                temp_file_path = dataset.temporary_file_path()
                COS().upload_data(username,dataset,temp_file_path)
        except:
            pass
        return redirect('../train',request.session)
    else:
        username = request.session['username']

        if not username:
            return render(request, 'login.html')
        return render(request, 'upload_data.html')

def Train_View(request):
    if request.method == 'POST':
        username = request.session['username']
        epochs = int(request.POST['epochs'])
        lr = float(request.POST['lr'])
        model_filename = request.POST['filename']
        model = request.POST["selected_net"]
        datasets = request.POST.getlist("selected_dataset")
        category = len(datasets)
        if datasets:
            for data in datasets:
                COS().unzip_file_from_cos(username,data)
                traverse_directory(r"D:\PycharmProjects\一站式平台\bishe\dataset")
        if model:
            COS().download_net(username,model)
            model = load_model_architecture(f'bishe/Nets/{request.POST["selected_net"]}', category)
            # 创建事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # 调用异步训练任务
            task = train_async(model, epochs, lr, 32, model_filename)
            loop.run_until_complete(task)

            # 关闭事件循环
            loop.close()
        COS().upload_model(username,model_filename,rf"D:\PycharmProjects\一站式平台\bishe\Models/{model_filename}")
        COS().upload_train_data(username,model_filename,rf"D:\PycharmProjects\一站式平台\bishe\Models\train_data\{model_filename}.json")
        return redirect('../train',request.session)
    elif request.method == 'GET':
        username = request.session['username']
        if not username:
            return render(request, 'login.html')
        try:
            nets = COS().read_net(username)
            datasets = COS().read_dataset(username)
            return render(request,'train.html',{"nets":nets,"datasets":datasets})
        except:
            return render(request,'train.html')

@csrf_exempt
def show_models_view(request):
    if request.method == 'GET':
        username = request.session['username']
        if not username:
            return render(request, 'login.html')
        models = COS().read_model(username)
        return render(request,'show_models.html',{"models":models})
    else:
        username = request.session['username']
        model = request.POST["selected_model"]
        COS().download_train_data(username,model)
        with open(r"D:\PycharmProjects\一站式平台\bishe\Models\train_data" + '/' + model + '.json', 'r') as f:
            data = json.load(f)
        figureAcc, figureloss = figure_train(data)
        return render(request,'show_models.html',{"figureAcc":figureAcc,"figureloss":figureloss})

def predict_view(request):
    Model_path = rf"D:\PycharmProjects\一站式平台\bishe\Models"
    Net_path = rf"D:\PycharmProjects\一站式平台\bishe\Nets"
    if request.method == 'POST':
        username = request.session['username']
        nets = COS().read_net(username)
        models = COS().read_model(username)
        model = request.POST["selected_model"]
        net = request.POST["selected_net"]
        if not os.path.exists(Model_path+ "/" + f"{model}"):
            COS().download_model(username, model)
        if not os.path.exists(Net_path+ "/" + f"{net}"):
            COS().download_net(username, net)
        upload_file = request.FILES.get('file')
        try:
            file_name = upload_file.name
            file_path = rf"D:\PycharmProjects\一站式平台\templates\static\images\uploadfiles\{file_name}"
            with open(file_path, 'wb') as file:
                file.write(upload_file.read())
        except:
            return redirect('../predict', request.session)
        if net and model:
            net = load_model_architecture(f'bishe/Nets/{request.POST["selected_net"]}',int(3))
            model = f'bishe/Models/{request.POST["selected_model"]}'
            try:
                prob, tag = predict(net, model, file_path)
            except:
                prob, tag = "无", "识别有误"
            return render(request, 'predict.html', {'prob': prob, 'tag': tag,'img':file_name,'nets':nets,"models":models})
    elif request.method == 'GET':
        username = request.session['username']
        if not username:
            return render(request, 'login.html')
        try:
            nets = COS().read_net(username)
            models = COS().read_model(username)
            return render(request,'predict.html',{"nets":nets,"models":models})
        except:
            return render(request,'predict.html')