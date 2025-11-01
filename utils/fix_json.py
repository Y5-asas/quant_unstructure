import json
import re
from typing import Any, Optional


def fix_basic_json(json_str: str) -> Optional[Any]:
    """
    修复基本的 JSON 格式错误
    """
    try:
        # 尝试直接解析
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        try:
            # 常见修复：处理多余的逗号、引号问题等
            json_str = re.sub(r",\s*}", "}", json_str)  # 尾部多余逗号
            json_str = re.sub(r",\s*]", "]", json_str)  # 数组尾部多余逗号
            json_str = re.sub(r"'", '"', json_str)  # 单引号转双引号

            return json.loads(json_str)
        except json.JSONDecodeError:
            return None


def fix_advanced_json(json_str: str) -> Optional[Any]:
    """
    高级 JSON 修复，处理更多边界情况
    """
    if not json_str.strip():
        return None

    json_str = json_str.strip()

    # 移除可能的代码块标记
    if json_str.startswith("```json"):
        json_str = json_str[7:]
    if json_str.startswith("```"):
        json_str = json_str[3:]
    if json_str.endswith("```"):
        json_str = json_str[:-3]
    json_str = json_str.strip()

    # 常见大模型输出问题修复
    fixes = [
        # 修复未转义的特殊字符
        (r'\\"', '"'),  # 过度转义
        (r"\\n", "\\\\n"),  # 换行符转义
        (r"\\t", "\\\\t"),  # 制表符转义
        # 修复键名引号问题
        (r"(\w+)\s*:", r'"\1":'),  # 无引号键名
        # 修复布尔值
        (r":\s*True\b", ":true"),
        (r":\s*False\b", ":false"),
        (r":\s*None\b", ":null"),
    ]

    for pattern, replacement in fixes:
        json_str = re.sub(pattern, replacement, json_str)

    # 处理尾部逗号
    json_str = re.sub(r",\s*([}\]])", r"\1", json_str)

    # 尝试解析
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        # 如果还是失败，尝试提取第一个完整的 JSON 对象
        return extract_json_object(json_str)


def extract_json_object(text: str) -> Optional[Any]:
    """
    从文本中提取第一个完整的 JSON 对象
    """
    stack = []
    start_index = -1

    for i, char in enumerate(text):
        if char in "{[":
            if not stack:  # 找到开始位置
                start_index = i
            stack.append(char)
        elif char in "}]":
            if not stack:
                continue

            if (char == "}" and stack[-1] == "{") or (char == "]" and stack[-1] == "["):
                stack.pop()

                if not stack and start_index != -1:  # 找到完整对象
                    json_str = text[start_index : i + 1]
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        # 继续寻找下一个
                        stack = []
                        start_index = -1
            else:
                # 括号不匹配，重置
                stack = []
                start_index = -1

    return None


def safe_eval_json(json_str: str) -> Optional[Any]:
    """
    安全地将类似 Python 字典的字符串转换为 JSON
    """
    try:
        # 将 Python 的 None, True, False 转换为 JSON 格式
        json_str = re.sub(r":\s*True\b", ":true", json_str)
        json_str = re.sub(r":\s*False\b", ":false", json_str)
        json_str = re.sub(r":\s*None\b", ":null", json_str)

        # 使用 ast.literal_eval 安全评估
        import ast

        python_obj = ast.literal_eval(json_str)

        # 转换为 JSON 兼容格式
        return json.loads(json.dumps(python_obj))
    except:
        return None


def smart_fix_json(json_str: str, max_attempts: int = 5) -> dict:
    """
    智能修复 JSON，包含多种策略
    """
    attempts = [
        # 策略1: 直接解析
        lambda s: json.loads(s),
        # 策略2: 基础修复
        lambda s: fix_basic_json(s),
        # 策略3: 提取 JSON 对象
        lambda s: extract_json_object(s),
        # 策略4: 尝试作为 Python 字典解析（安全方式）
        lambda s: safe_eval_json(s),
        # 策略5: 最后尝试，移除所有空白后解析
        lambda s: json.loads(re.sub(r"\s+", "", s)),
    ]

    for i, attempt in enumerate(attempts[:max_attempts]):
        try:
            result = attempt(json_str)
            if result is not None:
                # print(f"JSON 修复成功 (策略 {i+1})")
                return result
        except:
            continue

    raise ValueError("无法修复 JSON 格式")
