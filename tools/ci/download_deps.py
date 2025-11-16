import os
import sys
import argparse
import subprocess

# Set encoding to utf-8
sys.stdout.reconfigure(encoding='utf-8')

def main():
    parser = argparse.ArgumentParser(description='下载Python依赖')
    parser.add_argument('--deps-dir', required=True, help='依赖安装目录')
    args = parser.parse_args()
    
    deps_dir = args.deps_dir
    requirements_file = "requirements.txt"
    
    print(f"依赖安装目录: {deps_dir}")
    print(f"使用Python: {sys.executable}")
    
    # 确保依赖目录存在
    os.makedirs(deps_dir, exist_ok=True)
    
    # 检查requirements.txt是否存在
    if not os.path.exists(requirements_file):
        print(f"错误: 未找到 {requirements_file}")
        sys.exit(1)
    
    # 安装依赖到指定目录
    print("正在安装Python依赖...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install",
            "-r", requirements_file,
            "--target", deps_dir,
            "--no-deps"  # 不安装依赖的依赖，避免冲突
        ], check=True)
        print("Python依赖安装完成。")
    except subprocess.CalledProcessError as e:
        print(f"依赖安装失败: {e}")
        sys.exit(1)
    
    # 创建__init__.py文件，使目录成为Python包
    init_file = os.path.join(deps_dir, "__init__.py")
    if not os.path.exists(init_file):
        with open(init_file, "w") as f:
            f.write("# Python dependencies package\n")
        print(f"已创建 {init_file}")

if __name__ == "__main__":
    main()