import os, requests, pandas as pd
from flask import Flask,request,jsonify
from datetime import datetime
from zoneinfo import ZoneInfo
app=Flask(__name__)
B="https://fapi.binance.com"; T="https://api.telegram.org/bot{}"
SYMBOL=os.getenv("SYMBOL","PHAUSDT"); TZ=os.getenv("TIMEZONE","Asia/Karachi")
TOKEN=os.getenv("TELEGRAM_BOT_TOKEN",""); CHAT=os.getenv("TELEGRAM_CHAT_ID",""); SECRET=os.getenv("WEBHOOK_SECRET","")
def kl(i,n=300):
 r=requests.get(f"{B}/fapi/v1/klines",params={"symbol":SYMBOL,"interval":i,"limit":n},timeout=15); r.raise_for_status()
 c=["ot","open","high","low","close","volume","ct","qv","trades","tbv","tbq","x"]; d=pd.DataFrame(r.json(),columns=c)
 for x in ["open","high","low","close","volume"]: d[x]=pd.to_numeric(d[x])
 return d
def ema(s,n): return s.ewm(span=n,adjust=False).mean()
def rsi(s,n=14):
 d=s.diff(); g=d.clip(lower=0); l=-d.clip(upper=0); ag=g.ewm(alpha=1/n,adjust=False,min_periods=n).mean(); al=l.ewm(alpha=1/n,adjust=False,min_periods=n).mean()
 return 100-100/(1+ag/al.replace(0,float("nan")))
def atr(d,n=14):
 p=d.close.shift(); tr=pd.concat([d.high-d.low,(d.high-p).abs(),(d.low-p).abs()],axis=1).max(axis=1)
 return tr.ewm(alpha=1/n,adjust=False,min_periods=n).mean()
def state(d):
 d=d.copy(); d["e20"]=ema(d.close,20); d["e50"]=ema(d.close,50); d["e200"]=ema(d.close,200); d["r"]=rsi(d.close)
 m=ema(d.close,12)-ema(d.close,26); d["mh"]=m-ema(m,9)
 x=d.iloc[-1]; s=(1 if x.close>x.e20 else -1)+(1 if x.e20>x.e50 else -1)+(1 if x.close>x.e200 else -1)+(1 if x.r>=55 else -1 if x.r<=45 else 0)+(1 if x.mh>0 else -1)
 return s,float(x.close),float(x.r),float(x.e20),float(x.e50),float(x.e200),float(atr(d).iloc[-1])
def fmt(x):
 if abs(x)>=100:return f"{x:,.2f}"
 if abs(x)>=1:return f"{x:.4f}"
 return f"{x:.8f}".rstrip("0").rstrip(".")
def analysis():
 a=state(kl("4h")); b=state(kl("1h")); c=state(kl("15m")); w=a[0]*3+b[0]*2+c[0]
 act="LONG" if w>=8 else "SHORT" if w<=-8 else "NO TRADE"
 d=kl("1h"); p=b[1]; A=b[6]; lo=float(d.tail(80).low.min()); hi=float(d.tail(80).high.max())
 if act=="LONG":
  sl=min(lo-.1*A,p-1.2*A); risk=max(p-sl,.5*A); ent=f"{fmt(max(lo,p-.6*A))} — {fmt(p)}"; tp=[p+risk,p+2*risk,p+3*risk]
 elif act=="SHORT":
  sl=max(hi+.1*A,p+1.2*A); risk=max(sl-p,.5*A); ent=f"{fmt(p)} — {fmt(min(hi,p+.6*A))}"; tp=[p-risk,p-2*risk,p-3*risk]
 now=datetime.now(ZoneInfo(TZ))
 z=[f"📊 PHA/USDT FUTURES — DAILY ANALYSIS",f"🕒 {now:%Y-%m-%d %H:%M} ({TZ})","",f"💵 Price: {fmt(p)}",f"🎯 Bias: {act}",f"📈 Score: {w:+d}","",f"4H: {'BULLISH' if a[0]>=3 else 'BEARISH' if a[0]<=-3 else 'NEUTRAL'} | RSI {a[2]:.1f}",f"1H: {'BULLISH' if b[0]>=3 else 'BEARISH' if b[0]<=-3 else 'NEUTRAL'} | RSI {b[2]:.1f}",f"15M: {'BULLISH' if c[0]>=3 else 'BEARISH' if c[0]<=-3 else 'NEUTRAL'} | RSI {c[2]:.1f}","",f"🧱 Support: {fmt(lo)}",f"🧱 Resistance: {fmt(hi)}"]
 if act!="NO TRADE": z += ["",f"📍 Entry: {ent}",f"🛑 SL: {fmt(sl)}",f"🎯 TP1: {fmt(tp[0])}",f"🎯 TP2: {fmt(tp[1])}",f"🎯 TP3: {fmt(tp[2])}"]
 else:z += ["","⏸ No clean setup — wait for confirmation."]
 return "\n".join(z+["","⚠️ Analysis only. No orders are placed. Verify live levels before trading."])
def send(msg,c=None):
 r=requests.post(T.format(TOKEN)+"/sendMessage",json={"chat_id":c or CHAT,"text":msg},timeout=20); r.raise_for_status()
@app.get("/")
def home(): return "PHA/USDT analysis bot is running."
@app.get("/daily")
def daily():
 if request.args.get("secret")!=SECRET:return jsonify(ok=False),401
 send(analysis()); return jsonify(ok=True)
@app.post("/telegram")
def telegram():
 u=request.get_json(silent=True) or {}; m=u.get("message",{}); t=(m.get("text") or "").lower().strip(); c=m.get("chat",{}).get("id")
 if c and t in ("/start","/analysis"):
  try:send(analysis(),c)
  except Exception as e:send("⚠️ Error: "+str(e),c)
 return jsonify(ok=True)
