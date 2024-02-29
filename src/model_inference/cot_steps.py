
import csv
import json
import os

RESPONSE_DIR = ''
LEN_ICLSET = 60

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

# cot_steps(model='gpt-3.5-turbo-0125', example_num=60)
# cot_steps(model='gpt-3.5-turbo-0125', example_num=12)

# str1 = '''[
#   ""invocation_line"": ""cs.internalsprintf(x)"",
#   ""receiver_object"": ""cs"",
#   ""declared_type"": ""ConversionSpecification"",
#   ""runtime_type"": ""ConversionSpecification"",
#   ""answer"": ""YES"",
#   ""your_explanation"": ""Method x calls method y on the object cs, which is of type ConversionSpecification. Both the declared and runtime types match the class B, which is fr.inria.optimization.cmaes.PrintfFormat$ConversionSpecification. Therefore, method x in class A calls method y in class B.""
# ]'''
# result = extract_content(str1.replace('""', '"'))
# print(result.get('invocation_line1', ''))
