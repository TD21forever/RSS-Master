import logging
import os

import openai

logger = logging.getLogger()
openai.api_key = os.getenv("OPENAI_API_KEY")


def gpt_summary(query, model, summary_length):
    if len(query) < 400:
        logger.debug(f"Query Length: {len(query)}, Too Short, Return")
        return ""
    query = query[:3000]
    messages = [
            {"role": "user", "content": query},
            {"role": "assistant", "content": f"请用中文总结这篇文章，先提取出三个关键词，在同一行内输出，然后输出两个<br>, 再用中文在{summary_length}字内写一个简短总结.即格式为:关键词 + '<br><br>总结:'. 强调下, <br>是HTML的换行符，输出时必须保留2个，并且必须在'总结:'二字之前"}
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
    logger.debug(f"Query Length: {len(query)}, Total Tokens Usage: {total_tokens}, Price: {price:.8f}") # type: ignore
    return chat["choices"][0]["message"]["content"] # type: ignore
