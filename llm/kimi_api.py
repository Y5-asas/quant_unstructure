from openai import OpenAI

KIMI_API_KEY = "sk-SXRupCTCmRozXPTBLE237MN4iyHaAm1sN1GKybRAIkhHXwdQ"
KIMI_BASE_URL = "https://api.moonshot.cn/v1"


def kimi_response(
    sys_prompt, user_prompt, model="kimi-k2-0905-preview", temperature=0.6
):
    """
    每次对话都重新起一个 client
    """
    client = OpenAI(
        api_key=KIMI_API_KEY,
        base_url="https://api.moonshot.cn/v1",
    )

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": sys_prompt,
            },
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
    )

    # print(completion.choices[0].message.content)
    content = completion.choices[0].message.content
    return content


def kimi_client_response(
    client: OpenAI,
    sys_prompt,
    user_prompt,
    model="kimi-k2-0905-preview",
    temperature=0.6,
):
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": sys_prompt,
            },
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
    )

    # print(completion.choices[0].message.content)
    content = completion.choices[0].message.content
    return content
