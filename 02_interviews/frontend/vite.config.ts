import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
const originOf=(value:string,fallback:string)=>{try{return new URL(value).origin}catch{return fallback}};
const apiOrigin=originOf(process.env.VITE_API_URL||"http://localhost:8000","http://localhost:8000");
const canvasOrigin=originOf(process.env.VITE_CANVAS_SYNC_URL||"http://localhost:8787","http://localhost:8787");
const editorOrigin=originOf(process.env.VITE_DRAWIO_EDITOR_URL||"http://localhost:8090/editor.html","http://localhost:8090");
const canvasWs=canvasOrigin.replace(/^http/,"ws");
export default defineConfig({plugins:[react()],server:{headers:{"Content-Security-Policy":`default-src 'self'; base-uri 'self'; object-src 'none'; frame-ancestors 'none'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline' https://accounts.google.com https://www.google.com; frame-src 'self' https://accounts.google.com https://www.google.com ${editorOrigin}; connect-src 'self' ${apiOrigin} ${canvasOrigin} ${canvasWs} https://www.google.com`}},test:{environment:"jsdom",globals:true,include:["src/**/*.{test,spec}.{js,ts,jsx,tsx}"]}});
