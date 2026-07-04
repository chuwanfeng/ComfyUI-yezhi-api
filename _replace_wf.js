const fs = require('fs');

const appJs = fs.readFileSync('static/js/app.js', 'utf8');
const pagesNew = fs.readFileSync('static/js/pages_new.js', 'utf8');

// Extract WorkflowsPage from pages_new.js
const wfMatch = pagesNew.match(/const WorkflowsPage = \{[\s\S]*?\n\};/);
if (!wfMatch) {
  console.error('Could not find WorkflowsPage in pages_new.js');
  process.exit(1);
}
const newWf = wfMatch[0];

// Find and replace WorkflowsPage in app.js
const startMarker = 'const WorkflowsPage = {';
const endMarker = '\n};\n';
const startIdx = appJs.indexOf(startMarker);
if (startIdx === -1) {
  console.error('Could not find WorkflowsPage in app.js');
  process.exit(1);
}

// Find the closing }; after the WorkflowsPage object
let depth = 0;
let endIdx = startIdx;
let inString = false;
let stringChar = null;
let escaped = false;
for (let i = startIdx; i < appJs.length; i++) {
  const ch = appJs[i];
  if (escaped) { escaped = false; continue; }
  if (ch === '\\') { escaped = true; continue; }
  if (inString) {
    if (ch === stringChar) inString = false;
    continue;
  }
  if (ch === '`' || ch === "'" || ch === '"') {
    inString = true;
    stringChar = ch;
    continue;
  }
  if (ch === '{') depth++;
  if (ch === '}') {
    depth--;
    if (depth === 0) {
      // Find the next ; after this }
      endIdx = appJs.indexOf(';', i);
      if (endIdx === -1) endIdx = i;
      else endIdx = endIdx; // include the ;
      break;
    }
  }
}

const before = appJs.substring(0, startIdx);
const after = appJs.substring(endIdx + 1); // skip the ;
const result = before + newWf + '\n' + after;

fs.writeFileSync('static/js/app.js', result, 'utf8');
console.log('Replaced WorkflowsPage. New length:', result.length);

// Verify syntax
try {
  new Function(result);
  console.log('Syntax OK');
} catch (e) {
  console.error('Syntax ERROR:', e.message.substring(0, 200));
  // Restore original
  fs.writeFileSync('static/js/app.js', appJs, 'utf8');
  console.log('Restored original');
  process.exit(1);
}
