class Form {
  constructor() { this.buttons = []; this._title = ""; this._body = ""; this.fields = []; }
  title(t) { this._title = t; return this; }
  body(b) { this._body = b; return this; }
  button(text, icon) { this.buttons.push({ text, icon }); return this; }
  textField(...a) { this.fields.push(a); return this; }
  toggle(...a) { this.fields.push(a); return this; }
  dropdown(...a) { this.fields.push(a); return this; }
  slider(...a) { this.fields.push(a); return this; }
  label(...a) { return this; }
  show(player) { (globalThis.__shown ||= []).push(this); return Promise.resolve(globalThis.__answer ? globalThis.__answer(this) : { canceled: true }); }
}
export class ActionFormData extends Form {}
export class ModalFormData extends Form {}
export class MessageFormData extends Form { button1(t) { return this; } button2(t) { return this; } }
