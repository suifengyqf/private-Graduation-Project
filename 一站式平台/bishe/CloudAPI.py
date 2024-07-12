# 腾讯云
import json

from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
from qcloud_cos import CosServiceError
from qcloud_cos.cos_threadpool import SimpleThreadPool
from zipfile import ZipFile

# Others
import pandas as pd
from io import BytesIO
import io
import random
import os
import zipfile
# -*- coding=utf-8
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client

class COS:
    def __init__(self):
        """初始化COS"""
        self.secret_id = ''
        self.secret_key = ''
        self.region = 'ap-nanjing'
        self.bucket = ''
        self.config = CosConfig(Region=self.region, SecretId=self.secret_id, SecretKey=self.secret_key)
        self.client = CosS3Client(self.config)

    def reset_user_pwd(self,phonenumber,password):
        """
        intro:重置用户密码
        :param phonenumber: 用户手机号
        :param password: 用户密码
        :return:
        """
        try:
            response = self.client.get_object(
                Bucket=self.bucket,
                Key='user.xlsx'
            )
            data = response['Body'].get_raw_stream().read()
            df = pd.read_excel(data, sheet_name='Sheet1')
            df.loc[df['phoneNumber'] == phonenumber, 'password'] = password
            buf = BytesIO()
            df.to_excel(buf, index=False)
            self.client.put_object(
                Bucket=self.bucket,
                Key='user.xlsx',
                Body=buf.getvalue()
            )
        except Exception as e:
            print("Read COS error:", e)

    def read_user_from_dataset(self):
        """
        intro:从COS中读取Excel文件内容
        :return: df:pd.DataFrame
        """
        try:
            response = self.client.get_object(
                Bucket=self.bucket,
                Key='user.xlsx'
            )
            data = response['Body'].get_raw_stream().read()
            df = pd.read_excel(data, sheet_name='Sheet1')
            return df
        except Exception as e:
            print("Read COS error:", e)

    def write_user_to_dataset(self, new_data: pd.DataFrame):
        """
        intro:将新数据写入COS中的Excel文件
        :param new_data: 写入的新数据
        :return:
        """
        try:
            # 读取数据
            df = self.read_user_from_dataset()

            # 将新数据追加到原有数据中
            df = pd.concat([df, new_data])

            # 将修改后的数据写入 COS 中的 Excel 文件
            buf = BytesIO()
            df.to_excel(buf, index=False)
            self.client.put_object(
                Bucket=self.bucket,
                Key='user.xlsx',
                Body=buf.getvalue()
            )
            print('Write COS success!')
        except Exception as e:
            print("Write COS error:", e)

    def create_db(self,username,db_name,db_description,db_version,db_remark):
        """
        intro:创建数据集
        :return:
        """
        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=f'{username}_database/{db_name}',
                Body=''
            )
            print(f"Folder 'database' created in bucket '{self.bucket}'")
        except Exception as e:
            print(f"Error creating folder: {e}")

    # def send_code(self, to_phone_number: str):
    #     """
    #     intro:向指定手机号码(to)发送短信验证码
    #     :param to_phone_number:str 指定手机号码
    #     :return:
    #     """
    #     # 初始化
    #     # client = UniSMS("your access key id", "your access key secret") # 若使用简易验签模式仅传入第一个参数即可
    #     client = UniSMS("m8mpM9rU2M4PbFbhy2HtB8fDgfdRgXGQMquodxBvDaAeu2QNV")  # 若使用简易验签模式仅传入第一个参数即可
    #
    #     try:
    #         # 随机生成6为纯数字验证码
    #         code = random.randint(100000, 999999)
    #         # 发送短信
    #         res = client.send({
    #             "to": to_phone_number,
    #             "signature": "余俊瑜测试",
    #             "templateId": "pub_verif_register_ttl",
    #             "templateData": {
    #                 "code": code,
    #                 "ttl": 2
    #             }
    #         })
    #         # print(res.data)
    #         print("Send SMS success!")
    #         return to_phone_number, code
    #     except UniException as e:
    #         print("Send SMS error:", e)

    def create_user_database(self, user_name: str):
        """
        intro:创建个人用户的数据库，用于后续存储数据集、模型等数据
        :return:
        """
        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=user_name + '_database/',
                Body=''
            )
            print(f"Folder '{user_name}' created in bucket '{self.bucket}'")
        except Exception as e:
            print(f"Error creating folder: {e}")

    def generate_engineer_folder(self, user_name: str):
        """
        intro:生成工程项目结构
        :param user_name:
        :return:
        """
        folder_path = user_name + '_database/'
        model_path = folder_path + 'models/'
        Nets_path = folder_path + 'nets/'
        images_path = folder_path + 'images/'
        model_data_path = model_path + 'train_data/'
        self.client.put_object(Bucket=self.bucket, Key=model_path, Body='')
        self.client.put_object(Bucket=self.bucket, Key=Nets_path, Body='')
        self.client.put_object(Bucket=self.bucket, Key=images_path, Body='')
        self.client.put_object(Bucket=self.bucket, Key=model_path, Body='')

    def judge_database_if_exist(self, user_name: str):
        """
        intro:判断该用户是否在COS已有数据库
        :return:True/False
        """
        # 列出指定前缀的对象
        folder_path = user_name + '_database/'
        response = self.client.list_objects(
            Bucket=self.bucket,
            Prefix=folder_path,
        )

        # 检查是否存在指定的文件夹
        for content in response.get('Contents', []):
            if content.get('Key') == folder_path:
                return True
        return False

    def batch_upload(self, folder_path: str, uploadDir: str):
        """
        intro:批量上传数据
        :return:
        """
        g = os.walk(uploadDir)
        # 创建上传的线程池
        pool = SimpleThreadPool()
        for path, dir_list, file_list in g:
            for file_name in file_list:
                srcKey = os.path.join(path, file_name)
                cosObjectKey = srcKey.strip('/')
                # 判断 COS 上文件是否存在
                exists = False
                try:
                    response = self.client.head_object(Bucket=self.bucket, Key=cosObjectKey)
                    exists = True
                except CosServiceError as e:
                    if e.get_status_code() == 404:
                        exists = False
                    else:
                        print("Error happened, reupload it.")
                if not exists:
                    print("File %s not exists in cos, upload it", srcKey)
                    pool.add_task(self.client.upload_file, self.bucket, os.path.join(folder_path, cosObjectKey), srcKey)

        pool.wait_completion()
        result = pool.get_result()
        if not result['success_all']:
            print("Not all files upload sucessed. you should retry")

    def upload_data(self, user_name: str, upload_dir: str, path: str):
        """
        intro:上传数据集
        :return:
        """
        try:
            if self.judge_database_if_exist(user_name) == True:
                response = self.client.upload_file(
                    Bucket=self.bucket,
                    Key=user_name + f'_database/images/{upload_dir}',
                    LocalFilePath=path,
                    EnableMD5=False,
                    progress_callback=None
                )
            else:
                self.create_user_database(user_name)
                self.generate_engineer_folder(user_name)
                response = self.client.upload_file(
                    Bucket=self.bucket,
                    Key=user_name + f'_database/images/{upload_dir}',
                    LocalFilePath=path,
                    EnableMD5=False,
                    progress_callback=None
                )
        except Exception as e:
            print(e)

    def unzip_file_from_cos(self,username, zip_fileanme):
        folder_path = username + '_database/' + 'images/' + zip_fileanme
        DestFilePath = r'D:\PycharmProjects\一站式平台\bishe\zips\{}'.format(zip_fileanme)
        extract_folder = r'D:\PycharmProjects\一站式平台\bishe\dataset'
        self.client.download_file(
            Bucket=self.bucket,
            Key=folder_path,
            DestFilePath=DestFilePath,
            progress_callback=None
        )
        # 解压缩文件
        def support_gbk(zip_file: ZipFile):
            name_to_info = zip_file.NameToInfo
            # copy map first
            for name, info in name_to_info.copy().items():
                real_name = name.encode('cp437').decode('gbk')
                if real_name != name:
                    info.filename = real_name
                    del name_to_info[name]
                    name_to_info[real_name] = info
            return zip_file
        with support_gbk(zipfile.ZipFile(DestFilePath, 'r')) as zip_ref:
            zip_ref.extractall(extract_folder)
        return extract_folder

    def download_net(self, username: str, net_name: str):
        try:
            folder_path = username + '_database/' + 'nets/' + net_name
            local_path = rf'D:\PycharmProjects\一站式平台\bishe\Nets\{net_name}'
            self.client.download_file(
                Bucket=self.bucket,
                Key=folder_path,
                DestFilePath=local_path,
                progress_callback=None
            )
        except Exception as e:
            print(net_name)
            print(e)

    def download_model(self, username: str, modle_name: str):
        try:
            folder_path = username + '_database/' + 'models/' + modle_name
            local_path = rf'D:\PycharmProjects\一站式平台\bishe\Models/{modle_name}'
            self.client.download_file(
                Bucket=self.bucket,
                Key=folder_path,
                DestFilePath=local_path,
                progress_callback=None
            )

        except Exception as e:
            print(modle_name)
            print(e)

    def download_train_data(self, username: str, modle_name: str):
        try:
            folder_path = username + '_database/' + 'models/' + 'train_data/' + modle_name + '.json'
            local_path = rf'D:\PycharmProjects\一站式平台\bishe\Models\train_data\{modle_name}.json'
            self.client.download_file(
                Bucket=self.bucket,
                Key=folder_path,
                DestFilePath=local_path,
                progress_callback=None
            )

        except Exception as e:
            print(modle_name)
            print(e)

    def upload_net(self, user_name: str, model_dir: str, path: str):
        """
        intro:上传模型
        :return:
        """
        """
        intro:上传数据集
        :return:
        """
        try:
            if self.judge_database_if_exist(user_name) == True:
                response = self.client.upload_file(
                    Bucket=self.bucket,
                    Key=user_name + f'_database/nets/{model_dir}',
                    LocalFilePath=path,
                    EnableMD5=False,
                    progress_callback=None
                )
            else:
                self.create_user_database(user_name)
                self.generate_engineer_folder(user_name)
                response = self.client.upload_file(
                    Bucket=self.bucket,
                    Key=user_name + f'_database/nets/{model_dir}',
                    LocalFilePath=path,
                    EnableMD5=False,
                    progress_callback=None
                )
        except Exception as e:
            print(e)

    def upload_model(self, user_name: str, model_dir: str, path: str):
        """
                intro:上传模型
                :return:
                """
        """
        intro:上传数据集
        :return:
        """
        try:
            if self.judge_database_if_exist(user_name) == True:
                response = self.client.upload_file(
                    Bucket=self.bucket,
                    Key=user_name + f'_database/models/{model_dir}',
                    LocalFilePath=path,
                    EnableMD5=False,
                    progress_callback=None
                )

            else:
                self.create_user_database(user_name)
                self.generate_engineer_folder(user_name)
                response = self.client.upload_file(
                    Bucket=self.bucket,
                    Key=user_name + f'_database/models/{model_dir}',
                    LocalFilePath=path,
                    EnableMD5=False,
                    progress_callback=None
                )
        except Exception as e:
            print(e)

    def upload_train_data(self, user_name: str, model_dir: str, path: str):
        """
                intro:上传训练数据
                :return:
        """

        try:
            if self.judge_database_if_exist(user_name) == True:
                response = self.client.upload_file(
                    Bucket=self.bucket,
                    Key=user_name + f'_database/models/train_data/{model_dir}.json',
                    LocalFilePath=path,
                    EnableMD5=False,
                    progress_callback=None
                )

            else:
                self.create_user_database(user_name)
                self.generate_engineer_folder(user_name)
                response = self.client.upload_file(
                    Bucket=self.bucket,
                    Key=user_name + f'_database/models/train_data/{model_dir}.json',
                    LocalFilePath=path,
                    EnableMD5=False,
                    progress_callback=None
                )
        except Exception as e:
            print(e)

    def read_model(self, user_name: str):
        """
        intro:读取模型
        :return:
        """
        folder_path = user_name + '_database/' + 'models/'
        response = self.client.list_objects(Bucket=self.bucket,
                                Prefix=folder_path)
        return response['Contents'][1:]

    def read_net(self, user_name: str):
        """
        intro:读取模型
        :return:
        """
        folder_path = user_name + '_database/' + 'nets/'
        response = self.client.list_objects(Bucket=self.bucket,
                                            Prefix=folder_path)
        return response['Contents'][1:]

    def read_dataset(self, user_name: str):
        """
        intro:读取模型
        :return:
        """
        folder_path = user_name + '_database/' + 'images/'
        response = self.client.list_objects(Bucket=self.bucket,
                                            Prefix=folder_path)
        return response['Contents'][1:]

