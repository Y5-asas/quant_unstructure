import os
from openai import OpenAI


def qwen_response(sys_prompt, user_prompt, model="qwen-plus"):
    """
    每次对话都重新起一个 client
    """
    client = OpenAI(
        # 新加坡和北京地域的API Key不同。
        # 获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
        api_key=None,
        # 以下是北京地域base_url，如果使用新加坡地域的模型，需要将base_url替换为：
        # https://dashscope-intl.aliyuncs.com/compatible-mode/v1
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    completion = client.chat.completions.create(
        # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
        model=model,
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    # print(completion.choices[0].message.content)
    content = completion.choices[0].message.content
    return content


def qwen_client_response(client: OpenAI, sys_prompt, user_prompt, model="qwen-plus"):
    completion = client.chat.completions.create(
        # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
        model=model,
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    # print(completion.choices[0].message.content)
    content = completion.choices[0].message.content
    return content
