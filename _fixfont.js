const fs = require('fs');
let css = fs.readFileSync('D:\\vps\\python\\ComfyUI-yezhi-api\\static\\css\\app.css', 'utf8');
css = css.replace(/"MaShanZheng"/g, '"Ma Shan Zheng"');
css = css.replace(/"NotoSerifSC"/g, '"Noto Serif SC"');
fs.writeFileSync('D:\\vps\\python\\ComfyUI-yezhi-api\\static\\css\\app.css', css, 'utf8');
console.log('Done. Size:', css.length);
