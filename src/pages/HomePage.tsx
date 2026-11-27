import type {Era,Composer} from '../types';
import {Portrait} from '../components/Portrait';
type Props={eras:Era[];composers:Composer[];era:string;setEra:(s:string)=>void;go:(r:string)=>void;query:string;setQuery:(s:string)=>void};
export function HomePage({eras,composers,era,setEra,go,query,setQuery}:Props){return <>
<section className="welcome"><h1>はじめての<br/>クラシックコンサート</h1><p>有名な作曲家から、<br/>今聴けるコンサートを見つけよう</p><form onSubmit={e=>{e.preventDefault();go('concerts')}}><input aria-label="公演検索" placeholder="⌕ 作曲家・曲・会場で探す" value={query} onChange={e=>setQuery(e.target.value)}/></form></section>
<section className="browse"><h2>時代から探す</h2><div className="eras">{eras.map(e=><button className={era===e.id?'active':''} key={e.id} onClick={()=>setEra(e.id)}>{e.name}<small>{e.years}</small></button>)}</div><h2>この時代の有名な作曲家</h2><div className="composer-grid">{composers.filter(c=>c.eraId===era).map(c=><button key={c.id} onClick={()=>go('composer/'+c.id)}><Portrait composer={c}/><strong>{c.name}</strong></button>)}</div><button className="link history-link" onClick={()=>go('history')}>この時代の歴史を知る ›</button></section></>;}
