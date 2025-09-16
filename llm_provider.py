#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM Provider 模块
用于提供简单的GLM模型测试接口
"""

# 首先设置环境变量，确保在导入任何模块之前完成
import os
# 设置默认环境变量
os.environ['HF_HOME'] = "/root/autodl-tmp/huggingface_cache"
os.environ['HF_ENDPOINT'] = "https://hf-mirror.com"
os.environ['HF_HUB_DISABLE_TELEMETRY'] = "1"
os.environ['HF_HUB_DOWNLOAD_TIMEOUT'] = "1000"

# 然后导入其他模块
import torch
import random
from transformers import AutoTokenizer, AutoModel
from typing import Optional, Tuple, List, Any


class LLMProvider:
    """GLM模型提供者类，用于加载和使用GLM模型"""
    
    def __init__(self, model_name="THUDM/chatglm2-6b", cache_dir=None, use_mirror=True):
        """
        初始化LLM提供者
        
        参数:
            model_name: 模型名称，默认为"THUDM/chatglm2-6b"
            cache_dir: 缓存目录，默认为None
            use_mirror: 是否使用镜像，默认为True
        """
        # 更新环境变量（如果需要）
        if cache_dir:
            os.environ['HF_HOME'] = cache_dir
        if not use_mirror:
            os.environ.pop('HF_ENDPOINT', None)
        
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        
        # 打印环境设置
        self._print_environment()
    
    def _print_environment(self):
        """打印环境变量设置"""
        print("🚀 环境变量设置:")
        print(f"📁 缓存目录: {os.environ.get('HF_HOME', '未设置')}")
        print(f"🌐 镜像源: {os.environ.get('HF_ENDPOINT', '未设置')}")
        print("✅ 环境变量设置完成")
    
    def load_model(self) -> bool:
        """
        加载模型和tokenizer
        
        返回:
            bool: 是否成功加载模型
        """
        print(f"🔍 正在加载模型: {self.model_name}")
        
        try:
            # 加载tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name, 
                trust_remote_code=True
            )
            print("✅ Tokenizer加载成功")
            
            # 加载模型
            self.model = AutoModel.from_pretrained(
                self.model_name, 
                trust_remote_code=True, 
                device_map='auto',
                torch_dtype=torch.float16
            )
            print("✅ 模型加载成功")
            
            # 打印模型信息
            self.print_model_info()
            
            return True
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")
            return False
    
    def print_model_info(self) -> None:
        """打印模型信息"""
        if self.model is None:
            print("❌ 模型未加载")
            return
        
        print("\n📊 模型信息:")
        print(f"模型类型: {type(self.model)}")
        print(f"设备: {next(self.model.parameters()).device}")
        print(f"数据类型: {next(self.model.parameters()).dtype}")
        
        # 计算参数数量
        total_params = sum(p.numel() for p in self.model.parameters())
        trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        print(f"总参数数量: {total_params:,}")
        print(f"可训练参数数量: {trainable_params:,}")
    
    def generate_text(self, text: str, max_new_tokens: int = 50, 
                     temperature: float = 0.7, do_sample: bool = True) -> Optional[str]:
        """
        生成文本
        
        参数:
            text: 输入文本
            max_new_tokens: 最大新生成token数
            temperature: 温度参数
            do_sample: 是否采样
            
        返回:
            生成的文本，如果失败则返回None
        """
        # 检查模型是否已加载
        if self.model is None or self.tokenizer is None:
            print("❌ 模型或tokenizer未加载")
            return None
        
        try:
            # 获取模型设备
            device = next(self.model.parameters()).device
            
            # 文本编码
            inputs = self.tokenizer.encode(text, return_tensors="pt")
            inputs = inputs.to(device)
            print(f"✅ 文本编码成功: {text} -> {inputs.shape} -> {inputs.device}")
            
            # 生成文本
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_length=inputs.shape[1] + max_new_tokens,
                    num_return_sequences=1,
                    temperature=temperature,
                    do_sample=do_sample,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return response
        except Exception as e:
            print(f"❌ 生成失败: {e}")
            return None
    
    def chat(self, prompt: str, history: Optional[List[Tuple[str, str]]] = None) -> Tuple[Optional[str], List[Tuple[str, str]]]:
        """
        使用chat函数进行对话
        
        参数:
            prompt: 输入提示
            history: 对话历史，默认为None
            
        返回:
            (回复, 更新后的历史)
        """
        # 检查模型是否已加载
        if self.model is None or self.tokenizer is None:
            print("❌ 模型或tokenizer未加载")
            return None, history or []
        
        if history is None:
            history = []
        
        try:
            response, new_history = self.model.chat(self.tokenizer, prompt, history=history)
            return response, new_history
        except Exception as e:
            print(f"❌ Chat失败: {e}")
            return None, history
    
    def analyze_financial_text(self, text: str) -> Optional[str]:
        """
        分析金融文本
        
        参数:
            text: 金融文本
            
        返回:
            分析结果，如果失败则返回None
        """
        prompt = f"""请分析以下金融文本的情感倾向（积极/消极/中性）：

