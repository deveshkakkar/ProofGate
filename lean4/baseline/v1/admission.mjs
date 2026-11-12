import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
const executable = fileURLToPath(new URL('./core', import.meta.url));
const LIMIT = 281474976710655;
// A subprocess is deliberate: no dynamic library lookup or candidate export shim.
// The verifier tests this exact adapter and copies these bytes with the core.
export function batch(inputs) {
  for (const [balance, amount] of inputs) {
    if (!Number.isSafeInteger(balance) || balance < 0 || balance > 100
      || !Number.isSafeInteger(amount) || Math.abs(amount) > LIMIT) throw Error('Invalid core input');
  }
  const text = execFileSync(executable, [], {
    input: inputs.map(([b, a]) => `${b} ${a}\n`).join(''),
    encoding: 'utf8', timeout: 5000, maxBuffer: 1024 * 1024,
    env: { LANG: 'C' }
  });
  const lines = text.trimEnd().split('\n');
  if (lines.length !== inputs.length) throw Error('Invalid core response count');
  return lines.map(line => {
    if (!/^[01] \d+ \d+$/.test(line)) throw Error('Malformed core response');
    const [success, granted, balance] = line.split(' ').map(Number);
    if (!Number.isSafeInteger(granted) || granted > LIMIT
      || !Number.isSafeInteger(balance) || balance > 100) throw Error('Invalid core response');
    return { $: 'Response', success: success === 1, granted, balance };
  });
}
export default { admission(balance, amount) {
  if (amount === null || typeof amount !== 'object') throw Error('Invalid amount');
  let signed;
  if (amount.$ === 'Nonneg' && Number.isSafeInteger(amount.magnitude) && amount.magnitude >= 0) signed = amount.magnitude;
  else if (amount.$ === 'Neg' && Number.isSafeInteger(amount.pred) && amount.pred >= 0) signed = -amount.pred - 1;
  else throw Error('Invalid amount representation');
  return batch([[balance, signed]])[0];
} };
