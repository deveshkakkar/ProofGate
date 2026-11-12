#!/usr/bin/env python3
"""Trusted host-side HTTP acceptance driver; candidate is only a sandboxed child.
Never imports candidate code. Server stdout/stderr never become the test report.
"""
import argparse,json,os,pathlib,signal,socket,subprocess,tempfile,time,urllib.request,urllib.error,concurrent.futures,sys
IDS=['fresh-grant','boundary','invalid','repeat-conflict','concurrent-distinct','concurrent-same','restart']

def http(port,path,body=None,raw=None):
    data=raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    req=urllib.request.Request(f'http://127.0.0.1:{port}{path}',data=data,headers={'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req,timeout=12) as r:return r.status,json.loads(r.read())
    except urllib.error.HTTPError as e:return e.code,json.loads(e.read())

def assert_result(r,success,granted,balance):
    code,body=r
    assert code==200,(code,body)
    assert body['success'] is success and body['granted']==granted and body['balance']==balance,body
    return body

class App:
    def __init__(self,prefix,node,entry):
        self.temp=tempfile.TemporaryDirectory(prefix='proofgate-http-');self.home=pathlib.Path(self.temp.name)
        self.prefix=prefix;self.node=node;self.entry=entry;self.proc=None
        self.db=self.home/'state.sqlite'
    def start(self):
        with socket.socket() as s:s.bind(('127.0.0.1',0));self.port=s.getsockname()[1]
        self.log=open(self.home/'service.log','ab')
        # Dedicated writable DB mount. No test driver, host home, evidence writer or deployment path is mounted.
        cmd=self.prefix+['--bind',str(self.home),'/data','--setenv','PORT',str(self.port),'--setenv','DB_PATH','/data/state.sqlite',self.node,self.entry]
        self.proc=subprocess.Popen(cmd,stdout=self.log,stderr=self.log,start_new_session=True)
        for _ in range(100):
            if self.proc.poll() is not None:raise AssertionError('service exited: '+(self.home/'service.log').read_text(errors='replace'))
            try:
                if http(self.port,'/status')[0]==200:return
            except (OSError,ValueError,urllib.error.URLError):pass
            time.sleep(.05)
        raise AssertionError('service readiness timed out')
    def stop(self):
        if self.proc and self.proc.poll() is None:
            os.killpg(self.proc.pid,signal.SIGTERM)
            try:self.proc.wait(timeout=3)
            except subprocess.TimeoutExpired:os.killpg(self.proc.pid,signal.SIGKILL);self.proc.wait()
        if hasattr(self,'log'):self.log.close()
    def close(self):self.stop();self.temp.cleanup()
    def reserve(self,id,amount):
        result=http(self.port,'/reserve',{'requestId':id,'amount':amount})
        code,body=result
        if code==200:
            assert set(body)=={'requestId','amount','success','granted','balance','reason'},body
            assert body['requestId']==id and body['amount']==amount,body
            assert type(body['success']) is bool and type(body['balance']) is int and 0<=body['balance']<=100,body
            assert type(body['granted']) is int,body
            expected='granted' if body['success'] else ('invalid_amount' if amount<=0 else 'insufficient_credits')
            assert body['reason']==expected,body
            assert body['granted']==(amount if body['success'] else 0),body
        return result
    def balance(self):
        code,body=http(self.port,'/status');assert code==200 and type(body['balance']) is int,body
        return body['balance']

def main():
    p=argparse.ArgumentParser();p.add_argument('--prefix-json',required=True);p.add_argument('--node',required=True);p.add_argument('--entry',required=True);a=p.parse_args()
    prefix=json.loads(a.prefix_json);rows=[]
    for tid in IDS:
        app=App(prefix,a.node,a.entry)
        try:
            app.start()
            if tid=='fresh-grant':
                assert app.balance()==100;assert_result(app.reserve('a',30),True,30,70);assert app.balance()==70
            elif tid=='boundary':
                assert_result(app.reserve('all',100),True,100,0);assert_result(app.reserve('over',1),False,0,0)
            elif tid=='invalid':
                for i,v in enumerate([0,-1,101,281474976710655,-281474976710655]):assert_result(app.reserve('n'+str(i),v),False,0,100)
                for i,v in enumerate([1.5,'5',None,True,9007199254740991,9007199254740992,281474976710656,-281474976710656]):
                    code,_=app.reserve('bad'+str(i),v);assert code==400,(v,code)
                assert http(app.port,'/reserve',{'requestId':'missing'})[0]==400
                for envelope in [{'amount':1},{'requestId':'','amount':1},{'requestId':12,'amount':1},{'requestId':None,'amount':1}]:assert http(app.port,'/reserve',envelope)[0]==400
                assert http(app.port,'/reserve',raw=b'{broken')[0]==400
                assert http(app.port,'/reserve',raw=b'\xff')[0]==400
                assert http(app.port,'/reserve',raw=b' '*70000)[0]==413
                zero=app.reserve('minus-zero',-0.0);assert app.reserve('minus-zero',0)==zero
                assert app.balance()==100
                assert_result(app.reserve('bad0',1),True,1,99)
            elif tid=='repeat-conflict':
                first=assert_result(app.reserve('ok',25),True,25,75)
                rejected=assert_result(app.reserve('reject',90),False,0,75)
                negative=assert_result(app.reserve('negative',-1),False,0,75)
                app.reserve('later',10)
                assert app.reserve('ok',25)==(200,first);assert app.reserve('reject',90)==(200,rejected);assert app.reserve('negative',-1)==(200,negative)
                for id,amount in [('ok',24),('reject',1),('negative',2)]:assert app.reserve(id,amount)==(409,{'error':'conflict'})
                assert app.balance()==65
            elif tid=='concurrent-distinct':
                with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:rs=list(ex.map(lambda i:app.reserve('c'+str(i),7),range(30)))
                assert all(r[0]==200 for r in rs);granted=sum(r[1]['granted'] for r in rs);assert granted+app.balance()==100
                assert sum(r[1]['success'] for r in rs)==14;assert app.balance()==2
            elif tid=='concurrent-same':
                with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:rs=list(ex.map(lambda _:app.reserve('one',30),range(20)))
                assert all(r==rs[0] for r in rs);assert app.balance()==70
                with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:rs=list(ex.map(lambda n:app.reserve('race',n),[1,2]*10))
                winners=[r[1] for r in rs if r[0]==200];assert winners and all(w==winners[0] for w in winners)
                assert sum(r[0]==409 for r in rs)==10;assert app.balance()==70-winners[0]['granted']
            elif tid=='restart':
                first=app.reserve('a',40);reject=app.reserve('no',80);neg=app.reserve('neg',-2)
                app.stop();assert app.db.is_file(),'no actual persisted database';app.start();assert app.balance()==60
                assert app.reserve('a',40)==first;assert app.reserve('no',80)==reject;assert app.reserve('neg',-2)==neg
                assert app.reserve('no',1)==(409,{'error':'conflict'});assert app.balance()==60
            rows.append({'id':tid,'status':'passed'})
        except Exception:
            log=app.home/'service.log'
            if log.exists():print(log.read_text(errors='replace')[-20000:],file=sys.stderr)
            raise
        finally:app.close()
    print(json.dumps({'schema':1,'tests':rows},sort_keys=True))
if __name__=='__main__':main()
