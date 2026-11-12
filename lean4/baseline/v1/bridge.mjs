import assert from 'node:assert/strict';
import { performance } from 'node:perf_hooks';
import Core, { batch } from '/out/admission.mjs';
const inputs = [];
for (let b = 0; b <= 100; b++) {
  for (const a of [...Array.from({length:114}, (_, i) => i - 3), 281474976710655, -281474976710655]) inputs.push([b,a]);
}
const start = performance.now();
const outputs = batch(inputs);
const milliseconds = performance.now() - start;
outputs.forEach((result, i) => {
  const [b,a] = inputs[i], success = a > 0 && a <= b;
  assert.deepEqual(result, {$:'Response', success, granted:success ? a : 0, balance:success ? b-a : b});
});
assert.equal(inputs.length, 11716);
// Exercise the actual single-request adapter used by the service, including sign conversion.
const singleStart = performance.now();
for (const [b,a] of [[100,1],[100,100],[0,1],[100,0],[100,-1],[100,281474976710655],[100,-281474976710655]]) {
  const wire = a < 0 ? {$:'Neg',pred:-a-1} : {$:'Nonneg',magnitude:a};
  assert.deepEqual(Core.admission(b,wire), batch([[b,a]])[0]);
}
for (const pair of [[101,1],[-1,1],[100,1.5],[100,281474976710656],[100,NaN]]) assert.throws(() => batch([pair]));
for (const amount of [null, {}, {$:'Neg',pred:-1}, {$:'Nonneg',magnitude:-1}]) assert.throws(() => Core.admission(100,amount));
console.log(JSON.stringify({cases:inputs.length, batch_milliseconds:milliseconds, single_pair_milliseconds:(performance.now()-singleStart)/7}));
