# -*- coding: utf-8 -*-

# Copyright (c) 2025 shmilee

import os
import openai
import base64
import json_repair
import yaml
import functools
print = functools.partial(print, flush=True)


class Analyzer(object):
    '''
    识别图中内容，返回 JSON 输出
    '''
    default_model = "NO-MODEL"

    def __init__(self, model=None, max_tokens=8192,
                 temperature=1.0, thinking=False,
                 system_prompt=None, user_prompt=None, **kwargs):
        self.set_AiClient()
        self.model = model or self.default_model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.thinking = thinking
        self.system_prompt = system_prompt or """
            用户将提供一些图片，你作为一个专业的图片分析器，
            任务是准确分析图片内容，确定适合图片的一些标签，
            并根据用户要求描述图片。
            请严格按照以下 JSON 格式输出：
            {
                "name": "图片的名称",
                "desc": "图片的详细描述",
                "tags": ["一些适合图片的标签"]
            }
        """
        self.user_prompt = user_prompt or '图片描述控制在200字左右。'

    def set_AiClient(self):
        # for self.client.chat.completions.create
        raise NotImplementedError()

    def _create_img_msg(self, image_data: bytes, mime_type: str):
        base64_data = base64.b64encode(image_data).decode('utf-8')
        return {
            "type": "image_url",
            "image_url": {
                "url": f"data:{mime_type};base64,{base64_data}"
            }
        }

    def _create_thinking_kwargs(self):
        return dict(extra_body={
            "thinking": {
                "type": "enabled" if self.thinking else "disabled",
            }
        })

    def create_response(self, image_data: bytes, mime_type: str):
        img_msg = self._create_img_msg(image_data, mime_type)
        text_msg = {"type": "text", "text": self.user_prompt}
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": [img_msg, text_msg]},
            ],
            response_format={
                "type": "json_object",
            },
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            stream=True,  # 启用流式输出
            **self._create_thinking_kwargs()
        )
        return response

    def get_response_message(self, response):
        # 初始化变量用于收集流式数据
        reasoning_content = ""     # 推理过程内容
        content = ""               # 回答内容
        reasoning_started = False  # 推理过程开始标志
        content_started = False    # 内容输出开始标志
        for idx, chunk in enumerate(response, 1):
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            # 处理流式推理过程输出
            if (self.thinking and hasattr(delta, 'reasoning_content')
                    and delta.reasoning_content):
                if not reasoning_started:
                    print("\n🧠 思考过程：")
                    reasoning_started = True
                reasoning_content += delta.reasoning_content
                if reasoning_content.strip():
                    print(delta.reasoning_content, end="")
            # 处理流式回答内容输出
            if hasattr(delta, 'content') and delta.content:
                if not content_started:
                    print("\n💬 回答内容：")
                    content_started = True
                content += delta.content
                if content.strip():
                    print(delta.content, end="")
        return content.strip()

    def chat(self, image_data: bytes, mime_type: str):
        print('🤖 Creating chat ...', end=' ')
        response = self.create_response(image_data, mime_type)
        print('Done.')
        msg = self.get_response_message(response)
        # ref: https://github.com/mangiucugna/json_repair
        obj = json_repair.repair_json(msg, return_objects=True,
                                      ensure_ascii=False)
        # with open('./sample-msg.json', 'w') as fp:
        #    import json
        #    json.dump(obj, fp, indent=2, ensure_ascii=False)
        return obj


class GeminiAnalyzer(Analyzer):
    '''
    选用兼容 openai 接口
    '''
    default_model = "gemini-2.5-flash"

    def set_AiClient(self):
        # https://ai.google.dev/gemini-api/docs/openai?hl=zh-cn
        # need GEMINI_API_KEY environment variable
        self.client = openai.OpenAI(
            api_key=os.environ.get("GEMINI_API_KEY"),
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )

    def _create_thinking_kwargs(self):
        return dict(extra_body={
            'extra_body': {
                "google": {
                    "thinking_config": {
                        "thinking_budget": "low",
                        "include_thoughts": True
                    }
                }
            }
        }) if self.thinking else dict(reasoning_effort="none")


