import json
import logging
import os

import openai

logger = logging.getLogger()
openai.api_key = os.getenv("OPENAI_API_KEY")


def gpt_summary(query, model, summary_length):
    response = {
        "summary": "",
        "price": 0,
        "tokens": 0
    }
    if len(query) < 400:
        logger.debug(f"Query Length: {len(query)}, Too Short, Return")
        return response
    query = query[:3000]
    messages = [
            {"role": "user", "content": query},
            {"role": "assistant", "content": f"First, you will first extract at most five short keywords and output them on the same line. Then, add two HTML line breaks (<br>). Next, I want you to act as a text summarizer to help me create a concise Chinese summary of the text I provide. The summary section will start with the words '总结:' and the summary can be up to 8 sentences in length, expressing the key points and concepts written in the original text without adding your interpretations."}
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
