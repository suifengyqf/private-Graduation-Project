import os

import torch
import torchvision.transforms as transforms
from PIL import Image
import numpy as np

class Predict():
    def __init__(self, net, model):
        super(Predict, self).__init__()
        self.model = model
        self.CUDA = torch.cuda.is_available()
        self.net = net
        if self.CUDA:
            self.net.cuda()
            device = 'cuda'
        else:
            device = 'cpu'
        state = torch.load(self.model, map_location=device)
        self.net.load_state_dict(state)
        # print('模型加载完成！')
        self.net.eval()

    @torch.no_grad()
    def recognize(self, img):
        with torch.no_grad():
            if self.CUDA:
                img = img.cuda()
            img = img.view(-1, 3, 64, 64)  # 等于reshape
            y = self.net(img)
            p_y = torch.nn.functional.softmax(y, dim=1)
            # print(p_y)
            p, cls_index = torch.max(p_y, dim=1)
            return cls_index.cpu(), p.cpu()

def predict(net, model, img_path):
    transform = transforms.Compose([
        transforms.Resize((64, 64)),
        transforms.ToTensor(),
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
    ])
    dataset_path = rf"D:\PycharmProjects\一站式平台\bishe\dataset"
    recognizer = Predict(net, model)
    classes = os.listdir(dataset_path)
    img = Image.open(img_path)
    img = Image.fromarray(np.uint8(img))
    img = transform(img)
    cls, p = recognizer.recognize(img)
    return classes[cls], p.numpy()[0]