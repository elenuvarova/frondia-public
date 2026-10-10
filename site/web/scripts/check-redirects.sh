#!/usr/bin/env bash
# Plan 6: every old address answers with a permanent redirect to the site, path and query kept.
#   frondia.ontwrpn.com, facta.ontwrpn.com, www.frondia.eu  ->  301  ->  https://frondia.eu<same path and query>
#   An address with a trailing slash first gets Next's own 308 on the same host (/atlas/?... -> /atlas?...), then the 301
#   (plan 4, Q11); a direct 301 that keeps the slash is accepted too, and where it finally lands is checked either way.
#   The fragment (#threshold) never reaches a server: browsers carry it across redirects themselves.
# Live, after the switch (from site/):   bash web/scripts/check-redirects.sh
#   also checks http:// -> https:// (permanent; ALLOW_TEMPORARY_HTTP=1 accepts Traefik's 307 until plan 6 Task 7), where
#   each old address finally lands, the preview (og) a crawler gets, HSTS on the site (EXPECT_HSTS) and, with
#   CHECK_COMPRESSION=1, that pages come zstd- or brotli-compressed.
# Local, against `next start` with SITE_URL=https://frondia.eu:
#   ORIGIN=http://127.0.0.1:5191 bash web/scripts/check-redirects.sh      (the old host goes in the Host header; first hops only)
# Prints addresses, statuses and Locations only. Exit status 0 when every check passes. GET/HEAD only.
set -u
SITE=${SITE:-https://frondia.eu}
ORIGIN=${ORIGIN:-}
EXPECT_HSTS=${EXPECT_HSTS:-max-age=31536000}
HOSTS=(frondia.ontwrpn.com facta.ontwrpn.com www.frondia.eu)
# <old path and query>|<status where it finally lands on the site>
PATHS=(
  '/|200'
  '/?utm_source=old&utm_medium=link|200'
  '/atlas|200'
  '/atlas?city=ghent&sector=44021A00-|200'
  '/atlas?city=antwerp&sector=11001A01-&q=change|200'
  '/atlas/?city=charleroi&q=need&lens=heat|200'
  '/atlas/|200'
  '/atlas?case=ninove|200'
  '/atlas?city=antwerp&case=droogdokkenpark|200'
  '/dossier?city=brussels&sector=21004E72-|200'
  '/dossier/?city=ghent|200'
  '/commune?code=21001|200'
  '/data?city=ghent|200'
  '/data/?city=liege|200'
  '/register?show=yes&checked=1|200'
  '/privacy|200'
  '/en/privacy|200'
  # Dutch and French (plan 5 fix wave): the same rule under their prefixes
  '/nl|200'
  '/fr/privacy|200'
  '/nl/atlas?city=ghent&sector=44021A00-|200'
  '/fr/dossier?city=liege|200'
  '/nl/commune?code=21002|200'
  '/fr/data?city=liege|200'
  '/og/nl.jpg|200'
  '/og/fr.jpg|200'
  '/nl/foo|404'
  '/directions|404'
  '/data/brussels.json|200'
  '/data/communes.json|200'
  '/downloads/brussels/art8_balance_2025.csv|200'
  '/downloads/ghent/art8_balance_2025.csv|200'
  '/field/antwerp-photo-2024.jpg|200'
  '/photo/lilac-wind-og.jpg|200'
  '/favicon.svg|200'
  '/favicon.ico|200'
  '/og/en.jpg|200'
  '/robots.txt|200'
  '/sitemap.xml|200'
  '/health|200'
  '/atlas/assets/index.js|404'
  '/q%20x?a=%C3%A9&b=1%262|404'
)

pass=0
fail=0
ok() { pass=$((pass + 1)); echo "✓ $*"; }
bad() { fail=$((fail + 1)); echo "✗ $*"; }

# one request, no redirect followed: "<status> <location>"
hop() {
  local args=(-s -o /dev/null -D - --max-time 20)
  [ -n "${2:-}" ] && args+=(-H "Host: $2")
  curl --retry 2 --retry-delay 1 "${args[@]}" "$1" | tr -d '\r' | awk 'NR == 1 { s = $2 } tolower($1) == "location:" { l = $2 } END { print s, l }'
}
# where to send a request for <host><path>, and which Host header to give it
at() { if [ -n "$ORIGIN" ]; then echo "$ORIGIN$2"; else echo "https://$1$2"; fi; }
hosthdr() { if [ -n "$ORIGIN" ]; then echo "$1"; fi; }
# /atlas/?x -> /atlas?x, /atlas/ -> /atlas, / stays /
noslash() { printf '%s' "$1" | sed -E 's#^(/[^?]*[^/?])/(\?|$)#\1\2#'; }

for host in "${HOSTS[@]}"; do
  for entry in "${PATHS[@]}"; do
    p=${entry%|*}
    final=${entry##*|}
    q=$(noslash "$p")
    read -r s loc <<< "$(hop "$(at "$host" "$p")" "$(hosthdr "$host")")"
    if [ "$s" = 308 ] && [ "$q" != "$p" ]; then
      rel=${loc#https://$host}
      rel=${rel#http://$host}
      [ -n "$ORIGIN" ] && rel=${rel#$ORIGIN}
      if [ "$rel" != "$q" ]; then bad "$host$p -> 308 $loc (expected $q on the same host)"; continue; fi
      read -r s loc <<< "$(hop "$(at "$host" "$q")" "$(hosthdr "$host")")"
      want="$SITE$q"
      how="308 + 301"
    else
      want="$SITE$p"
      how="301"
    fi
    if [ "$s" = 301 ] && [ "$loc" = "$want" ]; then ok "$host$p -> $how $loc"; else bad "$host$p -> $s $loc (expected 301 $want)"; continue; fi
    if [ -z "$ORIGIN" ]; then
      read -r code n end <<< "$(curl --retry 2 --retry-delay 1 -s -o /dev/null -L --compressed --max-redirs 6 --max-time 30 -w '%{http_code} %{num_redirects} %{url_effective}' "https://$host$p")"
      case "$end" in "$SITE" | "$SITE"/*) ;; *) bad "$host$p ends at $end"; continue ;; esac
      if [ "$code" = "$final" ]; then ok "$host$p lands $code at $end ($n hops)"; else bad "$host$p lands $code at $end, expected $final"; fi
    fi
  done
done

if [ -z "$ORIGIN" ]; then
  # http -> https on the same host, permanent (Traefik; plan 6 Task 7)
  for host in frondia.eu "${HOSTS[@]}"; do
    p='/atlas?city=ghent'
    read -r s loc <<< "$(hop "http://$host$p")"
    case "$s" in
      301 | 308) if [ "$loc" = "https://$host$p" ]; then ok "http://$host$p -> $s $loc"; else bad "http://$host$p -> $s $loc"; fi ;;
      302 | 307) if [ "${ALLOW_TEMPORARY_HTTP:-0}" = 1 ]; then ok "http://$host$p -> $s (temporary, allowed until Task 7)"; else bad "http://$host$p -> $s $loc: temporary, should be 308"; fi ;;
      *) bad "http://$host$p -> $s $loc" ;;
    esac
  done
  # the preview a messenger builds from an old link: og:image and og:url on the site
  for u in 'https://frondia.ontwrpn.com/' 'https://frondia.ontwrpn.com/atlas?city=ghent' 'https://facta.ontwrpn.com/dossier?city=brussels&sector=21004E72-'; do
    html=$(curl --retry 2 --retry-delay 1 -sL --compressed --max-redirs 6 --max-time 30 -A 'facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)' "$u")
    img=$(printf '%s' "$html" | grep -o '<meta property="og:image" content="[^"]*"' | head -1 | sed 's/.*content="//; s/"$//')
    url=$(printf '%s' "$html" | grep -o '<meta property="og:url" content="[^"]*"' | head -1 | sed 's/.*content="//; s/"$//')
    case "$img" in "$SITE"/*) img_ok=1 ;; *) img_ok=0 ;; esac
    case "$url" in "$SITE" | "$SITE"/*) url_ok=1 ;; *) url_ok=0 ;; esac
    if [ "$img_ok$url_ok" = 11 ]; then ok "preview of $u: $img, $url"; else bad "preview of $u: og:image '$img', og:url '$url'"; fi
  done
  # HSTS on the site (D6; Task 8 may change the expected value)
  h=$(curl --retry 2 --retry-delay 1 -sI --max-time 20 "$SITE/" | tr -d '\r' | awk 'tolower($1) == "strict-transport-security:" { $1 = ""; sub(/^ /, ""); print }')
  if [ "$h" = "$EXPECT_HSTS" ]; then ok "HSTS on $SITE: $h"; else bad "HSTS on $SITE: '$h', expected '$EXPECT_HSTS'"; fi
  # compression at the proxy (D7, Task 3): a browser's Accept-Encoding gets zstd or br; the landing stays under 260 KB
  if [ "${CHECK_COMPRESSION:-0}" = 1 ]; then
    for p in / /data /register /data/brussels.json; do
      enc=$(curl --retry 2 --retry-delay 1 -s -o /dev/null -D - --max-time 30 -H 'Accept-Encoding: gzip, deflate, br, zstd' "$SITE$p" | tr -d '\r' | awk 'tolower($1) == "content-encoding:" { print $2 }')
      size=$(curl --retry 2 --retry-delay 1 -s --max-time 30 -H 'Accept-Encoding: gzip, deflate, br, zstd' "$SITE$p" | wc -c | tr -d ' ')
      case "$enc" in
        zstd | br) if [ "$p" = / ] && [ "$size" -gt 260000 ]; then bad "$SITE$p: $enc but $size bytes"; else ok "$SITE$p: $enc, $size bytes"; fi ;;
        *) bad "$SITE$p: '$enc', $size bytes (expected zstd or br)" ;;
      esac
    done
  fi
fi

echo "$pass passed, $fail failed"
[ "$fail" = 0 ]
