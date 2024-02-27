
from src.preparation.find_features import *
from src.preparation.class_hierarchy import *
from src.preparation.file_structure import *

from src.utils.constant import *


# 根据人工得到的结果获取其他信息
# iclset_idx: 
# program_idx,file_path,idx,src,dst,src_code,dst_code,offset,sa_lb_direct,sa_lb,da_lb,dst_name_match,dst_funcname,actual_lb,actual_lb_trans
# iclset：
# program_idx,file_path,idx,src,dst,src_code,dst_code,sa_lb_direct,sa_lb,da_lb,dst_name_match,dst_funcname,actual_lb,actual_lb_trans,is_static,src_class,mvs,src_ancestors,src_descendants,dst_class,dst_ancestors,dst_descendants
# 还需要人工添加的信息：invocation_line,receiver_object,declared_type,runtime_type,class_B,method_x_calls_method_y,	your_explanation

def complete_iclset(set_idx_path = 'info/iclset/iclset_idx.csv', set_path = 'info/iclset/iclset_pre.csv', mode = 'train'):
    # run once 
    set_idx_file = open(set_idx_path, 'r')
    csv_reader = csv.reader(set_idx_file)
    csv_reader_header = ["program_idx","file_path","idx","src","dst","src_code","dst_code","offset","sa_lb_direct","sa_lb","da_lb","dst_name_match","dst_funcname","actual_lb","actual_lb_trans"]
    
    written_file = open(set_path, 'w', encoding='gbk')
    csv_writer = csv.writer(written_file)
    csv_write_header = ['id',"program_idx","file_path","idx","src","dst","src_code","dst_code","sa_lb_direct","sa_lb","da_lb","dst_name_match","dst_funcname","actual_lb","actual_lb_trans","is_static","src_class","mvs","src_ancestors","src_descendants","dst_class","dst_ancestors","dst_descendants","invocation_line","receiver_object","declared_type","runtime_type","class_B","method_x_calls_method_y","your_explanation"]
    csv_writer.writerow(csv_write_header)  # 添加表头
    
    # 获取表头（第一行）
    headers = next(csv_reader)
    print(headers)
    # 逐行读取CSV数据
    id = 0
    for row in csv_reader:
        # 对每行数据进行处理
        program_idx,file_path,idx,actual_lb,actual_lb_trans = row[0],row[1],row[2],row[-2],row[-1]
        sa_lb_direct,sa_lb,da_lb= row[8],row[9],row[10]
        
        program_idx = int(program_idx)
        idx = int(idx)
        
        # mode, program_idx, idx
        src = get_caller_fqn(mode, file_path, idx)
        dst = get_callee_fqn(mode, file_path, idx)
        
        # 根据 src 和 dst 找到具体的 code，用的是无注释的代码
        descriptor2code = load_code_wo_cmt(os.path.join(PROCESSED_PATH, get_program_name(mode, program_idx), 'code_wo_cmt.csv'))    
        src_code, dst_code = '', ''
                    
        # 确保调用者是有 body 的。
        if src == '<boot>': continue
        if src in descriptor2code:
            src_code = descriptor2code[src]
        else:
            continue
        
        dst_descriptor = convert(dst)
        dst_code = descriptor2code[dst] if dst in descriptor2code else dst_descriptor.__tocode__()
        
        dst_funcname = extract_function_name(dst)
        dst_name_match = dst_func_name_in_src_code(src, src_code, dst_funcname)
        is_static = 'static' in dst_code
        
        # - 方法 A 所在的类的名称 A_Class【新增】        
        src_class = fqn_to_class(src)
        # - A_Class 的成员变量【新增】
        mvs = get_member_variables(mode, program_idx, idx)
        # - A_Class 的 ancestors【新增】
        # - A_Class 的 descendants【新增】
        src_ancestors, src_descendants = find_all_relatives_from(program_idx, src, mode)
        # - 方法 B 所在的类的名称 B_Class【新增】
        dst_class = fqn_to_class(dst)
        # - B_Class 的 ancestors【新增】
        # - B_Class 的 descendants【新增】
        dst_ancestors, dst_descendants = find_all_relatives_from(program_idx, dst, mode)
        
        # new_line = [id,program_idx,file_path,idx,src,dst,src_code,dst_code,sa_lb_direct,sa_lb,da_lb,dst_name_match,dst_funcname,actual_lb,actual_lb_trans,is_static,src_class,mvs,src_ancestors,src_descendants,dst_class,dst_ancestors,dst_descendants,invocation_line,receiver_object,declared_type,runtime_type,class_B,method_x_calls_method_y,your_explanation]
        
        new_row = [id,program_idx,file_path,idx,src,dst,src_code,dst_code,sa_lb_direct,sa_lb,da_lb,dst_name_match,dst_funcname,actual_lb,actual_lb_trans,is_static,src_class,mvs,src_ancestors,src_descendants,dst_class,dst_ancestors,dst_descendants,'','','','',dst_class,'YES' if str(actual_lb_trans)=='1' else 'NO','']  # invocation_line,receiver_object,declared_type,runtime_type,class_B,method_x_calls_method_y,your_explanation
        csv_writer.writerow(new_row) 
        id += 1
        
        

if __name__ == '__main__':
    complete_iclset()