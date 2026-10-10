// the container's HEALTHCHECK: the server answers, nothing more
export function GET() {
  return new Response('ok', { headers: { 'content-type': 'text/plain' } })
}
