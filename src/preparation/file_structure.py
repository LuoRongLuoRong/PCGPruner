# 和 Java 文件有关的功能，如 class 的成员变量和成员方法，静态方法

from src.preparation.find_features import get_caller_fqn, get_program_name_and_its_raw_data_filepath
from src.preparation.class_hierarchy import fqn_to_class, get_info_filepath

from src.utils.log import logger

# 获取某一行的成员变量
def get_member_variables(mode, program_idx, idx):
    # 1. 获取 fqn
    program_name, filepath = get_program_name_and_its_raw_data_filepath(mode, program_idx)
    fqn = get_caller_fqn(mode, filepath, idx)
    # print("program_name =", program_name)
    # print("filepath =", filepath)
    
    # 2. 根据 fqn 获得 class
    classname = fqn_to_class(fqn)
    filepath_declarations, filepath_classes = get_info_filepath(mode, program_idx)
    # print("filepath_declarations =", filepath_declarations)
    
    # 3. 根据 declarations 获得 class 的成员变量
    member_variables = get_member_variables_by(filepath_declarations, classname)
    return member_variables

    
# 根据文件名和 class 名字获取 caller 的成员变量
def get_member_variables_by(filepath_declarations, classname):
    # print("classname =", classname)
    mv_list = []
    meet_class = False
    excluede_data_type = ['int', 'long', 'short', 'char', 'double', 'boolean']
    with open(filepath_declarations, 'r') as f:
        for line in f:
            if 'class ' + classname + ' ' in line or 'interface ' + classname + ' ' in line:
                meet_class = True
                continue
            if meet_class and ('(' in line or '}' in line):break
            if not meet_class: continue
            # 排除基本数据类型
            if any(edt + ' ' in line or edt + '[' in line for edt in excluede_data_type): continue
            mv_list.append(line.strip())
    return ', '.join(mv_list)


def test_get_member_variables():
    mode, program_idx, idx = 'test', 1, 364
    member_variables = get_member_variables(mode, program_idx, idx)
    # print(member_variables)
    
    
def get_methods(mode, program_idx, idx):
    # 1. 获取 fqn
    program_name, filepath = get_program_name_and_its_raw_data_filepath(mode, program_idx)
    fqn = get_caller_fqn(mode, filepath, idx)    
    # 2. 根据 fqn 获得 class
    classname = fqn_to_class(fqn)
    filepath_declarations, filepath_classes = get_info_filepath(mode, program_idx)   
    # 3. 根据 declarations 获得 class 的方法
    methods = get_methods_by(filepath_declarations, classname)
    return methods


def get_methods_by(filepath_declarations, classname):
    # logger.log(classname)
    mv_list = []
    meet_class = False
    with open(filepath_declarations, 'r') as f:
        for line in f:
            if 'class ' + classname + ' ' in line or 'interface ' + classname + ' ' in line:
                meet_class = True
                continue
            if meet_class and '(' not in line:  # 函数
                continue
            if meet_class and '}' in line:
                break
            mv_list.append(line.strip())
    return ', '.join(mv_list)

def test_get_methods():
    mode, program_idx, idx = 'train', 8, 12648
    methods = get_methods(mode, program_idx, idx)
    logger.log(methods)

# 根据文件名和 class 名字获取其类别：抽象类，接口，普通类，三方库
def get_class_category_by(filepath, classname):
    # logger.log(classname)
    category = 'third_party'  # class 到底是 interface 还是 class
    with open(filepath, 'r') as f:
        for line in f:
            if 'class ' + classname + ' ' in line or 'interface ' + classname + ' ' in line:
                if 'abstract class' in line:
                    category = 'abstract'
                elif 'interface' in line:
                    category = 'interface'
                else:
                    category = 'class'                
                break
    return category           
            
if __name__ == '__main__':
    test_get_member_variables()
    # test_get_methods()
    