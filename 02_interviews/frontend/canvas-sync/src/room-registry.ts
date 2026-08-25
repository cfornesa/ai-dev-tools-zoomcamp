export type ClosableRoom={close:()=>void};
export class RoomRegistry<R extends ClosableRoom>{private rooms=new Map<string,R>();constructor(private readonly factory:(name:string,onEmpty:()=>void)=>R){}get(name:string){let room=this.rooms.get(name);if(!room){room=this.factory(name,()=>{room?.close();this.rooms.delete(name)});this.rooms.set(name,room)}return room}size(){return this.rooms.size}}
