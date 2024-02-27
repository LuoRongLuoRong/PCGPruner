import re
from src.utils.descriptor import Descriptor

key_to_type = {
    'B': 'byte',
    'C': 'char',
    'D': 'double',
    'F': 'float',
    'I': 'int',
    'J': 'long',
    'S': 'short',
    'Z': 'boolean',
    'V': 'void'
}

# 从给定的路径字符串中移除对象索引，然后返回修改后的路径字符串。
# 例如，如果 source_path 是 path$01$object，
# 那么函数返回的路径将是 path$object，移除了对象索引部分的数字。
def remove_object_idx(source_path):
    prefix = source_path.split('$')[0]
    obj = source_path.split('$')[1]
    while obj.startswith(('0', '1', '2', '3', '4', '5', '6', '7', '8', '9')):
        obj = obj[1:]
    
    return '$'.join([prefix, obj])


# 从函数名称中提取出函数名、类名和源路径
def extract_function(name):
    parts = re.split('\.', name)
    # function_name = parts[1]
    function_name = extract_function_name(signature=name)
    class_name = parts[0]
    if '$' in class_name:
        class_name = remove_object_idx(class_name)

    source_path = class_name
    if '$' in source_path:
        source_path = source_path.split('$')[0]
    
    if '$' in function_name:
        function_name = function_name.split('$')[0]        

    return function_name, class_name, source_path


def extract_return_type(des):
    type = ''
    while des.startswith('['):
        type = type + '[]'
        des = des[1:]
    if des.startswith('L') and des.endswith(';'):
        type = re.split('/', des)[-1][:-1] + type
    else:
        type = key_to_type[des] + type
    if "$" in type:
        type = type.split('$')[-1]

    return type


def extract_params(des):
    if des == '':
        return []
    params = []
    parts = re.split(';', des)
    for part in parts:
        type = ''
        while len(part) > 0:
            if part.startswith('['):
                type = type + '[]'
                part = part[1:]
            else:
                if not part.startswith('L'):
                    type = key_to_type[part[0]] + type
                    params.append(type)
                    type = ''
                    part = part[1:]
                else:
                    type = re.split('/', part)[-1] + type
                    params.append(type)
                    break

    return params


def remove_params_idx(params):
    result = []
    for param in params:
        if '$' in param:
            result.append(param.split('$')[0])
        else:
            result.append(param)

    return result

# 从 description 或者 descriptor 中抽取出函数的名称。举例：
# 1. de/codesourcery/engine/linalg/Vector4.toString:()Ljava/lang/String; 抽取出 toString；
# 2. de/codesourcery/engine/Test3D.run:()V抽取出 run；
# 3. de/codesourcery/engine/Test3D.main:([Ljava/lang/String;)V 抽取出 main；
# 4. de/codesourcery/engine/render/SoftwareRenderer$PrimitiveBatch$1.compare:(Ljava/lang/Object;Ljava/lang/Object;)I 抽取出compare
# 5. org/json/JSONObject.<init>:(Lorg/json/JSONTokener;)V 原本应该是<init> 但是需要替换成类名即 JSONObject
# 6. com/bigfatplayer/hello/Calculator$calculate_args$_Fields.<init>:(Ljava/lang/String;ISLjava/lang/String;)V 原本应该是<init> 但是需要替换成近似类名即 Calculator
# 其它抽取出 ""
def extract_function_name(signature): 
    colon_index = signature.find(':') 
    if colon_index > 0:
        signature = signature[:colon_index]
    # 使用正则表达式匹配函数名称
    dot_index = signature.find('.')
    RES_NONE_VALUE = "空字符串"
    if dot_index < 0:
        # 字符串中没有点号或冒号
        return RES_NONE_VALUE
    func_name = signature[dot_index + 1:]
    # print("func_name", func_name)
    if func_name.startswith('<init'):
        # 替换 "<init>" 为类名
        last_slash_index = signature.rfind("/", 0, dot_index)
        return signature[last_slash_index + 1 : dot_index]
    else:
        return func_name


# 将给定的函数描述符转换为 Descriptor 对象。
# 提取函数名、类名、源路径、参数和返回类型，
# 并使用 remove_params_idx 函数处理参数中的索引部分。
# 最后，它创建并返回一个 Descriptor 对象。
def convert(descriptor):
    pattern = '\(|\)'
    descriptor = descriptor.replace(':', '')
    parts = re.split(pattern, descriptor)
    function_name, class_name, source_path = extract_function(parts[0])
    params = remove_params_idx(extract_params(parts[1]))
    return_type = extract_return_type(parts[2])

    return Descriptor(class_name, function_name, source_path, params, return_type)


if __name__ == '__main__':
    dst_fqn = "com/bigfatplayer/hello/Calculator$calculate_args$_Fields.<init>:(Ljava/lang/String;ISLjava/lang/String;)V"
    # dst_fqn = "TriviaQuestions/MovieTriviaQuestionFactory.buildQuestion:()LTriviaQuestions/MovieTriviaQuestion;"
    e = convert(dst_fqn)
    print(dst_fqn)
    
    print(e.__tocode__())  # class Calculator$calculate_args { void Calculator ( String a0, int a1, short a2, String a3, ) { return void1; }
    print(e.__tomethod__())  # Calculator
    