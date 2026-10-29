"""Evaluator-only regression probes; never copy this file into review workspaces.

Assertions adapted from upstream fixes/tests cited by catalog.json. Run each in a
fresh subprocess against the actual source tree, not an installed HTTP client.
"""
import asyncio
import importlib
import io
import os
from pathlib import Path
import pickle
import sys
import tempfile
from unittest.mock import patch


def probe(case_id, workspace):
    project, number = case_id.split('-')
    if project not in ('httpx', 'requests') or not number.isdigit() or not 1 <= int(number) <= 10:
        raise ValueError(f'unknown case: {case_id}')
    sys.path[:0] = [str(workspace / 'src'), str(workspace)]
    module = importlib.import_module(project)
    assert Path(module.__file__).resolve().is_relative_to(workspace.resolve()), module.__file__
    i = int(number)
    if project == 'httpx':
        h = module
        if i == 1:
            from httpx._config import create_ssl_context
            try:
                create_ssl_context(verify=False, cert='/__logic_lens_missing_cert__.pem', trust_env=False)
            except FileNotFoundError:
                return
            raise AssertionError('client certificate was silently skipped')
        if i == 2:
            assert h.Response(200, headers={'Content-Encoding': 'zstd'}, content=b'').content == b''
        if i == 3:
            seen = []
            def handle(req):
                seen.append(req.extensions.get('timeout'))
                return h.Response(200)
            with h.Client(timeout=0.25, transport=h.MockTransport(handle)) as client:
                client.send(h.Request('GET', 'http://example.org/'))
            assert seen == [dict(connect=0.25, read=0.25, write=0.25, pool=0.25)], seen
        if i == 4:
            auth = h.DigestAuth('Mufasa', 'CircleOfLife')
            request = h.Request('GET', 'http://example.org/dir/index.html')
            flow = auth.sync_auth_flow(request)
            request = next(flow)
            response = h.Response(401, request=request, headers={'WWW-Authenticate':
                'Digest realm="testrealm@host.com", nonce="dcd98b7102dd2f0e8b11d0f600bfb0c093", opaque="5ccc069c403ebaf9f0171e9517f40e41"'})
            header = flow.send(response).headers['Authorization']
            assert 'response="1949323746fe6a43ef61f9606e7febea"' in header, header
        if i == 5:
            response = h.Response(200, content=iter((b'Hello,', b' world!')))
            assert list(response.iter_text()) == ['Hello,', ' world!']
        if i in (6, 7):
            async def check():
                paths = []
                async def app(scope, receive, send):
                    if i == 7:
                        raise RuntimeError('application failure before response')
                    paths.append(scope['raw_path'])
                    await send({'type':'http.response.start', 'status':200, 'headers':[]})
                    await send({'type':'http.response.body', 'body':b'ok'})
                transport = h.ASGITransport(app=app, raise_app_exceptions=False)
                async with h.AsyncClient(transport=transport) as client:
                    response = await client.get('http://example.org/path?query')
                if i == 6:
                    assert paths == [b'/path'], paths
                else:
                    assert response.status_code == 500, response.status_code
            asyncio.run(check())
        if i == 8:
            from httpx._utils import get_environment_proxies
            with patch.dict(os.environ, {'no_proxy':'127.0.0.1,::1,localhost'}, clear=True):
                actual = get_environment_proxies()
            expected = {'all://127.0.0.1':None, 'all://[::1]':None, 'all://localhost':None}
            assert actual == expected, actual
        if i == 9:
            assert str(h.QueryParams('a=')) == 'a='
        if i == 10:
            headers = h.Headers({'x-header':'old'})
            headers.update([('x-header','1'), ('x-header','2,3')])
            assert headers.get_list('x-header') == ['1', '2,3'], headers
    else:
        r = module
        if i == 1:
            with tempfile.NamedTemporaryFile(mode='w+') as f:
                f.write('contents'); f.seek(0)
                req = r.Request('POST','http://example.org/',files={'file':f}).prepare()
                assert b'contents' in req.body
        if i == 2:
            class AttrProxy:
                def __init__(self): self.file = io.BytesIO(b'data')
                def __getattr__(self, name): return getattr(self.file, name)
            data = AttrProxy()
            req = r.Request('POST', 'http://example.org/', data=data).prepare()
            assert req.body is data and req._body_position == 0
        if i == 3:
            req = r.Request('GET','http://example.org//v:h').prepare()
            assert r.adapters.HTTPAdapter().request_url(req,{}) == '//v:h'
        if i == 4:
            headers = r.structures.CaseInsensitiveDict({'content-type':'text/html; charset'})
            assert r.utils.get_encoding_from_headers(headers) == 'ISO-8859-1'
        if i == 5:
            with tempfile.TemporaryDirectory() as directory:
                netrc = Path(directory)/'.netrc'
                netrc.write_text('machine example.com login user password pass\ndefault\n')
                with patch.dict(os.environ, {'NETRC':str(netrc)}):
                    assert r.utils.get_netrc_auth('http://httpbin.org/') is None
        if i == 6:
            error = r.exceptions.JSONDecodeError('Extra data', '{}{}', 2)
            assert repr(pickle.loads(pickle.dumps(error))) == repr(error)
        if i == 7:
            if os.name != 'nt':
                print('BLOCKED: requires native Windows path semantics')
                return 77
            path = r'\\localhost\invalid\location'
            assert r.utils.extract_zipped_paths(path) == path
        if i == 8:
            response = r.Response()
            response._content = b'\xff\xfe{\x00"\x00K0"\x00=\x00"\x00\xab0"\x00'
            response.encoding = None
            try:
                response.json()
            except r.exceptions.JSONDecodeError as exc:
                assert isinstance(exc, r.exceptions.RequestException)
            else:
                raise AssertionError('malformed JSON unexpectedly accepted')
        if i == 9:
            with patch.dict(os.environ, {'REQUESTS_CA_BUNDLE':'','CURL_CA_BUNDLE':''}, clear=True):
                session = r.Session()
                session.verify = '/explicit/ca.pem'
                settings = session.merge_environment_settings('http://example.org/', {}, False, True, None)
                assert settings['verify'] is True, settings
        if i == 10:
            from urllib3.exceptions import InvalidHeader
            class Pool:
                def urlopen(self, *a, **kw): raise InvalidHeader('conflicting content lengths')
            adapter = r.adapters.HTTPAdapter()
            adapter.get_connection = lambda *a, **kw: Pool()
            req = r.Request('GET','http://example.org/').prepare()
            try:
                adapter.send(req)
            except r.exceptions.InvalidHeader:
                return
            raise AssertionError('InvalidHeader not translated')
    return 0


if __name__ == '__main__':
    sys.exit(probe(sys.argv[1], Path(sys.argv[2]).resolve()))
