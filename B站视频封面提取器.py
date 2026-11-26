import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os
import time
import urllib.parse
import re
from PIL import Image, ImageTk
import threading
import io
from datetime import datetime

class BilibiliCoverCrawler:
    def __init__(self, root):
        self.root = root
        self.root.title("B站视频封面爬取工具 v2.0")
        self.root.geometry("1000x700")

        style = ttk.Style()
        style.configure("Title.TLabel", font=("Arial", 12, "bold"))
        style.configure("Status.TLabel", font=("Arial", 10))
        
        self.main_frame = ttk.Frame(root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = ttk.Label(self.main_frame, text="B站视频封面下载器", style="Title.TLabel")
        title_label.pack(pady=(0, 20))
        
        self.create_search_section()
        
        self.create_result_section()

        self.create_status_bar()

        self.cover_dir = "bilibili_covers"
        if not os.path.exists(self.cover_dir):
            os.makedirs(self.cover_dir)

        self.log_file = "crawler_log.txt"

        self.session = requests.Session()
        self.update_session_headers()

        self.timeout = 15
        
    def create_search_section(self):
        search_frame = ttk.LabelFrame(self.main_frame, text="搜索设置", padding="10")
        search_frame.pack(fill=tk.X, pady=(0, 20))

        keyword_frame = ttk.Frame(search_frame)
        keyword_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(keyword_frame, text="搜索关键词:").pack(side=tk.LEFT, padx=(0, 10))
        self.search_entry = ttk.Entry(keyword_frame, width=50)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        count_frame = ttk.Frame(search_frame)
        count_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(count_frame, text="获取数量:").pack(side=tk.LEFT, padx=(0, 10))
        self.count_var = tk.StringVar(value="20")
        count_spinbox = ttk.Spinbox(count_frame, from_=5, to=100, textvariable=self.count_var, width=10)
        count_spinbox.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(count_frame, text="排序方式:").pack(side=tk.LEFT, padx=(0, 10))
        self.sort_var = tk.StringVar(value="totalrank")
        sort_combo = ttk.Combobox(count_frame, textvariable=self.sort_var, width=15, state="readonly")
        sort_combo['values'] = ('totalrank', 'click', 'pubdate', 'dm', 'stow')
        sort_combo.pack(side=tk.LEFT)

        self.search_button = ttk.Button(search_frame, text="开始搜索", command=self.start_search, width=20)
        self.search_button.pack(pady=(10, 0))
        
    def create_result_section(self):

        paned = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        list_frame = ttk.LabelFrame(paned, text="搜索结果列表", padding="5")

        columns = ("序号", "标题", "UP主", "时长", "播放量")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="tree headings", height=15)

        self.tree.column("#0", width=0, stretch=False)
        self.tree.column("序号", width=50, anchor="center")
        self.tree.column("标题", width=300)
        self.tree.column("UP主", width=100)
        self.tree.column("时长", width=80, anchor="center")
        self.tree.column("播放量", width=100, anchor="center")

        for col in columns:
            self.tree.heading(col, text=col)

        tree_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self.on_video_select)
        
        paned.add(list_frame, weight=1)

        preview_frame = ttk.LabelFrame(paned, text="封面预览", padding="10")

        self.cover_image_label = ttk.Label(preview_frame, text="点击左侧列表中的视频预览封面", 
                                          anchor="center", relief="sunken")
        self.cover_image_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.info_text = tk.Text(preview_frame, height=8, width=40, state="disabled", 
                                font=("Arial", 10), wrap="word")
        self.info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        button_frame = ttk.Frame(preview_frame)
        button_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.download_button = ttk.Button(button_frame, text="下载选中封面", 
                                         command=self.download_selected_cover, state="disabled")
        self.download_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.download_all_button = ttk.Button(button_frame, text="下载全部封面", 
                                            command=self.download_all_covers)
        self.download_all_button.pack(side=tk.LEFT)
        
        paned.add(preview_frame, weight=1)
        
        self.video_data = []
        self.current_cover_image = None
        
    def create_status_bar(self):
        status_frame = ttk.Frame(self.main_frame)
        status_frame.pack(fill=tk.X)
        
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, 
                                style="Status.TLabel", relief="sunken", padding=5)
        status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.progress = ttk.Progressbar(status_frame, mode='indeterminate')
        self.progress.pack(side=tk.RIGHT, padx=(5, 0))
        
    def update_session_headers(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        }
        self.session.headers.update(headers)
        
    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        
        self.root.after(0, lambda: self.status_var.set(message[:50]))
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_message + "\n")
        except:
            pass
            
    def start_search(self):
        keyword = self.search_entry.get().strip()
        if not keyword:
            messagebox.showwarning("警告", "请输入搜索关键词")
            return

        for item in self.tree.get_children():
            self.tree.delete(item)
        self.video_data.clear()

        self.search_button.config(state="disabled")
        self.download_all_button.config(state="disabled")
        self.progress.start()

        threading.Thread(target=self.perform_search, args=(keyword,), daemon=True).start()
        
    def perform_search(self, keyword):
        try:
            self.log(f"开始搜索: {keyword}")
            videos = self.search_via_html(keyword)
            
            if not videos:
                self.log("HTML搜索失败，尝试API搜索")
                videos = self.search_via_api(keyword)
            
            if not videos:
                self.log("API搜索失败，尝试备用接口")
                videos = self.search_backup(keyword)
            
            if videos:
                self.video_data = videos
                self.display_video_list(videos)
                self.log(f"搜索完成，找到 {len(videos)} 个视频")
            else:
                self.root.after(0, lambda: messagebox.showerror("错误", 
                    "搜索失败！\n\n可能的原因：\n"
                    "1. 网络连接问题\n"
                    "2. B站反爬虫机制\n"
                    "3. 网站接口变更\n\n"
                    "请检查网络后重试，或稍后再试。"))
                
        except Exception as e:
            self.log(f"搜索过程出错: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror("错误", f"搜索失败: {str(e)}"))
        finally:
            self.root.after(0, self.reset_ui)
            
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
            
            self.log(f"请求搜索页面: {search_url}")
            response = self.session.get(search_url, params=params, timeout=self.timeout)
            response.raise_for_status()
            html_content = response.text
            
            videos = []
            import re
            pattern = r'window\.__INITIAL_STATE__\s*=\s*({.*?});'
            match = re.search(pattern, html_content, re.DOTALL)
            
            if match:
                try:
                    json_str = match.group(1)
                    data = json.loads(json_str)

                    if 'videoData' in data:
                        video_list = data['videoData']
                    elif 'result' in data:
                        video_list = data['result']
                    elif 'data' in data and 'result' in data['data']:
                        video_list = data['data']['result']
                    else:
                        video_list = self.find_video_data(data)
                    
                    if video_list:
                        for video in video_list[:int(self.count_var.get())]:
                            video_info = self.extract_video_info(video)
                            if video_info:
                                videos.append(video_info)
                                
                        if videos:
                            return videos
                            
                except Exception as e:
                    self.log(f"JSON解析失败: {str(e)}")
            
            videos = self.parse_html_videos(html_content, keyword)
            if videos:
                return videos
                
        except Exception as e:
            self.log(f"HTML搜索失败: {str(e)}")
            
        return []
        
    def find_video_data(self, data):
        videos = []
        
        def search_in_dict(obj, depth=0):
            if depth > 5:  
                return []
                
            if isinstance(obj, dict):
                if all(key in obj for key in ['title', 'pic', 'bvid']):
                    return [obj]
                
                results = []
                for value in obj.values():
                    results.extend(search_in_dict(value, depth + 1))
                return results
                
            elif isinstance(obj, list):
                results = []
                for item in obj:
                    results.extend(search_in_dict(item, depth + 1))
                return results
                
            return []
        
        return search_in_dict(data)
        
    def parse_html_videos(self, html_content, keyword):
        videos = []
        patterns = [
            r'"title":"([^"]+)".*?"pic":"([^"]+)".*?"bvid":"([^"]+)".*?"author":"([^"]+)"',
            r'<a[^>]*title="([^"]+)"[^>]*href="[^"]*/(BV[^"/]+)"[^>]*>',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html_content, re.DOTALL)
            for match in matches:
                if len(match) >= 3:
                    if len(match) == 4:
                        title, pic, bvid, author = match
                    else:
                        title, bvid = match[0], match[1]
                        pic = f"https://i0.hdslb.com/bfs/archive/{bvid}.jpg"
                        author = "未知UP主"
                    
                    title = title.replace('\\u002F', '/').replace('\\"', '"')
                    
                    video_info = {
                        'title': title[:100] + "..." if len(title) > 100 else title,
                        'pic': pic if pic.startswith('http') else f'https:{pic}',
                        'bvid': bvid if bvid.startswith('BV') else f'BV{bvid}',
                        'author': author,
                        'duration': '--:--',
                        'play': '--'
                    }
                    videos.append(video_info)
                    
                    if len(videos) >= int(self.count_var.get()):
                        break
        
        return videos
        
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
                
                if not bvid and 'aid' in video:
                    bvid = self.aid_to_bvid(video['aid'])
                
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
        
    def aid_to_bvid(self, aid):
        return f"aid{aid}"
        
    def format_duration(self, duration):
        if isinstance(duration, (int, float)):
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            return f"{minutes}:{seconds:02d}"
        return str(duration)
        
    def format_number(self, num):
        try:
            num = int(num)
            if num >= 10000:
                return f"{num/10000:.1f}万"
            return str(num)
        except:
            return str(num)
        
    def search_via_api(self, keyword):
        try:
            url = "https://api.bilibili.com/x/web-interface/search/all/v2"
            params = {
                'keyword': keyword,
                'page': 1,
                'page_size': int(self.count_var.get())
            }
            
            self.log(f"请求API: {url}")
            response = self.session.get(url, params=params, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0:
                    videos = []
                    for item in data.get('data', {}).get('result', []):
                        if item.get('result_type') == 'video':
                            for video in item.get('data', []):
                                video_info = self.extract_video_info(video)
                                if video_info:
                                    videos.append(video_info)
                    return videos
        except Exception as e:
            self.log(f"API搜索失败: {str(e)}")
            
        return []
        
    def search_backup(self, keyword):
        try:
            url = f"https://api.bilibili.com/x/web-interface/wbi/search/all/v2?keyword={urllib.parse.quote(keyword)}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.bilibili.com/',
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return self.process_search_results(data)
        except:
            pass
            
        return []
        
    def process_search_results(self, data):
        videos = []
        
        if data.get('code') == 0:
            result_data = data.get('data', {})
            
            result_types = ['result', 'list', 'data']
            for result_type in result_types:
                if result_type in result_data:
                    items = result_data[result_type]
                    if isinstance(items, list):
                        for item in items:
                            video_info = self.extract_video_info(item)
                            if video_info:
                                videos.append(video_info)
                    elif isinstance(items, dict) and 'vlist' in items:
                        for item in items['vlist']:
                            video_info = self.extract_video_info(item)
                            if video_info:
                                videos.append(video_info)
        
        return videos[:int(self.count_var.get())]
        
    def display_video_list(self, videos):
        self.root.after(0, lambda: self._update_treeview(videos))
        
    def _update_treeview(self, videos):
        for i, video in enumerate(videos, 1):
            self.tree.insert("", "end", iid=str(i), values=(
                i,
                video['title'],
                video['author'],
                video['duration'],
                video['play']
            ))
        
    def on_video_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
            
        index = int(selection[0]) - 1
        if 0 <= index < len(self.video_data):
            video = self.video_data[index]
            self.display_cover_preview(video)
            self.download_button.config(state="normal")
            
    def display_cover_preview(self, video):
        try:
            info_text = f"标题: {video['title']}\n\n"
            info_text += f"UP主: {video['author']}\n"
            info_text += f"时长: {video['duration']}\n"
            info_text += f"播放量: {video['play']}\n"
            info_text += f"BV号: {video['bvid']}\n\n"
            info_text += f"封面URL:\n{video['pic']}"
            
            self.info_text.config(state="normal")
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(1.0, info_text)
            self.info_text.config(state="disabled")
            
            threading.Thread(target=self.load_cover_image, args=(video['pic'],), daemon=True).start()
            
        except Exception as e:
            self.log(f"显示预览失败: {str(e)}")
            
    def load_cover_image(self, image_url):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.bilibili.com/',
            }
            
            response = requests.get(image_url, headers=headers, timeout=10, stream=True)
            if response.status_code == 200:
                image_data = response.content
                image = Image.open(io.BytesIO(image_data))
                
                max_size = (300, 200)
                image.thumbnail(max_size, Image.LANCZOS)
                
                photo = ImageTk.PhotoImage(image)
                
                self.root.after(0, self._update_cover_image, photo)
                
        except Exception as e:
            self.log(f"加载图片失败: {str(e)}")
            self.root.after(0, lambda: self.cover_image_label.config(
                text=f"图片加载失败\n{str(e)[:30]}..."))
                
    def _update_cover_image(self, photo):
        self.current_cover_image = photo
        self.cover_image_label.config(image=photo, text="")
        
    def download_selected_cover(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选择一个视频")
            return
            
        index = int(selection[0]) - 1
        if 0 <= index < len(self.video_data):
            video = self.video_data[index]
            self.download_cover(video)
            
    def download_all_covers(self):
        if not self.video_data:
            messagebox.showinfo("提示", "没有可下载的视频")
            return
            
        progress_window = tk.Toplevel(self.root)
        progress_window.title("下载进度")
        progress_window.geometry("300x150")
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        ttk.Label(progress_window, text="正在下载封面图片...", padding=20).pack()
        
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(progress_window, variable=progress_var, maximum=len(self.video_data))
        progress_bar.pack(padx=20, pady=(0, 20), fill=tk.X)
        
        status_label = ttk.Label(progress_window, text="准备开始...")
        status_label.pack()
        
        def download_all():
            success_count = 0
            for i, video in enumerate(self.video_data, 1):
                progress_window.after(0, lambda idx=i: progress_var.set(idx))
                progress_window.after(0, lambda v=video: status_label.config(text=f"正在下载: {v['title'][:20]}..."))
                
                if self.download_cover(video, show_message=False):
                    success_count += 1
                
                time.sleep(0.5)  
            
            progress_window.after(0, progress_window.destroy)
            messagebox.showinfo("下载完成", f"成功下载 {success_count}/{len(self.video_data)} 个封面")
        
        threading.Thread(target=download_all, daemon=True).start()
        
    def download_cover(self, video, show_message=True):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.bilibili.com/',
            }
            
            response = requests.get(video['pic'], headers=headers, timeout=10)
            if response.status_code == 200:
                safe_title = re.sub(r'[<>:"/\\|?*]', '_', video['title'][:50])
                filename = f"{video['bvid']}_{safe_title}.jpg"
                filepath = os.path.join(self.cover_dir, filename)

                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                if show_message:
                    messagebox.showinfo("下载成功", f"封面已保存到:\n{filepath}")
                
                self.log(f"封面已保存: {filepath}")
                return True
            else:
                if show_message:
                    messagebox.showerror("下载失败", f"下载失败，HTTP状态码: {response.status_code}")
                return False
                
        except Exception as e:
            if show_message:
                messagebox.showerror("下载失败", f"下载失败: {str(e)}")
            self.log(f"封面下载失败: {str(e)}")
            return False
            
    def reset_ui(self):
        self.search_button.config(state="normal")
        self.download_all_button.config(state="normal" if self.video_data else "disabled")
        self.progress.stop()
        
    def on_closing(self):
        self.session.close()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = BilibiliCoverCrawler(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    app.search_entry.insert(0, " ")
    
    root.mainloop()
