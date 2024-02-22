# -*- coding: utf-8 -*-
import datetime
import base64
import shutil
import sys
import os
import re

from flask import Flask, make_response, request

app = Flask(__name__)
print(os.path.dirname(os.path.abspath(__file__)))
root_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'winux_file_com_root')
if os.path.exists(root_path):
    if os.path.isdir(root_path):
        shutil.rmtree(root_path)
    else:
        print('So coincindence, maybe you should rename the file: {}'.format(root_path))
        sys.exit(1)
os.mkdir(root_path)


@app.route("/upload", methods=['POST'])
def receive():
    resp = make_response('hello')
    if not request.cookies.get('id'):
        # 将客户端ip地址拼接时间戳作为当前会话的工作目录末端文件夹名称，将该文件夹名称通过base64编码后，作为cookie以维持会话。
        store_dir = '{}:{}'.format(request.remote_addr, datetime.datetime.now().isoformat())
        resp.set_cookie('id', base64.b64encode(store_dir.encode('utf8')).decode('utf8'))
    else:
        store_dir = base64.b64decode(request.cookies.get('id').encode('utf8')).decode('utf8')
    if not os.path.exists(os.path.join(root_path, store_dir, 'input')):
        os.makedirs(os.path.join(root_path, store_dir, 'input'))
    print(request.files)
    for file_name, handler in request.files.items():
        with open(os.path.join(root_path, store_dir, 'input', file_name), 'wb') as f:
            f.write(handler.read())
    return resp


@app.route("/convert", methods=["POST"])
def convert():
    executor_path = os.path.join(root_path, 'wav_remix')
    ticket = request.cookies.get('id')
    # 没有cookie的非upload请求，不予服务，上传文件是基本条件，上传文件会自动获取cookie
    if not ticket:
        return 'You have no ticket!', 400
    label = base64.b64decode(ticket.encode('utf8')).decode('utf8')
    output_path = os.path.join(root_path, label, 'output')
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    file_list = request.json.get('names')
    # 可根据业务需求添加对文件处理的逻辑，这里仅将client请求传入的参数获取，并将原文件复制到output目录下
    params = request.json.get('params') or '可在这里将非常常用的参数设置为默认'
    for file_name in file_list:
        input_path = os.path.join(root_path, label, 'input', file_name)
        output_path = os.path.join(root_path, label, 'output', f'converted_{file_name}')
        output_dir = os.path.join(root_path, label, 'output')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        if not os.path.exists(input_path):
            return 'The specified file: {} was not uploaded.'.format(file_name), 400
        command = 'cp {} {}'.format(input_path, output_path)
        if os.system(command):
            return 'Convert command failed', 500
    return 'OK', 200


@app.route("/download/<string:file_names>", methods=['GET'])
def send(file_names):
    file_list = file_names.split(';')
    ticket = request.cookies.get('id')
    if not ticket:
        return 'You have no ticket', 400
    label = base64.b64decode(ticket.encode('utf8')).decode('utf8')
    output_dir_path = os.path.join(root_path, label, 'output')
    print([os.path.join(output_dir_path, name) for name in file_list])
    if not all([os.path.exists(os.path.join(output_dir_path, name)) for name in file_list]):
        return 'Some files are not found, please check.', 400
    payload = b''
    for name in file_list:
        with open(os.path.join(output_dir_path, name), 'rb') as f:
            payload += f.read()
    resp = make_response(payload)
    return resp, 200


app.run(host='0.0.0.0')
