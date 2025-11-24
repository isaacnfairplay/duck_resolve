function parseQuery(q) {
  var parts = q.split('&');
  var items = [];
  for (var i=0;i<parts.length;i++) {
    if(!parts[i]) continue;
    var kv = parts[i].split('=');
    if(kv.length>=2 && kv[1] !== '') {
      items.push([decodeURIComponent(kv[0]), decodeURIComponent(kv[1])]);
    }
  }
  return items;
}
var entries = parseQuery('$query');
var current = JSON.parse(localStorage.getItem('resolverHistory') || '{}');
for (var i=0;i<entries.length;i++) {
  var pair = entries[i];
  current[pair[0]] = pair[1];
}
localStorage.setItem('resolverHistory', JSON.stringify(current));
