import React from "react";
import {Navigate} from "react-router-dom";
export function RouteGate({authorized,pending=false,children=null}:{authorized:boolean;pending?:boolean;children?:React.ReactNode}){if(pending)return <main className="card"><p>Authorizing session…</p></main>;if(!authorized)return <Navigate to="/login" replace/>;return <>{children}</>}
