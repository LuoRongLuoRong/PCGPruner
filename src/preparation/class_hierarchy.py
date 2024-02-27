import csv
import networkx as nx
import pickle
import matplotlib.pyplot as plt
import pygraphviz  # necessary for image generation

from src.utils.code import *
from src.utils.log import logger
from src.utils.constant import *


def get_info_filepath(mode, program_idx):
    program_info_filepath = '../replication_package/info_data/' + mode + '_programs.txt'
    program_name = ''
    with open(program_info_filepath, 'r') as file:
        csv_reader = csv.reader(file)
        lines = list(csv_reader)
        if program_idx <= len(lines):
            program_name = lines[program_idx - 1][0]
        else:
            program_name = "Invalid line index."
            logger.log('get_info_filepath error: Invalid line index', program_idx)
    
    filedir = NJR_DATASET + program_name + '/info/'
    filepath_declarations = filedir + "declarations"
    filepath_classes = filedir + 'classes'
    return filepath_declarations, filepath_classes

# 从 programs 中的 declarations 获取 class 的 hierarchy
def build_class_hierarchy(mode, program_idx):
    # 1. 根据 mode 和 program_idx 获取 declarations 的 filepath
    filepath_declarations, filepath_classes = get_info_filepath(mode, program_idx)
    
    # 2. 获取 classes 的行数
    with open(filepath_classes, 'r') as f:
        # 使用readlines()函数将文件的所有行读取到一个列表中
        lines = f.readlines()
    # 使用len()函数获取行数
    line_count = len(lines)
    logger.log("line_count", line_count)
    
    # 3. 读取 declarations 中的 class    
    relationships = []  # 匹配的结果
    dict_class_idx = {}  # 创建一个字典
    dict_idx_class = {}
    count = 0  # 真实经历的 class 的行数
    
    with open(filepath_declarations, 'r') as f:        
        for line in f:
            if 'class ' in line or 'interface ' in line:
                get_class_hierarchy_from(line, relationships, dict_class_idx, dict_idx_class)
                count += 1
    
    if count != line_count:
        logger.log("ERROR: classes count not euqal int program", program_idx, "true_count =", line_count, "calculated_count =", count)
        
        
    # 4. 将结果存成有向图
    directed_graph = create_directed_graph()  # 使用 idx 记录，虽然不够直观
    for item in relationships:
        child = dict_class_idx[item[0]]
        relationship = item[1]
        parent = dict_class_idx[item[2]]
        add_parent_child_relationship(graph=directed_graph, parent=parent, child=child)
    # # 存储有向图及必要数据到文件
    save_graph_filepath = save_graph_filepath = get_filename_by(program_idx=program_idx, mode=mode)
    data = {'directed_graph': directed_graph, 'dict_class_idx': dict_class_idx, 'dict_idx_class': dict_idx_class, 'relationships': relationships}
    save_graph_to_file(data, save_graph_filepath)
    
    # 可视化有向图
    visualize(directed_graph, program_idx)

    logger.log("len(relationships) =", len(relationships))
    logger.log("类的个数 =", len(dict_class_idx))


def add_class_to_dict(class_name, dict_class_idx, dict_idx_class, idx):
    if class_name not in dict_class_idx:
        dict_class_idx[class_name] = idx
        dict_idx_class[idx] = class_name
        return 1
    return 0


def split_interfaces_ignore_commas_and_spaces(input_string):
    count = 0
    relationships = []
    substring = ""
    
    left_brackets = ['<', '[', '(']
    right_brackets = ['>', ']', ')']

    for c in input_string:
        if c == "," and count == 0:
            if substring:
                if substring.endswith(','):
                    substring = substring[:-1]
                relationships.append(substring)
            substring = ""
            continue
            
        if c == ' ' and count == 0:
            continue
            
        if c in left_brackets:
            count += 1
        elif c in right_brackets:
            count -= 1            
        substring += c            

    if substring:
        relationships.append(substring)

    logger.log('接口 =', relationships)
    return relationships


# 获取三个数中的最小的非负数
def min_ge_zero(std, p, q):
    # std 肯定是非负数
    if p >= 0 and q >= 0:
        return min(p, q)
    if p >= 0:
        return p
    if q >= 0:
        return q
    return std


