#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动作积分自动统计工具（复刻版 · 无授权校验）

作用：
    读取「微信聊天记录」Excel（需包含 发送人 / 内容 两列），
    按「门店关键字」把每条记录归到对应门店，
    再按「动作关键字配置」统计每条内容里命中的动作次数（有上限），
    最后把结果写回「积分公示表」模版对应的单元格。

依赖：openpyxl
用法（命令行）：
    python jifen_tongji.py --chat 聊天记录.xlsx --template 模版.xlsx
可选参数：
    --chat-sheet / --template-sheet      指定 sheet（默认第一个）
    --keyword-col H                      门店关键字所在列（默认 H）
    --title-row 4                        动作标题所在行（默认 4）
    --title-col J                        动作标题起始列（默认 J）
    --config keyword_config.json         关键字配置（默认同目录 keyword_config.json，不存在自动生成）
    --out 输出.xlsx                      另存为新文件（默认直接写回模版）
图形界面：
    python jifen_tongji.py --gui
"""

import os
import sys
import json
import argparse

try:
    import openpyxl
except ImportError:  # pragma: no cover
    sys.stderr.write("缺少依赖 openpyxl，请先执行：pip install openpyxl\n")
    sys.exit(1)

# ----------------------------------------------------------------------------- 
# 默认关键字配置（与常见"3+X将帅营动作积分"口径一致，可自行修改）
# limit = 该动作每人每天最多计入的次数上限
# -----------------------------------------------------------------------------
DEFAULT_CONFIG = {
    "_settings": {
        "zero_handling": "blank",
        "description": "0值处理方式: blank=空白(推荐), zero=写入0, skip=跳过不写入",
    },
    "每日晨读": {"keywords": ["晨读", "早读", "晨会", "一读"], "limit": 2, "description": "每日晨读活动统计"},
    "3+X产品演练": {"keywords": ["产品演练", "产品培训", "演练"], "limit": 5, "description": "产品演练培训统计"},
    "上门测量": {"keywords": ["测量"], "limit": 10, "description": "上门测量服务统计"},
    "门店落地": {"keywords": ["落地"], "limit": 3, "description": "门店落地活动统计"},
    "破零攻坚": {"keywords": ["添加", "加微信"], "limit": 10, "description": "破零攻坚活动统计"},
    "订单晒单": {"keywords": ["订单晒单"], "limit": 5, "description": "订单晒单活动统计"},
    "日清": {"keywords": ["日清", "工作日志", "总结"], "limit": 1, "description": "日清工作总结统计"},
}


# ----------------------------------------------------------------------------- 
# Excel 列号工具
# -----------------------------------------------------------------------------
def column_number_to_letter(column_number):
    """列号 -> Excel 列名（1->A, 27->AA）"""
    result = ""
    while column_number > 0:
        column_number, remainder = divmod(column_number - 1, 26)
        result = chr(65 + remainder) + result
    return result


def letter_to_column_number(letter):
    """Excel 列名 -> 列号（A->1, AA->27）"""
    result = 0
    for char in str(letter).upper():
        if not ("A" <= char <= "Z"):
            continue
        result = result * 26 + (ord(char) - ord("A")) + 1
    return result


def list_excel_sheets(file_path):
    wb = openpyxl.load_workbook(file_path, read_only=True)
    try:
        return list(wb.sheetnames)
    finally:
        wb.close()


def _pick_sheet(wb, sheet_name):
    if sheet_name and sheet_name in wb.sheetnames:
        return wb[sheet_name]
    return wb.active


# ----------------------------------------------------------------------------- 
# 读取
# -----------------------------------------------------------------------------
def read_xlsx_to_objects(file_path, sheet_name=None):
    """读取表格：第一行作表头，其余行转成 dict 数组"""
    wb = openpyxl.load_workbook(file_path, data_only=True)
    try:
        sheet = _pick_sheet(wb, sheet_name)
        rows = list(sheet.iter_rows(values_only=True))
        if not rows:
            return []
        headers = [("" if h is None else str(h).strip()) for h in rows[0]]
        objects = []
        for row in rows[1:]:
            if row is None or all(c is None for c in row):
                continue
            obj = {}
            for j, cell in enumerate(row):
                key = headers[j] if j < len(headers) else f"col{j+1}"
                obj[key] = cell
            objects.append(obj)
        return objects
    finally:
        wb.close()


def read_template_file(template_path, sheet_name, keyword_col, title_start_row, title_start_col):
    """
    读取模版：门店关键字（同列，从第5行起）与动作标题（同一行，从指定列起）
    返回 (store_keywords, dynamic_titles, store_row_mapping, title_col_mapping)
    """
    wb = openpyxl.load_workbook(template_path)
    try:
        sheet = _pick_sheet(wb, sheet_name)
        store_keywords, store_row_mapping = [], {}
        for row_num in range(5, sheet.max_row + 1):
            kw = sheet.cell(row=row_num, column=keyword_col).value
            if kw is None:
                continue
            kw_str = str(kw).strip()
            if kw_str == "":
                continue
            store_keywords.append(kw_str)
            store_row_mapping[kw_str] = row_num

        dynamic_titles, title_col_mapping = [], {}
        col_index = title_start_col
        while True:
            cell_value = sheet.cell(row=title_start_row, column=col_index).value
            if cell_value is None or str(cell_value).strip() == "":
                break
            title = str(cell_value).strip()
            dynamic_titles.append(title)
            title_col_mapping[title] = col_index
            col_index += 1
        return store_keywords, dynamic_titles, store_row_mapping, title_col_mapping
    finally:
        wb.close()


# ----------------------------------------------------------------------------- 
# 关键字配置
# -----------------------------------------------------------------------------
def setup_keyword_config(config_file="keyword_config.json"):
    """加载/创建关键字配置，返回 (config, settings)"""
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                raw = json.load(f)
            settings = raw.pop("_settings", {"zero_handling": "blank"})
            config = {}
            for title, item in raw.items():
                if not isinstance(item, dict) or "keywords" not in item or "limit" not in item:
                    print(f"⚠️  配置项 '{title}' 格式不正确，跳过")
                    continue
                config[title] = item
            print(f"✅ 成功加载配置文件: {config_file}")
            return config, settings
        except json.JSONDecodeError as e:
            print(f"❌ JSON配置文件格式错误: {e}，使用默认配置并备份原文件")
            os.rename(config_file, config_file + ".backup")
        except Exception as e:
            print(f"❌ 读取配置出错: {e}，使用默认配置")

    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(DEFAULT_CONFIG, f, ensure_ascii=False, indent=4)
    print(f"📝 已创建默认配置文件: {config_file}")
    settings = DEFAULT_CONFIG.get("_settings", {"zero_handling": "blank"})
    config = {k: v for k, v in DEFAULT_CONFIG.items() if k != "_settings"}
    return config, settings


# ----------------------------------------------------------------------------- 
# 匹配与统计
# -----------------------------------------------------------------------------
def match_store(sender_name, store_keywords):
    """在发送人里找门店关键字，命中返回该关键字，否则 None"""
    if not sender_name:
        return None
    sender_name = str(sender_name)
    for keyword in store_keywords:
        if keyword and keyword in sender_name:
            return keyword
    return None


def count_keywords_in_content(content, keywords):
    """统计内容里命中的关键字个数（不是出现次数，是命中几个不同的关键字）"""
    if not content:
        return 0
    content = str(content)
    count = 0
    for keyword in keywords:
        if keyword and keyword in content:
            count += 1
    return count


def process_chat_records(chat_records, store_keywords, dynamic_titles, keyword_config, store_names,
                         verbose=False):
    """核心统计，返回 {门店: {动作标题: 次数}}"""
    result = {name: {t: 0 for t in dynamic_titles} for name in store_names}

    for i, record in enumerate(chat_records):
        sender = record.get("发送人", "") or ""
        content = record.get("内容", "") or ""
        content = str(content)

        matched_keyword = match_store(sender, store_keywords)
        if not matched_keyword:
            continue
        store = matched_keyword
        if store not in result:
            result[store] = {t: 0 for t in dynamic_titles}

        for title in dynamic_titles:
            if title not in keyword_config:
                continue
            keywords = keyword_config[title].get("keywords", [])
            limit = keyword_config[title].get("limit", 0)
            current = result[store][title]
            if current >= limit:
                continue
            hit = count_keywords_in_content(content, keywords)
            if hit > 0:
                result[store][title] = min(current + hit, limit)

    return result


# ----------------------------------------------------------------------------- 
# 写回模版
# -----------------------------------------------------------------------------
def write_result_to_template(result, template_path, store_row_mapping, title_col_mapping,
                             sheet_name=None, zero_handling="blank", out_path=None):
    wb = openpyxl.load_workbook(template_path)
    try:
        sheet = _pick_sheet(wb, sheet_name)
        written = 0
        for store_keyword, title_counts in result.items():
            row_num = None
            for name, row in store_row_mapping.items():
                if store_keyword in name or name in store_keyword:
                    row_num = row
                    break
            if row_num is None:
                print(f"⚠️ 未找到门店关键字 '{store_keyword}' 对应的行，跳过")
                continue
            for title, count in title_counts.items():
                col_num = title_col_mapping.get(title)
                if col_num is None:
                    print(f"⚠️ 未找到标题 '{title}' 对应的列号")
                    continue
                cell = sheet.cell(row=row_num, column=col_num)
                if count > 0:
                    cell.value = count
                    written += 1
                elif zero_handling == "blank":
                    cell.value = None
                elif zero_handling == "zero":
                    cell.value = 0
                elif zero_handling == "skip":
                    pass
        save_path = out_path or template_path
        wb.save(save_path)
        print(f"✅ 统计结果已写入: {save_path}  (共写入 {written} 个非零单元格)")
        return save_path
    finally:
        wb.close()


# ----------------------------------------------------------------------------- 
# 一键运行（供程序调用）
# -----------------------------------------------------------------------------
def run(chat_path, template_path, chat_sheet=None, template_sheet=None,
        keyword_col=8, title_start_row=4, title_start_col=10,
        config_file="keyword_config.json", out_path=None, verbose=False):
    """执行完整流程，返回统计结果 dict"""
    chat_records = read_xlsx_to_objects(chat_path, chat_sheet)
    print(f"成功读取 {len(chat_records)} 条聊天记录")
    store_keywords, dynamic_titles, store_row_mapping, title_col_mapping = \
        read_template_file(template_path, template_sheet, keyword_col, title_start_row, title_start_col)
    print(f"共读取到 {len(store_keywords)} 个门店关键字：{store_keywords}")
    print(f"动态标题：{dynamic_titles}")
    keyword_config, settings = setup_keyword_config(config_file)
    zero_handling = settings.get("zero_handling", "blank")
    result = process_chat_records(chat_records, store_keywords, dynamic_titles,
                                  keyword_config, store_keywords, verbose=verbose)
    write_result_to_template(result, template_path, store_row_mapping, title_col_mapping,
                             template_sheet, zero_handling, out_path)
    return result


# ----------------------------------------------------------------------------- 
# 命令行
# -----------------------------------------------------------------------------
def _cli(argv=None):
    parser = argparse.ArgumentParser(description="动作积分自动统计工具（复刻版）")
    parser.add_argument("--chat", help="聊天记录 Excel 路径")
    parser.add_argument("--template", help="积分公示表模版 Excel 路径")
    parser.add_argument("--chat-sheet", default=None)
    parser.add_argument("--template-sheet", default=None)
    parser.add_argument("--keyword-col", default="H", help="门店关键字列（默认H）")
    parser.add_argument("--title-row", type=int, default=4, help="动作标题行（默认4）")
    parser.add_argument("--title-col", default="J", help="动作标题起始列（默认J）")
    parser.add_argument("--config", default="keyword_config.json")
    parser.add_argument("--out", default=None, help="另存为新文件；默认写回模版")
    parser.add_argument("--gui", action="store_true", help="打开图形界面")
    args = parser.parse_args(argv)

    if args.gui or (not args.chat and not args.template):
        return _launch_gui()

    if not args.chat or not args.template:
        parser.error("需要 --chat 与 --template（或使用 --gui）")

    result = run(
        chat_path=args.chat, template_path=args.template,
        chat_sheet=args.chat_sheet, template_sheet=args.template_sheet,
        keyword_col=letter_to_column_number(args.keyword_col),
        title_start_row=args.title_row,
        title_start_col=letter_to_column_number(args.title_col),
        config_file=args.config, out_path=args.out,
    )
    print("\n=== 统计结果 ===")
    for store, counts in result.items():
        nonzero = {t: c for t, c in counts.items() if c > 0}
        print(f"  {store}: {nonzero if nonzero else '无数据'}")
    print("\n处理完成！")
    return 0


# ----------------------------------------------------------------------------- 
# 图形界面（tkinter，可选）
# -----------------------------------------------------------------------------
def _launch_gui():
    try:
        import tkinter as tk
        from tkinter import ttk, filedialog, messagebox, scrolledtext
    except Exception as e:  # pragma: no cover
        sys.stderr.write(f"无法加载图形界面（tkinter）: {e}\n请改用命令行参数运行。\n")
        return 1

    root = tk.Tk()
    root.title("动作积分自动统计工具 · 复刻版")
    root.geometry("900x680")

    vars_ = {
        "chat": tk.StringVar(),
        "chat_sheet": tk.StringVar(),
        "template": tk.StringVar(),
        "template_sheet": tk.StringVar(),
        "keyword_col": tk.StringVar(value="H"),
        "title_row": tk.StringVar(value="4"),
        "title_col": tk.StringVar(value="J"),
        "zero": tk.StringVar(value="blank"),
    }

    def browse(key):
        path = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx *.xls"), ("所有文件", "*.*")])
        if path:
            vars_[key].set(path)
            try:
                sheets = list_excel_sheets(path)
                combo = combos[key]
                combo["values"] = sheets
                if sheets:
                    vars_[key + "_sheet" if key + "_sheet" in vars_ else key].set("")  # noop
                    (chat_combo if key == "chat" else template_combo)["values"] = sheets
                    (chat_combo if key == "chat" else template_combo).set(sheets[0])
                    vars_["chat_sheet" if key == "chat" else "template_sheet"].set(sheets[0])
            except Exception as e:
                messagebox.showerror("读取失败", str(e))

    pad = {"padx": 8, "pady": 4}
    tk.Label(root, text="① 聊天记录文件").grid(row=0, column=0, sticky="w", **pad)
    tk.Entry(root, textvariable=vars_["chat"], width=70).grid(row=0, column=1, **pad)
    tk.Button(root, text="浏览", command=lambda: browse("chat")).grid(row=0, column=2, **pad)
    chat_combo = ttk.Combobox(root, textvariable=vars_["chat_sheet"], width=40, state="readonly")
    chat_combo.grid(row=1, column=1, sticky="w", **pad)

    tk.Label(root, text="② 积分公示表(模版)").grid(row=2, column=0, sticky="w", **pad)
    tk.Entry(root, textvariable=vars_["template"], width=70).grid(row=2, column=1, **pad)
    tk.Button(root, text="浏览", command=lambda: browse("template")).grid(row=2, column=2, **pad)
    template_combo = ttk.Combobox(root, textvariable=vars_["template_sheet"], width=40, state="readonly")
    template_combo.grid(row=3, column=1, sticky="w", **pad)

    combos = {"chat": chat_combo, "template": template_combo}

    tk.Label(root, text="③ 列配置").grid(row=4, column=0, sticky="w", **pad)
    f = tk.Frame(root)
    f.grid(row=4, column=1, sticky="w", **pad)
    tk.Label(f, text="门店关键字列").pack(side="left")
    tk.Entry(f, textvariable=vars_["keyword_col"], width=5).pack(side="left", padx=5)
    tk.Label(f, text="标题行").pack(side="left")
    tk.Entry(f, textvariable=vars_["title_row"], width=5).pack(side="left", padx=5)
    tk.Label(f, text="标题起始列").pack(side="left")
    tk.Entry(f, textvariable=vars_["title_col"], width=5).pack(side="left", padx=5)
    tk.Label(f, text="0值处理").pack(side="left")
    ttk.Combobox(f, textvariable=vars_["zero"], values=["blank", "zero", "skip"],
                 width=6, state="readonly").pack(side="left", padx=5)

    log = scrolledtext.ScrolledText(root, height=22, font=("Consolas", 9))
    log.grid(row=6, column=0, columnspan=3, sticky="nsew", **pad)
    root.grid_rowconfigure(6, weight=1)
    root.grid_columnconfigure(1, weight=1)

    def append(txt):
        log.insert("end", txt + "\n")
        log.see("end")
        root.update_idletasks()

    def start():
        try:
            if not vars_["chat"].get() or not vars_["template"].get():
                messagebox.showerror("提示", "请先选择聊天记录与模版文件")
                return
            append("=" * 50)
            append("开始分析…")
            config = dict(DEFAULT_CONFIG)
            config["_settings"] = {"zero_handling": vars_["zero"].get()}
            cfg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keyword_config.json")
            if not os.path.exists(cfg_path):
                with open(cfg_path, "w", encoding="utf-8") as fp:
                    json.dump(DEFAULT_CONFIG, fp, ensure_ascii=False, indent=4)
            result = run(
                chat_path=vars_["chat"].get(), template_path=vars_["template"].get(),
                chat_sheet=vars_["chat_sheet"].get() or None,
                template_sheet=vars_["template_sheet"].get() or None,
                keyword_col=letter_to_column_number(vars_["keyword_col"].get()),
                title_start_row=int(vars_["title_row"].get()),
                title_start_col=letter_to_column_number(vars_["title_col"].get()),
                config_file=cfg_path, out_path=None,
            )
            append("\n=== 统计结果 ===")
            for store, counts in result.items():
                nz = {t: c for t, c in counts.items() if c > 0}
                append(f"  {store}: {nz if nz else '无数据'}")
            append("处理完成！")
            messagebox.showinfo("完成", "统计完成，结果已写回模版文件")
        except Exception as e:
            append(f"❌ 处理失败: {e}")
            messagebox.showerror("错误", str(e))

    tk.Button(root, text="🎯 开始分析处理", command=start, bg="#FF3B30", fg="white",
              width=18, height=2).grid(row=5, column=1, pady=8)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
