import re


def extract_game_script(input_file, output_file):
    print(f"正在读取文件: {input_file} (UTF-8)...")

    with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
        text_content = f.read()

    # 1. 提取标题
    # 修正：允许标题中间有空格，匹配到换行符或多个空格为止
    title_pattern = r'([0-9０-９]{1,2}．.+?)(?=\s{2,}|\n|$)'
    titles = re.findall(title_pattern, text_content)

    # 2. 提取正文内容 ($m1 ... $m0)
    body_pattern = r'\$m1(.*?)\$m0'
    bodies = re.findall(body_pattern, text_content, re.DOTALL)

    print(f"原始统计 -> 标题: {len(titles)} 个, 内容: {len(bodies)} 个")

    # ================= 关键修正部分 =================
    # 自动检测并删除第一个如果是“$909090”这样的垃圾代码
    if len(bodies) > 0:
        first_body = bodies[0].strip()
        # 如果第一个内容很短（小于10个字）且包含数字或$，通常是系统代码
        if len(first_body) < 15 and ('$' in first_body or first_body.isdigit()):
            print(f"发现头部干扰数据: '{first_body}' -> 已自动剔除，进行对齐修正。")
            bodies.pop(0)  # 删除第一个元素
    # ==============================================

    # 再次统计
    count_limit = min(len(titles), len(bodies))
    print(f"修正后将输出 {count_limit} 组数据...")

    with open(output_file, 'w', encoding='utf-8') as out:
        for i in range(count_limit):
            t = titles[i].strip()
            # 替换掉原文中的 '|' 为换行，阅读体验更好（如果不需要可删掉 .replace）
            b = bodies[i].strip().replace('|', '\n')

            out.write(f"{t}\n")
            out.write(f"{b}\n")
            out.write("-" * 30 + "\n")  # 加个分割线更清晰

    print(f"提取完成！请查看: {output_file}")


if __name__ == '__main__':
    extract_game_script('1.txt', '最终结果.txt')