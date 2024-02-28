from src.utils.constant import *
import csv
from src.model_inference.complexity import num_tokens_from_string

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


# iclset
def get_output(invocation_line, receiver_object, declared_type, runtime_type,
               method_x_calls_method_y, your_explanation):
  return f"""output: {{
  "invocation_line":"{invocation_line}",
  "receiver_object":"{receiver_object}",
  "declared_type":"{declared_type}",
  "runtime_type":"{runtime_type}",
  "answer":"{method_x_calls_method_y}",
  "your_explanation":"{your_explanation}"]}}"""
  
# iclset
def get_prompt_example(caller, caller_fqn, callee_fqn, caller_class, callee_class, funcname,
               caller_ancestors, caller_descendants, callee_ancestors, callee_descendants, mvs,
               invocation_line, receiver_object, declared_type, runtime_type,
               method_x_calls_method_y, your_explanation):
  
  return get_input(caller, caller_fqn, callee_fqn, caller_class, callee_class, funcname,
               caller_ancestors, caller_descendants, callee_ancestors, callee_descendants, mvs) + get_output(invocation_line, receiver_object, declared_type, runtime_type,
               method_x_calls_method_y, your_explanation)



# 获取示例的 prompt，               
def get_prompt_example_by(id, expected_program_idx, expected_idx, iclset_filepath=ICLSET_FILEPATH):
  example = ''
  with open(iclset_filepath, 'r') as f:
    dataset_csv_reader = csv.reader(f)
    headers = next(dataset_csv_reader)
    # 逐行读取CSV数据
    for i, row in enumerate(dataset_csv_reader, start=1):
      id,program_idx,file_path,idx,src,dst,src_code,dst_code,sa_lb_direct,sa_lb,da_lb,dst_name_match,dst_funcname,actual_lb,actual_lb_trans,is_static,src_class,mvs,src_ancestors,src_descendants,dst_class,dst_ancestors,dst_descendants,invocation_line,receiver_object,declared_type,runtime_type,class_B,method_x_calls_method_y,your_explanation=row
      if int(id) == int(id) or (int(program_idx) == int(expected_program_idx) and int(expected_idx) == int(idx)):
        example = get_prompt_example(caller=src_code, callee=dst_code, caller_fqn=src, callee_fqn=dst, caller_class=src_class, funcname=dst_funcname,
                          callee_class=dst_class, caller_ancestors=src_ancestors, caller_descendants=src_descendants, callee_ancestors=dst_ancestors, callee_descendants=dst_descendants, mvs=mvs,
                          invocation_line=invocation_line, receiver_object=receiver_object, declared_type=declared_type, runtime_type=runtime_type,
                          method_x_calls_method_y=method_x_calls_method_y, your_explanation=your_explanation)
        break
  return example

if __name__ == '__main__':
  for i in range(0, 61):
    prompt_exmaple = get_prompt_example_by(i, '', '')
    length = num_tokens_from_string(prompt_exmaple)
    print(i, length)
