# This program demos how to connect to Milvus vector database, 
# create a vector collection,
# insert 10 vectors, 
# and execute a vector similarity search.

import random
import csv

from milvus import Milvus, IndexType, MetricType, Status

# Milvus server IP address and port.
# You may need to change _HOST and _PORT accordingly.
_HOST = '127.0.0.1'
_PORT = '19530'  # default value
# _PORT = '19121'  # default http value

# Vector parameters
_DIM = 1536  # dimension of vector

_INDEX_FILE_SIZE = 32  # max file size of stored index

ICLSET_VEC_FILEPATH = 'data/vector/iclset_vec.csv'
VALSET_VEC_FILEPATH = 'data/vector/valset_vec.csv'
SIMILARITY_DIR = 'data/similarity/'

def get_vectors(dataset_vec_filepath):
    vectors = []
    with open(dataset_vec_filepath, 'r') as dataset_file:
        # 逐行读取CSV数据
        reader = csv.DictReader(dataset_file)
        for row in reader:
            # if dataset_vec_filepath == ICLSET_VEC_FILEPATH:
            #     print(row['id'])
            vec = row['input_vec']
            vector = eval(vec)
            vectors.append(vector)
        print(len(vectors))
    return vectors

def main():
    # Specify server addr when create milvus client instance
    # milvus client instance maintain a connection pool, param
    # `pool_size` specify the max connection num.
    milvus = Milvus(_HOST, _PORT)

    collection_name = 'luorong_test_collection'
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
    print(collection)
    
    # 100 vectors with 1536 dimension
    # element per dimension is float32 type
    # vectors should be a 2-D array
    # vectors = [[random.random() for _ in range(_DIM)] for _ in range(61)]
    iclset_vectors = get_vectors(ICLSET_VEC_FILEPATH)
    valset_vectors = get_vectors(VALSET_VEC_FILEPATH)

    # Insert vectors into demo_collection, return status and vectors id list
    status, milvus_ids = milvus.insert(collection_name=collection_name, records=iclset_vectors)
    if not status.OK():
        print("Insert failed: {}".format(status))
    milvus_id2id = {}
    for i in range(len(milvus_ids)):
        id = i if i < 27 else i + 1
        milvus_id2id[milvus_ids[i]] = id
    print(milvus_id2id)

    # Flush collection inserted data to disk.
    milvus.flush([collection_name])
    # Get demo_collection row count 数据库中的数目
    status, result = milvus.count_entities(collection_name) 

    # present collection statistics info
    _, info = milvus.get_collection_stats(collection_name)
    # info = {'partitions': [{'row_count': 61, 'segments': [{'data_size': 375272, 'index_name': 'IDMAP', 'name': '1709234662417072000', 'row_count': 61}], 'tag': '_default'}], 'row_count': 61}

    # # Obtain raw vectors by providing vector ids
    # status, result_vectors = milvus.get_entity_by_id(collection_name, ids[:10])

    # describe index, get information of index
    status, index = milvus.get_index_info(collection_name)
    print(index)

    # Use the all vectors for similarity search
    query_vectors = valset_vectors

    # execute vector similarity search
    NPROBE = 100
    search_param = { "nprobe": NPROBE }

    print("Searching ... ")

    param = {
        'collection_name': collection_name,
        'query_records': query_vectors,
        'top_k': 20,  # 最相似的代码
        'params': search_param,
    }

    status, results = milvus.search(**param)
    if status.OK():
        # indicate search result
        # also use by:
        #   `results.distance_array[0][0] == 0.0 or results.id_array[0][0] == ids[0]`
        # if results[0][0].distance == 0.0 or results[0][0].id == ids[0]:
        #     print('Query result is correct')
        # else:
        #     print('Query result isn\'t correct')

        # print results
        valset_ids = []
        for i in range(len(query_vectors)):
            m_ids = results.id_array[i] 
            print(m_ids)
            ids = []
            for m_id in m_ids:
                print(m_id)
                id = milvus_id2id[m_id]
                print(id)
                ids.append(id)
            print(ids)
            valset_ids.append(ids)
        
        with open(SIMILARITY_DIR + 'text-embedding-3-small-' + str(NPROBE) + '.csv', 'w') as written_file:
            written_csv_writer = csv.writer(written_file)
            written_csv_writer.writerow(['program_idx','idx','ids'])
            with open(VALSET_VEC_FILEPATH, 'r') as dataset_file:
                # 逐行读取CSV数据
                dataset_csv_reader = csv.reader(dataset_file)
                # 跳过 header
                next(dataset_csv_reader)
                # 逐行读取CSV数据
                for i, row in enumerate(dataset_csv_reader):
                    print(i)
                    program_idx,file_path,idx,src,dst,src_code,dst_code,reason,offset,sa_lb_direct,sa_lb,da_lb,dst_name_match,dst_funcname,actual_lb,actual_lb_trans,is_static,src_class,mvs,src_ancestors,src_descendants,dst_class,dst_ancestors,dst_descendants,input_vec = row
                    written_csv_writer.writerow([program_idx, idx, valset_ids[i]])
            
    else:
        print("Search failed. ", status)

    # Delete demo_collection
    status = milvus.drop_collection(collection_name)


if __name__ == '__main__':
    main()
    # valset_strs = []
    # with open('data/valset.csv', 'r') as dataset_file:
    #     # 逐行读取CSV数据
    #     reader = csv.DictReader(dataset_file)
    #     for row in reader:
    #         # if dataset_vec_filepath == ICLSET_VEC_FILEPATH:
    #         #     print(row['id'])
    #         valset_strs.append(row['program_idx'] + ',' + row['idx'])
            
    # vec_strs = []
    # with open('data/similarity/text-embedding-3-small.csv', 'r') as dataset_file:
    #     # 逐行读取CSV数据
    #     reader = csv.DictReader(dataset_file)
    #     for row in reader:
    #         # if dataset_vec_filepath == ICLSET_VEC_FILEPATH:
    #         #     print(row['id'])
    #         vec_strs.append(row['program_idx'] + ',' + row['idx'])
    
    # print(len(valset_strs))
    # print(len(vec_strs))

