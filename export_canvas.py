import os
import re
import time
import random
import threading
import requests
import hashlib
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from canvasapi import Canvas
from canvasapi.exceptions import CanvasException, Forbidden
from markdownify import markdownify as md
from bs4 import BeautifulSoup, NavigableString
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
from rich.panel import Panel

# ================= 配置区域 =================
API_URL = "https://onlinelearn.sim.edu.sg"
API_KEY = ""  # 在这里填入 Token，或者运行时输入

# 并发与限流配置
WORKER_COUNT = 16
INITIAL_REQUEST_INTERVAL = 0.1
MIN_REQUEST_INTERVAL = 0.01
MAX_REQUEST_INTERVAL = 5.0

# 重试与退避配置
MAX_RETRIES = 5
BASE_BACKOFF_TIME = 1.0
BACKOFF_FACTOR = 2.0
JITTER_RANGE = 0.5

# 防火墙应对策略
RATE_LIMIT_COOLDOWN = 30.0
SUCCESS_THRESHOLD_TO_SPEEDUP = 50
SPEEDUP_FACTOR = 0.9
SLOWDOWN_FACTOR = 2.0
# ===========================================

console = Console()

class RateLimiter:
    """线程安全的动态速率限制器"""
    def __init__(self, initial_interval):
        self.interval = initial_interval
        self.lock = threading.Lock()
        self.last_request_time = 0
        self.success_count = 0
        self.is_throttled = False
        self.throttle_end_time = 0

    def acquire(self):
        while True:
            sleep_duration = 0
            with self.lock:
                current_time = time.time()
                if self.is_throttled:
                    if current_time < self.throttle_end_time:
                        sleep_duration = min(self.throttle_end_time - current_time, 1.0)
                    else:
                        self.is_throttled = False
                        console.log("[bold green]系统[/] 冷却结束，恢复请求。")
                
                if sleep_duration == 0:
                    time_since_last = current_time - self.last_request_time
                    if time_since_last < self.interval:
                        sleep_duration = self.interval - time_since_last
                    else:
                        self.last_request_time = time.time()
                        return

            if sleep_duration > 0:
                time.sleep(sleep_duration)

    def report_success(self):
        with self.lock:
            if self.is_throttled: return
            self.success_count += 1
            if self.success_count >= SUCCESS_THRESHOLD_TO_SPEEDUP:
                new_interval = max(self.interval * SPEEDUP_FACTOR, MIN_REQUEST_INTERVAL)
                if new_interval < self.interval:
                    self.interval = new_interval
                self.success_count = 0

    def report_soft_throttle(self):
        with self.lock:
            self.interval = min(self.interval * SLOWDOWN_FACTOR, MAX_REQUEST_INTERVAL)
            self.success_count = 0
            console.log("[bold yellow]警告[/] 速率过快，自动降速。")

    def report_hard_throttle(self):
        with self.lock:
            if self.is_throttled: return
            self.is_throttled = True
            self.throttle_end_time = time.time() + RATE_LIMIT_COOLDOWN
            self.interval = MAX_REQUEST_INTERVAL
            self.success_count = 0
            console.log(f"\n[bold red]严重警告[/] 触发防火墙！暂停 {RATE_LIMIT_COOLDOWN} 秒...")


class APIClient:
    def __init__(self, canvas_obj, rate_limiter):
        self.canvas = canvas_obj
        self.rate_limiter = rate_limiter

    def call(self, func, *args, **kwargs):
        retries = 0
        while True:
            try:
                self.rate_limiter.acquire()
                result = func(*args, **kwargs)
                self.rate_limiter.report_success()
                return result
            except (CanvasException, Forbidden) as e:
                err_str = str(e).lower()
                if "rate limit" in err_str or "429" in err_str:
                    self.rate_limiter.report_soft_throttle()
                    time.sleep(1) 
                    continue
                elif "403 forbidden" in err_str or "captcha" in err_str:
                    self.rate_limiter.report_hard_throttle()
                    continue
                else:
                    console.log(f"[bold red]API错误[/] {e}")
                    raise e
            except Exception as e:
                if retries >= MAX_RETRIES:
                    console.log(f"\n[bold red]失败[/] 达到最大重试次数: {e}")
                    raise e
                retries += 1
                sleep_time = BASE_BACKOFF_TIME * (BACKOFF_FACTOR ** (retries - 1)) + random.uniform(0, JITTER_RANGE)
                time.sleep(sleep_time)


