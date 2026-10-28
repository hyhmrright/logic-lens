"""Evaluator-only checks for additional discoveries in the Codex pilot.

These are not supplied to the reviewer. They run real historical HTTPX code with
in-process transports/temporary environment overrides, never network requests.
"""
import asyncio
import importlib
import os
from pathlib import Path
import sys
from unittest.mock import patch


def check(name, workspace):
    sys.path.insert(0,str(workspace))
    h=importlib.import_module('httpx')
    assert Path(h.__file__).resolve().is_relative_to(workspace.resolve())
    if name=='blank-query':
        assert str(h.QueryParams('a='))=='a=', 'blank query value was dropped'
    elif name=='idna-port':
        url=h.URL('https://中国.icom.museum/').copy_with(port=8443)
        assert url.port==8443 and url.host=='中国.icom.museum'
    elif name=='query-hash':
        a,b=h.QueryParams('a=1&b=2'),h.QueryParams('b=2&a=1')
        assert a==b
        assert hash(a)==hash(b), 'equal query params have unequal hashes'
    elif name=='asgi-env':
        async def app(scope,receive,send):pass
        async def inspect():
            with patch.dict(os.environ,{'HTTP_PROXY':'http://proxy.example:8080'},clear=True):
                async with h.AsyncClient(app=app) as client:
                    selected=client._transport_for_url(h.URL('http://testserver/'))
                    assert isinstance(selected,h.ASGITransport),type(selected).__name__
        asyncio.run(inspect())
    elif name=='auth-redirect-budget':
        def handle(request):
            if 'Authorization' not in request.headers:
                return h.Response(401,headers={'WWW-Authenticate':'Digest realm="test", nonce="n"'})
            return h.Response(200)
        with h.Client(max_redirects=0,auth=h.DigestAuth('u','p'),transport=h.MockTransport(handle)) as client:
            assert client.get('http://example.org/').status_code==200
    elif name=='auth-history':
        class Auth(h.Auth):
            def auth_flow(self,request):
                response=yield request
                if response.status_code==401:
                    response.request.headers['X-Authentication']='yes'
                    yield response.request
        def handle(request):
            if request.url.path=='/start':return h.Response(302,headers={'Location':'/protected'})
            return h.Response(200 if request.headers.get('X-Authentication') else 401)
        with h.Client(auth=Auth(),follow_redirects=True,transport=h.MockTransport(handle)) as client:
            response=client.get('http://example.org/start')
            assert [r.status_code for r in response.history]==[302,401],[r.status_code for r in response.history]
    else:raise ValueError(name)


if __name__=='__main__':check(sys.argv[1],Path(sys.argv[2]).resolve())