def get_class_hierarchy_from(text, relationships=[], dict_class_idx={}, dict_idx_class={}):
    logger.log('text =', text)
    # xxx class xxx extends xxx implements xxx {
    idx = len(dict_class_idx)
    
    # 1. ' {' 的位置
    end_idx = text.find(' {')
    if end_idx == -1:
        logger.log('ERROR: end not found, text =', text)
        return
    
    # 2. class 的位置
    class_word = 'class ' if 'class ' in text else 'interface '
    class_idx = text.find(class_word)   
    if end_idx == -1:
        logger.log('ERROR: class/interface not found, text =', text)
        return 
    # logger.log('class_idx', class_idx)
    
    # 3. implements 的位置
    implements_word = ' implements '
    implements_idx = text.find(implements_word, class_idx)
    
    # 4. extends 的位置
    extends_word = ' extends '
    extends_idx = text.find(extends_word, class_idx)
    
    # 1) 获取 classname    
    class_name_start = class_idx + len(class_word)
    class_name_end = min_ge_zero(std=end_idx, p=implements_idx, q=extends_idx)
    class_name = text[class_name_start : class_name_end]
    # logger.log('class_name =', class_name)
    idx += add_class_to_dict(class_name=class_name, dict_class_idx=dict_class_idx, dict_idx_class=dict_idx_class, idx=idx)
    
    # 2) 获取 extends
    if extends_idx != -1:
        parent_start = extends_idx + len(extends_word)
        parent_end = min_ge_zero(std=end_idx, p=implements_idx, q=end_idx)
        parent_name = text[parent_start : parent_end]
        # logger.log('parent_name =', parent_name)
        relationships.append([class_name, "extends", parent_name])
        idx += add_class_to_dict(class_name=parent_name, dict_class_idx=dict_class_idx, dict_idx_class=dict_idx_class, idx=idx)
        
    # 3) 获取 implements
    if implements_idx != -1:
        interfaces_start = implements_idx + len(implements_word)
        interfaces_end = end_idx
        interfaces = text[interfaces_start : interfaces_end]
        # logger.log('interfaces =', interfaces)
        
        items = split_interfaces_ignore_commas_and_spaces(interfaces)
        for interface in items:
            interface_class = interface.strip()
            relationships.append([class_name, "implements", interface_class])            
            idx += add_class_to_dict(class_name=interface_class, dict_class_idx=dict_class_idx, dict_idx_class=dict_idx_class, idx=idx)

# 根据 program_idx 获取 graph 存储的位置
def get_filename_by(program_idx, mode='test'):
    filename = CLASS_HIERARCHY_DIR + mode + str(program_idx) + '.pkl'
    return filename

def get_graph_by(program_idx, mode='test'):
    filename = get_filename_by(program_idx, mode)
    data = load_graph_from_file(filename)
    graph = data['directed_graph']
    return graph

def get_data_by(program_idx, mode='test'):
    filename = get_filename_by(program_idx, mode)
    data = load_graph_from_file(filename)
    graph = data['directed_graph']
    dict_class_idx = data['dict_class_idx']
    dict_idx_class = data['dict_idx_class']
    return graph, dict_class_idx, dict_idx_class

# 创建一个有向图
def create_directed_graph():
    return nx.DiGraph()

# 添加父子关系到有向图
def add_parent_child_relationship(graph, parent, child):
    graph.add_edge(parent, child)  # child -> parent
    
# 定义一个函数来找到所有父节点
def find_all_parents(graph, dict_idx_class, node_idx):
    parents = []
    if node_idx not in graph:
        return parents
    for parent in graph.predecessors(node_idx):
        parents.append(dict_idx_class[parent])
        parents.extend(find_all_parents(graph, dict_idx_class, parent))
    return parents

# 定义一个函数来找到所有子节点，node_idx 是个数字
def find_all_children(graph, dict_idx_class, node_idx):
    children = []
    if node_idx not in graph:
        return children
    for child in graph.successors(node_idx):
        children.append(dict_idx_class[child])
        children.extend(find_all_children(graph, dict_idx_class, child))
    return children

