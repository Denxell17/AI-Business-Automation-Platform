import fs from 'node:fs';

const tokenFile = process.argv[2];
const output = process.argv[3];
if (!tokenFile?.startsWith('/') || !output?.startsWith('/')) {
  throw new Error('Absolute secret-file and output paths are required.');
}
const metadata = fs.lstatSync(tokenFile);
if (!metadata.isFile() || metadata.isSymbolicLink() || metadata.size > 4096) {
  throw new Error('The provider-token secret file is not safe to read.');
}
const token = fs.readFileSync(tokenFile, 'utf8').replace(/\r?\n$/, '');
if (token.length < 32 || /\s/.test(token)) {
  throw new Error('The provider-token secret file contains an invalid token.');
}
const credential = [{
  id: 'abapProviderAuth001',
  name: 'ABAP private provider authentication',
  type: 'httpHeaderAuth',
  data: { name: 'Authorization', value: `Bearer ${token}` },
}];
fs.writeFileSync(output, JSON.stringify(credential), { encoding: 'utf8', mode: 0o600 });