class ThreadSafeCourseStructure:
    def __init__(self):
        self.lock = threading.Lock()
        self._structure = [] 
        self.item_details = {} 

    def add_module_data(self, module_obj, items_list):
        items_list.sort(key=lambda x: x.position if hasattr(x, 'position') else 999)
        with self.lock:
            self._structure.append((module_obj, items_list))

    def get_ordered_structure(self):
        with self.lock:
            self._structure.sort(key=lambda x: x[0].position if hasattr(x[0], 'position') else 999)
            return list(self._structure)

    def get_fetchable_items_map(self):
        items_map = {}
        with self.lock:
            for _, item_list in self._structure:
                for item in item_list:
                    if item.type in ['Page', 'File', 'Assignment']:
                        items_map[item.id] = item
        return items_map

    def save_item_detail(self, item_id, content):
        with self.lock:
            self.item_details[item_id] = content

    def get_item_detail(self, item_id):
        with self.lock:
            return self.item_details.get(item_id, "")

def download_image(img_url, images_dir, api_key):
    """下载图片并保存到本地，返回相对路径文件名"""
    try:
        if not img_url.startswith('http'):
            return img_url 

        url_hash = hashlib.md5(img_url.encode('utf-8')).hexdigest()
        
        parsed = urlparse(img_url)
        path_ext = os.path.splitext(parsed.path)[1]
        if not path_ext or len(path_ext) > 5:
            path_ext = ".png" 
        
        filename = f"{url_hash}{path_ext}"
        file_path = os.path.join(images_dir, filename)
        relative_path = f"images/{filename}"

        if os.path.exists(file_path):
            return relative_path

        headers = {'Authorization': f'Bearer {api_key}'} if api_key else {}
        
        response = requests.get(img_url, headers=headers, stream=True, timeout=10)
        if response.status_code == 200:
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            return relative_path
        else:
            return img_url
            
    except Exception as e:
        return img_url

def process_html_with_bs4(html_content, images_dir, api_key):
    """
    使用 BeautifulSoup 解析 HTML:
    1. 下载图片并替换 src。
    2. 保留原有的 width/height/style 属性。
    3. 使用 Placeholder 策略保护 img 标签不被 markdownify 转换成 ![]()。
    """
    if not html_content: return "", {}
    
    soup = BeautifulSoup(html_content, 'html.parser')
    placeholders = {}
    
    images = soup.find_all('img')
    
    for idx, img in enumerate(images):
        original_src = img.get('src')
        if original_src:
            if images_dir:
                new_src = download_image(original_src, images_dir, api_key)
                img['src'] = new_src
            
        existing_style = img.get('style', '')
        safe_style = f"{existing_style}; max-width: 100%; object-fit: contain;"
        
        if 'height' not in str(existing_style) and not img.get('height'):
             safe_style += " height: auto;"

        img['style'] = safe_style
        img['loading'] = "lazy" 

        placeholder_key = f"IMGPH{idx}RAND{random.randint(1000,9999)}"
        img_html_str = str(img)
        placeholders[placeholder_key] = img_html_str
        
        img.replace_with(NavigableString(placeholder_key))

    return str(soup), placeholders

def html_to_md(html_content, images_dir=None, api_key=None):
    if not html_content: return ""
    try:
        processed_html, placeholders = process_html_with_bs4(html_content, images_dir, api_key)

        md_text = md(processed_html, heading_style="ATX", strip=['script', 'style'])
        
        for key, html_tag in placeholders.items():
            md_text = md_text.replace(key, html_tag)
            
        return md_text
    except Exception as e:
        return f"> [转换错误] {e}"

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|\n]', "", name).strip()

def task_get_module_items(api_client, module_obj):
    return list(api_client.call(module_obj.get_module_items))

