import os
import sys
import json
import tempfile
import shutil
from datetime import datetime


def main():
    """
    Gating 主函数
    """
    if len(sys.argv) < 2:
        print("用法: Gating.exe <文件夹路径>")
        sys.exit(1)
    
    folder_path = sys.argv[1]
    
    if not os.path.exists(folder_path):
        print(f"错误：文件夹不存在: {folder_path}")
        sys.exit(1)
    
    if not os.path.isdir(folder_path):
        print(f"错误：路径不是文件夹: {folder_path}")
        sys.exit(1)
    
    print(f"开始处理文件夹: {folder_path}")
    
    try:
        result = process_folder(folder_path)
        save_result(folder_path, result)
        print(f"处理完成: {result}")
    except Exception as e:
        print(f"处理失败: {e}")
        result = {
            "status": "error",
            "error": str(e)
        }
        save_result(folder_path, result)
        sys.exit(1)


def process_folder(folder_path: str) -> dict:
    """
    处理文件夹
    
    Args:
        folder_path: 文件夹路径
    
    Returns:
        处理结果
    """
    parent_dir = os.path.dirname(folder_path)
    folder_name = os.path.basename(folder_path)
    
    print(f"文件夹名称: {folder_name}")
    print(f"父目录: {parent_dir}")
    
    # 生成结果路径列表
    result_paths = []
    
    # 生成图片路径
    image_path = os.path.join(parent_dir, f"{folder_name}_output.png")
    
    # 创建一个简单的图片（这里用文本文件代替，实际应该用 PIL 等库生成真实图片）
    try:
        with open(image_path, 'w') as f:
            f.write(f"这是 {folder_name} 的门控输出图片\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"源文件夹: {folder_path}\n")
        
        print(f"图片生成成功: {image_path}")
        result_paths.append(image_path)
        
        return {
            "status": "success",
            "result_paths": result_paths
        }
    except Exception as e:
        print(f"图片生成失败: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }


def save_result(folder_path: str, result: dict):
    """
    保存结果到记录文件（使用文件锁避免并发冲突）
    
    Args:
        folder_path: 文件夹路径
        result: 处理结果
    """
    # 记录文件路径（与 Service 在同一目录）
    # 开发环境：src/workspace_env/data/gating_records.json
    # 部署环境：dist/data/gating_records.json
    
    # 判断运行环境
    if getattr(sys, 'frozen', False):
        # 部署环境
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        project_root = os.path.dirname(exe_dir)
    else:
        # 开发环境
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.join(os.path.dirname(current_dir), 'workspace_env')
    
    record_file = os.path.join(project_root, 'data', 'gating_records.json')
    os.makedirs(os.path.dirname(record_file), exist_ok=True)
    
    # 使用文件锁避免并发冲突
    lock_file = record_file + '.lock'
    max_retries = 5
    retry_delay = 0.5
    
    for attempt in range(max_retries):
        try:
            # 尝试创建锁文件（独占模式）
            with open(lock_file, 'x') as f:
                pass
            
            # 成功获取锁，读取现有记录
            records = {}
            if os.path.exists(record_file):
                try:
                    with open(record_file, 'r', encoding='utf-8') as f:
                        records = json.load(f)
                except Exception as e:
                    print(f"加载记录文件失败: {e}")
                    records = {}
            
            # 更新记录（不操作 call_time）
            if folder_path in records:
                records[folder_path].update(result)
            else:
                records[folder_path] = result
            
            # 写入临时文件
            temp_file = record_file + '.tmp'
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(records, f, indent=4, ensure_ascii=False)
            
            # 原子操作：重命名临时文件到目标文件
            shutil.move(temp_file, record_file)
            
            # 释放锁
            os.remove(lock_file)
            
            print(f"记录保存成功: {record_file}")
            return
            
        except FileExistsError:
            # 锁文件已存在，等待后重试
            if attempt < max_retries - 1:
                import time
                time.sleep(retry_delay)
            else:
                print(f"警告：无法获取文件锁，放弃保存记录")
                return
        except Exception as e:
            # 发生其他错误，释放锁
            if os.path.exists(lock_file):
                try:
                    os.remove(lock_file)
                except:
                    pass
            print(f"保存记录文件失败: {e}")
            return


if __name__ == '__main__':
    main()