import time
import os
import json
import csv
import random
from openai import OpenAI
import tiktoken

client = OpenAI(
  # This is the default and can be omitted
  # api_key='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',  # 0226
  # api_key='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'  # 0229
  api_key='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'  # 0229
  # api_key='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' # 0229
)

LEN_ICLSET = 60
DEFAULT_MODEL = "gpt-3.5-turbo-0125"
INPUT_TOKEN_LIMIT = 16385 - 4096  # 12289, output_max = 4k, total_max = 16k
ICLSET_FILEPATH = '/content/drive/MyDrive/ColabNotebooks/datasetFeb2024/iclset.csv'
VALSET_FILEPATH = '/content/drive/MyDrive/ColabNotebooks/datasetFeb2024/valset.csv'
COMPLEXITY_DIR = '/content/drive/MyDrive/ColabNotebooks/datasetFeb2024/complexity/'
SIMILARITY_DIR = '/content/drive/MyDrive/ColabNotebooks/datasetFeb2024/SIMILARITY/'
RESPONSE_DIR = '/content/drive/MyDrive/ColabNotebooks/datasetFeb2024/response/'

# 计算源代码的长度
def num_tokens_from_string(string: str, model = DEFAULT_MODEL) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.encoding_for_model(model)
    num_tokens = len(encoding.encode(string))
    return num_tokens

# An error occurred: Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-3.5-turbo-0125 in organization org-nKZBuqZzkg6K1yshRGsCgFq8 on requests per day (RPD): Limit 200, Used 200, Requested 1. Please try again in 7m12s. Visit https://platform.openai.com/account/rate-limits to learn more. You can increase your rate limit by adding a payment method to your account at https://platform.openai.com/account/billing.', 'type': 'requests', 'param': None, 'code': 'rate_limit_exceeded'}}
# An error occurred: Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-3.5-turbo-0125 in organization org-nKZBuqZzkg6K1yshRGsCgFq8 on requests per min (RPM): Limit 3, Used 3, Requested 1. Please try again in 20s. Visit https://platform.openai.com/account/rate-limits to learn more. You can increase your rate limit by adding a payment method to your account at https://platform.openai.com/account/billing.', 'type': 'requests', 'param': None, 'code': 'rate_limit_exceeded'}}
def get_response(prompt, model = DEFAULT_MODEL):
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            temperature=0
        )
        return response
    except Exception as e:
        # 处理异常，例如输出错误信息或者等待一段时间后重新发送请求
        exception_info = str(e)
        print(f"An error occurred: {exception_info}")
        if 'per day (RPD)' in exception_info:
          return ''
        elif 'per min (RPM)' in exception_info:
          time.sleep(20)
          return get_response(prompt, model)
        # 其他异常，静观其变
        time.sleep(5) # 等待5秒后重新发送请求
        return get_response(prompt, model)  # 递归调用函数

def get_response_content(r):
    return r.choices[0].message.content # 回复的具体内容

# response 是和模型交互之后的回复
# program_idx 是训练集项目的 idx
# idx 是该条数据的 idx
def extract_and_save_info_from_response(r, program_idx, idx, r_saved_filepath):
  r_id = r.id # 当轮对话 id
  r_model = r.model # 当轮对话调用的模型
  r_choices = r.choices # 这里只有一个选择，表示对话完成的结果。
  r_message = r.choices[0].message # 是一个对话完成的消息对象，包含内容、角色等信息。
  r_content = r.choices[0].message.content # 回复的具体内容
  r_role = r.choices[0].message.role # 'assistant'，表示这个对话完成的角色是助手。
  r_function_call = r.choices[0].message.function_call # 表示没有在这个对话完成中调用的任何函数。
  r_tool_calls = r.choices[0].message.tool_calls # 表示在这个对话完成中调用的任何工具。
  r_usage = r.usage # 包含生成的对话完成的使用情况统计。
  r_completion_tokens = r.usage.completion_tokens # 表示生成的对话完成结果包含的标记（tokens）。
  r_prompt_tokens = r.usage.prompt_tokens  # 表示生成这个对话完成结果所用到的输入标记数。
  r_total_tokens = r.usage.total_tokens  # 表示这个对话完成任务总共用到的标记数。
  # 构建存储的行数据
  row = [program_idx, idx, r_id, r_model, r_choices, r_message, r_content, r_role,
         r_function_call, r_tool_calls, r_usage, r_completion_tokens, r_prompt_tokens, r_total_tokens]
  file_exists = os.path.isfile(r_saved_filepath)
  # 打开文件，写入数据
  with open(r_saved_filepath, 'a', newline='') as csvfile:
    writer = csv.writer(csvfile)
    if not file_exists:
      # 写入标题行
      writer.writerow(['program_idx', 'idx', 'id', 'model', 'choices', 'message', 'content', 'role',
                       'function_call', 'tool_calls', 'usage', 'completion_tokens', 'prompt_tokens', 'total_tokens'])
    writer.writerow(row)
    csvfile.flush()

