# -*- coding: utf-8 -*-
import os
import re
import time
import requests
import threading
from tkinter import *
from tkinter import filedialog
from requests_toolbelt.multipart import encoder


HOST_ROOT = 'http://192.168.153.128:5000'


class Client:

    def __init__(self, path=''):
        self.session = requests.session()
        self.target_path = path
        self.file_list = []
        self.max_file_len = 0
        self.color = '#09f7f7'
        self.logging = True
        self.current_upload = ''
        self.check_boxes = list()
        self.box_var_list = list()
        self.root = Tk()
        self.root.title('Winux_file_COM')
        self.root.geometry("730x400")
        self.root.resizable(width=False, height=False)
        self.all_selected = IntVar()
        self.body = Frame(self.root, width=370, height=330)
        self.body_scbar_x = Scrollbar(self.body, orient=HORIZONTAL)
        self.body_scbar_y = Scrollbar(self.body)
        self.canv = Canvas(self.body, width=370, height=300, bg=self.color)
        self.block = Frame(self.canv, width=370, bg=self.color)
        self.label = Label(self.root, text='Path:')
        self.target_path_in = Entry(self.root, width=29)
        self.params_input = Entry(self.root, width=22)
        self.select_file_button = Button(text=' ... ', command=self.select_target)
        self.switch_button = Button(text='switch', command=(lambda:
                                                            (lambda b:
                                                             [b.flush_canv() or b.all_selected.set(0)
                                                              for b.target_path in (b.target_path_in.get(),)])(self)))
        
        self.params_button = Button(text='Params', relief='ridge', cursor='hand2')
        self.upload_button = Button(text='Upload', command=lambda: (lambda b: b.create_action_task('upload'))(self))
        self.fetch_button = Button(text='Fetch', command=lambda: (lambda b: b.create_action_task('download'))(self))
        self.request_button = Button(text='Request Convert', command=(lambda:
                                                                      (lambda b:
                                                                       b.create_action_task('convert'))(self)))
        self.selectAll_button = Checkbutton(text='select all', variable=self.all_selected,
                                            command=(lambda:
                                                     (lambda b:
                                                      [(box.select() if b.all_selected.get() else box.deselect())
                                                       # and b.canv.update()
                                                       for box in b.check_boxes])(self)))
        self.log_frame = Frame(self.root)
        self.log_canvas = Canvas(self.log_frame, bg='#44BBA3', width=300, height=150)
        self.log_scb_x = Scrollbar(self.log_frame, orient=HORIZONTAL)
        self.log_scb_y = Scrollbar(self.log_frame)
        self.finished_log = ''
        self.going_log = ''
        # 文件列表区域的鼠标滚动事件
        self.canv.bind("<Enter>", (lambda event:(lambda ins: ins.block.bind_all("<MouseWheel>", ins.file_list_on_mousewheel))(self)))
        self.canv.bind("<Leave>", (lambda event:(lambda ins: ins.block.unbind_all("<MouseWheel>"))(self)))
        # log区域的鼠标滚动事件
        self.log_frame.bind("<Enter>", (lambda event:(lambda ins: ins.log_canvas.bind_all("<MouseWheel>", ins.log_zone_on_mousewheel))(self)))
        self.log_frame.bind("<Leave>", (lambda event:(lambda ins: ins.log_canvas.unbind_all("<MouseWheel>"))(self)))
        # 用一标记变量记录ctl是否按下，按住ctl滚轮将控制横向滚动
        self.roll_switch = False
        self.root.bind('<KeyPress-Control_L>', (lambda event: (lambda ins: [None for ins.roll_switch in (True, )])(self)))
        self.root.bind('<KeyRelease-Control_L>', (lambda event: (lambda ins: [None for ins.roll_switch in (False, )])(self)))
        

    def layout(self):
        self.label.place(x=5, y=20)
        self.target_path_in.place(x=45, y=19)
        self.select_file_button.place(x=265, y=16)
        self.switch_button.place(x=295, y=16)
        self.body.place(x=0, y=50)
        self.body_scbar_x.pack(side=BOTTOM, fill=X)
        self.body_scbar_y.pack(side=RIGHT, fill=Y)
        self.params_input.place(x=400, y=50)
        self.params_button.place(x=600, y=46)
        self.selectAll_button.place(x=400, y=100)
        self.upload_button.place(x=400, y=150)
        self.request_button.place(x=490, y=150)
        self.fetch_button.place(x=640, y=150)
        self.canv.pack()
        self.canv.create_window((0, 0), window=self.block, anchor='nw')
        self.log_scb_x.pack(side=BOTTOM, fill=X)
        self.log_scb_y.pack(side=RIGHT, fill=Y)
        self.log_canvas.pack()
        self.log_frame.place(x=400, y=210)
        self.log_block_relate()
        # 窗口被关闭时，停掉刷新log的线程
        self.root.bind('Destroy', lambda: (lambda ins: [None for ins.logging in (False, )])(self))

    def canv_relate(self):
        '''
        刷新装文件复选框列表的画布时，需要更新画布的滚动关联
        '''
        self.body_scbar_x.config(command=self.canv.xview)
        self.body_scbar_y.config(command=self.canv.yview)
        self.canv.config(xscrollcommand=self.body_scbar_x.set, yscrollcommand=self.body_scbar_y.set,
                         scrollregion=self.canv.bbox('all'))

    def log_block_relate(self):
        '''
        log区域的滚动关联
        '''
        self.log_scb_x.config(command=self.log_canvas.xview)
        self.log_scb_y.config(command=self.log_canvas.yview)
        self.log_canvas.config(xscrollcommand=self.log_scb_x.set, yscrollcommand=self.log_scb_y.set)

    def select_target(self):
        selected_path = filedialog.askopenfilename(filetypes=[('音频文件', '.wav')])
        selected_dir_path = os.path.dirname(selected_path)
        selected_file_name = os.path.basename(selected_path)
        self.target_path = selected_dir_path
        self.target_path_in.delete(0, 'end')
        self.target_path_in.insert(0, selected_dir_path)
        self.flush_canv()
        for i in self.check_boxes:
            if i.cget('text') == selected_file_name:
                i.select()
                break

    def flush_canv(self):
        '''
        刷新文件列表的父组件
        '''
        # 清空文件列表中的所有元素
        self.clear_check_boxes()
        if os.path.exists(self.target_path):
            self.file_list = [x for x in os.listdir(self.target_path) 
                                if os.path.isfile(os.path.join(self.target_path, x)) and x.endswith('.wav')]
            if not self.file_list:
                return
            # 计算文件名宽度，设置所有checkbutton的长度为最长文件名，以确保正常显示所有文件名
            # checkbutton的文本字体需要使用等宽字体是关键，但是，但是，但是 不适用中文名称的文件，待优化
            self.max_file_len = max(map(len, self.file_list)) + 3
            for file_name in self.file_list:
                v = IntVar()
                box = Checkbutton(self.block, text=file_name, bg=self.color, justify=LEFT, relief='groove', anchor='w',
                                  width=self.max_file_len, font='monospace', variable=v, command=self.relate_select_all_check_box)
                box.pack()
                self.check_boxes.append(box)
                self.box_var_list.append(v)
            self.canv.update()
            self.canv_relate()

    def log_zone_on_mousewheel(self, event):
        scroll = self.log_canvas.xview_scroll if self.roll_switch else self.log_canvas.yview_scroll
        scroll(0-(int(event.delta/80)), "units")

    def file_list_on_mousewheel(self, event):
        scroll = self.canv.xview_scroll if self.roll_switch else self.canv.yview_scroll
        scroll(0-(int(event.delta/80)), "units")

    def clear_check_boxes(self):
        for i in self.check_boxes:
            i.destroy()
        self.check_boxes = list()
        self.box_var_list = list()
    
    def relate_select_all_check_box(self):
        '''
        将文件列表的复选框状态同步到全选复选框
        当全选后再取消勾选某个文件，全选复选框会自动取消勾选
        当列表中的所有文件都被逐个选中时，全选复选框会自动切换为勾选状态
        '''
        self.all_selected.set(1 if all([v.get() for v in self.box_var_list]) else 0)

    def get_selected(self):
        return [self.check_boxes[index].cget('text')
                for index in range(len(self.box_var_list))
                if self.box_var_list[index].get()]

    def flush_log(self):
        '''
        更新log区域显示的方法，将通过多线程运行
        由于会有进度条的存在，所以log会存在中间字符增量，采取已完成log和正在进行log的拼接方式
        属性finished_log为已完成log，属性going_log为正在进行的log，通常是进度条字符
        '''
        while self.logging:
            self.log_canvas.delete('all')
            self.log_canvas.create_text(15, 15, text=self.finished_log+self.going_log, anchor='nw', font=('monospace', 8))
            self.log_canvas.config(scrollregion=self.log_canvas.bbox('all'))
            self.log_canvas.update()
            time.sleep(0.3)

    def log(self, finished='', going=''):
        '''
        调用本方法可添加或更新log
        '''
        if finished:
            if not finished.endswith('\n'):
                finished += '\n'
            self.finished_log += finished
        if going:
            self.going_log = going

    def run(self):
        self.layout()
        self.flush_canv()
        log_task = threading.Thread(target=self.flush_log)
        log_task.start()
        self.root.mainloop()
        self.logging = False

    def lock_button(self):
        '''
        上传，转换，下载操作必须串行，当有任何一个操作正在进行时，锁住所有相关按键。
        '''
        self.upload_button.config(state=DISABLED)
        self.fetch_button.config(state=DISABLED)
        self.request_button.config(state=DISABLED)
        # 有任务进行时，鼠标状态变为转圈
        self.root.config(cursor='watch')

    def unlock_button(self):
        self.upload_button.config(state=ACTIVE)
        self.fetch_button.config(state=ACTIVE)
        self.request_button.config(state=ACTIVE)
        # 没有任务进行时，鼠标状态恢复正常
        self.root.config(cursor='arrow')

    def upload_progress_callback(self, monitor):
        rate = int(monitor.bytes_read / monitor.len * 100)
        self.going_log = '   uploading {}: [{}]'.format(self.current_upload, ">>"*(rate//10)+"__"*(10-rate//10))

    def upload(self):
        self.lock_button()
        self.finished_log += '[Upload]\n'
        file_list = self.get_selected()
        files = {name: open(os.path.join(self.target_path, name), 'rb') for name in file_list}
        if not files:
            self.log(finished='No file was selected')
            self.unlock_button()
            return
        try:
            for file_name, file_handler in files.items():
                self.current_upload = file_name
                e = encoder.MultipartEncoder(
                    fields={file_name: (file_name, file_handler, 'audio/wav')}
                )
                # 上传进度条功能，进度条文本拼接在回调函数中实现
                m = encoder.MultipartEncoderMonitor(e, self.upload_progress_callback)
                resp = self.session.post(url='{}/upload'.format(HOST_ROOT), data=m,
                                         headers={"Content-Type": m.content_type})
                if resp.ok:
                    self.finished_log += f'   {file_name} Done\n'
                else:
                    self.finished_log += f'   {file_name} Error'
                    # TODO should alert and maybe it is necessary to interrupt upload action
        finally:
            self.current_upload = ''
            self.going_log = ''
            self.unlock_button()

    def request_convert(self):
        self.lock_button()
        self.log(finished='[Convert]\n')
        if not self.get_selected():
            self.log(finished='No file was selected to convert.')
            self.unlock_button()
            return
        # 将目前选中的所有文件名称列表以及附带参数传给web server端
        json_data = {'names': self.get_selected(), 'params': self.params_input.get()}
        resp = self.session.post(f'{HOST_ROOT}/convert', json=json_data)
        # print(resp.status_code, resp.text)  # 调试用
        if resp.ok:
            self.log(finished='convert finished')
        else:
            self.log(finished='convert error')
        self.unlock_button()

    def download(self):
        self.lock_button()
        self.log(finished='[Download]')
        if not self.get_selected():
            self.log(finished='No file was selected.')
            self.unlock_button()
            return
        # 下载时用的文件名和源文件名称有差异，使用前缀与后端处理后的前缀相同即可
        target_file_name_list = ['converted_'+i for i in self.get_selected()]
        try:
            for file_name in target_file_name_list:
                # 测试server接口发现需要额外转义的字符为('/', '?', '%', '#')，由于windows系统中文件名不允许包含('/', '?')，故只需要对 %和# 进行转义
                resp = self.session.get('{}/download/{}'.format(HOST_ROOT, file_name.replace('%', '%25').replace('#', '%23')), stream=True)
                if not resp.ok:
                    self.log(finished=f'   {file_name} Error')
                    continue
                    # TODO alert msg
                total_size = resp.headers.get('Content-Length', '0')
                if total_size == '0':
                    self.log(finished=f'   {file_name} Invalid [Content-Length]')
                    # TODO alert msg
                    continue
                chunk_size = int(total_size) // 10 + 1
                with open(os.path.join(self.target_path, file_name), 'wb') as f:
                    counter = 1
                    for chunk in resp.iter_content(chunk_size=chunk_size):
                        f.write(chunk)
                        # 下载进度条实现
                        self.log(going='   downloading {}: [{}]'.format(file_name, '>>'*counter+"__"*(10-counter)))
                        counter += 1
                self.log(finished=f'   {file_name} Done')
        finally:
            self.going_log = ''
            self.unlock_button()

    def create_action_task(self, action):
        '''
        用于创建上传，下载，请求转换的多线程任务，关联到相关按键
        '''
        act_map = {'upload': self.upload,
                   'convert': self.request_convert,
                   'download': self.download}
        task = threading.Thread(target=act_map[action])
        task.start()


if __name__ == '__main__':
    ins = Client()
    ins.run()
