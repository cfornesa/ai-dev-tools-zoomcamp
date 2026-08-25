import {createServer,IncomingMessage,ServerResponse} from "node:http";
import {WebSocketServer} from "ws";
import {DrawioRoomRegistry} from "./drawio-room";
import {verifyCanvasToken} from "./canvas-auth";

const port=Number(process.env.PORT||8787);const secret=process.env.CANVAS_TOKEN_SECRET||"local-canvas-secret-change-me-32b";const rooms=new DrawioRoomRegistry(process.env.DRAWIO_STATE_DIR||"./.drawio-state");
function token(req:IncomingMessage){const header=(req.headers.authorization||"").replace(/^Bearer /,"");if(header)return header;return new URL(req.url||"/","http://localhost").searchParams.get("token")||""}
function respond(res:ServerResponse,status:number,body:unknown){res.writeHead(status,{"content-type":"application/json"});res.end(JSON.stringify(body))}
function handler(req:IncomingMessage,res:ServerResponse){if(req.url==="/health"){respond(res,200,{ok:true,service:"canvas-sync",rooms:rooms.size()});return}const match=req.url?.match(/^\/drawio\/rooms\/([^/?]+)(?:\?.*)?$/);if(match){if(!verifyCanvasToken(token(req),match[1],secret)){respond(res,403,{error:"canvas authorization required"});return}respond(res,200,{ok:true,room:match[1],authorized:true});return}respond(res,404,{error:"not found"})}
const server=createServer(handler);const drawioWss=new WebSocketServer({noServer:true});
server.on("upgrade",(req,socket,head)=>{const match=req.url?.match(/^\/drawio\/rooms\/([^/?]+)/);const claims=match?verifyCanvasToken(token(req),match[1],secret):null;if(!match||!claims){socket.destroy();return}const room=rooms.get(match[1]);drawioWss.handleUpgrade(req,socket,head,ws=>{const client={send:(message:unknown)=>{if(ws.readyState===ws.OPEN)ws.send(JSON.stringify(message))}};room.connect(client);console.log(`canvas connected room=${match[1]} role=${claims.role}`);ws.on("message",raw=>{try{const message=JSON.parse(raw.toString());if(message.type==="save")room.save(client,message.revision,message.xml)}catch{ws.send(JSON.stringify({type:"error",message:"invalid canvas message"}))}});ws.on("close",()=>{room.disconnect(client);rooms.removeIfEmpty(match[1],room);console.log(`canvas disconnected room=${match[1]} role=${claims.role}`)})})});
server.listen(port,"0.0.0.0",()=>console.log(`canvas-sync listening on ${port}`));