# 准备工作
def get_length_of_csv(written_filepath):
  # 获取已有行的数量
  row_count = 0
  with open(written_filepath, 'r', encoding='gbk') as written_file:
    written_csv_reader = csv.reader(written_file)
    row_count = sum(1 for row in written_csv_reader)
  return row_count

def new_result_file(written_filepath, header):
  if os.path.exists(written_filepath):
    return
  with open(written_filepath, 'w', encoding='gbk') as written_file:
    written_csv_writer = csv.writer(written_file)
    written_csv_writer.writerow(header)
  print('添加完表头后该文件的 length：', get_length_of_csv(written_filepath))

# 拿到大语言模型的结果后，将其分解为 cot 的中间步骤
def cot_steps(model, example_type='complexity', example_num=0):
    example_num_str = 'inf' if example_num >= LEN_ICLSET else str(example_num)
    result_filepath = RESPONSE_DIR + model + '_' + example_type + '_' + example_num_str + '.csv'

    cot_steps_filepath = RESPONSE_DIR + model + '_' + example_type + '_' + example_num_str + '_cot_steps.csv'
    new_result_file(cot_steps_filepath, ['program_idx', 'idx', 'src', 'dst', 'src_code', 'dst_code', 'response_content', 'ids', 'ids_len', 'invocation_line', 'receiver_object', 'declared_type', 'runtime_type', 'answer', 'your_explanation'])
    with open(cot_steps_filepath, 'a') as written_file:
        cot_steps_csv_writer = csv.writer(written_file)
        with open(result_filepath, 'r') as file:
            header = ['program_idx', 'idx', 'src', 'dst', 'src_code', 'dst_code', 'response_content', 'ids', 'ids_len']
            csv_reader = csv.reader(file)
            next(csv_reader)  # 跳过首行
            for i, row in enumerate(csv_reader, start=1):
                program_idx, idx, src, dst, src_code, dst_code, response_content, ids, ids_len = row
                # print(response_content)
                cot_results = extract_content(response_content)
                invocation_line = cot_results.get('invocation_line', '')
                receiver_object = cot_results.get('receiver_object', '')
                declared_type = cot_results.get('declared_type', '')
                runtime_type = cot_results.get('runtime_type', '')
                answer = cot_results.get('answer', '')
                your_explanation = cot_results.get('your_explanation', '')

                new_row = [program_idx, idx, src, dst, src_code, dst_code, response_content, ids, ids_len, invocation_line, receiver_object, declared_type, runtime_type, answer, your_explanation]
                cot_steps_csv_writer.writerow(new_row)
#
def extract_content(json_string):
    json_string = json_string.replace('""', '"')
    content = {}
    try:
        parsed_data = json.loads(json_string)
        for key, value in parsed_data.items():
            content[key] = value
    except:
        print('模型输出不规范', json_string)
    return content

