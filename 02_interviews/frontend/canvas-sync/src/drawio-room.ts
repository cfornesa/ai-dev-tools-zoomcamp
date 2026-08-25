import {mkdirSync,readFileSync,writeFileSync} from "node:fs";
import {join} from "node:path";

export type DrawioUpdate={type:"document";sessionId:string;revision:number;xml:string};
type Client={send:(message:DrawioUpdate|{type:"conflict";revision:number;xml:string}|{type:"error";message:string})=>void};
type Snapshot={revision:number;xml:string};
const EMPTY_XML="<canvas version=\"1\"><shape type=\"text\" x=\"80\" y=\"90\" fill=\"#172033\">Interview canvas</shape></canvas>";
function safeSessionId(sessionId:string){if(!/^[a-zA-Z0-9_-]{1,128}$/.test(sessionId))throw new Error("invalid session id");return sessionId}
function validDocument(xml:string){return /^\s*<(?:canvas\b[\s\S]*<\/canvas>|mxfile\b[\s\S]*<\/mxfile>)\s*$/.test(xml)}
export class DrawioRoom{
  private clients=new Set<Client>(); private revision:number; private xml:string;
  constructor(readonly sessionId:string,private readonly stateDir:string){safeSessionId(sessionId);mkdirSync(stateDir,{recursive:true});try{const snapshot=JSON.parse(readFileSync(this.path(),"utf8")) as Snapshot;this.revision=Number.isInteger(snapshot.revision)&&snapshot.revision>=0?snapshot.revision:0;this.xml=typeof snapshot.xml==="string"?snapshot.xml:EMPTY_XML}catch{this.revision=0;this.xml=EMPTY_XML}}
  private path(){return join(this.stateDir,`${this.sessionId}.json`)}
  snapshot():DrawioUpdate{return {type:"document",sessionId:this.sessionId,revision:this.revision,xml:this.xml}}
  connect(client:Client){this.clients.add(client);client.send(this.snapshot())}
  disconnect(client:Client){this.clients.delete(client)}
  save(client:Client,baseRevision:number,xml:string){if(!this.clients.has(client))return {ok:false as const,reason:"unauthorized" as const};if(!Number.isInteger(baseRevision)||baseRevision!==this.revision){client.send({type:"conflict",revision:this.revision,xml:this.xml});return {ok:false as const,reason:"conflict" as const}}if(typeof xml!=="string"||xml.length>2_000_000||!validDocument(xml)){client.send({type:"error",message:"Canvas document is empty, malformed, unsupported, or too large"});return {ok:false as const,reason:"invalid" as const};}this.revision+=1;this.xml=xml;writeFileSync(this.path(),JSON.stringify({revision:this.revision,xml:this.xml}));const update=this.snapshot();for(const peer of this.clients)peer.send(update);return {ok:true as const,revision:this.revision}}
  close(){this.clients.clear()}
}
export class DrawioRoomRegistry{private rooms=new Map<string,DrawioRoom>();constructor(private readonly stateDir:string){mkdirSync(stateDir,{recursive:true})}get(sessionId:string){let room=this.rooms.get(sessionId);if(!room){room=new DrawioRoom(sessionId,this.stateDir);this.rooms.set(sessionId,room)}return room}removeIfEmpty(sessionId:string,room:DrawioRoom){if(this.rooms.get(sessionId)===room){room.close();this.rooms.delete(sessionId)}}size(){return this.rooms.size}}
