from math import ceil

model_price_map = {

    # OpenAI o1-preview
    'o1-preview-input': 0.015,
    'o1-preview-output': 0.060,
    'o1-preview-2024-09-12-input': 0.015,
    'o1-preview-2024-09-12-output': 0.060,
    # OpenAI o1-mini
    'o1-mini-input': 0.003,
    'o1-mini-output': 0.012,
    'o1-mini-2024-09-12-input': 0.003,
    'o1-mini-2024-09-12-output': 0.012,
    # GPT-4o mini
    'gpt-4o-mini-input': 0.000150,
    'gpt-4o-mini-output': 0.000600,
    'gpt-4o-mini-vision': 0.005,
    'gpt-4o-mini-2024-07-18-input': 0.000150,
    'gpt-4o-mini-2024-07-18-output': 0.000600,
    # GPT-4o
    'gpt-4o-input': 0.0050,
    'gpt-4o-output': 0.0150,
    'gpt-4o-vision': 0.005,
    'gpt-4o-2024-05-13-input': 0.0050,
    'gpt-4o-2024-05-13-output': 0.0150,
    # GPT-3.5
    'gpt-3.5-turbo-0125-input': 0.00050,
    'gpt-3.5-turbo-0125-output': 0.00150,
    'gpt-3.5-turbo-input': 0.00050,
    'gpt-3.5-turbo-output': 0.00150,
    'gpt-3.5-turbo-instruct-input': 0.00150,
    'gpt-3.5-turbo-instruct-output': 0.00200,
    # DALLE 2
    'dall-e-2-256x256': 0.016,
    'dall-e-2-512x512': 0.018,
    'dall-e-2-1024x1024': 0.020,
    # DALLE 3
    'dalle-3-standard-1024x1024': 0.040,
    'dalle-3-standard-1024x1792': 0.080,
    'dalle-3-standard-1792x1024': 0.080,
    'dalle-3-hd-1024x1024': 0.080,
    'dalle-3-hd-1024x1792': 0.120,
    'dalle-3-hd-1792x1024': 0.120,
    # Embedding
    'text-embedding-3-large': 0.00013,
    'text-embedding-3-small': 0.00002,
    'text-embedding-ada-002': 0.00010,
    # Voice
    'whisper-1': 0.006,
    'tts-1': 0.015,
    'tts-1-hd': 0.030,
    # Older Models
    "chatgpt-4o-latest-input": 0.0050,
    "chatgpt-4o-latest-output": 0.0150,
    "gpt-4-turbo-input": 0.0100,
    "gpt-4-turbo-output": 0.0300,
    "gpt-4-turbo-2024-04-09-input": 0.0100,
    "gpt-4-turbo-2024-04-09-output": 0.0300,
    "gpt-4-input": 0.0300,
    "gpt-4-output": 0.0600,
    "gpt-4-32k-input": 0.0600,
    "gpt-4-32k-output": 0.1200,
    "gpt-4-0125-preview-input": 0.0100,
    "gpt-4-0125-preview-output": 0.0300,
    "gpt-4-1106-preview-input": 0.0100,
    "gpt-4-1106-preview-output": 0.0300,
    "gpt-4-vision-preview-input": 0.0100,
    "gpt-4-vision-preview-output": 0.0300,
    "gpt-3.5-turbo-1106-input": 0.0010,
    "gpt-3.5-turbo-1106-output": 0.0020,
    "gpt-3.5-turbo-0613-input": 0.0015,
    "gpt-3.5-turbo-0613-output": 0.0020,
    "gpt-3.5-turbo-16k-0613-input": 0.0030,
    "gpt-3.5-turbo-16k-0613-output": 0.0040,
    "gpt-3.5-turbo-0301-input": 0.0015,
    "gpt-3.5-turbo-0301-output": 0.0020,
    "davinci-002-input": 0.0020,
    "davinci-002-output": 0.0020,
    "babbage-002-input": 0.0004,
    "babbage-002-output": 0.0004
}


def calculate_pricing(model,
                      token_input=0,
                      token_output=0,
                      img_num=0,
                      minutes=0.00,
                      img_w=0,
                      img_h=0):

    if token_input != 0 and model[0:4] in ['gpt', 'dav', 'bab', 'o1', 'chat'
                                           ] and (img_w and img_h) == 0:

        token_price = model_price_map.get(model + '-input', 0)
        input_cost = (token_input / 1000) * token_price
        token_price = model_price_map.get(model + '-output', 0)
        output_cost = (token_output / 1000) * token_price

        return input_cost + output_cost

    elif img_num != 0 and model[:5] in ['dalle', 'dall']:

        dimn_price = model_price_map.get(model, 0)
        dalle_price = dimn_price * img_num

        return dalle_price

    elif minutes != 0.00 and model in ['whisper-1', 'tts-1', 'tts-1-hd']:

        mint_price = model_price_map.get(model, 0)
        whisp_price = mint_price * minutes

        return whisp_price

    elif (img_w != 0 and img_h != 0) and model in [
            'gpt-4o-mini', 'gpt-4o', 'gpt-4-vision-preview'
    ]:

        price_per_thousand_tokens = 0.005
        num_tiles = ceil(img_w / 512) * ceil(img_h / 512)
        base_tokens = 85
        tile_tokens = 170 * num_tiles
        total_tokens = base_tokens + tile_tokens
        image_price = (total_tokens / 1000) * price_per_thousand_tokens

        token_price = model_price_map.get(model + '-input', 0)
        input_cost = (token_input / 1000) * token_price
        token_price = model_price_map.get(model + '-output', 0)
        output_cost = (token_output / 1000) * token_price

        return input_cost + output_cost + round(image_price, 6)

    else:
        return None
