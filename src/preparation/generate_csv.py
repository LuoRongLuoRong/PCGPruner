
import os
import random
import pandas as pd

from src.preparation.class_hierarchy import *
from src.preparation.file_structure import get_member_variables
from src.preparation.find_features import dst_func_name_in_src_code

from src.utils.file import read_config_file
from src.utils.code import *
from src.utils.log import logger
from src.utils.converter import convert, extract_function_name
from src.utils.constant import *


class CsvGenerator():
    def __init__(self, config, mode):
        self.mode = mode  # train or test
        self.config = config
        # turbo.config: BENCHMARK_CALLGRAPHS=../replication_package/raw_data/
        self.raw_data_path = self.config["BENCHMARK_CALLGRAPHS"]
        # wala.config: PROCESSED_DATA=../replication_package/processed_data/wala/
        self.processed_path = self.config["PROCESSED_DATA"]
        self.cg_file = self.config["FULL_FILE"]

        if self.mode == "train":
            self.program_lists = os.path.join(self.config["TRAINING_PROGRAMS_LIST"])
        elif self.mode == "test":
            self.program_lists = os.path.join(self.config["TEST_PROGRAMS_LIST"])
        else:
            return NotImplemented
    
    # 计算 programs 的性质，将其转换为 csv，便于人工观察、筛选
    def program_to_json(self):
        logger.log("观察静态分析工具-" + self.mode + "集-生成的数据的整体情况")
        
        with open(self.program_lists, "r") as f:
            mark_idx = 1
            for line in f: 
                logger.log(mark_idx, "（下标从1开始）")                               
                filename = line.strip()
                file_path = os.path.join(self.raw_data_path, filename, self.cg_file)

                # program_idx,file_path,idx,src,dst,src_code,dst_code,reason,sa_lb_direct,sa_lb,da_lb,dst_name_match,dst_funcname,actual_lb,actual_lb_trans,is_static,src_class,mvs,src_ancestors,src_descendants,dst_class,dst_ancestors,dst_descendants
                recorder_columns = ['file_idx', 'file_path', "idx", 'src', 'dst', 'src_code', 'dst_code','offset', 'sa_lb_direct', 'sa_lb', 'da_lb', 'dst_name_match', 'dst_funcname', 'actual_lb', 'actual_lb_trans']
                recorder = pd.DataFrame(columns=recorder_columns) 
                df = pd.read_csv(file_path)
                
                # 随机抽取出多条数据
                length = len(df['wiretap'])   
                chosen = 0
                sampled_idx = get_sampled_idx(length=length, targetLen=MAX_LEN_OF_DATA_FROM_ONE_PROGRAM)
                for i in range(length):
                    if chosen >= MAX_LEN_OF_DATA_FROM_ONE_PROGRAM:
                        break
                    if i not in sampled_idx:
                        continue
                    
                    src, dst, offset, da_lb, sa_lb, sa_lb_direct = df['method'][i], df['target'][i], df['offset'][i], df['wiretap'][i], df[self.config["SA_LABEL"]][i], df['wala-cge-0cfa-noreflect-intf-direct'][i]
                    
                    # 根据 src 和 dst 找到具体的 code，用的是无注释的代码
                    descriptor2code = load_code_wo_cmt(os.path.join(self.processed_path, filename, 'code_wo_cmt.csv'))                        
                    src_code, dst_code = '', ''
                    
                    # 确保调用者是有 body 的。
                    if src == '<boot>': continue
                    if src in descriptor2code:
                        src_code = descriptor2code[src]
                    else:
                        continue
                    
                    dst_descriptor = convert(dst)
                    dst_code = descriptor2code[dst] if dst in descriptor2code else dst_descriptor.__tocode__()
                    if len(dst_code) < MIN_LEN_OF_METHOD:
                        continue
                    
                    dst_funcname = extract_function_name(dst)
                    dst_name_match = dst_func_name_in_src_code(src, src_code, dst_funcname)
                    
                    program_idx = mark_idx

                    recorder_one_line = [program_idx, file_path, i, src, dst, src_code, dst_code, offset, sa_lb_direct, sa_lb, da_lb, dst_name_match, dst_funcname, '', ''] 
                    # 将新数据帧添加到现有数据帧的末尾
                    recorder.loc[len(recorder)] = recorder_one_line
                    chosen += 1
                    
                recorder.to_csv('info/programs-' + self.mode + '/program-' + str(mark_idx) + '.csv') 
                mark_idx += 1

        
def get_sampled_idx(length, targetLen):
    if length <= targetLen:
        return range(targetLen)
    sample_size = targetLen
    sampled_idx = random.sample(range(length), sample_size)
    return sampled_idx       
            
if __name__ == '__main__':
    config = read_config_file("config/turbo.config")
    generator = CsvGenerator(config=config, mode="test")
    generator.program_to_json()
    generator = CsvGenerator(config=config, mode="train")
    generator.program_to_json()
