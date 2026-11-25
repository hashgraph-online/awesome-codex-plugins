/*@lang en*/K.add({ en: { p0: "Order placed", p1: "Cooking", p2: "Courier picked up", p3: "On the way", p4: "Delivered",
        late: "Delayed", canc: "Cancelled", eta: "Arrives about", eta2: "New arrival time about", cour: "Courier",
        call: "Call courier", help: "Help", none: "No order yet. The bot will fill this in." } });/*@end*/
/*@lang ru*/K.add({ ru: { p0: "Заказ принят", p1: "Готовится", p2: "Курьер забрал", p3: "В пути", p4: "Доставлен",
        late: "Задерживается", canc: "Отменён", eta: "Приедет около", eta2: "Новое время около", cour: "Курьер",
        call: "Позвонить курьеру", help: "Помощь", none: "Заказа пока нет. Бот его пришлёт." } });/*@end*/
/*@lang uk*/K.add({ uk: { p0: "Замовлення прийнято", p1: "Готується", p2: "Кур'єр забрав", p3: "В дорозі", p4: "Доставлено",
        late: "Затримується", canc: "Скасовано", eta: "Приїде близько", eta2: "Новий час близько", cour: "Кур'єр",
        call: "Зателефонувати кур'єру", help: "Допомога", none: "Замовлення поки немає. Бот його надішле." } });/*@end*/
function draw() {
  var s = K.S.chatData, $ = K.$;
  if (!s) { $("ti").textContent = K.t("none"); $("pl").textContent = ""; $("eta").textContent = ""; $("tl").innerHTML = ""; $("cr").hidden = 1; $("ac").innerHTML = ""; return; }
  var m = s.m | 0, live = m != 2 && s.s < 4, dis = K.busy || !K.can();
  $("ti").textContent = s.no;
  var k = m == 2 ? 2 : s.s > 3 ? 0 : m ? 1 : 0, pl = $("pl");
  pl.textContent = K.t(m == 2 ? "canc" : s.s > 3 ? "p4" : m ? "late" : "p" + s.s);
  pl.className = "pl s" + k;
  $("eta").textContent = live ? K.t(m ? "eta2" : "eta") + " " + K.time(s.eta) : s.t4 && m != 2 ? K.t("p4") + " " + K.time(s.t4) : "";
  var tl = $("tl"); tl.innerHTML = "";
  for (var i = 0; i < 5; i++) {
    var r = K.h("div", "sp" + (i < s.s || s.s > 3 ? " d" : i == s.s ? " c" + (m == 2 ? " x" : m ? " w" : "") : ""));
    r.appendChild(K.h("i"));
    r.appendChild(K.h("b", "el", K.t("p" + i)));
    r.appendChild(K.h("span", "mt", s["t" + i] ? K.time(s["t" + i]) : ""));
    tl.appendChild(r);
  }
  var cr = s.cr && live && s.s > 1;
  $("cr").hidden = !cr;
  if (cr) { $("cn").textContent = s.cr; $("cl").textContent = K.t("cour"); }
  var ac = $("ac"); ac.innerHTML = "";
  [["call", cr], ["help", 1]].forEach(function (a) {
    if (!a[1]) return;
    var b = K.h("button", "", K.t(a[0]));
    b.disabled = dis;
    b.onclick = function () { K.ask(a[0]); };
    ac.appendChild(b);
  });
}
K.start(draw, { sync: "sync" });