def read_complexity_ids_from_file(complexity_dir = COMPLEXITY_DIR, model = DEFAULT_MODEL, example_num = LEN_ICLSET):
  if example_num <= 0:
    return []
  complexity_filepath = complexity_dir + model + '_' + 'complexity_example_ids.csv'
  with open(complexity_filepath, 'r', newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
      if int(row['example_num']) == int(example_num):
        return eval(row['ids'])
  return [5, 59, 28, 47, 51, 13, 0, 24, 7, 45, 46, 42, 29, 9, 12, 14, 32, 57, 48, 17, 38, 43, 44, 33, 21, 60, 16, 18, 8, 41, 23, 30, 35, 6, 3, 4, 56, 20, 49, 58, 11, 36, 22, 26, 55, 37, 31, 50, 52, 25, 39, 53, 54, 34, 10, 40, 15, 19, 1, 2]

def read_similarity_ids_from_file(input, similarity_dir = SIMILARITY_DIR, model = DEFAULT_MODEL, example_num = 20):
  print()


def get_icl_examples_by_ids(ids, example_num = 12):
  # 顺序一：简洁度
  ids = ids[:example_num]
  examples = []
  for id in ids:
    examples.append(get_prompt_example_by(id=id))
  return examples


# 获取 iclset 中构成示例的 input 部分，这部分用于向量
def get_input(caller, caller_fqn, callee_fqn, caller_class, callee_class, funcname,
               caller_ancestors, caller_descendants, callee_ancestors, callee_descendants, mvs):
  return f"""input: {{
  "fqn_method_x":"{caller_fqn}",
  "source_code_method_x": "{caller}",
  "class_A": "{caller_class}",
  "member_variables_of_A": "{mvs}",
  "ancestors_of_A": "{caller_ancestors}",
  "descendants_of_A": "{caller_descendants}",
  "fqn_method_y": "{callee_fqn}",
  "funcname_of_method_y":"{funcname}",
  "class_B": "{callee_class}",
  "ancestors_of_B": "{callee_ancestors}",
  "descendants_of_B": "{callee_descendants}"]}}"""



def get_output(invocation_line, receiver_object, declared_type, runtime_type,
               method_x_calls_method_y, your_explanation):
  return f"""output: {{
  "invocation_line":"{invocation_line}",
  "receiver_object":"{receiver_object}",
  "declared_type":"{declared_type}",
  "runtime_type":"{runtime_type}",
  "answer":"{method_x_calls_method_y}",
  "your_explanation":"{your_explanation}"]}}"""


def get_prompt_example(caller, caller_fqn, callee_fqn, caller_class, callee_class, funcname,
               caller_ancestors, caller_descendants, callee_ancestors, callee_descendants, mvs,
               invocation_line, receiver_object, declared_type, runtime_type,
               method_x_calls_method_y, your_explanation):

  return get_input(caller, caller_fqn, callee_fqn, caller_class, callee_class, funcname,
               caller_ancestors, caller_descendants, callee_ancestors, callee_descendants, mvs) + get_output(invocation_line, receiver_object, declared_type, runtime_type, method_x_calls_method_y, your_explanation)


def get_prompt_example_by(id='-1', expected_program_idx='-1', expected_idx='-1', iclset_filepath=ICLSET_FILEPATH):
  example = ''
  with open(iclset_filepath, 'r') as f:
    dataset_csv_reader = csv.reader(f)
    headers = next(dataset_csv_reader)
    # 逐行读取CSV数据
    for i, row in enumerate(dataset_csv_reader, start=1):
      id,program_idx,file_path,idx,src,dst,src_code,dst_code,sa_lb_direct,sa_lb,da_lb,dst_name_match,dst_funcname,actual_lb,actual_lb_trans,is_static,src_class,mvs,src_ancestors,src_descendants,dst_class,dst_ancestors,dst_descendants,invocation_line,receiver_object,declared_type,runtime_type,class_B,method_x_calls_method_y,your_explanation=row
      if int(id) == int(id) or (int(program_idx) == int(expected_program_idx) and int(expected_idx) == int(idx)):
        example = get_prompt_example(caller=src_code, caller_fqn=src, callee_fqn=dst, caller_class=src_class, funcname=dst_funcname,
                          callee_class=dst_class, caller_ancestors=src_ancestors, caller_descendants=src_descendants, callee_ancestors=dst_ancestors, callee_descendants=dst_descendants, mvs=mvs,
                          invocation_line=invocation_line, receiver_object=receiver_object, declared_type=declared_type, runtime_type=runtime_type,
                          method_x_calls_method_y=method_x_calls_method_y, your_explanation=your_explanation)
        break
  return example

# 在 prompt 中加上示例
def get_prompt_icl(few_shot_examples, caller, caller_fqn, callee_fqn, funcname, caller_class, callee_class, caller_ancestors, caller_descendants, callee_ancestors, callee_descendants, mvs):
  cur_input = get_input(caller, caller_fqn, callee_fqn, caller_class, callee_class, funcname,
               caller_ancestors, caller_descendants, callee_ancestors, callee_descendants, mvs) + 'output:'
  pre = '''A Java static analysis tool indicates that method x invokes method y.
Your task is to determine whether method x in class A calls method y in class B.
Step 1: Please speculate on 'invocation_line', the code fragment most likely to call method y in method x.
Step 2: Retrieve the 'receiver_object', which is the receiver object of 'invocation_line'. For "ro.foo()", 'receiver_object' is "ro"; for "bar()", 'receiver_object' is 'this'; for 'new Clazz()' or '(Clazz) obj', 'receiver_object' is "Clazz".
Step 3: Predict 'declared_type' and 'runtime_type', which represent the declared and runtime type of the receiver object.
Step 4: If 'runtime_type' is unknown, proceed to step 5. Compare 'runtime_type' with 'class_B'. If they are equal, it means that method x invokes method y. The answer is "YES"; otherwise, it is "NO".
Step 5: Compare 'declared_type' with 'class_B'. If they are equal or have an inheritance relationship, it is likely that method x invokes method y. So, the answer is "YES"; otherwise, it is "NO".
Some background information will be provided as a JSON object. The keys are as follows: "fqn" for "fully qualified name", "ancestors" for "ancestor classes", "descendants" for "descendant classes".
Format your response as a JSON object with keys ["invocation_line", "receiver_object", "declared_type", "runtime_type", "answer", "your_explanation"]. If the information cannot be inferred, use "unknown" as the value. Keep your response as concise as possible.

'''
  for item in few_shot_examples:
    program_idx = item[0]
    idx = item[1]
    example = get_prompt_example_by(expected_program_idx=program_idx, expected_idx=idx)
    if num_tokens_from_string(example) + num_tokens_from_string(pre + cur_input) > INPUT_TOKEN_LIMIT:
      continue
    pre += example
  prompt = pre + cur_input
  return prompt

def do_experiment(few_shot_examples, caller, caller_fqn, callee_fqn, funcname, caller_class, callee_class, caller_ancestors, caller_descendants, callee_ancestors, callee_descendants, mvs):
  prompt = get_prompt_icl(few_shot_examples, caller, caller_fqn, callee_fqn, funcname, caller_class, callee_class, caller_ancestors, caller_descendants, callee_ancestors, callee_descendants, mvs)
  response = get_response(prompt=prompt)
  if response == '':
    return '', '', ''
  response_content = get_response_content(response)
  return response, response_content, prompt

# 读取文件 valset.csv
# 读取已完成的文件的内容
def record_result_to_file(model, valset_filepath, example_type, example_num):
  example_num_str = 'inf' if example_num >= LEN_ICLSET else str(example_num)
  written_filepath = RESPONSE_DIR + model + '_' + example_type + '_' + example_num_str + '.csv'
  if not os.path.exists(written_filepath):
    new_result_file(written_filepath, ['program_idx', 'idx', 'src', 'dst', 'src_code', 'dst_code', 'response_content', 'ids', 'ids_len'])
  r_saved_filepath = RESPONSE_DIR + model + '_' + example_type + '_' + example_num_str + '_response.csv'

  # 读取到了第几行
  start_row = get_length_of_csv(written_filepath)
  with open(written_filepath, 'a') as written_file:
    written_csv_writer = csv.writer(written_file)
    with open(valset_filepath, 'r') as dataset_file:
      dataset_csv_reader = csv.reader(dataset_file)
      # 跳过前面的行
      for _ in range(start_row):
        next(dataset_csv_reader)
      # 逐行读取CSV数据
      for i, row in enumerate(dataset_csv_reader, start=1):
        # 对每行数据进行处理
        program_idx,file_path,idx,src,dst,src_code,dst_code,reason,offset,sa_lb_direct,sa_lb,da_lb,dst_name_match,dst_funcname,actual_lb,actual_lb_trans,is_static,src_class,mvs,src_ancestors,src_descendants,dst_class,dst_ancestors,dst_descendants = row
        print(program_idx,idx)
        
        ids = []
        few_shot_examples = []
        if example_type == 'complexity':
          ids = read_complexity_ids_from_file(complexity_dir = COMPLEXITY_DIR, model = model, example_num=example_num)
        elif example_type == 'random':
          ids = random.sample(range(LEN_ICLSET), example_num)
        elif example_type == 'similarity':
          # 当前数据的 input
          cur_input = get_input(caller=src_code, callee=dst_code, caller_fqn=src, callee_fqn=dst, funcname=dst_funcname, caller_class=src_class, callee_class=dst_class, caller_ancestors=src_ancestors, caller_descendants=src_descendants, mvs=mvs)
          # TODO:找到和 cur_input 最相似的向量
          print()
        few_shot_examples = get_icl_examples_by_ids(ids, example_num)

        response, response_content, prompt = do_experiment(few_shot_examples=few_shot_examples, caller=src_code, caller_fqn=src, callee_fqn=dst, funcname=dst_funcname, caller_class=src_class, callee_class=dst_class, caller_ancestors=src_ancestors, caller_descendants=src_descendants, callee_ancestors=dst_ancestors, callee_descendants=dst_descendants, mvs=mvs)
        if response == '':
          return # 报错了，终止程序
        # 1. 记录回复的 response
        extract_and_save_info_from_response(r = response, program_idx=program_idx, idx=idx, r_saved_filepath=r_saved_filepath)
        response_content = response_content.replace('"', '""')
        # 2. 记录 few-shot 的 examples
        ids_len = len(ids)
        new_row = [program_idx, idx, src, dst, src_code, dst_code, response_content, ids, ids_len]
        written_csv_writer.writerow(new_row)
        written_file.flush()

        # time.sleep(20)
  cot_steps(model=model, example_num=example_num)

record_result_to_file(model=DEFAULT_MODEL, valset_filepath=VALSET_FILEPATH, example_type='complexity', example_num=0)
