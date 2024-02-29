# 计算 icl 的 complexity

import tiktoken
import csv

from src.utils.constant import *

# 计算源代码的长度
def num_tokens_from_string(string: str, model: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.encoding_for_model(model)
    num_tokens = len(encoding.encode(string))
    return num_tokens


def process_data(iclset_filepath = ICLSET_FILEPATH, model = DEFAULT_MODEL):
    # 读取文件，计算长度，存储到字典中
    data = {}
    with open(iclset_filepath, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        # id,program_idx,file_path,idx,src,dst,src_code,dst_code,sa_lb_direct,sa_lb,da_lb,dst_name_match,dst_funcname,actual_lb,actual_lb_trans,is_static,src_class,mvs,src_ancestors,src_descendants,dst_class,dst_ancestors,dst_descendants,invocation_line,receiver_object,declared_type,runtime_type,class_B,method_x_calls_method_y,your_explanation
        for row in reader:
            data[row['id']] = {'str': row['src_code'], 'length': num_tokens_from_string(row['src_code'], model)}    # length 表示 token 的数目

    # 按字符串长度升序排序
    sorted_data = sorted(data.items(), key=lambda x: x[1]['length'])
    return sorted_data

def save_to_file(data, complexity_dir = COMPLEXITY_DIR, model = DEFAULT_MODEL):
    # 将排序后的结果存储到文件中
    complexity_filepath = complexity_dir + model
    with open(complexity_filepath, 'w', newline='') as csvfile:
        fieldnames = ['id', 'str', 'length']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for item in data:
            writer.writerow({'id': item[0], 'str': item[1]['str'], 'length': item[1]['length']})

def read_from_file(num_records, complexity_dir = COMPLEXITY_DIR, model = DEFAULT_MODEL):
    # 从文件中读取排序后的结果，并返回指定数量的记录
    complexity_filepath = complexity_dir + model
    result = []
    with open(complexity_filepath, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        count = 0
        for row in reader:
            if count < num_records:
                result.append({'id': row['id'], 'str': row['str'], 'length': row['length']})
                count += 1
            else:
                break
    return result

def split_into_equal_intervals(numbers, num_intervals):
    # 计算每个区间应包含的数目
    num_per_interval = len(numbers) // num_intervals
    
    # 创建空的区间列表
    intervals = [[] for _ in range(num_intervals)]
    
    # 依次将数字分配到对应的区间中
    for i in range(num_intervals):
        intervals[i] = numbers[i*num_per_interval : (i+1)*num_per_interval]
    return intervals

# 根据复杂度获取 ids，默认最高是12
def get_iclset_ids_complexity(model, example_num):
    shortest = read_from_file(complexity_dir = COMPLEXITY_DIR, model = model, num_records = 61)
    lens = []
    for item in shortest:
        # print(f"id: {item['id']}, str: {item['str']}")
        lens.append(int(item['id']))
    intervals = split_into_equal_intervals(lens, num_intervals=example_num)
    
    # 取出每个区间的第一个 id
    ids = [interval[0] for interval in intervals if interval]
    # print(ids)
    return ids


def save_ids_to_file(complexity_dir = COMPLEXITY_DIR, model = DEFAULT_MODEL):
    # 将按复杂度排序的 id 存储到文件中
    filepath = complexity_dir + model + '_' + 'complexity_example_ids.csv'
    with open(filepath, 'w', newline='') as csvfile:
        fieldnames = ['example_num', 'ids']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for example_num in range(1, 60):
            ids = get_iclset_ids_complexity(model, example_num)
            writer.writerow({'example_num': example_num, 'ids': ids})
            # print(ids)

def read_ids_from_file(example_num, complexity_dir = COMPLEXITY_DIR, model = DEFAULT_MODEL):
    # 从文件中读取排序后的结果，并返回指定数量的记录
    complexity_filepath = complexity_dir + model + '_' + 'complexity_example_ids.csv'
    with open(complexity_filepath, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if int(row['example_num']) == example_num:
                return eval(row['ids'])
    return [11, 18, 29, 35, 50, 67, 78, 87, 95, 107, 145, 271]

def test_save():
    # 处理数据并将结果存储到文件中
    sorted_data = process_data(iclset_filepath = ICLSET_FILEPATH, model = DEFAULT_MODEL)
    save_to_file(sorted_data, complexity_dir = COMPLEXITY_DIR, model = DEFAULT_MODEL)

def test_read():
    ids = get_iclset_ids_complexity()
    print(ids)

if __name__ == '__main__':
    # test_save()
    # test_read()
    # save_ids_to_file()
    result = read_ids_from_file(example_num=2)
    print(result)
