# Python 课程设计报告：B站视频封面提取器

**课程名称：** Python 程序设计
**学号：** ROB240235
**姓名：** 叶铭杨
**同组成员（如有）：** 陈佳灏 (分工：markdown文档编写，PPT制作，数据核心结构及封面下载封面下载核心编写)
**提交日期：** 2025年12月24日

---

## 1. 项目背景与目标
> *此处简要介绍为什么要做这个项目，解决了什么问题，或者实现了什么有趣的功能。*

**B站没有直接提供封面下载入口，难以下载封面，制作提取器使封面的下载得到了便利，降低了操作门槛，原先需要用第三方软件才能够下载下来，现在可以一键提取高清原图，并且保证了图片质量，避免了截图导致的画质受损，有的第三方软件下载封面会压缩封面画质，而提取器不用。** 


## 2. 系统设计

### 2.1 技术栈选型
*   **开发语言：** python
*   **GUI 框架：** Tkinter+ttk组合
*   **数据存储：** JSON 文件 /re
*   **外部接口/库：** Requests/urllib.parse

### 2.2 功能模块说明
> *简单描述程序包含哪些主要模块或功能点。*

1.  **关键词搜索模块：** 支持同B站视频的关键词搜索
2.  **[封面预览]：** [能够对爬取的封面数据进行预览]
3.  **[封面下载]：** [能够将爬取的封面内容以图片的形式进行保存]

## 3. 核心代码解析 (关键环节)
> *注意：不要粘贴全部代码！只粘贴最核心、最能体现你水平的代码片段（约3-5个片段），并加上注释说明。*



### 3.1 核心功能：[搜索功能]

    def search_via_html(self, keyword):
    try:
        search_url = f"https://search.bilibili.com/all"
        params = {
            'keyword': keyword,
            'from_source': 'webtop_search',
            'spm_id_from': '333.1007',
            'search_source': '5',
            'page': 1,
            'o': 30
        }
        
        response = self.session.get(search_url, params=params, timeout=self.timeout)
        response.raise_for_status()
        
        html_content = response.text
        
        videos = []
        pattern = r'window\.__INITIAL_STATE__\s*=\s*({.*?});'
        match = re.search(pattern, html_content, re.DOTALL)
        
        if match:
            json_str = match.group(1)
            data = json.loads(json_str)

   
**代码原理解析：** 本段通过解析B站搜索页面的HTML内容来获取视频信息的方法，关键词搜索通过URL参数传递搜索条件，避免直接调用API可能存在的限制。

### 3.2 核心功能：[视频信息提取]

    def extract_video_info(self, video):
    try:
        if isinstance(video, dict):
            title = video.get('title') or video.get('name') or ''
            pic = video.get('pic') or video.get('cover') or video.get('face') or ''
            bvid = video.get('bvid') or video.get('aid') or ''
            author = video.get('author') or video.get('owner', {}).get('name') or '未知UP主'
            duration = video.get('duration', '--:--')
            play = video.get('play') or video.get('view') or video.get('click') or '--'
            
            if pic and not pic.startswith('http'):
                pic = f'https:{pic}' if pic.startswith('//') else f'https://{pic}'
            
            if title and pic and bvid:
                return {
                    'title': title[:100] + "..." if len(title) > 100 else title,
                    'pic': pic,
                    'bvid': bvid,
                    'author': author,
                    'duration': self.format_duration(duration),
                    'play': self.format_number(play)
                }
    except Exception as e:
        self.log(f"提取视频信息失败: {str(e)}")
    
    return None

**代码原理解析：** （try)处理不同类型的视频数据格式，确保单个视频数据异常也不会影响结果，以及将封URL标准化处理，确保所有封面的URL都是HTTP链接

## 4. 遇到的重难点与解决思路 (必填)

> *这是老师评分的重要依据，请真实记录你在开发过程中遇到的报错和困难，以及你是如何解决的。*

#### 困难 1：[例如 图片无法显示]

- **问题描述：** 运行程序时报错 `image "pyimage1" doesn't exist`，或者图片显示一片空白。
- **分析过程：** 查阅资料发现，Tkinter 的 PhotoImage 对象如果在函数内部定义，会被 Python 的垃圾回收机制回收。
- **解决方案：** 将图片对象定义为类的成员变量 `self.img = ...`，保持引用，问题解决。

#### 困难 2：[请求requests库错误]

- **问题描述：** 软件运行中无法调用requests库，无法正常下载requests库。
- **分析过程：** 上网搜索疑似python安装时为能完整安装
- **解决方案：**重新安装python解释器，并使用pip安装requests库。

#### 困难 3：[数据爬取错误]

- **问题描述：** 爬取过程中出现412错误。
- **分析过程：** 查阅资料发现，412错误常见问题为请求头不完整，缺少必要的cookie。
- **解决方案：** 添加完整的请求头，并使用官方的API。



## 5. 项目运行展示

> *请提供 2-3 张程序运行时的关键截图，证明程序可以正常运行。*

![主界面截图]<img src="0.jpg" widh="300" height="300" style="display" margin:0> 
     *图1：系统启动主界面*

![功能演示截图]<img src="1.jpg" widh="300" height="300" style="display"> 
*图2：B站视频爬取结果*

## 6. 总结与反思

- **不足之处：** ：目前 UI 界面比较简陋，没有做美化；搜索时间较长；
- **心得体会：** 通过本次大作业，深入理解了Python生态在桌面应用开发中的优势和局限，也积累了处理反爬机制和API变化的实战经验，了解到GUI框架的使用和多线程处理，同时也知道了自身的不足，明确了未来的学习方向
## 7. 附录：源码地址

https://github.com/Elysia-317/elysia.git
