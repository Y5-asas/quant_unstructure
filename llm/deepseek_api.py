import os
from openai import OpenAI


def deepseek_response(sys_prompt, user_prompt, model="deepseek-chat"):
    """
    每次对话都重新起一个 client
    """
    client = OpenAI(api_key=None, base_url="https://api.deepseek.com")
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt},
        ],
        stream=False,
    )

    # print(response.choices[0].message.content)
    content = response.choices[0].message.content
    return content


def deepseek_client_response(
    client: OpenAI, sys_prompt, user_prompt, model="deepseek-chat"
):
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt},
        ],
        stream=False,
    )

    # print(response.choices[0].message.content)
    content = response.choices[0].message.content
    return content
