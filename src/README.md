本文件夹用于数据库处理相关。

# 目的

本文件夹的目的是从 AutoPruner 的数据集（本文将该数据集命名为 CGPrunerSet）中构建高质量调用关系数据集 ValSet 数据集和 IclSet 数据集，其含义如下：

- ValSet: 从 CGPrunerSet 训练集中挑选的数据。
- IclSet: 从 CGPrunerSet 测试集中挑选的数据。

# 子文件夹

子文件夹的含义如下：

- preparation: 用于获取构建 ValSet 数据集和 IclSet 数据集所需要的信息。
- construction: 用于从上一步骤获取到的信息，构建出 valset。

## preparation

1. generate_csv.py: 从 CGPrunerSet 中生成可以方便人工观察和标注的数据
2. 

## construction

