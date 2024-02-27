import json


# 从指定路径读取配置文件，并将配置参数存储在 config 变量中
def read_config_file(config_file):
    configs = {}
    with open(config_file) as f:
        for line in f.readlines():
            line = line.strip()
            split_line = line.split("=")
            configs[split_line[0]] = split_line[1]
    return configs


def json_to_csv(path, content):
    with open(path, "w") as file:
        json.dump(content, file)

def csv_to_json(path):
    with open(path, "r") as file:
        content = json.load(file)
        return content
