#### 工具简介

本工具名为Winux_file_COM，由其英文全程（Win and Linux file communication）精简而来。

功能如其名，产生该工具的主要需求为：工作环境与生产环境不一致，例如在window系统工作，linux系统生产，而有些对文件处理的操作只能在生产环境下运行，频繁切换工作环境会使得工作效率低下，且有较高概率出错。通过该工具可实现将文件传输到生产环境，并选择生产环境端提供的功能接口进行相应操作，完成后可在工作环境端下载输出文件，最终达到不切换工作环境实现跨环境处理文件的目的，高效而准确。

#### 结构及实现介绍

工具为CS架构，初始调试及功能实现是按照windows作为client端，linux作为server端。使用http协议完成文件的传输以及操作参数的传递，使用简单cookie实现会话。server端并未实现具体的需要对上传的文件进行的操作，可根据需要编写相关视图函数。UI界面使用轻量级官方库tkinter实现，客户端应用层逻辑基本完善，包含上传下载进度条，预览选取文件和目录，日志显示等。

#### 工具工作流程简介

主要流程为选中源文件，点击upload上传所有选中源文件，点击convert请求后端对当前选中文件进行处理（这里仅将源文件复制并加前缀）点击download时，向后端请求获取以client端选中文件为源文件的输出。每次客户端被打开到客户端被关闭期间，被作为一次http会话，首次发起upload请求时，server端会根据客户端相关信息配发cookie。

#### 工具界面预览及简介

![image-20240223010745180](.\image-20240223010745180.png)