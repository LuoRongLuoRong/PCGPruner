
import pandas as pd

# 将字符串列表中的元素转换为单行字符串，同时移除多余的空格，使得单词之间只有一个空格分隔。
def load_code(path):
    data = {}
    df = pd.read_csv(path)
    descriptor = df['descriptor']
    code = df['code']
    for i in range(len(descriptor)):
        if isinstance(code[i], str):
            data[descriptor[i]] = code[i]
    return data

# descriptor2code = self.load_code_wo_cmt(os.path.join(self.processed_path, filename, 'code_wo_cmt.csv')) 
def load_code_wo_cmt(path):
    data = {}
    df = pd.read_csv(path)
    descriptor = df['descriptor']
    code = df['code_wo_cmt']
    for i in range(len(descriptor)):
        # if not isinstance(code[i], str):
        if "fr/inria/optimization/cmaes/examples/Rosenbrock.isFeasible:([D)Z" is descriptor[i]:
            print(isinstance(code[i], str), code[i], "*" * 100, descriptor[i])
            input("点击运行……")  
            print("\n")
        if isinstance(code[i], str):
            data[descriptor[i]] = code[i]
    return data
    
