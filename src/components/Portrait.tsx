import {useState} from 'react';
import type {Composer} from '../types';
export function Portrait({composer}:{composer:Composer}){const [failed,setFailed]=useState(false);return <div className="composer-photo">{composer.portrait&&!failed?<img src={import.meta.env.BASE_URL+composer.portrait} alt={composer.name} title="画像出典は images/composers/credits.html を参照" loading="lazy" onError={()=>setFailed(true)}/>:<span>{composer.name.slice(0,1)}</span>}</div>}
