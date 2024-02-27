# PCGPruner
《基于提示工程的静态调用图剪枝方法》

## 数据

### 原始数据集

原始数据集来自[AutoPruner](https://github.com/soarsmu/AutoPruner)，其数据集的下载网址：https://zenodo.org/records/6369874#.ZBlU2XZBzb2

下载完毕后，使用 `tar -zxvf` 命令解压 data.tar.gz 文件，该数据集的详细介绍见[AutoPruner数据集介绍](https://github.com/soarsmu/AutoPruner?tab=readme-ov-file#-repository-organization)。

### 本文数据集
本文构造的数据集在 data 文件夹 下，其中的文件含义如下：

- valset.csv: 人工构造的验证数据集
- fewshot.csv: 用于上下文学习的示例数据集

## 