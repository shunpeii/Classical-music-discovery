import {useState} from 'react';
import type {Composer} from '../types';
export function Portrait({composer,detail=false,priority=false}:{composer:Composer;detail?:boolean;priority?:boolean}){
 const [failed,setFailed]=useState(false);
 return <div className="composer-photo">{composer.portrait&&!failed?<img src={import.meta.env.BASE_URL+composer.portrait} alt={composer.name} loading={detail||priority?'eager':'lazy'} onError={()=>setFailed(true)}/>:<span>{composer.name.slice(0,1)}</span>}</div>
}
