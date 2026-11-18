const headers = {'Cache-Control':'private, no-store','X-Robots-Tag':'noindex','Content-Type':'text/html; charset=utf-8'};
export async function onRequest({ request, env }) {
  if (!env.QUIZ || !env.UNLOCK_CODE) return new Response('题库暂时未配置', {status:503, headers});
  const bytes = new TextEncoder().encode('49labs-fde-session-v1');
  const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(env.UNLOCK_CODE), {name:'HMAC',hash:'SHA-256'}, false, ['sign']);
  const token = Array.from(new Uint8Array(await crypto.subtle.sign('HMAC',key,bytes)), b=>b.toString(16).padStart(2,'0')).join('');
  const signedIn = (request.headers.get('Cookie') || '').split(';').some(s=>s.trim()==='fde_session='+token);
  if(request.method==='POST'){
    if(request.headers.get('Origin')!==new URL(request.url).origin) return new Response('来源无效',{status:403,headers});
    const form = await request.formData();
    const ok = form.get('code')===env.UNLOCK_CODE;
    const redirect = new Headers(headers);
    redirect.set('Location', ok ? './quiz' : '../FDE%E5%B7%A5%E7%A8%8B%E5%B8%88%E8%80%83%E6%A0%B8%E9%A2%98%E5%BA%93.html?error=1');
    if(ok) redirect.set('Set-Cookie','fde_session='+token+'; Path=/tools/fde/api/; HttpOnly; Secure; SameSite=Lax; Max-Age=604800');
    return new Response(null,{status:303,headers:redirect});
  }
  if(request.method!=='GET') return new Response(null,{status:405,headers});
  if(!signedIn) return new Response('请先输入解锁码。',{status:401,headers});
  const page=await env.QUIZ.get('quiz-html');
  return new Response(page ? page.replace('<head>', '<head><base href="/tools/fde/">') : '题库暂时不可用',{status:page?200:503,headers});
}
