import re
import os


def findSubStrIndex(str, substr, time):
    times = str.count(substr)
    if (times == 0) or (times < time):
        pass
    else:
        i = 0
        index = -1
        while i < time:
            index = str.find(substr, index + 1)
            i += 1
        return index


# 将androguard的log转换成proguard可识别的log
def praise_log(androguard_log_lines):
    praised_lines = []
    if androguard_log_lines:
        for line in androguard_log_lines:
            # print(line)
            if line == 'in\n' or line == '\n':
                # 非内容行，不做处理
                continue
            line = line.replace('\n', '')
            if line.startswith('XREFto for '):
                # 直接引用
                line = line.replace('XREFto for ', '')
            elif line.startswith('XREFfrom for '):
                # 直接引用
                line = line.replace('XREFfrom for ', '')
            else:
                # 去掉前面到:的文本
                start_index = line.find(':')
                if start_index != -1:
                    line = line[start_index + 1:]
            # 截取到类名+方法名（去掉块标记信息）
            line = re.sub(r'^L(.+)\(.*', r'at \1', line)
            # 更改为.调用
            line = line.replace('/', '.').replace(';->', '.')
            # 写入一个方法前的类的点分割数，方便后面反混淆时识别到类名
            quote_count = line.count('.')
            line = line + f'({quote_count})'

            praised_lines.append(line)
    return praised_lines


def retrace(log_input_path, mapping_path):
    # 反混淆
    mapping_path = '/Users/kevin/Downloads/proguard/QDReaderGank.App-master-release-mapping.txt'
    retrace_output_path = log_input_path + "_retrace.txt"
    os.system('qdpshield/tools/proguard/bin/retrace.sh -verbose ' + mapping_path + ' ' + log_input_path + ' > ' + retrace_output_path)

    with open(retrace_output_path, 'r') as fp:
        retrace_raw_lines = fp.readlines()

    praised_lines = []
    if retrace_raw_lines:
        for line in retrace_raw_lines:
            if not line.startswith('at '):
                # 忽略其他的
                continue
            line = line.replace('\n', '').replace('at ', '')
            line_output = ''
            if line.find(' ') != -1:
                # 有反混淆的，需要处理
                parts = line.split(' ')
                # 从后一部分获取点的数量（用来截取出调用的类名）
                sub_parts = parts[1].split(')(')
                method_name = sub_parts[0] + ')'
                quote_count = sub_parts[1][0:sub_parts[1].rfind(')')]
                index = findSubStrIndex(parts[0], '.', int(quote_count))
                class_name = parts[0]
                return_str = 'void'
                if index != -1:
                    class_name = parts[0][0:index]
                    return_str = parts[0][index + 1:]
                line_output = class_name + '.' + method_name + ':' + return_str  # + '     ' + quote_count)
            else:
                # 没有反混淆，去掉at和后面的数字即可
                line_output = line[0:line.rfind('(') + 1] + ')'
            praised_lines.append(line_output)
    # 删除混淆生成的中间文件
    #os.remove(retrace_output_path)

    return praised_lines


def get_retrace_from_log(mapping_path, log_lines, praised_log_path):
    """
    mapping_path 混淆产生的mapping文件
    log_lines 原始堆栈信息
    """
    # 转换堆栈数据
    praised_lines = praise_log(log_lines)

    # 写入转换后的堆栈数据到文件
    if len(praised_lines) > 0:
        with open(praised_log_path, 'w') as fp:
            for l in praised_lines:
                fp.write(l + '\n')

    if len(log_lines) > 0:
        with open(praised_log_path + '_origin.txt', 'w') as fp:
            for l in log_lines:
                fp.write(l + '\n')

    # 反混淆
    result_lines = retrace(praised_log_path, mapping_path)

    #os.remove(praised_log_path)

    return result_lines

if __name__ == '__main__':

    input_log_path = '/Users/kevin/Downloads/proguard/src2.txt'
    print("解析log数据：")

    print('==============================================')

    with open(input_log_path, 'r') as fp:
        lines = fp.readlines()

    praised_lines = praise_log(lines)

    if not os.path.exists('proguard'):
        # 新建文件夹
        os.mkdir('proguard')

    output_log_path = 'proguard/src2_praise.txt'
    if len(praised_lines) > 0:
        with open(output_log_path, 'w') as fp:
            for l in praised_lines:
                fp.write(l + '\n')

    # 打印
    # for l in praised_lines:
    #     print(l)

    # 反混淆
    retrace_input_path = 'proguard/src2_praise.txt'

    result_lines = retrace(retrace_input_path, '')

    os.remove(retrace_input_path)

    # 打印
    for l in result_lines:
        print(l)

    print('==============================================')