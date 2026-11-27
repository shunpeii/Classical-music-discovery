import {useEffect,useState} from 'react';
import type {Data,Era,Composer,Work,Concert} from '../types';
import {load} from '../data';
export function useAppState(){
 const [data,setData]=useState<Data>();const [error,setError]=useState(false);
 const [route,setRoute]=useState(location.hash.slice(1)||'home');
 const [era,setEra]=useState('classical');const [query,setQuery]=useState('');const [area,setArea]=useState('');const [mood,setMood]=useState('');const [date,setDate]=useState('');
 const [saved,setSaved]=useState<string[]>(()=>{try{const v=JSON.parse(localStorage.getItem('opus-saved')||'[]');return Array.isArray(v)?v:[]}catch{return[]}});
 useEffect(()=>{const h=()=>{setRoute(location.hash.slice(1)||'home');window.scrollTo(0,0)};window.addEventListener('hashchange',h);return()=>window.removeEventListener('hashchange',h)},[]);
 useEffect(()=>{Promise.all([load<Era[]>('master/eras.json'),load<Composer[]>('master/composers.json'),load<Work[]>('master/works.json'),load<{file:string;sample:boolean}>('concerts/latest.json').then(async x=>({concerts:await load<Concert[]>('concerts/'+x.file),sample:x.sample}))]).then(([eras,composers,works,snapshot])=>setData({eras,composers,works,...snapshot})).catch(()=>setError(true))},[]);
 useEffect(()=>{try{localStorage.setItem('opus-saved',JSON.stringify(saved))}catch{}},[saved]);
 const go=(r:string)=>{location.hash=r};const toggle=(id:string)=>setSaved(s=>s.includes(id)?s.filter(x=>x!==id):[...s,id]);

return {data,error,route,era,setEra,query,setQuery,area,setArea,mood,setMood,date,setDate,saved,go,toggle};
}