class GenaiAnalyzer(Analyzer):
    '''
    #from google import genai 不兼容 OpenAI
    https://ai.google.dev/gemini-api/docs/image-understanding?hl=zh-cn
    '''
    default_model = "gemini-2.5-flash"

    def set_AiClient(self):
        # need GEMINI_API_KEY environment variable
        from google import genai
        self.client = genai.Client()

    def create_response(self, image_data: bytes, mime_type: str):
        from google.genai import types
        response = self.client.models.generate_content_stream(  # 流式响应
            model=self.model,
            config=types.GenerateContentConfig(
                system_instruction=self.system_prompt,
                # TODO https://ai.google.dev/gemini-api/docs/structured-output?hl=zh-cn
                response_mime_type="application/json",
                # https://ai.google.dev/gemini-api/docs/thinking?hl=zh-cn
                thinking_config=(
                    types.ThinkingConfig(thinking_level="low")
                    if self.thinking else types.ThinkingConfig(thinking_budget=0))
            ),
            contents=[
                types.Part.from_bytes(data=image_data, mime_type=mime_type),
                self.user_prompt
            ],
            # TODO
            # max_tokens=self.max_tokens,
            # temperature=self.temperature,
        )
        return response


class ZhipuAnalyzer(Analyzer):
    # https://bigmodel.cn/usercenter/proj-mgmt/apikeys
    # https://docs.bigmodel.cn/cn/guide/models/free/glm-4.6v-flash
    default_model = "glm-4.6v-flash"

    def set_AiClient(self):
        # need ZAI_API_KEY environment variable
        from zai import ZhipuAiClient
        self.client = ZhipuAiClient(
            api_key=os.environ.get("ZAI_API_KEY")
        )

    def _create_thinking_kwargs(self):
        return dict(thinking={
            "type": "enabled" if self.thinking else "disabled",
        })


class DeepseekAnalyzer(Analyzer):
    '''
    禁用深度思考模式可加速响应, 减少费用。
    启用思考模式 temperature 参数失效。
    https://api-docs.deepseek.com/zh-cn/guides/thinking_mode
    '''
    default_model = "deepseek-chat"

    def set_AiClient(self):
        # https://api-docs.deepseek.com/zh-cn/
        # need XXX_API_KEY environment variable
        self.client = openai.OpenAI(
            api_key=os.environ.get('DEEPSEEK_API_KEY'),
            base_url="https://api.deepseek.com")


# TODO 其他免费平台 https://github.com/fruitbars/simple-one-api
AnalyzerMap = dict(
    default=ZhipuAnalyzer,
    GeminiAnalyzer=GeminiAnalyzer,
    GenaiAnalyzer=GenaiAnalyzer,
    ZhipuAnalyzer=ZhipuAnalyzer,
    DeepseekAnalyzer=DeepseekAnalyzer,  # 不免费
)


def get_analyzer_config(yaml_config: str):
    '''
    ```yaml
    analyzer: class-name
    setting:
       model: deepseek-chat
       system_prompt: XXX
       other-init-kwargs: XXX...
    ```
    '''
    if os.path.isfile(yaml_config):
        with open(yaml_config, 'r', encoding='utf-8') as yc:
            config = yaml.safe_load(yc)
        return dict(
            analyzer=config.get('analyzer', None) or 'default',
            setting=config.get('setting', None) or {}
        )
    else:
        raise FileNotFoundError(f'File {yaml_config} not found!')


if __name__ == "__main__":
    # 单张图片分析
    config = get_analyzer_config('./App-DescTags/config.yaml')
    analyzer = AnalyzerMap[config['analyzer']](**config['setting'])
    image_path = "./logos/aimglyze-light.png"  # 测试 logo 图片
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()
    ext = os.path.splitext(image_path)[1].lower()
    mime_type = f"image/{ext[1:] if ext else 'png'}"
    msg = analyzer.chat(image_data, mime_type)
    print(f"\n🤖 分析结果:\n{msg}")
