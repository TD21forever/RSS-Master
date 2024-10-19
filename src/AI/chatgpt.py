import json
import logging

import openai

from .openai_price_cost import calculate_pricing

logger = logging.getLogger()


def gpt_summary(query, model):
    # Define a default response structure
    response = {
        "summary": "",
        "price": 0,
        "tokens": 0
    }

    # Early exit for short queries
    if len(query) < 400:
        logger.debug(
            f"Query too short (Length: {len(query)}), skipping request.")
        return response

    # Construct the prompt
    prompt = f"""
    假设你是一位多语言的文字编辑工作者,有丰富的文字内容创作经验,对于<>括起来的文本,我需要你
    
    1. 生成4个关键词
    2. 使用中文简要总结文中提出的关键论点,要包含原文核心思想和概念,不增加自己的解释,不超过8句话

    请使用以下格式:
    关键词: <提取出来的关键词,使用逗号分割>
    <br>
    <br>
    总结: <中文概括>
    
    Text: <{query}>
    """

    messages = [{"role": "user", "content": prompt}]

    try:
        # Request GPT completion
        chat = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=0,  # More deterministic result
            n=1,            # Only one response
            timeout=30
        )
        # Calculate the cost and total tokens used
        total_tokens = chat['usage']['total_tokens']  # type: ignore
        cost = calculate_pricing(
            model=model,
            token_input=chat.usage.prompt_tokens,  # type: ignore
            token_output=chat.usage.completion_tokens  # type: ignore
        )

        # Extract content from the response
        content = chat["choices"][0]["message"]["content"]  # type: ignore

        # Populate response
        response.update({
            "price": cost,
            "tokens": total_tokens,
            "summary": content
        })

    except Exception as e:
        logger.error(f"Error in GPT completion: {str(e)}", exc_info=True)
        return response

    logger.debug(
        f"GPT Summary Response: {json.dumps(response, indent=2, ensure_ascii=False)}")
    return response
