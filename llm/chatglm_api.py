from zai import ZhipuAiClient

CHATGLM_API_KEY = "e20eebe7ff144058a9aa499443a52857.FtSUlR93Y5udS2Cz"


def chatglm_api(sys_prompt, user_prompt, model="glm-4.6", temperature=0.6):
    """
    每次对话都重新起一个 client
    """
    client = ZhipuAiClient(api_key=CHATGLM_API_KEY)

    # 创建聊天完成请求
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
    )

    # print(response.choices[0].message.content)
    content = response.choices[0].message.content
    return content


def chatglm_client_response(
    client: ZhipuAiClient, sys_prompt, user_prompt, model="glm-4.6", temperature=0.6
):
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
    )

    # print(response.choices[0].message.content)
    content = response.choices[0].message.content
    return content
