import os, hashlib
import argparse
import shutil, io
import tarfile
import zipfile
import bz2
import gzip
import rarfile
import py7zr
import os, sys
from charset_mnbvc import api
from better_zipfile import fixcharset_zipfile
import shutil

def get_directory_size(directory):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if not os.path.islink(filepath):
                total_size += os.path.getsize(filepath)
    return total_size


def get_extension(file_path):
    filename, extension = os.path.splitext(file_path)

    extensions = []
    if extension:
        extensions.insert(0, extension)
        filename_1, extension = os.path.splitext(filename)
        if extension == '.tar':
            extensions.insert(0, extension)
            filename = filename_1
    return filename, ''.join(extensions)


def check_long_name(extract_full_path, zip_file_name):# longname返回true
    paths = zip_file_name.split('/')
    file_name = paths[-1]
    if len(file_name.encode()) > 255 and len(os.path.join(extract_full_path, zip_file_name).encode()) < 4095:
        print(f"File name too long: \n{os.path.join(extract_full_path, zip_file_name)} \n")
        basename, extensions =  get_extension(file_name)
        length = (255-len(extensions.encode())-8)//2
        basename = basename.encode()[:length].decode('utf-8', errors='ignore')+hashlib.md5(file_name.encode()).hexdigest()[:8]+basename.encode()[-length:].decode('utf-8', errors='ignore')
        new_name = basename + extensions
        return os.path.join(extract_full_path, '/'.join(paths[:-1]), new_name), True
    elif any(len(path.encode()) > 255 for path in paths) or len(os.path.join(extract_full_path, zip_file_name).encode()) > 4095:
        print(f"File name too long: \n {os.path.join(extract_full_path, zip_file_name)} \n")

        length = min(255, 4096-len(os.path.join(extract_full_path, 'long_name').encode()))-8

        new_name = zip_file_name.encode()[:length//2-1].decode('utf-8', errors='ignore') +hashlib.md5(zip_file_name.encode()).hexdigest()[:8]+ zip_file_name.encode()[1-length//2:].decode('utf-8', errors='ignore')
        new_name = '_'.join(new_name.split('/'))
        return os.path.join(extract_full_path, 'long_name', new_name), True

    return os.path.join(extract_full_path, zip_file_name), False


def extract_zip(file, password, extract_full_path):

    with fixcharset_zipfile.ZipFile(file, 'r') as zip:
        zip.setpassword(password)

        auto_filelists = []

        for file in zip.namelist():
            problem = False
            if file.endswith('/'):
                continue

            new_file_path, if_long_name = check_long_name(extract_full_path, file)
            if if_long_name:
                problem = True
            
            if problem:
                basename = os.path.dirname(new_file_path)
                os.makedirs(basename, exist_ok=True)
                with zip.open(file, 'r') as f_in:
                    data = f_in.read()
                    with open(new_file_path, 'wb') as f_out:
                        f_out.write(data)
            else:
                auto_filelists.append(file)
        
        zip.extractall(extract_full_path, auto_filelists)





def extract_archive(file_path, extract_full_path, file, password=None):

    filename, extension = get_extension(file)
    extract_succcessful = True
    try:
        if extension == '.tar':
            with tarfile.open(file_path, 'r') as tar:
                tar.extractall(extract_full_path)
        elif extension == '.tbz2' or extension == '.tar.bz2':
            with tarfile.open(file_path, 'r:bz2') as tar:
                tar.extractall(extract_full_path)
        elif extension == '.tgz' or extension == '.tar.gz' or extension == '.tar.Z':
            with tarfile.open(file_path, 'r:gz') as tar:
                tar.extractall(extract_full_path)
        elif extension == '.tar.xz':
            with tarfile.open(file_path, 'r:xz') as tar:  
                tar.extractall(extract_full_path)
        elif extension == '.bz2':
            if not os.path.exists(extract_full_path):
                os.mkdir(extract_full_path)
            with bz2.open(file_path, 'rb') as f_in:
                with open(os.path.join(extract_full_path, filename), 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        elif extension == '.rar':
            with rarfile.RarFile(file_path, 'r') as rar:
                rar.setpassword(password)

                problem = False

                for file in rar.namelist():
                    if file.endswith('/'):
                        continue
                    new_file_path, if_long_name = check_long_name(extract_full_path, file)
                    if if_long_name:
                        problem = True
                        break

                if problem:
                    for file in rar.namelist():
                        if file.endswith('/'):
                            continue
                        new_file_path, _ = check_long_name(extract_full_path, file)
                        basename = os.path.dirname(new_file_path)

                        os.makedirs(basename, exist_ok=True)
                        with rar.open(file, 'r') as f_in:
                            data = f_in.read()
                            with open(new_file_path, 'wb') as f_out:
                                f_out.write(data)
                        # print(f"File extract to: {new_file_path}")
                else:
                    rar.extractall(extract_full_path)

        elif extension == '.gz':
            if not os.path.exists(extract_full_path):
                os.mkdir(extract_full_path)

            with gzip.open(file_path, 'rb') as f_in:
                with open(os.path.join(extract_full_path, filename), 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        elif extension in ('.zip', '.exe'):
            extract_zip(file_path, password, extract_full_path)

        elif extension == '.7z':
            with py7zr.SevenZipFile(file_path, mode='r', password=password) as seven_zip:
                seven_zip.extractall(extract_full_path)
        else:
            print(f"Unsupported file format: {extension}")
            extract_succcessful = False
    
    except Exception as e:
        print(f"Extracting {file_path} failed: {e}")
        extract_succcessful = False
    
    if extract_succcessful and os.path.getsize(file_path) <= get_directory_size(extract_full_path):
        os.remove(file_path)
        print(f"文件 '{file_path}' 已成功删除。")
    else:
    	#检查路径长度，避免删除风险
        if len(extract_full_path) >= 20:
            # 确保路径存在，并且实际上是一个目录
            if os.path.isdir(extract_full_path):
                shutil.rmtree(extract_full_path)
                print(f"目录 '{extract_full_path}' 已成功删除。")
            else:
                print("提供的路径不是有效的目录。")
        else:
            print(f"路径 '{extract_full_path}' 长度不足，为了安全起见，路径长度至少需要20个字符。")
    
    return extract_succcessful


def traverse_directory(folder_path, passwords=None):
    if not os.path.exists(folder_path):
        print(f"{folder_path} does not exist!")
        return
    if not passwords is None:
        with open(passwords, 'r') as f:
            balsklist = f.readlines()
        passwords = [x.strip() for x in balsklist]
    else :
        passwords = []


    for root, dirs, files in os.walk(folder_path):
        extract_path_set = set(dirs)

        for file in files:
            # 判断文件是否为压缩包类型
            if file.endswith(('.tar', '.tbz2', '.tgz', '.tar.bz2', '.tar.gz', '.tar.xz', '.tar.Z', '.bz2', '.rar', '.gz', '.zip', '.xz', '.7z', '.exe')):

                file_path = os.path.join(root, file)
                # 把压缩包解压到的文件夹名
                extract_path, _ = get_extension(file)

                if extract_path in extract_path_set:
                    for i in range(1, 10000):
                        if f"{extract_path}_{i}" not in extract_path_set:
                            extract_path = f"{extract_path}_{i}"
                            break
                        if i == 9999:
                            print(f"Too many files in {root}")
                            raise Exception(f"Too many files in {root}")

                extract_full_path = os.path.join(root, extract_path)
                
                extract_succcessful = extract_archive(file_path, extract_full_path, file)
                
                if not extract_succcessful:
                    for password in passwords:
                        print(f"Try password: {password}")
                        extract_succcessful = extract_archive(file_path, extract_full_path, file, password=password.encode())
                        if extract_succcessful:
                            break
                
                # if extract_succcessful:
                #     traverse_directory(extract_full_path)
                
                extract_path_set.add(extract_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--folder_path', type=str, required=True, help="压缩包路径")
    parser.add_argument('--passwords_files', type=str, default=None, help="压缩包密码文件路径")
    args = parser.parse_args()

    traverse_directory(args.folder_path, args.passwords_files)