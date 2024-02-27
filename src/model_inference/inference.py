from src.model_inference.complexity import num_tokens_from_string
from openai import OpenAI

api_key = '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'  # 0226
client = OpenAI(api_key=api_key)


def get_completion(prompt, model="gpt-3.5-turbo"):
  try:
    # prompt 不超过 2048 个字符
    num_tokens = num_tokens_from_string(prompt)
    if num_tokens > 2048:
      # 超过则直接返回，不进行询问
      return "TOO_LONG_" + str(num_tokens)
    messages = [{"role": "user", "content": prompt}]
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0, # this is the degree of randomness of the model's output, 0: precise, 1: creative
    )
    return response.choices[0].message["content"]
  except Exception as e:
    # 处理未知异常的逻辑
    print()
    traceback.print_exc()  # 打印异常的堆栈跟踪信息
    time.sleep(10)

    if 'Limit: 200 / day.' in str(e):
      print("RateLimitError！" * 10)
      return
    return get_completion(prompt)

print(num_tokens_from_string('I love China!'))
