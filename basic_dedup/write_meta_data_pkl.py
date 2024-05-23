import os
import hashlib
import pandas as pd
import argparse
import time

# 计算文件的 SHA256 哈希值
def sha256(filename):
    hash_sha256 = hashlib.sha256()
    with open(filename, 'rb') as f:
        for chunk in iter(lambda: f.read(1024*1024*256), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

# 递归遍历目录并输出文件路径、文件大小和 SHA256 哈希值
def get_all_files_list(dir_path):
    file_path_list = []
    for root, _, files in os.walk(dir_path):
        #print(files)
        for file in files:
            file_path = os.path.join(root, file)
            file_path_list.append(file_path)
    file_path_list = sorted(file_path_list)
    return file_path_list


# 将文件路径、大小和哈希值写入 PKL 文件
def write_to_csv(dir_path, pkl_file='files.pkl'):
    try:
        existing_df = pd.read_pickle(pkl_file)
    except FileNotFoundError:
        existing_df = pd.DataFrame({'File': [], 'Size': [], 'SHA256': []})
    
    data = {'File': [], 'Size': [], 'SHA256': []}
    file_path_set = set(get_all_files_list(dir_path))
    #print(file_path_set)

    file_path_set -= set(existing_df['File'])

    for filepath in file_path_set:
        try:
            file_size = os.path.getsize(filepath)
            file_sha256 = sha256(filepath)
            data['File'].append(filepath)
            data['Size'].append(file_size)
            data['SHA256'].append(file_sha256)
        except:
            print("file not exist:" + filepath)
            
    df = pd.concat([existing_df, pd.DataFrame(data)], ignore_index=True)

    # 将 DataFrame 写入 pickle 文件
    df.to_pickle(pkl_file)

# 示例用法
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dir_path', required=True, help='The directory to traverse')
    parser.add_argument('--pkl_file', required=True, help='The pickle file to write to')

    args = parser.parse_args()
    write_to_csv(args.dir_path, args.pkl_file)