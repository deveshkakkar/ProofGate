import Core from './smoke.mjs';
const actual: number = Core.main();
if (actual !== 4) throw new Error(`unexpected ${actual}`);
console.log(JSON.stringify({typescriptCall: true, actual}));
