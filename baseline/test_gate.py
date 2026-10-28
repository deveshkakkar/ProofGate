import copy, json, pathlib, tempfile, unittest
import gate
BASE=pathlib.Path(__file__).parent
class GateTests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.tmp.name)
 def tearDown(self):self.tmp.cleanup()
 def policy(self):return gate.read_json(BASE/'policy.json')
 def test_policy_valid(self):gate.check_policy(self.policy())
 def test_removed_check(self):
  p=self.policy();p['checks'].pop()
  with self.assertRaises(ValueError):gate.check_policy(p)
 def test_disabled_check(self):
  p=self.policy();p['checks'][0]['enabled']=False
  with self.assertRaises(ValueError):gate.check_policy(p)
 def test_duplicate_check(self):
  p=self.policy();p['checks'].append(p['checks'][0])
  with self.assertRaises(ValueError):gate.check_policy(p)
 def test_unsupported_parser(self):
  p=self.policy();p['checks'][0]['parser']='trust-me'
  with self.assertRaises(ValueError):gate.check_policy(p)
 def test_timeout_required(self):
  p=self.policy();p['checks'][0]['timeout_seconds']=0
  with self.assertRaises(ValueError):gate.check_policy(p)
 def test_marker_requires_exact_single(self):
  c=self.policy()['checks'][0]
  for text in [b'',b'not checked',b'ALL PROOFS CHECK\nALL PROOFS CHECK']:
   with self.assertRaises(ValueError):gate.parse_check(c,text)
 def test_malformed_report(self):
  with self.assertRaises(ValueError):gate.parse_check(self.policy()['checks'][-1],b'not json')
 def test_missing_and_skipped_tests(self):
  c=self.policy()['checks'][-1]
  for rows in [[],[{'id':x,'status':'skipped'} for x in c['required_tests']],[{'id':x,'status':'passed'} for x in c['required_tests'][:-1]]]:
   with self.assertRaises(ValueError):gate.parse_check(c,json.dumps({'schema':1,'tests':rows}).encode())
 def test_valid_report(self):
  c=self.policy()['checks'][-1];r={'schema':1,'tests':[{'id':x,'status':'passed'} for x in c['required_tests']]}
  self.assertEqual(gate.parse_check(c,json.dumps(r).encode()),r)
 def test_missing_checker_actual(self):
  c={'id':'formal','argv':['/no/such/proofgate-checker'],'timeout_seconds':1,'parser':'marker','required_marker':'PASS'}
  r=gate.run_check(c,[],self.root,None);self.assertEqual(r['status'],'failed');self.assertIn('FileNotFoundError',r['error'])
 def test_timed_out_checker_actual(self):
  c={'id':'formal','argv':['/bin/sleep','5'],'timeout_seconds':.01,'parser':'marker','required_marker':'PASS'}
  r=gate.run_check(c,[],self.root,None);self.assertEqual(r['status'],'failed');self.assertIn('TimeoutError',r['error'])
 def test_nonzero_checker(self):
  c={'id':'formal','argv':['/bin/false'],'timeout_seconds':1,'parser':'marker','required_marker':'PASS'}
  self.assertEqual(gate.run_check(c,[],self.root,None)['status'],'failed')
 def test_exit_zero_without_marker_blocks(self):
  c={'id':'formal','argv':['/bin/true'],'timeout_seconds':1,'parser':'marker','required_marker':'PASS'}
  self.assertEqual(gate.run_check(c,[],self.root,None)['status'],'failed')
 def freeze(self):
  (self.root/'law').write_text('independent law')
  m={'schema':1,'review':{'approved':True},'files':gate.files_manifest(self.root)};gate.write_json(self.root/'frozen.json',m)
  return gate.digest(gate.canonical(m))
 def test_baseline_removed_law(self):
  sha=self.freeze();(self.root/'law').unlink()
  with self.assertRaisesRegex(ValueError,'content altered'):gate.assert_baseline(self.root,sha)
 def test_baseline_changed_law(self):
  sha=self.freeze();(self.root/'law').write_text('weakened law')
  with self.assertRaises(ValueError):gate.assert_baseline(self.root,sha)
 def test_baseline_manifest_tamper(self):
  sha=self.freeze();m=gate.read_json(self.root/'frozen.json');m['files']={};gate.write_json(self.root/'frozen.json',m)
  with self.assertRaisesRegex(ValueError,'identity'):gate.assert_baseline(self.root,sha)
 def test_baseline_unapproved(self):
  m={'schema':1,'review':{'approved':False},'files':{}};gate.write_json(self.root/'frozen.json',m)
  with self.assertRaisesRegex(ValueError,'approved'):gate.assert_baseline(self.root,gate.digest(gate.canonical(m)))
 def test_symlink_rejected(self):
  (self.root/'link').symlink_to('/etc/passwd')
  with self.assertRaises(ValueError):gate.files_manifest(self.root)
 def test_candidate_protected_overlap(self):
  p=self.policy();p['source_files'].append('formal/Model.bend')
  with self.assertRaises(ValueError):gate.check_policy(p)
 def test_unsafe_path(self):
  for p in ['/etc/passwd','../other','']:
   with self.assertRaises(ValueError):gate.relative(p)
if __name__=='__main__':unittest.main(verbosity=2)
