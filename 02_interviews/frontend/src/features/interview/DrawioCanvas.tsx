import { useEffect, useRef, useState } from "react";

type DocumentMessage = { type: "document"; revision: number; xml: string };
type CanvasMessage = DocumentMessage | { type: "conflict"; revision: number; xml: string } | { type: "error"; message: string };
type Props = { sessionId: string; token: string; canvasUrl: string; editorUrl: string };

export function DrawioCanvas({ sessionId, token, canvasUrl, editorUrl }: Props) {
  const frame = useRef<HTMLIFrameElement>(null);
  const socket = useRef<WebSocket>();
  const latest = useRef<DocumentMessage>();
  const saving = useRef(false);
  const pendingSave = useRef<{ xml: string }>();
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
        if (saving.current) { sendToEditor({ action: "error", message: "A canvas save is already in progress. Wait for it to finish." }); return; }
        saving.current = true;
        pendingSave.current = { xml: message.xml };
        setStatus("Saving canvas…");
        const baseRevision = latest.current?.revision;
        if (baseRevision === undefined || !socket.current || socket.current.readyState !== WebSocket.OPEN) { saving.current = false; sendToEditor({ action: "error", message: "Canvas is disconnected. Reconnect before saving." }); return; }
        socket.current.send(JSON.stringify({ type: "save", revision: baseRevision, xml: message.xml }));
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
          const message = JSON.parse(event.data) as CanvasMessage;
          if (message.type === "document" || message.type === "conflict") {
            latest.current = { type: "document", revision: message.revision, xml: message.xml };
            if (message.type === "conflict" && pendingSave.current) sendToEditor({ action: "conflict", localXml: pendingSave.current.xml, xml: message.xml, revision: message.revision });
            else sendToEditor({ action: "load", xml: message.xml, revision: message.revision });
            setStatus(message.type === "conflict" ? "Canvas conflict: reload latest or reapply your changes" : saving.current ? "Canvas saved" : "Canvas connected");
            saving.current = false;
            pendingSave.current = undefined;
          } else if (message.type === "error") {
            saving.current = false;
            setStatus(`Canvas error: ${message.message.slice(0, 180)}`);
            sendToEditor({ action: "error", message: message.message.slice(0, 180) });
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
