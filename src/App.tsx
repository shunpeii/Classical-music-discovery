import {useAppState} from './hooks/useAppState';
import {catalog} from './components/catalog';
import {HomePage} from './pages/HomePage';
import {HistoryPage} from './pages/HistoryPage';
import {ComposerPage} from './pages/ComposerPage';
import {WorkPage} from './pages/WorkPage';
import {ConcertPage} from './pages/ConcertPage';
import {SavedPage} from './pages/SavedPage';
import {ConcertsPage} from './pages/ConcertsPage';
export function App(){
 const {data,error,route,era,setEra,query,setQuery,area,setArea,mood,setMood,date,setDate,saved,go,toggle}=useAppState();
 if(!data)return <main>{error?'データを読み込めませんでした。':'読み込み中…'}{error&&<button onClick={()=>location.reload()}>再試行</button>}</main>;
 const {eras,composers,works,concerts}=data;const [page,id]=route.split('/');
 const selected=eras.find(e=>e.id===era)||eras[0];const composer=composers.find(c=>c.id===id);const work=works.find(w=>w.id===id);const concert=concerts.find(c=>c.id===id);
 const {spotify,price,cards,workRows}=catalog({composers,works,saved,go,toggle});
 return <><header><button className="logo link" onClick={()=>go('home')}>opus.</button><span>関東 / CLASSICAL MUSIC</span></header><main>{data.sample&&<div className="sample">DEMO · 公演情報は架空のサンプルです</div>}
 {page==='home'?<HomePage eras={eras} go={go} setMood={setMood} setEra={setEra} cards={cards} concerts={concerts}/>:
 page==='history'?<HistoryPage eras={eras} era={era} setEra={setEra} selected={selected} composers={composers} go={go}/>:
 page==='composer'&&composer?<ComposerPage composer={composer} setEra={setEra} go={go} workRows={workRows} works={works} id={id} cards={cards} concerts={concerts}/>:
 page==='work'&&work?<WorkPage work={work} go={go} spotify={spotify} cards={cards} concerts={concerts} id={id}/>:
 page==='concert'&&concert?<ConcertPage concert={concert} go={go} price={price} toggle={toggle} id={id} saved={saved} workRows={workRows} works={works}/>:
 page==='saved'?<SavedPage cards={cards} concerts={concerts} saved={saved}/>:
 page==='concerts'?<ConcertsPage query={query} setQuery={setQuery} area={area} setArea={setArea} mood={mood} setMood={setMood} date={date} setDate={setDate} concerts={concerts} cards={cards} works={works} composers={composers}/>:<><h1>ページが見つかりません</h1><button onClick={()=>go('home')}>ホームへ</button></>}
 </main><nav>{[['home','⌂','ホーム'],['history','♫','音楽を知る'],['concerts','⌕','公演検索'],['saved','♡','保存']].map(([r,i,n])=><button className={page===r?'active':''} key={r} onClick={()=>go(r)}><span>{i}</span>{n}</button>)}</nav></>
}
