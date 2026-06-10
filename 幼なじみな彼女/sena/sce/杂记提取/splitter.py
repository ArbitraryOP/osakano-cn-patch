import re
import os


def split_game_script(input_file):
    print(f"正在读取源文件: {input_file} ...")

    # 读取文件内容
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"错误：找不到文件 '{input_file}'。请确保该文件在当前目录下。")
        return

    # 使用分割线将文本切分为块
    # 你的文件中使用的是 30 个减号
    separator = "-" * 30
    # split后可能会有空块，需要过滤
    raw_blocks = content.split(separator)

    # 准备四个列表容器
    run1 = []  # 一周目 (1, 4, 7...)
    run2 = []  # 二周目 (2, 5, 8...)
    run3 = []  # 三周目 (3, 6, 9...)
    true_end = []  # 真结局 (49+)

    count = 0

    for block in raw_blocks:
        block = block.strip()
        if not block:
            continue

        # 使用正则提取标题中的数字
        # 兼容全角数字(１)和半角数字(1)
        match = re.match(r'^([0-9０-９]+)[．.]', block)

        if match:
            # Python的int()函数可以直接把全角数字字符转换为整数
            num = int(match.group(1))
            count += 1

            # 按照你的逻辑进行分类
            if num >= 49:
                # 49及以后 -> 真结局
                true_end.append(block)
            elif num % 3 == 1:
                # 余数为1 (1, 4, 7...) -> 一周目
                run1.append(block)
            elif num % 3 == 2:
                # 余数为2 (2, 5, 8...) -> 二周目
                run2.append(block)
            elif num % 3 == 0:
                # 余数为0 (3, 6, 9...) -> 三周目
                run3.append(block)
        else:
            # 如果匹配不到数字，保留到真结局或者打印警告（通常是文件末尾的空行）
            pass

    print(f"共处理了 {count} 个章节。")

    # 定义写入文件的辅助函数
    def write_to_file(filename, blocks):
        print(f"正在生成: {filename} (包含 {len(blocks)} 个章节)")
        with open(filename, 'w', encoding='utf-8') as f:
            for b in blocks:
                f.write(b)
                f.write("\n")
                f.write(separator)
                f.write("\n")

    # 定义输出文件名 (注意：将冒号替换为下划线，否则无法保存)
    file1_name = "一周目_标题与内容对应1,4,7....46.txt"
    file2_name = "二周目_标题与内容对应2,5,8...47.txt"
    file3_name = "三周目_标题与内容对应3,6,9......48.txt"
    file4_name = "真结局_标题与内容对应49以及后续所有内容.txt"

    # 执行写入
    write_to_file(file1_name, run1)
    write_to_file(file2_name, run2)
    write_to_file(file3_name, run3)
    write_to_file(file4_name, true_end)

    print("\n所有文件拆分完成！")


if __name__ == '__main__':
    # 这里的输入文件名要和你当前目录下的文件名一致
    # 如果你之前保存的是 "最终修正版.txt" 或 "1.txt" 或 "杂记.txt"，请在这里修改
    split_game_script('杂记.txt')