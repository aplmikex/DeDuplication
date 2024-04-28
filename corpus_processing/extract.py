import os, hashlib
import argparse
import shutil
import tarfile
import zipfile
import bz2
import gzip
import rarfile
import py7zr
import os, sys
from charset_mnbvc import api

def get_directory_size(directory):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
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

def test_encode(file_path : bytes):
    try:
        bytes.decode(file_path, encoding='utf-8')
        return 'utf-8'
    except:
        pass
    try:
        bytes.decode(file_path, encoding='gb18030')
        return 'gb18030'
    except:
        pass
    return None

def check_long_name(extract_full_path, zip_file_name):
    paths = zip_file_name.split('/')
    file_name = paths[-1]
    if len(file_name.encode()) > 255 and len(os.path.join(extract_full_path, zip_file_name).encode()) < 4095:
        print(f"File name too long: \n{os.path.join(extract_full_path, zip_file_name)} \n")
        basename, extensions =  get_extension(file_name)
        length = (255-len(extensions.encode())-8)//2
        basename = basename.encode()[:length].decode('utf-8', errors='ignore')+hashlib.md5(file_name.encode()).hexdigest()[:8]+basename.encode()[-length:].decode('utf-8', errors='ignore')
        new_name = basename + extensions
        return os.path.join(extract_full_path, '/'.join(paths[:-1]), new_name)
    elif any(len(path.encode()) > 255 for path in paths) or len(os.path.join(extract_full_path, zip_file_name).encode()) > 4095:
        print(f"File name too long: \n {os.path.join(extract_full_path, zip_file_name)} \n")

        length = min(255, 4096-len(os.path.join(extract_full_path, 'long_name').encode()))-8

        new_name = zip_file_name.encode()[:length//2-1].decode('utf-8', errors='ignore') +hashlib.md5(zip_file_name.encode()).hexdigest()[:8]+ zip_file_name.encode()[1-length//2:].decode('utf-8', errors='ignore')
        new_name = '_'.join(new_name.split('/'))
        return os.path.join(extract_full_path, 'long_name', new_name)
    
    zipfileName = remove_between_first_second_slash( zip_file_name)
    fullPath = os.path.join(extract_full_path, zipfileName)
    return fullPath


def extract_archive(file_path, extract_full_path, file, password=None):

    filename, extension = get_extension(file)
    extract_succcessful = True
    try:
        if extension == '.tar':
            with tarfile.open(file_path, 'r') as tar:
                extract_and_convert_zip(tar,extract_full_path)
            os.remove(file_path)
        elif extension == '.tbz2' or extension == '.tar.bz2':
            with tarfile.open(file_path, 'r:bz2') as tar:
                tar.extractall(extract_full_path)
            os.remove(file_path)
        elif extension == '.tgz' or extension == '.tar.gz' or extension == '.tar.Z':
            with tarfile.open(file_path, 'r:gz') as tar:
                tar.extractall(extract_full_path)
            os.remove(file_path)
        elif extension == '.tar.xz':
            with tarfile.open(file_path, 'r:xz') as tar:  
                tar.extractall(extract_full_path)
            os.remove(file_path)
        elif extension == '.bz2':
            if not os.path.exists(extract_full_path):
                os.mkdir(extract_full_path)
            with bz2.open(file_path, 'rb') as f_in:
                with open(os.path.join(extract_full_path, filename), 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            os.remove(file_path)
        elif extension == '.rar':
            with rarfile.RarFile(file_path, 'r') as rar:
                rar.setpassword(password)
                extract_and_convert_zip(rar,extract_full_path)
            os.remove(file_path)
                    

        elif extension == '.gz':
            if not os.path.exists(extract_full_path):
                os.mkdir(extract_full_path)

            with gzip.open(file_path, 'rb') as f_in:
                with open(os.path.join(extract_full_path, filename), 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            os.remove(file_path)
        elif extension in ('.zip', '.exe'):
            try:
                with zipfile.ZipFile(file_path, 'r') as zip:
                    zip.setpassword(password)
                    extract_and_convert_zip(zip,extract_full_path)
                    # for file_info in zip.infolist():
                    #     file =  file_info.filename
                    #     if file.endswith('/') or file.startswith('__MACOSX/') or is_macos_metadata(file):
                    #         continue
                        
                    #     try:
                    #         file_bytes = file.encode('cp437')
                    #     except:
                    #         file_bytes = file.encode('utf-8')

                    #     coding_name = test_encode(file_bytes)

                    #     if coding_name is None:
                    #         coding_name = api.from_data(file_bytes, mode=2)

                    #     utf8_name = api.convert_encoding(
                    #         source_data=file_bytes,
                    #         source_encoding=coding_name,
                    #         target_encoding="utf-8",
                    #     )

                    #     new_file_path = check_long_name(extract_full_path, utf8_name)
                    #     basename = os.path.dirname(new_file_path)
                    #     os.makedirs(basename, exist_ok=True)
                    #     # 复制文件
                    #     source = zip.open(file_info)
                    #     with open(new_file_path, "wb") as target:
                    #         shutil.copyfileobj(source, target)
                
                os.remove(file_path)
                print("解压缩完成")
            except zipfile.BadZipFile:
                print("错误：无效的ZIP文件。")
                extract_succcessful = False
            except FileNotFoundError:
                print("错误：文件未找到。")
                extract_succcessful = False
            except IOError as e:
                print(f"输入/输出错误：{e}")
                extract_succcessful = False
            except Exception as e:
                print(f"发生了一个未知错误：{e}")
                extract_succcessful = False
        elif extension == '.7z':
            with py7zr.SevenZipFile(file_path, mode='r', password=password) as seven_zip:
                seven_zip.extractall(extract_full_path)
        else:
            print(f"Unsupported file format: {extension}")
            extract_succcessful = False
    
    except Exception as e:
        print(f"Extracting {file_path} failed: {e}")
        extract_succcessful = False
    
    if extract_succcessful:
        if os.path.getsize(file_path) <= get_directory_size(extract_full_path):
            os.remove(file_path)
    
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
        if root != folder_path:
            continue
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


def remove_between_first_second_slash(path):
    """
    Remove the substring from the first '/' to the second '/' in the path, inclusive.

    :param path: The original path as a string.
    :return: The path after removing the substring between the first and second '/'.
    """
    first_slash_index = path.find('/')
    if first_slash_index == -1:
        return path  # No '/' found
    

    return path[first_slash_index + 1:]

def is_macos_metadata(path):
    """
    Check if the given path is a macOS metadata file.

    :param path: The path to be checked.
    :return: True if the path is a macOS metadata file, False otherwise.
    """
    return path.split('/')[-1].startswith('._')


def extract_and_convert_zip(zip_file, extract_full_path):
    """
    Extract files from the zip file, convert filenames to UTF-8, and save them to a target directory.

    :param zip_file: ZipFile object to be extracted.
    """
    for file_info in zip_file.infolist():
        file = file_info.filename
       
        if file.endswith('/') or file.startswith('__MACOSX/') or is_macos_metadata(file):
            continue

        try:
            file_bytes = file.encode('cp437')
        except:
            file_bytes = file.encode('utf-8')

        coding_name = test_encode(file_bytes)

        if coding_name is None:
            coding_name = api.from_data(file_bytes, mode=2)

        utf8_name = api.convert_encoding(
            source_data=file_bytes,
            source_encoding=coding_name,
            target_encoding="utf-8",
        )

        new_file_path = check_long_name(extract_full_path, utf8_name)
        basename = os.path.dirname(new_file_path)
        os.makedirs(basename, exist_ok=True)

        # 复制文件
        with zip_file.open(file_info) as source:
            with open(new_file_path, "wb") as target:
                shutil.copyfileobj(source, target)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--folder_path', type=str, required=True, help="压缩包路径")
    parser.add_argument('--passwords_files', type=str, default=None, help="压缩包密码文件路径")
    args = parser.parse_args()

    traverse_directory(args.folder_path, args.passwords_files)