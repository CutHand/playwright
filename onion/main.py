from playwright.sync_api import sync_playwright
import requests, re, os, base64
import logging

# 配置日志记录
logging.basicConfig(
    filename="yangcong.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
key_url = ""
m3u8_url = ""
vtt_url = ""
download_list = [
    ("高中", "英语", "人教版"),
    ("高中", "生物", "人教版"),
    ("小学", "语文", "通用版"),
]
full_name_list = ["洋葱"]


def handle_name(list):
    for index, item in enumerate(list):
        list[index] = re.sub(r'[\\/:*?"<>|“”]', "_", item).strip()
        list[index] = re.sub(r"(^_|_$)", "", list[index]).strip()
    return list


def delete_quotes(str):
    res_list = re.sub(r'("|”|“)', " ", str).strip().split()
    if len(res_list) == 1:
        return f'contains(text(),"{res_list[0]}")'
    res_str = f'contains(text(),"{res_list.pop(0)}") '
    for res in res_list:
        res_str = f'{res_str}and contains(text(),"{res}") '
    return res_str


with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=False, slow_mo=1000)
    context = browser.new_context()
    # 配置追踪开始
    # context.tracing.start(screenshots=True, snapshots=True, sources=True)
    page = context.new_page()

    def get_option_ui(num):
        all_input = page.locator(".ant-dropdown-trigger").all()
        current_option = all_input[num]
        current_option.click()

    def get_options():
        return page.locator(
            '//*[contains(@class,"ant-dropdown") and contains(@class,"ant-dropdown-placement-bottomLeft") and not(contains(@class,"ant-dropdown-hidden"))]//li'
        )

    def set_option_by_text(op):
        学段, 科目, 版本 = op
        get_option_ui(0)
        options = get_options()
        options.get_by_text(学段).click()
        get_option_ui(1)
        options = get_options()
        options.get_by_text(科目).click()
        get_option_ui(2)
        options = get_options()
        options.get_by_text(版本).click()
        return f"{学段}-{科目}-{版本}"

    def set_option(num, index):
        get_option_ui(num)
        options = get_options().all()
        option = options[index]
        option_name = option.inner_text()
        option.click()
        return option_name

    def get_option_count(num):
        get_option_ui(num)
        options = get_options().all()
        options[0].click()
        return len(options)

    def handle(route, request):
        response_url = request.url
        if "getHlsEncryptKey" in response_url:
            global key_url
            key_url = response_url
        if "m3u8" in response_url:
            global m3u8_url
            m3u8_url = response_url
        if "vtt" in response_url:
            global vtt_url
            vtt_url = response_url
        route.continue_()

    page.route(re.compile(r".*(getHlsEncryptKey|\.m3u8|\.vtt).*"), handle)
    page.goto("https://school.yangcongxueyuan.com/", wait_until="networkidle")
    page.get_by_placeholder("手机号/用户名").fill("15316310863")
    page.locator("#password").fill("liuchang17")
    page.get_by_role("button", name="登录", exact=True).click()
    page.wait_for_timeout(2000)

    # 学段 # 科目 # 版本
    for op in download_list:
        op_name = set_option_by_text(op)
        full_name_list.append(op_name)
        # 循环年纪
        book_count = get_option_count(3)
        for book_index in range(book_count):
            book_name = set_option(3, book_index)
            full_name_list.append(book_name)
            # 跳转到思维拓展
            # page.get_by_text('思维拓展').click()
            # full_name_list.append('思维拓展')
            # 循环章节
            article_count = get_option_count(4)
            for section_index in range(article_count):
                section_name = set_option(4, section_index)
                full_name_list.append(section_name)
                # 获取所有小单元的名称
                all_unit_name_list = []
                all_unit_div = page.locator(".exhibit>div").all()
                for div in all_unit_div:
                    h2 = div.locator("h2")
                    for h3 in div.locator("h3").all():
                        all_unit_name_list.append([h2.inner_text(), h3.inner_text()])
                for unit in all_unit_name_list:
                    full_name_list = full_name_list + unit
                    vide_types = page.locator(
                        f"//*[{delete_quotes(unit[-1])}]/../ul/li//h4"
                    )
                    for index, vide_type in enumerate(vide_types.all()):
                        vide_type_str = vide_type.inner_text()
                        num = f"{index+1}".zfill(2)
                        full_name_list.append(f"{num}{vide_type_str}")
                        vide_type.click()
                        page.wait_for_timeout(2000)
                        all_articles = page.locator(".list-topic button")
                        all_articles_name = page.locator(".list-topic h3")
                        for index, article in enumerate(all_articles.all()):
                            num = f"{index+1}".zfill(2)
                            full_name_list.append(
                                f"{num}{all_articles_name.nth(index).inner_text()}"
                            )
                            logging.info(full_name_list)
                            # 处理文件名
                            full_name_list = handle_name(full_name_list)
                            article.click()
                            page.wait_for_timeout(2000)
                            looked = page.query_selector('//*[contains(text(),"视频讲解")]')
                            if looked is not None:
                                looked.click()
                            # 创建文件夹
                            current_path = os.getcwd()
                            full_path = os.path.abspath(current_path)
                            current_path = full_path
                            for item in full_name_list[:-1]:
                                current_path = os.path.join(current_path, item)
                            if not os.path.exists(current_path):
                                os.makedirs(current_path)
                            # 获取key
                            if key_url != "":
                                response = requests.get(key_url)
                                # 检查响应状态码
                                if response.status_code == 200:
                                    base64_data = base64.b64encode(
                                        response.content
                                    )  # 将内容转换为Base64编码
                                    base64_string = base64_data.decode(
                                        "utf-8"
                                    )  # 转换为字符串形式
                            # 获取vtt_url文件
                            if vtt_url != "":
                                response = requests.get(vtt_url)
                                if response.status_code == 200:
                                    file_full_path = os.path.join(
                                        current_path, f"{full_name_list[-1]}.vtt"
                                    )
                                    with open(file_full_path, "wb") as f:
                                        f.write(response.content)
                            # 下载文件
                            download_tool = os.path.join(
                                os.getcwd(), "m3u8dl", "m3u8dl.exe"
                            )
                            if m3u8_url != "":
                                cmd_commend = rf'{download_tool} "{m3u8_url}" --workDir "{current_path}" --saveName "{full_name_list[-1]}" --useKeyBase64 "{base64_string}" --enableDelAfterDone --headers "Referer:https://hls.media.yangcong345.com/high/" '
                            # 清空链接
                            key_url = ""
                            m3u8_url = ""
                            vtt_url = ""
                            os.system(cmd_commend)
                            page.locator(".icon-ic_quit").click()
                            page.get_by_text("确认退出").click()
                            # print(full_name_list)
                            full_name_list.pop()
                        page.locator('//*[@data-balloon="返回"]').click()
                        full_name_list.pop()
                    full_name_list = full_name_list[: -len(unit)]
                full_name_list.pop()
            full_name_list.pop()
        full_name_list.pop()
    # context.tracing.stop(path="trace.zip") # 结束追踪的地方，添加 tracing 的结束配置。
    context.close()
    browser.close()
