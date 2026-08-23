import {createHmac,timingSafeEqual} from "node:crypto";
import {createServer,IncomingMessage,ServerResponse} from "node:http";
import {randomUUID} from "node:crypto";
import {TLSocketRoom} from "@tldraw/sync-core";
import {WebSocketServer} from "ws";
const port=8787; const secret=process.env.CANVAS_TOKEN_SECRET||"local-canvas-secret-change-me-32b";
function verify(raw:string,room:string){try{const [head,payload,signature]=raw.split(".");const expected=createHmac("sha256",secret).update(`${head}.${payload}`).digest("base64url");if(!signature||!timingSafeEqual(Buffer.from(signature),Buffer.from(expected)))return false;const claims=JSON.parse(Buffer.from(payload,"base64url").toString());return claims.kind==="canvas"&&claims.session_id===room&&claims.exp*1000>Date.now()}catch{return false}}
function respond(res:ServerResponse,status:number,body:unknown){res.writeHead(status,{"content-type":"application/json"});res.end(JSON.stringify(body))}
const rooms=new Map<string,TLSocketRoom>();
function roomFor(name:string){let room=rooms.get(name);if(!room){room=new TLSocketRoom({log:{error:(...args)=>console.error("canvas-sync",...args)}});rooms.set(name,room)}return room}
function token(req:IncomingMessage){const header=(req.headers.authorization||"").replace(/^Bearer /,"");if(header)return header;return new URL(req.url||"/","http://localhost").searchParams.get("token")||""}
function handler(req:IncomingMessage,res:ServerResponse){if(req.url==="/health"){respond(res,200,{ok:true,service:"canvas-sync"});return}const match=req.url?.match(/^\/rooms\/([^/?]+)(?:\?.*)?$/);if(match){if(!verify(token(req),match[1])){respond(res,403,{error:"canvas authorization required"});return}respond(res,200,{ok:true,room:match[1],authorized:true});return}respond(res,404,{error:"not found"})}
const server=createServer(handler); const wss=new WebSocketServer({noServer:true});
server.on("upgrade",(req,socket,head)=>{const match=req.url?.match(/^\/rooms\/([^/?]+)/);if(!match||!verify(token(req),match[1])){socket.destroy();return}wss.handleUpgrade(req,socket,head,ws=>{roomFor(match[1]).handleSocketConnect({sessionId:randomUUID(),socket:ws})})});
server.listen(port,"0.0.0.0",()=>console.log(`canvas-sync listening on ${port}`));
