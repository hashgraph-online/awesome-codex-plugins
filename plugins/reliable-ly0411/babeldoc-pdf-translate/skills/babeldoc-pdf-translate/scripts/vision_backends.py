"""Image transport for explicitly configured OpenAI-compatible vision servers."""
import base64
import json
import time
import httpx
import chat_bridge as bridge
from model_endpoints import api_key,loopback


class CompatibleVision:
    def __init__(self,provider,schema,transport=None):
        self.provider,self.schema,self.transport=provider,schema,transport
        self.version='openai-chat-completions-image-v1'

    def doctor(self):
        api_key(self.provider)  # Check only; never reveal the value.
        if self.provider['model'].startswith('YOUR-') or '.example' in self.provider['base_url']:
            raise ValueError('Replace example model and endpoint before execution')
        return {'ready':True,'native_version':self.version,'backend':'openai'}

    def inspect(self,prompt,images,timeout,schema=None):
        response_schema=self.schema if schema is None else schema
        started=time.monotonic()
        content=[{'type':'text','text':prompt}]
        for path in images:
            if path.stat().st_size>20*1024*1024:
                raise bridge.BridgeError('VISION_IMAGE_LIMIT')
            content.append({'type':'image_url','image_url':{'url':'data:image/png;base64,'+
                base64.b64encode(path.read_bytes()).decode('ascii')}})
        payload={'model':self.provider['model'],'messages':[{'role':'user','content':content}],
                 'stream':False,self.provider['token_limit_field']:self.provider['max_tokens']}
        fmt=self.provider['response_format']
        if fmt=='json_schema':
            payload['response_format']={'type':'json_schema','json_schema':{'name':'pdf_visual_review',
                                         'strict':True,'schema':response_schema}}
        elif fmt=='json_object':
            payload['response_format']={'type':'json_object'}
        # Even endpoints without schema support receive the exact schema as data.
        content[0]['text']+='\nRequired JSON schema:\n'+bridge.canonical(response_schema)
        key=api_key(self.provider)
        headers={'Authorization':'Bearer '+key} if key else {}
        try:
            with httpx.Client(transport=self.transport,follow_redirects=False,
                              trust_env=not loopback(self.provider['base_url'])) as client:
                with client.stream('POST',self.provider['base_url']+'/chat/completions',
                                   json=payload,headers=headers,timeout=timeout) as response:
                    if response.status_code!=200:
                        raise bridge.BridgeError('VISION_HTTP_'+str(response.status_code))
                    data=bytearray()
                    for chunk in response.iter_bytes():
                        if time.monotonic()-started>=timeout:
                            raise bridge.BridgeError('VISION_TIMEOUT')
                        data.extend(chunk)
                        if len(data)>2*bridge.MAX_REPLY:
                            raise bridge.BridgeError('VISION_OUTPUT_LIMIT')
            reply=json.loads(data)
            choices=reply['choices']
            if len(choices)!=1 or choices[0].get('finish_reason') not in {None,'stop'}:
                raise bridge.BridgeError('VISION_INCOMPLETE_RESPONSE')
            message=choices[0]['message']
            if message.get('tool_calls') or message.get('function_call'):
                raise bridge.BridgeError('UNEXPECTED_TOOL_USE')
            if message.get('refusal'):
                raise bridge.BridgeError('VISION_REFUSAL')
            value=message['content']
            if not isinstance(value,str) or len(value.encode('utf-8'))>bridge.MAX_REPLY:
                raise ValueError()
            return json.loads(value),reply.get('usage')
        except httpx.TimeoutException:
            raise bridge.BridgeError('VISION_TIMEOUT') from None
        except httpx.HTTPError:
            raise bridge.BridgeError('VISION_CONNECTION_FAILED') from None
        except (ValueError,KeyError,TypeError):
            raise bridge.BridgeError('INVALID_VISUAL_RESPONSE') from None
