"""Explicit OpenAI-compatible endpoints, including already-running local servers."""
import ipaddress
import os
from pathlib import Path
import re
from urllib.parse import urlparse


def loopback(url):
    host=urlparse(url).hostname
    if host=='localhost':
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except (ValueError,TypeError):
        return False


def validate_api_provider(provider,base,*,vision=False):
    if not isinstance(provider,dict):
        raise ValueError('Provider must be an object')
    fields={'type','base_url','model','api_key_env','auth'}
    if vision:
        fields|={'vision','timeout_seconds','retries','cache_dir','max_model_calls','response_format','max_tokens','token_limit_field'}
    if set(provider)-fields or not {'base_url','model'}<=set(provider):
        raise ValueError('Unknown or missing compatible API provider fields')
    result=dict(provider)
    if result.setdefault('type','openai')!='openai':
        raise ValueError('Compatible API provider type must be openai')
    for key in ('base_url','model'):
        if not isinstance(result[key],str) or not result[key].strip():
            raise ValueError('provider.'+key+' must be a nonempty string')
    url=urlparse(result['base_url'])
    if url.scheme not in {'http','https'} or not url.hostname or url.username or url.password or url.query or url.fragment:
        raise ValueError('Endpoint must be http(s), without embedded credentials/query/fragment')
    try:
        url.port
    except ValueError:
        raise ValueError('Invalid endpoint port') from None
    result['base_url']=result['base_url'].rstrip('/')
    auth=result.setdefault('auth','env')
    if auth=='none':
        if not loopback(result['base_url']) or 'api_key_env' in result:
            raise ValueError('auth=none requires a loopback endpoint and no credential field')
    elif auth=='env':
        if not isinstance(result.get('api_key_env'),str) or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',result['api_key_env']):
            raise ValueError('Invalid API key environment variable name')
    else:
        raise ValueError('provider.auth must be env or explicit local none')
    if vision:
        if result.get('vision') is not True:
            raise ValueError('Visual review requires provider.vision=true and a successful image capability probe')
        for key,default,low,high in [('timeout_seconds',180,5,1800),('max_model_calls',6,1,64),('max_tokens',8192,256,65536)]:
            value=result.setdefault(key,default)
            if type(value) is not int or not low<=value<=high:
                raise ValueError('Invalid provider budget: '+key)
        retries=result.setdefault('retries',0)
        if type(retries) is not int or retries!=0:
            raise ValueError('Visual requests use zero automatic retries')
        fmt=result.setdefault('response_format','json_schema')
        if not isinstance(fmt,str) or fmt not in {'json_schema','json_object','none'}:
            raise ValueError('Unknown compatible API response format')
        field=result.setdefault('token_limit_field','max_tokens')
        if not isinstance(field,str) or field not in {'max_tokens','max_completion_tokens'}:
            raise ValueError('Unknown compatible API token limit field')
        if 'cache_dir' in result:
            if not isinstance(result['cache_dir'],str) or not result['cache_dir'].strip():
                raise ValueError('Invalid cache directory')
            result['cache_dir']=str((base/Path(result['cache_dir']).expanduser()).resolve())
    return result


def api_key(provider):
    if provider['auth']=='none':
        return None
    value=os.environ.get(provider['api_key_env'])
    if not value:
        raise ValueError('Required credential environment variable is unset')
    return value
