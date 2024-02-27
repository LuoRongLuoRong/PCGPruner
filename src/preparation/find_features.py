import csv
import os
import pandas as pd

from src.utils.code import load_code_wo_cmt
from src.utils.log import logger
from src.utils.converter import convert, extract_function_name


def get_line(mode, filepath, idx):
    '''
    mode: train or test
    path: program 所在的文件的路径
    idx: 该调用关系对所在的 idx
    '''
    idx = idx + 1  # 记录的 idx 是 df 下的，所以要 +1，去掉表头
    with open(filepath, 'r') as file:
        csv_reader = csv.reader(file)
        lines = list(csv_reader)
        if idx < len(lines):
            return lines[idx]
        else:
            logger.log(f'ERROR: filepath[{filepath}], idx[{idx}] cannot find line')
            return [""] * 32

def test_get_line():
    print(get_line('test', '../replication_package/raw_data/url433bec1e56_sarobe_DifficultyInvestigation_tgz-pJ8-fr_inria_optimization_cmaes_examples_CMAExample1J8/wala0cfa.csv', 3))
    # expected result：
    # ['1', '1', '1', '4', '4', '10', '1', '3', '1', '1', '1', '1', '158.0', '431.0', '2.7278481012658227', '1.0278422273781902', '4', '4', '10', '1', '3', '1', '1', '1', '1', '158.0', '534.0', '3.3797468354430378', '1.0374531835205993', 'fr/inria/optimization/cmaes/PrintfFormat.sprintf:(I)Ljava/lang/String;', '87', 'fr/inria/optimization/cmaes/PrintfFormat$ConversionSpecification.internalsprintf:(I)Ljava/lang/String;']

def get_funcname(mode, filepath, idx):
    dst = get_callee_fqn(mode, filepath, idx)
    return extract_function_name(dst)

def get_caller_fqn(mode, filepath, idx):
    # wala0cfa.csv 中的关键部分: method offset target
    #                           29     30     31
    # logger.log('filepath:', filepath)
    aaa = get_line(mode, filepath, idx)
    # logger.log(len(aaa), aaa)
    return get_line(mode, filepath, idx)[29]

def get_callee_fqn(mode, filepath, idx):
    return get_line(mode, filepath, idx)[31]


def get_program_name(mode, program_idx):
    program_info_filepath = '../replication_package/info_data/' + mode + '_programs.txt'
    program_name = ''
    with open(program_info_filepath, 'r') as file:
        csv_reader = csv.reader(file)
        lines = list(csv_reader)
        if program_idx <= len(lines):
            program_name = lines[program_idx - 1][0]
        else:
            program_name = "Invalid line index."
            # logger.log('error')
    return program_name


def get_program_name_and_its_raw_data_filepath(mode, program_idx):   
    program_name = get_program_name(mode, program_idx) 
    filepath = '../replication_package/raw_data/' + program_name + '/wala0cfa.csv'    
    # logger.log('program_name =', program_name)  # url416ee5b4ee_martinmarinov_HonProj_tgz-pJ8-martin_gui_MainJ8
    return program_name, filepath


def get_callees_by_caller(mode, program_idx, line_idx):    
    # line_idx = line_idx + 1  # 记录的 idx 是 df 下的，所以要 +1，去掉表头
    # program_idx = program_idx - 1  # 记录的 program_idx 是从 1 开始的
    
    # 1. 根据 mode 和 program_idx 获取 filepath
    program_name, filepath = get_program_name_and_its_raw_data_filepath(mode, filepath)
    
    # 2. 将 filepath 和 line_idx 作为入参获取 caller_fqn 和 callee_fqn
    caller_fqn = get_caller_fqn(mode, filepath, line_idx)
    callee_fqn = get_callee_fqn(mode, filepath, line_idx)
    # logger.log(caller_fqn)
    # logger.log(callee_fqn)
    
    # 3. 遍历整个 program file，将 caller_fqn 相同的都获取到，尽可能把所有属性都记录下来
    recorder_columns = ['file_idx', 'file_path', "idx", 'src', 'dst', 'src_code', 'dst_code','offset', 'sa_lb_direct', 'sa_lb', 'da_lb', 'dst_name_match', 'dst_funcname', 'actual_lb', 'data_type']
    recorder = pd.DataFrame(columns=recorder_columns) 
    df = pd.read_csv(filepath)
        
    # 随机抽取出 2000 条数据
    length = len(df['wiretap'])
    for i in range(length):    
        src, dst, offset, da_lb, sa_lb, sa_lb_direct = df['method'][i], df['target'][i], df['offset'][i], df['wiretap'][i], df['wala-cge-0cfa-noreflect-intf-trans'][i], df['wala-cge-0cfa-noreflect-intf-direct'][i]
        
        if src != caller_fqn:
            continue
        
        # 根据 src 和 dst 找到具体的 code，用的是无注释的代码
        descriptor2code = load_code_wo_cmt(os.path.join('../replication_package/processed_data/wala/' + program_name + '/code_wo_cmt.csv'))
        src_code = ''
        dst_code = ''
        
        if src == '<boot>':
            continue
        if src in descriptor2code:
            src_code = descriptor2code[src]
        # else:
        #     src_code = convert(src).__tocode__()
        
        dst_descriptor = convert(dst)
        
        if dst in descriptor2code:
            dst_code = descriptor2code[dst]
        # else:
        #     dst_code = dst_descriptor.__tocode__()
                            
        
        funcname = extract_function_name(dst)
        is_match = (funcname + '(') in src_code
        # logger.log("字符串匹配:", funcname, is_match)                    
                    
        # 如果动态分析的结果是 1，那么 actual_lb 必然是 1，数据类型 data_type 也是 0                   
        actual_lb = ''
        data_type = ''  
        
        if da_lb == 1:
            if sa_lb == 1:                            
                actual_lb = '1'  # 确实存在调用关系的意思
                data_type = '0'  # 静 1 动 1
            else:
                actual_lb = '-1'  # 不关注的意思
                data_type = '30'  # 静 0 动 1
        
        # ['file_path', "idx", 'src', 'dst', 'src_code', 'dst_code','offset', 'sa_lb_direct','sa_lb','da_lb', 'dst_name_match', 'dst_funcname', 'actual_lb', 'data_type']
        recorder_one_line = [program_idx, filepath, i, src, dst, src_code, dst_code, offset, sa_lb_direct, sa_lb, da_lb, is_match, funcname, actual_lb, data_type] 
        # 将新数据帧添加到现有数据帧的末尾
        recorder.loc[len(recorder)] = recorder_one_line
        
    recorder.to_csv('output/callees/program-' + str(program_idx) + '_' + str(line_idx) + '.csv')         
    
