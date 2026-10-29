"""Evaluator-only checks for additional discoveries in the Codex pilot.

These are not supplied to the reviewer. They run real historical HTTPX code with
in-process transports/temporary environment overrides, never network requests.
"""
import asyncio
import importlib
import os
from pathlib import Path
import sys
sys.dont_write_bytecode = True
from unittest.mock import patch


def check(name, workspace):
    sys.path[:0]=[str(workspace/'src'),str(workspace)]
    h=importlib.import_module('requests' if name.startswith('requests-') else 'httpx')
    assert Path(h.__file__).resolve().is_relative_to(workspace.resolve())
    if name=='requests-buffer-length':
        view=memoryview(b'abcd').cast('H')
        request=h.Request('POST','http://example.org/',data=view).prepare()
        assert int(request.headers['Content-Length'])==view.nbytes,dict(request.headers)
    elif name=='requests-ignored-json':
        request=h.Request('POST','http://example.org/',files={'f':('a.txt',b'ok')},json={'n':float('nan')}).prepare()
        assert b'ok' in request.body
    elif name=='requests-sized-iterable':
        from collections import deque
        request=h.Request('POST','http://example.org/',data=deque([b'ab',b'cd'])).prepare()
        actual=len(b''.join(request.body))
        assert 'Content-Length' not in request.headers or int(request.headers['Content-Length'])==actual,dict(request.headers)
    elif name=='requests-zero-chunk':
        import io
        raw=h.Response();raw.raw=io.BytesIO(b'abc')
        cached=h.Response();cached._content=b'abc';cached._content_consumed=True
        assert list(raw.iter_content(0))==list(cached.iter_content(0))
    elif name=='requests-auth-empty-body':
        def empty(request):request.body=b'';return request
        request=h.Request('POST','http://example.org/',data=b'abc',auth=empty).prepare()
        assert request.headers.get('Content-Length')=='0',dict(request.headers)
    elif name=='requests-response-next':
        import pickle
        response=h.Response();response._content=b'ok';response._content_consumed=True
        assert response.next is None
        assert pickle.loads(pickle.dumps(response)).next is None
    elif name=='requests-json-state':
        import pickle
        request=h.Request('GET','http://example.org/').prepare()
        response=h.Response();response.request=request;response.status_code=502
        error=h.exceptions.JSONDecodeError('bad','x',0,response=response)
        restored=pickle.loads(pickle.dumps(error))
        assert restored.response is not None and restored.request is not None
    elif name=='requests-lines':
        response=h.Response();response._content=b'a\r\nb\r\n';response._content_consumed=True
        assert list(response.iter_lines(chunk_size=2))==[b'a',b'b']
    elif name=='requests-framing':
        request=h.Request('POST','http://example.org/',data=(part for part in [b'abc']),headers={'Content-Length':'3'}).prepare()
        assert not ('Content-Length' in request.headers and 'Transfer-Encoding' in request.headers),dict(request.headers)
    elif name=='requests-readable-rewind':
        import io
        class Readable:
            def __init__(self):self.buffer=io.BytesIO(b'test')
            def read(self,*a):return self.buffer.read(*a)
            def tell(self):return self.buffer.tell()
            def seek(self,*a):return self.buffer.seek(*a)
        request=h.Request('POST','http://example.org/start',data=Readable()).prepare()
        request.body.read()
        response=h.Response();response.status_code=307;response.url=request.url;response.request=request
        response.headers['Location']='/finish';response._content=b''
        redirected=next(h.Session().resolve_redirects(response,request,yield_requests=True))
        assert redirected.body.tell()==0,redirected.body.tell()
    elif name=='blank-query':
        assert str(h.QueryParams('a='))=='a=', 'blank query value was dropped'
    elif name=='idna-port':
        url=h.URL('https://中国.icom.museum/').copy_with(port=8443)
        assert url.port==8443 and url.host=='中国.icom.museum'
    elif name=='query-hash':
        a,b=h.QueryParams('a=1&b=2'),h.QueryParams('b=2&a=1')
        assert a==b
        assert hash(a)==hash(b), 'equal query params have unequal hashes'
    elif name=='relative-absolute-join':
        from urllib.parse import urljoin
        actual=h.URL('/base').join('https://other.example/x')
        assert str(actual)==urljoin('/base','https://other.example/x'),str(actual)
    elif name=='header-encoding-cache':
        headers=h.Headers({'x':'old'})
        headers.update([(b'x',b'\xc3\xa9')])
        assert headers['x']=='é'
    elif name=='credential-slash':
        url=h.URL('https://example.org/').copy_with(username='a/b')
        assert url.host=='example.org' and url.username=='a/b',str(url)
    elif name=='idna-subdomain':
        assert h.URL('https://www.xn--fiqs8s.icom.museum/').host=='www.中国.icom.museum'
    elif name=='stale-encoding':
        response=h.Response(200,headers={'Content-Type':'text/plain; charset=utf-8'},content=b'\xff')
        old=response.text
        response.encoding='latin-1'
        assert response.text=='ÿ',(old,response.text,list(response.iter_text()))
    elif name=='base-query':
        with h.Client(base_url='https://example.org/api?token=abc',trust_env=False) as client:
            request=client.build_request('GET','users')
            assert request.url.path=='/api/users',str(request.url)
    elif name=='password-log':
        import logging
        messages=[]
        class Capture(logging.Handler):
            def emit(self,record):messages.append(record.getMessage())
        logger=logging.getLogger('httpx');handler=Capture();old=logger.level
        logger.addHandler(handler);logger.setLevel(logging.INFO)
        try:
            with h.Client(transport=h.MockTransport(lambda request:h.Response(200)),trust_env=False) as client:
                client.get('http://alice:secret@example.org/')
        finally:
            logger.removeHandler(handler);logger.setLevel(old)
        assert not any('secret' in message for message in messages),messages
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
