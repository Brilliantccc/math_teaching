"""工具定义 - 供Agent使用"""

import os
import ast
import subprocess
from typing import Optional, List, Dict, Any
from langchain_core.tools import tool


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@tool
def read_file(file_path: str) -> str:
    """读取指定文件的内容

    Args:
        file_path: 文件路径（相对于项目根目录）
    """
    full_path = os.path.join(BASE_DIR, file_path)
    if not os.path.exists(full_path):
        return f"错误: 文件不存在 - {file_path}"

    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        return f"错误: 读取文件失败 - {str(e)}"


@tool
def write_file(file_path: str, content: str) -> str:
    """写入内容到指定文件

    Args:
        file_path: 文件路径（相对于项目根目录）
        content: 文件内容
    """
    full_path = os.path.join(BASE_DIR, file_path)

    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return f"成功: 文件已写入 - {file_path}"
    except Exception as e:
        return f"错误: 写入文件失败 - {str(e)}"


@tool
def edit_file(file_path: str, old_text: str, new_text: str) -> str:
    """编辑文件，替换指定内容

    Args:
        file_path: 文件路径（相对于项目根目录）
        old_text: 要替换的旧文本
        new_text: 替换后的新文本
    """
    full_path = os.path.join(BASE_DIR, file_path)

    if not os.path.exists(full_path):
        return f"错误: 文件不存在 - {file_path}"

    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if old_text not in content:
            return f"错误: 未找到要替换的文本"

        new_content = content.replace(old_text, new_text, 1)

        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        return f"成功: 文件已编辑 - {file_path}"
    except Exception as e:
        return f"错误: 编辑文件失败 - {str(e)}"


@tool
def check_python_syntax(file_path: str) -> str:
    """检查Python文件语法

    Args:
        file_path: Python文件路径（相对于项目根目录）
    """
    full_path = os.path.join(BASE_DIR, file_path)

    if not os.path.exists(full_path):
        return f"错误: 文件不存在 - {file_path}"

    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        ast.parse(content)
        return f"成功: 语法检查通过 - {file_path}"
    except SyntaxError as e:
        return f"语法错误: 第{e.lineno}行 - {e.msg}"
    except Exception as e:
        return f"错误: 检查失败 - {str(e)}"


@tool
def list_files(directory: str, pattern: str = "*.py") -> str:
    """列出目录中的文件

    Args:
        directory: 目录路径（相对于项目根目录）
        pattern: 文件匹配模式（如 *.py, *.vue）
    """
    full_path = os.path.join(BASE_DIR, directory)

    if not os.path.exists(full_path):
        return f"错误: 目录不存在 - {directory}"

    try:
        import glob
        search_pattern = os.path.join(full_path, "**", pattern)
        files = glob.glob(search_pattern, recursive=True)

        # 转换为相对路径
        relative_files = [os.path.relpath(f, BASE_DIR) for f in files]

        if not relative_files:
            return f"未找到匹配的文件: {pattern}"

        return "\n".join(relative_files)
    except Exception as e:
        return f"错误: 列出文件失败 - {str(e)}"


@tool
def run_command(command: str) -> str:
    """运行shell命令

    Args:
        command: 要运行的命令
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=BASE_DIR,
            timeout=30
        )

        output = result.stdout
        if result.stderr:
            output += f"\n stderr: {result.stderr}"

        if result.returncode != 0:
            return f"命令执行失败 (exit code {result.returncode}):\n{output}"

        return f"命令执行成功:\n{output}"
    except subprocess.TimeoutExpired:
        return "错误: 命令执行超时"
    except Exception as e:
        return f"错误: 执行命令失败 - {str(e)}"


@tool
def validate_imports(file_path: str) -> str:
    """验证Python文件的导入是否正确

    Args:
        file_path: Python文件路径（相对于项目根目录）
    """
    full_path = os.path.join(BASE_DIR, file_path)

    if not os.path.exists(full_path):
        return f"错误: 文件不存在 - {file_path}"

    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)

        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

        # 检查本地导入
        local_imports = [imp for imp in imports if imp.startswith('backend.')]

        return f"文件: {file_path}\n导入数量: {len(imports)}\n本地导入: {local_imports}"
    except SyntaxError as e:
        return f"语法错误: 第{e.lineno}行 - {e.msg}"
    except Exception as e:
        return f"错误: 验证失败 - {str(e)}"


def get_all_tools() -> List:
    """获取所有可用工具"""
    return [
        read_file,
        write_file,
        edit_file,
        check_python_syntax,
        list_files,
        run_command,
        validate_imports,
    ]
