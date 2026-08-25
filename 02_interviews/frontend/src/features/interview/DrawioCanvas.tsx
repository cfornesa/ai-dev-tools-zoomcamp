import { useEffect, useRef, useState } from "react";

type DocumentMessage = { type: "document"; revision: number; xml: string };
type Props = { sessionId: string; token: string; canvasUrl: string; editorUrl: string };

export function DrawioCanvas({ sessionId, token, canvasUrl, editorUrl }: Props) {
  const frame = useRef<HTMLIFrameElement>(null);
  const socket = useRef<WebSocket>();
  const latest = useRef<DocumentMessage>();
  const saving = useRef(false);
  const [status, setStatus] = useState("Connecting to canvas…");

  useEffect(() => {
    const frameOrigin = new URL(editorUrl, window.location.href).origin;
    const wsUrl = `${canvasUrl.replace(/^http/, "ws")}/drawio/rooms/${encodeURIComponent(sessionId)}?token=${encodeURIComponent(token)}`;
    let closed = false;
    const sendToEditor = (message: unknown) => frame.current?.contentWindow?.postMessage(JSON.stringify(message), frameOrigin);

    const onMessage = (event: MessageEvent) => {
      if (event.origin !== frameOrigin || event.source !== frame.current?.contentWindow) return;
      let message: Record<string, unknown>;
      try { message = JSON.parse(String(event.data)); } catch { return; }
      if (message.event === "init" && latest.current) {
        sendToEditor({ action: "load", xml: latest.current.xml, revision: latest.current.revision });
      } else if (message.event === "saved" && typeof message.xml === "string") {
        saving.current = true;
        setStatus("Saving canvas…");
        socket.current?.send(JSON.stringify({ type: "save", revision: Number(message.revision), xml: message.xml }));
      } else if (message.event === "request-load" && latest.current) {
        sendToEditor({ action: "load", xml: latest.current.xml, revision: latest.current.revision });
      } else if (message.event === "error" && typeof message.message === "string") {
        setStatus(`Canvas error: ${message.message.slice(0, 180)}`);
      } else if (message.event === "state" && typeof message.text === "string") {
        setStatus(message.text.slice(0, 180));
      }
    };
    window.addEventListener("message", onMessage);

    const connect = () => {
      if (closed) return;
      if (typeof WebSocket === "undefined") { setStatus("Canvas temporarily unavailable"); return; }
      setStatus("Connecting to canvas…");
      const ws = new WebSocket(wsUrl);
      socket.current = ws;
      ws.onopen = () => setStatus("Connected to canvas");
      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data) as DocumentMessage | { type: "conflict"; revision: number; xml: string };
          if (message.type === "document" || message.type === "conflict") {
            latest.current = { type: "document", revision: message.revision, xml: message.xml };
            sendToEditor({ action: "load", xml: message.xml, revision: message.revision });
            setStatus(message.type === "conflict" ? "Canvas changed elsewhere; reloaded latest version" : saving.current ? "Canvas saved" : "Canvas connected");
            saving.current = false;
          }
        } catch { setStatus("Canvas sent an invalid update"); }
      };
      ws.onerror = () => setStatus("Canvas temporarily unavailable");
      ws.onclose = () => {
        socket.current = undefined;
        if (!closed) { setStatus("Canvas disconnected; retrying…"); window.setTimeout(connect, 1000); }
      };
    };
    connect();
    return () => { closed = true; window.removeEventListener("message", onMessage); socket.current?.close(); };
  }, [canvasUrl, editorUrl, sessionId, token]);

  const embeddedEditorUrl = `${editorUrl}${editorUrl.includes("?") ? "&" : "?"}embedded=1`;
  return <section className="canvas-editor" aria-label="Collaborative draw.io canvas">
    <p className="status" role="status">{status}</p>
    <iframe className="canvas-frame" ref={frame} title="Collaborative canvas" src={embeddedEditorUrl} onLoad={() => setStatus("Editor loaded; joining canvas…")} sandbox="allow-scripts allow-same-origin" />
  </section>;
}
