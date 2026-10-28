import importlib.util,pathlib
p=pathlib.Path(__file__).with_name('apply-codex-files.py');s=importlib.util.spec_from_file_location('a',p);a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
def payload(path, content='x'):return {'summary':'test','files':[{'path':path,'content':content}],'checksToRun':[],'limitations':[]}
cases=[('traversal',payload('../trusted/LAWS.bend')),('absolute',payload('/tmp/x')),('protected',payload('formal/LAWS.bend')),('malformed',{'files':[]}),('duplicate',dict(payload('app/server.ts'),files=[{'path':'app/server.ts','content':'1'},{'path':'app/server.ts','content':'2'}]))]
for name,p in cases:
 try:a.validate(p,a.REPAIR);raise AssertionError(name+' accepted')
 except ValueError:print(name+': blocked')
link=a.CANDIDATE/'app';link.symlink_to('/tmp')
try:
 try:a.validate(payload('app/server.ts'),a.REPAIR);raise AssertionError('symlink accepted')
 except ValueError:print('symlink: blocked')
finally:link.unlink()
print('6 interface rejection tests passed')
