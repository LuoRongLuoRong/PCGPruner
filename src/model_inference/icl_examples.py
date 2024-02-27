

INPUT_TOKEN_LIMIT = 4080

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
               caller_ancestors, caller_descendants, callee_ancestors, callee_descendants, mvs) + get_output(invocation_line, receiver_object, declared_type, runtime_type,
               method_x_calls_method_y, your_explanation)
               
               
def get_example(expected_program_idx, expected_idx):
  example = ''
  with open(iclset_filepath, 'r') as f:
    dataset_csv_reader = csv.reader(f)
    headers = next(dataset_csv_reader)
    # 逐行读取CSV数据
    for i, row in enumerate(dataset_csv_reader, start=1):
      id,program_idx,file_path,idx,src,dst,src_code,dst_code,sa_lb_direct,sa_lb,da_lb,dst_name_match,dst_funcname,actual_lb,actual_lb_trans,is_static,src_class,mvs,src_ancestors,src_descendants,dst_class,dst_ancestors,dst_descendants,invocation_line,receiver_object,declared_type,runtime_type,class_B,method_x_calls_method_y,your_explanation=row
      if int(program_idx) == int(expected_program_idx) and int(expected_idx) == int(idx):
        example = get_prompt_example(caller=src_code, callee=dst_code, caller_fqn=src, callee_fqn=dst, caller_class=src_class, funcname=dst_funcname,
                          callee_class=dst_class, caller_ancestors=src_ancestors, caller_descendants=src_descendants, callee_ancestors=dst_ancestors, callee_descendants=dst_descendants, mvs=mvs,
                          invocation_line=invocation_line, receiver_object=receiver_object, declared_type=declared_type, runtime_type=runtime_type,
                          method_x_calls_method_y=method_x_calls_method_y, your_explanation=your_explanation)
        break
  return example

def get_prompt(caller, caller_fqn, callee_fqn, funcname, caller_class, callee_class, caller_ancestors, caller_descendants, callee_ancestors, callee_descendants, mvs, few_shot_examples):
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
    example = get_example(program_idx, idx)
    if num_tokens_from_string(example) + num_tokens_from_string(pre + cur_input) > INPUT_TOKEN_LIMIT:
      continue
    pre += example
  prompt = pre + cur_input
  return prompt

def get_response_prompt(caller, callee, caller_fqn, callee_fqn, funcname, caller_class, callee_class, caller_ancestors, caller_descendants, callee_ancestors, callee_descendants, mvs):
  prompt = get_prompt(caller, callee, caller_fqn, callee_fqn, funcname, caller_class, callee_class, caller_ancestors, caller_descendants, callee_ancestors, callee_descendants, mvs)
  # print('prompt', prompt)
  response = get_completion(prompt)
  return response, prompt

# 读取文件 valset.csv
# 读取已完成的文件的内容
def write_response_to_file(written_filepath, dataset_filepath):
  if not os.path.exists(written_filepath):
    newFile(written_filepath)

  # 读取到了第几行
  start_row = get_length_of_csv(written_filepath)

  with open(written_filepath, 'a', encoding='gbk') as written_file:

    written_csv_writer = csv.writer(written_file)

    with open(dataset_filepath, 'r') as dataset_file:
      dataset_csv_reader = csv.reader(dataset_file)
      # 跳过前面的行
      for _ in range(start_row):
        next(dataset_csv_reader)
      # 逐行读取CSV数据
      for i, row in enumerate(dataset_csv_reader, start=1):

        # 对每行数据进行处理
        program_idx,file_path,idx,src,dst,src_code,dst_code,reason,offset,sa_lb_direct,sa_lb,da_lb,dst_name_match,dst_funcname,actual_lb,actual_lb_trans,predicted_lb,is_static,src_class,mvs,src_ancestors,src_descendants,dst_class,dst_ancestors,dst_descendants = row
        # program_idx,file_path,idx,src,dst,src_code,dst_code,reason,offset,sa_lb_direct,sa_lb,da_lb,dst_name_match,dst_funcname,actual_lb,actual_lb_trans,predicted_lb,is_static,src_class,mvs,src_ancestors,src_descendants,dst_class,dst_ancestors,dst_descendants
        response, prompt = get_response_prompt(caller=src_code, callee=dst_code, caller_fqn=src, callee_fqn=dst, funcname=dst_funcname, caller_class=src_class, callee_class=dst_class, caller_ancestors=src_ancestors, caller_descendants=src_descendants, callee_ancestors=dst_ancestors, callee_descendants=dst_descendants, mvs=mvs)

        new_row = [program_idx, idx, response, prompt]
        response = response.replace('"', '""')
        print(str(program_idx) + ',' + str(idx) + ',"' + response + '",' + '""')
        written_csv_writer.writerow(new_row)

        time.sleep(20)


def read_len(written_filepath, dataset_filepath):
  if not os.path.exists(written_filepath):
    newFile(written_filepath)

  # 读取到了第几行
  start_row = get_length_of_csv(written_filepath)

  # program_idx,idx,response,result
  with open(written_filepath, 'a', encoding='gbk') as written_file:

    written_csv_writer = csv.writer(written_file)

    with open(dataset_filepath, 'r') as dataset_file:
      dataset_csv_reader = csv.reader(dataset_file)
      # 跳过前面的行
      for _ in range(start_row):
        next(dataset_csv_reader)
      # 逐行读取CSV数据
      for i, row in enumerate(dataset_csv_reader, start=1):
        # 对每行数据进行处理
        # print(len(row), row)
        program_idx,file_path,idx,src,dst,src_code,dst_code,reason,offset,sa_lb_direct,sa_lb,da_lb,dst_name_match,dst_funcname,actual_lb,actual_lb_trans,predicted_lb,is_static,src_class,mvs,src_ancestors,src_descendants,dst_class,dst_ancestors,dst_descendants = row
        # program_idx,file_path,idx,src,dst,src_code,dst_code,reason,offset,sa_lb_direct,sa_lb,da_lb,dst_name_match,dst_funcname,actual_lb,actual_lb_trans,predicted_lb,is_static,src_class,mvs,src_ancestors,src_descendants,dst_class,dst_ancestors,dst_descendants
        # program_idx,file_path,idx,src,dst,src_code,dst_code,reason,offset,sa_lb_direct,sa_lb,da_lb,dst_name_match,dst_funcname,actual_lb,actual_lb_trans,predicted_lb,is_static
        prompt = get_prompt(caller=src_code, callee=dst_code, caller_fqn=src, callee_fqn=dst, funcname=dst_funcname, caller_class=src_class, callee_class=dst_class, caller_ancestors=src_ancestors, caller_descendants=src_descendants, callee_ancestors=dst_ancestors, callee_descendants=dst_descendants, mvs=mvs)
        num_tokens = num_tokens_from_string(prompt)
        print(str(program_idx) + ',' + str(idx) + ',' + str(num_tokens))
        # print(prompt)

        new_row = [program_idx, idx, num_tokens]
        written_csv_writer.writerow(new_row)

# prompt 中有 fgn
dataset_filepath   = '/content/drive/MyDrive/ColabNotebooks/dataset/valset.csv'
# written_len_filepath = '/content/drive/MyDrive/ColabNotebooks/dataset/res_len_ablation_1.csv'
# read_len(written_filepath=written_len_filepath, dataset_filepath=dataset_filepath)
written_filepath = '/content/drive/MyDrive/ColabNotebooks/dataset/res_ablation_1.csv'
write_response_to_file(written_filepath=written_filepath, dataset_filepath=dataset_filepath)
