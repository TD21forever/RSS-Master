import os

from openai import ChatCompletion



def gpt_summary(query, model, keyword_length, summary_length):
    messages = [
            {"role": "user", "content": query},
            {"role": "assistant", "content": f"请用中文总结这篇文章，先提取出{keyword_length}个关键词，在同一行内输出，然后换行，用中文在{summary_length}字内写一个简短总结，按照以下格式输出'<br><br>总结:'，<br>是HTML的换行符，输出时必须保留2个，并且必须在'总结:'二字之前"}
        ]
    chat = ChatCompletion.create(
        model=model,
        api_key=os.environ.get("OPENAI_API_KEY", None),
        messages=messages,
        temperature=0,  # most confident result
        n=1,  # only one choice
        timeout=30
    )
    return chat["choices"][0]["message"]["content"] # type: ignore
