// Extracts CSS + body HTML from a v3 inject script and writes a static preview.
// Usage: node _extract.js <inject-script.js> <out.html> "<title>"
const fs = require('fs');
const path = require('path');

// JSDOM-free shim: stub out document, window, navigator etc
function buildShim(){
  const styles = [];
  const heads = [];
  let bodyHTML = '';
  const bodyStyle = { cssText: '' };
  const elShim = () => ({
    id:'', textContent:'', src:'', async:false,
    setAttribute(){}, getAttribute(){return null;},
    appendChild(){}, removeChild(){}, replaceChild(){}, parentNode:{ replaceChild(){} },
    rel:'', tagName:'', nodeType:1, insertBefore(){},
  });
  const document = {
    title: '',
    head: {
      appendChild(node){ heads.push(node); if(node && typeof node.textContent === 'string' && (node.id === 'bb-styles' || /^\s*\/?\*|^\s*[a-z*\.#@:]/i.test(node.textContent))){ styles.push(node.textContent); } },
    },
    body: {
      get innerHTML(){ return bodyHTML; },
      set innerHTML(v){ bodyHTML = v; },
      style: bodyStyle,
      querySelectorAll(){ return []; },
    },
    documentElement: { style: {} },
    createElement(tag){ const e = elShim(); e.tagName = tag.toUpperCase(); return e; },
    createTextNode(){ return elShim(); },
    querySelector(){ return null; },
    querySelectorAll(){ return []; },
    addEventListener(){},
    getElementById(){ return null; },
  };
  const window = {
    addEventListener(){},
    open(){},
    location: { pathname:'/', href:'' },
    setTimeout: setTimeout, setInterval: ()=>0, clearInterval: ()=>{},
    requestAnimationFrame: ()=>0,
    matchMedia: ()=>({matches:false, addEventListener(){}, addListener(){}}),
    IntersectionObserver: function(){ return { observe(){}, disconnect(){} }; },
    MutationObserver: function(){ return { observe(){}, disconnect(){} }; },
    navigator: { userAgent: 'node' },
  };
  return { document, window, styles, getBodyHTML: () => bodyHTML };
}

function extract(file){
  const src = fs.readFileSync(file, 'utf8');
  const shim = buildShim();
  // Wrap in a function exposing globals
  const fn = new Function('document','window','navigator','setTimeout','setInterval','clearInterval','requestAnimationFrame','IntersectionObserver','MutationObserver',
    `try { ${src} } catch(e) { /* ignore runtime errors after extraction */ }`);
  try {
    fn(shim.document, shim.window, shim.window.navigator, shim.window.setTimeout, shim.window.setInterval, shim.window.clearInterval, shim.window.requestAnimationFrame, shim.window.IntersectionObserver, shim.window.MutationObserver);
  } catch(e) {
    console.error('runtime error during extraction (continuing):', e.message);
  }
  return { css: shim.styles.join('\n'), body: shim.getBodyHTML() };
}

// Rewrite navbar links so preview pages link to peer .html files instead
// of the absolute Zoho production paths. Production inject scripts stay
// untouched (they need / and /trip-planning to resolve under butlerbutton.co).
function rewriteNavForPreview(body){
  return body
    .replace(/href="\/"/g, 'href="home.html"')
    .replace(/href="\/trip-planning"/g, 'href="trip-planning.html"')
    .replace(/href="\/concierge"/g, 'href="concierge.html"')
    .replace(/href="\/travel-advisor"/g, 'href="travel-advisor.html"')
    .replace(/href="\/supplier-code"/g, 'href="supplier-code.html"');
}

function buildPreview(css, body, title){
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${title}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style id="bb-styles">${css}</style>
</head>
<body style="background:#000;margin:0;padding:0;overflow-x:hidden">
${body}
</body>
</html>
`;
}

const [,, infile, outfile, title] = process.argv;
if (!infile || !outfile) { console.error('usage: node _extract.js <in.js> <out.html> [title]'); process.exit(1); }
const { css, body } = extract(path.resolve(infile));
const previewBody = rewriteNavForPreview(body);
fs.writeFileSync(outfile, buildPreview(css, previewBody, title || 'Butler Button preview'));
console.log('wrote', outfile, 'css:', css.length, 'body:', body.length);