def task_fetch_item_content(api_client, course, item, images_dir, api_key):
    content_md = ""
    try:
        if item.type == 'Page':
            page = api_client.call(course.get_page, item.page_url)
            if hasattr(page, 'body') and page.body:
                content_md = html_to_md(page.body, images_dir, api_key)
                content_md += f"\n\n> [原网页链接]({item.html_url})\n"

        elif item.type == 'File':
            f_obj = api_client.call(course.get_file, item.content_id)
            content_md += f"- **文件名**: `{f_obj.filename}`\n"
            content_md += f"- **下载链接**: [点击下载]({f_obj.url})\n"
            content_md += f"- *Size: {f_obj.size / 1024:.2f} KB*\n"

        elif item.type == 'Assignment':
            assignment = api_client.call(course.get_assignment, item.content_id)
            content_md += f"- **Due**: {assignment.due_at}\n"
            if hasattr(assignment, 'description') and assignment.description:
                content_md += f"\n--- 作业说明 ---\n"
                content_md += html_to_md(assignment.description, images_dir, api_key)
                content_md += f"\n---\n"
            content_md += f"- [作业链接]({item.html_url})\n"
    except Exception as e:
        content_md = f"> ⚠️ 解析内容出错: {e}\n"
        
    return content_md

def write_markdown_file(file_path, course, structure_data):
    ordered_structure = structure_data.get_ordered_structure()
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"# {course.name}\n\n")
        f.write(f"**Course Code**: {getattr(course, 'course_code', 'N/A')}\n")
        f.write(f"**Exported at**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("---\n\n")

        f.write("## 📑 目录 (Table of Contents)\n\n")
        for module_obj, items in ordered_structure:
            mod_id = f"mod-{module_obj.id}"
            mod_name = module_obj.name if hasattr(module_obj, 'name') else "Unnamed Module"
            f.write(f"- [{mod_name}](#{mod_id})\n")
            
            for item in items:
                item_id = f"item-{item.id}"
                title = item.title if hasattr(item, 'title') else "Untitled"
                if item.type in ['Page', 'File', 'Assignment', 'ExternalUrl']:
                    f.write(f"  - [{title}](#{item_id})\n")
        
        f.write("\n---\n\n")

        for module_obj, items in ordered_structure:
            mod_id = f"mod-{module_obj.id}"
            mod_name = module_obj.name if hasattr(module_obj, 'name') else "Unnamed Module"
            
            f.write(f'<span id="{mod_id}" style="display:block; margin-top:-60px; padding-top:60px;"></span>\n')
            f.write(f"## 📂 Module: {mod_name}\n\n")
            
            for item in items:
                item_id = f"item-{item.id}"
                title = item.title if hasattr(item, 'title') else "Untitled"
                indent = "###"
                
                f.write(f'<span id="{item_id}" style="display:block; margin-top:-60px; padding-top:60px;"></span>\n')

                if item.type == 'SubHeader':
                    f.write(f"{indent} 📌 {title}\n\n")
                elif item.type == 'ExternalUrl':
                     f.write(f"{indent} 🔗 Link: {title}\n\n")
                     f.write(f"- 跳转链接: [{item.external_url}]({item.external_url})\n\n")
                elif item.type in ['Page', 'File', 'Assignment']:
                    icon = {'Page': '📄', 'File': '📎', 'Assignment': '📝'}.get(item.type, '')
                    f.write(f"{indent} {icon} {item.type}: {title}\n\n")
                    detail = structure_data.get_item_detail(item.id)
                    f.write(detail + "\n\n")
                else:
                    f.write(f"{indent} {title} ({item.type})\n")
                    if hasattr(item, 'html_url'): f.write(f"- [链接]({item.html_url})\n")
                    f.write("\n")
            f.write("---\n\n")

def process_course_fully_parallel(api_client, course, base_dir, executor, download_imgs=False, api_key=None):
    course_safe_name = sanitize_filename(course.name)
    course_dir = os.path.join(base_dir, course_safe_name)
    if not os.path.exists(course_dir): os.makedirs(course_dir)
    
    images_dir = None
    if download_imgs:
        images_dir = os.path.join(course_dir, "images")
        if not os.path.exists(images_dir):
            os.makedirs(images_dir)
    
    file_path = os.path.join(course_dir, f"{course_safe_name}.md")

    console.rule(f"[bold blue]处理课程: {course.name}")
    if download_imgs:
        console.print(f"[dim]图片将保存至: {images_dir}[/]")

    structure_data = ThreadSafeCourseStructure()
    
    try:
        modules = list(api_client.call(course.get_modules))
    except Exception as e:
        console.print(f"[bold red]无法获取课程模块: {e}")
        return

    if not modules:
        console.print("[yellow]该课程没有模块，跳过。")
        return

    future_to_module = {}
    for module in modules:
        f = executor.submit(task_get_module_items, api_client, module)
        future_to_module[f] = module

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeRemainingColumn(),
        console=console,
        transient=True
    ) as progress:
        task_scan = progress.add_task("[cyan]扫描课程结构...", total=len(modules))
        
        for future in as_completed(future_to_module):
            module = future_to_module[future]
            try:
                items = future.result()
                structure_data.add_module_data(module, items)
                progress.update(task_scan, advance=1, description=f"[cyan]扫描: {module.name[:20]}")
            except Exception as e:
                console.log(f"[red]扫描模块失败: {e}")

    items_map = structure_data.get_fetchable_items_map()
    total_items = len(items_map)
    
    if total_items > 0:
        future_to_item_id = {}
        for item_id, item in items_map.items():
            f = executor.submit(task_fetch_item_content, api_client, course, item, images_dir, api_key)
            future_to_item_id[f] = item_id

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[green]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            desc_text = f"[green]下载内容{' (含图片)' if download_imgs else ''}..."
            task_download = progress.add_task(desc_text, total=total_items)

            for future in as_completed(future_to_item_id):
                item_id = future_to_item_id[future]
                item = items_map[item_id]
                title = item.title if hasattr(item, 'title') else "Item"
                try:
                    content_md = future.result()
                    structure_data.save_item_detail(item_id, content_md)
                    progress.update(task_download, advance=1, description=f"[green]处理: {title[:15]}")
                except Exception as e:
                    structure_data.save_item_detail(item_id, f"> Error: {e}")
                    progress.update(task_download, advance=1)

    console.print(f"[dim]正在写入文件...[/]")
    write_markdown_file(file_path, course, structure_data)
    console.print(f"✅ [bold green]导出成功:[/] {file_path}")

