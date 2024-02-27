# This program demos how to connect to Milvus vector database, 
# create a vector collection,
# insert 10 vectors, 
# and execute a vector similarity search.

import random

from milvus import Milvus, IndexType, MetricType, Status

# Milvus server IP address and port.
# You may need to change _HOST and _PORT accordingly.
_HOST = '127.0.0.1'
_PORT = '19530'  # default value
# _PORT = '19121'  # default http value

# Vector parameters
_DIM = 1536  # dimension of vector

_INDEX_FILE_SIZE = 32  # max file size of stored index

# 首先，代码连接到 Milvus 服务器，并定义了一些参数，如服务器地址（_HOST）、端口号（_PORT）、向量维度（_DIM）等。

# 然后，代码检查是否已经存在一个名为 example_collection_ 的集合，如果不存在，则创建一个新的集合，其中包括集合的维度、索引文件大小和度量类型。

# 接下来，代码生成了一些随机向量，并将这些向量插入到刚刚创建的集合中。随后，代码进行了一些操作，如刷新数据到磁盘、获取集合的行数和统计信息等。

# 然后，代码获取了插入的向量的原始值，并为这些向量创建了索引，以加速后续的相似性搜索操作。然后，使用一部分插入的向量作为查询向量，执行了相似性搜索，并打印了搜索结果。

# 最后，代码删除了创建的集合。

def build_vd(collection_name, vectors):
    # Specify server addr when create milvus client instance
    # milvus client instance maintain a connection pool, param
    # `pool_size` specify the max connection num.
    milvus = Milvus(_HOST, _PORT)

    status, ok = milvus.has_collection(collection_name)
    if not ok:
        print("重新创建一个喽！")
        param = {
            'collection_name': collection_name,
            'dimension': _DIM,
            'index_file_size': _INDEX_FILE_SIZE,  # optional
            'metric_type': MetricType.L2  # optional
        }

        milvus.create_collection(param)

    # Show collections in Milvus server
    _, collections = milvus.list_collections()
    # Describe demo_collection
    _, collection = milvus.get_collection_info(collection_name)
    
    # 100 vectors with 1536 dimension
    # element per dimension is float32 type
    # vectors should be a 2-D array
    # vectors = [[random.random() for _ in range(_DIM)] for _ in range(10)]


def main():
    # Insert vectors into demo_collection, return status and vectors id list
    status, ids = milvus.insert(collection_name=collection_name, records=vectors)
    if not status.OK():
        print("Insert failed: {}".format(status))

    # Flush collection  inserted data to disk.
    milvus.flush([collection_name])
    # Get demo_collection row count
    status, result = milvus.count_entities(collection_name)

    # present collection statistics info
    _, info = milvus.get_collection_stats(collection_name)
    print(info)

    # Obtain raw vectors by providing vector ids
    status, result_vectors = milvus.get_entity_by_id(collection_name, ids[:10])

    # create index of vectors, search more rapidly
    index_param = {
        'nlist': 2048
    }

    # Create ivflat index in demo_collection
    # You can search vectors without creating index. however, Creating index help to
    # search faster
    print("Creating index: {}".format(index_param))
    status = milvus.create_index(collection_name, IndexType.IVF_FLAT, index_param)

    # describe index, get information of index
    status, index = milvus.get_index_info(collection_name)
    print(index)

    # Use the top 10 vectors for similarity search
    query_vectors = vectors[0:10]

    # execute vector similarity search
    search_param = {
        "nprobe": 16
    }

    print("Searching ... ")

    param = {
        'collection_name': collection_name,
        'query_records': query_vectors,
        'top_k': 1,
        'params': search_param,
    }

    status, results = milvus.search(**param)
    if status.OK():
        # indicate search result
        # also use by:
        #   `results.distance_array[0][0] == 0.0 or results.id_array[0][0] == ids[0]`
        if results[0][0].distance == 0.0 or results[0][0].id == ids[0]:
            print('Query result is correct')
        else:
            print('Query result isn\'t correct')

        # print results
        print(results)
    else:
        print("Search failed. ", status)

    # Delete demo_collection
    # status = milvus.drop_collection(collection_name)


if __name__ == '__main__':
    main()