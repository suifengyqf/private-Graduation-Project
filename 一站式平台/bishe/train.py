import json

import torch
import torchvision.transforms as transforms
from torchvision.datasets import ImageFolder
from torch.utils.data import DataLoader
import requests
# 设置超参数

def load_data(batch_size, num_workers):
    transform = transforms.Compose([
        transforms.Resize((64, 64)),
        transforms.ToTensor(),
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
    ])
    root = r"D:\PycharmProjects\一站式平台\bishe\dataset"
    dataset = ImageFolder(root=root, transform=transform)
    train_size = int(len(dataset) * 0.8)
    test_size = len(dataset) - train_size
    train_dataset, test_dataset = torch.utils.data.random_split(dataset, [train_size, test_size])
    train_loader = DataLoader(dataset=train_dataset,batch_size=batch_size,num_workers=num_workers,shuffle=True)
    test_loader = DataLoader(dataset=test_dataset,batch_size=batch_size,num_workers=num_workers,shuffle=False)
    return train_loader, test_loader

class Train():
    def __init__(self,net, epoch, lr, batch_size, num_workers, model_filename):
        self.jsonfilename = f"{model_filename}.json"
        self.batch_size = batch_size
        self.num_workers = num_workers
        self.net = net
        self.epoch = epoch
        self.lr = lr
        self.model_filename = model_filename
        self.loss_function = torch.nn.CrossEntropyLoss()
        self.CUDA = torch.cuda.is_available()
        self.optimizer = torch.optim.Adam(self.net.parameters(), lr=self.lr)
        self.train_loader, self.test_loader = load_data(self.batch_size, self.num_workers)

    async def Training(self):
        root = r'D:\PycharmProjects\一站式平台\bishe\Models\train_data'
        data_list = []
        for epoch in range(1, self.epoch + 1):
            self.net.train()
            inputs_num = 0.0
            correct_num = 0.0
            loss = 0.0
            for i, (inputs, labels) in enumerate(self.train_loader):
                    self.optimizer.zero_grad()
                    # 前向传播
                    if self.CUDA:
                        inputs = inputs.cuda()
                        labels = labels.cuda()
                    outputs = self.net(inputs)
                    loss = self.loss_function(outputs, labels)
                    # 反向传播和优化
                    self.optimizer.zero_grad()
                    loss.backward()
                    self.optimizer.step()
                    # 转换为概率
                    pre = torch.nn.functional.softmax(outputs, dim=1)
                    # 输出预测类别
                    pre = torch.argmax(pre, dim=1)
                    # 累加预测正确的数量
                    correct_num += (pre == labels).float().sum()
                    inputs_num += len(inputs)
            train_acc = (correct_num / inputs_num) * 100.0

            # 使用测试集验证
            val_acc, val_loss = self.validating()
            print(f"{epoch}:{self.epoch}, train_acc:{train_acc}, val_acc:{val_acc}, train_loss:{loss}, val_loss:{val_loss}")
            # 打印训练过程
            data = {
                "epoch": epoch,
                "train_acc": train_acc.item(),
                "val_acc": val_acc.item(),
                "train_loss": loss.item(),
                "val_loss": val_loss.item(),
                "selected_model": self.model_filename
            }

            data_list.append(data)

        with open(root + '/' + self.jsonfilename, 'w') as f:
            json.dump(data_list, f)
        torch.save(self.net.state_dict(), f'bishe/Models/{self.model_filename}')

    @torch.no_grad()
    def validating(self):
        self.net.eval()  # 测试前加
        inputs_num = 0.0
        correct_num = 0.0
        loss = 0.0
        for inputs, labels in self.test_loader:
            # print(labels)
            if self.CUDA:
                inputs = inputs.cuda()
                labels = labels.cuda()
            outputs = self.net(inputs)
            loss = self.loss_function(outputs, labels)

            pre = torch.nn.functional.softmax(outputs, dim=1)
            pre = torch.argmax(pre, dim=1)
            correct_num += (pre == labels).float().sum()
            inputs_num += len(inputs)
        return (correct_num / inputs_num) * 100.0, loss


