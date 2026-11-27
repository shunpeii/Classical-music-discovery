/// <reference types="vite/client" />
export async function load<T>(path:string):Promise<T>{const r=await fetch(import.meta.env.BASE_URL+'data/'+path,{cache:'no-cache'});if(!r.ok)throw Error(path);return r.json()}