文本：{text}

分析结果："""
        
        response, _ = self.chat(prompt)
        return response


def read_financial_report_section(file_path: str, max_length: int = 1000) -> str:
    """
    读取财报文件中的一个部分
    
    参数:
        file_path: 文件路径
        max_length: 最大字符数
        
    返回:
        财报文本的一个部分
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 将内容分成段落
        paragraphs = content.split('\n\n')
        
        # 选择一个有意义的部分（跳过表格和标题）
        valid_paragraphs = []
        for p in paragraphs:
            # 跳过表格和短段落
            if '[表格:' not in p and len(p) > 50 and not p.startswith('#'):
                valid_paragraphs.append(p)
        
        # 如果没有找到有效段落，返回原始内容的一部分
        if not valid_paragraphs:
            return content[:max_length]
        
        # 随机选择一个段落
        selected = random.choice(valid_paragraphs)
        
        # 如果段落太长，截断它
        if len(selected) > max_length:
            return selected[:max_length]
        
        return selected
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return ""


def find_financial_reports(base_dir: str = 'dogs_of_30_mdna', limit: int = 3) -> List[str]:
    """
    查找财报文件
    
    参数:
        base_dir: 基础目录
        limit: 最大文件数量
        
    返回:
        财报文件路径列表
    """
    report_files = []
    
    try:
        # 获取所有公司目录
        companies = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
        
        # 随机选择一些公司
        selected_companies = random.sample(companies, min(limit, len(companies)))
        
        for company in selected_companies:
            company_dir = os.path.join(base_dir, company)
            # 获取该公司的所有清洁版MD文件
            md_files = [f for f in os.listdir(company_dir) if f.endswith('_cleaned.md')]
            
            if md_files:
                # 随机选择一个文件
                selected_file = random.choice(md_files)
                report_files.append(os.path.join(company_dir, selected_file))
    
    except Exception as e:
        print(f"❌ 查找财报文件失败: {e}")
    
    return report_files


def test_llm_provider():
    """测试LLMProvider类"""
    print("🚀 开始测试LLMProvider...")
    print("=" * 60)
    
    # 初始化LLMProvider
    provider = LLMProvider(cache_dir="/root/autodl-tmp/huggingface_cache")
    
    # 加载模型
    if not provider.load_model():
        print("❌ 模型加载失败，程序退出")
        return
    
    # 测试生成文本
    print("\n🔍 测试文本生成...")
    response = provider.generate_text("你好")
    print(f"生成结果: {response}")
    
    # 测试chat函数
    print("\n🔍 测试chat函数...")
    response, history = provider.chat("你好，请介绍一下你自己")
    print(f"Chat结果: {response}")
    
    # 测试金融文本分析（使用示例文本）
    print("\n📈 测试金融文本分析（示例文本）...")
    sample_texts = [
        "公司第四季度财报超出预期，股价大涨10%",
        "经济数据疲软，市场担忧情绪上升",
        "央行宣布降息政策，利好股市"
    ]
    
    for i, text in enumerate(sample_texts, 1):
        print(f"\n--- 示例 {i} ---")
        print(f"原文：{text}")
        analysis = provider.analyze_financial_text(text)
        print(f"分析：{analysis}")
    
    # 测试使用真实财报数据进行分析
    print("\n📊 测试使用真实财报数据进行分析...")
    report_files = find_financial_reports()
    
    for i, file_path in enumerate(report_files, 1):
        print(f"\n--- 财报 {i}: {os.path.basename(file_path)} ---")
        
        # 读取财报的一个部分
        report_section = read_financial_report_section(file_path)
        print(f"财报部分（前100个字符）: {report_section[:100]}...")
        
        # 分析财报
        analysis = provider.analyze_financial_text(report_section)
        print(f"分析结果: {analysis}")
    
    print("\n🎉 所有测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    test_llm_provider()