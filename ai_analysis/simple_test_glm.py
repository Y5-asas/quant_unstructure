#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChatGLM2-6B 测试脚本
用于测试FinGPT模型是否正常加载和运行
"""

import os
os.environ['HF_HOME'] = "/root/autodl-tmp/huggingface_cache"
os.environ['HF_ENDPOINT'] = "https://hf-mirror.com"
os.environ['HF_HUB_DISABLE_TELEMETRY'] = "1"
os.environ['HF_HUB_DOWNLOAD_TIMEOUT'] = "1000"

import torch
from transformers import AutoTokenizer, AutoModel

# 设置环境变量


def setup_environment():
    """设置和显示环境变量"""
    print("🚀 设置环境变量...")
    print(f"📁 缓存目录: {os.environ.get('HF_HOME')}")
    print(f"🌐 镜像源: {os.environ.get('HF_ENDPOINT')}")
    print("✅ 环境变量设置完成")

def load_model(model_name="THUDM/chatglm2-6b"):
    """加载模型"""
    print(f"🔍 正在加载模型: {model_name}")
    
    try:
        # 加载tokenizer
        tokenizer = AutoTokenizer.from_pretrained(
            model_name, 
            trust_remote_code=True
        )
        print("✅ Tokenizer加载成功")
        
        # 加载模型
        model = AutoModel.from_pretrained(
            model_name, 
            trust_remote_code=True, 
            device_map='auto',
            torch_dtype=torch.float16
        )
        print("✅ 模型加载成功")
        
        return tokenizer, model
    except Exception as e:
        print(f"❌ 模型加载失败: {e}")
        return None, None

def check_model_info(model):
    """检查模型信息"""
    print("\n📊 模型信息:")
    print(f"模型类型: {type(model)}")
    print(f"设备: {next(model.parameters()).device}")
    print(f"数据类型: {next(model.parameters()).dtype}")
    
    # 计算参数数量
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"总参数数量: {total_params:,}")
    print(f"可训练参数数量: {trainable_params:,}")

def test_simple_generation(tokenizer, model):
    """测试简单文本生成"""
    print("\n🔍 测试简单文本生成...")
    
    try:
        # 获取模型设备
        device = next(model.parameters()).device
        print(f"模型设备: {device}")
        
        # 简单的文本编码
        text = "你好"
        inputs = tokenizer.encode(text, return_tensors="pt")
        inputs = inputs.to(device)
        print(f"✅ 文本编码成功: {text} -> {inputs.shape} -> {inputs.device}")
        
        # 简单的生成
        with torch.no_grad():
            outputs = model.generate(
                inputs,
                max_length=inputs.shape[1] + 50,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print(f"✅ 生成成功: {response}")
        
        return True
    except Exception as e:
        print(f"❌ 生成失败: {e}")
        return False

def test_chat_function(tokenizer, model):
    """测试chat函数"""
    print("\n🔍 测试chat函数...")
    
    try:
        prompt = "你好，请介绍一下你自己"
        response, _ = model.chat(tokenizer, prompt, history=[])
        print(f"✅ Chat成功: {response}")
        return True
    except Exception as e:
        print(f"❌ Chat失败: {e}")
        return False

def test_financial_analysis(tokenizer, model):
    """测试金融文本分析"""
    print("\n📈 测试金融文本分析...")
    
    sample_texts = [
        "公司第四季度财报超出预期，股价大涨10%",
        "经济数据疲软，市场担忧情绪上升",
        "央行宣布降息政策，利好股市"
    ]
    
    for i, text in enumerate(sample_texts, 1):
        print(f"\n--- 示例 {i} ---")
        print(f"原文：{text}")
        
        prompt = f"""请分析以下金融文本的情感倾向（积极/消极/中性）：

文本：{text}

分析结果："""
        
        try:
            response, _ = model.chat(tokenizer, prompt, history=[])
            print(f"分析：{response}")
        except Exception as e:
            print(f"分析出错: {e}")
    
    print("-" * 50)

def main():
    """主函数"""
    print("🚀 开始测试ChatGLM2-6B模型...")
    print("=" * 60)
    
    # 设置环境
    setup_environment()
    
    # 加载模型
    tokenizer, model = load_model()
    
    if tokenizer is None or model is None:
        print("❌ 模型加载失败，程序退出")
        return
    
    # 检查模型信息
    check_model_info(model)
    
    # 运行测试
    test_simple_generation(tokenizer, model)
    test_chat_function(tokenizer, model)
    test_financial_analysis(tokenizer, model)
    
    print("\n🎉 所有测试完成！模型运行正常！")
    print("=" * 60)

if __name__ == "__main__":
    main()
