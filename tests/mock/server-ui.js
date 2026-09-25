// Stand-in for @minecraft/server-ui: forms record what they were built with and answer from a queue
export const answers = [];
export const shown = [];

class Form {
  constructor(kind) {
    this.kind = kind;
    this.parts = [];
  }
  title(t) {
    this.parts.push(["title", t]);
    return this;
  }
  body(t) {
    this.parts.push(["body", t]);
    return this;
  }
  button(text, icon) {
    this.parts.push(["button", text, icon]);
    return this;
  }
  slider(label, min, max, step, value) {
    this.parts.push(["slider", label, min, max, step, value]);
    return this;
  }
  toggle(label, value) {
    this.parts.push(["toggle", label, value]);
    return this;
  }
  dropdown(label, options, value) {
    this.parts.push(["dropdown", label, options, value]);
    return this;
  }
  textField(label) {
    this.parts.push(["text", label]);
    return this;
  }
  submitButton(t) {
    this.parts.push(["submit", t]);
    return this;
  }
  divider() {
    return this;
  }
  label() {
    return this;
  }
  async show() {
    shown.push(this);
    const a = answers.shift();
    return a ?? { canceled: true, cancelationReason: "UserClosed" };
  }
}
export class ActionFormData extends Form {
  constructor() {
    super("action");
  }
}
export class ModalFormData extends Form {
  constructor() {
    super("modal");
  }
}
export class MessageFormData extends Form {
  constructor() {
    super("message");
  }
  button1(t) {
    return this.button(t);
  }
  button2(t) {
    return this.button(t);
  }
}