if __name__ == '__main__':
    # 【初始化COS】
    import sys

    MyCOS = COS()
    MyCOS.unzip_file_from_cos('18059189949','flower.zip')
    # def load_model_architecture(filepath):
    #     with open(filepath, 'r', encoding='utf-8') as file:
    #         code = file.read()
    #     globals_dict = {}
    #     exec(code, globals_dict)
    #     model = globals_dict['CNNModel'](3)  # 这里的 2 是类别数目，根据你的实际情况修改
    #     return model

    # e = load_model_architecture('Nets/CNN.py')
    # print(e)
    # 【读取数据】
    # MyCOS.reset_user_pwd(10086, '123456788')
    # data = MyCOS.read_user_from_dataset()

    # MyCOS.download_net('18059189942', '111.py')
    # print(json.dumps(MyCOS.read_model('18059189942')))

    # 【添加新数据】
    # new_phone_number = '18888888888'
    # new_password = '123456'
    # new_data = pd.DataFrame({
    #     'phoneNumber': [new_phone_number],
    #     'password': [new_password]
    # })
    # MyCOS.write_user_to_dataset(new_data)

    # 【短信验证】
    # phone_number, code = MyCOS.send_code(to_phone_number='17788595485')
    # print(phone_number, code)

    # 【上传数据集】
    # MyCOS.upload_data(user_name='17788595485', upload_dir='img')

    # 【读取数据集】
    # MyCOS.read_img_data(user_name='17788595485', imgdataset='img')