def get_callees_by_caller_and_funcname(mode, program_idx, line_idx):    
    # line_idx = line_idx + 1  # 记录的 idx 是 df 下的，所以要 +1，去掉表头
    # program_idx = program_idx - 1  # 记录的 program_idx 是从 1 开始的
    
    # 1. 根据 mode 和 program_idx 获取 filepath
    program_name, filepath = get_program_name_and_its_raw_data_filepath(mode, filepath)
    
    # 2. 将 filepath 和 line_idx 作为入参获取 caller_fqn 和 callee_fqn
    caller_fqn = get_caller_fqn(mode, filepath, line_idx)
    callee_fqn = get_callee_fqn(mode, filepath, line_idx)
    callee_funcname = get_funcname(mode, filepath, line_idx)
    # logger.log(caller_fqn)
    # logger.log(callee_fqn)
    # logger.log(callee_funcname)
    
    # 3. 遍历整个 program file，将 caller_fqn 相同的都获取到，尽可能把所有属性都记录下来
    recorder_columns = ['file_idx', 'file_path', "idx", 'src', 'dst', 'src_code', 'dst_code','offset', 'sa_lb_direct', 'sa_lb', 'da_lb', 'dst_name_match', 'dst_funcname', 'actual_lb', 'data_type']
    recorder = pd.DataFrame(columns=recorder_columns) 
    df = pd.read_csv(filepath)
        
    # 随机抽取出 2000 条数据
    length = len(df['wiretap'])
    for i in range(length):    
        src, dst, offset, da_lb, sa_lb, sa_lb_direct = df['method'][i], df['target'][i], df['offset'][i], df['wiretap'][i], df['wala-cge-0cfa-noreflect-intf-trans'][i], df['wala-cge-0cfa-noreflect-intf-direct'][i]
        
        if src != caller_fqn:
            continue
        
        funcname = extract_function_name(dst)  # line 的 funcname
        if funcname != callee_funcname:
            continue
        
        # 根据 src 和 dst 找到具体的 code，用的是无注释的代码
        descriptor2code = load_code_wo_cmt(os.path.join('../replication_package/processed_data/wala/' + program_name + '/code_wo_cmt.csv'))
        src_code = ''
        dst_code = ''                
        
        if dst in descriptor2code:
            dst_code = descriptor2code[dst]
        
        is_match = (funcname + '(') in src_code
        # logger.log("字符串匹配:", funcname, is_match)                    
                    
        # 如果动态分析的结果是 1，那么 actual_lb 必然是 1，数据类型 data_type 也是 0                   
        actual_lb = ''
        data_type = ''  
        
        if da_lb == 1:
            if sa_lb == 1:                            
                actual_lb = '1'  # 确实存在调用关系的意思
                data_type = '0'  # 静 1 动 1
            else:
                actual_lb = '-1'  # 不关注的意思
                data_type = '30'  # 静 0 动 1
        
        # ['file_path', "idx", 'src', 'dst', 'src_code', 'dst_code','offset', 'sa_lb_direct','sa_lb','da_lb', 'dst_name_match', 'dst_funcname', 'actual_lb', 'data_type']
        recorder_one_line = [program_idx, filepath, i, src, dst, src_code, dst_code, offset, sa_lb_direct, sa_lb, da_lb, is_match, funcname, actual_lb, data_type] 
        # 将新数据帧添加到现有数据帧的末尾
        recorder.loc[len(recorder)] = recorder_one_line
        
    recorder.to_csv('output/callees/program-' + str(program_idx) + '_' + str(line_idx) + '.csv')         
 
    
