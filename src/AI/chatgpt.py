import json
import logging
import os

import openai

logger = logging.getLogger()
openai.api_key = os.getenv("OPENAI_API_KEY")


def gpt_summary(query, model):
    response = {
        "summary": "",
        "price": 0,
        "tokens": 0
    }
    if len(query) < 400:
        logger.debug(f"Query Length: {len(query)}, Too Short, Return")
        return response
    query = query[:3000]
    prompt = f"""
        假设你是一位多语言的文字编辑工作者,有丰富的文字内容创作经验,对于<>括起来的文本,我需要你
        
        1. 生成4个关键词
        2. 使用中文进行概括,要包含原文核心思想和概念,不增加自己的解释,不超过8句话

        请使用一下格式:
        关键词: <提取出来的关键词,使用逗号分割>
        <br>
        <br>
        总结: <中文概括>
        
        Text: <{query}>
    """
    messages = [
            {"role": "user", "content": prompt}
        ]
    chat = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=0,  # most confident result
        n=1,  # only one choice
        timeout=30
    )
    completion_tokens = chat['usage']['completion_tokens'] # type: ignore
    prompt_tokens = chat['usage']['prompt_tokens'] # type: ignore
    total_tokens = chat['usage']['total_tokens'] # type: ignore
    price = completion_tokens // 1000 * 0.0015 + prompt_tokens // 1000 * 0.0002
    content = chat["choices"][0]["message"]["content"] # type: ignore
    response["price"], response["tokens"], response["summary"] = price, total_tokens, content
    logger.debug(f"GPT Summary Response {json.dumps(response, indent=2)}")
    return response
