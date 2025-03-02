import json
import logging
from typing import Dict, Any, Optional

from openai import OpenAI
from .openai_price_cost import calculate_pricing

logger = logging.getLogger()

# 移除全局客户端
# client = OpenAI()

def gpt_summary(query: str, model: str, client: Optional[OpenAI] = None) -> Dict[str, Any]:
    """
    Generate a summary of the provided text using OpenAI's API.
    
    Args:
        query: The text to summarize
        model: The OpenAI model to use
        client: OpenAI client instance. If None, will create a new client.
        
    Returns:
        Dictionary containing the summary, cost, and token usage
    """
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

    try:
        # 如果没有提供客户端，则创建一个新的客户端
        if client is None:
            client = OpenAI()
            logger.debug("Creating new OpenAI client")
        
        # Request GPT completion using the provided or new client
        chat_completion = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            timeout=30
        )
        
        # Calculate the cost and total tokens used
        total_tokens = chat_completion.usage.total_tokens
        
        # cost = calculate_pricing(
        #     model=model,
        #     token_input=chat_completion.usage.prompt_tokens,
        #     token_output=chat_completion.usage.completion_tokens
        # )

        # Extract content from the response
        content = chat_completion.choices[0].message.content

        # Populate response
        response.update({
            "price": 0,
            "tokens": total_tokens,
            "summary": content or ""
        })

    except Exception as e:
        logger.error(f"Error in GPT completion: {str(e)}", exc_info=True)
        return response

    logger.debug(
        f"GPT Summary Response: {json.dumps(response, indent=2, ensure_ascii=False)}")
    return response