# 判断节点是否是另一个节点的父节点或祖先节点
def is_ancestor(program_idx, ancestor, descendant):
    ancestor = fqn_to_class(ancestor)
    descendant = fqn_to_class(descendant)
        
    filename = get_filename_by(program_idx)
    data = load_graph_from_file(filename)
    graph = data['directed_graph']
    dict_class_idx = data['dict_class_idx']
    
    ancestor_idx = dict_class_idx[ancestor]
    descendant_idx = dict_class_idx[descendant]
    return nx.has_path(graph, ancestor_idx, descendant_idx)

# 给定 ro 在 caller 中的声明类型 declared_type，判断它是不是 callee 的 node_idx 的父类
def is_ancestor_from(program_idx, declared_type, descendant, mode='test'):        
    # 两个类相等
    descendant = fqn_to_class(descendant)
    if descendant.endswith(declared_type):
        return True
    
    # 找到 node_idx 的所有父类及祖先类
    filename = get_filename_by(program_idx, mode)
    data = load_graph_from_file(filename)
    graph = data['directed_graph']
    dict_class_idx = data['dict_class_idx']
    dict_idx_class = data['dict_idx_class']
    
    descendant_idx = dict_class_idx[descendant]
    parents = find_all_parents(graph, dict_idx_class, descendant_idx)
    for p in parents:
        if p.endswith(declared_type):
            return True
    return False


# 存储有向图到文件
def save_graph_to_file(data, filename):    
    with open(filename, 'wb') as file:
        pickle.dump(data, file)

# 从文件中加载有向图
def load_graph_from_file(filename):
    logger.log(filename)
    with open(filename, 'rb') as file:
        graph = pickle.load(file)
    return graph

def visualize(directed_graph, program_idx, mode='test'):
    directed_graph = directed_graph.reverse()
    
    # 绘制足够大的图
    plt.figure(figsize=(24, 16))
    
    # 使用Graphviz布局
    pos = nx.nx_agraph.graphviz_layout(directed_graph, prog='dot')

    # 绘制有向图
    nx.draw(directed_graph, pos, with_labels=True, node_size=500, node_color='skyblue', font_size=10, font_color='black', font_weight='bold')
    plt.show()
    
    # 保存图表为图片文件
    plt.savefig('info/class_hierarchy_pics/' + mode + str(program_idx) + '.png')
    # 显示图表
    plt.show()
    
    
# 将全限定名转换为 class 的名字，示例如下：
# fr/inria/optimization/cmaes/logger.logfFormat.<init>:(Ljava/util/Locale;Ljava/lang/String;)V
# fr.inria.optimization.cmaes.logger.logfFormat
# fr/inria/optimization/cmaes/CMAEvolutionStrategy$StopCondition.test:()I
# fr.inria.optimization.cmaes.CMAEvolutionStrategy$StopCondition
def fqn_to_class(fqn):
    # 将 / 转成 . 碰到 . 就结束匹配
    dot_idx = fqn.find('.')   
    path = fqn[:dot_idx] 
    path = path.replace('/', '.')
    return path
    
def find_all_parents_from(program_idx, fqn, mode='test'):
    graph, dict_class_idx, dict_idx_class = get_data_by(program_idx, mode)
    node = fqn_to_class(fqn)
    if node not in dict_class_idx:
        logger.log(f'>>> {program_idx} - {fqn} 【三方库】')
        return ''
    node_idx = dict_class_idx[node]
    
    parents = find_all_parents(graph, dict_idx_class, node_idx)
    # logger.log(f'>>> {program_idx} - {fqn} 【{node_idx}】')
    # logger.log('父节点：')
    # # 使用join方法将列表元素用括号分隔并形成字符串
    result = "[" + "][".join(map(str, parents)) + "]"
    return result