def select_courses(api_client, user):
    with console.status("[bold green]正在获取课程列表..."):
        raw_courses = api_client.call(user.get_courses, enrollment_state='active')
        valid_courses = [c for c in raw_courses if hasattr(c, 'name')]
    
    console.print(Panel(f"发现 {len(valid_courses)} 门活跃课程", title="课程列表", border_style="blue"))
    
    for idx, course in enumerate(valid_courses):
        code = getattr(course, 'course_code', 'No Code')
        console.print(f"[bold cyan]{idx + 1}.[/] [[dim]{code}[/]] {course.name}")
    
    console.print("\n[bold yellow]请输入序号 (如 1,3) 或 'all' 导出所有:[/]")
    selection = input("> ").strip().lower()
    
    if selection == 'all': return valid_courses
    try:
        indices = [int(x.strip()) - 1 for x in selection.split(',')]
        return [valid_courses[i] for i in indices if 0 <= i < len(valid_courses)]
    except: 
        console.print("[red]输入无效。")
        return []

def main():
    key = API_KEY if API_KEY else console.input("[bold green]请输入你的 Canvas API Token: [/]").strip()
    if not key: 
        console.input("[bold red]未输入 Token，按回车退出...[/]")
        return

    rate_limiter = RateLimiter(INITIAL_REQUEST_INTERVAL)
    canvas = Canvas(API_URL, key)
    api_client = APIClient(canvas, rate_limiter)

    try:
        with console.status("[bold green]正在登录..."):
            user = api_client.call(canvas.get_current_user)
        console.print(f"👋 登录成功: [bold blue]{user.name}[/]")

        selected_courses = select_courses(api_client, user)
        if not selected_courses: 
            console.input("[bold red]未选择课程，按回车退出...[/]")
            return

        download_choice = console.input("\n[bold yellow]是否将图片下载到本地? (y/N): [/]").strip().lower()
        should_download_imgs = (download_choice == 'y')

        base_dir = "Canvas_Exports"
        if not os.path.exists(base_dir): os.makedirs(base_dir)

        console.print(f"\n🚀 [bold]启动并行引擎 (线程数: {WORKER_COUNT})...[/]")
        
        with ThreadPoolExecutor(max_workers=WORKER_COUNT) as executor:
            for course in selected_courses:
                process_course_fully_parallel(api_client, course, base_dir, executor, should_download_imgs, key)

        console.print(Panel(f"所有任务完成！请查看 '{base_dir}' 文件夹。", title="完成", border_style="green"))
        console.input("\n[bold green]按回车键退出...[/]")

    except Exception as e:
        console.print(f"\n❌ [bold red]错误: {e}")
        console.input("\n[bold red]按回车键退出...[/]")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()