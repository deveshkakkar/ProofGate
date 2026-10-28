import assert from 'node:assert/strict';
const {default:Core}=await import('/out/admission.mjs');
let cases=0;
for(let balance=0;balance<=100;balance++){
  for(const amount of [...Array.from({length:114},(_,i)=>i-3),281474976710655,-281474976710655]){
    const wire=amount>=0?{$:'Nonneg',magnitude:amount}:{$:'Neg',pred:-amount-1};
    const result=Core.admission(balance,wire);
    const success=amount>0&&amount<=balance;
    assert.deepEqual(result,{$:'Response',success,granted:success?amount:0,balance:success?balance-amount:balance});
    cases++;
  }
}
assert.equal(cases,11716);
console.log('CORE_BRIDGE_11716_PASSED');