# 给定一个 program_idx 和 callee 的 全限定名，判断它是否存在。
# 确保 node 没有子类
def find_all_children_from(program_idx, fqn, mode='test'):
    graph, dict_class_idx, dict_idx_class = get_data_by(program_idx, mode)
    node = fqn_to_class(fqn)
    if node not in dict_class_idx:
        logger.log(f'>>> {program_idx} - {fqn} 【三方库】')
        return ''
    node_idx = dict_class_idx[node]
    
    children = find_all_children(graph, dict_idx_class, node_idx)
    result = "[" + "][".join(map(str, children)) + "]"
    return result   


def find_all_relatives_from(program_idx, fqn, mode='test'):
    graph, dict_class_idx, dict_idx_class = get_data_by(program_idx, mode)
    node = fqn_to_class(fqn)
    if node not in dict_class_idx:
        logger.log(f'>>> {program_idx} - {fqn} 【三方库】')
        return '', ''
    node_idx = dict_class_idx[node]
    
    parents = find_all_parents(graph, dict_idx_class, node_idx)
    parents = "[" + "][".join(map(str, parents)) + "]"
    
    children = find_all_children(graph, dict_idx_class, node_idx)
    children = "[" + "][".join(map(str, children)) + "]"
    return parents, children

    
# 为测试集所有 programs 绘制 class_hierarchy[存储 graph + 可视化响应的 graph]
def build_class_hierarchy_for(mode):
    if mode == 'test':
        for i in range(0, 41):
            build_class_hierarchy(mode, i + 1)        
    
    if mode == 'train':
        for i in range(0, 100):
            build_class_hierarchy(mode, i + 1)  


def test_is_ancestor():
    logger.log(is_ancestor(16, 'martin/math/MathsItem', 'martin/math/MathIm.clone:()Lmartin/math/MathsItem;'))
    
def test_is_ancestor_from():
    res = is_ancestor_from(16, 'MathExp', 'martin/math/MathExpression.add:(Lmartin/math/MathsItem;)Z')
    logger.log(res)
    
def test_get_class_hierarchy_from():
    # 定义要匹配的文本
    text = "class A extends B implements C,    D {"
    get_class_hierarchy_from(text, [], {}, {})
    
    text = "class X extends Y {"
    get_class_hierarchy_from(text, [], {}, {})
    
    text = "class E {"
    get_class_hierarchy_from(text, [], {}, {})
    
    text = "class E implements F {"
    get_class_hierarchy_from(text, [], {}, {})
    
    text = "public class tivoo.Event extends java.util.HashMap<java.lang.String, java.lang.Map<Integer, I>> implements Map<java.lang.String, java.lang.Map<Integer, I>>, hhh, gigyug {"    
    get_class_hierarchy_from(text, [], {}, {})


def test_graph_file():
    # 创建一个有向图
    directed_graph = create_directed_graph()

    # 添加父子关系
    add_parent_child_relationship(directed_graph, "A", "B")
    add_parent_child_relationship(directed_graph, "B", "C")
    add_parent_child_relationship(directed_graph, "B", "D")
    add_parent_child_relationship(directed_graph, "C", "E")

    # 存储有向图到文件
    saved_filepath = get_filename_by(program_idx="directed_graph", mode="")
    save_graph_to_file(directed_graph, saved_filepath)

    # 从文件中加载有向图
    loaded_graph = load_graph_from_file(saved_filepath)

    # 判断节点关系
    logger.log(nx.has_path(loaded_graph, "C", "D"))  # 输出 False
    logger.log(nx.has_path(loaded_graph, "B", "E"))  # 输出 True
    
    visualize(loaded_graph, program_idx="directed_graph", mode="")


if __name__ == '__main__':
    logger.log("从 programs 中的 declarations 获取 class 的 hierarchy")
    # build_class_hierarchy_for('train')
    # build_class_hierarchy_for('test')
    # build_class_hierarchy('test', 33)
    # test_graph_file()    
    # test_is_ancestor()
    # test_is_ancestor_from()
    # test_find_all_parents()
    
    mode = 'train'
    program_idx = 62
    fqn = 'org/eclipse/recommenders/jayes/util/triangulation/MinFillIn.getHeuristicValue:(Lorg/eclipse/recommenders/jayes/util/triangulation/QuotientGraph;I)I'  
    relatives = find_all_relatives_from(program_idx, fqn, mode)  
    print(relatives)