def test_get_callees_by_caller():
    mode = 'test'
    program_idx = 15
    line_idx = 666
    get_callees_by_caller(mode, program_idx, line_idx)
    
    
def get_callers_by_callee(mode, program_idx, line_idx):
    # line_idx = line_idx + 1  # 记录的 idx 是 df 下的，所以要 +1，去掉表头
    # program_idx = program_idx - 1  # 记录的 program_idx 是从 1 开始的
    
    # 1. 根据 mode 和 program_idx 获取 filepath    
    program_name, filepath = get_program_name_and_its_raw_data_filepath(mode, filepath)
    
    # 2. 将 filepath 和 line_idx 作为入参获取 caller_fqn 和 callee_fqn
    caller_fqn = get_caller_fqn(mode, filepath, line_idx)
    callee_fqn = get_callee_fqn(mode, filepath, line_idx)
    # logger.log(caller_fqn)
    # logger.log(callee_fqn)
    
    # 3. 遍历整个 program file，将 caller_fqn 相同的都获取到，尽可能把所有属性都记录下来
    recorder_columns = ['file_idx', 'file_path', "idx", 'src', 'dst', 'src_code', 'dst_code','offset', 'sa_lb_direct', 'sa_lb', 'da_lb', 'dst_name_match', 'dst_funcname', 'actual_lb', 'data_type']
    recorder = pd.DataFrame(columns=recorder_columns) 
    df = pd.read_csv(filepath)
        
    # 随机抽取出 2000 条数据
    length = len(df['wiretap'])
    for i in range(length):    
        src, dst, offset, da_lb, sa_lb, sa_lb_direct = df['method'][i], df['target'][i], df['offset'][i], df['wiretap'][i], df['wala-cge-0cfa-noreflect-intf-trans'][i], df['wala-cge-0cfa-noreflect-intf-direct'][i]
        
        if dst != callee_fqn:
            continue
        
        # 根据 src 和 dst 找到具体的 code，用的是无注释的代码
        descriptor2code = load_code_wo_cmt(os.path.join('../replication_package/processed_data/wala/' + program_name + '/code_wo_cmt.csv'))
        src_code = ''
        dst_code = ''
        
        if src == '<boot>':
            continue
        if src in descriptor2code:
            src_code = descriptor2code[src]
        
        dst_descriptor = convert(dst)
        
        if dst in descriptor2code:
            dst_code = descriptor2code[dst]
        # else:
        #     dst_code = dst_descriptor.__tocode__()
                            
        
        funcname = extract_function_name(dst)
        is_match = (funcname + '(') in src_code
        # logger.log("字符串匹配:", funcname, is_match)                    
                    
        # 如果动态分析的结果是 1，那么 actual_lb 必然是 1，数据类型 data_type 也是 0                   
        actual_lb = ''
        data_type = ''  
        
        if da_lb == 1:
            if sa_lb == 1:                            
                actual_lb = '1'  # 确实存在调用关系的意思
                data_type = '0'  # 静 1 动 1
            else:
                actual_lb = '-1'  # 不关注的意思
                data_type = '30'  # 静 0 动 1
        
        # ['file_path', "idx", 'src', 'dst', 'src_code', 'dst_code','offset', 'sa_lb_direct','sa_lb','da_lb', 'dst_name_match', 'dst_funcname', 'actual_lb', 'data_type']
        recorder_one_line = [program_idx, filepath, i, src, dst, src_code, dst_code, offset, sa_lb_direct, sa_lb, da_lb, is_match, funcname, actual_lb, data_type] 
        # 将新数据帧添加到现有数据帧的末尾
        recorder.loc[len(recorder)] = recorder_one_line
        
    recorder.to_csv('output/callers/program-' + str(program_idx) + '_' + str(line_idx) + '.csv')   

# src 是指 function 的全限定名
# src_code 是指 function 的整个部分
# funcname 是指 dst_code 的名称
def dst_func_name_in_src_code(src, src_code, funcname):
    return src == '<boot>' or funcname in src_code    
    
def test_get_callers_by_callee():
    mode = 'test'
    program_idx = 15
    line_idx = 666
    # fqn：fully qualified name 全限定名
    caller_fqn = 'com/zeroturnaround/rebellabs/oceanofmemories/common/util/JvmUtil.init:()V'
    callee_fqn = 'com/zeroturnaround/rebellabs/oceanofmemories/common/util/JvmUtil$Address64BitWithCompressedOopsJvmUtil.<init>:(Lcom/zeroturnaround/rebellabs/oceanofmemories/common/util/JvmUtil$1;)V'
    get_callers_by_callee(mode, program_idx, line_idx)

def test_get_program_name():
    print(get_program_name('test', 1))

if __name__ == '__main__':
    # test_get_line()
    test_get_program_name()
    # test_get_callees_by_caller()
    # test_get_callers_by_callee()
    # get_callers_by_callee('test', 36, 5286)
    # get_callees_by_caller_and_funcname('test', 23, 710)
    # get_callees_by_caller('test', 25, 1339)
    
    
