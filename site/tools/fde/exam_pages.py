#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业级智能体交付实战手册 · v5.0 两个独立页面生成器
====================================================
零第三方依赖，纯 Python 标准库；由 build_html.py 调用。

产出（均为单文件自包含、无外部请求）：
  FDE工程师考核题库.html   208 题 / 单选 + 多选 / 14 个能力域；支持打乱复习
  手册展示页.html           对外展示用的一页式能力体系说明（旧版，保留源码）

题库页面能力（v5.0 起全部为选择题）：
  练习 / 考试 / 错题 三种模式；题型、能力域、难度、题量筛选；
  Fisher–Yates 题序打乱；单选 / 多选一律选项乱序并重新映射答案；
  题型混排；错题优先注入；错题本（连对 2 次出本）；
  即时判分与解析、考试模式统一交卷、正确率与薄弱能力域；
  全部题目统一自动判分；localStorage 保存进度；深浅主题、手机、打印。
"""

import json

import question_bank_data as qb

QUIZ_HTML = "FDE工程师考核题库.html"
SHOW_HTML = "手册展示页.html"

# ---------------------------------------------------------------- 共享样式
SHARED_CSS = r"""
:root{--bg:#f5f5f7;--card:#fff;--text:#1d1d1f;--text-2:#424245;--muted:#6e6e73;
--line:#e5e5ea;--line-2:#d2d2d7;--accent:#0071e3;--accent-soft:#eaf3ff;--soft:#fafafa;
--ok:#0a8f4a;--ok-soft:#e6f7ee;--bad:#c8362f;--bad-soft:#fdeceb;--warn:#9a6508;--warn-soft:#fff3d9;
--fs:15px;--shadow:0 8px 30px rgba(0,0,0,.07)}
html[data-theme="dark"]{--bg:#16181d;--card:#20232a;--text:#f2f2f5;--text-2:#c9ccd3;
--muted:#9297a2;--line:#2f333c;--line-2:#3d424d;--accent:#63adff;--accent-soft:#172c47;
--soft:#1a1d23;--ok:#5ed39a;--ok-soft:#14372a;--bad:#ff8b84;--bad-soft:#3a1f20;
--warn:#e7bd6a;--warn-soft:#3a2f18;--shadow:0 8px 30px rgba(0,0,0,.45)}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--text);font-size:var(--fs);line-height:1.7;
font-family:-apple-system,BlinkMacSystemFont,"SF Pro Text","PingFang SC","Microsoft YaHei",sans-serif;
-webkit-font-smoothing:antialiased;-webkit-text-size-adjust:100%}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
.wrap{max-width:1040px;margin:0 auto;padding:24px 20px 70px}
.hero{background:linear-gradient(135deg,var(--accent-soft) 0%,var(--soft) 60%,var(--card) 100%);
border:1px solid var(--line);border-radius:22px;padding:32px 34px;margin-bottom:18px}
.hero .k{font-size:11.5px;font-weight:700;letter-spacing:.14em;color:var(--accent)}
.hero h1{font-size:31px;line-height:1.3;margin:11px 0 9px;letter-spacing:-.02em}
.hero p{color:var(--muted);margin:0;font-size:14px}
.pills{display:flex;flex-wrap:wrap;gap:7px;margin-top:18px}
.pills span{font-size:12px;background:var(--card);border:1px solid var(--line);border-radius:999px;
padding:5px 12px;color:var(--text-2)}
.nav{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 18px}
.nav a,.nav button{font-size:12.5px;border:1px solid var(--line);border-radius:9px;padding:6px 12px;
background:var(--card);color:var(--text-2);font-family:inherit;cursor:pointer;text-decoration:none}
.nav a:hover,.nav button:hover{border-color:var(--accent);color:var(--accent);text-decoration:none}
.foot{margin-top:28px;color:var(--muted);font-size:12.5px;text-align:center;line-height:1.85}
.panel{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:18px 20px;
margin-bottom:16px;box-shadow:var(--shadow)}
.panel h2{font-size:16px;margin:0 0 12px}
h2.sec{font-size:20px;margin:30px 0 12px;padding-bottom:10px;border-bottom:1px solid var(--line)}
.tag{display:inline-block;font-size:11px;border:1px solid var(--line);border-radius:999px;
padding:2px 9px;color:var(--muted);background:var(--soft)}
@media(max-width:760px){.wrap{padding:14px 12px 50px}.hero{padding:24px 18px}.hero h1{font-size:24px}}
"""

# ---------------------------------------------------------------- 题库样式
QUIZ_CSS = r"""
.frow{display:flex;flex-wrap:wrap;gap:10px 20px;margin-bottom:12px;align-items:flex-start}
.fgroup{min-width:190px;flex:1}
.fgroup>label{display:block;font-size:11.5px;font-weight:700;color:var(--muted);letter-spacing:.04em;margin-bottom:6px}
select,input[type=text],textarea{width:100%;padding:9px 12px;border:1px solid var(--line);border-radius:9px;
background:var(--bg);color:var(--text);font-size:13.5px;font-family:inherit;outline:none}
select:focus,input[type=text]:focus,textarea:focus{border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-soft)}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chip{font-size:12.2px;border:1px solid var(--line);border-radius:999px;padding:5px 11px;
background:var(--bg);color:var(--text-2);cursor:pointer;user-select:none;font-family:inherit}
.chip.on{background:var(--accent-soft);border-color:var(--accent);color:var(--accent);font-weight:700}
.chk{display:inline-flex;align-items:center;gap:5px;font-size:12.5px;color:var(--text-2);
margin:0 12px 6px 0;cursor:pointer}
.chk input{accent-color:var(--accent)}
.btns{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}
.btn{font-size:13px;border:1px solid var(--line);border-radius:9px;padding:9px 15px;
background:var(--card);color:var(--text-2);cursor:pointer;font-family:inherit}
.btn:hover{border-color:var(--accent);color:var(--accent)}
.btn.pri{background:var(--accent);border-color:var(--accent);color:#fff;font-weight:700}
.btn.pri:hover{color:#fff;filter:brightness(1.07)}
.btn:disabled{opacity:.45;cursor:not-allowed}
.statbar{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px}
.statbar div{flex:1;min-width:110px;background:var(--card);border:1px solid var(--line);
border-radius:11px;padding:9px 12px;font-size:12px;color:var(--muted)}
.statbar b{display:block;font-size:19px;color:var(--text);line-height:1.35}
.qcard{background:var(--card);border:1px solid var(--line);border-radius:16px;
padding:22px 24px;box-shadow:var(--shadow);margin-bottom:14px}
.qhead{display:flex;flex-wrap:wrap;gap:7px;align-items:center;margin-bottom:12px}
.qhead .qno{font-size:12.5px;font-weight:700;color:var(--accent)}
.qhead .tag{font-size:11px}
.stem{font-size:16.5px;font-weight:650;line-height:1.65;margin:0 0 16px}
.opts{display:flex;flex-direction:column;gap:8px;margin-bottom:6px}
.opt{display:flex;align-items:flex-start;gap:10px;border:1px solid var(--line);border-radius:11px;
padding:11px 13px;background:var(--soft);cursor:pointer;font-size:14px;line-height:1.6}
.opt:hover{border-color:var(--accent)}
.opt.sel{border-color:var(--accent);background:var(--accent-soft)}
.opt input{margin-top:4px;accent-color:var(--accent);flex:none}
.opt .ol{font-weight:700;color:var(--accent);flex:none;min-width:20px}
.orderlist{display:flex;flex-direction:column;gap:7px;margin-bottom:6px}
.ord{display:flex;align-items:center;gap:10px;border:1px solid var(--line);border-radius:10px;
padding:10px 12px;background:var(--soft);font-size:14px}
.ord .n{font-weight:700;color:var(--accent);min-width:22px}
.ord .txt{flex:1}
.ord button{font:inherit;font-size:12px;border:1px solid var(--line);border-radius:7px;
background:var(--card);color:var(--text-2);padding:3px 9px;cursor:pointer}
.ord button:hover{border-color:var(--accent);color:var(--accent)}
.blankbox{max-width:520px}
textarea{min-height:96px;resize:vertical;line-height:1.7}
.fb{border-radius:11px;padding:13px 15px;margin-top:14px;font-size:13.5px;line-height:1.75}
.fb.good{background:var(--ok-soft);border:1px solid var(--ok);color:var(--text)}
.fb.bad{background:var(--bad-soft);border:1px solid var(--bad);color:var(--text)}
.fb.info{background:var(--accent-soft);border:1px solid var(--accent);color:var(--text)}
.fb b{color:var(--accent)}
.fb .fl{display:block;font-size:11.5px;color:var(--muted);font-weight:700;letter-spacing:.04em;margin-bottom:4px}
.fb ul{margin:7px 0 0;padding-left:20px}
.qnav{display:grid;grid-template-columns:repeat(auto-fill,minmax(38px,1fr));gap:6px;margin-top:12px}
.qnav button{font:inherit;font-size:12px;border:1px solid var(--line);border-radius:8px;padding:6px 0;
background:var(--card);color:var(--text-2);cursor:pointer}
.qnav button.cur{border-color:var(--accent);background:var(--accent-soft);color:var(--accent);font-weight:700}
.qnav button.done{background:var(--soft)}
.qnav button.ok{border-color:var(--ok);color:var(--ok)}
.qnav button.no{border-color:var(--bad);color:var(--bad)}
.result{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:24px;
box-shadow:var(--shadow)}
.result h2{margin:0 0 6px;font-size:22px}
.domtable{width:100%;border-collapse:collapse;font-size:13px;margin-top:12px}
.domtable th,.domtable td{border-bottom:1px solid var(--line);padding:8px 9px;text-align:left}
.domtable th{color:var(--muted);font-size:11.5px;letter-spacing:.04em}
.review{margin-top:18px;border-top:1px solid var(--line);padding-top:14px}
.review .ri{border:1px solid var(--line);border-radius:11px;padding:12px 14px;margin-bottom:9px;font-size:13px}
.review .ri .rh{font-size:11.5px;color:var(--muted);margin-bottom:5px}
.notice{font-size:12.5px;color:var(--muted);margin-top:10px;line-height:1.7}
#printSheet{display:none}
@media(max-width:760px){.qcard{padding:16px 15px}.stem{font-size:15.5px}.fgroup{min-width:100%}}
@media print{
 .nav,.panel,.statbar,.qcard,.qnav,.btns,.result,.hero .pills,.foot,#setup{display:none!important}
 body{background:#fff;color:#111;font-size:12px}
 .wrap{padding:0;max-width:none}
 .hero{background:#fff;border:none;padding:0 0 12px;box-shadow:none}
 .hero h1{font-size:20px}
 #printSheet{display:block}
 #printSheet h2{font-size:15px;margin:16px 0 8px}
 #printSheet .pq{border-bottom:1px solid #ddd;padding:7px 0;page-break-inside:avoid}
 #printSheet .pq b{font-size:12.5px}
 #printSheet .po{font-size:11.5px;color:#333}
 #printSheet .key{font-size:11.5px;margin-top:16px}
 *{-webkit-print-color-adjust:exact;print-color-adjust:exact}
}
"""

# ---------------------------------------------------------------- 题库脚本
QUIZ_JS = r"""
(function(){
'use strict';
var D=window.__FDE_QDATA__, $=function(id){return document.getElementById(id);},
    root=document.documentElement, T=D.types;
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){
  return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
function LGet(k,d){try{var v=localStorage.getItem(k);return v?JSON.parse(v):d;}catch(e){return d;}}
function LSet(k,v){try{localStorage.setItem(k,JSON.stringify(v));}catch(e){}}
function shuffle(a){for(var i=a.length-1;i>0;i--){var j=Math.floor(Math.random()*(i+1));
  var t=a[i];a[i]=a[j];a[j]=t;}return a;}
function numsort(a,b){return a-b;}
function sameSet(a,b){a=(a||[]).slice().sort(numsort);b=(b||[]).slice().sort(numsort);
  if(a.length!==b.length)return false;for(var i=0;i<a.length;i++)if(a[i]!==b[i])return false;return true;}
var wrong=LGet('fde-quiz-wrong',{});
var S={list:[],idx:0,mode:'practice',ans:{},graded:{},submitted:false};
var autoTypes={single:1,multiple:1};

function getMode(){var e=document.querySelector('input[name=mode]:checked');return e?e.value:'practice';}
function typesOn(){var o={},e=document.querySelectorAll('#typeBox input');
  for(var i=0;i<e.length;i++)if(e[i].checked)o[e[i].value]=1;return o;}
function prepare(q,so){
  var v={id:q.id,q:q,opts:[],ans:[]},arr=[],i,j;
  for(i=0;i<q.options.length;i++)arr.push({t:q.options[i],o:i});
  if(so)shuffle(arr);
  for(i=0;i<arr.length;i++)v.opts.push(arr[i].t);
  for(i=0;i<q.answer.length;i++){for(j=0;j<arr.length;j++)if(arr[j].o===q.answer[i])v.ans.push(j);}
  v.ans.sort(numsort);
  return v;
}
function interleave(pool){
  var g={},order=[],i;
  for(i=0;i<pool.length;i++){var t=pool[i].type;
    if(!g[t]){g[t]=[];order.push(t);}g[t].push(pool[i]);}
  shuffle(order);
  for(i=0;i<order.length;i++)shuffle(g[order[i]]);
  var out=[],round=0,more=true;
  while(more){more=false;
    for(i=0;i<order.length;i++){var a=g[order[i]];if(round<a.length){out.push(a[round]);more=true;}}
    round++;}
  return out;
}
function buildPaper(){
  var mode=getMode(),types=typesOn(),dom=$('fDomain').value,lv=$('fLevel').value,
      lim=parseInt($('fLimit').value,10)||0,mix=$('optMix').checked,
      sq=$('optShuffleQ').checked,so=$('optShuffleO').checked,pool=[],i;
  if(mode==='wrong'){
    pool=D.questions.filter(function(q){return !!wrong[q.id];});
    pool.sort(function(a,b){return (wrong[b.id].n||0)-(wrong[a.id].n||0);});
  }else{
    pool=D.questions.filter(function(q){return types[q.type]&&
      (dom==='__all__'||q.domain===dom)&&(lv==='__all__'||q.level===lv);});
    if(sq)shuffle(pool);
    if(mix)pool=interleave(pool);
    var hot=pool.filter(function(q){return !!wrong[q.id];})
      .sort(function(a,b){return (wrong[b.id].n||0)-(wrong[a.id].n||0);}).slice(0,5);
    if(hot.length){var seen={};for(i=0;i<hot.length;i++)seen[hot[i].id]=1;
      pool=hot.concat(pool.filter(function(q){return !seen[q.id];}));}
  }
  if(lim>0&&pool.length>lim)pool=pool.slice(0,lim);
  S={list:pool.map(function(q){return prepare(q,so);}),idx:0,mode:mode,
     ans:{},graded:{},submitted:false};
  if(!S.list.length){
    $('qcard').hidden=true;$('result').hidden=false;
    $('result').innerHTML='<h2>没有符合条件的题目</h2><p class="notice">请放宽题型 / 能力域 / 难度筛选；'
      +'错题模式下若错题本为空，属正常情况——先去练习模式做几题。</p>';
    $('qnav').innerHTML='';updateStat();return;
  }
  $('result').hidden=true;$('qcard').hidden=false;
  renderCard();updateStat();save();
}
function grade(v,resp){
  if(resp==null||resp==='')return false;
  if(v.q.type==='single')return Number(resp)===v.ans[0];
  if(v.q.type==='multiple')return sameSet(resp,v.ans);
  return false;
}
function answerText(v){
  var out=[],i;
  for(i=0;i<v.ans.length;i++)out.push(v.opts[v.ans[i]]);
  return out.join('；');
}
function renderCard(){
  var v=S.list[S.idx],q=v.q,h='',i,resp=S.ans[q.id];
  h+='<div class="qhead"><span class="qno">第 '+(S.idx+1)+' / '+S.list.length+' 题</span>';
  h+='<span class="tag">'+esc(T[q.type])+'</span><span class="tag">'+esc(q.domain)+'</span>';
  h+='<span class="tag">'+esc(q.level)+'</span><span class="tag">出处 '+esc(q.src)+'</span>';
  h+='<span class="tag">'+esc(q.id)+'</span></div>';
  h+='<div class="stem">'+esc(q.stem)+'</div>';
  var multi=q.type==='multiple';
  h+='<div class="opts" id="optBox">';
  for(i=0;i<v.opts.length;i++){
    var on=multi?(resp||[]).indexOf(i)>-1:resp===i;
    h+='<label class="opt'+(on?' sel':'')+'"><input type="'+(multi?'checkbox':'radio')
      +'" name="opt" value="'+i+'"'+(on?' checked':'')+'>'
      +'<span class="ol">'+String.fromCharCode(65+i)+'.</span><span>'+esc(v.opts[i])+'</span></label>';
  }
  h+='</div>';
  $('qbody').innerHTML=h;
  var fb=$('fb');fb.innerHTML='';fb.className='';
  if(S.graded[q.id]!==undefined&&S.mode!=='exam')showFeedback(v,S.graded[q.id]);
  if(S.submitted&&S.mode==='exam')showFeedback(v,S.graded[q.id],true);
  $('btnPrev').disabled=S.idx===0;
  $('btnNext').disabled=S.idx===S.list.length-1;
  $('btnFinish').hidden=S.mode!=='exam'||S.submitted;
  $('btnSubmit').hidden=S.submitted;
  renderNav();
}
function renderNav(){
  var h='';
  for(var i=0;i<S.list.length;i++){
    var v=S.list[i],g=S.graded[v.id],cls=i===S.idx?'cur':'';
    if(g===true)cls+=' ok';else if(g===false)cls+=' no';
    else if(S.ans[v.id]!==undefined)cls+=' done';
    h+='<button class="'+cls+'" data-go="'+i+'" title="'+esc(v.q.id)+'">'+(i+1)+'</button>';
  }
  $('qnav').innerHTML=h;
}
function collect(){
  var v=S.list[S.idx],q=v.q,i;
  if(q.type==='single'){
    var e=document.querySelector('input[name=opt]:checked');if(e)S.ans[q.id]=Number(e.value);
  }else{
    var es=document.querySelectorAll('#optBox input:checked'),a=[];
    for(i=0;i<es.length;i++)a.push(Number(es[i].value));
    S.ans[q.id]=a;
  }
  return v;
}
function showFeedback(v,ok,examMode){
  var q=v.q,fb=$('fb'),good=ok===true;
  fb.className='';
  fb.innerHTML='<div class="fb '+(good?'good':'bad')+'"><span class="fl">'
    +(good?'✓ 回答正确':'✗ 回答错误'+(examMode?'（考试模式统一判分）':''))+'</span>'
    +'<div><b>正确答案：</b>'+esc(answerText(v))+'</div>'
    +'<div style="margin-top:5px"><b>解析：</b>'+esc(q.explain)+'</div>'
    +'<div style="margin-top:5px;color:var(--muted)">出处：'+esc(q.src)+'　｜　'+esc(q.domain)+'</div></div>';
}
function bump(id,ok){
  if(!wrong[id])wrong[id]={n:0,s:0};
  if(ok){wrong[id].s=(wrong[id].s||0)+1;if(wrong[id].s>=2)delete wrong[id];}
  else{wrong[id].n=(wrong[id].n||0)+1;wrong[id].s=0;}
  LSet('fde-quiz-wrong',wrong);
}
function submitOne(moveNext){
  var v=collect(),q=v.q,resp=S.ans[q.id];
  if(resp===undefined||resp===''||(resp instanceof Array&&!resp.length)){
    $('fb').className='';$('fb').innerHTML='<div class="fb info">还没有作答，请先选择选项。</div>';return;}
  var ok=grade(v,resp);
  /* 考试模式：交卷前不写 graded / 错题本，避免导航格与统计条泄露答案 */
  if(S.mode!=='exam'){S.graded[q.id]=ok;bump(q.id,ok);}
  if(S.mode==='exam'){
    $('fb').className='';$('fb').innerHTML='<div class="fb info">已记录本题答案。'
      +'考试模式不逐题公布结果，点「交卷」后统一出成绩单。</div>';
  }else showFeedback(v,ok);
  save();updateStat();renderNav();
  if(moveNext&&S.idx<S.list.length-1){S.idx++;renderCard();save();}
}
function updateStat(){
  var total=S.list.length,answered=0,right=0,multi=0;
  for(var i=0;i<S.list.length;i++){var v=S.list[i],q=v.q,r=S.ans[q.id],g=S.graded[q.id];
    if(q.type==='multiple')multi++;
    if(g===true)right++;
    if(r!==undefined&&r!==''&&(!(r instanceof Array)||r.length))answered++;
  }
  var rate=total?Math.round(right/total*100):0;
  $('stProgress').textContent=total?(S.idx+1)+' / '+total:'0 / 0';
  $('stAnswered').textContent=answered+' / '+total;
  $('stRight').textContent=right+' / '+total;
  $('stRate').textContent=rate+'%';
  $('stWrong').textContent=Object.keys(wrong).length;
  $('stMulti').textContent=multi+' / '+total;
}
function showResult(){
  S.submitted=true;
  var total=0,right=0,byDom={},i;
  for(i=0;i<S.list.length;i++){
    var v=S.list[i],q=v.q,d=q.domain;
    if(!byDom[d])byDom[d]={a:0,r:0};
    total++;byDom[d].a++;
    var ok=grade(v,S.ans[q.id]);S.graded[q.id]=ok;
    if(ok){right++;byDom[d].r++;}
    bump(q.id,ok);
  }
  var rate=total?Math.round(right/total*100):0;
  var h='<h2>成绩单 · '+(S.mode==='exam'?'考试模式':S.mode==='wrong'?'错题模式':'练习模式')+'</h2>';
  h+='<p class="notice">全部 '+total+' 题统一自动判分，答对 '+right+' 题，正确率 <b>'+rate+'%</b>。'
    +'v5.0 起题库只含单选与多选两类选择题；正确率只用于定位薄弱能力域，<b>不作为能力认证结论</b>。</p>';
  var arr=Object.keys(byDom).map(function(k){return {k:k,a:byDom[k].a,r:byDom[k].r};})
    .sort(function(x,y){return (x.r/x.a)-(y.r/y.a);});
  h+='<table class="domtable"><thead><tr><th>能力域</th><th>题数</th><th>答对</th><th>正确率</th><th>建议</th></tr></thead><tbody>';
  for(i=0;i<arr.length;i++){var o=arr[i],p=o.a?Math.round(o.r/o.a*100):0;
    h+='<tr><td>'+esc(o.k)+'</td><td>'+o.a+'</td><td>'+o.r+'</td><td>'+p+'%</td><td>'
      +(p<70?'优先回正文对应章节重做':'保持间隔复习')+'</td></tr>';}
  h+='</tbody></table>';
  if(arr.length&&arr[0].a)h+='<p class="notice"><b>最薄弱能力域：</b>'+esc(arr[0].k)
    +'。建议先回正文对应章节，再用「只练该能力域 + 打乱题序」重做一轮。</p>';
  h+='<div class="btns"><button class="btn pri" data-res="again">重新组卷</button>'
    +'<button class="btn" data-res="wrong">只看错题本</button>'
    +'<button class="btn" data-res="back">返回题目逐题回看</button>'
    +'<button class="btn" data-res="print">打印 / PDF（含答案页）</button></div>';
  h+='<div class="review"><h2 style="font-size:16px">逐题回看与解析</h2>';
  for(i=0;i<S.list.length;i++){
    var v2=S.list[i],q2=v2.q,g2=S.graded[q2.id];
    h+='<div class="ri"><div class="rh">第 '+(i+1)+' 题 · '+esc(T[q2.type])+' · '+esc(q2.id)
      +' · '+esc(q2.src)+' · '+(g2===true?'✓ 正确':g2===false?'✗ 错误':'未作答')+'</div>'
      +'<div><b>'+esc(q2.stem)+'</b></div>'
      +'<div>正确答案：'+esc(answerText(v2))+'</div>'
      +'<div style="color:var(--muted)">'+esc(q2.explain)+'</div></div>';
  }
  h+='</div>';
  $('qcard').hidden=true;$('result').hidden=false;$('result').innerHTML=h;
  $('result').scrollIntoView({behavior:'smooth',block:'start'});
  updateStat();save();
}
function buildPrint(){
  var h='<h2>FDE 工程师考核 · 本次试卷（共 '+S.list.length+' 题）</h2>';
  for(var i=0;i<S.list.length;i++){
    var q=S.list[i].q;
    h+='<div class="pq"><b>'+(i+1)+'. ['+esc(T[q.type])+'] '+esc(q.stem)+'</b>';
    if(q.options&&q.options.length){
      h+='<div class="po">'+q.options.map(function(o,k){return String.fromCharCode(65+k)+'. '+esc(o);}).join('　｜　')+'</div>';
    }
    h+='<div class="po">出处：'+esc(q.src)+'　能力域：'+esc(q.domain)+'　难度：'+esc(q.level)+'</div></div>';
  }
  h+='<div class="key"><b>答案页</b><br>';
  for(var j=0;j<S.list.length;j++){
    var v=S.list[j];
    h+=(j+1)+'. '+esc(v.q.id)+'　'+esc(answerText(v))+'<br>';
  }
  h+='</div>';
  $('printSheet').innerHTML=h;
}
function save(){LSet('fde-quiz-state',{list:S.list,idx:S.idx,mode:S.mode,
  ans:S.ans,graded:S.graded,submitted:S.submitted});}
function restore(st){
  S.list=st.list||[];S.idx=st.idx||0;S.mode=st.mode||'practice';
  S.ans=st.ans||{};S.graded=st.graded||{};S.submitted=!!st.submitted;
  var e=document.querySelector('input[name=mode][value="'+S.mode+'"]');if(e)e.checked=true;
  if(!S.list.length)return;
  if(S.submitted){showResult();}else{$('result').hidden=true;$('qcard').hidden=false;renderCard();}
  updateStat();
  $('resumeNote').hidden=false;
}

/* ---- 事件 ---- */
$('btnStart').addEventListener('click',function(){buildPaper();});
$('btnResume').addEventListener('click',function(){
  var st=LGet('fde-quiz-state',null);if(st&&st.list&&st.list.length)restore(st);
});
$('btnClear').addEventListener('click',function(){
  if(!confirm('清空错题本与上次进度？当前组卷不受影响。'))return;
  wrong={};LSet('fde-quiz-wrong',{});LSet('fde-quiz-state',null);
  $('resumeNote').hidden=true;updateStat();alert('已清空错题本与进度。');
});
$('btnSubmit').addEventListener('click',function(){submitOne(false);});
$('btnNext').addEventListener('click',function(){
  collect();if(S.idx<S.list.length-1){S.idx++;renderCard();save();}});
$('btnPrev').addEventListener('click',function(){
  collect();if(S.idx>0){S.idx--;renderCard();save();}});
$('btnFinish').addEventListener('click',function(){
  collect();if(!confirm('交卷后本次组卷统一判分，确认？'))return;showResult();});
$('btnPrint').addEventListener('click',function(){buildPrint();window.print();});
$('qbody').addEventListener('click',function(e){
  var b=e.target;while(b&&b!==this&&b.tagName!=='BUTTON')b=b.parentNode;
  if(!b||b.tagName!=='BUTTON')return;
  if(b.getAttribute('data-act')==='self'){submitOne(false);}
});
$('qbody').addEventListener('change',function(e){
  var t=e.target;if(t.name==='opt'){
    var labs=document.querySelectorAll('#optBox .opt');
    for(var i=0;i<labs.length;i++){var inp=labs[i].querySelector('input');
      labs[i].classList.toggle('sel',!!inp&&inp.checked);}
  }
  collect();save();updateStat();renderNav();
});
$('qnav').addEventListener('click',function(e){
  var b=e.target;while(b&&b!==this&&b.tagName!=='BUTTON')b=b.parentNode;
  if(!b||b.tagName!=='BUTTON')return;
  collect();S.idx=Number(b.getAttribute('data-go'));renderCard();save();updateStat();
});
$('result').addEventListener('click',function(e){
  var b=e.target;while(b&&b!==this&&b.tagName!=='BUTTON')b=b.parentNode;
  if(!b||b.tagName!=='BUTTON')return;
  var a=b.getAttribute('data-res');
  if(a==='again'){buildPaper();return;}
  if(a==='wrong'){
    var m=document.querySelector('input[name=mode][value=wrong]');if(m)m.checked=true;
    buildPaper();return;}
  if(a==='back'){$('result').hidden=true;$('qcard').hidden=false;S.submitted=false;
    S.idx=0;renderCard();save();return;}
  if(a==='print'){buildPrint();window.print();return;}
});
$('typeBox').addEventListener('click',function(e){
  var b=e.target;while(b&&b!==this&&b.tagName!=='BUTTON')b=b.parentNode;
  if(!b||b.tagName!=='BUTTON')return;
  b.classList.toggle('on');var inp=b.querySelector('input');if(inp){inp.checked=b.classList.contains('on');}
});
$('typeAll').addEventListener('click',function(){
  var bs=document.querySelectorAll('#typeBox .chip');
  for(var i=0;i<bs.length;i++){bs[i].classList.add('on');bs[i].querySelector('input').checked=true;}
});
var tb=$('themeBtn');
function paint(){var d=root.getAttribute('data-theme')==='dark';if(tb)tb.textContent=d?'☀️':'🌙';}
if(tb)tb.addEventListener('click',function(){
  var d=root.getAttribute('data-theme')==='dark';
  root.setAttribute('data-theme',d?'light':'dark');
  try{localStorage.setItem('fde-theme',d?'light':'dark');}catch(e){}
  paint();});
paint();
var saved=LGet('fde-quiz-state',null);
if(saved&&saved.list&&saved.list.length)$('resumeNote').hidden=false;
buildPaper();
})();
"""

# ---------------------------------------------------------------- 展示页样式
SHOW_CSS = r"""
.lead{font-size:16px;color:var(--text-2);line-height:1.85}
.lead b{color:var(--text)}
.cols3{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.cols2{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}
.box{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:17px 19px;box-shadow:var(--shadow)}
.box h3{font-size:15px;margin:0 0 7px}
.box p{font-size:13px;color:var(--muted);margin:0;line-height:1.75}
.box .n{font-size:11.5px;color:var(--accent);font-weight:700;letter-spacing:.08em}
.tiles{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
.tile{background:var(--card);border:1px solid var(--line);border-radius:13px;padding:15px 12px;text-align:center}
.tile b{display:block;font-size:26px;color:var(--accent);line-height:1.25;letter-spacing:-.02em}
.tile span{font-size:11.8px;color:var(--muted)}
.tbl{width:100%;border-collapse:collapse;font-size:13px;background:var(--card);
border:1px solid var(--line);border-radius:12px;overflow:hidden}
.tbl th,.tbl td{border-bottom:1px solid var(--line);padding:9px 11px;text-align:left;vertical-align:top}
.tbl th{background:var(--soft);color:var(--muted);font-size:11.5px;letter-spacing:.04em}
.tbl td:first-child{font-weight:650;color:var(--accent);white-space:nowrap}
.figbox{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:12px;box-shadow:var(--shadow)}
.figbox svg{width:100%;height:auto;display:block}
.figbox .cap{font-size:12px;color:var(--muted);text-align:center;margin-top:4px}
.figbox svg .b{fill:var(--accent-soft);stroke:var(--accent);stroke-width:1.4}
.figbox svg .ba{fill:var(--card);stroke:var(--accent);stroke-width:1.8}
.figbox svg .t{fill:var(--text);font-size:13px;font-weight:650}
.figbox svg .s{fill:var(--muted);font-size:11px}
.figbox svg .ln{stroke:var(--line-2);stroke-width:1.6;fill:none}
.figbox svg .ar{stroke:var(--accent);stroke-width:1.6;fill:none}
.chips2{display:flex;flex-wrap:wrap;gap:7px;margin-top:10px}
.chips2 span{font-size:12.3px;border:1px solid var(--line);border-radius:999px;
padding:5px 12px;background:var(--soft);color:var(--text-2)}
.cta{display:flex;flex-wrap:wrap;gap:10px;margin-top:14px}
.cta a{font-size:13.5px;border:1px solid var(--line);border-radius:11px;padding:11px 17px;
background:var(--card);color:var(--text-2);font-weight:650;text-decoration:none}
.cta a:hover{border-color:var(--accent);color:var(--accent);text-decoration:none}
.cta a.pri{background:var(--accent);border-color:var(--accent);color:#fff}
.cta a.pri:hover{color:#fff;filter:brightness(1.07)}
.bound{background:var(--warn-soft);border:1px solid var(--warn);border-radius:13px;padding:15px 18px;
font-size:13px;color:var(--text)}
.bound ul{margin:7px 0 0;padding-left:20px}
.steps{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
.step{background:var(--card);border:1px solid var(--line);border-radius:13px;padding:14px 15px}
.step .sn{font-size:11.5px;color:var(--accent);font-weight:700;letter-spacing:.06em}
.step b{display:block;font-size:14px;margin:4px 0 5px}
.step span{font-size:12.2px;color:var(--muted);line-height:1.7}
@media(max-width:900px){.cols3,.cols2,.steps{grid-template-columns:1fr 1fr}.tiles{grid-template-columns:repeat(2,1fr)}}
@media(max-width:600px){.cols3,.cols2,.steps{grid-template-columns:1fr}.tiles{grid-template-columns:repeat(2,1fr)}}
@media print{.nav,.cta{display:none!important}.box,.tile,.figbox,.step{box-shadow:none}
 body{background:#fff;color:#111}*{print-color-adjust:exact;-webkit-print-color-adjust:exact}}
"""

SHOW_JS = r"""
(function(){
var root=document.documentElement,tb=document.getElementById('themeBtn');
function paint(){var d=root.getAttribute('data-theme')==='dark';if(tb)tb.textContent=d?'☀️':'🌙';}
if(tb)tb.addEventListener('click',function(){
  var d=root.getAttribute('data-theme')==='dark';
  root.setAttribute('data-theme',d?'light':'dark');
  try{localStorage.setItem('fde-theme',d?'light':'dark');}catch(e){}
  paint();});
paint();
var pb=document.getElementById('printShow');
if(pb)pb.addEventListener('click',function(){window.print();});
})();
"""

SHOW_SVG = r"""
<svg viewBox="0 0 680 330" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="FDE 能力体系与五阶段交付示意图">
<defs><marker id="sah" markerWidth="9" markerHeight="9" refX="8" refY="3" orient="auto">
<path d="M0,0 L0,6 L8,3 z" style="fill:var(--accent)"/></marker></defs>
<rect class="b" x="18" y="16" width="644" height="60" rx="12"/>
<text class="t" x="34" y="41">三项核心能力（判断 · 实施 · 治理）</text>
<text class="s" x="34" y="61">场景理解与方案设计　｜　交付实施与评测运维　｜　安全合规与责任 AI</text>
<rect class="ba" x="18" y="100" width="198" height="66" rx="11"/>
<text class="t" x="34" y="126">① 场景判断</text>
<text class="s" x="34" y="146">值不值得做 · 边界 · 验收线</text>
<rect class="ba" x="241" y="100" width="198" height="66" rx="11"/>
<text class="t" x="257" y="126">② 方案与建设</text>
<text class="s" x="257" y="146">五种构建模式 · 知识 · 编排</text>
<rect class="ba" x="464" y="100" width="198" height="66" rx="11"/>
<text class="t" x="480" y="126">③ 证明与治理</text>
<text class="s" x="480" y="146">评测集 · 权限 · 审计 · 运维</text>
<line class="ar" x1="218" y1="133" x2="238" y2="133" marker-end="url(#sah)"/>
<line class="ar" x1="441" y1="133" x2="461" y2="133" marker-end="url(#sah)"/>
<line class="ln" x1="340" y1="78" x2="340" y2="96"/>
<text class="s" x="18" y="196">五阶段交付方法论（每阶段都有产出物与完成判据）</text>
<g>
<rect class="b" x="18" y="208" width="120" height="52" rx="9"/>
<text class="t" x="36" y="230">接入</text><text class="s" x="36" y="248">材料与边界</text>
<rect class="b" x="146" y="208" width="120" height="52" rx="9"/>
<text class="t" x="164" y="230">建设</text><text class="s" x="164" y="248">知识/流程/工具</text>
<rect class="b" x="274" y="208" width="120" height="52" rx="9"/>
<text class="t" x="292" y="230">验证</text><text class="s" x="292" y="248">评测集与基线</text>
<rect class="b" x="402" y="208" width="120" height="52" rx="9"/>
<text class="t" x="420" y="230">推广</text><text class="s" x="420" y="248">灰度/培训/采纳</text>
<rect class="b" x="530" y="208" width="132" height="52" rx="9"/>
<text class="t" x="548" y="230">治理</text><text class="s" x="548" y="248">版本/成本/回滚</text>
</g>
<line class="ar" x1="140" y1="234" x2="144" y2="234" marker-end="url(#sah)"/>
<line class="ar" x1="268" y1="234" x2="272" y2="234" marker-end="url(#sah)"/>
<line class="ar" x1="396" y1="234" x2="400" y2="234" marker-end="url(#sah)"/>
<line class="ar" x1="524" y1="234" x2="528" y2="234" marker-end="url(#sah)"/>
<rect class="ba" x="18" y="278" width="644" height="40" rx="10"/>
<text class="t" x="34" y="303">产出物：场景判断卡 → 方案画布 → 配置与评测集 → 验收报告 → 上线检查单与运维手册</text>
</svg>
"""


def _qdata():
    data = {
        "types": qb.TYPES,
        "domains": qb.DOMAINS,
        "levels": qb.LEVELS,
        "stats": qb.STATS,
        "questions": qb.QUESTIONS,
    }
    return (json.dumps(data, ensure_ascii=False, separators=(',', ':'))
            .replace('</', '<\\/'))


def nav_html(active):
    items = [
        ("index.html", "📚 总入口"),
        (SHOW_HTML, "🎯 手册展示"),
        ("01_主手册.html", "📖 主手册"),
        ("02_速查手册.html", "⚡ 速查手册"),
        ("03_开源课程解读.html", "📗 开源精读"),
        (QUIZ_HTML, "📝 考核题库"),
        ("术语词典.html", "🔤 术语词典"),
    ]
    h = ['<div class="nav">']
    for href, label in items:
        if href == active:
            h.append('<span class="tag" style="padding:6px 12px;border-radius:9px">%s</span>' % label)
        else:
            h.append('<a href="%s">%s</a>' % (href, label))
    h.append('<button id="themeBtn" title="切换深浅色">🌙</button></div>')
    return ''.join(h)


def _shell(title, hero_kicker, hero_h1, hero_p, pills, body, css, js, extra_head="", anchor=""):
    return ('<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            '<meta name="color-scheme" content="light dark"><title>' + title + '</title>'
            + extra_head + '<style>' + SHARED_CSS + css + '</style></head><body><div class="wrap">'
            '<div class="hero"' + (' id="' + anchor + '"' if anchor else '') + '>'
            '<div class="k">' + hero_kicker + '</div><h1>' + hero_h1 + '</h1>'
            '<p>' + hero_p + '</p><div class="pills">' + pills + '</div></div>'
            + body + '</div><script>' + js + '</script></body></html>')


def quiz_doc(head_script=""):
    st = qb.STATS
    by_type = st['by_type']
    pills = ''.join('<span>%s</span>' % p for p in [
        '共 %d 题' % st['total'], '单选 + 多选 两类选择题',
        '%d 个能力域' % len(qb.DOMAINS), '3 个难度层级',
        '练习 / 考试 / 错题 三种模式',
        '题序与选项均可打乱', '错题本本地保存', '零外部资源 · 手机 / 电脑',
    ])

    # 题型筛选 chips（默认全选）
    chips = []
    for k, label in qb.TYPES.items():
        chips.append('<button type="button" class="chip on">%s %d'
                     '<input type="checkbox" value="%s" checked style="display:none"></button>'
                     % (label, by_type[k], k))
    chips_html = ''.join(chips)

    dom_opts = ['<option value="__all__">全部能力域（%d 题）</option>' % st['total']]
    for d in qb.DOMAINS:
        dom_opts.append('<option value="%s">%s（%d 题）</option>'
                        % (d, d, st['by_domain'][d]))
    lv_opts = ['<option value="__all__">全部难度</option>']
    for lv in qb.LEVELS:
        lv_opts.append('<option value="%s">%s（%d 题）</option>' % (lv, lv, st['by_level'][lv]))

    body = []
    body.append(nav_html(QUIZ_HTML))
    body.append('<div class="panel" id="setup"><h2>① 组卷设置</h2>')
    body.append('<div class="frow"><div class="fgroup"><label>复习模式</label><div class="chips">'
                '<label class="chk"><input type="radio" name="mode" value="practice" checked>练习模式（逐题即时判分）</label>'
                '<label class="chk"><input type="radio" name="mode" value="exam">考试模式（统一交卷）</label>'
                '<label class="chk"><input type="radio" name="mode" value="wrong">错题模式（错题本优先）</label>'
                '</div></div></div>')
    body.append('<div class="frow"><div class="fgroup" style="flex:2"><label>题型（可多选，至少选 1 类）</label>'
                '<div class="chips" id="typeBox">%s</div>'
                '<button type="button" class="chip" id="typeAll" style="margin-top:8px">全选两类</button></div></div>' % chips_html)
    body.append('<div class="frow">'
                '<div class="fgroup"><label>能力域</label><select id="fDomain">%s</select></div>'
                '<div class="fgroup"><label>难度</label><select id="fLevel">%s</select></div>'
                '<div class="fgroup"><label>本次题量</label><select id="fLimit">'
                '<option value="10">10 题（快速盲区扫描）</option>'
                '<option value="20" selected>20 题（标准一轮）</option>'
                '<option value="40">40 题（专项强化）</option>'
                '<option value="60">60 题（模拟考核）</option>'
                '<option value="0">全部符合条件的题</option></select></div></div>'
                % (''.join(dom_opts), ''.join(lv_opts)))
    body.append('<div class="frow"><div class="fgroup" style="flex:3"><label>打乱规则（防止背题序、背选项位置）</label>'
                '<label class="chk"><input type="checkbox" id="optShuffleQ" checked>题序打乱（Fisher–Yates）</label>'
                '<label class="chk"><input type="checkbox" id="optShuffleO" checked>选项乱序（答案索引重映射）</label>'
                '<label class="chk"><input type="checkbox" id="optMix" checked>题型混排（单选 / 多选交叉）</label>'
                '<div class="notice">v5.0 起全部为选择题：单选题与多选题一律参与题序打乱与选项乱序，'
                '答案索引随之重映射；错题本按错误次数优先注入，连续答对 2 次自动移出。</div>'
                '</div></div>')
    body.append('<div class="btns"><button class="btn pri" id="btnStart">开始 / 重新组卷</button>'
                '<button class="btn" id="btnResume">继续上次进度</button>'
                '<button class="btn" id="btnPrint">打印 / PDF（含答案页）</button>'
                '<button class="btn" id="btnClear">清空错题本与进度</button></div>')
    body.append('<div class="notice" id="resumeNote" hidden>检测到本地保存的上次进度，'
                '点「继续上次进度」可回到原来的题序与作答。</div></div>')

    body.append('<div class="statbar">'
                '<div>当前进度<b id="stProgress">0 / 0</b></div>'
                '<div>已作答<b id="stAnswered">0 / 0</b></div>'
                '<div>答对<b id="stRight">0 / 0</b></div>'
                '<div>正确率<b id="stRate">0%</b></div>'
                '<div>错题本<b id="stWrong">0</b></div>'
                '<div>多选题<b id="stMulti">0 / 0</b></div></div>')

    body.append('<div class="qcard" id="qcard"><div id="qbody"></div><div id="fb"></div>'
                '<div class="btns"><button class="btn" id="btnPrev">← 上一题</button>'
                '<button class="btn pri" id="btnSubmit">提交本题 / 看解析</button>'
                '<button class="btn" id="btnNext">下一题 →</button>'
                '<button class="btn" id="btnFinish" hidden>交卷并出成绩单</button></div></div>')
    body.append('<div class="panel"><h2>② 题目导航（点编号直达；绿=对 / 红=错 / 灰=已答）</h2>'
                '<div class="qnav" id="qnav"></div></div>')
    body.append('<div class="result" id="result" hidden></div>')
    body.append('<div id="printSheet"></div>')
    body.append('<h2 class="sec">题型与判分口径（对应主手册 10.5.1）</h2>')
    body.append('<div class="panel"><table class="domtable"><thead><tr>'
                '<th>题型</th><th>题量</th><th>考什么</th><th>判分口径</th></tr></thead><tbody>'
                '<tr><td>单选题</td><td>%d</td><td>概念、口径、参数、硬约束、正确顺序、术语全称</td><td>唯一正确项，选错不得分</td></tr>'
                '<tr><td>多选题</td><td>%d</td><td>组合判断、完整清单、边界条件、场景处置</td><td>全部选对才得分，漏选与错选同等不得分</td></tr>'
                '</tbody></table><div class="notice"><b>v5.0 起题库统一为选择题</b>：'
                '原判断题 / 填空题 / 排序题 / 场景自评题已改写为单选或多选，'
                '开放性问题转到每个学习点的「🔍 细节追问」，不计入分数。'
                '两类题目全部自动判分，正确率只用于定位薄弱能力域，<b>不作为能力认证结论</b>；'
                '能否交付仍以主手册 0.4 的产出物与项目验收报告为准。</div></div>'
                % (by_type['single'], by_type['multiple']))
    body.append('<div class="foot">本题库为独立学习整理，<b>非官方题库</b>；'
                '题目与正文章节一一对应，答案与解析以本手册口径为准。<br>'
                '正文出现的产品与开源项目名称均为公开资料举例，'
                '不构成推荐、排名、背书或采购建议；平台功能、许可与规格以当期官方文档为准。<br>'
                '本页 CSS / JS / 题目 JSON 全部内嵌，进度与错题本只写浏览器 localStorage，不发起任何网络请求。</div>')

    js = 'window.__FDE_QDATA__=' + _qdata() + ';\n' + QUIZ_JS
    return _shell('FDE 工程师考核题库 · 208 题打乱复习 | 企业级智能体交付',
                  'FDE ASSESSMENT BANK · OFFLINE · v5.0',
                  'FDE 工程师考核题库｜208 题 · 打乱复习（单选 + 多选）',
                  '按 19 个知识单元、7 项能力权重、三种核心能力、五种构建模式、评测调优、安全合规、'
                  '工程治理、国内选型、开源课程精读、模型与 Agent 工程、语音 TTS、跨行业案例共 14 个能力域分组；'
                  '每题标注能力域、难度、出处与解析。支持题序 / 选项打乱、题型混排、三种复习模式与错题本。',
                  pills, ''.join(body), QUIZ_CSS, js,
                  extra_head=head_script, anchor='anchor-quiz')

def showcase_doc(head_script=""):
    st = qb.STATS
    pills = ''.join('<span>%s</span>' % p for p in [
        '跨行业通用 / 厂商中立', '十四篇 + 附录 A–F', '19 个知识单元',
        '14 步学习路径', '291 条可点术语', '8 张离线图示',
        '%d 道考核题' % st['total'], '38 项必背速达', '零外部资源',
    ])

    body = [nav_html(SHOW_HTML)]
    body.append('<h2 class="sec">一、这套手册是什么</h2>')
    body.append('<div class="panel"><p class="lead">'
                '<b>一句话定义：</b>前沿部署工程师（FDE）是把企业级智能体从「能用」做到'
                '「可验收、可上线、可治理」的人：先判断场景值不值得做，再选构建模式把知识和流程接进来，'
                '然后用评测集证明效果，最后用权限、审计与运维把风险管住。<br>'
                '这套手册把上述能力拆成<b>可学、可练、可查、可考、可讲</b>的五件事，'
                '面向零售 / 制造 / 金融 / 医疗 / 教育 / 政务 / 能源 / 物流等所有需要把智能体接入真实流程的行业，'
                '<b>不绑定任何厂商、不绑定任何行业</b>。</p></div>')
    body.append('<div class="cols3">'
                '<div class="box"><div class="n">CAPABILITY 01</div><h3>场景理解与方案设计</h3>'
                '<p>需求收敛 7 维度、场景评分卡、能做 / 难做 / 不能做、方案画布、一句话可验收需求、停止条件。</p></div>'
                '<div class="box"><div class="n">CAPABILITY 02</div><h3>交付实施与评测运维</h3>'
                '<p>五阶段交付、五种构建模式、评测集与 Badcase 归因、灰度与回滚、监控告警、成本与容量。</p></div>'
                '<div class="box"><div class="n">CAPABILITY 03</div><h3>安全合规与责任 AI</h3>'
                '<p>数据分级、RBAC 与最小权限、提示注入与越权检索、L1/L2/L3 操作分级、审计留痕与红队测试。</p></div>'
                '</div>')

    body.append('<h2 class="sec">二、能力体系与五阶段交付</h2>')
    body.append('<div class="figbox">' + SHOW_SVG +
                '<div class="cap">图｜三项核心能力 → 五阶段交付 → 逐阶段产出物（教学归纳，非厂商方案）</div></div>')

    body.append('<h2 class="sec">三、十四篇结构与附录</h2>')
    body.append('<table class="tbl"><thead><tr><th>位置</th><th>讲什么</th><th>解决什么来意</th></tr></thead><tbody>'
                '<tr><td>第零篇 · 使用说明</td><td>14 步分步学习路径、环境准备、适用范围与跨行业映射</td><td>第一次学，照着做</td></tr>'
                '<tr><td>第一篇 · AI 与 Agent 基础</td><td>AI / LLM / Transformer / RAG / Agent 与编排的概念地图</td><td>把名词和边界弄清楚</td></tr>'
                '<tr><td>第二篇 · 平台能力地图</td><td>构建模式 × 核心能力组件 × 模型；知识库、工作流、Multi-Agent</td><td>知道平台能做什么、不能做什么</td></tr>'
                '<tr><td>第三篇 · 五种模式实战</td><td>三个全新演练项目：门店运营、信贷合规问答、设备维修追溯</td><td>完整跑一遍配置与演示</td></tr>'
                '<tr><td>第四篇 · 评测与调优</td><td>评测集、Badcase 归因、Prompt / RAG / 工作流 / Multi-Agent 调优</td><td>把「效果不好」变成可定位的问题</td></tr>'
                '<tr><td>第五篇 · 企业级交付标准</td><td>五阶段、15+ 交付物、验收指标、安全合规与责任 AI</td><td>能签字、能上线</td></tr>'
                '<tr><td>第六篇 · 能力自评与备考</td><td>能力雷达、权重对照、自评表与复习节奏</td><td>知道自己还差什么</td></tr>'
                '<tr><td>第七篇 · 完全版补遗</td><td>工程基底、数据治理、部署运维、项目管理、行业纵深等 12 个专题</td><td>补齐课程之外的企业级细节</td></tr>'
                '<tr><td>第八篇 · 对外表达与讲解</td><td>一句话定义、30 秒 / 3 分钟 / 10 分钟讲法、四类听众话术、白板七层</td><td>能跟别人讲明白</td></tr>'
                '<tr><td>第九篇 · 国内技术选型</td><td>四输入变量、六层能力映射、四个部署方案包、评审 12 问</td><td>能解释技术选择与部署方案</td></tr>'
                '<tr><td>第十篇 · 扩展阅读与缺口</td><td>覆盖自评、10 类诚实缺口、六条主题线、考核题型与间隔复习</td><td>知道边界在哪、下一步往哪走</td></tr>'
                '<tr><td>附录 A–F</td><td>19 节覆盖对照、易混淆与模板集、版本改造记录、公开出处、最终目录总表</td><td>核验、复用与排复习顺序</td></tr>'
                '</tbody></table>')

    body.append('<h2 class="sec">四、一眼看懂规模</h2>')
    tiles = [
        ('19', '个知识单元全覆盖'), ('7', '项能力权重对照'), ('3', '个全新演练项目'),
        ('14', '步四阶段学习路径'), ('291', '条可点击术语'), ('8', '张内联 SVG 图示'),
        ('%d' % st['total'], '道考核题 / 单选 + 多选'), ('38', '项必背速达'),
        ('40', '行最终目录总表'), ('19', '节逐节笔记副本'), ('265', '张本地课程截图'),
        ('4', '个部署方案包'),
    ]
    body.append('<div class="tiles">' + ''.join(
        '<div class="tile"><b>%s</b><span>%s</span></div>' % (a, b) for a, b in tiles) + '</div>')

    body.append('<h2 class="sec">五、六个产品特色</h2>')
    body.append('<div class="cols3">'
                '<div class="box"><h3>① 完全离线</h3><p>CSS / JS / 术语 JSON / SVG / 截图全部内嵌或本地存放；'
                '无 CDN、无在线字体、无账号、无网络请求。整包解压即用。</p></div>'
                '<div class="box"><h3>② 手机 + 电脑双端</h3><p>电脑侧边栏、手机抽屉目录、目录过滤、'
                '阅读进度、深浅主题、字号调节、打印 / PDF。</p></div>'
                '<div class="box"><h3>③ 术语点击即查</h3><p>专业名词 / 英文 / 缩写带虚线标记，'
                '点击弹出全称、定义、交付意义与相关词条；独立词典页可分类检索。</p></div>'
                '<div class="box"><h3>④ 图示可打印</h3><p>8 张内联 SVG 随主题变色，'
                '把架构、闸门、集成、选型、路径、认知分层画清楚。</p></div>'
                '<div class="box"><h3>⑤ 可考核、可打乱</h3><p>208 道题 / 单选 + 多选 / 14 个能力域；'
                '题序与选项乱序、题型混排、错题本、三种复习模式、成绩单与薄弱能力域。</p></div>'
                '<div class="box"><h3>⑥ 边界诚实</h3><p>第十篇如实列出 10 类缺口与六项不承诺；'
                '不编造性能数字、价格、合规资质与真实客户成效。</p></div></div>')

    body.append('<h2 class="sec">六、学习节奏：14 步四阶段 + 间隔复习</h2>')
    body.append('<div class="steps">'
                '<div class="step"><div class="sn">STAGE 01</div><b>判断力 · Step 1–3</b>'
                '<span>概念地图、场景判断、需求收敛；产出场景判断卡与方案画布。</span></div>'
                '<div class="step"><div class="sn">STAGE 02</div><b>动手力 · Step 4–7</b>'
                '<span>五种构建模式、知识工程、工作流与工具；产出配置表与变量表。</span></div>'
                '<div class="step"><div class="sn">STAGE 03</div><b>证明力 · Step 8–12</b>'
                '<span>评测集、调优、安全合规、灰度上线；产出评测报告与验收基线。</span></div>'
                '<div class="step"><div class="sn">STAGE 04</div><b>治理与表达 · Step 13–14</b>'
                '<span>技术选型、对外讲解、复盘与扩展阅读；产出选型说明与复习计划。</span></div></div>')
    body.append('<div class="panel" style="margin-top:12px"><h2>间隔复习节奏（对应题库动作）</h2>'
                '<table class="domtable"><thead><tr><th>时间点</th><th>做什么</th><th>题库动作</th></tr></thead><tbody>'
                '<tr><td>学完当天</td><td>只看产出物清单与最终目录，逐项打勾</td><td>练习模式 · 全库随机 10 题</td></tr>'
                '<tr><td>第 2 天</td><td>闭卷复述一句话定义、五阶段、四环节、八段、白板七层</td><td>单选题专项 · 术语与硬约束</td></tr>'
                '<tr><td>第 7 天</td><td>重做 Badcase 归因与方案画布</td><td>考试模式 · 随机 20 题，记薄弱能力域</td></tr>'
                '<tr><td>第 30 天</td><td>重跑评测集回归，核对当期文档</td><td>错题模式 + 多选题专项</td></tr>'
                '<tr><td>每季度</td><td>复核许可 / 版本 / 价格 / 资质与成本模型</td><td>考试模式 · 第九篇能力域专项</td></tr>'
                '<tr><td>每次立项</td><td>重做四输入变量表与评审 12 问</td><td>多选题 · 模型与 TTS 选型两组</td></tr>'
                '</tbody></table></div>')

    body.append('<h2 class="sec">七、跨行业适用与典型角色</h2>')
    body.append('<div class="cols2">'
                '<div class="box"><h3>决定成败的是约束类型，不是行业名称</h3>'
                '<p>同一个知识问答，在零售是门店制度查询，在制造是设备维修手册，在金融是信贷合规问答，'
                '在医疗是诊疗规范检索——构建模式、评测方法、安全框架完全共用，变化的只是知识、权限与验收口径。</p>'
                '<div class="chips2">' + ''.join('<span>%s</span>' % x for x in
                ['零售', '制造', '金融', '医疗', '教育', '政务', '能源', '物流', '运营商', '地产']) + '</div></div>'
                '<div class="box"><h3>五类角色怎么用</h3>'
                '<p><b>业务负责人</b>：0.4 / 3.0 / 8.1，写清边界与停止条件。<br>'
                '<b>FDE</b>：全册，按 14 步跑完三个项目并补齐交付物。<br>'
                '<b>平台运维</b>：7.1 / 7.3 / 7.7 / 9.4，画拓扑、做压测与回滚演练。<br>'
                '<b>安全合规</b>：5.5 / 7.6 / 9.6，出权限矩阵与红队用例。<br>'
                '<b>内训讲师</b>：0.4 / 第八篇 / 附录 F，用最终目录排课。</p></div></div>')

    body.append('<h2 class="sec">八、边界声明</h2>')
    body.append('<div class="bound"><b>请连同以下边界一起对外使用：</b><ul>'
                '<li>本手册是独立学习整理的能力体系，不隶属、不代言任何厂商，不是任何认证的官方教材；题库亦非官方题库。</li>'
                '<li>第九篇、附录 E、术语词典与题库中出现的产品与开源项目名称，均为公开资料举例，'
                '不构成推荐、排名、背书或采购建议。</li>'
                '<li>三个演练项目与四个部署方案包均为教学演练组合，非真实客户案例或官方实施方案，数据为演示用假设值。</li>'
                '<li>不提供性能实测数字、价格、合规资质结论或投资回报承诺；平台功能、许可与规格以当期官方文档为准。</li>'
                '<li>题库正确率只用于定位薄弱能力域，不作为能力认证结论。</li></ul></div>')

    body.append('<h2 class="sec">九、从这里进入</h2>')
    body.append('<div class="cta">'
                '<a class="pri" href="index.html">📚 打开离线总入口</a>'
                '<a href="01_主手册.html">📖 主手册（完全版）</a>'
                '<a href="02_速查手册.html">⚡ 速查手册 A–N</a>'
                '<a href="' + QUIZ_HTML + '">📝 考核题库（打乱复习）</a>'
                '<a href="术语词典.html">🔤 术语词典</a>'
                '<a href="01_主手册.html#anchor-catalog">🗂 科学化最终目录</a>'
                '<a href="01_主手册.html#anchor-selection">🧭 国内方案选型</a>'
                '<a href="核验报告.md">✅ 全面核验报告</a></div>')
    body.append('<div class="btns"><button class="btn" id="printShow">打印 / PDF</button></div>')
    body.append('<div class="foot">企业级智能体交付实战手册 · 前沿部署工程师（FDE）能力体系与实施标准 · v5.0<br>'
                '跨行业通用 / 厂商中立 ｜ 全部资源离线自包含，不发起任何网络请求。</div>')

    return _shell('手册展示页 · 企业级智能体交付实战手册 v5.0',
                  'CAPABILITY SHOWCASE · ENTERPRISE AGENT DELIVERY · v5.0',
                  '企业级智能体交付实战手册<br>FDE 能力体系与实施标准',
                  '一页看清：这套手册讲什么、怎么学、怎么查、怎么考、怎么讲给别人听，'
                  '以及它明确不承诺什么。适用于所有需要把智能体接入真实业务流程的行业。',
                  pills, ''.join(body), SHOW_CSS, SHOW_JS,
                  extra_head=head_script, anchor='anchor-showcase')
